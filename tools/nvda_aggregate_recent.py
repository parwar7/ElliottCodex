"""Frozen aggregate occurrence audit and independently issued recent scopes."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import nvda_digital_multidegree as old
from elliott_runtime.market_data.aggregate_extremum import (
    find_extremum_occurrences, occurrence_envelope, metadata, digest, observation_identities,
)
from elliott_runtime.market_data.geometric_pivots import GeometricPivotDiscoveryRequest, discover_geometric_pivots
from elliott_runtime.analysis.normal_impulse_partial_evaluation import validate_normal_impulse_partial_evaluation_result

STAGE='NVDA-AGGREGATE-EXTREMUM-TIME-EVIDENCE-AND-RECENT-ANALYSIS-V1'
PACK=old.ROOT/'kernel_reviews'/STAGE
BASE='5886c05c4ee40664577128bc7d58618dca253e5c'


def integrity():
    manifest=old.read(old.PACK/'REVIEW_manifest.json')
    assert old.hash_file(old.PACK/'REVIEW_manifest.json')=='2538c3c9d17e5cee965d6a368574b70405d589a81698bbbdfcde75cca6d7fdbe'
    for key,root in [('files',old.PACK),('implementation_files',old.ROOT)]:
        for entry in manifest[key]:
            path=root/entry['path'];assert old.hash_file(path)==entry['sha256'] and path.stat().st_size==entry['bytes'],path
    return old.verify_integrity()


def evidence_row(identifier,e):
    e.validated();a=metadata(e.aggregate);f=metadata(e.finer)
    def occurrence(bar):
        bounds=occurrence_envelope(e.finer,bar)
        return {'bar_timestamp':bar.timestamp_utc.isoformat(),'price':getattr(bar,e.price_field),
                'price_field':e.price_field,'represented_ratio':old.p.plain(old.Fraction(getattr(bar,e.price_field))),
                'source_hash':e.finer.observations.provenance.source_sha256,'bar_provenance':old.p.plain(bar.provenance),
                'occurrence_envelope':old.p.plain(bounds),'exact_extremum_instant':None,'orthodox_endpoint':False}
    parent=e.parent_result.evaluations[0].hypothesis if e.parent_result else None
    return {'evidence_id':identifier,'original_bar_timestamp':e.aggregate_bar.timestamp_utc.isoformat(),
            'original_price':getattr(e.aggregate_bar,e.price_field),'price_field':e.price_field,
            'aggregate_source_hash':e.aggregate.observations.provenance.source_sha256,
            'aggregate_resolution':a['context']['resolution'],'finer_resolution':f['context']['resolution'],
            'finer_source_hash':e.finer.observations.provenance.source_sha256,
            'interval_evidence':old.p.plain(e.interval_evidence),'status':e.status,'limitations':list(e.limitations),
            'examined_rows':len(e.examined),'occurrences':[occurrence(b) for b in e.matches],
            'capture_times':[a['captured_at_utc'],f['captured_at_utc']],
            'original_parent_hypothesis_id':parent.hypothesis_id if parent else None,
            'original_binding_id':parent.five_slot_view.binding.binding_id if parent else None,
            'original_parent_subject':old.p.plain(parent.generated_candidate.subject) if parent else None,
            'role_index':e.role_index,'edge':e.edge,'family_authority':False,'wave_completion':False}


def _geometry_identities(snapshot,config,bars,discovery):
    originals=observation_identities(snapshot)+(config,bars,discovery)+bars
    if discovery is not None:
        originals+=(discovery.input_observations,discovery.config,discovery.scoped_bars,discovery.pivots,
                    discovery.provenance_refs,discovery.diagnostics)+discovery.pivots
        originals+=tuple(p.discovery_parameters for p in discovery.pivots)+tuple(p.provenance_refs for p in discovery.pivots)
    return originals


def geometry_window(snapshot,start,end,config,cache):
    key=(id(snapshot),start,end,id(config))
    if key in cache:
        original,parameters,bars,discovery,fingerprint,identities=cache[key]
        current=_geometry_identities(snapshot,config,bars,discovery)
        if original is not snapshot or parameters is not config or len(current)!=len(identities) or any(a is not b for a,b in zip(current,identities)) or digest((snapshot,config,bars,discovery))!=fingerprint:
            raise ValueError('Stale/substituted geometry cache')
        return bars,discovery
    bars=tuple(b for b in snapshot.observations.bars if start<=b.timestamp_utc.date().isoformat()<end)
    if len(bars)>4000:raise ValueError('Declared bar cap exceeded')
    identifier='aggregate-recent-geometry:'+old.hashlib.sha256((snapshot.observations.provenance.source_sha256+start+end+repr(config)).encode()).hexdigest()[:24]
    discovery=discover_geometric_pivots(GeometricPivotDiscoveryRequest(identifier,snapshot.observations,config,(STAGE,),bars)) if bars else None
    cache[key]=(snapshot,config,bars,discovery,digest((snapshot,config,bars,discovery)),_geometry_identities(snapshot,config,bars,discovery))
    return bars,discovery


def evaluate_independent(identifier,snapshot,discovery,selected,evidence,kernel):
    """Observational context only; subject/binding are fresh, never old parents."""
    for e in evidence:
        e.validated()
        if e.finer is not snapshot:raise ValueError('Foreign context snapshot')
    subject=old.p.AnalyzedWaveSubject(identifier+':independent-subject',snapshot.observations.provenance.source_sha256)
    result=old.evaluate_scope(identifier,subject,snapshot.observations,discovery,selected,snapshot.observations.provenance.ingested_at_utc,kernel)
    validate_normal_impulse_partial_evaluation_result(result)
    item=result.evaluations[0]
    assert item.hypothesis.generated_candidate.subject is subject
    assert item.hypothesis.generated_candidate.source_observations is snapshot.observations
    for e in evidence:
        e.validated()
        if e.parent_result:
            parent=e.parent_result.evaluations[0].hypothesis
            if item.hypothesis.five_slot_view.binding is parent.five_slot_view.binding or subject is parent.generated_candidate.subject:
                raise ValueError('Old ancestry transferred')
    return result


def run(output=PACK):
    output=Path(output);plan=old.read(PACK/'search_plan.json');old.save(output/'pre_integrity.json',integrity())
    snapshots,raw=old.tv.load_inputs();kernel=old.p.MethodologyKernel(Path('C:/ElliottCodex/Brain_LOCKED'))
    jobs,_,_=old.root_plan(snapshots['1M'].observations,old.read(old.PACK/'search_plan.json'))
    originals={}
    for identifier,discovery,points,kind in jobs:
        if identifier not in ('M1','M2'):continue
        subject=old.p.AnalyzedWaveSubject(old.STAGE+':'+identifier,snapshots['1M'].observations.provenance.source_sha256)
        originals[identifier]=old.evaluate_scope(old.STAGE+':'+identifier,subject,snapshots['1M'].observations,discovery,points,snapshots['1M'].observations.provenance.ingested_at_utc,kernel)
    original_fingerprints={key:digest(value) for key,value in originals.items()}
    july=next(b for b in snapshots['1M'].observations.bars if b.timestamp_utc.date().isoformat()=='2026-07-01')
    targets=[]
    for name,parent in originals.items():
        boundary=parent.evaluations[0].hypothesis.role_bindings[4].end_boundary
        bar=next(b for b in snapshots['1M'].observations.bars if b.timestamp_utc==boundary.timestamp_utc)
        targets.append((name,snapshots['1M'],bar,'high',parent))
    targets.append(('JULY',snapshots['1M'],july,'low',None))
    evidence=[];live_evidence={};cache={}
    for name,snapshot,bar,field,parent in targets:
        for res in plan['finer_resolutions']:
            eid=name+':'+res
            e=find_extremum_occurrences(snapshot,bar,field,snapshots[res],parent_result=parent,role_index=4 if parent else None,edge='end' if parent else None,cache=cache)
            live_evidence[eid]=e;evidence.append(evidence_row(eid,e))
            if res=='1D':
                for number,match in enumerate(e.matches):
                    for finer_res in ('240','60','15'):
                        nested_id=eid+':occurrence:'+str(number)+':'+finer_res
                        nested=find_extremum_occurrences(snapshots['1D'],match,field,snapshots[finer_res],cache=cache)
                        row=evidence_row(nested_id,nested);row['aggregate_occurrence_context']=eid
                        evidence.append(row);live_evidence[nested_id]=nested
    old.save(output/'occurrence_evidence.json',evidence)
    # All geometry and selection dispositions are captured before any NEW recent P004/P005 evaluation.
    contexts={'MAY':['M1'],'MAY_JULY':['M1','JULY'],'JULY':['JULY'],'RECENT':['JULY','M2']}
    geometry=old.geometry(plan['geometry_width']);geo_cache={};searches=[];pending=[];total_windows=0
    for label,start,end in plan['search_windows']:
        for res in plan['finer_resolutions']:
            bars,discovery=geometry_window(snapshots[res],start,end,geometry,geo_cache)
            pivots=discovery.pivots if discovery else ();windows=[];eligible=[]
            for i in range(max(0,len(pivots)-5)):
                domain=old.movement_domain(tuple(p.observed_price for p in pivots[i:i+6]));total_windows+=1
                if total_windows>plan['max_total_windows_examined']:raise ValueError('Aggregate preflight geometry budget exceeded')
                if domain['eligible']:eligible.append(i)
                windows.append({'start':i,'domain':domain,'pivot_ids':[p.pivot_id for p in pivots[i:i+6]],'disposition':'UNVISITED_BUDGET' if domain['eligible'] else 'DOMAIN_EXCLUDED'})
            selected=list(dict.fromkeys([eligible[0],eligible[-1]])) if eligible else []
            for i in selected:windows[i]['disposition']='SELECTED'
            sid=label+':'+res
            search={'id':sid,'window':[start,end],'resolution':res,'bars':len(bars),'pivots':len(pivots),'windows':windows,'selected':selected,
                    'reason':'SCOPES_SELECTED' if selected else 'NO_OBSERVATIONS' if not bars else 'INSUFFICIENT_PIVOTS' if len(pivots)<6 else 'NO_SEQUENCE_IN_DOMAIN',
                    'first_available':snapshots[res].observations.bars[0].timestamp_utc.isoformat(),'source_hash':snapshots[res].observations.provenance.source_sha256,
                    'context_evidence_ids':[n+':'+res for n in contexts[label]],'attachment':'OBSERVATIONAL_CONTEXT_ONLY_NO_VALIDATED_PARENT_CHILD_ATTACHMENT','results':[]}
            searches.append(search)
            for i in selected:pending.append((search,snapshots[res],discovery,i))
    assert len(searches)<=plan['max_searches'] and len(pending)<=plan['max_hypotheses']
    old.save(output/'selection_before_evaluation.json',{'plan_sha256':old.hash_file(PACK/'search_plan.json'),'searches':searches,'planned_hypotheses':len(pending),'total_windows':total_windows})
    doc={'stage':STAGE,'hypotheses':[],'nodes':[],'searches':searches,'inventories':[11,7,0,0],'scenario_ranking':None,'occurrence_evidence':evidence,'old_ancestry_modified':False}
    live=[]
    for search,snapshot,discovery,i in pending:
        identifier=search['id']+':S'+str(i);print('Evaluate '+identifier,flush=True)
        linked=[live_evidence[n] for n in search['context_evidence_ids']]
        result=evaluate_independent(STAGE+':'+identifier,snapshot,discovery,discovery.pivots[i:i+6],linked,kernel)
        row,nodes=old.export_hypothesis(result,identifier,snapshot.observations)
        row['context_evidence_ids']=search['context_evidence_ids'];row['attachment']=search['attachment']
        row['old_parent_id']=None;doc['hypotheses'].append(row);doc['nodes']+=nodes;search['results'].append(identifier);live.append(result)
    for result in live:validate_normal_impulse_partial_evaluation_result(result)
    for e in live_evidence.values():e.validated()
    for key,value in originals.items():
        validate_normal_impulse_partial_evaluation_result(value);assert digest(value)==original_fingerprints[key]
    for snapshot,parameters,bars,discovery,fingerprint,identities in geo_cache.values():
        assert digest((snapshot,parameters,bars,discovery))==fingerprint
        assert all(a is b for a,b in zip(_geometry_identities(snapshot,parameters,bars,discovery),identities))
    doc['totals']={k:dict(Counter(h[k]['status'] for h in doc['hypotheses'])) for k in ('p004','p005')}
    doc['totals']['p004_rejected_despite_p005']=sum(h['p004']['fatal'] and h['p005']['status']=='SUFFICIENT_CONDITION_ESTABLISHED' for h in doc['hypotheses'])
    doc['audit']=old.audit_hierarchy(doc,snapshots)
    doc['original_parent_receipt']={key:{'fingerprint_unchanged':digest(value)==original_fingerprints[key],'hypothesis_id':value.evaluations[0].hypothesis.hypothesis_id,'binding_id':value.evaluations[0].hypothesis.five_slot_view.binding.binding_id} for key,value in originals.items()}
    old.save(output/'canonical_analysis.json',doc)
    print({'hypotheses':len(live),'evidence':len(evidence),'totals':doc['totals'],'audit':doc['audit']})
    return doc


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=PACK)
    run(parser.parse_args().output)
