"""Bounded analyst proposals and factual measurements; delegates all methodology."""
from collections import Counter
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
import argparse
import json

import nvda_coherent_report as previous
import nvda_aggregate_recent as aggregate
from elliott_runtime.market_data.geometric_pivots import GeometricPivotDiscoveryRequest, discover_geometric_pivots
from elliott_runtime.analysis.geometric_swing_search import movement_domain
from elliott_runtime.analysis.normal_impulse_partial_evaluation import validate_normal_impulse_partial_evaluation_result
from elliott_runtime.market_data.aggregate_extremum import find_extremum_occurrences
from elliott_runtime.analysis.observational_hierarchy import link_observations, validate_observational_graph

old = previous.old
STAGE = 'NVDA-TSLA-STYLE-SOURCE-LOCKED-ANALYSIS-V1'
PACK = old.ROOT/'kernel_reviews'/STAGE
PRIOR_HASH = '0bed549ef5c6f625df6263ad1c39006b27d1c53a35409fad404337514adec10b'


def integrity():
    path = previous.PACK/'REVIEW_manifest.json'
    if old.hash_file(path) != PRIOR_HASH:
        raise ValueError('Coherent baseline changed')
    for key, root in (('files', previous.PACK), ('implementation_files', old.ROOT)):
        for e in old.read(path)[key]:
            p = root/e['path']
            if p.stat().st_size != e['bytes'] or old.hash_file(p) != e['sha256']:
                raise ValueError('Previous artifact changed: '+str(p))
    return previous.integrity()


def select_regions(discovery, regions):
    """Declared calendar regions; extreme selection is operational, never a rule."""
    if type(regions) is not tuple or len(regions) != 6:
        raise ValueError('Six explicitly declared regions required')
    selected = []
    for start, end, kind in regions:
        if start >= end or kind not in ('HIGH', 'LOW'):
            raise ValueError('Invalid region')
        points = [p for p in discovery.pivots if start <= p.timestamp_utc.date().isoformat() < end and p.pivot_kind.value == kind]
        if not points:
            return (), 'MISSING_ORIGINAL_PIVOT'
        selected.append(max(points, key=lambda p: (p.observed_price if kind == 'HIGH' else -p.observed_price, p.timestamp_utc)))
    points = tuple(selected)
    if len({id(p) for p in points}) != 6 or any(a.timestamp_utc >= b.timestamp_utc for a,b in zip(points,points[1:])):
        raise ValueError('Duplicate or unordered selected observations')
    if not movement_domain(tuple(p.observed_price for p in points))['eligible']:
        return points, 'NONALTERNATING_OPERATIONAL_DOMAIN'
    return points, 'PLANNED'


def regions(dates):
    return tuple((date, end, 'LOW' if i%2==0 else 'HIGH') for i,(date,end) in enumerate(dates))


ROOT_COMMON = [('2002-10','2002-11'),('2007-10','2007-11'),('2008-11','2008-12'),('2021-11','2021-12'),('2022-10','2022-11')]
PLANS = (
    ('H-MAY','1M',regions(ROOT_COMMON+[('2026-05','2026-06')])),
    ('H-SEP','1M',regions(ROOT_COMMON+[('2026-09','2026-10')])),
    ('EARLY-W','1W',regions([('2002-09','2002-11'),('2003-05','2003-08'),('2004-07','2004-10'),('2006-04','2006-06'),('2006-06','2006-09'),('2007-09','2007-12')])),
    ('MIDDLE-W','1W',regions([('2008-10','2008-12'),('2011-01','2011-04'),('2012-10','2013-01'),('2018-09','2018-11'),('2018-11','2019-02'),('2021-10','2021-12')])),
    ('RECENT-W-A','1W',regions([('2022-09','2022-11'),('2023-07','2023-10'),('2023-09','2023-12'),('2024-05','2024-08'),('2024-07','2024-10'),('2026-04','2026-07')])),
    ('RECENT-W-B','1W',regions([('2022-09','2022-11'),('2023-07','2023-10'),('2023-09','2023-12'),('2024-12','2025-03'),('2025-03','2025-06'),('2026-04','2026-07')])),
    ('MIDDLE-D','1D',regions([('2008-11','2008-12'),('2011-02','2011-03'),('2012-11','2012-12'),('2018-10','2018-11'),('2018-12','2019-01'),('2021-11','2021-12')])),
    ('RECENT-D','1D',regions([('2022-10','2022-11'),('2023-08','2023-09'),('2023-10','2023-11'),('2025-01','2025-02'),('2025-04','2025-05'),('2026-05','2026-06')])),
)


