import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pickle
import unittest

import support
import elliott_methodology_kernel._structural_invalidity_certification as structural_private
import elliott_methodology_kernel._validated_internal_family_certification as family_private
from elliott_methodology_kernel import MethodologyKernel
from elliott_methodology_kernel.contracts import MarketType, SymbolIdentity, Timeframe
from elliott_methodology_kernel.p004 import P004_BEHAVIOR_ID, RuleCheckStatus
from elliott_runtime.analysis.candidate_generation import (
    CandidateGenerationConfig,
    CandidateGenerationRequest,
    CandidateHypothesisShape,
    CandidatePivotWindow,
    generate_candidate_hypotheses,
)
from elliott_runtime.analysis.competing_candidates import (
    CompetingCandidateSetRequest,
    build_competing_candidate_set,
)
from elliott_runtime.analysis.family_hypotheses import (
    FamilyEvaluationKind,
    FamilyHypothesisBridgeRequest,
    build_family_evaluation_hypotheses,
)
from elliott_runtime.analysis.family_internal_subdivisions import RequiredInternalShape
import elliott_runtime.analysis.normal_impulse_partial_evaluation as module
from elliott_runtime.analysis.normal_impulse_partial_evaluation import (
    NormalImpulseEvaluationHypothesis,
    NormalImpulseEvaluationSourceKind,
    NormalImpulseMethodologyDependency,
    NormalImpulsePartialEvaluationError,
    NormalImpulsePartialEvaluationLimitExceeded,
    NormalImpulsePartialEvaluationRequest,
    NormalImpulsePartialEvaluationState,
    evaluate_normal_impulse_partial_scope,
    validate_normal_impulse_partial_evaluation_result,
)
from elliott_runtime.analysis.recursive_child_family_evaluation import (
    ChildFamilyCoverageState,
    _SCOPE,
)
from elliott_runtime.market_data.geometric_pivots import (
    EqualExtremePolicy,
    GeometricPivotDiscoveryConfig,
    GeometricPivotDiscoveryMethod,
    GeometricPivotDiscoveryRequest,
    discover_geometric_pivots,
)
from elliott_runtime.market_data.ingestion import _normalize
from test_candidate_generation import geometry, market_observations, subject
from test_recursive_child_family_evaluation import child_result


def parent_bridge(*, many=False, mixed=False):
    data = market_observations(40 if many else 24)
    pivots = geometry(data)
    count = min(12, len(pivots.pivots)) if many else 6
    candidates = generate_candidate_hypotheses(CandidateGenerationRequest(
        "normal-impulse-parent-generation",
        "2026-09-04T18:00:00Z",
        subject("normal-impulse-parent"),
        data,
        pivots,
        CandidateGenerationConfig(
            count,
            6,
            0,
            10 if mixed else max(1, count - 5),
            (
                CandidateHypothesisShape.THREE_SEGMENT_HYPOTHESIS,
                CandidateHypothesisShape.FIVE_SEGMENT_HYPOTHESIS,
            ) if mixed else (CandidateHypothesisShape.FIVE_SEGMENT_HYPOTHESIS,),
            CandidatePivotWindow.EARLIEST,
        ),
        (),
        ("test:normal-impulse-parent",),
    ))
    competing = build_competing_candidate_set(CompetingCandidateSetRequest(
        "normal-impulse-parent-set", "normal-impulse-parent", candidates,
        ("test:normal-impulse-parent-set",),
    ))
    return build_family_evaluation_hypotheses(FamilyHypothesisBridgeRequest(
        "normal-impulse-parent-bridge", "2026-09-04T18:00:00Z", competing,
        tuple(FamilyEvaluationKind), ("test:normal-impulse-parent-bridge",),
    ), MethodologyKernel(support.PROTECTED_ROOT))


def equality_bridge(*, invert=False):
    highs = [11, 20, 11, 20, 12, 22, 13, 23, 14, 24, 15, 25]
    records = []
    for index, high in enumerate(highs):
        low = high - 1
        if invert:
            high, low = -low, -high
        middle = (high + low) / 2
        records.append({
            "timestamp": (datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(days=index)).isoformat(),
            "open": middle, "high": high, "low": low, "close": middle, "volume": 1,
        })
    data = _normalize(
        records, b"normal-impulse-equality", "test", "normal-impulse-equality",
        SymbolIdentity("TEST", MarketType.STOCK), Timeframe("1d", 86400),
    )
    config = GeometricPivotDiscoveryConfig(
        GeometricPivotDiscoveryMethod.WINDOWED_LOCAL_EXTREMA, 1, 1,
        EqualExtremePolicy.LAST, True,
    )
    pivots = discover_geometric_pivots(GeometricPivotDiscoveryRequest(
        "normal-impulse-equality-pivots", data, config, ("test:equality",),
    ))
    generated = generate_candidate_hypotheses(CandidateGenerationRequest(
        "normal-impulse-equality-generation", "2026-09-04T18:00:00Z",
        subject("normal-impulse-equality"), data, pivots,
        CandidateGenerationConfig(
            6, 6, 0, 1, (CandidateHypothesisShape.FIVE_SEGMENT_HYPOTHESIS,),
            CandidatePivotWindow.EARLIEST,
        ), (), ("test:equality",), pivots.pivots[:6],
    ))
    competing = build_competing_candidate_set(CompetingCandidateSetRequest(
        "normal-impulse-equality-set", "normal-impulse-equality", generated,
        ("test:equality",),
    ))
    return build_family_evaluation_hypotheses(FamilyHypothesisBridgeRequest(
        "normal-impulse-equality-bridge", "2026-09-04T18:00:00Z", competing,
        (), ("test:equality",),
    ), MethodologyKernel(support.PROTECTED_ROOT))


