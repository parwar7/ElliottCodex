"""Finite recent search and existing public evaluations; no new authority."""
import argparse
from collections import Counter
from pathlib import Path
import time

import nvda_observational_hierarchy as previous
import nvda_bounded_report as bounded
from elliott_runtime.analysis.normal_component_exploration import (
    CandidateGenerationRequest, CandidateGenerationConfig, CandidatePivotWindow,
    CandidateHypothesisShape, generate_candidate_hypotheses,
    CompetingCandidateSetRequest, build_competing_candidate_set,
    FamilyHypothesisBridgeRequest, FamilyEvaluationKind, build_family_evaluation_hypotheses,
)
prior = previous.prior
old = previous.old
STAGE = 'NVDA-TARGETED-RECENT-PATH-SEARCH-AND-SYNTHESIS-V1'
PACK = old.ROOT / 'kernel_reviews' / STAGE
PREVIOUS_HASH = 'bb9e07cd16a8644074c19675b5b798a3c9e312a6cd06d729e194b96135df5058'


def integrity():
    path = previous.PACK / 'REVIEW_manifest.json'
    if old.hash_file(path) != PREVIOUS_HASH:
        raise ValueError('Previous baseline manifest changed')
    manifest = old.read(path)
    for key, root in (('files', previous.PACK), ('implementation_files', old.ROOT)):
        for e in manifest[key]:
            p = root / e['path']
            if p.stat().st_size != e['bytes'] or old.hash_file(p) != e['sha256']:
                raise ValueError('Previous approved entry changed: ' + str(p))
    return previous.integrity()


