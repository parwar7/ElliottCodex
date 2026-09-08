"""Real public factories; synthetic deterministic inputs, never labelled NVDA."""
from dataclasses import replace
from datetime import datetime,timedelta,timezone
import pickle
import unittest
import support
from elliott_methodology_kernel import MethodologyKernel, OrderedChildBinding, AnalyzedWaveSubject
from elliott_methodology_kernel.contracts import Timeframe
from elliott_runtime.market_data.ingestion import _normalize
from elliott_runtime.analysis import normal_component_exploration as m
from test_normal_impulse_partial_evaluation import evaluate,equality_bridge
from test_candidate_generation import geometry

def fixture(start=None,count=96):
    parent=evaluate(equality_bridge())
    old=parent.evaluations[0].hypothesis.generated_candidate.source_observations
    start=start or datetime(2024,1,1,tzinfo=timezone.utc)
    rows=[]
    for i in range(count):
        center=30+(i%2)*5+i/100
        rows.append({'timestamp':(start+timedelta(hours=i)).isoformat(),'open':center,'high':center+1,'low':center-1,'close':center,'volume':100})
    finer=_normalize(rows,b'component-fixture','test','synthetic',old.symbol,Timeframe('1h',3600))
    config=geometry().config
    return parent,finer,config

class ComponentExplorationTests(unittest.TestCase):
    def setUp(self):self.kernel=MethodologyKernel(support.PROTECTED_ROOT)
    def test_genuine_identity_and_composition(self):
        parent,finer,config=fixture();s=m.prepare_component_search(parent,0,0,finer,config)
        r=m.evaluate_component(s,'2024-01-10T00:00:00Z',self.kernel,'genuine')
        self.assertTrue(r.children);self.assertIs(r,r.validated())
        role=parent.evaluations[0].hypothesis.role_bindings[0]
        for child,c in zip(r.children,r.compositions):
            self.assertIs(child.evaluations[0].bounded_result.subject,role.child_subject)
            self.assertIs(c.child_binding.ordered_children[0],role.child_subject)
            self.assertFalse(child.evaluations[0].family_validity_authority)
    def test_equivalent_foreign_binding_rejected_repeatedly(self):
        parent,finer,c=fixture();s=m.prepare_component_search(parent,0,0,finer,c)
        view=parent.evaluations[0].hypothesis.five_slot_view;b=view.binding
        object.__setattr__(view,'binding',OrderedChildBinding(b.binding_id,b.parent_subject,b.ordered_children))
        for _ in range(2):
            with self.assertRaises(ValueError):s.validated()
    def test_nested_parent_mutation_rejected(self):
        parent,finer,c=fixture();s=m.prepare_component_search(parent,0,0,finer,c)
        b=parent.evaluations[0].hypothesis.five_slot_view.binding
        object.__setattr__(b,'parent_subject',AnalyzedWaveSubject('foreign','foreign'))
        with self.assertRaises(ValueError):s.validated()
    def test_equal_content_foreign_snapshot_rejected(self):
        parent,finer,c=fixture();s=m.prepare_component_search(parent,0,0,finer,c)
        object.__setattr__(s,'observations',replace(finer))
        with self.assertRaises(ValueError):s.validated()
    def test_foreign_bar_tuple_rejected(self):
        parent,finer,c=fixture();s=m.prepare_component_search(parent,0,0,finer,c)
        object.__setattr__(s,'bars',tuple(list(s.bars)))
        with self.assertRaises(ValueError):s.validated()
    def test_nested_bar_mutation_rejected_without_refresh(self):
        parent,finer,c=fixture();s=m.prepare_component_search(parent,0,0,finer,c)
        object.__setattr__(s.bars[0],'volume',101)
        for _ in range(2):
            with self.assertRaises(ValueError):s.validated()
    def test_cache_identity_reused_not_context_authority(self):
        parent,finer,c=fixture();cache={}
        a=m.prepare_component_search(parent,0,0,finer,c,cache);b=m.prepare_component_search(parent,0,0,finer,c,cache)
        self.assertIs(a.discovery,b.discovery);self.assertIsNot(a,b)
        object.__setattr__(a.discovery.pivots[0],'observed_price',1.0)
        with self.assertRaises(ValueError):m.prepare_component_search(parent,0,0,finer,c,cache)
    def test_missing_history_is_not_impossibility(self):
        parent,finer,c=fixture(datetime(2025,1,1,tzinfo=timezone.utc))
        s=m.prepare_component_search(parent,0,0,finer,c)
        self.assertEqual('NO_FINER_COVERAGE',m.plan_component(s)['reason'])
        self.assertEqual((),m.evaluate_component(s,'2025-02-01',self.kernel,'empty').children)
    def test_partial_history_visible(self):
        parent,finer,c=fixture(datetime(2024,1,2,12,tzinfo=timezone.utc),24)
        s=m.prepare_component_search(parent,0,0,finer,c)
        self.assertEqual('PARTIAL_FINER_HISTORY',s.coverage)
    def test_insufficient_pivots_explicit(self):
        parent,finer,c=fixture(datetime(2024,1,2,tzinfo=timezone.utc),3)
        s=m.prepare_component_search(parent,0,0,finer,c)
        self.assertEqual('INSUFFICIENT_GEOMETRIC_PIVOTS',m.plan_component(s)['reason'])
    def test_parent_rejection_not_rescued_or_expanded(self):
        parent,finer,c=fixture();parent=evaluate()
        s=m.prepare_component_search(parent,0,0,finer,c)
        self.assertTrue(parent.evaluations[0].p004_result.fatal_to_candidate)
        self.assertEqual((),m.evaluate_component(s,'2024-01-10',self.kernel,'rejected').children)
    def test_order_budget_and_no_outcome_selection(self):
        parent,finer,c=fixture();s=m.prepare_component_search(parent,0,0,finer,c)
        plan=m.plan_component(s);self.assertEqual(plan,m.plan_component(s))
        self.assertLessEqual(len(plan['selected_starts']),2)
        self.assertFalse(plan['authority']);self.assertFalse(plan['exhaustive'])
        eligible=[x['start_index'] for x in plan['windows'] if x['domain']['eligible']]
        self.assertEqual(list(dict.fromkeys([eligible[0],eligible[-1]])),plan['selected_starts'])
    def test_forming_geometry_never_completion(self):
        parent,finer,c=fixture();s=m.prepare_component_search(parent,0,0,finer,c)
        r=m.evaluate_component(s,'2024-01-10',self.kernel,'forming')
        for child in r.children:
            item=child.evaluations[0];self.assertFalse(item.hypothesis.completion_authority)
            if any(x.state.value=='DEVELOPING' for x in item.hypothesis.generated_candidate.ordered_selected_pivots):
                self.assertEqual('UNRESOLVED',item.p005_result.status.value)
    def test_pickle_cannot_restore_live_links(self):
        parent,finer,c=fixture();s=m.prepare_component_search(parent,0,0,finer,c)
        with self.assertRaises(TypeError):pickle.dumps(s)
    def test_equal_resolution_not_degree_substitution(self):
        parent,finer,c=fixture()
        with self.assertRaises(ValueError):m.prepare_component_search(parent,0,0,replace(finer,timeframe=Timeframe('1d',86400)),c)
    def test_foreign_child_substitution(self):
        parent,finer,c=fixture();s=m.prepare_component_search(parent,0,0,finer,c)
        r=m.evaluate_component(s,'2024-01-10',self.kernel,'original')
        object.__setattr__(r,'children',(evaluate(equality_bridge()),))
        with self.assertRaises(ValueError):r.validated()
    def test_no_new_methodology_inventory(self):
        from elliott_methodology_kernel import EXECUTABLE_BEHAVIOR_IDS
        from elliott_methodology_kernel import _structural_invalidity_certification as a,_validated_internal_family_certification as b
        self.assertEqual((11,7,0,0),(len(EXECUTABLE_BEHAVIOR_IDS),len(a._PRODUCERS),len(b._PRODUCERS),len(b._ISSUED)))

if __name__=='__main__':unittest.main()
