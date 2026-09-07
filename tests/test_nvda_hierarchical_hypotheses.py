"""Historical planning and identity-bound reporting over genuine public results."""
import copy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import support
sys.path.insert(0, str(support.RUNTIME_ROOT/'tools'))
import nvda_hierarchical_hypotheses as h


class HistoricalPlanningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest,cls.data=h.p.load_inputs(h.INPUTS)
        cls.geometry=h.p.GeometricPivotDiscoveryConfig(h.p.GeometricPivotDiscoveryMethod.WINDOWED_LOCAL_EXTREMA,2,2,h.p.EqualExtremePolicy.LAST,True)
        cls.pivots=h.p.discover_geometric_pivots(h.p.GeometricPivotDiscoveryRequest('history-test',cls.data['1mo'],cls.geometry,('test',)))

    def test_regions_cannot_disappear_behind_latest_only(self):
        jobs,coverage=h.plan_windows(self.pivots.pivots,h.configuration()['regions_utc_years'])
        self.assertEqual([1,2,3],[x['region'] for x in coverage])
        self.assertEqual([0,1,2,3,4,5],jobs[0]['indices'])
        self.assertTrue(all(len(x['scheduled_window_starts'])==2 for x in coverage))

    def test_budget_exhaustion_has_exact_unvisited_windows(self):
        _,coverage=h.plan_windows(self.pivots.pivots,h.configuration()['regions_utc_years'],0)
        for c in coverage:
            self.assertEqual(c['eligible_window_starts'],c['unvisited_window_starts'])
            self.assertEqual([],c['scheduled_window_starts'])

    def test_deterministic_plan_and_no_duplicate_indices(self):
        a=h.plan_windows(self.pivots.pivots,h.configuration()['regions_utc_years'])
        self.assertEqual(a,h.plan_windows(self.pivots.pivots,h.configuration()['regions_utc_years']))
        for job in a[0]:self.assertEqual(sorted(set(job['indices'])),job['indices'])

    def test_coarsening_is_explicit_not_elliott_significance(self):
        jobs,_=h.plan_windows(self.pivots.pivots,h.configuration()['regions_utc_years'])
        self.assertEqual([0,14,28,42,56,70],jobs[-1]['indices'])
        self.assertEqual('COARSENED_SPANNING_HYPOTHESIS',jobs[-1]['kind'])
        self.assertIn('no significance claim',h.configuration()['spanning_policy'])

    def test_no_degree_or_position_authority(self):
        self.assertFalse(h.configuration()['degree_authority'])
        self.assertFalse(h.configuration()['current_position_template_authority'])
        self.assertGreater(self.pivots.pivots[0].timestamp_utc,self.data['1mo'].bars[0].timestamp_utc)

    def test_invalid_budget_rejected(self):
        for n in (True,-1,3,1.0):
            with self.subTest(n=n),self.assertRaises(ValueError):h.plan_windows(self.pivots.pivots,[],n)


class GenuineHierarchyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest,cls.data=h.p.load_inputs(h.INPUTS); collected=[]
        with patch.object(h.p.YahooFinanceProvider,'fetch',side_effect=AssertionError('No live network')):
            h.p.run_scope(cls.data['1mo'],cls.data['1wk'],h.p.MethodologyKernel(support.PROTECTED_ROOT),cls.manifest['requested_at_utc'],lambda _:None,observe_results=lambda *x:collected.append(x))
        cls.families,cls.internals,cls.child_families,cls.parent_partial,cls.child_partial=collected[0]
        cls.items=[i for i in cls.child_families.child_evaluations if i.family_hypothesis_result is not None and i.family_hypothesis_result.family_hypotheses]
        rows=h.reporting.family_rows(cls.families,'level-0','root')+h.reporting.normal_rows(cls.parent_partial,'level-0','root')
        for r in rows:r.update(root_job='root',level=0)
        children=[]
        for item in cls.items:
            req=h.check_child_link(cls.child_families,item,item.family_hypothesis_result)
            children+=h.reporting.family_rows(item.family_hypothesis_result,'level-1','root',req)
        children+=h.reporting.normal_rows(cls.child_partial,'level-1','root')
        for r in children:r.update(root_job='root',level=1)
        rows+=children
        for r in rows:r['observation_relation']=h.observation_relation(r,cls.data[r['timeframe']])
        requirements=[]
        for r in cls.internals.internal_requirements:
            a,b=r.parent_candidate.ordered_selected_pivots[r.child_index:r.child_index+2]
            requirements.append({'requirement_id':r.requirement_id,'parent_hypothesis_id':r.family_hypothesis.hypothesis_id,'start':a.timestamp_utc.isoformat(),'end':b.timestamp_utc.isoformat(),'requirement_satisfied':False})
        cls.doc={'hypotheses':rows,'requirements':requirements}

    def test_genuine_parent_child_ancestry_validates(self):
        self.assertGreater(h.audit(self.doc,self.data)['linked_rows'],0)
        item=self.items[0]
        self.assertIs(item.generated_child_evidence.internal_requirement,h.check_child_link(self.child_families,item,item.family_hypothesis_result))

    def test_cross_branch_substitution_rejected(self):
        self.assertGreater(len(self.items),1)
        with self.assertRaises(ValueError):h.check_child_link(self.child_families,self.items[0],self.items[1].family_hypothesis_result)

    def test_mapping_rejected_by_public_validator(self):
        with self.assertRaises(ValueError):h.check_child_link({},self.items[0],self.items[0].family_hypothesis_result)

    def test_report_branch_mutation_rejected(self):
        doc=copy.deepcopy(self.doc);r=next(x for x in doc['hypotheses'] if x['requirement_id']);r['root_job']='foreign'
        with self.assertRaises(ValueError):h.audit(doc,self.data)

    def test_trailing_bars_never_become_current_wave(self):
        rows=[r for r in self.doc['hypotheses'] if r['observation_relation']['trailing_unassigned_bars']]
        self.assertTrue(rows)
        self.assertTrue(all(r['observation_relation']['current_position']=='CURRENT_POSITION_UNRESOLVED' for r in rows))

    def test_endpoint_mutation_rejected(self):
        doc=copy.deepcopy(self.doc);doc['hypotheses'][0]['endpoints'][0]['price']+=1
        with self.assertRaises(ValueError):h.audit(doc,self.data)

    def test_p004_non_rescue_and_no_family_authority(self):
        rows=[r for r in self.doc['hypotheses'] if r['p005'] and r['p005']['status']=='SUFFICIENT_CONDITION_ESTABLISHED' and r['p004']['fatal']]
        self.assertTrue(rows)
        self.assertTrue(all(r['report_status']=='REJECTED_EXACT_HYPOTHESIS_P004' for r in rows))
        self.assertTrue(all(not r['authority']['family_validity'] for r in self.doc['hypotheses']))

    def test_duplicate_contexts_retain_every_link(self):
        rows=copy.deepcopy(self.doc['hypotheses']);groups=h.reporting.group_rows(rows)
        self.assertEqual(len(rows),sum(len(g['hypothesis_ids']) for g in groups))
        self.assertTrue(any(len(g['hypothesis_ids'])>1 for g in groups))

    def test_false_requirement_satisfaction_rejected(self):
        doc=copy.deepcopy(self.doc);doc['requirements'][0]['requirement_satisfied']=True
        with self.assertRaises(ValueError):h.audit(doc,self.data)

    def test_missing_finer_history_is_not_substituted(self):
        # Build a genuine earliest-history family; never fabricate a requirement.
        p=h.p;obs=self.data['1mo'];kernel=p.MethodologyKernel(support.PROTECTED_ROOT)
        geometry=p.GeometricPivotDiscoveryConfig(p.GeometricPivotDiscoveryMethod.WINDOWED_LOCAL_EXTREMA,2,2,p.EqualExtremePolicy.LAST,True)
        pivots=p.discover_geometric_pivots(p.GeometricPivotDiscoveryRequest('earliest-test',obs,geometry,('test',)))
        gen=p.generate_candidate_hypotheses(p.CandidateGenerationRequest('earliest-test',self.manifest['requested_at_utc'],p.AnalyzedWaveSubject('earliest-test','test'),obs,pivots,
            p.CandidateGenerationConfig(6,6,0,10,p.SHAPES,p.CandidatePivotWindow.EARLIEST),(),('test',)))
        competing=p.build_competing_candidate_set(p.CompetingCandidateSetRequest('earliest-test:set','test',gen,('test',)))
        bridge=p.build_family_evaluation_hypotheses(p.FamilyHypothesisBridgeRequest('earliest-test:family',self.manifest['requested_at_utc'],competing,(p.FamilyEvaluationKind.SINGLE_ZIGZAG,),('test',)),kernel)
        internals,selections,children,families,partial=h.child_layer(bridge,self.data['1h'],kernel,self.manifest['requested_at_utc'],'earliest-test:child',geometry)
        req=internals.internal_requirements[0]
        self.assertLess(req.parent_candidate.ordered_selected_pivots[req.child_index].timestamp_utc,self.data['1h'].bars[0].timestamp_utc)
        self.assertFalse(req.validated_child_family_authority)
        self.assertFalse(children.generated_child_evidence)
        self.assertTrue(all(s.selected_window.coverage_state.value=='NO_WINDOW_COVERAGE' for s in selections))

    def test_child_bridge_can_construct_next_exact_requirements(self):
        item=self.items[0];bridge=item.family_hypothesis_result
        req=h.check_child_link(self.child_families,item,bridge)
        next_result=h.p.evaluate_family_internal_subdivisions(h.p.FamilyInternalSubdivisionEvaluationRequest('next-test',bridge,(),('test',)))
        self.assertTrue(next_result.internal_requirements)
        self.assertTrue(all(r.family_hypothesis.parent_subject is req.child_subject for r in next_result.internal_requirements))

    def test_foreign_snapshot_rejected(self):
        doc=copy.deepcopy(self.doc);doc['hypotheses'][0]['snapshot_content_sha256']='foreign'
        with self.assertRaises(ValueError):h.audit(doc,self.data)

    def test_render_and_csv_are_deterministic(self):
        doc=copy.deepcopy(self.doc)
        h.reporting.assign_display_refs(doc)
        doc['groups']=h.reporting.group_rows(doc['hypotheses'])
        for i,r in enumerate(doc['requirements']):r['display_ref']=f'R{i:04}'
        doc.update(coverage=[],stops=[],cross_region_window_starts_excluded_by_policy=[])
        doc['audit']=h.audit(doc,self.data)
        text=h.render(doc)
        self.assertEqual(text,h.render(copy.deepcopy(doc)))
        self.assertEqual(h.reporting.evidence_exports(doc),h.reporting.evidence_exports(copy.deepcopy(doc)))
        self.assertIn('Current position: unresolved',text)

    def test_exact_ratio_and_provenance_tamper_rejected(self):
        for field in ('represented_ratio','bar_provenance'):
            doc=copy.deepcopy(self.doc);doc['hypotheses'][0]['endpoints'][0][field]={}
            with self.subTest(field=field),self.assertRaises(ValueError):h.audit(doc,self.data)


if __name__=='__main__':unittest.main()
