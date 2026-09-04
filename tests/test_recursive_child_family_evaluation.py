import ast
from dataclasses import FrozenInstanceError
import inspect
import unittest

import support
import elliott_methodology_kernel._validated_internal_family_certification as family_private
from elliott_methodology_kernel import MethodologyKernel
from elliott_runtime.analysis.family_hypotheses import FamilyEvaluationKind
from elliott_runtime.analysis.family_internal_subdivisions import RequiredInternalShape
from elliott_runtime.analysis.recursive_child_candidate_generation import (
    ChildCandidateGenerationConfig,
    RecursiveChildCandidateGenerationRequest,
    generate_child_candidate_evidence,
)
import elliott_runtime.analysis.recursive_child_family_evaluation as module
from elliott_runtime.analysis.recursive_child_family_evaluation import (
    ChildCandidateFamilyEvaluationState,
    ChildFamilyCoverageState,
    ChildFamilyEvaluationConfig,
    RecursiveChildFamilyEvaluationError,
    RecursiveChildFamilyEvaluationLimitExceeded,
    RecursiveChildFamilyEvaluationRequest,
    evaluate_recursive_child_family_hypotheses,
)
from test_recursive_child_candidate_generation import SHAPES, upstream


def child_result():
    source = upstream()
    return generate_child_candidate_evidence(RecursiveChildCandidateGenerationRequest(
        "child-family:source", "2026-09-04T00:00:00Z", source,
        ChildCandidateGenerationConfig(20, 20, 8, 6, 1, 12, 100, SHAPES),
        ("test:child-family-source",),
    ))


def config(**changes):
    values = dict(
        allowed_family_kinds=tuple(FamilyEvaluationKind),
        max_requirements_processed=20,
        max_child_candidate_sets_processed=20,
        max_child_candidates_processed=100,
        max_family_hypotheses_per_child_candidate=3,
        max_total_child_family_hypotheses=200,
        max_total_methodology_evaluations=200,
    )
    values.update(changes)
    return ChildFamilyEvaluationConfig(**values)


def request(source=None, configured=None):
    return RecursiveChildFamilyEvaluationRequest(
        "child-family:test", "2026-09-04T00:00:00Z", source or child_result(),
        configured or config(), ("test:child-family",),
    )


def evaluate(source=None, configured=None):
    return evaluate_recursive_child_family_hypotheses(
        request(source, configured), MethodologyKernel(support.PROTECTED_ROOT)
    )