def spread(indices, cap):
    """Chronological equal-count-bin midpoints; not a ranking or price heuristic."""
    if type(cap) is not int or cap < 1 or type(indices) is not tuple:
        raise ValueError('Positive exact cap and tuple required')
    if any(type(i) is not int for i in indices) or tuple(sorted(set(indices))) != indices:
        raise ValueError('Unique ordered exact integer indices required')
    if len(indices) <= cap:
        return indices
    return tuple(indices[((2*j+1)*len(indices))//(2*cap)] for j in range(cap))


def sequence_key(res, source, points):
    return (res, source, tuple((p.timestamp_utc.isoformat(), p.pivot_kind.value.lower(),
                               str(old.Fraction(p.observed_price))) for p in points))


def exported_key(row, res):
    endpoints = [row['endpoints'][0]] + row['endpoints'][1::2]
    return (res, row['source_response_sha256'], tuple((e['timestamp_utc'], e['price_field'],
                                                     str(old.Fraction(e['price']))) for e in endpoints))


def select_sequences(pivots, count, cap, old_keys, res, source):
    if count not in (4, 6):
        raise ValueError('Only declared neutral 3/5 segment scopes')
    rows = []
    for i in range(max(0, len(pivots)-count+1)):
        points = pivots[i:i+count]
        domain = old.movement_domain(tuple(p.observed_price for p in points))
        disposition = ('DOMAIN_EXCLUDED' if not domain['eligible'] else
                       'PREVIOUSLY_EVALUATED_COORDINATES' if sequence_key(res, source, points) in old_keys else
                       'UNVISITED_BUDGET')
        rows.append({'start_index': i, 'pivot_ids': [p.pivot_id for p in points],
                     'domain': domain, 'disposition': disposition})
    selected = spread(tuple(r['start_index'] for r in rows if r['disposition']=='UNVISITED_BUDGET'), cap)
    for i in selected:
        rows[i]['disposition'] = 'SELECTED'
    return rows, selected


def corrective(identifier, snapshot, discovery, points, kernel):
    """Fresh exact four-point evaluate-as bridge; no geometry/family assertion."""
    if len(points) != 4:
        raise ValueError('Exact three-segment hypothesis required')
    subject = old.p.AnalyzedWaveSubject(identifier, snapshot.observations.provenance.source_sha256)
    refs = (STAGE, 'EVALUATE_AS_NOT_FAMILY_CLASSIFICATION')
    at = snapshot.observations.provenance.ingested_at_utc
    generated = generate_candidate_hypotheses(CandidateGenerationRequest(identifier, at, subject,
        snapshot.observations, discovery, CandidateGenerationConfig(4,4,0,1,
        (CandidateHypothesisShape.THREE_SEGMENT_HYPOTHESIS,), CandidatePivotWindow.EARLIEST), (), refs, points))
    competing = build_competing_candidate_set(CompetingCandidateSetRequest(identifier+':set', identifier, generated, refs))
    bridge = build_family_evaluation_hypotheses(FamilyHypothesisBridgeRequest(identifier+':bridge', at,
        competing, (FamilyEvaluationKind.SINGLE_ZIGZAG, FamilyEvaluationKind.FLAT), refs), kernel)
    return bridge


def check_demand(searches, pending, plan):
    """Aggregate operational preflight, before public evaluator invocation."""
    if len(plan['windows'])>plan['max_search_windows'] or sum(len(x['rows']) for x in searches)>plan['max_geometric_sequences_examined'] or len(pending)>plan['max_new_scopes']:
        raise ValueError('Aggregate selection cap exceeded before execution')
    if sum(n==6 for *_,n in pending)>plan['max_normal_results'] or 2*sum(n==4 for *_,n in pending)>plan['max_corrective_hypotheses']:
        raise ValueError('Evaluation preflight cap')


def tail(row, snapshot):
    last = row['endpoints'][-1]['timestamp_utc']
    bars = snapshot.observations.bars
    return {'hypothesis': row['display_id'], 'last_endpoint': last,
            'last_observation': bars[-1].timestamp_utc.isoformat(), 'last_close': bars[-1].close,
            'trailing_bars': sum(b.timestamp_utc.isoformat()>last for b in bars),
            'last_bar_forming': snapshot.last_bar_forming,
            'endpoint_developing': row['endpoints'][-1]['pivot_state']=='DEVELOPING',
            'state': 'CURRENT_WAVE_POSITION_UNRESOLVED', 'completion_authority': False,
            'reason': 'Original proposed endpoint and developing flags are retained, but do not establish an active Elliott wave or completion. Any trailing captured bars remain unclassified.'}


def build(output=PACK):
    output = Path(output)
    started = time.monotonic()
    pre = integrity(); old.save(output/'pre_integrity.json', pre)
    plan = old.read(PACK/'search_plan.json')
    snapshots, raw = old.tv.load_inputs()
    saved = old.read(previous.PACK/'canonical_hierarchy.json')
    res_by_hash = {s.observations.provenance.source_sha256: k for k,s in snapshots.items()}
    old_keys = {exported_key(h, res_by_hash[h['source_response_sha256']]) for h in saved['hypotheses']}
    cache = {}; cfg = old.geometry(plan['geometry_width']); searches = []; pending = []
    # Entire selection ledger saved before any new methodology evaluation.
    for label,res,start,end,cap in plan['windows']:
        s = snapshots[res]; bars, d = prior.geometry_window(s,start,end,cfg,cache)
        for count in plan['point_counts']:
            sid = f'{label}:{res}:N{count}'
            rows, indices = select_sequences(d.pivots if d else (),count,cap,old_keys,res,s.observations.provenance.source_sha256)
            search = {'id': sid, 'resolution':res, 'window':[start,end], 'point_count':count,
                      'bars':len(bars), 'pivots':len(d.pivots) if d else 0, 'cap':cap,
                      'rows':rows, 'selected':list(indices), 'source_hash':s.observations.provenance.source_sha256,
                      'discovery_id':d.request_id if d and hasattr(d,'request_id') else None,
                      'reason':'SELECTED' if indices else 'NO_DATA' if not bars else 'NO_NEW_ELIGIBLE_SEQUENCE'}
            searches.append(search)
            for i in indices: pending.append((search,s,d,i,count))
    check_demand(searches,pending,plan)
    old.save(output/'selection_before_evaluation.json', {'plan_sha256':old.hash_file(PACK/'search_plan.json'),
             'searches':searches, 'planned_scopes':len(pending), 'evaluation_outcomes_used':False})
    kernel = old.p.MethodologyKernel(Path('C:/ElliottCodex/Brain_LOCKED'))
    live = {}; doc = {'stage':STAGE,'inventories':[11,7,0,0], 'hypotheses':[], 'corrective_hypotheses':[],
        'nodes':[], 'searches':[], 'links':[], 'occurrence_evidence':[], 'scenario_ranking':None,
        'kernel_ancestry_links_added':0,'validated_families':0,'execution_ledger':[]}
    jobs,_,_ = old.root_plan(snapshots['1M'].observations,old.read(old.PACK/'search_plan.json'))
    for alias,d,points,_ in jobs:
        if alias not in ('M1','M2'):continue
        s=snapshots['1M']; ident=old.STAGE+':'+alias
        result=old.evaluate_scope(ident,old.p.AnalyzedWaveSubject(ident,s.observations.provenance.source_sha256),s.observations,d,points,s.observations.provenance.ingested_at_utc,kernel)
        row,nodes=old.export_hypothesis(result,alias,s.observations)
        expected=next(h for h in saved['hypotheses'] if h['display_id']==alias)
        for key in ('hypothesis_id','endpoints','p004','p005'):
            if row[key]!=expected[key]:raise ValueError('Old root replay differs')
        row.update(evaluation_origin='OLD_REPLAY',resolution='1M')
        doc['hypotheses'].append(row);doc['nodes']+=nodes;live[alias]=result
    for search,s,d,i,count in pending:
        alias=search['id']+':S'+str(i)
        ledger={'alias':alias,'search_id':search['id'],'start_index':i,'point_count':count}
        if time.monotonic()-started>plan['wall_time_seconds']:
            ledger['status']='UNVISITED_TIME_BUDGET';doc['execution_ledger'].append(ledger);continue
        print('Evaluate '+alias,flush=True)
        if count==6:
            result=prior.evaluate_independent(STAGE+':'+alias,s,d,d.pivots[i:i+count],(),kernel)
            row,nodes=old.export_hypothesis(result,alias,s.observations)
            row.update(evaluation_origin='NEW',resolution=search['resolution'],search_id=search['id'])
            doc['hypotheses'].append(row);doc['nodes']+=nodes;live[alias]=result
        else:
            bridge=corrective(STAGE+':'+alias,s,d,d.pivots[i:i+count],kernel)
            for row in bounded.family_rows(bridge,'independent',alias):
                row.update(display_id=alias+':'+row['family'],evaluation_origin='NEW',resolution=search['resolution'],
                           search_id=search['id'],parent_node_id=None,relative_degree='DEGREE_UNRESOLVED',
                           internal_status='INTERNALS_UNRESOLVED',family_validity=False,
                           observation_link_status='EXISTING_TYPED_LINK_ACCEPTS_NORMAL_IMPULSE_ONLY_NOT_TRANSFERRED')
                row['endpoints']=[old.endpoint_row(e,s.observations) for e in row['endpoints']]
                doc['corrective_hypotheses'].append(row)
        ledger['status']='EVALUATED';doc['execution_ledger'].append(ledger)
    link_results(doc,live,snapshots,plan,output,started)
    doc['input_coverage']={k:{'source_hash':s.observations.provenance.source_sha256,'metadata':previous.metadata(s),
        'bars':len(s.observations.bars),'last_bar_forming':s.last_bar_forming,
        'first_bar':s.observations.bars[0].timestamp_utc.isoformat(),'last_bar':s.observations.bars[-1].timestamp_utc.isoformat(),
        'last_close':s.observations.bars[-1].close} for k,s in snapshots.items()}
    doc['open_tails']=[tail(h,snapshots[h['resolution']]) for h in doc['hypotheses']+doc['corrective_hypotheses']]
    new=[h for h in doc['hypotheses'] if h['evaluation_origin']=='NEW']
    unique={exported_key(h,h['resolution']) for h in new}
    corrections=doc['corrective_hypotheses']
    doc['totals']={'new_normal_hypotheses':len(new),'new_corrective_evaluate_as_hypotheses':len(corrections),
        'new_unique_normal_endpoint_sequences':len(unique),'new_normal_duplicate_contexts':len(new)-len(unique),
        'new_unique_corrective_endpoint_sequences':len({exported_key(h,h['resolution']) for h in corrections}),
        'old_replayed':2,'previous_selected_normal':25,'previous_supported_observational_links':1,
        'new_p004':dict(Counter(h['p004']['status'] for h in new)),
        'new_p005':dict(Counter(h['p005']['status'] for h in new)),
        'new_fatal_despite_p005':sum(h['p004']['fatal'] and h['p005']['status']=='SUFFICIENT_CONDITION_ESTABLISHED' for h in new),
        'selection_dispositions':dict(Counter(r['disposition'] for s in searches for r in s['rows'])),
        'executed_scopes':sum(r['status']=='EVALUATED' for r in doc['execution_ledger']),
        'time_unvisited_scopes':sum(r['status']!='EVALUATED' for r in doc['execution_ledger']),
        'links':len(doc['links']), 'surviving_observational_links':sum(l['surviving_observational_link'] for l in doc['links']),
        'relationships':dict(Counter(l['relationship'] for l in doc['links'])),
        'family_certificates':0}
    doc['audit']=old.audit_hierarchy(doc,snapshots)
    old.save(output/'canonical_hierarchy.json',doc)
    print(doc['totals'],flush=True)
    return doc


def link_results(doc,live,snapshots,plan,output,started):
    by_obs={id(s.observations):s for s in snapshots.values()}
    planned=[]
    for pa,parent in live.items():
        ps=by_obs[id(parent.evaluations[0].hypothesis.generated_candidate.source_observations)]
        res=previous.metadata(ps)['context']['resolution']
        if res not in ('1M','1D'):continue
        roles=(4,) if res=='1M' else tuple(range(5))
        for index in roles:
            role=parent.evaluations[0].hypothesis.role_bindings[index]
            for ca,child in live.items():
                cs=by_obs[id(child.evaluations[0].hypothesis.generated_candidate.source_observations)]
                cres=previous.metadata(cs)['context']['resolution']
                if (res=='1M' and cres!='1D') or (res=='1D' and cres not in ('240','60','15')):continue
                points=child.evaluations[0].hypothesis.generated_candidate.ordered_selected_pivots
                if res=='1D' and not (role.start_boundary.timestamp_utc.date()<=points[-1].timestamp_utc.date() and points[0].timestamp_utc.date()<=role.end_boundary.timestamp_utc.date()):continue
                planned.append((pa,index,ca,ps,cs))
    selected=set(spread(tuple(range(len(planned))),plan['max_links']))
    old.save(output/'planned_links.json',{'date_overlap_is_routing_only':True,
        'items':[{'parent':pa,'role':i+1,'child':ca,'status':'SELECTED' if j in selected else 'UNVISITED_LINK_BUDGET'} for j,(pa,i,ca,_,_) in enumerate(planned)]})
    cache={};evidence={};links=[];pairings=0
    doc['unvisited_links']=[]
    for j,(pa,index,ca,ps,cs) in enumerate(planned):
        if j not in selected:continue
        if time.monotonic()-started>plan['wall_time_seconds']:
            doc['unvisited_links'].append({'parent':pa,'role':index+1,'child':ca,'reason':'TIME_BUDGET'});continue
        parent=live[pa];role=parent.evaluations[0].hypothesis.role_bindings[index];ev=[]
        for side in ('start','end'):
            ep=getattr(role,side+'_boundary')
            bar=next(b for b in ps.observations.bars if b.timestamp_utc==ep.timestamp_utc)
            eid=f'{pa}:role{index+1}:{side}:'+previous.metadata(cs)['context']['resolution']
            if eid not in evidence:
                evidence[eid]=previous.find_extremum_occurrences(ps,bar,ep.pivot_kind.value.lower(),cs,parent_result=parent,role_index=index,edge=side,cache=cache)
            ev.append((eid,evidence[eid]))
        count=len(ev[0][1].matches)*len(ev[1][1].matches)
        if count>plan['max_pairings_per_link'] or pairings+count>plan['max_total_pairings']:
            doc['unvisited_links'].append({'parent':pa,'role':index+1,'child':ca,'reason':'PAIRING_BUDGET','required_pairings':count});continue
        pairings+=count
        link=previous.link_observations(parent,index,live[ca],ev[0][1],ev[1][1],max_pairings=plan['max_pairings_per_link'])
        links.append(link);p=parent.evaluations[0];c=live[ca].evaluations[0]
        doc['links'].append({'link_id':f'{pa}:role{index+1}=>{ca}','parent_alias':pa,'child_alias':ca,'role_number':index+1,
            'parent_hypothesis_id':p.hypothesis.hypothesis_id,'parent_binding_id':p.hypothesis.five_slot_view.binding.binding_id,
            'parent_subject':old.p.plain(p.hypothesis.generated_candidate.subject),
            'child_hypothesis_id':c.hypothesis.hypothesis_id,'child_binding_id':c.hypothesis.five_slot_view.binding.binding_id,
            'child_subject':old.p.plain(c.hypothesis.generated_candidate.subject),'start_evidence_id':ev[0][0],'end_evidence_id':ev[1][0],
            'relationship':link.relationship,'limitations':list(link.limitations),
            'pairings':[{'start_bar':a.timestamp_utc.isoformat(),'end_bar':b.timestamp_utc.isoformat(),'state':state,'child_start_corresponds':left,'child_end_corresponds':right} for a,b,state,left,right in link.pairings],
            'p004_rejected':link.p004_rejected,'surviving_observational_link':link.surviving_observational_link,
            'complete_subdivision':False,'kernel_ancestry':False})
        if len(links)%25==0:print('Checked links '+str(len(links)),flush=True)
    previous.validate_observational_graph(tuple(links),max_links=plan['max_links'])
    doc['occurrence_evidence']=[prior.evidence_row(k,v) for k,v in evidence.items()]
    doc['link_budget']={'planned':len(planned),'selected':len(selected),'examined':len(links),
        'unvisited_selection':len(planned)-len(selected),'unvisited_execution':len(doc['unvisited_links']),'pairings':pairings}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=PACK)
    build(parser.parse_args().output)
