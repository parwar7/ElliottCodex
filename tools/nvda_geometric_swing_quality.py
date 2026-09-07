"""Replay NVDA through outcome-independent alternating geometric search."""
import argparse
from collections import Counter
from pathlib import Path

import nvda_hierarchical_hypotheses as hierarchy
from elliott_runtime.analysis.geometric_swing_search import (
    GeometricSwingSearchConfig, movement_domain, select_geometric_swing_requests,
)

p = hierarchy.p
reporting = hierarchy.reporting
STAGE = 'NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1'
PREVIOUS = p.ROOT / 'kernel_reviews/NVDA-FULL-HISTORY-HIERARCHICAL-HYPOTHESES-V1'


def configuration():
    return {
        'classification': 'PROJECT_OPERATIONAL_POLICY_NOT_ELLIOTT_METHODOLOGY',
        'geometry_windows': [2, 4, 8], 'equal_extreme_policy': 'LAST', 'include_developing': True,
        'root_resolution': '1mo', 'regions': [[1999, 2007], [2008, 2016], [2017, 2026]],
        'sequences_per_region_per_scale': 1, 'sequence_pivots': 6,
        'selection': 'first chronological eligible consecutive six-pivot sequence in each region; no consolidation or cross-scale splice',
        'max_source_pivots': 10000, 'max_source_bars': 10000, 'max_root_jobs': 9,
        'root_candidate_bounds': {'pivots': 6, 'span': 6, 'skips': 0, 'candidates': 4},
        'child_exploration': 'one level for scale-2 roots only, at most three roots, Monthly -> Weekly',
        'child_geometry': {'left': 2, 'right': 2, 'equal_extreme_policy': 'LAST', 'include_developing': True},
        'child_limits': hierarchy.configuration()['child_limits'],
        'child_search_domain': 'EXISTING_UNFILTERED_CHILD_API; geometric membership reported separately, no filtered ancestry substituted',
        'duplicates': 'retain all discovery/requirement origins; identical price sequences are not independent confirmation',
        'omissions': ['cross-region consecutive sequences', 'all skipped-pivot combinations', 'later eligible regional starts beyond budget',
                      'children for scales 4/8', 'second and deeper child levels', 'additional resolutions/scales'],
        'ranking': False, 'degree_inference': False, 'current_position_inference': False,
    }


def pivot_records(result):
    bars = {b.timestamp_utc: b for b in result.input_observations.bars}
    return [p.plain({'pivot_id': x.pivot_id, 'timestamp': x.timestamp_utc, 'price': x.observed_price,
                    'price_field': x.pivot_kind.value.lower(), 'state': x.state,
                    'config': result.config, 'bar_provenance': bars[x.timestamp_utc].provenance,
                    'provenance_refs': x.provenance_refs}) for x in result.pivots]


def row_domain(row):
    endpoints = row['endpoints']
    prices = tuple([endpoints[0]['price']] + [x['price'] for x in endpoints if x['edge'] == 'end'])
    return movement_domain(prices)


def old_comparison(data):
    manifest_path = PREVIOUS / 'NVDA_FULL_HISTORY_HIERARCHICAL_HYPOTHESES_manifest.json'
    if p.sha(manifest_path.read_bytes()) != '5940061743ddae509d7675c47d727a7258341c6a2f6b3dc49a6cd9ae81846e5e':
        raise ValueError('Previous baseline manifest differs')
    manifest = p.json.loads(manifest_path.read_bytes())
    path = PREVIOUS / 'report/results.json'
    entry = next(e for e in manifest['artifacts'] if e['path'].endswith('/report/results.json'))
    if p.sha(path.read_bytes()) != entry['sha256']:
        raise ValueError('Historical result hash differs')
    old = p.json.loads(path.read_bytes())
    row = next(x for x in old['hypotheses'] if x['display_ref'] == 'H0467')
    if row['snapshot_content_sha256'] != p.sha(p.encoded(data['1mo'])):
        raise ValueError('Comparison snapshot differs')
    bars = {b.timestamp_utc.isoformat(): b for b in data['1mo'].bars}
    for e in row['endpoints']:
        if e['price'] != getattr(bars[e['timestamp_utc']], e['price_field']):
            raise ValueError('Historical price differs from saved bars')
    return {'baseline': PREVIOUS.name, 'display_ref': 'H0467', 'hypothesis_id': row['hypothesis_id'],
            'snapshot_content_sha256': row['snapshot_content_sha256'], 'endpoints': row['endpoints'],
            'domain': row_domain(row), 'original_p004': row['p004'], 'original_p005': row['p005'],
            'new_structural_certificate': False, 'interpretation': 'OUTSIDE_NEW_SEARCH_DOMAIN_NOT_NEW_ELLIOTT_INVALIDITY'}