def plan(snapshots):
    discoveries = {}; jobs = []; notes = []
    for alias, res, windows in PLANS:
        if res not in discoveries:
            observations = snapshots[res].observations
            discoveries[res] = discover_geometric_pivots(GeometricPivotDiscoveryRequest(STAGE+':geometry:'+res, observations, old.geometry(2),('ANALYST_REGION_PROPOSAL_NOT_ENDPOINT_AUTHORITY',)))
        d = discoveries[res]; points, state = select_regions(d, windows)
        notes.append({'alias': alias, 'resolution': res, 'regions': windows, 'status': state,
                      'source_hash': d.input_observations.provenance.source_sha256,
                      'discovery_pivots': len(d.pivots), 'selected': old.p.plain(points),
                      'not_selected_pivots': len(d.pivots)-len(points),
                      'selection_authority': 'PROJECT_OPERATIONAL_POLICY_NOT_ELLIOTT_SIGNIFICANCE'})
        if state == 'PLANNED': jobs.append((alias,res,d,points))
    if len(jobs)>18: raise ValueError('Declared cap exceeded')
    return jobs, notes


def factual_measures(h, snapshot):
    """Descriptive arithmetic only. No fib score, tolerance, or family assertion."""
    if h['source_response_sha256'] != snapshot.observations.provenance.source_sha256:
        raise ValueError('Foreign snapshot')
    lengths=[]; windows=[]
    by_time={b.timestamp_utc.isoformat():b for b in snapshot.observations.bars}
    for i in range(5):
        a,b=h['endpoints'][2*i:2*i+2]
        for e in (a,b):
            bar=by_time[e['timestamp_utc']]
            if e['source_hash']!=snapshot.observations.provenance.source_sha256 or e['price_field'] not in ('high','low') or getattr(bar,e['price_field'])!=e['price']:
                raise ValueError('Foreign endpoint or substituted field')
        delta=abs(Fraction(b['price'])-Fraction(a['price']))
        if not delta: raise ValueError('Zero-length descriptive denominator')
        lengths.append(delta)
        # Aggregate endpoint bars cannot apportion volume by unknown extremum time.
        bars=[r for r in snapshot.observations.bars if a['timestamp_utc']<r.timestamp_utc.isoformat()<b['timestamp_utc']]
        usable=[r for r in bars if r.volume is not None]
        peak=max((r.volume for r in usable),default=None)
        windows.append({'role':i+1,'bar_label_window_open':[a['timestamp_utc'],b['timestamp_utc']],
                        'interior_bars':len(bars),'missing_volume_bars':len(bars)-len(usable),
                        'peak_volume':peak,'peak_occurrences':[previous.observed(r,'volume',snapshot) for r in usable if r.volume==peak],
                        'volume_interpretation':'NEUTRAL_ADJUSTMENT_AND_EQUAL_DEGREE_UNRESOLVED',
                        'endpoint_bars_excluded':True})
    ratios={key:old.p.plain(lengths[i]/lengths[j]) for key,i,j in [('role2_over_role1',1,0),('role4_over_role3',3,2),('role3_over_role1',2,0),('role5_over_role1',4,0)]}
    return {'alias':h['display_id'],'hypothesis_id':h['hypothesis_id'],'basis':'ABSOLUTE_REPRESENTED_PRICE_DISTANCE_DESCRIPTIVE_NOT_P005',
            'source_hash':h['source_response_sha256'],'lengths':[old.p.plain(x) for x in lengths],
            'ratios':ratios,'ratio_decimal_display':{k:float(Fraction(v['numerator'],v['denominator'])) for k,v in ratios.items()},
            'tolerance':None,'fib_match_asserted':False,'target':None,'volume_windows':windows}


