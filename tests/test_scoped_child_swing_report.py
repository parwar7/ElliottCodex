"""Read-only audit of the preserved experiment; no live market retrieval."""
import copy
import sys
import unittest
import support

sys.path.insert(0, str(support.RUNTIME_ROOT / 'tools'))
import nvda_scoped_child_swing_search as report


class ScopedChildReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = support.RUNTIME_ROOT / 'kernel_reviews' / report.STAGE / 'report'
        cls.document = report.p.json.loads((cls.folder / 'results.json').read_bytes())
        _, cls.data = report.p.load_inputs(report.h.INPUTS)

    def test_saved_observations_links_and_scope_audit(self):
        result = report.audit(self.document, self.data)
        self.assertEqual(84, result['search_scopes_verified'])

    def test_export_reconciliation(self):
        for mode in ('before', 'after'):
            for name, text in report.r.evidence_exports(self.document[mode]).items():
                self.assertEqual(text.encode(), (self.folder / mode / name).read_bytes())

    def test_render_roundtrip_and_caveats(self):
        text = report.render(self.document)
        self.assertEqual(text, report.render(report.p.json.loads(report.p.encoded(self.document))))
        self.assertIn('not 58 unique invalid waves', text)
        self.assertIn('SOURCE_DERIVED_BASE_CASE_NOT_FOUND', text)
        self.assertIn('unvisited', text)

    def test_changed_selected_pivot_or_omission_rejected(self):
        for field in ('selected_pivot_ids', 'omitted_pivot_ids'):
            doc = copy.deepcopy(self.document)
            record = next(x for x in doc['scopes'] if x['diagnostics'][field])
            record['diagnostics'][field].pop()
            with self.assertRaises(ValueError):
                report.audit(doc, self.data)

    def test_changed_snapshot_or_price_rejected(self):
        for field in ('snapshot_content_sha256', 'price'):
            doc = copy.deepcopy(self.document)
            if field == 'price':
                doc['after']['hypotheses'][0]['endpoints'][0]['price'] += 1
            else:
                doc['after']['hypotheses'][0][field] = 'foreign'
            with self.assertRaises(ValueError):
                report.audit(doc, self.data)

    def test_cross_requirement_child_link_rejected(self):
        doc = copy.deepcopy(self.document)
        row = next(x for x in doc['after']['hypotheses'] if x['path'] == 'child')
        row['parent_family_hypothesis_id'] = 'foreign'
        with self.assertRaises(ValueError):
            report.audit(doc, self.data)

    def test_no_silent_outcome_promotion(self):
        doc = copy.deepcopy(self.document)
        row = next(x for x in doc['after']['hypotheses'] if x['p005'])
        row['p005']['reason'] = 'fabricated'
        doc['after']['totals'] = report.previous.totals(doc['after']['hypotheses'])
        with self.assertRaises(ValueError):
            report.audit(doc, self.data)

    def test_no_silent_budget_truncation(self):
        doc = copy.deepcopy(self.document)
        window = next(w for s in doc['scopes'] for w in s['diagnostics'].get('windows', [])
                      if w['disposition'] == 'UNVISITED_BUDGET')
        window['disposition'] = 'SEARCH_DOMAIN_EXCLUDED'
        with self.assertRaises(ValueError):
            report.audit(doc, self.data)


if __name__ == '__main__':
    unittest.main()
