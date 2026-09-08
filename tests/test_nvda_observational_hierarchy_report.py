"""Reconcile exported links and visuals with the approved real saved snapshots."""
import copy
from datetime import datetime
from fractions import Fraction
import unittest

import nvda_observational_hierarchy as task
import nvda_observational_hierarchy_report as report


class ObservationalReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=task.old.read(task.PACK/'canonical_hierarchy.json')
        cls.snapshots,cls.raw=task.old.tv.load_inputs()

    def test_all_saved_observations_reconcile(self):
        result=report.reconcile(self.doc,self.snapshots,self.raw)
        self.assertEqual(result['result'],'PASS');self.assertEqual(result['links_checked'],150)

    def test_july_mismatch_never_substituted(self):
        ev=[e for e in self.doc['occurrence_evidence'] if e['original_bar_timestamp'].startswith('2026-07-29') and e['price_field']=='low']
        self.assertTrue(ev)
        for e in ev:
            self.assertEqual(e['original_price'],190.01);self.assertFalse(e['occurrences'])
            res=e['finer_resolution']
            prices=[b.low for b in self.snapshots[res].observations.bars if b.timestamp_utc.date().isoformat()=='2026-07-29']
            self.assertEqual(min(prices),190.02)
            self.assertEqual(e['status'],'NO_OBSERVED_MATCH_IN_AVAILABLE_ROWS')

    def test_missing_2022_finer_history_remains_missing(self):
        ev=[e for e in self.doc['occurrence_evidence'] if e['original_bar_timestamp'].startswith('2022-10') and e['finer_resolution'] in ('60','15')]
        self.assertTrue(ev)
        self.assertTrue(all(e['status']=='NO_FINER_COVERAGE' for e in ev))

    def test_own_p004_rejections_excluded_despite_sufficiency(self):
        h={h['display_id']:h for h in self.doc['hypotheses']}
        witnesses=[l for l in self.doc['links'] if h[l['child_alias']]['p004']['fatal'] and h[l['child_alias']]['p005']['status']=='SUFFICIENT_CONDITION_ESTABLISHED']
        self.assertTrue(witnesses)
        for l in witnesses:
            self.assertFalse(l['surviving_observational_link']);self.assertEqual(l['style'],'REJECTED')
        self.assertFalse(h['M2']['p004']['fatal'])

    def test_coincident_contexts_retained_not_confirmation_count(self):
        aliases={l['child_alias'] for l in self.doc['links']}
        self.assertIn('MAY_JULY:60:S75',aliases);self.assertIn('JULY:60:S23',aliases)
        h={h['display_id']:h for h in self.doc['hypotheses']}
        self.assertEqual([(e['timestamp_utc'],e['price']) for e in h['MAY_JULY:60:S75']['endpoints']],[(e['timestamp_utc'],e['price']) for e in h['JULY:60:S23']['endpoints']])
        self.assertNotEqual(h['MAY_JULY:60:S75']['binding_id'],h['JULY:60:S23']['binding_id'])

    def test_supported_path_does_not_reach_latest_bar(self):
        paths=report.paths(self.doc);self.assertTrue(paths)
        self.assertTrue(all(not p['reaches_latest_captured_bar'] and not p['active_wave_authority'] for p in paths))
        self.assertEqual(task.old.read(task.PACK/'proposed_paths.json'),paths)

    def test_uncovered_intervals_are_exact_and_not_subdivisions(self):
        rows=report.coverage_rows(self.doc,self.snapshots)
        self.assertEqual(rows,task.old.read(task.PACK/'link_coverage.json'))
        row=next(r for r in rows if r['link_id']=='M2:role5=>JULY:1D:S0')
        pair=row['pair_coverage'][0]
        self.assertEqual(pair['uncovered_before_child'],['2022-10-13T20:00:00+00:00','2026-07-07T13:30:00+00:00'])
        self.assertEqual(pair['uncovered_after_child'],['2026-07-31T20:00:00+00:00','2026-09-04T13:30:00+00:00'])
        self.assertTrue(pair['unexamined_internal_structure']);self.assertFalse(pair['intrabar_order_claim'])

    def test_foreign_binding_export_rejected(self):
        doc=copy.deepcopy(self.doc);doc['links'][0]['child_binding_id']='foreign'
        with self.assertRaises(ValueError):report.reconcile(doc,self.snapshots,self.raw)

    def test_pairing_census_cannot_drop_occurrence(self):
        doc=copy.deepcopy(self.doc);l=next(l for l in doc['links'] if l['pairings']);l['pairings']=[]
        with self.assertRaises(ValueError):report.reconcile(doc,self.snapshots,self.raw)

    def test_pairing_state_cannot_promote_coverage(self):
        doc=copy.deepcopy(self.doc);l=next(l for l in doc['links'] if l['pairings']);l['pairings'][0]['state']='BOUNDARY_SUPPORTED_PROPOSED_REFINEMENT'
        with self.assertRaises(ValueError):report.reconcile(doc,self.snapshots,self.raw)

    def test_rejection_cannot_be_hidden(self):
        doc=copy.deepcopy(self.doc);l=next(l for l in doc['links'] if l['p004_rejected']);l['surviving_observational_link']=True
        with self.assertRaises(ValueError):report.reconcile(doc,self.snapshots,self.raw)

    def test_exact_occurrence_interval_cannot_be_changed(self):
        doc=copy.deepcopy(self.doc);e=next(e for e in doc['occurrence_evidence'] if e['occurrences'])
        e['occurrences'][0]['occurrence_envelope'][1]=e['occurrences'][0]['occurrence_envelope'][0]
        with self.assertRaises(ValueError):report.reconcile(doc,self.snapshots,self.raw)

    def test_stale_capture_and_forming_state_cannot_be_hidden(self):
        doc=copy.deepcopy(self.doc);doc['input_coverage']['15']['last_bar_forming']=False
        with self.assertRaises(ValueError):report.reconcile(doc,self.snapshots,self.raw)

    def test_chart_table_json_labels_exact_and_separate_snapshots(self):
        data=task.old.read(task.PACK/'chart_rows.json');h={h['display_id']:h for h in self.doc['hypotheses']}
        src={s.observations.provenance.source_sha256:{b.timestamp_utc.isoformat():b for b in s.observations.bars} for s in self.snapshots.values()}
        for key,rows in data.items():
            alias=key[len('chart-'):].replace('-',':')
            labels=[r for r in rows if r['label']]
            expected=[h[alias]['endpoints'][0]]+h[alias]['endpoints'][1::2]
            self.assertEqual(len(labels),6)
            for row,e in zip(labels,expected):
                self.assertEqual((row['time'],row['price'],row['field'],row['source_hash']),
                                 (e['timestamp_utc'],e['price'],e['price_field'],e['source_hash']))
            for row in rows:
                self.assertEqual(Fraction(getattr(src[row['source_hash']][row['time']],row['field'])),Fraction(row['price']))
        artifact=task.old.read(task.PACK/'artifact.json')
        self.assertEqual(data,artifact['snapshot']['datasets'])
        self.assertEqual(task.old.read(task.PACK/'wave_table.json'),report.display.wave_table(self.doc))

    def test_indicator_context_preserved_without_inference(self):
        evidence=task.old.read(task.PACK/'indicator_evidence.json')
        expected=report.display.indicator_rows(task.old.read(task.old.PREVIOUS/'indicators_1D_verified.json'),task.old.read(task.old.PREVIOUS/'indicator_summary.json'))
        self.assertEqual(evidence['rows'],expected)
        self.assertTrue(all(not r['price_snapshot_comparable'] for r in expected))

    def test_report_styles_and_no_unverified_fragment_navigation(self):
        artifact=task.old.read(task.PACK/'artifact.json')
        prose='\n'.join(b.get('body','') for b in artifact['manifest']['blocks'])
        for marker in ('↝','⋯?⋯','×','CURRENT_WAVE_POSITION_UNRESOLVED','190.01','190.02'):
            self.assertIn(marker,prose)
        self.assertNotIn('](#',prose)
        for h in self.doc['hypotheses']:self.assertIn(h['display_id'],prose)


if __name__=='__main__':unittest.main()
