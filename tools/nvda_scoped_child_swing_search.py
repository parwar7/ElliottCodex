"""Offline, exact scoped child search comparison on the approved scale-2 roots."""
import argparse
from collections import Counter
from pathlib import Path

import nvda_geometric_swing_quality as previous
from elliott_runtime.analysis.geometric_swing_search import select_child_geometric_swing_scope

p = previous.p
h = previous.hierarchy
r = previous.reporting
STAGE = 'EXACT-SCOPED-CHILD-SWING-SEARCH-TRANSPORT-V1'
PREVIOUS = p.ROOT / 'kernel_reviews/NVDA-GEOMETRIC-SWING-CANDIDATE-QUALITY-V1'
PREVIOUS_MANIFEST_SHA = '7bf5845b8929ac8a236076d8a75432c5365ad5530ec6de1dc52ccd9248fa8a53'


def history():
    path = PREVIOUS / 'NVDA_GEOMETRIC_SWING_CANDIDATE_QUALITY_manifest.json'
    if p.sha(path.read_bytes()) != PREVIOUS_MANIFEST_SHA:
        raise ValueError('Previous baseline manifest changed')
    manifest = p.json.loads(path.read_bytes())
    entry = next(x for x in manifest['artifacts'] if x['path'].endswith('/report/results.json'))
    data = (PREVIOUS / 'report/results.json').read_bytes()
    if p.sha(data) != entry['sha256']:
        raise ValueError('Previous results changed')
    return p.json.loads(data)


def select_scopes(selections):
    scopes, records = [], []
    for selection in selections:
        window = selection.request.proposed_child_window
        config = previous.GeometricSwingSearchConfig(
            ((window.start_pivot.timestamp_utc.year, window.end_pivot.timestamp_utc.year),),
            1, 10000, 10000)
        scope, diagnostic = select_child_geometric_swing_scope(selection, config)
        if scope is not None:
            scopes.append(scope)
        records.append({'requirement_id': selection.request.internal_requirement.requirement_id,
                        'selection_id': selection.request.selection_id,
                        'snapshot_content_sha256': p.sha(p.encoded(selection.request.selected_observations)),
                        'source_pivots': [] if selection.finer_geometric_pivots is None else previous.pivot_records(selection.finer_geometric_pivots),
                        'config': p.plain(config), 'diagnostics': diagnostic})
    return tuple(scopes), records


def rows_for_children(families, partial, job):
    rows = []
    for item in families.child_evaluations:
        if item.family_hypothesis_result is not None:
            requirement = h.check_child_link(families, item, item.family_hypothesis_result)
            rows.extend(r.family_rows(item.family_hypothesis_result, 'child', job, requirement))
    rows.extend(r.normal_rows(partial, 'child', job))
    return rows


