"""Meaningful analysis/report regressions; no live retrieval or full search replay."""
import ast
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
import unittest
from unittest.mock import patch

import nvda_english_analysis as task
import nvda_english_report as report


class EnglishAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snapshots,cls.raw=task.old.tv.load_inputs()
        cls.doc=task.old.read(task.PACK/'analysis.json')
        cls.canonical=task.old.read(task.PACK/'canonical_hierarchy.json')
        cls.cases=cls.canonical['new_hypotheses']+cls.canonical['reused_local_cases']
        cls.jobs,cls.plan=task.plan(cls.snapshots)

    def test_predeclared_plan_deterministic(self):
        _,again=task.plan(self.snapshots)
        self.assertEqual(again,self.plan)
        self.assertEqual(len(self.jobs),8)
        saved=task.old.read(task.PACK/'selection_before_evaluation.json')
        self.assertFalse(saved['outcome_selection'])
        self.assertLessEqual(len(self.jobs),saved['max_evaluations'])

    def test_every_selected_pivot_is_exact_original_member(self):
        for alias,res,d,points in self.jobs:
            self.assertIs(d.input_observations,self.snapshots[res].observations)
            self.assertEqual(type(points),tuple)
            self.assertEqual(len({id(p) for p in points}),6)
            for p in points:self.assertTrue(any(p is q for q in d.pivots))
            self.assertTrue(all(a.timestamp_utc<b.timestamp_utc for a,b in zip(points,points[1:])))

    def test_revised_root_uses_2008_and_does_not_rewrite_2009(self):
        h=self.cases[0]
        self.assertEqual(h['endpoints'][3]['price'],0.14375)
        self.assertTrue(h['endpoints'][3]['timestamp_utc'].startswith('2008-11'))
        prior=task.old.read(task.previous.PACK/'synthesis.json')
        self.assertEqual(prior['display_cases'][0]['endpoints'][3]['price'],0.289)

    def test_data_start_not_assigned_origin(self):
        h=self.cases[0];s=self.snapshots['1M']
        self.assertGreater(h['endpoints'][0]['timestamp_utc'],s.observations.bars[0].timestamp_utc.isoformat())
        self.assertEqual(h['degree'],'DEGREE_UNRESOLVED')

    def test_invalid_or_empty_regions(self):
        d=self.jobs[0][2]
        with self.assertRaises(ValueError):task.select_regions(d,())
        missing=tuple(('1800','1801','HIGH') for _ in range(6))
        self.assertEqual(task.select_regions(d,missing),((),'MISSING_ORIGINAL_PIVOT'))
        duplicate=tuple(('2007-10','2007-11','HIGH') for _ in range(6))
        with self.assertRaises(ValueError):task.select_regions(d,duplicate)

    def test_all_exported_operands_reconcile_to_raw(self):
        self.assertEqual(report.reconcile_cases(self.cases,self.snapshots,self.raw)['raw_endpoint_fields_checked'],122)

    def test_foreign_snapshot_rejected(self):
        h=deepcopy(self.cases[0]);h['source_response_sha256']='foreign'
        with self.assertRaises(ValueError):report.reconcile_cases([h],self.snapshots,self.raw)
        with self.assertRaises(ValueError):task.factual_measures(h,self.snapshots['1M'])

    def test_altered_price_and_field_rejected(self):
        for field,value in [('price',0.061),('price_field','high')]:
            h=deepcopy(self.cases[0]);h['endpoints'][0][field]=value
            with self.assertRaises(ValueError):report.reconcile_cases([h],self.snapshots,self.raw)
            with self.assertRaises(ValueError):task.factual_measures(h,self.snapshots['1M'])

    def test_p004_rejection_not_rescued_by_p005(self):
        h=deepcopy(self.cases[0]);self.assertEqual(h['p005']['status'],'SUFFICIENT_CONDITION_ESTABLISHED')
        h['p004']['fatal']=True
        with self.assertRaises(ValueError):report.reconcile_cases([h],self.snapshots,self.raw)

    def test_foreign_orthodox_authority_rejected(self):
        h=deepcopy(self.cases[0]);h['endpoints'][0]['orthodox_endpoint_authority']=True
        with self.assertRaises(ValueError):report.reconcile_cases([h],self.snapshots,self.raw)

    def test_factual_ratios_are_exact_and_not_p005(self):
        h=self.cases[0];m=task.factual_measures(h,self.snapshots['1M'])
        length=lambda i:abs(Fraction(h['endpoints'][2*i+1]['price'])-Fraction(h['endpoints'][2*i]['price']))
        self.assertEqual(m['ratios']['role2_over_role1'],task.old.p.plain(length(1)/length(0)))
        self.assertFalse(m['fib_match_asserted']);self.assertIsNone(m['target']);self.assertIsNone(m['tolerance'])
        self.assertIn('NOT_P005',m['basis'])

    def test_volume_peak_uses_declared_interior_bars(self):
        h=next(h for h in self.cases if h['display_id']=='RECENT-D')
        m=task.factual_measures(h,self.snapshots['1D'])
        for v in m['volume_windows']:
            a,b=v['bar_label_window_open']
            bars=[r for r in self.snapshots['1D'].observations.bars if a<r.timestamp_utc.isoformat()<b and r.volume is not None]
            self.assertEqual(v['peak_volume'],max(r.volume for r in bars))
            self.assertTrue(all(a<e['bar_label_utc']<b for e in v['peak_occurrences']))
            self.assertTrue(v['endpoint_bars_excluded'])
            self.assertTrue(v['volume_interpretation'].startswith('NEUTRAL'))

    def test_snapshot_and_developing_alternatives_separate(self):
        a,b=self.cases[:2]
        self.assertNotEqual(a['hypothesis_id'],b['hypothesis_id'])
        self.assertEqual(a['endpoints'][-1]['price'],236.54)
        self.assertEqual(b['endpoints'][-1]['pivot_state'],'DEVELOPING')
        self.assertEqual(b['p005']['reason'],'DEVELOPING_REQUIRED_ENDPOINT')
        self.assertFalse(b['current_position']['completion_authority'])

    def test_genuine_links_preserve_duplicate_contexts(self):
        links=self.doc['links']
        self.assertEqual(len(links),4)
        samechild=[x for x in links if x['child']=='MIDDLE-D']
        self.assertEqual(len(samechild),2)
        self.assertEqual(len({x['child_hypothesis_id'] for x in samechild}),1)
        self.assertEqual(len({x['parent_hypothesis_id'] for x in samechild}),2)
        self.assertTrue(all(not x['kernel_ancestry'] and not x['complete_subdivision'] for x in links))
        self.assertEqual([x for x in links if x['parent']=='H-SEP' and x['child']=='RECENT-D'][0]['relationship'],'INTERIOR_OBSERVATION')

    def test_weekly_contexts_not_invented_factory_links(self):
        self.assertTrue(all(not x['child'].endswith('-W') for x in self.doc['links']))
        self.assertIn('UNSUPPORTED',self.doc['weekly_relationship_limit'])

    def test_reused_local_cases_and_links_are_unchanged(self):
        original=task.old.read(task.previous.previous.PACK/'canonical_hierarchy.json')
        by_id={h['display_id']:h for h in original['hypotheses']+original['corrective_hypotheses']}
        for h in self.canonical['reused_local_cases']:self.assertEqual(h,by_id[h['display_id']])
        self.assertEqual(self.canonical['unmodified_prior_interior_links'],[x for x in original['links'] if x['surviving_observational_link']])

    def test_wave_table_keeps_actual_role_and_parent(self):
        rows=report.wave_rows(self.cases);self.assertEqual(rows,self.canonical['wave_rows'])
        self.assertEqual(len(rows),61)
        for r in rows:
            h=next(x for x in self.cases if x['display_id']==r['parent_id'])
            self.assertEqual(r['hypothesis_id'],h['hypothesis_id'])
            self.assertEqual(r['internal_status'],'INTERNALS_UNRESOLVED')

    def test_charts_match_saved_values_and_tail_stays_unlabelled(self):
        datasets=task.old.read(task.PACK/'chart_rows.json')
        self.assertEqual(report.reconcile_charts(datasets,self.snapshots,self.raw),1939)
        rows=datasets['plot-D2026-1D-N6-S38']
        self.assertGreater(max(r['time'] for r in rows if not r['label']),max(r['time'] for r in rows if r['label']))

    def test_english_and_no_false_current_position(self):
        text=(task.PACK/'report.md').read_text(encoding='utf-8')
        self.assertFalse(any('\u0600'<=c<='\u06ff' for c in text))
        self.assertIn('CURRENT_WAVE_POSITION_UNRESOLVED',text)
        self.assertIsNone(self.canonical['rank']);self.assertFalse(self.canonical['family_validity'])
        self.assertEqual(self.canonical['inventories'],[11,7,0,0])

    def test_no_outside_write_or_sealed_pack_rebuild(self):
        with self.assertRaises(ValueError):report.build(Path('C:/outside'))

    def test_report_has_no_evaluation_network_or_certificate_calls(self):
        tree=ast.parse(Path(report.__file__).read_text())
        names=[ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n,ast.Call)]
        self.assertFalse(any(any(x in n for x in ('evaluate_scope','certify_','requests.','fetch','subprocess')) for n in names))


if __name__=='__main__':unittest.main()
