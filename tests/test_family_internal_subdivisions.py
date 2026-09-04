import ast
import copy
from dataclasses import FrozenInstanceError
import inspect
import pickle
import unittest

import support
import elliott_methodology_kernel._validated_internal_family_certification as family_private
from elliott_methodology_kernel import (
    AnalysisResolutionState,
    BoundedRecursiveAnalysisNode,
    BoundedRecursiveAnalysisResolution,
    CandidateScope,
    ImpulseDirection,
    MethodologyKernel,
    OperationalAggregationState,
    P004Input,
    P023VisibilityInput,
    P023VisibilityState,
    certify_structural_invalidity,
    check_p004,
    evaluate_p023_visibility_for_subject,
)
import elliott_runtime.analysis.family_internal_subdivisions as internal_module
from elliott_runtime.analysis.family_hypotheses import FamilyEvaluationKind
from elliott_runtime.analysis.family_internal_subdivisions import (
    ARTIFACT_CLASSIFICATION,
    CHILD_EVIDENCE_CLASSIFICATION,
    INTERNAL_FAMILY_PROOF_BLOCKED_BY_NO_SOURCE_DERIVED_BASE_CASE,
    INTERNAL_REQUIREMENT_IS_NOT_INTERNAL_PROOF,
    RECURSIVE_REVIEW_IS_NOT_ELLIOTT_TERMINALITY,
    REQUIREMENT_AUTHORITY_CLASSIFICATION,
    REVIEWED_CHILD_IS_NOT_VALIDATED_FAMILY,
    SOURCE_DERIVED_BASE_CASE_NOT_FOUND,
    SUMMARY_CLASSIFICATION,
    TIMEFRAME_IS_NOT_DEGREE,
    FamilyChildCandidateEvidence,
    FamilyInternalDiagnosticCode,
    FamilyInternalOperationalSummary,
    FamilyInternalSubdivisionError,
    FamilyInternalSubdivisionEvaluationRequest,
    FamilyInternalSubdivisionEvaluationResult,
    InternalRequirementStatus,
    RequiredInternalShape,
    evaluate_family_internal_subdivisions,
)
from test_family_hypotheses import bridge


def request(source=None, evidence=(), **changes):
    values = {
        "evaluation_id": "internal:test",
        "family_hypothesis_result": source or bridge(),
        "child_evidence": evidence,
        "provenance_refs": ("internal:test",),
    }
    values.update(changes)
    return FamilyInternalSubdivisionEvaluationRequest(**values)


def evaluate(source=None, evidence=()):
    return evaluate_family_internal_subdivisions(request(source, evidence))


def leaf(subject, state, *, certificate=None, visibility=None):
    return BoundedRecursiveAnalysisNode(
        subject,
        None,
        (),
        BoundedRecursiveAnalysisResolution(
            subject,
            state,
            f"Exact caller-supplied operational state: {state.value}.",
            supporting_structural_invalidity_certificate=certificate,
            supporting_visibility_result=visibility,
            provenance_refs=("child:evidence",),
        ),
    )


def evidence_for(hypothesis, child_index, node):
    return FamilyChildCandidateEvidence(
        hypothesis,
        child_index,
        hypothesis.ordered_child_subjects[child_index],
        node,
        ("child:evidence",),
    )