def request(source=None, cap=100):
    return NormalImpulsePartialEvaluationRequest(
        "normal-impulse-partial:test", "2026-09-04T18:00:00Z",
        source or parent_bridge(), cap, cap, cap, ("test:normal-impulse-partial",),
    )


def evaluate(source=None, cap=100):
    return evaluate_normal_impulse_partial_scope(
        request(source, cap), MethodologyKernel(support.PROTECTED_ROOT)
    )


class NormalImpulsePartialEvaluationTests(unittest.TestCase):
    def test_source_locked_boundary_constants_are_exact(self):
        self.assertEqual("PROJECT_ANALYSIS_INFRASTRUCTURE", module.ARTIFACT_CLASSIFICATION)
        self.assertEqual("SOURCE_DERIVED_EVALUATION_SCOPE", module.EVALUATION_SCOPE_CLASSIFICATION)
        self.assertEqual("HYPOTHESIS_ROLE_METADATA", module.ROLE_CLASSIFICATION)
        self.assertEqual("HYPOTHESIS_CONDITIONAL_STRUCTURAL_TEST", module.EXECUTION_CLASSIFICATION)
        self.assertTrue(module.FIVE_SEGMENTS_IS_NOT_NORMAL_IMPULSE)
        self.assertTrue(module.P004_PASS_IS_NOT_FAMILY_VALIDITY)
        self.assertTrue(module.P004_FAILURE_IS_HYPOTHESIS_LOCAL)

    def test_p004_protected_traceability_is_retained_unchanged(self):
        result = evaluate().evaluations[0].p004_result
        self.assertEqual((
            "docs/elliott/PATTERN_BRAIN.md#A-normal-impulse-rule-1",
            "docs/elliott/SOURCE_EVIDENCE_MAP.json#P004",
            "docs/elliott/MASTER_PROTOCOL.md#step-5",
        ), result.protected_sources)

    def test_only_exact_five_segment_candidates_create_hypotheses(self):
        result = evaluate()
        self.assertTrue(result.hypotheses)
        self.assertTrue(all(
            item.generated_candidate.candidate_shape
            is CandidateHypothesisShape.FIVE_SEGMENT_HYPOTHESIS
            for item in result.hypotheses
        ))
        self.assertFalse(any("THREE_SEGMENT" in item.hypothesis_id for item in result.hypotheses))

    def test_three_segment_candidates_cannot_create_normal_impulse_hypotheses(self):
        source = parent_bridge(mixed=True)
        three_count = sum(
            item.generated_candidate.candidate_shape is CandidateHypothesisShape.THREE_SEGMENT_HYPOTHESIS
            for item in source.candidate_evaluations
        )
        self.assertGreater(three_count, 0)
        self.assertEqual(
            sum(item.generated_candidate.candidate_shape is CandidateHypothesisShape.FIVE_SEGMENT_HYPOTHESIS for item in source.candidate_evaluations),
            len(evaluate(source).hypotheses),
        )

    def test_parent_bridge_candidate_and_competing_set_identities_are_retained(self):
        source = parent_bridge()
        result = evaluate(source)
        self.assertIs(source, result.request.source)
        for hypothesis in result.hypotheses:
            self.assertIs(source.competing_candidate_set, hypothesis.competing_candidate_set)
            self.assertTrue(any(
                hypothesis.generated_candidate is item.generated_candidate
                for item in source.candidate_evaluations
            ))
            self.assertIsNone(hypothesis.generated_child_evidence)
            self.assertIs(NormalImpulseEvaluationSourceKind.PARENT_FAMILY_BRIDGE, hypothesis.source_kind)

    def test_roles_one_through_five_are_exact_hypothesis_local_metadata(self):
        hypothesis = evaluate().hypotheses[0]
        candidate = hypothesis.generated_candidate
        self.assertEqual(("1", "2", "3", "4", "5"), tuple(x.component_role for x in hypothesis.role_bindings))
        for index, role in enumerate(hypothesis.role_bindings):
            self.assertIs(candidate.ordered_selected_pivots[index], role.start_boundary)
            self.assertIs(candidate.ordered_selected_pivots[index + 1], role.end_boundary)
            self.assertIs(hypothesis.five_slot_view.binding.ordered_children[index], role.child_subject)
            self.assertTrue(role.hypothesis_role_metadata)
            self.assertFalse(role.wave_validity_authority)

    def test_hypothesis_has_no_validity_completion_degree_or_rank_authority(self):
        for hypothesis in evaluate().hypotheses:
            self.assertTrue(hypothesis.hypothesis_only)
            self.assertFalse(any((
                hypothesis.family_validity_authority,
                hypothesis.wave_validity_authority,
                hypothesis.completion_authority,
                hypothesis.terminality_authority,
                hypothesis.degree_authority,
                hypothesis.ranking_authority,
            )))

    def test_p004_binding_uses_exact_wave1_origin_and_wave2_end_boundaries(self):
        evaluation = evaluate().evaluations[0]
        pivots = evaluation.hypothesis.generated_candidate.ordered_selected_pivots
        self.assertIs(pivots[0].observed_price, evaluation.p004_fact.wave1_origin_price)
        self.assertIs(pivots[2].observed_price, evaluation.p004_fact.wave2_end_price)
        self.assertEqual(P004_BEHAVIOR_ID, evaluation.p004_result.behavior_id)
        self.assertEqual((evaluation.p004_fact,), evaluation.bounded_request.manual_behavior_facts)

    def test_existing_p004_handles_rising_and_falling_satisfied_and_violated_cases(self):
        result = evaluate(parent_bridge(many=True))
        observed = {(item.p004_fact.direction.value, item.p004_result.status) for item in result.evaluations}
        observed.add((
            evaluate(equality_bridge(invert=True)).evaluations[0].p004_fact.direction.value,
            evaluate(equality_bridge(invert=True)).evaluations[0].p004_result.status,
        ))
        self.assertIn(("UP", RuleCheckStatus.RULE_VIOLATED), observed)
        self.assertIn(("UP", RuleCheckStatus.RULE_SATISFIED), observed)
        self.assertIn(("DOWN", RuleCheckStatus.RULE_VIOLATED), observed)
        self.assertIn(("DOWN", RuleCheckStatus.RULE_SATISFIED), observed)

    def test_existing_p004_equality_boundary_remains_satisfied(self):
        evaluation = evaluate(equality_bridge()).evaluations[0]
        self.assertEqual(evaluation.p004_fact.wave1_origin_price, evaluation.p004_fact.wave2_end_price)
        self.assertIs(RuleCheckStatus.RULE_SATISFIED, evaluation.p004_result.status)
        self.assertIs(
            NormalImpulsePartialEvaluationState.P004_SATISFIED_WITH_UNRESOLVED_METHODOLOGY_DEPENDENCIES,
            evaluation.state,
        )

    def test_genuine_p004_violation_uses_existing_certificate_and_is_hypothesis_local(self):
        source = parent_bridge()
        sibling_before = tuple(source.family_hypotheses)
        result = evaluate(source)
        violation = next(x for x in result.evaluations if x.p004_result.status is RuleCheckStatus.RULE_VIOLATED)
        self.assertIs(violation.p004_result, violation.structural_invalidity_certificate.origin)
        self.assertIn(violation.structural_invalidity_certificate, result.p004_certificates)
        self.assertEqual(sibling_before, source.family_hypotheses)
        self.assertFalse(violation.hypothesis.generated_candidate.elliott_validity_authority)
        self.assertEqual(
            {FamilyEvaluationKind.TRIANGLE, FamilyEvaluationKind.ENDING_DIAGONAL},
            {item.family_kind for item in source.family_hypotheses},
        )
        source._validated()

    def test_p004_satisfaction_stays_unresolved_with_all_dependencies_explicit(self):
        evaluation = next(
            x for x in evaluate(parent_bridge(many=True)).evaluations
            if x.p004_result.status is RuleCheckStatus.RULE_SATISFIED
        )
        self.assertEqual(tuple(NormalImpulseMethodologyDependency), evaluation.unresolved_dependencies)
        self.assertFalse(any((
            evaluation.family_validity_authority,
            evaluation.complete_methodology_review_authority,
            evaluation.requirement_satisfaction_authority,
        )))
        self.assertIsNone(evaluation.structural_invalidity_certificate)

    def test_motive_five_scope_is_partial_open_world_and_never_satisfied(self):
        state, compatible, unavailable, blockers, source_class = _SCOPE[
            RequiredInternalShape.MOTIVE_FIVE_FAMILY_REQUIRED
        ]
        self.assertIs(ChildFamilyCoverageState.PARTIAL_EXECUTABLE_FAMILY_COVERAGE, state)
        self.assertEqual((), compatible)
        self.assertEqual(("LEADING_DIAGONAL",), unavailable)
        self.assertIn("NORMAL_IMPULSE_P005_UNRESOLVED", blockers)
        self.assertIn("NORMAL_IMPULSE_P006_UNRESOLVED_CONFLICT", blockers)
        self.assertIn("LEADING_DIAGONAL_EXECUTION_UNAVAILABLE", blockers)
        self.assertEqual("SOURCE_DEFINITION", source_class)

    def test_recursive_child_motive_requirements_gain_only_partial_p004_scope(self):
        source = child_result()
        result = evaluate(source)
        self.assertTrue(result.hypotheses)
        for hypothesis in result.hypotheses:
            self.assertIs(source, hypothesis.source)
            self.assertIs(NormalImpulseEvaluationSourceKind.RECURSIVE_CHILD_CANDIDATE_GENERATION, hypothesis.source_kind)
            evidence = hypothesis.generated_child_evidence
            self.assertIs(RequiredInternalShape.MOTIVE_FIVE_FAMILY_REQUIRED, evidence.internal_requirement.required_internal_shape)
            self.assertIs(evidence.competing_candidate_set, hypothesis.competing_candidate_set)
            self.assertIs(evidence.candidate_generation_result.input_observations, hypothesis.generated_candidate.source_observations)
            self.assertFalse(evidence.requirement_satisfied)

    def test_recursive_scope_adds_no_grandchildren_p023_degree_or_timeframe_mapping(self):
        result = evaluate(child_result())
        source = Path(module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        self.assertFalse(any(name in source for name in ("P023Visibility", "grandchild", "lower_degree", "degree_assignment")))
        self.assertFalse(any(isinstance(node, (ast.Import, ast.ImportFrom)) and "finer_child" in ast.unparse(node) for node in ast.walk(tree)))
        self.assertTrue(all(not hasattr(item.hypothesis, "children") for item in result.evaluations))

    def test_resource_caps_fail_before_any_partial_result(self):
        with self.assertRaises(NormalImpulsePartialEvaluationLimitExceeded):
            evaluate(parent_bridge(many=True), cap=1)

    def test_mapping_duck_subclass_and_manual_hypothesis_are_rejected(self):
        with self.assertRaises(NormalImpulsePartialEvaluationError):
            request({"source": parent_bridge()})
        class Duck:
            pass
        with self.assertRaises(NormalImpulsePartialEvaluationError):
            request(Duck())
        with self.assertRaises(TypeError):
            class BadRequest(NormalImpulsePartialEvaluationRequest):
                pass
        with self.assertRaises(TypeError):
            NormalImpulseEvaluationHypothesis()

    def test_reconstructed_or_foreign_role_boundary_fails_closed(self):
        hypothesis = evaluate().hypotheses[0]
        role = hypothesis.role_bindings[0]
        object.__setattr__(role, "start_boundary", hypothesis.generated_candidate.ordered_selected_pivots[1])
        with self.assertRaises(NormalImpulsePartialEvaluationError):
            role._validated()

    def test_mutation_and_pickle_fail_closed(self):
        result = evaluate()
        with self.assertRaises(TypeError):
            pickle.dumps(result)
        object.__setattr__(result, "validated_normal_impulses", 1)
        with self.assertRaises(NormalImpulsePartialEvaluationError):
            validate_normal_impulse_partial_evaluation_result(result)

    def test_no_new_methodology_or_family_producer_is_created(self):
        before_structural = tuple(structural_private._PRODUCERS)
        before_family = tuple(family_private._PRODUCERS)
        before_issuances = len(family_private._ISSUED)
        result = evaluate(parent_bridge(many=True))
        self.assertEqual(before_structural, tuple(structural_private._PRODUCERS))
        self.assertEqual(before_family, tuple(family_private._PRODUCERS))
        self.assertEqual(before_issuances, len(family_private._ISSUED))
        self.assertEqual(0, result.validated_normal_impulses)
        self.assertEqual(0, result.validated_motive_families)

    def test_no_p005_p006_or_forbidden_feature_logic_is_present(self):
        source = Path(module.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        calls = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        self.assertNotIn("check_p004", calls)
        self.assertNotIn("eval", calls)
        self.assertNotIn("exec", calls)
        forbidden = ("fibonacci", "macd", "ewo", "volume interpretation", "forecast", "target price", "trade decision", "confidence", "probability")
        lowered = source.lower()
        self.assertFalse(any(token in lowered for token in forbidden))
        self.assertNotIn("rsi", {node.id.lower() for node in ast.walk(tree) if isinstance(node, ast.Name)})


if __name__ == "__main__":
    unittest.main()
