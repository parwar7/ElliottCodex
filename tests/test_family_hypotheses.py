import ast
import copy
from dataclasses import FrozenInstanceError
import inspect
import pickle
import unittest

import support
import elliott_methodology_kernel._structural_invalidity_certification as structural_private
import elliott_methodology_kernel._validated_internal_family_certification as family_private
from elliott_methodology_kernel import (
    BoundedManualChartFinalSummary,
    ManualCardinalityBehavior,
    MethodologyKernel,
)
from elliott_runtime.analysis.candidate_generation import CandidateHypothesisShape
from elliott_runtime.analysis.competing_candidates import (
    build_competing_candidate_set,
)
import elliott_runtime.analysis.family_hypotheses as family_module
from elliott_runtime.analysis.family_hypotheses import (
    ARTIFACT_CLASSIFICATION,
    CARDINALITY_MATCH_IS_NOT_FULL_FAMILY_VALIDITY,
    CHILD_HYPOTHESIS_CLASSIFICATION,
    EVALUATE_AS_IS_NOT_THIS_IS,
    EVALUATION_SCOPE_CLASSIFICATION,
    FAMILY_HYPOTHESIS_IS_NOT_CLASSIFICATION,
    FAN_OUT_ORDER_CLASSIFICATION,
    GEOMETRIC_PIVOT_IS_NOT_WAVE_ENDPOINT,
    TIMEFRAME_IS_NOT_DEGREE,
    FamilyEvaluationKind,
    FamilyHypothesisBridgeError,
    FamilyHypothesisBridgeRequest,
    FamilyHypothesisDiagnosticCode,
    build_family_evaluation_hypotheses,
)
from test_competing_candidates import generation, mixed_generation, set_request


ALL_FAMILIES = tuple(FamilyEvaluationKind)


def competing(*, generated=None):
    return build_competing_candidate_set(set_request(generated or generation()))


def request(candidate_set=None, families=ALL_FAMILIES, **changes):
    values = {
        "bridge_id": "family-bridge:test",
        "requested_at_utc": "2026-09-04T16:00:00Z",
        "competing_candidate_set": candidate_set or competing(),
        "allowed_family_kinds": families,
        "provenance_refs": ("family-bridge:test",),
    }
    values.update(changes)
    return FamilyHypothesisBridgeRequest(**values)


def bridge(candidate_set=None, families=ALL_FAMILIES):
    return build_family_evaluation_hypotheses(
        request(candidate_set, families),
        MethodologyKernel(support.PROTECTED_ROOT),
    )


