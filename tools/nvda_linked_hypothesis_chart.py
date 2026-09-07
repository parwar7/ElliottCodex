"""Read-only projection of a hash-locked saved experiment into an offline viewer.

No factory issuance, analysis, endpoint selection or market retrieval occurs here.
JSON identifiers preserve recorded context; deserialization grants no live authority.
"""
import argparse
import copy
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGE = 'NVDA-LINKED-HYPOTHESIS-CHART-V1'
PREVIOUS = ROOT / 'kernel_reviews/EXACT-SCOPED-CHILD-SWING-SEARCH-TRANSPORT-V1'
PREVIOUS_HASH = '414d11c24974db3c05114762325025ddbb23dbaebf18d5e83687fe71dcff1019'
INPUTS = ROOT / 'kernel_reviews/NVDA-BOUNDED-ANALYSIS-REPORT-V1/inputs'
INPUT_HASH = 'bb8d73a6ace250a5d8815cd215760b210913db715fb43d6ef3327a8cb535424e'
TEMPLATE = Path(__file__).with_name('nvda_linked_hypothesis_chart.html')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode('utf-8')


def verify_manifest(path, digest, root, entries_key):
    raw = path.read_bytes()
    if sha(raw) != digest:
        raise ValueError('Manifest hash mismatch: ' + str(path))
    manifest = json.loads(raw)
    for entry in manifest[entries_key]:
        target = (root / entry['path']).resolve()
        if not target.is_relative_to(root.resolve()):
            raise ValueError('Manifest path escapes root')
        data = target.read_bytes()
        if sha(data) != entry['sha256'] or len(data) != entry.get('bytes', entry.get('byte_length')):
            raise ValueError('Manifest entry mismatch: ' + str(target))
    return manifest


def load_evidence():
    """Verify artifacts before parsing; reuse existing read-only observation audit."""
    verify_manifest(PREVIOUS / 'EXACT_SCOPED_CHILD_SWING_SEARCH_TRANSPORT_manifest.json', PREVIOUS_HASH, ROOT, 'artifacts')
    verify_manifest(INPUTS / 'input_manifest.json', INPUT_HASH, INPUTS, 'files')
    import nvda_scoped_child_swing_search as saved
    _, datasets = saved.p.load_inputs(INPUTS)
    document = json.loads((PREVIOUS / 'report/results.json').read_bytes())
    receipt = saved.audit(document, datasets)
    return document, datasets, receipt


def reach(row):
    """Display only the already recorded position boundary, never infer active waves."""
    relation = copy.deepcopy(row['observation_relation'])
    return {
        'status': 'CURRENT_WAVE_POSITION_UNRESOLVED',
        'last_evidenced_endpoint': row['endpoints'][-1]['timestamp_utc'],
        'last_evidenced_price': repr(row['endpoints'][-1]['price']),
        'latest_observation_timestamp': relation['latest_observation_timestamp'],
        'trailing_unassigned_bars': relation['trailing_unassigned_bars'],
        'bound_developing_component': 'NOT_ESTABLISHED_IN_SAVED_EVIDENCE',
        'developing_geometric_endpoints': sum(e['pivot_state'] == 'DEVELOPING' for e in row['endpoints']),
        'reasons': relation['reasons'],
        'caveat': 'Geometric developing metadata is not a bound active-wave component. Absence is not completion proof.',
    }


