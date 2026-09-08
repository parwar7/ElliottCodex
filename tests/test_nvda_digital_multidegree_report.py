"""Frozen local evidence only. Export validation does not restore runtime authority."""
import copy
import unittest
import support
import nvda_digital_multidegree as run
import nvda_digital_multidegree_report as report


class DigitalReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshots,_=run.tv.load_inputs()
        cls.doc=run.read(run.PACK/'resolution_expanded/hierarchy.json')
        cls.raw=run.read(run.PREVIOUS/'indicators_1D_verified.json')
        cls.summary=run.read(run.PREVIOUS/'indicator_summary.json')

    def changed(self):return copy.deepcopy(self.doc)

    def test_all_exported_endpoints_and_links_match_saved_inputs(self):
        self.assertIs(report.canonical(self.doc,self.snapshots),self.doc)
        self.assertEqual(len(report.wave_table(self.doc)),150)

    def test_foreign_snapshot_rejected(self):
        d=self.changed();d['nodes'][0]['start']['source_hash']='foreign'
        with self.assertRaises((ValueError,KeyError)):report.canonical(d,self.snapshots)

    def test_table_price_substitution_rejected(self):
        d=self.changed();d['hypotheses'][0]['endpoints'][0]['price']+=1
        with self.assertRaises(ValueError):report.canonical(d,self.snapshots)

    def test_parent_link_substitution_rejected(self):
        d=self.changed();d['hypotheses'][0]['parent_node_id']='M1.1'
        with self.assertRaises(ValueError):report.canonical(d,self.snapshots)

    def test_result_relabeling_rejected(self):
        d=self.changed();d['hypotheses'][0]['p004']['fatal']=False
        with self.assertRaises(ValueError):report.canonical(d,self.snapshots)

    def test_no_p005_rescue(self):
        both=[h for h in self.doc['hypotheses'] if h['p004']['fatal'] and h['p005']['status']=='SUFFICIENT_CONDITION_ESTABLISHED']
        self.assertEqual(len(both),7)
        for h in both:self.assertEqual(h['report_status'],'REJECTED_EXACT_HYPOTHESIS_P004')

    def test_forming_metadata_cannot_be_hidden(self):
        d=self.changed();h=next(h for h in d['hypotheses'] if h['display_id']=='M2')
        self.assertTrue(h['current_position']['developing_endpoint'])
        self.assertEqual(h['p005']['status'],'UNRESOLVED')
        h['current_position']['developing_endpoint']=False
        with self.assertRaises(ValueError):report.canonical(d,self.snapshots)

    def test_no_active_wave_or_completion_export(self):
        d=self.changed();d['hypotheses'][0]['current_position']['completion_authority']=True
        with self.assertRaises(ValueError):report.canonical(d,self.snapshots)

    def test_duplicate_context_links_retained(self):
        m1=[h for h in self.doc['hypotheses'] if h['parent_node_id']=='M1.5']
        m2=[h for h in self.doc['hypotheses'] if h['parent_node_id']=='M2.5']
        self.assertEqual(len(m1),2);self.assertEqual(len(m2),2)
        self.assertNotEqual(m1[0]['hypothesis_id'],m2[0]['hypothesis_id'])
        self.assertEqual(m1[0]['endpoints'][0]['price'],m2[0]['endpoints'][0]['price'])

    def test_indicator_values_verified_not_recomputed(self):
        rows=report.indicator_rows(self.raw,self.summary)
        self.assertEqual(len(rows),10)
        self.assertTrue(all(not r['price_snapshot_comparable'] for r in rows))

    def test_indicator_snapshot_or_value_leakage_rejected(self):
        for key,value in [('capture','2026-09-08T13:49:15.086Z'),('value',0)]:
            s=copy.deepcopy(self.summary);s['rows'][0][key]=value
            with self.assertRaises(ValueError):report.indicator_rows(self.raw,s)

    def test_chart_labels_and_prices_match_exact_roles(self):
        h=next(h for h in self.doc['hypotheses'] if h['display_id']=='M1')
        rows,sql=report.chart_data(self.snapshots['1M'],h)
        selected=sorted([r for r in rows if r['label']],key=lambda r:int(r['label']))
        endpoints=[h['endpoints'][0]]+h['endpoints'][1::2]
        self.assertEqual(len(selected),6);self.assertIn('SELECT',sql)
        for row,e in zip(selected,endpoints):
            self.assertEqual((row['time'],row['price'],row['field']),(e['timestamp_utc'],e['price'],e['price_field']))
            self.assertEqual(row['source_hash'],e['source_hash'])

    def test_no_family_authority_and_actual_depth(self):
        self.assertTrue(all(not n['family_validity'] for n in self.doc['nodes']))
        self.assertEqual(max(h['level'] for h in self.doc['hypotheses']),2)
        self.assertEqual(self.doc['inventories'],[11,7,0,0])


if __name__=='__main__':unittest.main()