class FamilyHypothesisBridgeTests(unittest.TestCase):
    def test_classifications_and_authority_boundaries_are_exact(self):
        self.assertEqual("PROJECT_ANALYSIS_INFRASTRUCTURE", ARTIFACT_CLASSIFICATION)
        self.assertEqual("SOURCE_DERIVED_EVALUATION_SCOPE", EVALUATION_SCOPE_CLASSIFICATION)
        self.assertEqual("CALLER_OR_GENERATOR_SUPPLIED_CHILD_HYPOTHESIS", CHILD_HYPOTHESIS_CLASSIFICATION)
        self.assertEqual("PROJECT_OPERATIONAL_POLICY", FAN_OUT_ORDER_CLASSIFICATION)
        self.assertEqual((True, True, True, True, True), (
            FAMILY_HYPOTHESIS_IS_NOT_CLASSIFICATION,
            EVALUATE_AS_IS_NOT_THIS_IS,
            CARDINALITY_MATCH_IS_NOT_FULL_FAMILY_VALIDITY,
            GEOMETRIC_PIVOT_IS_NOT_WAVE_ENDPOINT,
            TIMEFRAME_IS_NOT_DEGREE,
        ))

    def test_exact_competing_set_and_candidate_identities_are_retained(self):
        source = competing()
        result = bridge(source)
        self.assertIs(source, result.competing_candidate_set)
        self.assertEqual(len(source.ordered_candidates), len(result.candidate_evaluations))
        self.assertTrue(all(
            observed.generated_candidate is expected
            for observed, expected in zip(
                result.candidate_evaluations, source.ordered_candidates, strict=True
            )
        ))

    def test_three_segment_fans_out_only_to_zigzag_and_flat(self):
        result = bridge()
        for evaluation in result.candidate_evaluations:
            if evaluation.generated_candidate.candidate_shape is CandidateHypothesisShape.THREE_SEGMENT_HYPOTHESIS:
                self.assertEqual(
                    (FamilyEvaluationKind.SINGLE_ZIGZAG, FamilyEvaluationKind.FLAT),
                    tuple(item.family_kind for item in evaluation.family_hypotheses),
                )

    def test_five_segment_fans_out_only_to_triangle_and_ending_diagonal(self):
        result = bridge()
        for evaluation in result.candidate_evaluations:
            if evaluation.generated_candidate.candidate_shape is CandidateHypothesisShape.FIVE_SEGMENT_HYPOTHESIS:
                self.assertEqual(
                    (FamilyEvaluationKind.TRIANGLE, FamilyEvaluationKind.ENDING_DIAGONAL),
                    tuple(item.family_kind for item in evaluation.family_hypotheses),
                )

    def test_three_never_creates_triangle_or_ending_diagonal(self):
        result = bridge()
        forbidden = {FamilyEvaluationKind.TRIANGLE, FamilyEvaluationKind.ENDING_DIAGONAL}
        for evaluation in result.candidate_evaluations:
            if evaluation.generated_candidate.candidate_shape is CandidateHypothesisShape.THREE_SEGMENT_HYPOTHESIS:
                self.assertTrue(forbidden.isdisjoint(item.family_kind for item in evaluation.family_hypotheses))

    def test_five_never_creates_zigzag_flat_or_impulse(self):
        result = bridge()
        forbidden = {FamilyEvaluationKind.SINGLE_ZIGZAG, FamilyEvaluationKind.FLAT}
        for evaluation in result.candidate_evaluations:
            if evaluation.generated_candidate.candidate_shape is CandidateHypothesisShape.FIVE_SEGMENT_HYPOTHESIS:
                self.assertTrue(forbidden.isdisjoint(item.family_kind for item in evaluation.family_hypotheses))
        self.assertNotIn("NORMAL_IMPULSE", FamilyEvaluationKind.__members__)

    def test_allowed_scope_filters_without_selecting_a_winner(self):
        result = bridge(families=(FamilyEvaluationKind.FLAT, FamilyEvaluationKind.TRIANGLE))
        self.assertEqual(
            {FamilyEvaluationKind.FLAT, FamilyEvaluationKind.TRIANGLE},
            {item.family_kind for item in result.family_hypotheses},
        )
        self.assertFalse(any(hasattr(result, name) for name in ("winner", "preferred", "best_family", "rank")))

    def test_empty_allowed_scope_retains_every_candidate_with_zero_hypotheses(self):
        source = competing()
        result = bridge(source, ())
        self.assertEqual((), result.family_hypotheses)
        self.assertEqual(len(source.ordered_candidates), len(result.candidate_evaluations))
        self.assertTrue(all(not item.family_hypotheses for item in result.candidate_evaluations))
        self.assertIn(
            FamilyHypothesisDiagnosticCode.NO_COMPATIBLE_FAMILY_REQUESTED,
            tuple(item.code for item in result.diagnostics),
        )

    def test_proposed_child_subjects_are_deterministic_neutral_and_ordered(self):
        first = bridge()
        second = bridge()
        first_ids = [
            tuple(child.subject_id for child in item.ordered_child_subjects)
            for item in first.candidate_evaluations
        ]
        second_ids = [
            tuple(child.subject_id for child in item.ordered_child_subjects)
            for item in second.candidate_evaluations
        ]
        self.assertEqual(first_ids, second_ids)
        for evaluation in first.candidate_evaluations:
            count = evaluation.generated_candidate.candidate_shape.selected_pivot_count - 1
            self.assertEqual(count, len(evaluation.ordered_child_subjects))
            self.assertTrue(all(
                child.subject_id.endswith(f":proposed-child:{index + 1}")
                for index, child in enumerate(evaluation.ordered_child_subjects)
            ))
            self.assertFalse(any(label in child.subject_id for child in evaluation.ordered_child_subjects for label in (":A", ":B", ":C", ":W", ":X", ":Y")))

    def test_binding_preserves_exact_parent_child_identity_and_order_without_proof(self):
        result = bridge()
        for evaluation in result.candidate_evaluations:
            self.assertIs(evaluation.generated_candidate.subject, evaluation.child_binding.parent_subject)
            self.assertIs(evaluation.ordered_child_subjects, evaluation.child_binding.ordered_children)
            for hypothesis in evaluation.family_hypotheses:
                self.assertIs(evaluation.child_binding, hypothesis.child_binding)
                self.assertIs(evaluation.ordered_child_subjects, hypothesis.ordered_child_subjects)

    def test_each_family_creates_only_its_exact_existing_cardinality_fact(self):
        expected = {
            FamilyEvaluationKind.SINGLE_ZIGZAG: ManualCardinalityBehavior.SINGLE_ZIGZAG,
            FamilyEvaluationKind.FLAT: ManualCardinalityBehavior.FLAT,
            FamilyEvaluationKind.TRIANGLE: ManualCardinalityBehavior.TRIANGLE,
            FamilyEvaluationKind.ENDING_DIAGONAL: ManualCardinalityBehavior.ENDING_DIAGONAL,
        }
        for hypothesis in bridge().family_hypotheses:
            self.assertIs(expected[hypothesis.family_kind], hypothesis.manual_fact.behavior)
            self.assertEqual((hypothesis.manual_fact,), hypothesis.bounded_request.manual_behavior_facts)

    def test_existing_bounded_pipeline_is_reused_and_exact_results_retained(self):
        expected = {
            FamilyEvaluationKind.SINGLE_ZIGZAG: "P007_SINGLE_ZIGZAG_DIRECT_CHILD_CARDINALITY",
            FamilyEvaluationKind.FLAT: "P008_FLAT_DIRECT_CHILD_CARDINALITY",
            FamilyEvaluationKind.TRIANGLE: "P009_TRIANGLE_DIRECT_CHILD_CARDINALITY",
            FamilyEvaluationKind.ENDING_DIAGONAL: "ENDING_DIAGONAL_DIRECT_CHILD_CARDINALITY",
        }
        for hypothesis in bridge().family_hypotheses:
            result = hypothesis.bounded_result
            self.assertIs(hypothesis.parent_subject, result.subject)
            self.assertEqual(hypothesis.generated_candidate.candidate_id, result.candidate_id)
            self.assertEqual((expected[hypothesis.family_kind],), tuple(item.behavior_id for item in result.traceability))
            self.assertIs(hypothesis.manual_fact, result.traceability[0].manual_fact)
            self.assertIs(hypothesis.child_binding, result.manual_build_result.request.effective_child_binding)

    def test_matching_cardinality_is_only_current_supplied_scope_reviewed(self):
        result = bridge()
        self.assertEqual(result.family_hypotheses, result.reviewed_scope_hypotheses)
        self.assertEqual((), result.structurally_invalid_hypotheses)
        self.assertEqual((), result.unresolved_hypotheses)
        self.assertTrue(all(
            item.bounded_result.final_summary
            is BoundedManualChartFinalSummary.CURRENT_SUPPLIED_SCOPE_REVIEWED
            for item in result.family_hypotheses
        ))

    def test_multiple_family_hypotheses_coexist_independently(self):
        result = bridge()
        self.assertTrue(all(len(item.family_hypotheses) == 2 for item in result.candidate_evaluations))
        self.assertIn(
            FamilyHypothesisDiagnosticCode.MULTIPLE_FAMILIES_COEXIST,
            tuple(item.code for item in result.diagnostics),
        )

    def test_original_genuine_invalidity_remains_in_exact_neutral_candidate_ancestry(self):
        generated, certificate = mixed_generation(one_invalid=True)
        source = competing(generated=generated)
        result = bridge(source)
        candidate = result.candidate_evaluations[0].generated_candidate
        self.assertIs(source.ordered_candidates[0], candidate)
        self.assertIs(
            certificate,
            candidate.downstream_methodology_result.structural_invalidity_certificates[0],
        )
        self.assertEqual(2, len(result.family_hypotheses))
        self.assertTrue(all(
            item.bounded_result.final_summary
            is BoundedManualChartFinalSummary.CURRENT_SUPPLIED_SCOPE_REVIEWED
            for item in result.family_hypotheses
        ))
        self.assertIs(candidate, result.family_hypotheses[0].generated_candidate)

    def test_one_family_outcome_does_not_validate_or_mutate_siblings_or_candidate(self):
        source = competing()
        original_states = tuple(item.review_state for item in source.ordered_candidates)
        result = bridge(source)
        self.assertEqual(original_states, tuple(item.review_state for item in source.ordered_candidates))
        for evaluation in result.candidate_evaluations:
            self.assertTrue(all(item.generated_candidate is evaluation.generated_candidate for item in evaluation.family_hypotheses))
            self.assertTrue(all(item.family_validity_authority is False for item in evaluation.family_hypotheses))

    def test_hypothesis_authority_flags_never_strengthen_results(self):
        for hypothesis in bridge().family_hypotheses:
            self.assertEqual((True, False, False, False, False), (
                hypothesis.hypothesis_only,
                hypothesis.family_validity_authority,
                hypothesis.completion_authority,
                hypothesis.degree_authority,
                hypothesis.ranking_authority,
            ))

    def test_no_validated_family_certificate_or_producer_is_created(self):
        before = (len(family_private._PRODUCERS), len(family_private._ISSUED))
        result = bridge()
        after = (len(family_private._PRODUCERS), len(family_private._ISSUED))
        self.assertEqual((0, 0), before)
        self.assertEqual(before, after)
        self.assertFalse(any(
            "CertifiedValidatedInternalFamily" in type(getattr(item, name)).__name__
            for item in result.family_hypotheses
            for name in item.__dataclass_fields__
        ))

    def test_bridge_does_not_issue_structural_certificates(self):
        before = len(structural_private._ISSUED)
        result = bridge()
        self.assertEqual(before, len(structural_private._ISSUED))
        self.assertTrue(all(not item.bounded_result.structural_invalidity_certificates for item in result.family_hypotheses))

    def test_normal_impulse_leading_diagonal_and_combinations_are_unavailable(self):
        self.assertEqual(
            {"SINGLE_ZIGZAG", "FLAT", "TRIANGLE", "ENDING_DIAGONAL"},
            set(FamilyEvaluationKind.__members__),
        )
        source = inspect.getsource(family_module)
        for unsupported in ("WXY", "WXYXZ", "LEADING_DIAGONAL", "NORMAL_IMPULSE"):
            self.assertNotIn(f'FamilyEvaluationKind.{unsupported}', source)

    def test_no_p004_p003_p023_or_degree_fact_is_constructed(self):
        for hypothesis in bridge().family_hypotheses:
            self.assertEqual(1, len(hypothesis.bounded_request.manual_behavior_facts))
            self.assertIs(type(hypothesis.manual_fact), type(hypothesis.bounded_request.manual_behavior_facts[0]))
            supplied = tuple(
                item.behavior_id
                for item in hypothesis.bounded_result.methodology_coverage
                if item.state.value == "SUPPLIED_AND_EXECUTED"
            )
            self.assertEqual(1, len(supplied))

    def test_dataset_start_pivots_have_no_origin_or_endpoint_semantics(self):
        result = bridge()
        self.assertFalse(any(
            hasattr(item, name)
            for item in result.family_hypotheses
            for name in ("wave_origin", "cycle_origin", "degree", "wave_endpoint")
        ))

    def test_request_result_and_nested_membership_are_immutable_nonpickle(self):
        requested = request()
        result = build_family_evaluation_hypotheses(requested, MethodologyKernel(support.PROTECTED_ROOT))
        with self.assertRaises(FrozenInstanceError):
            requested.bridge_id = "changed"
        with self.assertRaises(FrozenInstanceError):
            result.bridge_id = "changed"
        with self.assertRaises(TypeError):
            type(result)(result)
        for value in (requested, result, result.family_hypotheses[0]):
            with self.assertRaises(TypeError):
                pickle.dumps(value)
        self.assertIs(result, copy.copy(result))
        self.assertIs(result, copy.deepcopy(result))

    def test_mapping_duck_subclass_and_wrong_kernel_are_rejected(self):
        exact = request()
        for value in ({"bridge_id": "x"}, type("Duck", (), {})()):
            with self.assertRaises(FamilyHypothesisBridgeError):
                build_family_evaluation_hypotheses(value, MethodologyKernel(support.PROTECTED_ROOT))
        with self.assertRaises(TypeError):
            type("RequestSubclass", (FamilyHypothesisBridgeRequest,), {})
        with self.assertRaises(FamilyHypothesisBridgeError):
            build_family_evaluation_hypotheses(exact, object())

    def test_duplicate_or_nonexact_family_scope_fails_closed(self):
        with self.assertRaises(FamilyHypothesisBridgeError):
            request(families=(FamilyEvaluationKind.FLAT, FamilyEvaluationKind.FLAT))
        with self.assertRaises(FamilyHypothesisBridgeError):
            request(families=("FLAT",))
        with self.assertRaises(FamilyHypothesisBridgeError):
            request(families=[FamilyEvaluationKind.FLAT])

    def test_low_level_request_set_hypothesis_and_fact_mutation_fail_closed(self):
        requested = request()
        object.__setattr__(requested, "bridge_id", "mutated")
        with self.assertRaises(FamilyHypothesisBridgeError):
            build_family_evaluation_hypotheses(requested, MethodologyKernel(support.PROTECTED_ROOT))
        result = bridge()
        hypothesis = result.family_hypotheses[0]
        object.__setattr__(hypothesis.manual_fact, "behavior", ManualCardinalityBehavior.TRIANGLE)
        with self.assertRaises(FamilyHypothesisBridgeError):
            copy.copy(result)

    def test_low_level_result_membership_and_child_mutation_fail_closed(self):
        result = bridge()
        object.__setattr__(result, "family_hypotheses", result.family_hypotheses[1:])
        with self.assertRaises(FamilyHypothesisBridgeError):
            copy.copy(result)
        result = bridge()
        child = result.family_hypotheses[0].ordered_child_subjects[0]
        object.__setattr__(child, "subject_id", "mutated")
        with self.assertRaises(FamilyHypothesisBridgeError):
            copy.copy(result)

    def test_result_has_no_ranking_confidence_family_truth_or_forecast_surface(self):
        result = bridge()
        forbidden = {
            "rank", "score", "confidence", "preferred", "alternative",
            "confirmed_family", "valid_family", "forecast", "target", "trade",
        }
        names = set(result.__dataclass_fields__)
        for hypothesis in result.family_hypotheses:
            names.update(hypothesis.__dataclass_fields__)
        self.assertTrue(forbidden.isdisjoint(names))

    def test_no_indicators_traps_fundamentals_forecast_trading_or_recursion(self):
        source = inspect.getsource(family_module).lower()
        for forbidden in (
            "rsi", "macd", "ewo", "bull_trap", "bear_trap", "fundamental",
            "price_target", "trade_entry", "recursive_family", "confidence_score",
        ):
            self.assertNotIn(forbidden, source)

    def test_no_direct_validator_certifier_dynamic_import_network_process_or_callable_injection(self):
        path = support.SRC / "elliott_runtime" / "analysis" / "family_hypotheses.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(item.name for item in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module or "")
        self.assertTrue({"socket", "urllib", "requests", "http", "subprocess", "importlib"}.isdisjoint(imports))
        self.assertNotIn("check_p007", source)
        self.assertNotIn("check_p008", source)
        self.assertNotIn("check_p009", source)
        self.assertNotIn("check_ending_diagonal", source)
        self.assertNotIn("certify_", source)
        self.assertFalse(any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in {"eval", "exec", "compile", "__import__"}
            for node in ast.walk(tree)
        ))
        fields = FamilyHypothesisBridgeRequest.__dataclass_fields__
        self.assertFalse(any("call" in name or "func" in name or "hook" in name for name in fields))

    def test_diagnostics_use_only_neutral_scope_language(self):
        result = bridge()
        codes = tuple(item.code for item in result.diagnostics)
        self.assertIn(FamilyHypothesisDiagnosticCode.FAMILY_HYPOTHESES_CREATED, codes)
        self.assertIn(FamilyHypothesisDiagnosticCode.CARDINALITY_SCOPE_REVIEWED, codes)
        text = " ".join(item.detail.lower() for item in result.diagnostics)
        for forbidden in ("valid family", "confirmed family", "best", "preferred", "probability"):
            self.assertNotIn(forbidden, text)

    def test_methodology_and_registries_remain_exact(self):
        observed = set()
        root = support.SRC / "elliott_methodology_kernel"
        for path in root.glob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, (ast.Assign, ast.AnnAssign)):
                    targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
                    if any(isinstance(item, ast.Name) and item.id.endswith(("BEHAVIOR_ID", "BEHAVIOR")) for item in targets) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        observed.add(node.value.value)
        self.assertEqual(10, len(observed))
        self.assertEqual(7, len(structural_private._PRODUCERS))
        self.assertEqual(0, len(family_private._PRODUCERS))
        self.assertEqual(0, len(family_private._ISSUED))

    def test_legacy_analyze_remains_not_implemented(self):
        kernel = MethodologyKernel(support.PROTECTED_ROOT)
        source = inspect.getsource(kernel.analyze)
        self.assertIn("KernelStatus.NOT_IMPLEMENTED", source)


if __name__ == "__main__":
    unittest.main()
