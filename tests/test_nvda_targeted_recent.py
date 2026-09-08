"""New orchestration risks using genuine public-factory synthetic evidence."""
import copy
from dataclasses import replace
import unittest

import nvda_targeted_recent as task
import test_observational_hierarchy as fixtures
import nvda_targeted_recent_report as report


class TargetedSelectionTests(unittest.TestCase):
    def test_spread_visits_interior_not_only_edges(self):
        self.assertEqual(task.spread(tuple(range(20)),4),(2,7,12,17))

    def test_under_budget_retains_all_siblings(self):
        self.assertEqual(task.spread((1,3,6),8),(1,3,6))

    def test_explicit_empty_has_no_fallback(self):
        self.assertEqual(task.spread((),4),())

    def test_invalid_budgets_fail(self):
        for cap in (True,0,-1,1.5):
            with self.subTest(cap=cap),self.assertRaises(ValueError):task.spread((1,2),cap)

    def test_duplicate_and_reordered_indices_fail(self):
        for values in ((1,1),(2,1),(True,2),[1,2]):
            with self.subTest(values=values),self.assertRaises(ValueError):task.spread(values,1)

    def test_deterministic_cap_for_many_lengths(self):
        for size in range(1,100):
            selected=task.spread(tuple(range(size)),7)
            self.assertEqual(len(selected),min(size,7))
            self.assertEqual(tuple(sorted(set(selected))),selected)
            self.assertEqual(selected,task.spread(tuple(range(size)),7))

    def test_aggregate_preflight_counts_family_fanout(self):
        p={'windows':[1,2],'max_search_windows':2,'max_geometric_sequences_examined':5,
           'max_new_scopes':3,'max_normal_results':1,'max_corrective_hypotheses':4}
        task.check_demand([{'rows':[1,2,3]}],[(6,),(4,),(4,)],p)
        for key,value in (('max_search_windows',1),('max_geometric_sequences_examined',2),
                          ('max_new_scopes',2),('max_normal_results',0),('max_corrective_hypotheses',3)):
            with self.subTest(key=key),self.assertRaises(ValueError):
                task.check_demand([{'rows':[1,2,3]}],[(6,),(4,),(4,)],dict(p,**{key:value}))


