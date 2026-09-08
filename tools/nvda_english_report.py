"""English evidence-only report/export. Does not execute or rank hypotheses."""
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
import argparse

import nvda_english_analysis as analysis
import nvda_digital_multidegree_report as digital_report

old=analysis.old
PACK=analysis.PACK
display=analysis.previous.display
LOCAL=('D2026:1D:N6:S38','RECENT:60:N6:S43','TAIL:15:N6:S10',
       'H4CONTEXT:240:N4:S31:SINGLE_ZIGZAG','H4CONTEXT:240:N4:S31:FLAT')


def reconcile_cases(cases,snapshots,raw):
    source={s.observations.provenance.source_sha256:{datetime.fromtimestamp(r['value'][0],timezone.utc).isoformat():r['value'] for r in raw[k]['rows']} for k,s in snapshots.items()}
    fields={'high':2,'low':3};checked=0
    if len({h['display_id'] for h in cases})!=len(cases):raise ValueError('Duplicate context aliases')
    for h in cases:
        if h['authority'].get('family_validity') or h.get('family_validity'):
            raise ValueError('No family authority')
        if h['p004'] is not None and h['p004']['fatal']:
            raise ValueError('Rejected hypothesis cannot be a surviving display case')
        for e in h['endpoints']:
            if e['source_hash']!=h['source_response_sha256'] or e['orthodox_endpoint_authority']:
                raise ValueError('Foreign or promoted endpoint')
            value=source[e['source_hash']][e['timestamp_utc']][fields[e['price_field']]]
            if Fraction(value)!=Fraction(e['price']) or old.p.plain(Fraction(value))!=e['represented_ratio']:
                raise ValueError('Raw represented endpoint mismatch')
            checked+=1
        for a,b in zip(h['endpoints'][1:-1:2],h['endpoints'][2::2]):
            if any(a[k]!=b[k] for k in ('pivot_id','timestamp_utc','price_field','price','source_hash')):
                raise ValueError('Disconnected role boundary')
    return {'cases':len(cases),'raw_endpoint_fields_checked':checked,'p004_nonrescue':True,'certificate_claims':0}


