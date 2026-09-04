import ast
import copy
import pickle
import unittest

import support
import elliott_methodology_kernel._structural_invalidity_certification as structural_private
import elliott_methodology_kernel._validated_internal_family_certification as family_private
from elliott_runtime.analysis.endpoint_path_evidence import (
    ENDPOINT_AUTHORITY_CLASS,
    EndpointPathEvidenceRequest,
    ObservedComponentDirection,
    build_endpoint_path_evidence,
)
from elliott_runtime.analysis.family_hypotheses import FamilyEvaluationKind
from elliott_runtime.analysis.flat_subtype_hypotheses import (
    GENERIC_FLAT_IS_NOT_INVALIDATED_BY_SUBTYPE_RESULTS,
    HYPOTHESIS_BOUND_ENDPOINT_IS_NOT_ORTHODOX_ENDPOINT,
    IRREGULAR_EXPANDED_ALIAS_DECISION,
    SUBTYPE_HYPOTHESIS_IS_NOT_SUBTYPE_CLASSIFICATION,
    TAXONOMY_COMPLETENESS,
    FlatSubtypeEvaluationHypothesis,
    FlatSubtypeEvaluationKind,
    FlatSubtypeHypothesisError,
    FlatSubtypeHypothesisLimitExceeded,
    FlatSubtypeHypothesisRequest,
    FlatSubtypeSourceKind,
    build_flat_subtype_hypotheses,
    validate_flat_subtype_hypothesis_result,
)
from test_family_hypotheses import bridge
from test_recursive_child_family_evaluation import evaluate as child_family_evaluate


def endpoint_result(hypothesis, suffix="parent"):
    return build_endpoint_path_evidence(
        EndpointPathEvidenceRequest(
            f"flat-subtype:endpoint:{suffix}:{hypothesis.hypothesis_id}",
            hypothesis,
            hypothesis.generated_candidate.source_observations,
            100_000,
            ("test:flat-subtype-endpoint",),
        )
    )


def parent_source():
    return bridge(families=(FamilyEvaluationKind.FLAT,))


def subtype_request(source=None, **changes):
    if source is None:
        source = parent_source()
    flats = tuple(
        item for item in source.family_hypotheses
        if item.family_kind is FamilyEvaluationKind.FLAT
    )
    values = {
        "request_id": "flat-subtype:test",
        "family_source": source,
        "endpoint_evidence_results": tuple(endpoint_result(item) for item in flats),
        "max_flat_hypotheses_processed": 100,
        "max_subtypes_per_flat": 3,
        "max_total_flat_subtype_hypotheses": 300,
        "provenance_refs": ("test:flat-subtype",),
    }
    values.update(changes)
    return FlatSubtypeHypothesisRequest(**values)