def project(document, datasets):
    """Lossless selected fields; no deduplication by endpoint coordinates."""
    rows = []
    fields = ('hypothesis_id', 'candidate_id', 'binding_id', 'requirement_id',
              'parent_family_hypothesis_id', 'display_ref', 'family', 'path', 'level',
              'root_job', 'timeframe', 'snapshot_content_sha256', 'source_response_sha256',
              'candidate_shape', 'direction', 'endpoints', 'p004', 'p005', 'state',
              'authority', 'coverage', 'unresolved_reasons', 'observation_relation', 'group_id')
    for original in document['after']['hypotheses']:
        row = {key: copy.deepcopy(original[key]) for key in fields}
        row['report_status'] = original.get('report_status')
        row['role_authority'] = original.get('role_authority', 'PROPOSED_DIRECT_CHILD_SLOTS_ONLY')
        row['reach'] = reach(original)
        row['checks'] = copy.deepcopy(original.get('checks', []))
        row['p005_observation_trace'] = copy.deepcopy(original.get('p005_observation_trace'))
        for endpoint in row['endpoints']:
            endpoint['represented_price_text'] = repr(endpoint['price'])
        rows.append(row)
    scopes = []
    for source in document['scopes']:
        diagnostic = source['diagnostics']
        scopes.append({
            'requirement_id': source['requirement_id'], 'selection_id': source['selection_id'],
            'snapshot_content_sha256': source['snapshot_content_sha256'],
            'config': copy.deepcopy(source['config']),
            'reason': diagnostic['reason'],
            'source_pivot_ids': copy.deepcopy(diagnostic['source_pivot_ids']),
            'selected_pivot_ids': copy.deepcopy(diagnostic['selected_pivot_ids']),
            'omitted_pivot_ids': copy.deepcopy(diagnostic['omitted_pivot_ids']),
            'dispositions': dict(Counter(w['disposition'] for w in diagnostic.get('windows', []))),
            'regions': copy.deepcopy(diagnostic.get('regions', [])),
        })
    prices = {}
    for timeframe in ('1mo', '1wk', '1d'):
        observations = datasets[timeframe]
        # Background close only; never substituted for high/low role operands.
        prices[timeframe] = [[b.timestamp_utc.isoformat(), b.close] for b in observations.bars]
    return {
        'stage': STAGE, 'kind': 'READ_ONLY_RENDERING_PROJECTION_NOT_AUTHORITY',
        'source': {'baseline': str(PREVIOUS.relative_to(ROOT)).replace('\\', '/'),
                   'manifest_sha256': PREVIOUS_HASH, 'capture_manifest_sha256': INPUT_HASH,
                   'results_sha256': sha((PREVIOUS / 'report/results.json').read_bytes())},
        'data': copy.deepcopy(document['data']), 'prices_close_usd': prices,
        'hypotheses': rows, 'requirements': copy.deepcopy(document['after']['requirements']),
        'generation_outcomes': copy.deepcopy(document['after']['generation_outcomes']),
        'scopes': scopes, 'configuration': copy.deepcopy(document['configuration']),
        'root_coverage': copy.deepcopy(document['root_coverage']),
        'inventories': copy.deepcopy(document['inventories']),
        'limitations': ['P006_UNRESOLVED_METHODOLOGY_DEPENDENCY_CONFLICT',
                        'FLAT_TRIANGLE_FROZEN_SCOPE_UNCHANGED',
                        'SOURCE_DERIVED_BASE_CASE_NOT_FOUND',
                        'NO_VALIDATED_FAMILY_NO_RANKING_NO_FORECAST',
                        'TIMEFRAME_AND_RECURSION_LEVEL_ARE_NOT_ELLIOTT_DEGREE',
                        'LEGACY_ANALYZE_NOT_IMPLEMENTED'],
    }


def validate_export(export, document, datasets):
    """Exact projection equality guards labels, all links, prices and scope accounting."""
    if encoded(export) != encoded(project(document, datasets)):
        raise ValueError('Export differs from canonical saved evidence projection')
    ids = [r['hypothesis_id'] for r in export['hypotheses']]
    if len(ids) != len(set(ids)):
        raise ValueError('Repeated ID, not repeated coordinates')
    return {'hypotheses': len(ids), 'endpoint_occurrences': sum(len(r['endpoints']) for r in export['hypotheses']),
            'linked_child_occurrences': sum(r['path'] == 'child' for r in export['hypotheses']),
            'requirements': len(export['requirements']), 'result': 'PASS'}


def render(export):
    payload = encoded(export).decode().replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    return TEMPLATE.read_text(encoding='utf-8').replace('/*CANONICAL_JSON*/', payload)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output == ROOT or not output.is_relative_to(ROOT):
        raise ValueError('Output must be beneath Runtime')
    document, datasets, receipt = load_evidence()
    export = project(document, datasets)
    audit = {'saved_evidence_audit': receipt, 'export': validate_export(export, document, datasets)}
    import nvda_bounded_report as reporting
    for name, data in [('canonical.json', encoded(export)), ('chart.html', render(export).encode('utf-8')),
                       ('render_audit.json', encoded(audit))]:
        reporting.write_bytes_new(output / name, data)
    print(json.dumps(audit))


if __name__ == '__main__':
    main()