def wave_rows(cases):
    rows=[]
    for h in cases:
        for i in range(len(h['endpoints'])//2):
            a,b=h['endpoints'][2*i:2*i+2]
            rows.append({'node_id':h['display_id']+'.'+str(i+1),'parent_id':h['display_id'],
                'hypothesis_id':h['hypothesis_id'],'candidate_id':h['candidate_id'],'binding_id':h.get('binding_id'),
                'role':str(i+1) if h['family']=='NORMAL_IMPULSE_PARTIAL' else 'child_'+str(i+1),
                'resolution':h['timeframe'],'start':deepcopy(a),'end':deepcopy(b),
                'proposed_only':True,'degree':'DEGREE_UNRESOLVED','internal_status':'INTERNALS_UNRESOLVED'})
    return rows


def reconcile_charts(datasets,snapshots,raw):
    sources={s.observations.provenance.source_sha256:{datetime.fromtimestamp(r['value'][0],timezone.utc).isoformat():r['value'] for r in raw[k]['rows']} for k,s in snapshots.items()}
    fields={'high':2,'low':3,'close':4};n=0
    for rows in datasets.values():
        for row in rows:
            if Fraction(sources[row['source_hash']][row['time']][fields[row['field']]])!=Fraction(row['price']):raise ValueError('Chart price mismatch')
            n+=1
    return n


def build(output=PACK):
    output=Path(output).resolve()
    if not output.is_relative_to(old.ROOT) or output==old.ROOT or (output/'REVIEW_manifest.json').exists():raise ValueError('New unsealed Runtime pack required')
    doc=old.read(PACK/'analysis.json');prior=old.read(analysis.previous.previous.PACK/'canonical_hierarchy.json')
    saved=prior['hypotheses']+prior['corrective_hypotheses']
    local=[deepcopy(next(h for h in saved if h['display_id']==alias)) for alias in LOCAL]
    cases=deepcopy(doc['hypotheses'])+local;by_alias={h['display_id']:h for h in cases}
    snapshots,raw=old.tv.load_inputs();res_by_hash={s.observations.provenance.source_sha256:k for k,s in snapshots.items()}
    audit=reconcile_cases(cases,snapshots,raw)
    measures=[analysis.factual_measures(h,snapshots[res_by_hash[h['source_response_sha256']]]) for h in doc['hypotheses']]
    if measures!=doc['measures']:raise ValueError('Saved measures do not replay')
    path_windows=[]
    for h in doc['hypotheses']:
        s=snapshots[res_by_hash[h['source_response_sha256']]]
        for i in range(5):
            a,b=h['endpoints'][2*i:2*i+2]
            path_windows.append({'alias':h['display_id'],'role':i+1,'observation':analysis.previous.inspect_window(s,a['timestamp_utc'],b['timestamp_utc'],inclusive_end=True)})
    old.save(output/'path_observations.json',path_windows)
    rows=wave_rows(cases)
    indicator_raw=old.read(old.PREVIOUS/'indicators_1D_verified.json')
    indicators=digital_report.indicator_rows(indicator_raw,old.read(old.PREVIOUS/'indicator_summary.json'))
    canonical={'stage':analysis.STAGE,'new_hypotheses':doc['hypotheses'],'reused_local_cases':local,
        'new_observational_links':doc['links'],'occurrence_evidence':doc['occurrence_evidence'],
        'unmodified_prior_interior_links':[x for x in prior['links'] if x['surviving_observational_link']],
        'prior_links_not_reparented':True,'wave_rows':rows,'measures':measures,'input_coverage':prior['input_coverage'],
        'indicators':{'source_sha256':old.hash_file(old.PREVIOUS/'indicators_1D_verified.json'),'resolution':'1D','rows':indicators,'interpretation':'OBSERVATION_ONLY_SEPARATE_STUDY_CAPTURE'},
        'current_position':'CURRENT_WAVE_POSITION_UNRESOLVED','rank':None,'family_validity':False,'inventories':[11,7,0,0],
        'output_kind':'PROVISIONAL_ANALYSIS_REVIEW_NOT_RANKED_ANALYSIS_SCHEMA'}
    old.save(output/'canonical_hierarchy.json',canonical)
    old.save(output/'wave_table.json',rows)
    title='NVDA — Full-history scenarios, proposed subwaves and conditional position'
    now=datetime.now(timezone.utc).isoformat();datasets={};parts=[]
    manifest={'version':1,'surface':'report','title':title,'description':'English source-locked review of the saved 8 September 2026 captures; not a validated count',
        'generatedAt':now,'cards':[],'charts':[],'tables':[],'blocks':[],
        'sources':[{'id':'evidence','label':'Saved BATS:NVDA observations and exact bounded hypotheses','path':'canonical_hierarchy.json'},
                   {'id':'authority','label':'Protected methodology trace and unchanged authority limits','path':'source_review.json'}]}
    def prose(key,body):
        manifest['blocks'].append({'id':key,'type':'markdown','body':body});parts.append(body)
    def table(key,title,headers,values):prose(key,'### '+title+'\n\n'+display.display.mdtable(headers,values))
    def roles(alias):
        selected=[x for x in rows if x['parent_id']==alias]
        table('table-'+alias.replace(':','-'),'Proposed roles — '+alias,
            ['Role','Start bar UTC','Field / USD','End bar UTC','Field / USD'],
            [[r['role'],r['start']['timestamp_utc'].replace('+00:00','Z'),r['start']['price_field']+' '+repr(r['start']['price']),r['end']['timestamp_utc'].replace('+00:00','Z'),r['end']['price_field']+' '+repr(r['end']['price'])] for r in selected])
    chart_map=[];template=old.read(analysis.previous.previous.PACK/'artifact.json')['manifest']['charts'][0]
    def plot(alias,res,title,full_history=False,historical=False):
        key='plot-'+alias.replace(':','-');h=by_alias[alias]
        data=display.chart_rows(snapshots[res],h,start='1999' if full_history else None)
        if historical:data=[r for r in data if r['time']<=h['endpoints'][-1]['timestamp_utc']]
        chart=deepcopy(template);chart.update(id=key,title=title,dataset=key)
        chart['encodings']['x']['label']='UTC bar time (continuous year)'
        chart['encodings']['y']['label']='log10(USD), display only'
        chart['encodings']['tooltip']=[{'field':'time','label':'Original UTC bar label'},{'field':'price','label':'Represented USD price'},{'field':'field','label':'Observed field'},{'field':'label','label':'Proposed role'}]
        chart['source'].update(id=key+'-source',path='chart_rows.json')
        manifest['charts'].append(chart);datasets[key]=data
        manifest['blocks'].append({'id':key+'-block','type':'chart','chartId':key,'layout':'full'})
        cue='Historical endpoint interval only' if historical else 'Captured trailing prices remain unlabelled beyond the hypothesis'
        prose(key+'-note',cue+'. '+res+' native bars; log10 price is a display transform only. Labels are proposed slots, never confirmed waves. Exact prices and dates are available in the chart source table.')
        chart_map.append({'id':key,'question':'How do these exact proposed endpoints sit within the observed price path?',
            'family':'scatter','variant':'dense temporal close observations plus labelled endpoint observations','resolution':res,'source':'chart_rows.json',
            'palette':'single-root preferred; labels identify proposed endpoints','rows':len(data),'date_range':[min(r['time'] for r in data),max(r['time'] for r in data)],
            'historical_display_window':historical,'no_rank_or_degree_authority':True})
    prose('title','# '+title)
    for section in old.read(PACK/'narrative.json'):
        key=section['id'];prose(key,section['body'])
        if key=='history':plot('H-MAY','1M','Full available Monthly history — H-MAY proposal',True)
        if key=='major':
            roles('H-MAY');roles('H-SEP');plot('H-SEP','1M','Full available Monthly history — H-SEP proposal',True)
        if key=='early':roles('EARLY-W');plot('EARLY-W','1W','2002–2007 Weekly proposed subdivision',historical=True)
        if key=='middle':
            roles('MIDDLE-D');plot('MIDDLE-W','1W','2008–2021 Weekly observations and proposed roles',historical=True)
        if key=='recent':
            roles('RECENT-W-A');roles('RECENT-D');plot('RECENT-W-B','1W','2022–capture Weekly proposed arrangement B')
            table('new-links','Exact new observation links',['Parent','Role','Child','Relationship','Full family proof'],[[l['parent'],l['parent_role'],l['child'],l['relationship'],'No'] for l in doc['links']])
        if key=='latest':
            roles(LOCAL[3]);plot(LOCAL[3],'240','Recent native 4H observations — three-segment hypothesis')
        if key=='local':
            roles(LOCAL[0]);roles(LOCAL[1]);roles(LOCAL[2]);plot(LOCAL[0],'1D','Late July–capture Daily proposal and unlabelled tail');plot(LOCAL[2],'15','Native 15m proposal and unlabelled tail')
        if key=='fib':
            table('proportions','Descriptive endpoint-distance ratios',['Hypothesis','2 / 1','4 / 3','3 / 1','5 / 1'],
                [[m['alias']]+[f"{m['ratio_decimal_display'][k]:.6f}" for k in ('role2_over_role1','role4_over_role3','role3_over_role1','role5_over_role1')] for m in measures])
        if key=='volume':
            table('volume-peaks','Interior-bar volume observations',['Hypothesis','Role','Peak saved volume','Peak UTC bar(s)'],
                [[m['alias'],v['role'],repr(v['peak_volume']),', '.join(e['bar_label_utc'][:10] for e in v['peak_occurrences'])] for m in measures if m['alias'] in ('H-MAY','MIDDLE-D','RECENT-D') for v in m['volume_windows'] if v['role'] in (3,5)])
            table('study-values','Separate saved Daily study observations',['Study','UTC bar','Value','Forming'],[[r['indicator'],r['bar_time'],repr(r['value']),r['forming']] for r in indicators])
        if key=='coverage':
            table('captures','Saved native coverage — each capture independent',['Resolution','Bars','First bar','Last bar','Capture UTC','Last close'],
                [[k,v['bars'],v['first_bar'][:10],v['last_bar'][:10],v['metadata']['captured_at_utc'],repr(v['last_close'])] for k,v in prior['input_coverage'].items()])
            table('checked','Actual new evaluations',['Hypothesis','P004','P005','Full family'],[[h['display_id'],h['p004']['status'],h['p005']['status']+': '+h['p005']['reason'],'Unresolved'] for h in doc['hypotheses']])
    artifact={'surface':'report','manifest':manifest,'snapshot':{'version':1,'generatedAt':now,'status':'ready','datasets':datasets},'sources':manifest['sources'],'package_info':{'delivery_mode':'html','language':'en'}}
    old.save(output/'artifact.json',artifact);old.save(output/'chart_rows.json',datasets)
    old.save(output/'chart_map.json',{'charts':chart_map,'repeated_family_reason':'Every chart asks a price-path/endpoint question at a separate historical context or resolution; exact lookup remains in role tables. No redundant charts for unrelated metrics.'})
    count=reconcile_charts(datasets,snapshots,raw)
    for name,body in [('report.md','\n\n'.join(parts)+'\n'),('wave_table.md',display.display.mdtable(['Node','Parent','Resolution','Start UTC','Start price','End UTC','End price'],[[r['node_id'],r['parent_id'],r['resolution'],r['start']['timestamp_utc'],repr(r['start']['price']),r['end']['timestamp_utc'],repr(r['end']['price'])] for r in rows])+'\n')]:
        with (output/name).open('x',encoding='utf-8',newline='\n') as f:f.write(body)
    old.save(output/'export_audit.json',dict(audit,chart_rows_reconciled=count,wave_rows=len(rows),indicator_values_reconciled=len(indicators),path_windows=len(path_windows),new_links=len(doc['links']),weekly_ancestry_not_invented=True,prior_links_not_reparented=True,methodology_unchanged=True))
    print({'cases':len(cases),'chart_rows':count,'blocks':len(manifest['blocks']),'wave_rows':len(rows)})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=PACK);build(parser.parse_args().output)