def audit(doc, datasets):
    receipts = {}
    for mode in ('before', 'after'):
        part = doc[mode]
        receipts[mode] = h.audit(part, datasets)
        if part['totals'] != previous.totals(part['hypotheses']):
            raise ValueError('Comparison totals differ from actual rows')
        for row in part['hypotheses']:
            if row['geometric_domain'] != previous.row_domain(row):
                raise ValueError('Geometric membership differs')
            if mode == 'after' and not row['geometric_domain']['eligible']:
                raise ValueError('Out-of-domain scoped hypothesis')
            if row['p004']:
                trace = row['p005_observation_trace']
                for behavior in ('p004', 'p005'):
                    for field in ('status', 'reason'):
                        if row[behavior][field] != trace[behavior + '_' + field]:
                            raise ValueError('Reported outcome differs from live evaluation trace')
                if (row['p004']['fatal'] != trace['p004_fatal']
                        or row['p005']['percentage_movements'] != trace['percentage_movements']
                        or row['snapshot_content_sha256'] != trace['snapshot_content_sha256']
                        or row['requirement_id'] != trace['child_requirement_id']
                        or trace['exact_runtime_identity_checks_passed'] is not True):
                    raise ValueError('Original P004/P005 ancestry or outcome trace differs')
                endpoints = {(x['role'], x['edge']): x for x in row['endpoints']}
                for endpoint in trace['endpoints']:
                    original = endpoints[(endpoint['role'], endpoint['edge'])]
                    for field in ('pivot_id', 'timestamp_utc', 'price_field', 'price',
                                  'represented_ratio', 'bar_provenance', 'pivot_state'):
                        if original[field] != endpoint[field]:
                            raise ValueError('Role operand differs from original observation trace')
    historical = history()
    historical_rows = [x for x in historical['hypotheses'] if ':scale-2:' in x['root_job']]
    if previous.totals(historical_rows) != doc['before']['totals']:
        raise ValueError('Unfiltered replay differs from historical scale-2 result')
    if doc['before']['requirements'] != doc['after']['requirements']:
        raise ValueError('Comparison changed originating requirements')
    requirements = {x['requirement_id']: x for x in doc['after']['requirements']}
    scopes = {x['requirement_id']: x for x in doc['scopes']}
    if len(scopes) != len(doc['scopes']) or set(scopes) != set(requirements):
        raise ValueError('Scope coverage must account for every exact requirement once')
    for record in scopes.values():
        diagnostic = record['diagnostics']; req = requirements[record['requirement_id']]
        if record['snapshot_content_sha256'] != p.sha(p.encoded(datasets['1wk'])):
            raise ValueError('Scope observation snapshot changed')
        pivots = record['source_pivots']; by_id = {x['pivot_id']: x for x in pivots}
        bars = {x.timestamp_utc.isoformat(): x for x in datasets['1wk'].bars}
        for pivot in pivots:
            if (not req['start'] <= pivot['timestamp'] <= req['end']
                    or pivot['price'] != getattr(bars[pivot['timestamp']], pivot['price_field'])
                    or pivot['bar_provenance'] != p.plain(bars[pivot['timestamp']].provenance)):
                raise ValueError('Scope pivot escaped its exact saved window/observation')
        selected = diagnostic['selected_pivot_ids']; omitted = diagnostic['omitted_pivot_ids']
        if len(selected) + len(omitted) != len(pivots) or set(selected) & set(omitted) or set(selected + omitted) != set(by_id):
            raise ValueError('Unaccounted pivot omission')
        windows = diagnostic.get('windows', [])
        if len(windows) != max(0, len(pivots) - 5):
            raise ValueError('Unaccounted six-pivot search context')
        eligible = []
        for i, window in enumerate(windows):
            values = pivots[i:i + 6]
            if window['start_index'] != i or window['pivot_ids'] != [x['pivot_id'] for x in values] or window['domain'] != previous.movement_domain(tuple(x['price'] for x in values)):
                raise ValueError('Search-domain audit differs')
            if window['domain']['eligible']:
                eligible.append(i)
            expected = 'SEARCH_DOMAIN_EXCLUDED' if not window['domain']['eligible'] else 'SELECTED' if i == eligible[0] else 'UNVISITED_BUDGET'
            if window['disposition'] != expected:
                raise ValueError('Outcome-independent scope budget changed')
        expected_selected = [] if not eligible else [x['pivot_id'] for x in pivots[eligible[0]:eligible[0] + 6]]
        if selected != expected_selected:
            raise ValueError('Scope is not the first chronological eligible sequence')
    for row in doc['after']['hypotheses']:
        if row['path'] == 'child':
            record = scopes[row['requirement_id']]
            if any(x['pivot_id'] not in record['diagnostics']['selected_pivot_ids'] for x in row['endpoints']):
                raise ValueError('Child endpoint does not belong to its exact selected scope')
    receipts['search_scopes_verified'] = len(scopes)
    receipts['historical_58_are_hypothesis_occurrences_not_unique_invalid_waves'] = True
    return receipts


