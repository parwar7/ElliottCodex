"""Frozen TradingView quality audit and delegation to the existing bounded runner.

PYTHONPATH=src python -B tools/nvda_tradingview_replay.py --quality --output <new.json>
No live capture, new Elliott behavior, authority deserialization or Yahoo call.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path

from elliott_runtime.market_data.tradingview import load_tradingview_snapshot, INTERVALS

ROOT=Path(__file__).resolve().parents[1]
PACK=ROOT/'kernel_reviews/TRADINGVIEW-DIGITAL-DATA-AND-NVDA-ANALYSIS-BRIDGE-V1'
STAGE=PACK.name

def read(path): return json.loads(path.read_text(encoding='utf-8'))
def sha(raw): return hashlib.sha256(raw).hexdigest()
def iso(t): return datetime.fromtimestamp(t,timezone.utc).isoformat()

def load_inputs(pack=PACK):
    manifest=read(pack/'input_manifest.json'); result={}; raw={}
    if set(manifest['datasets'])!=set(INTERVALS): raise ValueError('Six explicit native resolutions required')
    for resolution,entry in manifest['datasets'].items():
        path=pack/entry['path']
        if not path.resolve().is_relative_to(pack.resolve()): raise ValueError('Foreign input path')
        data=path.read_bytes()
        if len(data)!=entry['byte_length']:raise ValueError('Input length mismatch')
        result[resolution]=load_tradingview_snapshot(data,expected_sha256=entry['sha256'],expected_resolution=resolution,source_identifier=STAGE+'/'+entry['path'])
        raw[resolution]=json.loads(data)
    return result,raw

def display_matches(number,text):
    """Chart formatting precision ONLY; never a market/rule tolerance."""
    value=text.replace('\u202f','').replace(',','').replace('−','-').strip()
    factor=Decimal(1)
    if value[-1:] in ('K','M','B'):
        factor={'K':Decimal(1000),'M':Decimal(1000000),'B':Decimal(1000000000)}[value[-1]];value=value[:-1]
    shown=Decimal(value); half=Decimal(5).scaleb(shown.as_tuple().exponent-1)*factor
    # Display formatting only: JSON's shortest decimal spelling is compared to
    # the displayed decimal cell. This is NOT original-decimal precision and
    # is NEVER used for prices supplied to P004/P005 (which retain floats).
    return abs(Decimal(str(number))-shown*factor)<=half

def quality(pack=PACK):
    datasets,raw=load_inputs(pack);out={'stage':STAGE,'datasets':{},'regions':[]}
    for res,snapshot in datasets.items():
        data=raw[res];by_time={r['value'][0]:r['value'] for r in data['rows']}
        receipt=read(pack/('reconciliation_'+res+('_completed' if res=='15' else '')+'.json'));c=receipt['context']
        for k in ('symbol','resolution','session','dividend_adjustment','back_adjustment','feed'):
            if c[k]!=data['context'][k]:raise ValueError('Reconciliation context mismatch')
        checks=[]
        if {s['row'][0] for s in receipt['samples']}!=set(receipt['requested_timestamps']):raise ValueError('Missing reconciliation samples')
        for sample in receipt['samples']:
            row=sample['row']; prior=by_time[row[0]]
            changed=row!=prior
            if changed and row[0]!=data['rows'][-1]['value'][0]:raise ValueError('Historical sample revision; exclude series')
            if changed and snapshot.last_bar_forming is not True:raise ValueError('Revision not explained by forming metadata')
            fields={x['title']:x['value'] for x in sample['window'] if x['visible']}
            matches={label:display_matches(row[i],fields[label]) for label,i in [('Open',1),('High',2),('Low',3),('Close',4),('Vol',5)] if row[i] is not None}
            if not all(matches.values()):raise ValueError(f'Data window differs: {res} {row} {fields} {matches}')
            checks.append({'timestamp':iso(row[0]),'native_values':prior,'later_window_values':row,'formatted_values':fields,'format_matches':matches,'forming_revision':changed})
        o=snapshot.observations
        out['datasets'][res]={'bars':len(o.bars),'first_bar_start':iso(data['rows'][0]['value'][0]),'last_bar_start':iso(data['rows'][-1]['value'][0]),
          'capture_start':data['capture_request']['started_at_utc'],'capture_end':data['captured_at_utc'],
          'forming_last_bar':snapshot.last_bar_forming,'source_sha256':o.provenance.source_sha256,'context':data['context'],
          'stop_reason':data['capture_request']['stop_reason'],'history_request':data['capture_request'],
          'missing_volume_count':sum(b.volume is None for b in o.bars),'duplicates':0,'nonfinite':0,'ohlc_errors':0,
          'elapsed_gap_intervals':len(o.quality.missing_intervals),'gap_interpretation':'Calendar-unaware elapsed gaps include scheduled closures; not proven data loss',
          'snapshot_revisions':data['revision_observation'],'reconciliation':checks,'input_usable':True}
    # Explicit historical VISUAL REGIONS, not optimized wave endpoints or validator input.
    regions=[('R_APR25','2025-04-01','2025-05-01','low'),('R_MAY25','2025-05-12','2025-05-23','high'),
      ('R_LATE_MAY25','2025-05-23','2025-06-02','low'),('R_AUG25','2025-08-01','2025-09-01','high'),
      ('R_SEP25','2025-09-01','2025-10-01','low'),('R_OCT25','2025-10-01','2025-11-10','high'),
      ('R_MAR26','2026-03-01','2026-04-01','low'),('R_MAY26','2026-05-01','2026-06-01','high'),
      ('R_JUL26','2026-07-20','2026-08-01','low')]
    daily=datasets['1D'].observations
    for name,start,end,field in regions:
        bars=[b for b in daily.bars if start<=b.timestamp_utc.date().isoformat()<end]
        value=(min if field=='low' else max)(getattr(b,field) for b in bars)
        # Preserve every tied observed extremum; no arbitrary exact endpoint tie break.
        out['regions'].append({'region_id':name,'window':[start,end],'field':field,'price':value,
          'observations':[{'timestamp':b.timestamp_utc.isoformat(),'source_record_index':b.provenance.source_record_index,
                           'ohlcv':[b.open,b.high,b.low,b.close,b.volume]} for b in bars if getattr(b,field)==value],
          'snapshot_sha256':daily.provenance.source_sha256,'authority':'OBSERVED_REGION_EXTREMUM_NOT_ORTHODOX_ENDPOINT',
          'methodology_evaluation':'NOT_EXECUTED_FROM_VISUAL_REGIONS'})
    return out

def pipeline(pack=PACK):
    from elliott_methodology_kernel import MethodologyKernel
    from nvda_post_p005_experiment import run_scope, configuration, plain
    snapshots,_=load_inputs(pack)
    # Re-validate saved data-window receipts before constructing methodology inputs.
    quality(pack)
    kernel=MethodologyKernel(Path(r'C:\ElliottCodex\Brain_LOCKED'))
    out={'stage':STAGE,'status':'INCOMPLETE','input_source':'TradingView BATS:NVDA / Cboe One regular; no Yahoo',
         'configuration':configuration(),'scopes':[],'inventories':[11,7,0,0],
         'delegation':'Unchanged nvda_post_p005_experiment.run_scope; legacy nvda-post-p005 ID namespace is retained, not a Yahoo data claim',
         'scope':'Six most recent geometric pivots per parent, one child level only. Full historical data is NOT fully searched.'}
    for parent,finer in (('1M','1W'),('1W','1D'),('1D','60')):
        at=snapshots[parent].observations.provenance.ingested_at_utc
        out['scopes'].append(run_scope(snapshots[parent].observations,snapshots[finer].observations,kernel,at))
    out['status']='COMPLETED_BOUNDED_OPERATIONAL_EXPERIMENT'
    return plain(out)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--quality',action='store_true');p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();dest=args.output.resolve()
    if not dest.is_relative_to(ROOT) or dest.exists():p.error('New Runtime output required')
    out=quality() if args.quality else pipeline()
    with dest.open('x',encoding='utf-8') as f:json.dump(out,f,ensure_ascii=False,indent=2,allow_nan=False)
    print(str(dest),flush=True)

if __name__=='__main__':main()