def totals(rows):
    result = {}
    for path in ('parent', 'child'):
        selected = [r for r in rows if r['path'] == path]
        result[path] = {'hypotheses': len(selected), 'candidate_contexts': len({r['candidate_id'] for r in selected}),
                        'families': dict(Counter(r['family'] for r in selected)),
                        'p004': dict(Counter(r['p004']['status'] for r in selected if r['p004'])),
                        'p005': dict(Counter(r['p005']['status'] for r in selected if r['p005'])),
                        'p005_unresolved_reasons': dict(Counter(r['p005']['reason'] for r in selected if r['p005'] and r['p005']['status'] == 'UNRESOLVED')),
                        'p004_invalid_despite_p005_sufficiency': sum(bool(r['p004'] and r['p004']['fatal'] and r['p005']['status'] == 'SUFFICIENT_CONDITION_ESTABLISHED') for r in selected),
                        'outside_geometric_domain': sum(not r['geometric_domain']['eligible'] for r in selected)}
    return result


def audit(doc, data):
    receipt = hierarchy.audit(doc, data)
    for row in doc['hypotheses']:
        if row['geometric_domain'] != row_domain(row):
            raise ValueError('Movement evidence changed')
        if row['path'] == 'parent' and not row['geometric_domain']['eligible']:
            raise ValueError('Ineligible root escaped search domain')
    if doc['totals'] != totals(doc['hypotheses']):
        raise ValueError('Totals differ')
    if doc['comparison'] != old_comparison(data):
        raise ValueError('Historical comparison changed')
    for scale in doc['scales']:
        c = scale['coverage']
        classified = Counter(x['disposition'] for x in c['windows'])
        if sum(classified.values()) != max(0, len(scale['pivots']) - 5):
            raise ValueError('Unaccounted search scope')
        for w in c['windows']:
            pivots = scale['pivots'][w['start_index']:w['start_index']+6]
            if w['domain'] != movement_domain(tuple(x['price'] for x in pivots)) or w['pivot_ids'] != [x['pivot_id'] for x in pivots]:
                raise ValueError('Search scope evidence changed')
        width = scale['window']
        geometry = p.GeometricPivotDiscoveryConfig(p.GeometricPivotDiscoveryMethod.WINDOWED_LOCAL_EXTREMA,width,width,p.EqualExtremePolicy.LAST,True)
        discovered = p.discover_geometric_pivots(p.GeometricPivotDiscoveryRequest(STAGE+f':scale-{width}',data['1mo'],geometry,(STAGE,)))
        if scale['pivots'] != pivot_records(discovered) or scale['config'] != p.plain(geometry) or scale['snapshot_content_sha256'] != p.sha(p.encoded(data['1mo'])):
            raise ValueError('Discovery evidence differs from preserved snapshot')
    receipt['all_new_parent_movements_alternate'] = True
    receipt['historical_result_preserved'] = True
    return receipt