class FamilyInternalSubdivisionTests(unittest.TestCase):
    def test_authority_boundaries_are_explicit(self):
        self.assertEqual("PROJECT_ANALYSIS_INFRASTRUCTURE", ARTIFACT_CLASSIFICATION)
        self.assertEqual(
            "SOURCE_DERIVED_INTERNAL_SUBDIVISION_EXPECTATION",
            REQUIREMENT_AUTHORITY_CLASSIFICATION,
        )
        self.assertEqual(
            "CALLER_SUPPLIED_OPERATIONAL_CHILD_EVIDENCE",
            CHILD_EVIDENCE_CLASSIFICATION,
        )
        self.assertEqual("PROJECT_OPERATIONAL_POLICY", SUMMARY_CLASSIFICATION)
        self.assertEqual((True, True, True, True), (
            INTERNAL_REQUIREMENT_IS_NOT_INTERNAL_PROOF,
            REVIEWED_CHILD_IS_NOT_VALIDATED_FAMILY,
            RECURSIVE_REVIEW_IS_NOT_ELLIOTT_TERMINALITY,
            TIMEFRAME_IS_NOT_DEGREE,
        ))

    def test_exact_family_result_and_identities_are_retained(self):
        source = bridge()
        result = evaluate(source)
        self.assertIs(source, result.family_hypothesis_result)
        self.assertEqual(len(source.family_hypotheses), len(result.hypothesis_evaluations))
        for hypothesis, evaluation in zip(
            source.family_hypotheses, result.hypothesis_evaluations, strict=True
        ):
            self.assertIs(hypothesis, evaluation.family_hypothesis)
            self.assertTrue(all(
                requirement.parent_candidate is hypothesis.generated_candidate
                for requirement in evaluation.internal_requirements
            ))

    def test_requirement_matrix_is_source_exact_and_deterministic(self):
        result = evaluate()
        expected = {
            FamilyEvaluationKind.SINGLE_ZIGZAG: (
                RequiredInternalShape.MOTIVE_FIVE_FAMILY_REQUIRED,
                RequiredInternalShape.CORRECTIVE_THREE_FAMILY_REQUIRED,
                RequiredInternalShape.MOTIVE_FIVE_FAMILY_REQUIRED,
            ),
            FamilyEvaluationKind.FLAT: (
                RequiredInternalShape.CORRECTIVE_THREE_FAMILY_REQUIRED,
                RequiredInternalShape.CORRECTIVE_THREE_FAMILY_REQUIRED,
                RequiredInternalShape.MOTIVE_FIVE_FAMILY_REQUIRED,
            ),
            FamilyEvaluationKind.TRIANGLE: (
                RequiredInternalShape.CORRECTIVE_FAMILY_REQUIRED,
            ) * 5,
            FamilyEvaluationKind.ENDING_DIAGONAL: (
                RequiredInternalShape.THREE_WAVE_STRUCTURE_REQUIRED,
            ) * 5,
        }
        for evaluation in result.hypothesis_evaluations:
            self.assertEqual(
                expected[evaluation.family_hypothesis.family_kind],
                tuple(item.required_internal_shape for item in evaluation.internal_requirements),
            )
        second = evaluate(result.family_hypothesis_result)
        self.assertEqual(
            tuple((item.family_hypothesis.hypothesis_id, item.child_index, item.required_internal_shape)
                  for item in result.internal_requirements),
            tuple((item.family_hypothesis.hypothesis_id, item.child_index, item.required_internal_shape)
                  for item in second.internal_requirements),
        )

    def test_source_class_ids_and_refs_are_exact(self):
        expected_ids = {
            FamilyEvaluationKind.SINGLE_ZIGZAG: "P007",
            FamilyEvaluationKind.FLAT: "P008",
            FamilyEvaluationKind.TRIANGLE: "P009",
            FamilyEvaluationKind.ENDING_DIAGONAL: None,
        }
        for item in evaluate().internal_requirements:
            self.assertEqual("SOURCE_DEFINITION", item.source_class)
            self.assertEqual(expected_ids[item.family_hypothesis.family_kind], item.source_principle_id)
            self.assertTrue(item.protected_refs)
            self.assertFalse(item.validated_child_family_authority)
            self.assertFalse(item.terminality_authority)

    def test_no_evidence_is_unresolved_and_not_a_terminal_base_case(self):
        result = evaluate()
        self.assertEqual((), result.structurally_blocked_hypotheses)
        self.assertEqual((), result.reviewed_internal_scope_hypotheses)
        self.assertEqual(len(result.hypothesis_evaluations), len(result.internally_unresolved_hypotheses))
        self.assertTrue(all(
            item.execution_status is InternalRequirementStatus.NO_CHILD_EVIDENCE_SUPPLIED
            for item in result.internal_requirements
        ))
        self.assertTrue(all(
            item.operational_summary
            is FamilyInternalOperationalSummary.BLOCKED_BY_UNRESOLVED_INTERNAL_STRUCTURE
            for item in result.hypothesis_evaluations
        ))

    def test_current_scope_reviewed_child_is_not_validated_family(self):
        source = bridge()
        hypothesis = source.family_hypotheses[0]
        child = hypothesis.ordered_child_subjects[0]
        node = leaf(child, AnalysisResolutionState.CURRENT_SUPPLIED_SCOPE_REVIEWED)
        result = evaluate(source, (evidence_for(hypothesis, 0, node),))
        requirement = result.hypothesis_evaluations[0].internal_requirements[0]
        self.assertIs(
            InternalRequirementStatus.INTERNAL_FAMILY_PROOF_BLOCKED_BY_NO_SOURCE_DERIVED_BASE_CASE,
            requirement.execution_status,
        )
        self.assertEqual((), result.reviewed_internal_scope_hypotheses)
        self.assertIn(
            SOURCE_DERIVED_BASE_CASE_NOT_FOUND,
            result.hypothesis_evaluations[0].unresolved_reasons,
        )
        self.assertEqual(
            "INTERNAL_FAMILY_PROOF_BLOCKED_BY_NO_SOURCE_DERIVED_BASE_CASE",
            INTERNAL_FAMILY_PROOF_BLOCKED_BY_NO_SOURCE_DERIVED_BASE_CASE,
        )

    def test_unresolved_child_remains_unresolved(self):
        source = bridge()
        hypothesis = source.family_hypotheses[0]
        child = hypothesis.ordered_child_subjects[0]
        node = leaf(child, AnalysisResolutionState.CURRENT_SUPPLIED_SCOPE_UNRESOLVED)
        result = evaluate(source, (evidence_for(hypothesis, 0, node),))
        self.assertIs(
            InternalRequirementStatus.CHILD_EVIDENCE_UNRESOLVED,
            result.hypothesis_evaluations[0].internal_requirements[0].execution_status,
        )

    def test_finer_data_does_not_auto_satisfy_p023_or_assign_degree(self):
        source = bridge()
        hypothesis = source.family_hypotheses[0]
        child = hypothesis.ordered_child_subjects[0]
        visibility = evaluate_p023_visibility_for_subject(
            child, P023VisibilityInput(P023VisibilityState.NOT_VISIBLE)
        )
        node = leaf(
            child,
            AnalysisResolutionState.UNRESOLVED_FINER_DATA_REQUIRED,
            visibility=visibility,
        )
        result = evaluate(source, (evidence_for(hypothesis, 0, node),))
        requirement = result.hypothesis_evaluations[0].internal_requirements[0]
        self.assertIs(InternalRequirementStatus.CHILD_EVIDENCE_UNRESOLVED, requirement.execution_status)
        source_text = inspect.getsource(internal_module)
        for forbidden in ("timeframe_degree", "recursive_depth", "degree_assignment"):
            self.assertNotIn(forbidden, source_text.lower())

    def test_genuine_structural_invalidity_is_retained_without_generator_issuance(self):
        source = bridge()
        hypothesis = source.family_hypotheses[0]
        child = hypothesis.ordered_child_subjects[0]
        origin = check_p004(P004Input(CandidateScope.NORMAL_IMPULSE, ImpulseDirection.UP, 100, 99))
        certificate = certify_structural_invalidity(origin)
        node = leaf(child, AnalysisResolutionState.STRUCTURALLY_INVALID, certificate=certificate)
        result = evaluate(source, (evidence_for(hypothesis, 0, node),))
        evaluation = result.hypothesis_evaluations[0]
        self.assertIs(FamilyInternalOperationalSummary.BLOCKED_BY_STRUCTURAL_INVALIDITY, evaluation.operational_summary)
        self.assertIs(OperationalAggregationState.BLOCKED_BY_INVALID_CHILD, evaluation.child_aggregation)
        self.assertEqual((certificate,), evaluation.structural_invalidity_evidence)
        self.assertIs(certificate, evaluation.structural_invalidity_evidence[0])
        self.assertIs(origin, certificate.origin)

    def test_one_family_failure_does_not_validate_competing_family(self):
        source = bridge()
        by_candidate = {}
        for hypothesis in source.family_hypotheses:
            by_candidate.setdefault(id(hypothesis.generated_candidate), []).append(hypothesis)
        pair = next(items for items in by_candidate.values() if len(items) > 1)
        first, second = pair[:2]
        child = first.ordered_child_subjects[0]
        certificate = certify_structural_invalidity(
            check_p004(P004Input(CandidateScope.NORMAL_IMPULSE, ImpulseDirection.UP, 100, 99))
        )
        result = evaluate(source, (evidence_for(
            first, 0, leaf(child, AnalysisResolutionState.STRUCTURALLY_INVALID, certificate=certificate)
        ),))
        evaluations = {item.family_hypothesis.hypothesis_id: item for item in result.hypothesis_evaluations}
        self.assertIs(
            FamilyInternalOperationalSummary.BLOCKED_BY_STRUCTURAL_INVALIDITY,
            evaluations[first.hypothesis_id].operational_summary,
        )
        self.assertIs(
            FamilyInternalOperationalSummary.BLOCKED_BY_UNRESOLVED_INTERNAL_STRUCTURE,
            evaluations[second.hypothesis_id].operational_summary,
        )

    def test_foreign_duplicate_wrong_subject_and_wrong_node_types_fail_closed(self):
        source = bridge()
        hypothesis = source.family_hypotheses[0]
        child = hypothesis.ordered_child_subjects[0]
        node = leaf(child, AnalysisResolutionState.CURRENT_SUPPLIED_SCOPE_UNRESOLVED)
        item = evidence_for(hypothesis, 0, node)
        with self.assertRaises(FamilyInternalSubdivisionError):
            request(source, (item, item))
        foreign = bridge().family_hypotheses[0]
        foreign_child = foreign.ordered_child_subjects[0]
        foreign_item = evidence_for(
            foreign, 0, leaf(foreign_child, AnalysisResolutionState.CURRENT_SUPPLIED_SCOPE_UNRESOLVED)
        )
        with self.assertRaises(FamilyInternalSubdivisionError):
            request(source, (foreign_item,))
        with self.assertRaises(FamilyInternalSubdivisionError):
            FamilyChildCandidateEvidence(hypothesis, 0, child, object(), ("x",))
        with self.assertRaises(FamilyInternalSubdivisionError):
            FamilyChildCandidateEvidence(
                hypothesis, 0, child,
                leaf(hypothesis.ordered_child_subjects[1], AnalysisResolutionState.CURRENT_SUPPLIED_SCOPE_UNRESOLVED),
                ("x",),
            )

    def test_mapping_duck_subclass_and_unissued_result_are_rejected(self):
        source = bridge()
        for supplied in ({"family_hypotheses": source.family_hypotheses}, object()):
            with self.subTest(supplied=type(supplied).__name__):
                with self.assertRaises(Exception):
                    request(family_hypothesis_result=supplied)
        with self.assertRaises(TypeError):
            type("EvidenceSubclass", (FamilyChildCandidateEvidence,), {})
        with self.assertRaises(TypeError):
            type("RequestSubclass", (FamilyInternalSubdivisionEvaluationRequest,), {})
        with self.assertRaises(TypeError):
            FamilyInternalSubdivisionEvaluationResult()
        malformed = object.__new__(FamilyInternalSubdivisionEvaluationResult)
        with self.assertRaises(Exception):
            malformed._validated()

    def test_objects_are_frozen_copy_stable_and_nonserializable(self):
        source = bridge()
        hypothesis = source.family_hypotheses[0]
        child = hypothesis.ordered_child_subjects[0]
        item = evidence_for(
            hypothesis, 0, leaf(child, AnalysisResolutionState.CURRENT_SUPPLIED_SCOPE_UNRESOLVED)
        )
        supplied_request = request(source, (item,))
        result = evaluate_family_internal_subdivisions(supplied_request)
        for value in (item, supplied_request, result):
            self.assertIs(value, copy.copy(value))
            self.assertIs(value, copy.deepcopy(value))
            with self.assertRaises(TypeError):
                pickle.dumps(value)
        with self.assertRaises(FrozenInstanceError):
            supplied_request.evaluation_id = "changed"

    def test_low_level_nested_mutation_fails_closed(self):
        result = evaluate()
        requirement = result.internal_requirements[0]
        object.__setattr__(requirement, "protected_refs", ("changed:but-well-formed",))
        with self.assertRaises(FamilyInternalSubdivisionError):
            result._validated()
        result = evaluate()
        evaluation = result.hypothesis_evaluations[0]
        object.__setattr__(evaluation, "unresolved_reasons", ("changed",))
        with self.assertRaises(FamilyInternalSubdivisionError):
            result._validated()
        result = evaluate()
        diagnostic = result.diagnostics[0]
        object.__setattr__(diagnostic, "detail", "changed")
        with self.assertRaises(FamilyInternalSubdivisionError):
            result._validated()

    def test_diagnostics_reconcile_exactly(self):
        result = evaluate()
        diagnostics = {item.code: item.count for item in result.diagnostics}
        self.assertEqual(len(result.internal_requirements), diagnostics[
            FamilyInternalDiagnosticCode.INTERNAL_REQUIREMENTS_CREATED
        ])
        self.assertEqual(len(result.internal_requirements), diagnostics[
            FamilyInternalDiagnosticCode.CHILD_EVIDENCE_MISSING
        ])
        self.assertEqual(0, diagnostics.get(FamilyInternalDiagnosticCode.CHILD_EVIDENCE_SUPPLIED, 0))
        self.assertEqual(0, diagnostics.get(FamilyInternalDiagnosticCode.STRUCTURAL_INVALIDITY_PRESENT, 0))
        self.assertEqual(0, diagnostics.get(FamilyInternalDiagnosticCode.CURRENT_INTERNAL_SCOPE_REVIEWED, 0))

    def test_existing_aggregator_is_reused_and_no_second_recursion_engine_exists(self):
        source = inspect.getsource(internal_module)
        self.assertIn("aggregate_supplied_child_resolutions", source)
        self.assertNotIn("def recurse", source.lower())
        self.assertNotIn("def discover", source.lower())

    def test_family_registry_remains_sealed_empty_and_no_certificate_is_constructed(self):
        evaluate()
        self.assertIs(True, family_private._REGISTRY_SEALED)
        self.assertEqual({}, family_private._PRODUCERS)
        self.assertEqual({}, family_private._ISSUED)
        source = inspect.getsource(internal_module)
        self.assertNotIn("certify_validated_internal_family", source)
        self.assertNotIn("CertifiedValidatedInternalFamily(", source)

    def test_no_impulse_combination_ranking_indicator_trap_forecast_or_trading_logic(self):
        tree = ast.parse(inspect.getsource(internal_module))
        imported = {
            alias.name.lower()
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        forbidden_imports = {"requests", "socket", "urllib", "subprocess", "yfinance", "tradingview"}
        self.assertTrue(imported.isdisjoint(forbidden_imports))
        source = inspect.getsource(internal_module).lower()
        for forbidden in (
            "rank", "confidence", "rsi", "macd", "ewo", "fibonacci", "trap",
            "forecast", "trade", "wxy", "impulse", "leading_diagonal",
        ):
            self.assertNotIn(f'"{forbidden}"', source)

    def test_no_observation_window_endpoint_or_elliott_label_authority(self):
        fields = FamilyInternalSubdivisionEvaluationRequest.__dataclass_fields__
        self.assertNotIn("timeframe", fields)
        self.assertNotIn("degree", fields)
        self.assertNotIn("observation_window", fields)
        self.assertNotIn("wave_label", fields)
        fields = FamilyChildCandidateEvidence.__dataclass_fields__
        self.assertNotIn("family_classification", fields)
        self.assertNotIn("validated_family", fields)

    def test_legacy_analyze_remains_not_implemented(self):
        kernel = MethodologyKernel(support.PROTECTED_ROOT)
        self.assertIn("KernelStatus.NOT_IMPLEMENTED", inspect.getsource(kernel.analyze))


if __name__ == "__main__":
    unittest.main()