class FlatSubtypeHypothesisTests(unittest.TestCase):
    def test_locked_taxonomy_and_alias_decisions_are_exact(self):
        self.assertEqual(
            ("REGULAR_FLAT", "EXPANDED_FLAT", "RUNNING_FLAT"),
            tuple(item.value for item in FlatSubtypeEvaluationKind),
        )
        self.assertEqual(
            "IRREGULAR_IS_HISTORICAL_ALIAS_OF_EXPANDED",
            IRREGULAR_EXPANDED_ALIAS_DECISION,
        )
        self.assertEqual("KNOWN_SUBTYPES_NON_EXHAUSTIVE", TAXONOMY_COMPLETENESS)

    def test_parent_flat_fans_out_deterministically_without_selection(self):
        request = subtype_request()
        result = build_flat_subtype_hypotheses(request)
        self.assertIs(request, result.request)
        self.assertIs(FlatSubtypeSourceKind.PARENT_FAMILY_HYPOTHESES, result.source_kind)
        self.assertEqual(
            tuple(FlatSubtypeEvaluationKind) * len(result.flat_family_hypotheses),
            tuple(item.subtype_kind for item in result.subtype_hypotheses),
        )
        self.assertEqual(("IRREGULAR_FLAT",), result.subtype_hypotheses[1].aliases)
        self.assertTrue(all(item.aliases == () for item in (result.subtype_hypotheses[0], result.subtype_hypotheses[2])))

    def test_exact_flat_ancestry_and_endpoint_evidence_are_retained(self):
        request = subtype_request()
        result = build_flat_subtype_hypotheses(request)
        for index, flat in enumerate(result.flat_family_hypotheses):
            evidence = request.endpoint_evidence_results[index]
            for item in result.subtype_hypotheses[index * 3 : index * 3 + 3]:
                self.assertIs(request.family_source, item.family_source)
                self.assertIs(flat, item.flat_family_hypothesis)
                self.assertIs(evidence, item.endpoint_evidence)
                self.assertIs(flat.generated_candidate.subject, item.flat_family_hypothesis.parent_subject)

    def test_a_start_a_end_b_end_c_end_roles_preserve_exact_identity(self):
        item = build_flat_subtype_hypotheses(subtype_request()).subtype_hypotheses[0]
        bindings = item.endpoint_evidence.component_role_bindings
        endpoints = item.endpoint_evidence.component_endpoint_evidence
        self.assertEqual(("A", "B", "C"), tuple(x.component_role for x in bindings))
        self.assertIs(bindings[0].start_boundary, item.a_start)
        self.assertIs(endpoints[0].boundary_pivot, item.a_end)
        self.assertIs(endpoints[1].boundary_pivot, item.b_end)
        self.assertIs(endpoints[2].boundary_pivot, item.c_end)
        self.assertEqual(ENDPOINT_AUTHORITY_CLASS, item.endpoint_authority_class)

    def test_a_direction_is_only_exact_endpoint_arithmetic(self):
        item = build_flat_subtype_hypotheses(subtype_request()).subtype_hypotheses[0]
        start = item.a_start.observed_price
        end = item.a_end.observed_price
        expected = (
            ObservedComponentDirection.UP
            if end > start
            else ObservedComponentDirection.DOWN
            if end < start
            else ObservedComponentDirection.EQUAL
        )
        self.assertIs(expected, item.a_direction)
        self.assertFalse(hasattr(item, "elliott_direction"))

    def test_every_authority_flag_remains_false(self):
        result = build_flat_subtype_hypotheses(subtype_request())
        self.assertTrue(SUBTYPE_HYPOTHESIS_IS_NOT_SUBTYPE_CLASSIFICATION)
        self.assertTrue(GENERIC_FLAT_IS_NOT_INVALIDATED_BY_SUBTYPE_RESULTS)
        self.assertTrue(HYPOTHESIS_BOUND_ENDPOINT_IS_NOT_ORTHODOX_ENDPOINT)
        self.assertFalse(result.exhaustive_taxonomy_authority)
        self.assertFalse(result.subtype_classification_authority)
        self.assertFalse(result.family_validity_authority)
        self.assertFalse(result.ranking_authority)
        for item in result.subtype_hypotheses:
            self.assertTrue(item.hypothesis_only)
            self.assertFalse(any((item.subtype_classification_authority, item.family_validity_authority, item.wave_validity_authority, item.completion_authority, item.degree_authority, item.ranking_authority)))

    def test_no_automatic_subtype_choice_or_geometry_rule_result_exists(self):
        result = build_flat_subtype_hypotheses(subtype_request())
        self.assertEqual(len(result.flat_family_hypotheses) * 3, len(result.subtype_hypotheses))
        for forbidden in ("selected_subtype", "preferred_subtype", "rank", "confidence", "structural_invalidity", "certificate", "geometry_status"):
            self.assertFalse(hasattr(result, forbidden))
            self.assertTrue(all(not hasattr(item, forbidden) for item in result.subtype_hypotheses))
        self.assertIn("NO_ENDPOINT_RULE_EXECUTION", result.diagnostics)

    def test_non_flat_family_hypotheses_are_not_promoted(self):
        source = bridge(families=(FamilyEvaluationKind.SINGLE_ZIGZAG,))
        request = subtype_request(source=source, endpoint_evidence_results=())
        result = build_flat_subtype_hypotheses(request)
        self.assertEqual((), result.flat_family_hypotheses)
        self.assertEqual((), result.subtype_hypotheses)

    def test_recursive_child_flat_hypotheses_use_same_subtype_system(self):
        source = child_family_evaluate()
        flats = tuple(item for item in source.family_hypotheses if item.family_kind is FamilyEvaluationKind.FLAT)
        self.assertTrue(flats)
        request = subtype_request(
            source=source,
            endpoint_evidence_results=tuple(endpoint_result(item, "child") for item in flats),
            max_flat_hypotheses_processed=len(flats),
            max_total_flat_subtype_hypotheses=len(flats) * 3,
        )
        result = build_flat_subtype_hypotheses(request)
        self.assertIs(FlatSubtypeSourceKind.RECURSIVE_CHILD_FAMILY_HYPOTHESES, result.source_kind)
        self.assertEqual(len(flats) * 3, len(result.subtype_hypotheses))
        self.assertTrue(all(item.family_source is source for item in result.subtype_hypotheses))

    def test_endpoint_evidence_must_match_every_flat_exactly_and_in_order(self):
        source = parent_source()
        evidence = subtype_request(source=source).endpoint_evidence_results
        with self.assertRaises(FlatSubtypeHypothesisError):
            subtype_request(source=source, endpoint_evidence_results=())
        with self.assertRaises(FlatSubtypeHypothesisError):
            subtype_request(source=source, endpoint_evidence_results=evidence + evidence)

    def test_exact_source_result_mapping_duck_and_subclasses_are_rejected(self):
        with self.assertRaises(FlatSubtypeHypothesisError):
            FlatSubtypeHypothesisRequest(
                "bad", {}, (), 1, 1, 1, ("bad",)
            )
        class Duck:
            family_hypotheses = ()
        with self.assertRaises(FlatSubtypeHypothesisError):
            FlatSubtypeHypothesisRequest(
                "bad", Duck(), (), 1, 1, 1, ("bad",)
            )
        with self.assertRaises(TypeError):
            class RequestSubclass(FlatSubtypeHypothesisRequest):
                pass
        with self.assertRaises(TypeError):
            class HypothesisSubclass(FlatSubtypeEvaluationHypothesis):
                pass

    def test_factory_only_hypothesis_and_result_reject_reconstruction(self):
        with self.assertRaises(TypeError):
            FlatSubtypeEvaluationHypothesis()
        with self.assertRaises(FlatSubtypeHypothesisError):
            validate_flat_subtype_hypothesis_result({})

    def test_request_and_issued_object_mutation_fail_closed(self):
        request = subtype_request()
        result = build_flat_subtype_hypotheses(request)
        object.__setattr__(result.subtype_hypotheses[0], "hypothesis_id", "changed")
        with self.assertRaises(FlatSubtypeHypothesisError):
            validate_flat_subtype_hypothesis_result(result)
        request = subtype_request()
        result = build_flat_subtype_hypotheses(request)
        object.__setattr__(request, "request_id", "changed")
        with self.assertRaises(FlatSubtypeHypothesisError):
            validate_flat_subtype_hypothesis_result(result)

    def test_copy_is_identity_and_pickle_cannot_restore_authority(self):
        request = subtype_request()
        result = build_flat_subtype_hypotheses(request)
        item = result.subtype_hypotheses[0]
        self.assertIs(request, copy.copy(request))
        self.assertIs(item, copy.copy(item))
        self.assertIs(result, copy.copy(result))
        for value in (request, item, result):
            with self.assertRaises(TypeError):
                pickle.dumps(value)

    def test_preflight_caps_fail_before_partial_result(self):
        request = subtype_request(max_subtypes_per_flat=2)
        with self.assertRaises(FlatSubtypeHypothesisLimitExceeded):
            build_flat_subtype_hypotheses(request)
        request = subtype_request(max_total_flat_subtype_hypotheses=2)
        with self.assertRaises(FlatSubtypeHypothesisLimitExceeded):
            build_flat_subtype_hypotheses(request)

    def test_no_methodology_or_family_certificate_is_issued(self):
        structural_before = len(structural_private._ISSUED)
        family_before = len(family_private._ISSUED)
        build_flat_subtype_hypotheses(subtype_request())
        self.assertEqual(structural_before, len(structural_private._ISSUED))
        self.assertEqual(family_before, len(family_private._ISSUED))
        self.assertEqual(7, len(structural_private._PRODUCERS))
        self.assertEqual(0, len(family_private._PRODUCERS))

    def test_runtime_source_has_no_hidden_methodology_network_or_forbidden_features(self):
        path = support.SRC / "elliott_runtime" / "analysis" / "flat_subtype_hypotheses.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        imports = {
            node.module or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
        } | {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        calls = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertTrue({"socket", "urllib", "requests", "http", "subprocess"}.isdisjoint(imports))
        self.assertTrue({"eval", "exec", "compile", "__import__"}.isdisjoint(calls))
        for forbidden in ("certify_structural_invalidity", "CertifiedValidatedInternalFamily", "P005", "P006", "MACD", "EWO", "Fibonacci", "trade_signal", "probability"):
            self.assertNotIn(forbidden, source)
        self.assertNotRegex(source, r"\bRSI\b")

    def test_zero_direction_is_transportable_but_carries_no_rule_semantics(self):
        self.assertIn(ObservedComponentDirection.EQUAL, tuple(ObservedComponentDirection))
        result = build_flat_subtype_hypotheses(subtype_request())
        self.assertFalse(any(hasattr(item, "zero_direction_subtype") for item in result.subtype_hypotheses))
        self.assertIn("NO_ENDPOINT_RULE_EXECUTION", result.diagnostics)


if __name__ == "__main__":
    unittest.main()
