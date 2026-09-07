"""Bounded historical exploration through existing exact hypothesis APIs only."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

import nvda_post_p005_experiment as p
import nvda_bounded_report as reporting
from elliott_runtime.analysis.recursive_child_family_evaluation import validate_recursive_child_family_evaluation_result
from elliott_runtime.analysis.family_hypotheses import validate_family_hypothesis_bridge_result

STAGE = 'NVDA-FULL-HISTORY-HIERARCHICAL-HYPOTHESES-V1'
INPUTS = p.ROOT / 'kernel_reviews/NVDA-BOUNDED-ANALYSIS-REPORT-V1/inputs'
INPUT_MANIFEST_SHA256 = 'bb8d73a6ace250a5d8815cd215760b210913db715fb43d6ef3327a8cb535424e'
RESOLUTIONS = ('1mo', '1wk', '1d', '1h')


def configuration():
    return {
        'classification': 'PROJECT_OPERATIONAL_POLICY_NOT_ELLIOTT_METHODOLOGY',
        'root_resolution': '1mo', 'regions_utc_years': [[1999, 2007], [2008, 2016], [2017, 2026]],
        'windows_per_region': 2, 'window_pivots': 6,
        'regional_order': 'chronological regions; first then last complete six-pivot window',
        'spanning_policy': 'six indices floor(i*(n-1)/5), i=0..5, across full Monthly pivot history; no significance claim',
        'root_order': 'regional windows followed by coarsened spanning proposal',
        'max_root_jobs': 7, 'max_successive_child_levels': 3,
        'expanded_child_bundles_per_root_per_level': 1,
        'branch_order': 'first existing nonempty compatible child-family bundle in source enumeration order; no outcome ranking',
        'child_window': 'earliest six genuine finer pivots within exact parent requirement endpoints',
        'candidate_config': {'max_pivots_considered': 6, 'max_candidate_span_pivots': 6, 'max_skipped_pivots': 0, 'max_candidates_generated': 10},
        'child_limits': {k: v for k,v in p.configuration().items() if k in ('geometry','child','selection','child_family','parent_normal_impulse_cap','child_normal_impulse_cap','parent_family_kinds','child_pivot_window')},
        'duplicates': 'all originating contexts retained; display grouping is not independent confirmation',
        'stop_conditions': ['no finer supplied dataset', 'no compatible child-family bundle', 'branch budget exhausted', 'three child edges', 'existing API bound failure'],
        'degree_authority': False, 'current_position_template_authority': False,
    }


def plan_windows(pivots, regions, per_region=2):
    """Plan by source chronology before observing any methodology outcome."""
    if type(per_region) is not int or not 0 <= per_region <= 2:
        raise ValueError('Regional window budget must be an exact integer in [0,2]')
    jobs, coverage = [], []
    for region_index, (first, last) in enumerate(regions):
        indices = [i for i, x in enumerate(pivots) if first <= x.timestamp_utc.year <= last]
        starts = list(range(max(0, len(indices) - 5)))
        selected = list(dict.fromkeys(([starts[0], starts[-1]] if starts else [])))[:per_region]
        for ordinal, offset in enumerate(selected):
            jobs.append({'job_id': f'region-{region_index + 1}-{ordinal + 1}', 'kind': 'REGIONAL_CONSECUTIVE',
                         'indices': indices[offset:offset + 6], 'region': region_index + 1})
        coverage.append({'region': region_index + 1, 'years': [first, last], 'pivot_indices': indices,
                         'eligible_window_starts': [indices[x] for x in starts],
                         'scheduled_window_starts': [indices[x] for x in selected],
                         'unvisited_window_starts': [indices[x] for x in starts if x not in selected],
                         'reason': 'CALLER_OPERATIONAL_WINDOW_BUDGET' if len(starts) > len(selected) else 'ALL_ELIGIBLE_WINDOWS_SCHEDULED'})
    if len(pivots) >= 6:
        jobs.append({'job_id': 'full-range-coarsened', 'kind': 'COARSENED_SPANNING_HYPOTHESIS',
                     'indices': [i * (len(pivots) - 1) // 5 for i in range(6)], 'region': None})
    return jobs, coverage


def check_child_link(result, item, bridge):
    """Check an existing edge; never synthesize an ancestry credential."""
    validate_recursive_child_family_evaluation_result(result)
    validate_family_hypothesis_bridge_result(bridge)
    if not any(item is x for x in result.child_evaluations) or item.family_hypothesis_result is not bridge:
        raise ValueError('Foreign child-family branch')
    evidence = item.generated_child_evidence
    requirement = evidence.internal_requirement
    if evidence.competing_candidate_set is not bridge.competing_candidate_set:
        raise ValueError('Foreign competing-set identity')
    if any(h.parent_subject is not requirement.child_subject for h in bridge.family_hypotheses):
        raise ValueError('Foreign child subject')
    return requirement


def observation_relation(row, observations):
    start = row['endpoints'][0]['timestamp_utc']; end = row['endpoints'][-1]['timestamp_utc']
    before = sum(b.timestamp_utc.isoformat() < start for b in observations.bars)
    after = sum(b.timestamp_utc.isoformat() > end for b in observations.bars)
    reasons = ['NO_AUTHORIZED_DEVELOPING_POSITION_TEMPLATE', 'FAMILY_PROOF_UNRESOLVED']
    if after: reasons.append('TRAILING_UNASSIGNED_OBSERVATIONS')
    if row['requirement_id'] is None: reasons.append('NO_LINKED_PARENT_REQUIREMENT')
    if row['p004'] and row['p004']['fatal']: reasons.append('EXACT_HYPOTHESIS_REJECTED_P004')
    return {'first_proposed_timestamp': start, 'last_proposed_timestamp': end,
            'latest_observation_timestamp': observations.bars[-1].timestamp_utc.isoformat(),
            'bars_before_proposal': before, 'bars_within_proposal': len(observations.bars) - before - after,
            'trailing_unassigned_bars': after, 'current_position': 'CURRENT_POSITION_UNRESOLVED',
            'reasons': reasons, 'completion_authority': False}


def child_layer(bridge, finer, kernel, at, prefix, geometry):
    refs = (STAGE, prefix)
    internals = p.evaluate_family_internal_subdivisions(p.FamilyInternalSubdivisionEvaluationRequest(prefix + ':internals', bridge, (), refs))
    selections, contexts = [], {}
    for requirement in internals.internal_requirements:
        h = requirement.family_hypothesis
        parent = requirement.parent_candidate.source_observations
        if h.hypothesis_id not in contexts:
            tree = kernel.compose_recursive_candidate(p.RecursiveCandidateCompositionRequest(
                h.hypothesis_id + ':transport', h.bounded_result, (),
                p.OrderedChildBinding(h.hypothesis_id + ':transport-binding', h.parent_subject, ()), refs))
            bundle = p.MultiTimeframeObservationBundle(parent.symbol, (parent, finer), refs)
            contexts[h.hypothesis_id] = kernel.attach_multi_timeframe_observations(p.MultiTimeframeObservationTransportRequest(h.hypothesis_id + ':observations', tree, bundle, (), refs))
        candidate = requirement.parent_candidate
        start, end = candidate.ordered_selected_pivots[requirement.child_index:requirement.child_index + 2]
        interval = tuple(x for x in candidate.source_geometric_pivots.pivots if start.timestamp_utc <= x.timestamp_utc <= end.timestamp_utc)
        window = p.ProposedChildEvaluationWindow(requirement, candidate.source_geometric_pivots, start, end, interval, refs)
        selections.append(p.select_finer_child_observations(p.ChildObservationSelectionRequest(
            requirement.requirement_id + ':selection', requirement, window, contexts[h.hypothesis_id], finer,
            geometry, p.ChildObservationSelectionConfig(10000, 5000), refs)))
    children = p.generate_child_candidate_evidence(p.RecursiveChildCandidateGenerationRequest(
        prefix + ':children', at, internals, p.ChildCandidateGenerationConfig(100, 100, 6, 6, 0, 10, 500, p.SHAPES, 100, 10000), refs, tuple(selections)))
    families = p.evaluate_recursive_child_family_hypotheses(p.RecursiveChildFamilyEvaluationRequest(
        prefix + ':families', at, children, p.ChildFamilyEvaluationConfig(tuple(p.FamilyEvaluationKind), 100, 100, 500, 3, 1500, 1500), refs), kernel)
    partial = p.evaluate_normal_impulse_partial_scope(p.NormalImpulsePartialEvaluationRequest(prefix + ':normal', at, children, 1000, 1000, 1000, refs), kernel)
    return internals, selections, children, families, partial


def audit(doc, datasets):
    rows = doc['hypotheses']; ids = [r['hypothesis_id'] for r in rows]
    if len(ids) != len(set(ids)): raise ValueError('Duplicate hypothesis ID')
    by_id = {r['hypothesis_id']: r for r in rows}
    requirements = {r['requirement_id']: r for r in doc['requirements']}
    prices = 0
    for row in rows:
        if row['authority'] != reporting.AUTHORITY: raise ValueError('Authority leak')
        obs = datasets[row['timeframe']]
        if row['snapshot_content_sha256'] != p.sha(p.encoded(obs)) or row['source_response_sha256'] != obs.provenance.source_sha256:
            raise ValueError('Foreign observation snapshot')
        if row['observation_relation'] != observation_relation(row, obs): raise ValueError('Current-position evidence changed')
        bars = {b.timestamp_utc.isoformat(): b for b in obs.bars}
        for e in row['endpoints']:
            if getattr(bars[e['timestamp_utc']], e['price_field']) != e['price']: raise ValueError('Price differs from saved observation')
            if p.plain(reporting.Fraction(e['price'])) != e['represented_ratio'] or p.plain(bars[e['timestamp_utc']].provenance) != e['bar_provenance']:
                raise ValueError('Exact price ratio or bar provenance changed')
            prices += 1
        if row['requirement_id']:
            req = requirements[row['requirement_id']]; parent = by_id[req['parent_hypothesis_id']]
            if row['parent_family_hypothesis_id'] != parent['hypothesis_id'] or row['level'] != parent['level'] + 1 or row['root_job'] != parent['root_job']:
                raise ValueError('Cross-branch reporting substitution')
            if not req['start'] <= row['endpoints'][0]['timestamp_utc'] <= row['endpoints'][-1]['timestamp_utc'] <= req['end']:
                raise ValueError('Child proposal escaped parent evaluation window')
        if row['p004']:
            rejected = row['p004']['status'] == 'RULE_VIOLATED'
            if rejected != row['p004']['fatal'] or rejected != (row['report_status'] == 'REJECTED_EXACT_HYPOTHESIS_P004'):
                raise ValueError('P004 rejection concealed')
    if any(r['requirement_satisfied'] for r in doc['requirements']): raise ValueError('False internal proof')
    return {'result': 'PASS', 'hypotheses': len(rows), 'requirements': len(requirements), 'prices_verified': prices,
            'linked_rows': sum(r['requirement_id'] is not None for r in rows),
            'max_observed_link_level': max((r['level'] for r in rows), default=0)}


def render(doc):
    rows = doc['hypotheses']; by_id = {r['hypothesis_id']: r for r in rows}
    lines = ['# NVDA historical hypotheses', '', '## Technical summary', '',
             'Bounded candidate exploration only: no complete validated Elliott count, current-wave claim or directional forecast is established.', '',
             f"{len(rows)} hypotheses were retained. Hierarchy levels are operational, never Elliott degrees. Current position remains unresolved for every context.", '',
             '## Four distinct capabilities', '',
             '- A. Bounded search across all three historical regions, not exhaustive full-history search.',
             '- B. Coarsened full-range endpoint proposals exist; they are not a coherent full-history Elliott count. Prefix/tail observations and unexamined interiors remain unresolved.',
             f"- C. The run retained exact links through {doc['audit']['max_observed_link_level']} child level(s). Unvisited branches are not reviewed or terminal.",
             '- D. No defensible current-position hypothesis is established. Final pivots do not authorize current or next-wave labels.', '',
             '## Data and definitions', '',
             'Reuses the preserved Yahoo capture from 6 September 2026. Latest bars are dated 4 September 2026. No fresh retrieval or resampling. Root resolution is Monthly; explicit finer selections are Weekly, Daily and 1H. Resolution is not degree.', '',
             'A window is a search scope, a hypothesis is an unconfirmed proposed structure, and a linked row is an exact parent-requirement evaluation context. Repeated endpoints are not independent confirmations.', '',
             '## Historical coverage and exclusions', '',
             'Regions retain scheduled and unvisited six-pivot windows separately. One additional coarsened proposal samples six source indices evenly across the full pivot range; this is an operational sampling policy, not important-wave selection.', '',
             '| Region | Years | Pivots | Examined windows | Unvisited windows |', '|---|---|---:|---:|---:|']
    for c in doc['coverage']:
        lines.append(f"| {c['region']} | {c['years'][0]}–{c['years'][1]} | {len(c['pivot_indices'])} | {len(c['scheduled_window_starts'])} | {len(c['unvisited_window_starts'])} |")
    lines += ['', f"Cross-region six-pivot windows excluded by the regional policy: {len(doc['cross_region_window_starts_excluded_by_policy'])}. Their exact start indices remain in JSON.", '',
              '## Linked hypothesis lookup', '', 'Each row below identifies a generated hypothesis and its exact parent requirement. The compact view shows the first hypothesis of each family per root and level, without ranking. JSON/CSV retain every executed context.', '',
              '| Ref | Root | Level | Family hypothesis | Parent | Requirement | P004 | P005 | Unassigned trailing bars |', '|---|---|---:|---|---|---|---|---|---:|']
    seen = set(); samples = []
    for r in rows:
        key = (r['root_job'], r['level'], r['family'])
        if key in seen: continue
        seen.add(key); samples.append(r)
        parent = by_id[r['parent_family_hypothesis_id']]['display_ref'] if r['parent_family_hypothesis_id'] else '—'
        req = next((x['display_ref'] for x in doc['requirements'] if x['requirement_id'] == r['requirement_id']), '—')
        lines.append(f"| {r['display_ref']} | {r['root_job']} | {r['level']} | {r['family']} | {parent} | {req} | {r['p004']['status'] if r['p004'] else 'not executed'} | {r['p005']['status'] if r['p005'] else 'not executed'} | {r['observation_relation']['trailing_unassigned_bars']} |")
    lines += ['', '## Proposed components', '', 'Prices below are exact transported HIGH/LOW observations rounded only for readable display; JSON/CSV preserve represented values. Labels are hypothesis slots, not orthodox endpoints. Direction for generic families is unassigned. No row is a forecast.', '']
    component_seen = set()
    for r in samples:
        component_key = (r['root_job'], r['level'], r['candidate_shape'], bool(r['p004']))
        if component_key in component_seen: continue
        component_seen.add(component_key)
        lines += [f"### {r['display_ref']} — {r['family']} ({r['timeframe']}, {r['direction']})", '', '| Slot | Start UTC | Price | End UTC | Price |', '|---|---|---:|---|---:|']
        for a,b in zip(r['endpoints'][::2], r['endpoints'][1::2], strict=True):
            lines.append(f"| {a['role']} | {a['timestamp_utc'][:10]} | {a['price']:.6g} | {b['timestamp_utc'][:10]} | {b['price']:.6g} |")
        lines += ['', 'Current position: unresolved. ' + ', '.join(r['observation_relation']['reasons']) + '.', '']
    lines += ['## Limits and unresolved dependencies', '',
              'Every P004 rejection remains local and fatal even if P005 establishes sufficiency. All internal requirements remain unsatisfied; cardinality and partial checks cannot supply a family certificate.', '',
              *('- ' + x for x in reporting.BLOCKERS), '',
              'Branch budgets, no-child cases and missing finer history are listed below. An unvisited branch is not an impossible family. Exact unvisited requirement IDs remain in JSON.', '',
              '| Root | Level | Child bundles | Expanded onward | Unvisited | Coverage | Stop |', '|---|---:|---:|---:|---:|---|---|',
              *(f"| {x['root']} | {x['level']} | {x['available_child_bundles']} | {x['expanded_next_level']} | {len(x['unvisited_requirement_ids'])} | {x['coverage_counts']} | {x['reason']} |" for x in doc['stops']), '',
              '## Reproducibility and next decision', '',
              'Use the baseline README command and unchanged preserved inputs. Review the unvisited historical regions and branch budgets before authorizing broader computation. Exact-family proof and a developing-position contract require separate authority; this run does not resolve those gates.', '']
    return '\n'.join(lines)


def run(inputs, output, progress=print):
    output = Path(output).resolve()
    if output.exists() or not output.is_relative_to(p.ROOT): raise ValueError('Output must be a new Runtime directory')
    manifest, data = p.load_inputs(Path(inputs)); cfg = configuration(); at = manifest['requested_at_utc']
    if p.sha((Path(inputs)/'input_manifest.json').read_bytes()) != INPUT_MANIFEST_SHA256:
        raise ValueError('This stage is pinned to the approved preserved capture')
    geometry = p.GeometricPivotDiscoveryConfig(p.GeometricPivotDiscoveryMethod.WINDOWED_LOCAL_EXTREMA, 2, 2, p.EqualExtremePolicy.LAST, True)
    pivots = p.discover_geometric_pivots(p.GeometricPivotDiscoveryRequest(STAGE + ':root-pivots', data['1mo'], geometry, (STAGE,)))
    jobs, coverage = plan_windows(pivots.pivots, cfg['regions_utc_years'])
    region_starts = {i for region in coverage for i in region['eligible_window_starts']}
    excluded_cross_region = [i for i in range(max(0, len(pivots.pivots)-5)) if i not in region_starts]
    if len(jobs) > cfg['max_root_jobs']: raise ValueError('Root budget exceeded before execution')
    reporting.write_bytes_new(output / 'configuration.json', p.encoded(cfg))
    reporting.write_bytes_new(output / 'search_plan.json', p.encoded({'jobs': jobs, 'coverage': coverage}))
    kernel = p.MethodologyKernel(Path('C:/ElliottCodex/Brain_LOCKED')); rows=[]; requirements=[]; stops=[]; live=[]
    def add(new, job, level):
        for row in new:
            row.update(root_job=job, level=level, degree='DEGREE_UNRESOLVED')
            row['observation_relation'] = observation_relation(row, data[row['timeframe']])
            rows.append(row)
    for job in jobs:
        prefix = STAGE + ':' + job['job_id']; refs=(STAGE, prefix)
        job['source_pivots_excluded_from_this_job'] = len(pivots.pivots) - len(job['indices'])
        job['actual_selected_timestamps'] = [pivots.pivots[i].timestamp_utc.isoformat() for i in job['indices']]
        progress(prefix + ':root')
        generated = p.generate_candidate_hypotheses(p.CandidateGenerationRequest(prefix, at, p.AnalyzedWaveSubject(prefix, data['1mo'].provenance.source_sha256), data['1mo'], pivots,
            p.CandidateGenerationConfig(6,6,0,10,p.SHAPES,p.CandidatePivotWindow.EARLIEST), (), refs, tuple(pivots.pivots[i] for i in job['indices'])))
        competing = p.build_competing_candidate_set(p.CompetingCandidateSetRequest(prefix+':set', prefix, generated, refs))
        bridge = p.build_family_evaluation_hypotheses(p.FamilyHypothesisBridgeRequest(prefix+':families',at,competing,tuple(p.FamilyEvaluationKind),refs),kernel)
        partial=p.evaluate_normal_impulse_partial_scope(p.NormalImpulsePartialEvaluationRequest(prefix+':normal',at,bridge,100,100,100,refs),kernel)
        add(reporting.family_rows(bridge,'level-0',job['job_id'])+reporting.normal_rows(partial,'level-0',job['job_id']),job['job_id'],0)
        chain=[]
        for level in range(1, cfg['max_successive_child_levels']+1):
            progress(prefix+f':level-{level}')
            for parent_result,item,child_bridge in chain: check_child_link(parent_result,item,child_bridge)
            internals,selections,children,families,partial=child_layer(bridge,data[RESOLUTIONS[level]],kernel,at,prefix+f':level-{level}',geometry)
            live.append((bridge,internals,children,families,partial,tuple(chain)))
            for req,selection,outcome in zip(internals.internal_requirements,selections,children.requirement_outcomes,strict=True):
                requirements.append({'requirement_id':req.requirement_id,'parent_hypothesis_id':req.family_hypothesis.hypothesis_id,'child_index':req.child_index,
                    'shape':req.required_internal_shape.value,'source_class':req.source_class,'protected_refs':list(req.protected_refs),
                    'start':selection.selected_window.parent_window_start_utc.isoformat(),'end':selection.selected_window.parent_window_end_utc.isoformat(),
                    'coverage':selection.selected_window.coverage_state.value,'generation_status':outcome.status.value,
                    'bars':len(selection.selected_window.ordered_bars),'requirement_satisfied':False})
            available=[]
            for item in families.child_evaluations:
                child_bridge=item.family_hypothesis_result
                if child_bridge is not None and child_bridge.family_hypotheses:
                    req=check_child_link(families,item,child_bridge)
                    add(reporting.family_rows(child_bridge,f'level-{level}',job['job_id'],req),job['job_id'],level)
                    available.append(item)
            add(reporting.normal_rows(partial,f'level-{level}',job['job_id']),job['job_id'],level)
            stops.append({'root':job['job_id'],'level':level,'available_child_bundles':len(available),
                'expanded_next_level':1 if available and level<cfg['max_successive_child_levels'] else 0,
                'unvisited_requirement_ids':[x.generated_child_evidence.internal_requirement.requirement_id for x in (available[1:] if level<cfg['max_successive_child_levels'] else available)],
                'reason':'NO_COMPATIBLE_CHILD_BUNDLE' if not available else 'LEVEL_BUDGET' if level==cfg['max_successive_child_levels'] else 'BRANCH_BUDGET',
                'coverage_counts':dict(Counter(s.selected_window.coverage_state.value for s in selections))})
            if not available: break
            chosen=available[0]; bridge=chosen.family_hypothesis_result; chain.append((families,chosen,bridge))
    for bridge,internals,children,families,partial,chain in live:
        reporting.validate_family_hypothesis_bridge_result(bridge)
        reporting.validate_family_internal_subdivision_evaluation_result(internals)
        validate_recursive_child_family_evaluation_result(families)
        reporting.validate_normal_impulse_partial_evaluation_result(partial)
        for x in chain: check_child_link(*x)
    doc={'stage':STAGE,'configuration':cfg,'data':reporting.data_notes(Path(inputs),manifest,data,'OFFLINE_REPLAY'),
         'jobs':jobs,'coverage':coverage,'hypotheses':rows,'requirements':requirements,'stops':stops,
         'cross_region_window_starts_excluded_by_policy':excluded_cross_region,
         'inventories':{'methodology':11,'structural_producers':7,'family_producers':0,'family_issuances':0}}
    reporting.assign_display_refs(doc)
    for i,r in enumerate(requirements,1):r['display_ref']=f'R{i:04}'
    doc['groups']=reporting.group_rows(rows);doc['audit']=audit(doc,data)
    reporting.write_bytes_new(output/'results.json',p.encoded(doc))
    reporting.write_bytes_new(output/'report.md',render(doc).encode())
    for name,text in reporting.evidence_exports(doc).items():reporting.write_bytes_new(output/name,text.encode())
    return doc


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs',type=Path,default=INPUTS);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=run(args.inputs,args.output,lambda x:print(x,flush=True));print(json.dumps(result['audit']))