class RecursiveChildFamilyEvaluationTests(unittest.TestCase):
    def test_boundary_constants_are_exact(self):
        self.assertEqual("PROJECT_ANALYSIS_INFRASTRUCTURE", module.ARTIFACT_CLASSIFICATION)
        self.assertEqual("SOURCE_DERIVED_EVALUATION_SCOPE", module.SCOPE_CLASSIFICATION)
        self.assertEqual("CALLER_SUPPLIED_OPERATIONAL_BOUND", module.BOUND_CLASSIFICATION)
        self.assertEqual(1, module.EXACT_CHILD_FAMILY_EVALUATION_LEVELS)
        self.assertEqual((True, True, True, True), (
            module.FAMILY_HYPOTHESIS_IS_NOT_FAMILY_CLASSIFICATION,
            module.INTERNAL_REQUIREMENT_IS_NOT_SATISFIED,
            module.ALL_EXECUTABLE_HYPOTHESES_INVALID_IS_NOT_CLOSED_WORLD_PROOF,
            module.TIMEFRAME_IS_NOT_DEGREE,
        ))

    def test_exact_ancestry_and_bridge_delegation_are_preserved(self):
        source = child_result()
        result = evaluate(source)
        self.assertIs(source, result.request.child_candidate_generation_result)
        self.assertEqual(len(source.generated_child_evidence), len(result.child_evaluations))
        for evidence, evaluation, scope in zip(source.generated_child_evidence, result.child_evaluations, result.requirement_scopes, strict=True):
            self.assertIs(evidence, evaluation.generated_child_evidence)
            self.assertIs(evidence.internal_requirement, scope.internal_requirement)
            if evaluation.family_hypothesis_result:
                self.assertIs(evidence.competing_candidate_set, evaluation.family_hypothesis_result.competing_candidate_set)
                self.assertTrue(all(h.generated_candidate in evidence.competing_candidate_set.ordered_candidates for h in evaluation.family_hypothesis_result.family_hypotheses))

    def test_source_safe_requirement_matrix_is_exact_and_non_exhaustive(self):
        result = evaluate()
        expected = {
            RequiredInternalShape.MOTIVE_FIVE_FAMILY_REQUIRED: (ChildFamilyCoverageState.NO_EXECUTABLE_FAMILY_COVERAGE, ()),
            RequiredInternalShape.CORRECTIVE_THREE_FAMILY_REQUIRED: (ChildFamilyCoverageState.PARTIAL_EXECUTABLE_FAMILY_COVERAGE, (FamilyEvaluationKind.SINGLE_ZIGZAG, FamilyEvaluationKind.FLAT)),
            RequiredInternalShape.CORRECTIVE_FAMILY_REQUIRED: (ChildFamilyCoverageState.PARTIAL_EXECUTABLE_FAMILY_COVERAGE, (FamilyEvaluationKind.SINGLE_ZIGZAG, FamilyEvaluationKind.FLAT, FamilyEvaluationKind.TRIANGLE)),
        }
        for scope in result.requirement_scopes:
            state, kinds = expected[scope.internal_requirement.required_internal_shape]
            self.assertIs(state, scope.coverage_state)
            self.assertEqual(kinds, scope.compatible_executable_family_kinds)
            self.assertFalse(scope.family_validity_authority)
            self.assertFalse(scope.requirement_satisfaction_authority)

    def test_three_wave_compatibility_remains_unresolved(self):
        source = child_result()
        # The ordinary upstream fixture supplies zigzag/flat; inspect the locked table directly
        row = module._SCOPE[RequiredInternalShape.THREE_WAVE_STRUCTURE_REQUIRED]
        self.assertIs(ChildFamilyCoverageState.UNRESOLVED_COMPATIBILITY, row[0])
        self.assertEqual((), row[1])
        self.assertEqual("UNRESOLVED", row[4])

    def test_neutral_shape_filters_via_existing_bridge_without_family_inference(self):
        result = evaluate()
        for evaluation in result.child_evaluations:
            bridge = evaluation.family_hypothesis_result
            if bridge is None:
                continue
            for candidate_evaluation in bridge.candidate_evaluations:
                shape = candidate_evaluation.generated_candidate.candidate_shape.value
                kinds = tuple(h.family_kind for h in candidate_evaluation.family_hypotheses)
                if shape == "THREE_SEGMENT_HYPOTHESIS":
                    self.assertTrue(set(kinds) <= {FamilyEvaluationKind.SINGLE_ZIGZAG, FamilyEvaluationKind.FLAT})
                else:
                    self.assertTrue(set(kinds) <= {FamilyEvaluationKind.TRIANGLE})

    def test_evaluation_never_satisfies_requirement_or_issues_family_authority(self):
        before_producers = tuple(family_private._PRODUCERS)
        before_issuances = len(family_private._ISSUED)
        result = evaluate()
        self.assertTrue(all(not item.requirement_satisfied and not item.family_validity_authority for item in result.child_evaluations))
        self.assertTrue(all(not h.family_validity_authority for h in result.family_hypotheses))
        self.assertEqual(before_producers, tuple(family_private._PRODUCERS))
        self.assertEqual(before_issuances, len(family_private._ISSUED))

    def test_caller_scope_can_reduce_but_not_expand_source_scope(self):
        result = evaluate(configured=config(allowed_family_kinds=(FamilyEvaluationKind.FLAT,)))
        self.assertTrue(all(h.family_kind is FamilyEvaluationKind.FLAT for h in result.family_hypotheses))
        empty = evaluate(configured=config(allowed_family_kinds=(FamilyEvaluationKind.ENDING_DIAGONAL,)))
        self.assertEqual((), empty.family_hypotheses)
        self.assertTrue(all(s.coverage_state is ChildFamilyCoverageState.NO_EXECUTABLE_FAMILY_COVERAGE for s in empty.requirement_scopes))
        self.assertTrue(all(
            item.evaluation_state is ChildCandidateFamilyEvaluationState.NO_EXECUTABLE_COMPATIBLE_CHILD_FAMILY_HYPOTHESIS
            for item in empty.child_evaluations
        ))

    def test_evaluation_state_is_open_world_and_never_requirement_validity(self):
        result = evaluate()
        self.assertTrue(all(item.evaluation_state in {
            ChildCandidateFamilyEvaluationState.EXECUTABLE_CHILD_FAMILY_HYPOTHESES_RETAINED,
            ChildCandidateFamilyEvaluationState.NO_EXECUTABLE_COMPATIBLE_CHILD_FAMILY_HYPOTHESIS,
        } for item in result.child_evaluations))
        self.assertNotIn("VALID", " ".join(item.value for item in ChildCandidateFamilyEvaluationState))
        self.assertTrue(module.ALL_EXECUTABLE_HYPOTHESES_INVALID_IS_NOT_CLOSED_WORLD_PROOF)

    def test_all_resource_bounds_fail_before_bridge_materialization(self):
        source = child_result()
        limits = (
            dict(max_requirements_processed=1), dict(max_child_candidate_sets_processed=1),
            dict(max_child_candidates_processed=1), dict(max_family_hypotheses_per_child_candidate=1),
            dict(max_total_child_family_hypotheses=1), dict(max_total_methodology_evaluations=1),
        )
        for change in limits:
            with self.subTest(change=change), self.assertRaises(RecursiveChildFamilyEvaluationLimitExceeded):
                evaluate(source, config(**change))

    def test_exact_types_immutability_and_no_serialized_lookalikes(self):
        source = child_result()
        with self.assertRaises(RecursiveChildFamilyEvaluationError):
            evaluate_recursive_child_family_hypotheses({"source": source}, MethodologyKernel(support.PROTECTED_ROOT))
        with self.assertRaises(FrozenInstanceError):
            config().max_requirements_processed = 1
        with self.assertRaises(TypeError):
            class Bad(RecursiveChildFamilyEvaluationRequest):
                pass

    def test_no_ranking_degree_visibility_recursion_or_closed_world_fields(self):
        result = evaluate()
        forbidden = ("preferred", "rank", "confidence", "degree", "visible", "terminal", "satisfied", "valid_family", "grandchild")
        fields = set(result.__dataclass_fields__)
        self.assertFalse(any(any(word in name.lower() for word in forbidden) for name in fields))
        self.assertFalse(hasattr(result, "winning_family"))

    def test_deterministic_order_and_ids(self):
        first, second = evaluate(), evaluate()
        self.assertEqual([h.hypothesis_id for h in first.family_hypotheses], [h.hypothesis_id for h in second.family_hypotheses])
        self.assertEqual([h.family_kind for h in first.family_hypotheses], [h.family_kind for h in second.family_hypotheses])

    def test_module_has_no_network_process_indicator_or_trading_capability(self):
        tree = ast.parse(inspect.getsource(module))
        imports = {node.names[0].name.split(".")[0] for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)) and node.names}
        self.assertTrue(imports.isdisjoint({"socket", "urllib", "requests", "http", "subprocess", "yfinance", "selenium"}))
        names = {node.id.lower() for node in ast.walk(tree) if isinstance(node, ast.Name)}
        names.update(node.attr.lower() for node in ast.walk(tree) if isinstance(node, ast.Attribute))
        self.assertTrue(names.isdisjoint({"rsi", "macd", "ewo", "fibonacci", "bull_trap", "bear_trap", "trade_order"}))


if __name__ == "__main__":
    unittest.main()
