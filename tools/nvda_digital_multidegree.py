"""Frozen TradingView full-history search and exact partial component reporting.

No live retrieval; no methodology rules or authority-bearing deserialization.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path

import nvda_tradingview_replay as tv
import nvda_post_p005_experiment as p
import nvda_bounded_report as report
from elliott_runtime.analysis.normal_component_exploration import (
    evaluate_scope, prepare_component_search, plan_component, evaluate_component,
)
from elliott_runtime.analysis.geometric_swing_search import movement_domain

ROOT=Path(__file__).resolve().parents[1]
STAGE='NVDA-DIGITAL-MULTIDEGREE-ANALYSIS-AND-REPORT-V1'
PACK=ROOT/'kernel_reviews'/STAGE
PREVIOUS=tv.PACK

def read(path):return json.loads(path.read_text(encoding='utf-8'))
def hash_file(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,data):
    path=Path(path).resolve()
    if not path.is_relative_to(ROOT) or path.exists():raise ValueError('New Runtime artifact required')
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8',newline='\n') as f:json.dump(data,f,ensure_ascii=False,indent=2,allow_nan=False)

def verify_integrity():
    baseline=read(PREVIOUS/'REVIEW_manifest.json')
    assert hash_file(PREVIOUS/'REVIEW_manifest.json')=='8821c441cbb1e72bfe8d99f4474b781316ec9f18d3af82fffd344bc73f0beb03'
    for e in baseline['files']:
        path=PREVIOUS/e['path'];assert path.stat().st_size==e['bytes'] and hash_file(path)==e['sha256'],str(path)
    for e in baseline['implementation_files']:
        path=ROOT/e['path'];assert path.stat().st_size==e['bytes'] and hash_file(path)==e['sha256'],str(path)
    receipt={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'packages':[],'mismatches':[]}
    for package in read(PREVIOUS/'final_integrity.json')['packages']:
        root=Path(package['root']);manifest=root/('PACKAGE_MANIFEST.json' if root.name=='Brain_LOCKED' else 'SOURCE_MANIFEST.json')
        assert hash_file(manifest)==package['manifest_sha256']
        entries=[]
        for e in package['entries']:
            path=root/e['path'];assert path.stat().st_size==e['bytes'] and hash_file(path)==e['sha256'],str(path)
            entries.append(e)
        receipt['packages'].append(dict(package,entries=entries))
    assert Path('C:/ElliottCodex/Brain_LOCKED/VERSION').read_text().strip()=='0.1.0'
    receipt.update(version='0.1.0',policy_sha256=hash_file(Path('C:/ElliottCodex/Brain_LOCKED/docs/elliott/SOURCE_POLICY.md')),prior_baseline_files_verified=len(baseline['files'])+len(baseline['implementation_files']))
    return receipt

def geometry(width):
    return p.GeometricPivotDiscoveryConfig(p.GeometricPivotDiscoveryMethod.WINDOWED_LOCAL_EXTREMA,width,width,p.EqualExtremePolicy.LAST,True)

def root_plan(data,config):
    jobs=[];coverage=[];discoveries={}
    for width in config['monthly_geometry_widths']:
        discovery=p.discover_geometric_pivots(p.GeometricPivotDiscoveryRequest(STAGE+':monthly:'+str(width),data,geometry(width),(STAGE,)))
        discoveries[width]=discovery
        windows=[];regional=[[] for _ in config['regions']]
        for i in range(max(0,len(discovery.pivots)-5)):
            points=discovery.pivots[i:i+6];domain=movement_domain(tuple(x.observed_price for x in points))
            region=next((j for j,(a,b) in enumerate(config['regions']) if a<=points[0].timestamp_utc.year and points[-1].timestamp_utc.year<=b),None)
            if domain['eligible'] and region is not None:regional[region].append(i)
            windows.append({'start':i,'region':region,'domain':domain,'pivot_ids':[x.pivot_id for x in points],'from':points[0].timestamp_utc.isoformat(),'to':points[-1].timestamp_utc.isoformat(),'disposition':'DOMAIN_EXCLUDED' if not domain['eligible'] else 'CROSS_REGION_EXCLUDED' if region is None else 'UNVISITED_BUDGET'})
        for region,indices in enumerate(regional):
            for i in list(dict.fromkeys([indices[0],indices[-1]])) if indices else []:
                windows[i]['disposition']='SELECTED'
                jobs.append((f'R{width}-{region}-{i}',discovery,discovery.pivots[i:i+6],'REGIONAL_SCOPE'))
        coverage.append({'width':width,'bars_inspected':len(data.bars),'pivots':p.plain(discovery.pivots),'windows':windows,'boundary':'First bar is a history boundary, never a wave origin','exhaustive':False})
    assert len(jobs)<=config['max_regional_roots']
    macro=config['macro_reassessment'];discovery=discoveries[macro['geometry_width']];macro_notes=[]
    for number,final in enumerate(macro['final_regions'],1):
        points=[];reason=None
        for start,end,kind in macro['common_regions']+[final]:
            candidates=[x for x in discovery.pivots if start<=x.timestamp_utc.date().isoformat()<end and (kind=='LATEST_ANY_KIND' or x.pivot_kind.value==kind)]
            if not candidates:reason='NO_ORIGINAL_GEOMETRIC_MEMBER_IN_DECLARED_REGION';break
            chosen=max(candidates,key=lambda x:(x.timestamp_utc,)) if kind=='LATEST_ANY_KIND' else sorted(candidates,key=lambda x:(x.observed_price if kind=='HIGH' else -x.observed_price,x.timestamp_utc))[-1]
            points.append(chosen)
        domain=movement_domain(tuple(x.observed_price for x in points)) if len(points)==6 else None
        if domain and not domain['eligible']:reason='NONALTERNATING_MACRO_PROPOSAL'
        macro_notes.append({'id':f'M{number}','reason':reason or 'PLANNED','selected':p.plain(points),'domain':domain,'skipped_pivots':len(discovery.pivots)-len(points),'selection_authority':'OPERATIONAL_ANALYST_REGION_PROPOSAL'})
        if reason is None:jobs.append((f'M{number}',discovery,tuple(points),'MACRO_REASSESSMENT'))
    return jobs,coverage,macro_notes

def endpoint_row(endpoint,snapshot):
    return dict(endpoint,source_hash=snapshot.provenance.source_sha256,precision='EXACT_REPRESENTED_FLOAT',orthodox_endpoint_authority=False)

def export_hypothesis(result, identifier, data, parent_role_id=None, level=0):
    rows=report.normal_rows(result,'root' if parent_role_id is None else 'component',identifier)
    if len(rows)!=1:raise ValueError('One result per explicit scope expected')
    row=rows[0];row.update(display_id=identifier,parent_node_id=parent_role_id,level=level,relative_degree='PROPOSED_CHILD_OF_PARENT_ONLY' if parent_role_id else 'ROOT_DEGREE_UNRESOLVED',degree='DEGREE_UNRESOLVED')
    row['endpoints']=[endpoint_row(e,data) for e in row['endpoints']]
    end=row['endpoints'][-1]['timestamp_utc'];trailing=[b for b in data.bars if b.timestamp_utc.isoformat()>end]
    row['current_position']={'engine':'CURRENT_WAVE_POSITION_UNRESOLVED','last_endpoint':end,'last_observation':data.bars[-1].timestamp_utc.isoformat(),'trailing_bars':len(trailing),'developing_endpoint':row['endpoints'][-1]['pivot_state']=='DEVELOPING','completion_authority':False}
    nodes=[{'node_id':identifier,'parent_id':parent_role_id,'kind':'NORMAL_IMPULSE_HYPOTHESIS','hypothesis_id':row['hypothesis_id'],'proposed_role':'partial five-slot hypothesis','relative_degree':row['relative_degree'],'degree_status':'DEGREE_UNRESOLVED','resolution':row['timeframe'],'start':row['endpoints'][0],'end':row['endpoints'][-1],'status':row['report_status'],'unresolved':row['unresolved_reasons'],'evaluations':{'p004':row['p004'],'p005':row['p005']},'family_validity':False}]
    for i in range(5):
        a,b=row['endpoints'][2*i:2*i+2]
        nodes.append({'node_id':identifier+'.'+str(i+1),'parent_id':identifier,'kind':'PROPOSED_ROLE','hypothesis_id':row['hypothesis_id'],'proposed_role':str(i+1),'relative_degree':'DIRECT_CHILD_PROPOSAL_ONLY','degree_status':'DEGREE_UNRESOLVED','resolution':row['timeframe'],'start':a,'end':b,'status':'ANCESTOR_REJECTED' if row['p004']['fatal'] else 'INTERNALS_UNRESOLVED','unresolved':['INTERNAL_FAMILY_PROOF_UNAVAILABLE','NO_TERMINAL_BASE_CASE'],'evaluation_scope':'Containing hypothesis only; this role has no independent P004/P005 claim','family_validity':False})
    return row,nodes

def audit_hierarchy(doc, snapshots):
    by_id={n['node_id']:n for n in doc['nodes']}
    if len(by_id)!=len(doc['nodes']):raise ValueError('Duplicate node IDs')
    source={s.observations.provenance.source_sha256:s.observations for s in snapshots.values()}
    prices=0
    for n in doc['nodes']:
        if n['family_validity'] or n['degree_status']!='DEGREE_UNRESOLVED':raise ValueError('False authority')
        for e in (n['start'],n['end']):
            obs=source[e['source_hash']];bar=next(b for b in obs.bars if b.timestamp_utc.isoformat()==e['timestamp_utc'])
            if getattr(bar,e['price_field'])!=e['price'] or p.plain(Fraction(e['price']))!=e['represented_ratio'] or p.plain(bar.provenance)!=e['bar_provenance']:raise ValueError('Foreign snapshot/operand')
            prices+=1
        if n['parent_id']:
            parent=by_id[n['parent_id']]
            if not parent['start']['timestamp_utc']<=n['start']['timestamp_utc']<=n['end']['timestamp_utc']<=parent['end']['timestamp_utc']:raise ValueError('Child outside parent')
        if n['kind']=='NORMAL_IMPULSE_HYPOTHESIS':
            rejected=n['evaluations']['p004']['fatal']
            if rejected!=(n['status']=='REJECTED_EXACT_HYPOTHESIS_P004'):raise ValueError('P004 rejection concealed')
    for item in doc['searches']:
        if item['reason']=='PARENT_REJECTED_P004' and item['children']:raise ValueError('Rejected parent expanded')
    return {'nodes':len(by_id),'endpoint_fields_reconciled':prices,'links':sum(n['parent_id'] is not None for n in doc['nodes']),'max_executed_child_level':max((r['level'] for r in doc['hypotheses']),default=0),'family_certificates':0,'result':'PASS'}

def run(output=PACK):
    output=Path(output);config=read(PACK/'search_plan.json')
    save(output/'pre_integrity.json',verify_integrity())
    snapshots,_=tv.load_inputs();quality=tv.quality();data={k:s.observations for k,s in snapshots.items()}
    jobs,coverage,macro=root_plan(data['1M'],config)
    save(output/'planned_search.json',{'config_sha256':hash_file(PACK/'search_plan.json'),'coverage':coverage,'macro':macro,'jobs':[{'id':i,'kind':kind,'pivots':p.plain(points)} for i,d,points,kind in jobs]})
    doc={'stage':STAGE,'config':config,'input_baseline':str(PREVIOUS.relative_to(ROOT)),'hypotheses':[],'nodes':[],'searches':[],'macro':macro,'inventories':[11,7,0,0],'data_quality':quality,'scenario_ranking':None}
    kernel=p.MethodologyKernel(Path('C:/ElliottCodex/Brain_LOCKED'));live=[];queue=[];executed=0
    for identifier,discovery,points,kind in jobs:
        print('Root '+identifier,flush=True)
        result=evaluate_scope(STAGE+':'+identifier,p.AnalyzedWaveSubject(STAGE+':'+identifier,data['1M'].provenance.source_sha256),data['1M'],discovery,points,data['1M'].provenance.ingested_at_utc,kernel)
        row,nodes=export_hypothesis(result,identifier,data['1M']);row['search_kind']=kind
        doc['hypotheses'].append(row);doc['nodes']+=nodes;live.append(result);executed+=1
        if kind=='MACRO_REASSESSMENT':
            for role in (0,2,4):queue.append((result,identifier,role,1,0))
    cache={};geo=geometry(config['child_geometry_width']);searched=0
    while queue:
        parent,parent_id,role,level,resolution_index=queue.pop(0)
        identifier=parent_id+'.'+str(role+1)+':L'+str(level)+':O'+str(resolution_index)
        if searched>=config['max_component_searches'] or executed+2>config['max_executable_normal_hypotheses']:
            doc['searches'].append({'id':identifier,'parent_node_id':parent_id+'.'+str(role+1),'reason':'AGGREGATE_BUDGET_EXHAUSTED','children':[]});continue
        if parent.evaluations[0].p004_result.fatal_to_candidate:
            doc['searches'].append({'id':identifier,'parent_node_id':parent_id+'.'+str(role+1),'reason':'PARENT_REJECTED_P004','children':[]});continue
        res=config['child_observation_sequence'][resolution_index]
        print('Component '+identifier+' on '+res,flush=True)
        search=prepare_component_search(parent,0,role,data[res],geo,cache);planned=plan_component(search)
        result=evaluate_component(search,data[res].provenance.ingested_at_utc,kernel,STAGE+':'+identifier)
        searched+=1;live.append(result)
        record=dict(planned,id=identifier,parent_node_id=parent_id+'.'+str(role+1),resolution=res,source_hash=data[res].provenance.source_sha256,children=[])
        for number,child in enumerate(result.children,1):
            child_id=identifier+':S'+str(number)
            row,nodes=export_hypothesis(child,child_id,data[res],parent_id+'.'+str(role+1),level)
            row['composition_summary']=result.compositions[number-1].composed_summary.value
            doc['hypotheses'].append(row);doc['nodes']+=nodes;record['children'].append(child_id);executed+=1
        doc['searches'].append(record)
        if result.children and level<config['max_child_levels'] and resolution_index+1<len(config['child_observation_sequence']):
            queue.append((result.children[-1],record['children'][-1],4,level+1,resolution_index+1))
        elif not result.children and resolution_index+1<len(config['child_observation_sequence']):
            queue.append((parent,parent_id,role,level,resolution_index+1))
            record['retry']='SAME_EXACT_PARENT_ROLE_FINER_RESOLUTION_NOT_NEW_DEGREE'
        else:record['next_level_stop']='DECLARED_DEPTH_OR_RESOLUTION_BUDGET_NOT_TERMINALITY'
    for item in live:
        if hasattr(item,'validated'):item.validated()
        else:report.validate_normal_impulse_partial_evaluation_result(item)
    doc['geometry_cache_entries']=len(cache)
    doc['totals']={k:dict(Counter(r[k]['status'] for r in doc['hypotheses'])) for k in ('p004','p005')}
    doc['totals']['p004_rejected_despite_p005']=sum(r['p004']['fatal'] and r['p005']['status']=='SUFFICIENT_CONDITION_ESTABLISHED' for r in doc['hypotheses'])
    doc['audit']=audit_hierarchy(doc,snapshots)
    save(output/'hierarchy.json',doc)
    print(json.dumps({'totals':doc['totals'],'audit':doc['audit']}),flush=True)
    return doc

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=PACK)
    run(parser.parse_args().output)