def render(doc):
    # Normalize ordering so live and JSON-reloaded evidence render identically.
    doc = p.json.loads(p.encoded(doc))
    lines = ['# NVDA geometric swing search', '', '## Technical summary', '',
             'This run selects nonzero alternating price movements before Elliott evaluation. It does not establish correct waves, a coherent count or a current-wave position.', '',
             '## Same data, different search domain', '',
             'The saved Yahoo capture is unchanged: collected 6 September 2026, latest bars 4 September 2026. Geometry windows 2, 4 and 8 are operational scales on Monthly bars, not degrees or proof of major waves.', '',
             'Historical H0467 movements: ' + ' / '.join(doc['comparison']['domain']['movements']) + '. It falls outside this search domain; no new structural rejection is issued.', '',
             '## Coverage by scale and historical region', '',
             'Each region selects its first eligible consecutive six-pivot sequence. All other starts are classified explicitly; this is not exhaustive history or skipped-pivot search.', '',
             '| Window | Region | Emitted pivots (whole scale) | Eligible starts | Selected | Unvisited |', '|---:|---|---:|---:|---:|---:|']
    for scale in doc['scales']:
        for region in scale['coverage']['regions']:
            lines.append(f"| {scale['window']} | {region['years'][0]}–{region['years'][1]} | {len(scale['pivots'])} | {len(region['eligible_starts'])} | {len(region['selected_starts'])} | {len(region['unvisited_starts'])} |")
    for scale in doc['scales']:
        lines += ['', f"Window {scale['window']} dispositions: {dict(Counter(x['disposition'] for x in scale['coverage']['windows']))}. Same-kind pairs: {len(scale['coverage']['same_kind_adjacent_pairs'])}; tied-extreme diagnostic windows: {len(scale['coverage']['tie_windows'])}. {scale['coverage']['geometry_diagnostics']}", '']
    lines += ['## Existing checks, not family proof', '',
              'Hypothesis counts include separate family selectors over the same neutral candidate. They are not independent confirmations. Child results below use the unchanged child API, not the new parent-domain filter.', '',
              '| Path | Hypotheses | Candidate contexts | P004 | P005 | Outside domain |', '|---|---:|---:|---|---|---:|']
    for key, value in doc['totals'].items():
        lines.append(f"| {key} | {value['hypotheses']} | {value['candidate_contexts']} | {value['p004']} | {value['p005']} | {value['outside_geometric_domain']} |")
    for key, value in doc['totals'].items():
        lines += ['', f"{key.capitalize()} P005 unresolved reasons: {value['p005_unresolved_reasons']}. P004-invalid despite P005 sufficiency: {value['p004_invalid_despite_p005_sufficiency']}."]
    lines += ['', 'P004 remains fatal to its exact hypothesis regardless of P005 sufficiency. Internal requirements remain unsatisfied. P005 is sufficiency-only; neither alternation nor these checks establish family validity.', '', '## Deterministic movement samples', '',
              'The first Normal Impulse proposal per root is displayed in enumeration order, not ranked. All prices/fields, original pivots and parent links are in JSON/CSV. Signs are factual price comparisons, not new wave rules.', '']
    samples = [r for r in doc['hypotheses'] if r['path'] == 'parent' and r['p004']]
    for r in samples:
        lines += [f"### {r['display_ref']} — {r['root_job']}", '', '| Role | Start UTC / field / price | End UTC / field / price | Move |', '|---|---|---|---|']
        for i, (a,b) in enumerate(zip(r['endpoints'][::2],r['endpoints'][1::2],strict=True)):
            lines.append(f"| {a['role']} | {a['timestamp_utc'][:10]} / {a['price_field']} / {a['price']!r} | {b['timestamp_utc'][:10]} / {b['price_field']} / {b['price']!r} | {r['geometric_domain']['movements'][i]} |")
        lines += ['', f"P004: {r['p004']['status']}; P005: {r['p005']['status']} ({r['p005']['reason']}). Current position unresolved.", '']
    lines += ['## Exact child links and operational stops', '',
              'One genuine Monthly→Weekly child layer is explored for the scale-2 roots only. Later scales and deeper levels remain unvisited, not impossible. A child outside the geometric search domain is separately identified; its existing methodology outcome is not rewritten.', '',
              '| Root | Requirements | Coverage | Child hypotheses | Further levels |', '|---|---:|---|---:|---|']
    for stop in doc['stops']:
        lines.append(f"| {stop['root']} | {stop['requirements']} | {stop['coverage']} | {stop['child_hypotheses']} | {stop['reason']} |")
    lines += ['', 'Representative first linked child per root (IDs are exact; full records retain all links):', '']
    seen = set()
    for row in doc['hypotheses']:
        if row['path'] != 'child' or row['root_job'] in seen: continue
        seen.add(row['root_job'])
        lines += [f"- {row['display_ref']}: parent `{row['parent_family_hypothesis_id']}`, requirement `{row['requirement_id']}`, hypothesis `{row['hypothesis_id']}`."]
    lines += ['', '## Limitations and next question', '',
              'No consolidation is performed. Discovery resolves equal extrema only by its explicit LAST policy and excludes ambiguous same-bar high/low extrema. Such omissions do not establish hidden endpoint order. Coarser windows are not guaranteed to identify meaningful Elliott waves.', '',
              'Duplicate origins are retained. The geometric signature groups in JSON identify repeated coordinates but do not merge ancestry or count repetitions as confirmation.', '',
              *('- ' + x for x in reporting.BLOCKERS), '',
              'CURRENT_POSITION_UNRESOLVED remains explicit for every context. Developing-position inference is still a separate missing capability. No degree, forecast, targets, confidence, ranking or trading signal is produced.', '',
              'Next engineering review: exact scoped child-search transport. The current child-evidence contract requires the full finer-discovery pivot tuple; filtered child selection would need an explicitly reviewed contract extension, not tuple substitution. No such extension is implemented here.', '']
    return '\n'.join(lines)


