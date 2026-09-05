# Read-only audit of saved outputs; not executable Runtime methodology.

from pathlib import Path
import json,hashlib,collections,math
from fractions import Fraction
from datetime import datetime
root=Path('kernel_reviews/NVDA-POST-P005-BOUNDED-PIPELINE-VALIDATION-V1')
report=json.loads((root/'experiment_results.json').read_bytes())
assert report['status']=='COMPLETED_BOUNDED_OPERATIONAL_EXPERIMENT'
inputs={}
quality=[]
for p in (root/'inputs').glob('NVDA_*.json'):
 d=json.loads(p.read_bytes());obs=d['observations'];meta=d['metadata']
 key=obs['timeframe']['label'];inputs[key]=d
 bars=obs['bars'];stamps=[b['timestamp_utc'] for b in bars]
 assert len(stamps)==len(set(stamps))
 assert all(datetime.fromisoformat(a)<datetime.fromisoformat(b) for a,b in zip(stamps,stamps[1:]))
 assert all(b['low']<=min(b['open'],b['high'],b['close']) and b['high']>=max(b['open'],b['low'],b['close']) for b in bars)
 assert all(type(b[n]) in (int,float) and math.isfinite(b[n]) for b in bars for n in ('open','high','low','close'))
 assert all(not b['provenance']['naive_timezone_assumed_utc'] for b in bars)
 assert not obs['provenance']['resampled']
 assert len(bars)+len(meta['dropped_null_ohlc_row_indices'])==meta['raw_row_count']
 quality.append(dict(timeframe=key,retrieved_at_utc=d['retrieved_at_utc'],start=stamps[0],end=stamps[-1],
 bars=len(bars),raw_rows=meta['raw_row_count'],dropped_null_ohlc_rows=meta['dropped_null_ohlc_row_indices'],
 duplicate_timestamps=0,naive_timestamp_assumptions=0,finite_OHLC=True,valid_OHLC=True,resampled=False,
 missing_volume_rows=meta['missing_volume_row_count'],warnings=d['warnings'],
 nominal_gap_intervals=len(obs['quality']['missing_intervals']),
 nominal_gaps_are_not_verified_missing_trading_bars=True,raw_response_sha256=meta['response_sha256']))
