import ast
import copy
import pickle
import unittest

import support
import elliott_methodology_kernel._structural_invalidity_certification as structural_private
import elliott_methodology_kernel._validated_internal_family_certification as family_private
from elliott_runtime.analysis.endpoint_path_evidence import (
    ENDPOINT_AUTHORITY_CLASS,
    ORTHODOX_ELLIOTT_ENDPOINT_AUTHORITY,
    PATH_EXTREME_IS_NOT_ORTHODOX_ENDPOINT,
    ROLE_CLASSIFICATION,
    ComponentEndpointState,
    EndpointPathEvidenceError,
    EndpointPathEvidenceLimitExceeded,
    EndpointPathEvidenceRequest,
    ObservedComponentDirection,
    build_endpoint_path_evidence,
    validate_endpoint_path_evidence_result,
)
from elliott_runtime.analysis.family_hypotheses import FamilyEvaluationKind
from elliott_runtime.market_data.geometric_pivots import GeometricPivotState
from test_family_hypotheses import bridge


def hypothesis(kind=FamilyEvaluationKind.TRIANGLE):
    return next(x for x in bridge(families=(kind,)).family_hypotheses if x.family_kind is kind)


def request(kind=FamilyEvaluationKind.TRIANGLE, **changes):
    h=changes.pop("family_hypothesis",hypothesis(kind))
    values={"request_id":"endpoint-path:test","family_hypothesis":h,"source_observations":h.generated_candidate.source_observations,"max_path_bars":1000,"provenance_refs":("endpoint-path:test",)}
    values.update(changes); return EndpointPathEvidenceRequest(**values)


