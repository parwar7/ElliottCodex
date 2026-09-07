"""Deterministic search-domain tests using genuine geometry/candidate factories."""
import copy
from dataclasses import replace
import math
import unittest
from unittest.mock import patch

import support
import sys
sys.path.insert(0,str(support.RUNTIME_ROOT/'tools'))
import nvda_geometric_swing_quality as s
from test_geometric_pivots import observations, config, request
from elliott_runtime.analysis.geometric_swing_search import GeometricSwingSearchConfig, movement_domain, select_geometric_swing_requests

p=s.p


def template(data, width=1, name='swing-test', configured=None):
    g=configured or config(left_window_bars=width,right_window_bars=width,include_developing=True)
    result=p.discover_geometric_pivots(request(data,g,request_id=name))
    return p.CandidateGenerationRequest(name,'2026-09-06T00:00:00Z',p.AnalyzedWaveSubject(name,'test'),data,result,
        p.CandidateGenerationConfig(6,6,0,4,p.SHAPES,p.CandidatePivotWindow.EARLIEST),(),('test',))


class MovementDomainTests(unittest.TestCase):
    def test_rising_consecutive_is_search_exclusion_not_invalidity(self):
        result=movement_domain((1,2,3,4));self.assertFalse(result['eligible']);self.assertFalse(result['structural_invalidity'])
        self.assertEqual(['CONSECUTIVE_SAME_DIRECTION'],result['search_exclusion_reasons'])

    def test_falling_consecutive_is_search_exclusion(self):
        self.assertFalse(movement_domain((5,4,3))['eligible'])

    def test_zero_movement_is_excluded(self):
        self.assertIn('ZERO_PRICE_MOVEMENT',movement_domain((1,2,2,1))['search_exclusion_reasons'])

    def test_alternating_both_directions_retained(self):
        for x in ((1,4,2,5,3,6),(6,3,5,2,4,1)):
            self.assertTrue(movement_domain(x)['eligible'])

    def test_exact_nextafter_no_tolerance(self):
        self.assertTrue(movement_domain((1.0,math.nextafter(1.0,2.0),1.0))['eligible'])

    def test_extreme_finite_values_without_subtraction_overflow(self):
        self.assertTrue(movement_domain((-1e308,1e308,-1e308))['eligible'])

    def test_bad_numeric_and_container_inputs(self):
        for x in ([1,2],(1,),('1',2),(True,2),(1,float('inf')),(float('nan'),1)):
            with self.subTest(x=x),self.assertRaises(ValueError):movement_domain(x)

    def test_no_elliott_authority_in_result(self):
        r=movement_domain((1,3,2));self.assertEqual('PROJECT_OPERATIONAL_POLICY',r['classification'])
        self.assertEqual({'eligible','movements','search_exclusion_reasons','classification','structural_invalidity'},set(r))


class SelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m,cls.data=p.load_inputs(s.hierarchy.INPUTS)
        cls.t=template(cls.data['1mo'],2)
        cls.c=GeometricSwingSearchConfig(((1999,2007),(2008,2016),(2017,2026)),1,10000,10000)

    def test_early_middle_recent_budget_and_unvisited(self):
        requests,d=select_geometric_swing_requests(self.t,self.c)
        self.assertEqual(3,len(requests));self.assertTrue(all(r['unvisited_starts'] for r in d['regions']))
        self.assertEqual([5,24,49],[r['selected_starts'][0] for r in d['regions']])

    def test_zero_budget_reports_all_unvisited(self):
        requests,d=select_geometric_swing_requests(self.t,replace(self.c,sequences_per_region=0))
        self.assertEqual((),requests)
        for r in d['regions']:self.assertEqual(r['eligible_starts'],r['unvisited_starts'])

    def test_deterministic_requests_and_diagnostics(self):
        a,ad=select_geometric_swing_requests(self.t,self.c);b,bd=select_geometric_swing_requests(self.t,self.c)
        self.assertEqual(ad,bd);self.assertEqual([r.request_id for r in a],[r.request_id for r in b])
        for x,y in zip(a,b):
            self.assertTrue(all(i is j for i,j in zip(x.scoped_pivots,y.scoped_pivots)))

    def test_exact_pivots_observation_config_and_generated_candidates(self):
        requests,_=select_geometric_swing_requests(self.t,self.c)
        r=requests[0];self.assertIs(r.observations,self.t.observations);self.assertIs(r.geometric_pivots,self.t.geometric_pivots)
        result=p.generate_candidate_hypotheses(r)
        self.assertEqual(4,len(result.candidates))
        for c in result.candidates:
            self.assertTrue(movement_domain(tuple(x.observed_price for x in c.ordered_selected_pivots))['eligible'])
            self.assertTrue(all(any(x is y for y in self.t.geometric_pivots.pivots) for x in c.ordered_selected_pivots))

    def test_cross_snapshot_substitution_rejected(self):
        t=copy.copy(self.t);object.__setattr__(t,'observations',copy.copy(t.observations))
        with self.assertRaises(ValueError):select_geometric_swing_requests(t,self.c)

    def test_cross_configuration_pivot_identity_rejected(self):
        t=copy.copy(self.t);result=copy.copy(t.geometric_pivots);pivot=copy.copy(result.pivots[0])
        object.__setattr__(pivot,'discovery_parameters',copy.copy(result.config))
        object.__setattr__(result,'pivots',(pivot,)+result.pivots[1:]);object.__setattr__(t,'geometric_pivots',result)
        with self.assertRaises(ValueError):select_geometric_swing_requests(t,self.c)

    def test_mapping_and_subclass_config_rejected(self):
        class Sub(GeometricSwingSearchConfig):pass
        for t,c in (({},self.c),(self.t,{}),(self.t,Sub(self.c.regions,1,10000,10000))):
            with self.assertRaises(ValueError):select_geometric_swing_requests(t,c)

    def test_bounds_and_overlapping_regions_fail(self):
        for c in (replace(self.c,sequences_per_region=True),replace(self.c,max_source_pivots=2),replace(self.c,max_source_bars=2),replace(self.c,regions=((2000,2010),(2009,2020)))):
            with self.assertRaises(ValueError):select_geometric_swing_requests(self.t,c)

    def test_tie_policy_and_dual_extrema_remain_discovery_diagnostics(self):
        data=observations([2,6,6,2,8,2],[1,3,3,1,0,1]);t=template(data,configured=config(equal_extreme_policy=p.EqualExtremePolicy.LAST,include_developing=True))
        _,d=select_geometric_swing_requests(t,replace(self.c,regions=((2024,2024),)))
        self.assertTrue(d['tie_windows']);self.assertIn('AMBIGUOUS_SAME_BAR_HIGH_LOW_EXCLUDED=1',d['geometry_diagnostics'])
        self.assertEqual('LAST',d['equal_extreme_policy']);self.assertFalse(d['structural_invalidity'])

    def test_same_kind_pairs_reported_without_consolidation(self):
        _,d=select_geometric_swing_requests(self.t,self.c)
        self.assertTrue(d['same_kind_adjacent_pairs']);self.assertTrue(d['consolidation'].startswith('NONE'))

    def test_duplicate_origin_retained_across_discoveries(self):
        other=template(self.data['1mo'],2,name='other-origin')
        a,_=select_geometric_swing_requests(self.t,self.c);b,_=select_geometric_swing_requests(other,self.c)
        self.assertNotEqual(a[0].request_id,b[0].request_id)
        self.assertEqual([x.observed_price for x in a[0].scoped_pivots],[x.observed_price for x in b[0].scoped_pivots])
        self.assertTrue(all(x is not y for x,y in zip(a[0].scoped_pivots,b[0].scoped_pivots)))

    def test_old_h0467_is_not_reclassified_as_elliott_invalid(self):
        c=s.old_comparison(self.data);self.assertEqual(['UP']*5,c['domain']['movements'])
        self.assertFalse(c['new_structural_certificate']);self.assertFalse(c['domain']['structural_invalidity'])

    def test_new_configuration_is_not_equal_index_sampling_or_degree(self):
        c=s.configuration();self.assertEqual([2,4,8],c['geometry_windows'])
        self.assertFalse(c['ranking']);self.assertFalse(c['degree_inference']);self.assertFalse(c['current_position_inference'])


class GenuineDelegationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m,cls.data=p.load_inputs(s.hierarchy.INPUTS);t=template(cls.data['1mo'],2)
        requests,_=select_geometric_swing_requests(t,GeometricSwingSearchConfig(((1999,2007),),1,10000,10000))
        cls.request=requests[0];refs=('swing-test',);at=cls.m['requested_at_utc'];cls.kernel=p.MethodologyKernel(support.PROTECTED_ROOT)
        with patch.object(p.YahooFinanceProvider,'fetch',side_effect=AssertionError('No live retrieval')):
            generated=p.generate_candidate_hypotheses(cls.request)
            competing=p.build_competing_candidate_set(p.CompetingCandidateSetRequest('swing-set','swing',generated,refs))
            cls.bridge=p.build_family_evaluation_hypotheses(p.FamilyHypothesisBridgeRequest('swing-family',at,competing,tuple(p.FamilyEvaluationKind),refs),cls.kernel)
            cls.partial=p.evaluate_normal_impulse_partial_scope(p.NormalImpulsePartialEvaluationRequest('swing-normal',at,cls.bridge,100,100,100,refs),cls.kernel)
            cls.internals,cls.selections,cls.children,cls.families,cls.child_partial=s.hierarchy.child_layer(cls.bridge,cls.data['1wk'],cls.kernel,at,'swing-child',cls.request.geometric_pivots.config)

    def test_existing_normal_endpoints_preserve_request_pivots(self):
        rows=s.reporting.normal_rows(self.partial,'parent','test')
        self.assertTrue(rows)
        for row in rows:
            self.assertTrue(s.row_domain(row)['eligible']);self.assertFalse(row['authority']['family_validity'])
        for e in self.partial.evaluations:
            self.assertIs(e.hypothesis.generated_candidate.source_geometric_pivots,self.request.geometric_pivots)

    def test_genuine_child_ancestry_and_foreign_substitution(self):
        items=[x for x in self.families.child_evaluations if x.family_hypothesis_result is not None]
        self.assertGreater(len(items),1)
        req=s.hierarchy.check_child_link(self.families,items[0],items[0].family_hypothesis_result)
        self.assertIs(req,items[0].generated_child_evidence.internal_requirement)
        with self.assertRaises(ValueError):s.hierarchy.check_child_link(self.families,items[0],items[1].family_hypothesis_result)

    def test_p004_fatality_not_overridden_and_no_family_proof(self):
        rows=s.reporting.normal_rows(self.partial,'parent','test')+s.reporting.normal_rows(self.child_partial,'child','test')
        self.assertTrue(rows)
        for row in rows:
            self.assertEqual(row['p004']['fatal'],row['report_status']=='REJECTED_EXACT_HYPOTHESIS_P004')
            self.assertFalse(row['authority']['family_validity'])
        for item in self.children.generated_child_evidence:
            self.assertFalse(item.requirement_satisfied);self.assertFalse(item.validated_internal_family)

    def reporting_document(self):
        rows=s.reporting.family_rows(self.bridge,'parent','test')+s.reporting.normal_rows(self.partial,'parent','test')
        requirements=[]
        for req,selection in zip(self.internals.internal_requirements,self.selections,strict=True):
            requirements.append({'requirement_id':req.requirement_id,'parent_hypothesis_id':req.family_hypothesis.hypothesis_id,
                'start':selection.selected_window.parent_window_start_utc.isoformat(),'end':selection.selected_window.parent_window_end_utc.isoformat(),'requirement_satisfied':False})
        for item in self.families.child_evaluations:
            if item.family_hypothesis_result is not None:
                req=s.hierarchy.check_child_link(self.families,item,item.family_hypothesis_result)
                rows+=s.reporting.family_rows(item.family_hypothesis_result,'child','test',req)
        rows+=s.reporting.normal_rows(self.child_partial,'child','test')
        for row in rows:
            row.update(root_job='test',level=0 if row['path']=='parent' else 1)
            row['observation_relation']=s.hierarchy.observation_relation(row,self.data[row['timeframe']])
            row['geometric_domain']=s.row_domain(row)
        doc={'hypotheses':rows,'requirements':requirements,'comparison':s.old_comparison(self.data),'scales':[],'stops':[]}
        doc['totals']=s.totals(rows);s.reporting.assign_display_refs(doc)
        doc['groups']=s.reporting.group_rows(rows)
        return doc

    def test_new_audit_accepts_genuine_links_and_exact_bar_prices(self):
        d=self.reporting_document();self.assertGreater(s.audit(d,self.data)['linked_rows'],0)

    def test_new_audit_rejects_false_movements_and_counts(self):
        for field in ('movements','totals'):
            d=self.reporting_document()
            if field=='movements':d['hypotheses'][0]['geometric_domain']['movements'][0]='ZERO'
            else:d['totals']['parent']['hypotheses']+=1
            with self.assertRaises(ValueError):s.audit(d,self.data)

    def test_report_and_existing_exports_replay_deterministically(self):
        d=self.reporting_document()
        self.assertEqual(s.render(d),s.render(copy.deepcopy(d)))
        self.assertEqual(s.render(d),s.render(p.json.loads(p.encoded(d))))
        self.assertEqual(s.reporting.evidence_exports(d),s.reporting.evidence_exports(copy.deepcopy(d)))
        self.assertIn('Current position unresolved',s.render(d))

    def test_report_audit_rejects_wrong_parent_link_and_false_current_position(self):
        for field in ('ancestry','position'):
            d=self.reporting_document();r=next(r for r in d['hypotheses'] if r['requirement_id'])
            if field=='ancestry':r['parent_family_hypothesis_id']='foreign'
            else:r['observation_relation']['current_position']='CURRENT_WAVE_5'
            with self.assertRaises(ValueError):s.audit(d,self.data)

    def test_report_audit_rejects_changed_discovery_evidence(self):
        d=self.reporting_document()
        g=p.GeometricPivotDiscoveryConfig(p.GeometricPivotDiscoveryMethod.WINDOWED_LOCAL_EXTREMA,2,2,p.EqualExtremePolicy.LAST,True)
        result=p.discover_geometric_pivots(p.GeometricPivotDiscoveryRequest(s.STAGE+':scale-2',self.data['1mo'],g,(s.STAGE,)))
        t=p.CandidateGenerationRequest(s.STAGE+':scale-2',self.m['requested_at_utc'],p.AnalyzedWaveSubject('audit-test','test'),self.data['1mo'],result,p.CandidateGenerationConfig(6,6,0,4,p.SHAPES,p.CandidatePivotWindow.EARLIEST),(),(s.STAGE,))
        _,coverage=select_geometric_swing_requests(t,GeometricSwingSearchConfig(((1999,2007),(2008,2016),(2017,2026)),1,10000,10000))
        d['scales']=[{'window':2,'coverage':coverage,'pivots':s.pivot_records(t.geometric_pivots),'config':p.plain(t.geometric_pivots.config),'snapshot_content_sha256':p.sha(p.encoded(self.data['1mo']))}]
        self.assertEqual('PASS',s.audit(d,self.data)['result'])
        d['scales'][0]['pivots'][0]['price']+=1
        with self.assertRaises(ValueError):s.audit(d,self.data)


class HistoricalNonRescueReportingTests(unittest.TestCase):
    def test_actual_saved_fatal_and_sufficient_contexts_remain_fatal_in_totals(self):
        d=p.json.loads((s.PREVIOUS/'report/results.json').read_bytes())
        rows=[r for r in d['hypotheses'] if r['p004'] and r['p004']['fatal'] and r['p005']['status']=='SUFFICIENT_CONDITION_ESTABLISHED']
        self.assertEqual(8,len(rows))
        for r in rows:
            self.assertEqual('REJECTED_EXACT_HYPOTHESIS_P004',r['report_status'])
            r['path']='child'
            r['geometric_domain']=s.row_domain(r)
        self.assertEqual(8,s.totals(rows)['child']['p004_invalid_despite_p005_sufficiency'])


if __name__=='__main__':unittest.main()