def run(output, progress=print):
    output = Path(output).resolve()
    if output.exists() or not output.is_relative_to(p.ROOT):
        raise ValueError('Output must be a new Runtime directory')
    inputs = hierarchy.INPUTS
    if p.sha((inputs/'input_manifest.json').read_bytes()) != hierarchy.INPUT_MANIFEST_SHA256:
        raise ValueError('Input manifest differs')
    manifest, data = p.load_inputs(inputs)
    cfg = configuration(); at = manifest['requested_at_utc']; refs = (STAGE,)
    kernel = p.MethodologyKernel(Path('C:/ElliottCodex/Brain_LOCKED'))
    scales, jobs = [], []
    for width in cfg['geometry_windows']:
        geometry = p.GeometricPivotDiscoveryConfig(p.GeometricPivotDiscoveryMethod.WINDOWED_LOCAL_EXTREMA,width,width,p.EqualExtremePolicy.LAST,True)
        discovered = p.discover_geometric_pivots(p.GeometricPivotDiscoveryRequest(STAGE+f':scale-{width}', data['1mo'],geometry,refs))
        template = p.CandidateGenerationRequest(STAGE+f':scale-{width}',at,p.AnalyzedWaveSubject(STAGE+f':scale-{width}',data['1mo'].provenance.source_sha256),data['1mo'],discovered,
            p.CandidateGenerationConfig(6,6,0,4,p.SHAPES,p.CandidatePivotWindow.EARLIEST),(),refs)
        requests, coverage = select_geometric_swing_requests(template,GeometricSwingSearchConfig(tuple(tuple(x) for x in cfg['regions']),1,10000,10000))
        scales.append({'window':width,'snapshot_content_sha256':p.sha(p.encoded(data['1mo'])), 'config':p.plain(geometry),'pivots':pivot_records(discovered),'coverage':coverage})
        jobs.extend((width,request) for request in requests)
    if len(jobs) > cfg['max_root_jobs']: raise ValueError('Root budget exceeded')
    reporting.write_bytes_new(output/'configuration.json',p.encoded(cfg))
    reporting.write_bytes_new(output/'search_plan.json',p.encoded(scales))
    rows,requirements,stops,live = [],[],[],[]
    def add(values, job, level):
        for row in values:
            row.update(root_job=job,level=level,degree='DEGREE_UNRESOLVED')
            row['geometric_domain']=row_domain(row)
            row['observation_relation']=hierarchy.observation_relation(row,data[row['timeframe']])
            rows.append(row)
    for width, request in jobs:
        job = request.request_id;progress(job)
        generated = p.generate_candidate_hypotheses(request)
        competing = p.build_competing_candidate_set(p.CompetingCandidateSetRequest(job+':set',job,generated,refs))
        bridge = p.build_family_evaluation_hypotheses(p.FamilyHypothesisBridgeRequest(job+':family',at,competing,tuple(p.FamilyEvaluationKind),refs),kernel)
        partial = p.evaluate_normal_impulse_partial_scope(p.NormalImpulsePartialEvaluationRequest(job+':normal',at,bridge,100,100,100,refs),kernel)
        add(reporting.family_rows(bridge,'parent',job)+reporting.normal_rows(partial,'parent',job),job,0)
        live.append((bridge,partial))
        if width != 2:
            stops.append({'root':job,'requirements':0,'coverage':{},'child_hypotheses':0,'reason':'CHILD_SCALE_BUDGET_UNVISITED'})
            continue
        internals,selections,children,families,child_partial=hierarchy.child_layer(bridge,data['1wk'],kernel,at,job+':child',request.geometric_pivots.config)
        before=len(rows)
        for req,selection,outcome in zip(internals.internal_requirements,selections,children.requirement_outcomes,strict=True):
            requirements.append({'requirement_id':req.requirement_id,'parent_hypothesis_id':req.family_hypothesis.hypothesis_id,'child_index':req.child_index,
                'shape':req.required_internal_shape.value,'source_class':req.source_class,'protected_refs':list(req.protected_refs),
                'start':selection.selected_window.parent_window_start_utc.isoformat(),'end':selection.selected_window.parent_window_end_utc.isoformat(),
                'coverage':selection.selected_window.coverage_state.value,'generation_status':outcome.status.value,
                'bars':len(selection.selected_window.ordered_bars),'requirement_satisfied':False})
        for item in families.child_evaluations:
            if item.family_hypothesis_result is not None:
                req=hierarchy.check_child_link(families,item,item.family_hypothesis_result)
                add(reporting.family_rows(item.family_hypothesis_result,'child',job,req),job,1)
        add(reporting.normal_rows(child_partial,'child',job),job,1)
        reporting.validate_family_internal_subdivision_evaluation_result(internals)
        hierarchy.validate_recursive_child_family_evaluation_result(families)
        reporting.validate_normal_impulse_partial_evaluation_result(child_partial)
        stops.append({'root':job,'requirements':len(selections),'coverage':dict(Counter(s.selected_window.coverage_state.value for s in selections)),
                      'child_hypotheses':len(rows)-before,'reason':'ONE_CHILD_LEVEL_BUDGET; DEEPER_LEVELS_UNVISITED'})
    for bridge,partial in live:
        reporting.validate_family_hypothesis_bridge_result(bridge)
        reporting.validate_normal_impulse_partial_evaluation_result(partial)
    doc={'stage':STAGE,'configuration':cfg,'data':reporting.data_notes(inputs,manifest,data,'OFFLINE_REPLAY'),
         'scales':scales,'hypotheses':rows,'requirements':requirements,'stops':stops,
         'comparison':old_comparison(data),'totals':totals(rows),
         'inventories':{'methodology':11,'structural_producers':7,'family_producers':0,'family_issuances':0}}
    reporting.assign_display_refs(doc)
    for i,r in enumerate(requirements,1):r['display_ref']=f'R{i:04}'
    doc['groups']=reporting.group_rows(rows)
    signatures={}
    for row in rows:
        signature=tuple((e['timestamp_utc'],e['price_field'],e['price']) for e in row['endpoints'])
        signatures.setdefault(signature,[]).append({'hypothesis_id':row['hypothesis_id'],'candidate_id':row['candidate_id'],'root':row['root_job'],'requirement':row['requirement_id']})
    doc['duplicate_coordinate_contexts']=[value for value in signatures.values() if len(value)>1]
    doc['audit']=audit(doc,data)
    reporting.write_bytes_new(output/'results.json',p.encoded(doc))
    reporting.write_bytes_new(output/'report.md',render(doc).encode())
    for name,text in reporting.evidence_exports(doc).items():reporting.write_bytes_new(output/name,text.encode())
    return doc


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=run(args.output,lambda message:print(message,flush=True));print(p.json.dumps({'audit':result['audit'],'totals':result['totals']}))
