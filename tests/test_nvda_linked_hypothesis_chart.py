"""Saved evidence projection tests; no live network or hypothesis generation."""
import copy
import json
import sys
import unittest
from collections import Counter
from unittest.mock import patch
import support

sys.path.insert(0, str(support.RUNTIME_ROOT / 'tools'))
import nvda_linked_hypothesis_chart as chart


class LinkedChartTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document, cls.datasets, cls.receipt = chart.load_evidence()
        cls.export = chart.project(cls.document, cls.datasets)

    def test_all_saved_endpoints_and_links_audited(self):
        self.assertEqual(612, self.receipt['after']['prices_verified'])
        self.assertEqual(63, self.receipt['after']['linked_rows'])
        self.assertEqual('PASS', chart.validate_export(self.export, self.document, self.datasets)['result'])

    def test_projection_retains_original_roles_prices_fields_and_parent_ids(self):
        for old, new in zip(self.document['after']['hypotheses'], self.export['hypotheses']):
            for key in ('hypothesis_id', 'requirement_id', 'parent_family_hypothesis_id', 'binding_id', 'candidate_id'):
                self.assertEqual(old[key], new[key])
            for a, b in zip(old['endpoints'], new['endpoints']):
                self.assertEqual(a, {k: v for k, v in b.items() if k != 'represented_price_text'})
                self.assertEqual(repr(a['price']), b['represented_price_text'])

    def test_parent_alternative_isolation_and_child_links(self):
        rows = self.export['hypotheses']
        ids = {h['hypothesis_id']: h for h in rows}
        requirements = {r['requirement_id']: r for r in self.export['requirements']}
        for child in (h for h in rows if h['path'] == 'child'):
            req = requirements[child['requirement_id']]
            self.assertEqual(req['parent_hypothesis_id'], child['parent_family_hypothesis_id'])
            self.assertIn(req['parent_hypothesis_id'], ids)
        self.assertEqual(27, sum(h['path'] == 'parent' for h in rows))
        self.assertEqual(63, sum(h['path'] == 'child' for h in rows))

    def test_equal_coordinates_keep_distinct_contexts(self):
        counts = Counter(tuple((e['timestamp_utc'], e['price']) for e in h['endpoints']) for h in self.export['hypotheses'])
        self.assertTrue(any(count > 1 for count in counts.values()))
        self.assertEqual(90, sum(counts.values()))

    def test_p004_rejection_is_not_rescued(self):
        rejected = [h for h in self.export['hypotheses'] if h['p004'] and h['p004']['fatal']]
        self.assertEqual(3, len(rejected))
        self.assertEqual(2, sum(h['p005']['status'] == 'SUFFICIENT_CONDITION_ESTABLISHED' for h in rejected))
        self.assertTrue(all(h['report_status'] == 'REJECTED_EXACT_HYPOTHESIS_P004' for h in rejected))

    def test_missing_children_are_not_fabricated(self):
        parents = [h for h in self.export['hypotheses'] if h['path'] == 'parent' and h['family'] == 'NORMAL_IMPULSE_PARTIAL']
        for parent in parents:
            self.assertFalse(any(h['parent_family_hypothesis_id'] == parent['hypothesis_id'] for h in self.export['hypotheses']))
        self.assertTrue(any(not any(h['requirement_id'] == r['requirement_id'] for h in self.export['hypotheses']) for r in self.export['requirements']))

    def test_stale_capture_and_exact_history_preserved(self):
        self.assertTrue(self.export['data']['capture_requested_at_utc'].startswith('2026-09-06'))
        for timeframe, prices in self.export['prices_close_usd'].items():
            self.assertEqual([[b.timestamp_utc.isoformat(), b.close] for b in self.datasets[timeframe].bars], prices)
        self.assertIn('Historical snapshot—not today', chart.render(self.export))

    def test_all_current_positions_unresolved_without_completion_claim(self):
        for h in self.export['hypotheses']:
            self.assertEqual('CURRENT_WAVE_POSITION_UNRESOLVED', h['reach']['status'])
            self.assertTrue(h['reach']['reasons'])
            self.assertEqual('NOT_ESTABLISHED_IN_SAVED_EVIDENCE', h['reach']['bound_developing_component'])
            self.assertFalse(h['authority']['completion'])

    def test_developing_geometry_is_not_active_wave(self):
        row = copy.deepcopy(self.document['after']['hypotheses'][0])
        row['endpoints'][-1]['pivot_state'] = 'DEVELOPING'
        value = chart.reach(row)
        self.assertEqual(1, value['developing_geometric_endpoints'])
        self.assertEqual('CURRENT_WAVE_POSITION_UNRESOLVED', value['status'])
        self.assertEqual('NOT_ESTABLISHED_IN_SAVED_EVIDENCE', value['bound_developing_component'])

    def test_search_exclusions_and_unvisited_not_methodology_rejection(self):
        totals = Counter()
        for scope in self.export['scopes']:
            totals.update(scope['dispositions'])
        self.assertEqual({'SELECTED': 18, 'UNVISITED_BUDGET': 116, 'SEARCH_DOMAIN_EXCLUDED': 98}, dict(totals))
        self.assertFalse(any(r['requirement_satisfied'] for r in self.export['requirements']))

    def test_missing_partial_coverage_retains_evidence_status(self):
        doc = copy.deepcopy(self.document)
        doc['after']['requirements'][0]['coverage'] = 'PARTIAL_WINDOW_COVERAGE'
        doc['after']['requirements'][1]['coverage'] = 'NO_FINER_OBSERVATION_COVERAGE'
        result = chart.project(doc, self.datasets)
        self.assertEqual('PARTIAL_WINDOW_COVERAGE', result['requirements'][0]['coverage'])
        self.assertEqual('NO_FINER_OBSERVATION_COVERAGE', result['requirements'][1]['coverage'])
        self.assertFalse(result['requirements'][0]['requirement_satisfied'])

    def test_changed_export_price_role_link_or_status_rejected(self):
        for field, value in [('price', 123), ('role', 'confirmed-wave'), ('timestamp_utc', '2026-01-01')]:
            changed = copy.deepcopy(self.export)
            changed['hypotheses'][0]['endpoints'][0][field] = value
            with self.assertRaises(ValueError): chart.validate_export(changed, self.document, self.datasets)
        for field in ('parent_family_hypothesis_id', 'report_status', 'snapshot_content_sha256'):
            changed = copy.deepcopy(self.export)
            changed['hypotheses'][-1][field] = 'foreign'
            with self.assertRaises(ValueError): chart.validate_export(changed, self.document, self.datasets)

    def test_html_embeds_exact_json_safely_and_deterministically(self):
        text = chart.render(self.export)
        payload = text.split('<script id="canonical" type="application/json">', 1)[1].split('</script>', 1)[0]
        self.assertEqual(self.export, json.loads(payload))
        self.assertEqual(text, chart.render(self.export))
        bad = copy.deepcopy(self.export); bad['test'] = '</script><script>alert(1)</script>'
        self.assertNotIn(bad['test'], chart.render(bad))
        self.assertIn("connect-src 'none'", text)
        self.assertNotIn('<script src=', text)
        self.assertIn('دليل الاستخدام', text)

    def test_manifests_fail_closed(self):
        with self.assertRaises(ValueError):
            chart.verify_manifest(chart.INPUTS / 'input_manifest.json', '0' * 64, chart.INPUTS, 'files')

    def test_inventory_and_no_rendering_authority(self):
        self.assertEqual({'methodology': 11, 'structural_producers': 7, 'family_producers': 0, 'family_issuances': 0}, self.export['inventories'])
        for row in self.export['hypotheses']:
            self.assertFalse(any(row['authority'].values()))


if __name__ == '__main__':
    unittest.main()