class TargetedFactoryTests(unittest.TestCase):
    def setUp(self):
        self.values=fixtures.fixture()
        self.s=self.values[1];self.c=self.values[3]
        self.h=self.c.evaluations[0].hypothesis
        self.d=self.h.generated_candidate.source_geometric_pivots
        self.points=self.h.generated_candidate.ordered_selected_pivots
        self.kernel=task.old.p.MethodologyKernel(fixtures.support.PROTECTED_ROOT)

    def test_new_context_does_not_reuse_subject_binding(self):
        other=task.prior.evaluate_independent('fresh-test',self.s,self.d,self.points,(),self.kernel)
        oh=other.evaluations[0].hypothesis
        self.assertIsNot(oh.generated_candidate.subject,self.h.generated_candidate.subject)
        self.assertIsNot(oh.five_slot_view.binding,self.h.five_slot_view.binding)
        self.assertIs(oh.generated_candidate.source_observations,self.s.observations)
        self.assertIs(other.evaluations[0].bounded_request.child_binding,oh.five_slot_view.binding)

    def test_foreign_snapshot_rejected(self):
        foreign=replace(self.s,observations=replace(self.s.observations))
        with self.assertRaises(ValueError):task.prior.evaluate_independent('foreign',foreign,self.d,self.points,(),self.kernel)

    def test_nested_binding_mutation_repeatedly_rejected(self):
        object.__setattr__(self.h.five_slot_view.binding,'parent_subject',task.old.p.AnalyzedWaveSubject('foreign','f'*64))
        for _ in range(2):
            with self.assertRaises(ValueError):task.bounded.normal_rows(self.c,'independent','test')

    def test_old_sequence_excluded_by_coordinates_not_alias(self):
        key=task.sequence_key('1D',self.s.observations.provenance.source_sha256,self.points)
        rows,selected=task.select_sequences(self.points,6,4,{key},'1D',key[1])
        self.assertEqual(selected,())
        self.assertEqual(rows[0]['disposition'],'PREVIOUSLY_EVALUATED_COORDINATES')

    def test_selection_preserves_dispositions(self):
        rows,selected=task.select_sequences(self.d.pivots,4,1,set(),'1D','test')
        self.assertLessEqual(len(selected),1)
        self.assertEqual(len(rows),max(0,len(self.d.pivots)-3))
        self.assertEqual(sum(r['disposition']=='SELECTED' for r in rows),len(selected))

    def test_unsupported_shape_rejected(self):
        with self.assertRaises(ValueError):task.select_sequences(self.points,5,1,set(),'1D','test')
        with self.assertRaises(ValueError):task.corrective('bad',self.s,self.d,self.points,self.kernel)

    def test_corrective_alternatives_remain_unresolved(self):
        bridge=task.corrective('corrective',self.s,self.d,self.points[:4],self.kernel)
        rows=task.bounded.family_rows(bridge,'independent','test')
        self.assertEqual({r['family'] for r in rows},{'SINGLE_ZIGZAG','FLAT'})
        self.assertTrue(all(r['p004'] is None and r['p005'] is None for r in rows))
        self.assertTrue(all('VALID'!=r['state'] for r in rows))
        self.assertEqual([len(r['endpoints']) for r in rows],[6,6])
        self.assertTrue(all(r['state']=='CURRENT_SUPPLIED_SCOPE_REVIEWED' for r in rows))
        self.assertTrue(all(r['authority']['family_validity'] is False for r in rows))
        for row in rows:
            executed=[r for r in row['coverage'] if r['state']=='SUPPLIED_AND_EXECUTED']
            self.assertEqual(len(executed),1)
            self.assertIn('CARDINALITY',executed[0]['behavior_id'])

    def test_opentail_not_inferred_from_last_label(self):
        row,_=task.old.export_hypothesis(self.c,'test',self.s.observations)
        tail=task.tail(row,self.s)
        self.assertGreater(tail['trailing_bars'],0)
        self.assertEqual(tail['state'],'CURRENT_WAVE_POSITION_UNRESOLVED')
        self.assertFalse(tail['completion_authority'])

    def test_p004_failure_retained_even_with_p005(self):
        _,s,_,c,*_=fixtures.fixture(reject=True)
        row,_=task.old.export_hypothesis(c,'rejected',s.observations)
        self.assertTrue(row['p004']['fatal'])
        self.assertEqual(row['report_status'],'REJECTED_EXACT_HYPOTHESIS_P004')
        self.assertEqual(task.tail(row,s)['state'],'CURRENT_WAVE_POSITION_UNRESOLVED')

    def test_chart_includes_tail_and_only_original_prices(self):
        row,_=task.old.export_hypothesis(self.c,'test',self.s.observations)
        rows=report.chart_rows(self.s,row)
        closes=[r for r in rows if r['kind']=='captured close']
        self.assertEqual(closes[-1]['time'],self.s.observations.bars[-1].timestamp_utc.isoformat())
        self.assertGreater(closes[-1]['time'],row['endpoints'][-1]['timestamp_utc'])
        self.assertEqual(len([r for r in rows if r['label']]),6)
        self.assertTrue(all(not r['label'] for r in closes))

    def test_chart_rejects_fabricated_endpoint_price(self):
        row,_=task.old.export_hypothesis(self.c,'test',self.s.observations)
        row['endpoints'][-1]['price']+=1
        with self.assertRaises(ValueError):report.chart_rows(self.s,row)

    def test_chart_rejects_equal_price_foreign_source(self):
        row,_=task.old.export_hypothesis(self.c,'test',self.s.observations)
        row['endpoints'][-1]['source_hash']='f'*64
        with self.assertRaises(ValueError):report.chart_rows(self.s,row)

    def test_forming_tail_has_no_active_wave_authority(self):
        _,s,_,c,*_=fixtures.fixture(forming=True)
        row,_=task.old.export_hypothesis(c,'forming',s.observations)
        t=task.tail(row,s)
        self.assertTrue(t['last_bar_forming'])
        self.assertFalse(t['completion_authority'])
        self.assertEqual(t['state'],'CURRENT_WAVE_POSITION_UNRESOLVED')

    def test_rejection_does_not_remove_sibling(self):
        good,_=task.old.export_hypothesis(self.c,'good',self.s.observations)
        bad=copy.deepcopy(good);bad['display_id']='bad';bad['p004']['fatal']=True
        for h in (good,bad):h.update(evaluation_origin='NEW',resolution='1D')
        rows=report.summaries({'hypotheses':[bad,good],'links':[]})
        self.assertEqual([r['alias'] for r in rows],['good'])
        self.assertEqual(rows[0]['classification'],'INDEPENDENT_LOCAL_HYPOTHESIS')

    def test_no_temporal_proximity_link_in_synthesis(self):
        row,_=task.old.export_hypothesis(self.c,'test',self.s.observations)
        row.update(evaluation_origin='NEW',resolution='1D')
        doc={'hypotheses':[row],'links':[{'child_alias':'test','link_id':'missing','surviving_observational_link':False}]}
        self.assertEqual(report.summaries(doc)[0]['incoming_links'],[])


class SavedTargetedExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=task.old.read(task.PACK/'canonical_hierarchy.json')
        cls.snapshots,cls.raw=task.old.tv.load_inputs()

    def test_complete_saved_reconciliation(self):
        result=report.reconcile(self.doc,self.snapshots,self.raw)
        self.assertEqual(result['result'],'PASS')
        self.assertEqual(result['old_coordinate_sequences_mislabelled_new'],[])

    def test_new_totals_tamper_rejected(self):
        d=copy.deepcopy(self.doc);d['totals']['new_normal_hypotheses']+=1
        with self.assertRaises(ValueError):report.reconcile(d,self.snapshots,self.raw)

    def test_corrective_endpoint_tamper_rejected(self):
        d=copy.deepcopy(self.doc);d['corrective_hypotheses'][0]['endpoints'][0]['price']+=1
        with self.assertRaises(ValueError):report.reconcile(d,self.snapshots,self.raw)

    def test_foreign_link_binding_rejected(self):
        d=copy.deepcopy(self.doc);d['links'][0]['parent_binding_id']='foreign'
        with self.assertRaises(ValueError):report.reconcile(d,self.snapshots,self.raw)

    def test_open_tail_cannot_be_hidden(self):
        d=copy.deepcopy(self.doc);d['open_tails'][0]['trailing_bars']+=1
        with self.assertRaises(ValueError):report.reconcile(d,self.snapshots,self.raw)

    def test_p004_rejected_hypothesis_not_in_survivors(self):
        candidates=report.summaries(self.doc)
        rejected={h['display_id'] for h in self.doc['hypotheses'] if h['p004']['fatal']}
        self.assertFalse(rejected & {r['alias'] for r in candidates})

    def test_boundary_diagnostic_values_match_raw_rows(self):
        from datetime import datetime,timezone
        diagnostics=report.boundary_diagnostics(self.snapshots)
        self.assertEqual(len(diagnostics),12)
        for d in diagnostics:
            values=[r['value'][3] for r in self.raw[d['resolution']]['rows']
                    if datetime.fromtimestamp(r['value'][0],timezone.utc).date().isoformat()==d['date']]
            self.assertEqual(d['minimum_observed_low'],min(values))
            self.assertIn('NOT_REPLACEMENT',d['usage'])

    def test_genuine_developing_tail_is_not_denied_or_promoted(self):
        tails=[t for t in self.doc['open_tails'] if t['endpoint_developing'] and t['last_endpoint']==t['last_observation']]
        self.assertTrue(tails)
        for t in tails:
            self.assertNotIn('No exact supported developing component',t['reason'])
            self.assertFalse(t['completion_authority'])
            self.assertEqual(t['state'],'CURRENT_WAVE_POSITION_UNRESOLVED')


if __name__=='__main__':unittest.main()
