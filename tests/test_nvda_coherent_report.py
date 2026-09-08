"""Report-only regressions; saved observations, no live retrieval/evaluation."""
import ast
import copy
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
import unittest
from unittest.mock import patch

import nvda_coherent_report as report


class CoherentReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshots, cls.raw = report.old.tv.load_inputs()
        cls.doc = report.old.read(report.previous.PACK/'canonical_hierarchy.json')

    def test_bands_cover_every_month_once(self):
        s = self.snapshots['1M']
        selected = [[b.timestamp_utc for b in s.observations.bars
                     if a <= b.timestamp_utc.isoformat() < z] for a, z in report.BANDS]
        flat = [x for row in selected for x in row]
        self.assertEqual(flat, [b.timestamp_utc for b in s.observations.bars])
        self.assertEqual(len(flat), 333)

    def test_window_empty_remains_empty(self):
        r = report.inspect_window(self.snapshots['1M'], '1900', '1901')
        self.assertEqual(r['status'], 'NO_OBSERVATIONS')
        self.assertEqual(r['low_occurrences'], [])

    def test_reversed_window_rejected(self):
        with self.assertRaises(ValueError):
            report.inspect_window(self.snapshots['1M'], '2026', '2025')

    def test_interval_boundary_is_explicit(self):
        s = self.snapshots['1M']
        a = s.observations.bars[0].timestamp_utc.isoformat()
        b = s.observations.bars[1].timestamp_utc.isoformat()
        self.assertEqual(report.inspect_window(s, a, b)['bars'], 1)
        self.assertEqual(report.inspect_window(s, a, b, inclusive_end=True)['bars'], 2)

    def test_path_findings_are_exact_raw_observations_not_rules(self):
        roots = report.inspect_roots(self.doc, self.snapshots['1M'])
        raw = {datetime.fromtimestamp(x['value'][0], timezone.utc).isoformat(): x['value']
               for x in self.raw['1M']['rows']}
        self.assertEqual(len(roots), 10)
        for r in roots:
            w = r['observed_window']
            self.assertFalse(w['endpoint_authority'])
            self.assertIsNone(w['methodology_evaluation'])
            for key, index in (('low_occurrences', 3), ('high_occurrences', 2)):
                for e in w[key]:
                    value = raw[e['bar_label_utc']][index]
                    self.assertEqual(Fraction(e['value']), Fraction(value))
                    self.assertEqual(e['represented_ratio'], report.old.p.plain(Fraction(value)))
        role2 = next(x for x in roots if x['hypothesis'] == 'M1' and x['role'] == 2)
        self.assertEqual(role2['original_end']['price'], 0.289)
        self.assertEqual(role2['observed_window']['low_occurrences'][0]['value'], 0.14375)
        role3 = next(x for x in roots if x['hypothesis'] == 'M1' and x['role'] == 3)
        self.assertEqual(role3['observed_window']['low_occurrences'][0]['value'], 0.21625)

    def test_foreign_root_hash_rejected(self):
        d = copy.deepcopy(self.doc)
        d['hypotheses'][0]['source_response_sha256'] = 'foreign'
        with self.assertRaises(ValueError):
            report.inspect_roots(d, self.snapshots['1M'])

    def test_rejected_root_cannot_support_synthesis(self):
        d = copy.deepcopy(self.doc)
        d['hypotheses'][0]['p004']['fatal'] = True
        self.assertEqual(d['hypotheses'][0]['p005']['status'], 'SUFFICIENT_CONDITION_ESTABLISHED')
        with self.assertRaises(ValueError):
            report.select_cases(d)
        with self.assertRaises(ValueError):
            report.inspect_roots(d, self.snapshots['1M'])

    def test_display_copies_do_not_mutate_canonical_roles(self):
        cases = report.select_cases(self.doc)
        original = self.doc['hypotheses'][0]['endpoints'][0]['price']
        cases[0]['endpoints'][0]['price'] = -1
        self.assertEqual(self.doc['hypotheses'][0]['endpoints'][0]['price'], original)

    def test_m1_m2_endpoints_and_developing_state_not_merged(self):
        cases = report.select_cases(self.doc)
        a, b = cases[:2]
        self.assertEqual(a['endpoints'][-1]['price'], 236.54)
        self.assertEqual(b['endpoints'][-1]['price'], 234.76)
        self.assertEqual(b['endpoints'][-1]['pivot_state'], 'DEVELOPING')
        self.assertEqual(b['p005']['reason'], 'DEVELOPING_REQUIRED_ENDPOINT')
        self.assertNotEqual(a['hypothesis_id'], b['hypothesis_id'])

    def test_corrective_alternatives_have_no_family_authority(self):
        a, b = report.select_cases(self.doc)[-2:]
        self.assertEqual(a['endpoints'], b['endpoints'])
        self.assertNotEqual(a['display_id'], b['display_id'])
        self.assertFalse(a['family_validity'])
        self.assertFalse(b['family_validity'])
        self.assertIsNone(a['parent_node_id'])
        self.assertIsNone(b['parent_node_id'])

    def test_monthly_chart_preserves_unlabelled_capture_tail(self):
        s = self.snapshots['1M']
        h = report.select_cases(self.doc)[0]
        rows = report.display.chart_rows(s, h, start='1999')
        closes = [r for r in rows if r['kind'] == 'captured close']
        labels = [r for r in rows if r['label']]
        self.assertEqual(len(closes), 333)
        self.assertEqual(closes[-1]['time'], s.observations.bars[-1].timestamp_utc.isoformat())
        self.assertLess(max(r['time'] for r in labels), closes[-1]['time'])

    def test_output_outside_runtime_rejected_before_writes(self):
        with patch.object(report, 'integrity', side_effect=AssertionError('must not reach integrity')):
            with self.assertRaises(ValueError):
                report.build(Path('C:/outside-runtime-report'))

    def test_changed_baseline_stops_before_protected_checks(self):
        with patch.object(report.old, 'hash_file', return_value='mismatch'):
            with self.assertRaises(ValueError):
                report.integrity()

    def test_no_new_evaluator_or_network_call(self):
        tree = ast.parse(Path(report.__file__).read_text(encoding='utf-8'))
        calls = [ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)]
        for name in calls:
            self.assertFalse(any(x in name for x in ('evaluate_scope', 'evaluate_independent', 'certify_', 'fetch', 'link_observations')))


if __name__ == '__main__':
    unittest.main()