def run(output=PACK):
    output=Path(output)
    old.save(output/'pre_integrity.json',integrity())
    snapshots,raw=old.tv.load_inputs(); jobs,notes=plan(snapshots)
    old.save(output/'selection_before_evaluation.json',{'plans':notes,'max_evaluations':18,'actual_planned':len(jobs),'outcome_selection':False,'width':2,'equal_extreme':'LAST','no_new_capture':True,'no_exhaustive_search':True})
    live={}; doc={'stage':STAGE,'hypotheses':[],'nodes':[],'searches':[], 'links':[], 'occurrence_evidence':[], 'inventories':[11,7,0,0],'scenario_ranking':None,'family_validity':False}
    kernel=old.p.MethodologyKernel(Path('C:/ElliottCodex/Brain_LOCKED'))
    for alias,res,d,points in jobs:
        obs=snapshots[res].observations
        result=old.evaluate_scope(STAGE+':'+alias,old.p.AnalyzedWaveSubject(STAGE+':'+alias,obs.provenance.source_sha256),obs,d,points,obs.provenance.ingested_at_utc,kernel)
        validate_normal_impulse_partial_evaluation_result(result); live[alias]=result
        row,nodes=old.export_hypothesis(result,alias,obs)
        doc['hypotheses'].append(row);doc['nodes']+=nodes
        # Durable individual receipt means completed evaluations need not be repeated.
        old.save(output/'evaluations'/(alias+'.json'),row)
        print(alias,row['p004'],row['p005'],flush=True)
    links=[];cache={}
    for pa in ('H-MAY','H-SEP'):
        for index,ca in ((2,'MIDDLE-D'),(4,'RECENT-D')):
            parent=live[pa]; role=parent.evaluations[0].hypothesis.role_bindings[index]; ev=[]
            for side in ('start','end'):
                endpoint=getattr(role,side+'_boundary'); ps=snapshots['1M'];cs=snapshots['1D']
                bar=next(b for b in ps.observations.bars if b.timestamp_utc==endpoint.timestamp_utc)
                e=find_extremum_occurrences(ps,bar,endpoint.pivot_kind.value.lower(),cs,parent_result=parent,role_index=index,edge=side,cache=cache)
                eid=pa+':'+str(index+1)+':'+side;ev.append(e)
                doc['occurrence_evidence'].append(aggregate.evidence_row(eid,e))
            link=link_observations(parent,index,live[ca],*ev,max_pairings=64);links.append(link)
            doc['links'].append({'parent':pa,'parent_role':index+1,'child':ca,'parent_hypothesis_id':parent.evaluations[0].hypothesis.hypothesis_id,'child_hypothesis_id':live[ca].evaluations[0].hypothesis.hypothesis_id,
                                 'relationship':link.relationship,'surviving_observational_link':link.surviving_observational_link,'p004_rejected':link.p004_rejected,
                                 'pairings':[{'start':a.timestamp_utc.isoformat(),'end':b.timestamp_utc.isoformat(),'state':state,'same_start':left,'same_end':right} for a,b,state,left,right in link.pairings],
                                 'limitations':link.limitations,'kernel_ancestry':False,'complete_subdivision':False})
    validate_observational_graph(tuple(links),max_links=8)
    for result in live.values(): validate_normal_impulse_partial_evaluation_result(result)
    doc['audit']=old.audit_hierarchy(doc,snapshots)
    doc['totals']={k:dict(Counter(r[k]['status'] for r in doc['hypotheses'])) for k in ('p004','p005')}
    doc['measures']=[factual_measures(h,snapshots[next(res for alias,res,_ in PLANS if alias==h['display_id'])]) for h in doc['hypotheses']]
    doc['weekly_relationship_limit']='WEEKLY_OCCURRENCE_ENVELOPE_UNSUPPORTED_BY_EXISTING_LINK_CONTRACT; proposed context only, no manufactured live link'
    old.save(output/'analysis.json',doc)
    print(json.dumps({'totals':doc['totals'],'links':doc['links'],'audit':doc['audit']},default=str),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--plan',action='store_true');args=parser.parse_args()
    if args.plan:
        s,_=old.tv.load_inputs();_,notes=plan(s)
        for n in notes:print(n['alias'],n['status'],[(p['timestamp_utc'],p['observed_price']) for p in n['selected']])
    else:run()