def render(doc):
    doc = p.json.loads(p.encoded(doc))
    lines = ['# Exact scoped NVDA child search', '',
             'Same saved Yahoo capture and the same three scale-2 Monthly parent roots. One Weekly child level only; no new retrieval or resampling.', '',
             'One first chronological nonzero alternating six-pivot scope per requirement. Other eligible scopes remain unvisited; this is operational selection, not Elliott validation or ranking.', '',
             '| Mode/path | Candidate contexts | Hypotheses | P004 | P005 | Outside domain |',
             '|---|---:|---:|---|---|---:|']
    for mode in ('before', 'after'):
        for path, values in doc[mode]['totals'].items():
            lines.append(f"| {mode}/{path} | {values['candidate_contexts']} | {values['hypotheses']} | {values['p004']} | {values['p005']} | {values['outside_geometric_domain']} |")
    for mode in ('before', 'after'):
        values = doc[mode]['totals']['child']
        lines += ['', f"{mode}: P004-invalid despite P005 sufficiency = {values['p004_invalid_despite_p005_sufficiency']}; unresolved P005 reasons = {values['p005_unresolved_reasons']}."]
    reasons = Counter(x['diagnostics']['reason'] for x in doc['scopes'])
    dispositions = Counter(w['disposition'] for x in doc['scopes'] for w in x['diagnostics'].get('windows', []))
    lines += ['', f'Scope reasons: {dict(reasons)}.', '', f'Six-pivot context dispositions: {dict(dispositions)}.', '',
              'The previous 58 out-of-domain child hypothesis occurrences were not 58 unique invalid waves. Domain exclusion produces no structural certificate. P004 remains fatal locally and P005 cannot rescue it.', '',
              'All 84 internal requirements remain unsatisfied. P006 and Flat/Triangle freezes, missing family producers and SOURCE_DERIVED_BASE_CASE_NOT_FOUND remain. No current-position inference, validated family, complete count, forecast or trading signal.', '',
              'Next stage: BOUNDED-CHILD-SCOPE-COVERAGE-REVIEW-V1 (engineering decision only): quantify the unvisited eligible scopes before considering any separately approved multi-scope transport extension. This is not a proposal to reopen frozen methodology.', '',
              'Full exact endpoint/role/field/snapshot evidence and original requirement links are retained in results.json and before/after CSV exports. Missing results in this bounded search are not proof of family impossibility.', '']
    return '\n'.join(lines)