class EndpointPathEvidenceTests(unittest.TestCase):
    def test_authority_levels_are_explicit_and_never_orthodox(self):
        result=build_endpoint_path_evidence(request())
        self.assertEqual("HYPOTHESIS_ROLE_METADATA",ROLE_CLASSIFICATION)
        self.assertEqual("HYPOTHESIS_BOUND_COMPONENT_ENDPOINT",ENDPOINT_AUTHORITY_CLASS)
        self.assertFalse(ORTHODOX_ELLIOTT_ENDPOINT_AUTHORITY)
        self.assertTrue(PATH_EXTREME_IS_NOT_ORTHODOX_ENDPOINT)
        self.assertFalse(any((result.family_validity_authority,result.wave_validity_authority,result.degree_authority)))
        self.assertTrue(all(x.hypothesis_only and not x.family_validity_authority and not x.wave_validity_authority and not x.degree_authority for x in result.component_role_bindings))

    def test_protected_family_role_orders_are_hypothesis_local(self):
        expected={FamilyEvaluationKind.SINGLE_ZIGZAG:("A","B","C"),FamilyEvaluationKind.FLAT:("A","B","C"),FamilyEvaluationKind.TRIANGLE:("A","B","C","D","E"),FamilyEvaluationKind.ENDING_DIAGONAL:("1","2","3","4","5")}
        for kind,roles in expected.items():
            with self.subTest(kind=kind):
                result=build_endpoint_path_evidence(request(kind))
                self.assertEqual(roles,tuple(x.component_role for x in result.component_role_bindings))
                self.assertFalse(any(x.family_validity_authority for x in result.component_role_bindings))

    def test_exact_hypothesis_candidate_pivots_children_and_prices_are_retained(self):
        req=request(); result=build_endpoint_path_evidence(req); h=req.family_hypothesis; pivots=h.generated_candidate.ordered_selected_pivots
        self.assertIs(h,result.family_hypothesis)
        for i,(binding,endpoint) in enumerate(zip(result.component_role_bindings,result.component_endpoint_evidence,strict=True)):
            self.assertIs(h,binding.family_hypothesis); self.assertIs(h.ordered_child_subjects[i],binding.child_subject)
            self.assertIs(pivots[i],binding.start_boundary); self.assertIs(pivots[i+1],binding.end_boundary)
            self.assertIs(binding.end_boundary,endpoint.boundary_pivot); self.assertIs(binding.end_boundary.observed_price,endpoint.observed_price)
            self.assertIs(binding.end_boundary.pivot_kind,endpoint.geometric_pivot_kind)

    def test_same_role_text_under_distinct_hypotheses_has_distinct_binding_identity(self):
        zig=build_endpoint_path_evidence(request(FamilyEvaluationKind.SINGLE_ZIGZAG))
        flat=build_endpoint_path_evidence(request(FamilyEvaluationKind.FLAT))
        self.assertEqual("A",zig.component_role_bindings[0].component_role)
        self.assertEqual("A",flat.component_role_bindings[0].component_role)
        self.assertIsNot(zig.component_role_bindings[0],flat.component_role_bindings[0])
        self.assertIsNot(zig.family_hypothesis,flat.family_hypothesis)

    def test_exact_inclusive_path_bars_and_factual_extrema(self):
        result=build_endpoint_path_evidence(request())
        for path in result.component_path_evidence:
            start=path.role_binding.start_boundary.timestamp_utc; end=path.role_binding.end_boundary.timestamp_utc
            expected=tuple(x for x in path.source_observations.bars if start<=x.timestamp_utc<=end)
            self.assertEqual(len(expected),len(path.exact_bars)); self.assertTrue(all(a is b for a,b in zip(expected,path.exact_bars,strict=True)))
            self.assertEqual(max(x.high for x in expected),path.observed_high_extreme)
            self.assertEqual(min(x.low for x in expected),path.observed_low_extreme)
            self.assertFalse(path.wave_validity_authority)

    def test_direction_is_endpoint_arithmetic_only(self):
        result=build_endpoint_path_evidence(request())
        for path in result.component_path_evidence:
            a=path.role_binding.start_boundary.observed_price; b=path.role_binding.end_boundary.observed_price
            expected=ObservedComponentDirection.UP if b>a else ObservedComponentDirection.DOWN if b<a else ObservedComponentDirection.EQUAL
            self.assertIs(expected,path.observed_direction)
        self.assertFalse(any(hasattr(path,"degree") for path in result.component_path_evidence))

    def test_developing_state_is_retained_without_elliott_confirmation(self):
        result=build_endpoint_path_evidence(request())
        for endpoint in result.component_endpoint_evidence:
            expected=ComponentEndpointState.DEVELOPING_HYPOTHESIS_BOUND_ENDPOINT if endpoint.geometric_state is GeometricPivotState.DEVELOPING else ComponentEndpointState.CONFIRMED_BY_GEOMETRY_HYPOTHESIS_BOUND_ENDPOINT
            self.assertIs(expected,endpoint.endpoint_state); self.assertFalse(endpoint.orthodox_elliott_endpoint_authority)

    def test_triangle_c_e_operands_are_available_but_no_rule_is_executed(self):
        result=build_endpoint_path_evidence(request())
        by_role={x.role_binding.component_role:x for x in result.component_endpoint_evidence}
        self.assertIs(result.component_role_bindings[2].end_boundary,by_role["C"].boundary_pivot)
        self.assertIs(result.component_role_bindings[4].end_boundary,by_role["E"].boundary_pivot)
        self.assertIn("NO_FAMILY_VALIDITY_OR_RULE_EXECUTION",result.diagnostics)
        self.assertFalse(hasattr(result,"structural_invalidity"))

    def test_foreign_observations_mapping_duck_and_subclass_fail_closed(self):
        h=hypothesis()
        with self.assertRaises(EndpointPathEvidenceError): EndpointPathEvidenceRequest("x",h,object(),10,("x",))
        with self.assertRaises(EndpointPathEvidenceError): build_endpoint_path_evidence({})
        class Duck: pass
        with self.assertRaises(EndpointPathEvidenceError): build_endpoint_path_evidence(Duck())
        with self.assertRaises(TypeError):
            class Sub(EndpointPathEvidenceRequest): pass

    def test_mutation_fails_closed(self):
        req=request(); result=build_endpoint_path_evidence(req)
        object.__setattr__(req,"request_id","changed")
        with self.assertRaises(EndpointPathEvidenceError): validate_endpoint_path_evidence_result(result)

    def test_pickle_cannot_restore_live_authority(self):
        result=build_endpoint_path_evidence(request())
        for value in (result.request,result,result.component_role_bindings[0],result.component_endpoint_evidence[0],result.component_path_evidence[0]):
            with self.assertRaises(TypeError): pickle.dumps(value)

    def test_preflight_cap_rejects_without_partial_result(self):
        req=request(max_path_bars=1)
        with self.assertRaises(EndpointPathEvidenceLimitExceeded): build_endpoint_path_evidence(req)

    def test_no_methodology_or_family_certificate_is_issued(self):
        before_s=len(structural_private._ISSUED); before_f=len(family_private._ISSUED)
        build_endpoint_path_evidence(request())
        self.assertEqual(before_s,len(structural_private._ISSUED)); self.assertEqual(before_f,len(family_private._ISSUED))
        self.assertEqual(7,len(structural_private._PRODUCERS)); self.assertEqual(0,len(family_private._PRODUCERS))

    def test_source_contains_no_dynamic_network_rank_indicator_or_trade_logic(self):
        path=support.SRC/"elliott_runtime"/"analysis"/"endpoint_path_evidence.py"; source=path.read_text(encoding="utf-8"); tree=ast.parse(source)
        imports={n.module or "" for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}|{a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names}
        calls={n.func.id for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
        self.assertTrue({"socket","urllib","requests","http","subprocess"}.isdisjoint(imports)); self.assertTrue({"eval","exec","compile","__import__"}.isdisjoint(calls))
        for forbidden in ("CertifiedStructuralInvalidity","certify_structural_invalidity","CertifiedValidatedInternalFamily","P005","P006","RSI","MACD","EWO","volume interpretation","bull trap","forecast","trade_signal","confidence","preferred","ranking"):
            self.assertNotIn(forbidden,source)

    def test_copy_retains_only_same_live_request_and_result_validation(self):
        req=request(); result=build_endpoint_path_evidence(req)
        self.assertIs(req,copy.copy(req)); self.assertIs(result,validate_endpoint_path_evidence_result(result))


if __name__ == "__main__": unittest.main()