summary=[];cases=[];checked=0;endpoint_checks=0
for scope in report['scopes']:
 output=dict(parent_timeframe=scope['parent_resolution'],finer_timeframe=scope['child_resolution'],
  neutral_parent_candidates=scope['neutral_parent_candidates'],parent_family_hypotheses=scope['parent_family_hypotheses'],
  neutral_child_candidates=scope['neutral_child_candidates'],child_family_hypotheses=scope['child_family_hypotheses'],
  internal_requirements=len(scope['requirements']),coverage_counts=scope['coverage_counts'],
  requirements_with_partial_normal_impulse_execution=scope['requirements_with_partial_normal_impulse_execution'],
  motive_five_requirements=sum(r['shape_required']=='MOTIVE_FIVE_FAMILY_REQUIRED' for r in scope['requirements']),
  requirements_satisfied=scope['requirements_satisfied'],caps_exhausted=scope['caps_exhausted'])
 assert len(scope['requirements'])==sum(scope['coverage_counts'].values())==sum(scope['child_generation_counts'].values())
 assert not any(r['requirement_satisfied'] for r in scope['requirements'])
 seen_cases=set()
 for path in ('parent','child'):
  result=scope[path];traces=result['traces']
  assert result['hypotheses']==len(traces)
  assert sum(result['p004'].values())==sum(result['p005'].values())==len(traces)
  output[path]=dict(hypotheses=len(traces),
   p004_satisfied=result['p004'].get('RULE_SATISFIED',0),p004_violated=result['p004'].get('RULE_VIOLATED',0),
   p004_unresolved=sum(v for k,v in result['p004'].items() if k.startswith('UNRESOLVED')),
   p005_sufficiency_established=result['p005'].get('SUFFICIENT_CONDITION_ESTABLISHED',0),
   p005_unresolved=result['p005'].get('UNRESOLVED',0),unresolved_reasons=result['p005_unresolved_reasons'],
   p004_invalid_despite_p005_sufficiency=result['p004_invalid_despite_p005_sufficiency'])
  data=inputs[scope['parent_resolution'] if path=='parent' else scope['child_resolution']]['observations']
  expected_hash=hashlib.sha256((json.dumps(data,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()).hexdigest()
  bars={b['timestamp_utc']:b for b in data['bars']}
  for trace in traces:
   checked+=1
   assert trace['snapshot_content_sha256']==expected_hash
   assert trace['source_response_sha256']==data['provenance']['source_sha256']
   assert trace['exact_runtime_identity_checks_passed'] and not trace['family_validity_authority']
   assert [e['role'] for e in trace['endpoints']]==['1','1','3','3','5','5']
   values=[];eligible=[]
   for e in trace['endpoints']:
    bar=bars[e['timestamp_utc']]
    assert e['price']==bar[e['price_field']]
    assert e['bar_provenance']==bar['provenance']
    f=Fraction(e['price']);values.append(f);eligible.append(e['eligible'])
    assert (f.numerator,f.denominator)==(e['represented_ratio']['numerator'],e['represented_ratio']['denominator'])
    assert e['eligible']==(e['pivot_state']=='CONFIRMED_BY_GEOMETRY')
    endpoint_checks+=1
   # Audit only: independently recompute the approved, unchanged sufficiency convention.
   direction=1 if trace['direction']=='UP' else -1
   movements=[]
   if any(v is False for v in eligible):
    assert trace['p005_status']=='UNRESOLVED' and trace['p005_reason']=='DEVELOPING_REQUIRED_ENDPOINT'
   elif any(direction*(values[i+1]-values[i])<=0 for i in (0,2,4)):
    assert trace['p005_status']=='UNRESOLVED' and trace['p005_reason']=='ZERO_OR_OPPOSING_ROLE_MOVEMENT'
   else:
    movements=[100*abs(values[i+1]-values[i])/values[i] for i in (0,2,4)]
    sufficient=movements[1]>movements[0] or movements[1]>movements[2]
    assert (trace['p005_status']=='SUFFICIENT_CONDITION_ESTABLISHED')==sufficient
    assert [{'numerator':v.numerator,'denominator':v.denominator} for v in movements]==trace['percentage_movements']
   violation=direction*(values[2]-values[0])<0
   assert (trace['p004_status']=='RULE_VIOLATED')==violation
   assert trace['p004_fatal']==violation==trace['p004_certificate_origin_identity']
   group=(path,trace['p004_status'],trace['p005_reason'])
   if group not in seen_cases:
    seen_cases.add(group);cases.append(dict(timeframe=scope['parent_resolution'],path=path,trace=trace))
  assert collections.Counter(t['p005_reason'] for t in traces if t['p005_status']=='UNRESOLVED')==result['p005_unresolved_reasons']
  assert sum(t['p004_fatal'] and t['p005_status']=='SUFFICIENT_CONDITION_ESTABLISHED' for t in traces)==result['p004_invalid_despite_p005_sufficiency']
 assert sum(bool(r['partial_normal_impulse_hypotheses']) for r in scope['requirements'])==scope['requirements_with_partial_normal_impulse_execution']
 summary.append(output)
print(json.dumps(dict(assessment='SHARE_WITH_CAVEATS_OPERATIONAL_ONLY',scopes=summary,quality=quality,
trace_cases=cases,identity_traces_checked=checked,endpoint_observations_checked=endpoint_checks,
all_outcome_and_requirement_totals_reconciled=True,exact_fraction_spot_checks='ALL_ELIGIBLE_TRACES_PASS',
snapshot_content_hash_checks='PASS',source_comparison='Fresh inputs; historical code-only attribution prohibited')))