def run(output, progress=print):
    output = Path(output).resolve()
    if output.exists() or not output.is_relative_to(p.ROOT):
        raise ValueError('Output must be a new Runtime directory')
    history()
    if p.sha((h.INPUTS / 'input_manifest.json').read_bytes()) != h.INPUT_MANIFEST_SHA256:
        raise ValueError('Saved capture changed')
    manifest, data = p.load_inputs(h.INPUTS)
    at = manifest['requested_at_utc']; refs = (previous.STAGE,)
    kernel = p.MethodologyKernel(Path('C:/ElliottCodex/Brain_LOCKED'))
    geometry = p.GeometricPivotDiscoveryConfig(p.GeometricPivotDiscoveryMethod.WINDOWED_LOCAL_EXTREMA, 2, 2, p.EqualExtremePolicy.LAST, True)
    prefix = previous.STAGE + ':scale-2'
    discovered = p.discover_geometric_pivots(p.GeometricPivotDiscoveryRequest(prefix, data['1mo'], geometry, refs))
    template = p.CandidateGenerationRequest(prefix, at, p.AnalyzedWaveSubject(prefix, data['1mo'].provenance.source_sha256), data['1mo'], discovered,
        p.CandidateGenerationConfig(6, 6, 0, 4, p.SHAPES, p.CandidatePivotWindow.EARLIEST), (), refs)
    requests, coverage = previous.select_geometric_swing_requests(template, previous.GeometricSwingSearchConfig(((1999, 2007), (2008, 2016), (2017, 2026)), 1, 10000, 10000))
    if [x.request_id for x in requests] != [prefix + ':swing:' + str(i) for i in (5, 24, 49)]:
        raise ValueError('Approved parent roots changed')
    doc = {'stage': STAGE, 'before': {'hypotheses': [], 'requirements': []}, 'after': {'hypotheses': [], 'requirements': []}, 'scopes': [],
           'capture_manifest_sha256': h.INPUT_MANIFEST_SHA256, 'data': r.data_notes(h.INPUTS, manifest, data, 'OFFLINE_REPLAY'),
           'configuration': previous.configuration(), 'root_coverage': coverage,
           'inventories': {'methodology': 11, 'structural_producers': 7, 'family_producers': 0, 'family_issuances': 0}}
    doc['configuration'].update(geometry_windows=[2], max_root_jobs=3,
        child_search_domain='EXACT_OPTIONAL_SCOPE; first eligible six-pivot sequence per requirement; budget one',
        scope_budget_per_requirement=1)
    def add(mode, values, job, level):
        for row in values:
            row.update(root_job=job, level=level, degree='DEGREE_UNRESOLVED')
            row['geometric_domain'] = previous.row_domain(row)
            row['observation_relation'] = h.observation_relation(row, data[row['timeframe']])
            doc[mode]['hypotheses'].append(row)
    for request in requests:
        job = request.request_id; progress(job)
        generated = p.generate_candidate_hypotheses(request)
        competing = p.build_competing_candidate_set(p.CompetingCandidateSetRequest(job + ':set', job, generated, refs))
        bridge = p.build_family_evaluation_hypotheses(p.FamilyHypothesisBridgeRequest(job + ':family', at, competing, tuple(p.FamilyEvaluationKind), refs), kernel)
        partial = p.evaluate_normal_impulse_partial_scope(p.NormalImpulsePartialEvaluationRequest(job + ':normal', at, bridge, 100, 100, 100, refs), kernel)
        for mode in ('before', 'after'):
            add(mode, r.family_rows(bridge, 'parent', job) + r.normal_rows(partial, 'parent', job), job, 0)
        internals, selections, before, before_families, before_partial = h.child_layer(bridge, data['1wk'], kernel, at, job + ':child', geometry)
        scopes, records = select_scopes(selections)
        doc['scopes'].extend(records)
        scoped_request = p.RecursiveChildCandidateGenerationRequest(job + ':scoped-children', at, internals, before.request.config, refs, tuple(selections), scopes)
        after = p.generate_child_candidate_evidence(scoped_request)
        families = p.evaluate_recursive_child_family_hypotheses(p.RecursiveChildFamilyEvaluationRequest(job + ':scoped-families', at, after, before_families.request.config, refs), kernel)
        child_partial = p.evaluate_normal_impulse_partial_scope(p.NormalImpulsePartialEvaluationRequest(job + ':scoped-normal', at, after, 1000, 1000, 1000, refs), kernel)
        add('before', rows_for_children(before_families, before_partial, job), job, 1)
        add('after', rows_for_children(families, child_partial, job), job, 1)
        for req, selection in zip(internals.internal_requirements, selections, strict=True):
            record = {'requirement_id': req.requirement_id, 'parent_hypothesis_id': req.family_hypothesis.hypothesis_id,
                      'child_index': req.child_index, 'shape': req.required_internal_shape.value,
                      'start': selection.selected_window.parent_window_start_utc.isoformat(),
                      'end': selection.selected_window.parent_window_end_utc.isoformat(),
                      'coverage': selection.selected_window.coverage_state.value, 'requirement_satisfied': False}
            for mode, result in (('before', before), ('after', after)):
                doc[mode]['requirements'].append(dict(record))
                doc[mode].setdefault('generation_outcomes', []).append({'requirement_id': req.requirement_id,
                    'status': next(o.status.value for o in result.requirement_outcomes if o.internal_requirement is req)})
        # Validate live ancestry through ordinary consumers, without reconstructing IDs.
        before._validated(); after._validated()
        h.validate_recursive_child_family_evaluation_result(families)
        r.validate_normal_impulse_partial_evaluation_result(child_partial)
    for mode in ('before', 'after'):
        part = doc[mode]
        r.assign_display_refs(part)
        part['groups'] = r.group_rows(part['hypotheses'])
        part['totals'] = previous.totals(part['hypotheses'])
    doc['audit'] = audit(doc, data)
    r.write_bytes_new(output / 'results.json', p.encoded(doc))
    r.write_bytes_new(output / 'report.md', render(doc).encode())
    for mode in ('before', 'after'):
        for name, text in r.evidence_exports(doc[mode]).items():
            r.write_bytes_new(output / mode / name, text.encode())
    return doc


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    doc = run(args.output, lambda message: print(message, flush=True))
    print(p.json.dumps({mode: doc[mode]['totals'] for mode in ('before', 'after')}))
