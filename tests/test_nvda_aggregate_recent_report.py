"""Frozen report reconciliations, independent raw prices, no live retrieval."""
import copy
from datetime import datetime
import unittest
import support
import nvda_aggregate_recent_report as report


class AggregateRecentReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshots,cls.raw=report.old.tv.load_inputs()
        cls.doc=report.old.read(report.task.PACK/'canonical_analysis.json')

    def test_all_raw_evidence_reconciles(self):
        result=report.reconcile(self.doc,self.snapshots,self.raw)
        self.assertEqual(result['raw_fields_reconciled'],286)
        self.assertEqual(result['hypotheses'],25)

    def test_no_match_does_not_choose_nearest_july_price(self):
        rows=[e for e in self.doc['occurrence_evidence'] if e['evidence_id'].startswith('JULY')]
        for e in rows:
            self.assertEqual(e['original_price'],190.01)
            if e['finer_resolution']!='1D':
                self.assertEqual(e['occurrences'],[])
                self.assertEqual(e['status'],'NO_OBSERVED_MATCH_IN_AVAILABLE_ROWS')
                self.assertIn('COMPLETE_TRADING_COVERAGE_UNVERIFIED',e['limitations'])

    def test_raw_census_rejects_omitted_occurrence(self):
        d=copy.deepcopy(self.doc);d['occurrence_evidence'][0]['occurrences']=[]
        d['occurrence_evidence'][0]['status']='NO_OBSERVED_MATCH_IN_AVAILABLE_ROWS'
        with self.assertRaises(ValueError):report.reconcile(d,self.snapshots,self.raw)

    def test_foreign_context_and_old_parent_attachment_rejected(self):
        for field,value in [('context_evidence_ids',['M1:1D']),('old_parent_id','M1')]:
            d=copy.deepcopy(self.doc);h=next(h for h in d['hypotheses'] if h['display_id']=='RECENT:15:S186');h[field]=value
            with self.assertRaises(ValueError):report.reconcile(d,self.snapshots,self.raw)

    def test_no_exact_instant_or_completion_promoted(self):
        for field,value in [('exact_extremum_instant','2026-05-14T19:00:00+00:00'),('orthodox_endpoint',True)]:
            d=copy.deepcopy(self.doc);d['occurrence_evidence'][0]['occurrences'][0][field]=value
            with self.assertRaises(ValueError):report.reconcile(d,self.snapshots,self.raw)

    def test_false_result_precedence_and_forming_export_rejected(self):
        for case in ('fatal','forming'):
            d=copy.deepcopy(self.doc)
            if case=='fatal':next(h for h in d['hypotheses'] if h['p004']['fatal'])['p004']['fatal']=False
            else:d['hypotheses'][0]['current_position']['developing_endpoint']=not d['hypotheses'][0]['current_position']['developing_endpoint']
            with self.assertRaises(ValueError):report.reconcile(d,self.snapshots,self.raw)

    def test_chart_labels_fields_and_prices_reconcile(self):
        h=next(h for h in self.doc['hypotheses'] if h['display_id']=='RECENT:15:S186')
        rows,_=report.display.chart_data(self.snapshots['15'],h)
        labelled={r['label']:r for r in rows if r['label']}
        self.assertEqual(set(labelled),set('012345'))
        for i,e in enumerate([h['endpoints'][0]]+h['endpoints'][1::2]):
            self.assertEqual((labelled[str(i)]['time'],labelled[str(i)]['price'],labelled[str(i)]['field']),(e['timestamp_utc'],e['price'],e['price_field']))
        lookup={r['value'][0]:r['value'] for r in self.raw['15']['rows']}
        for r in rows:
            self.assertEqual(r['price'],lookup[datetime.fromisoformat(r['time']).timestamp()][{'high':2,'low':3,'close':4}[r['field']]])

    def test_alternative_rejection_does_not_remove_siblings(self):
        self.assertEqual(len(self.doc['hypotheses']),25)
        fatal=[h for h in self.doc['hypotheses'] if h['p004']['fatal']]
        self.assertEqual(len(fatal),14)
        self.assertEqual(sum(h['p005']['status']=='SUFFICIENT_CONDITION_ESTABLISHED' for h in fatal),11)
        self.assertEqual(len([h for h in self.doc['hypotheses'] if not h['p004']['fatal']]),11)
        self.assertTrue(all(h['old_parent_id'] is None for h in self.doc['hypotheses']))

    def test_search_dispositions_are_explicit_and_predeclared(self):
        before=report.old.read(report.task.PACK/'selection_before_evaluation.json')
        self.assertEqual(before['planned_hypotheses'],25)
        counts=report.Counter(w['disposition'] for s in self.doc['searches'] for w in s['windows'])
        self.assertEqual(dict(counts),{'SELECTED':25,'DOMAIN_EXCLUDED':575,'UNVISITED_BUDGET':438})
        self.assertTrue(all(not s['results'] for s in before['searches']))

    def test_indicator_values_stay_in_own_capture(self):
        r=report.display.indicator_rows(report.old.read(report.old.PREVIOUS/'indicators_1D_verified.json'),report.old.read(report.old.PREVIOUS/'indicator_summary.json'))
        self.assertEqual(len(r),10)
        self.assertTrue(all(not x['price_snapshot_comparable'] and x['interpretation']=='OBSERVATION_ONLY' for x in r))


if __name__=='__main__':unittest.main()
