import ast
import copy
from dataclasses import FrozenInstanceError, asdict
from datetime import datetime, timezone
import inspect
import json
import pickle
import unittest

import support
import elliott_methodology_kernel as kernel_package
import elliott_methodology_kernel._structural_invalidity_certification as structural_private
import elliott_methodology_kernel._validated_internal_family_certification as family_private
import elliott_methodology_kernel.single_candidate_orchestration as orchestration_module
from elliott_methodology_kernel import (
    AnalysisResolutionState,
    AnalyzedWaveSubject,
    BoundedRecursiveAnalysisResolution,
    CandidateAnalysisEnvelope,
    CandidateBehaviorExecution,
    CandidateEvaluationPresence,
    CandidateMethodologyEvaluation,
    CandidateObservationAttachment,
    CandidateScope,
    ImpulseDirection,
    MethodologyDependencyCode,
    MethodologyKernel,
    OrderedChildBinding,
    P004Input,
    P007CandidateScope,
    P007SingleZigzagCardinalityInput,
    P023VisibilityInput,
    P023VisibilityState,
    SingleCandidateAnalysisRequest,
    SingleCandidateAnalysisResult,
    SingleCandidateExecutionSummary,
    SingleCandidateOrchestrationError,
    SubjectBoundObservedPriceObservation,
    apply_structural_invalidity_evidence_no_rescue,
    certify_structural_invalidity,
    certify_validated_internal_family,
    check_p004,
    check_p007_single_zigzag_cardinality,
    evaluate_p023_visibility_for_subject,
)
from elliott_methodology_kernel.models import (
    AnalysisRequest,
    DataProvenance,
    DataQualityReport,
    KernelStatus,
    MarketType,
    NormalizedMarketObservations,
    SymbolIdentity,
    Timeframe,
)


def subject(name: str) -> AnalyzedWaveSubject:
    return AnalyzedWaveSubject(name, f"observations:{name}")


def binding_for(analyzed_subject: AnalyzedWaveSubject, count: int = 2):
    return OrderedChildBinding(
        f"binding-{analyzed_subject.subject_id}-{count}",
        analyzed_subject,
        tuple(subject(f"child-{analyzed_subject.subject_id}-{index}") for index in range(count)),
    )


def p004_evaluation(
    analyzed_subject: AnalyzedWaveSubject,
    *,
    origin: int = 100,
    retracement: int = 100,
) -> CandidateMethodologyEvaluation:
    candidate = P004Input(
        CandidateScope.NORMAL_IMPULSE,
        ImpulseDirection.UP,
        origin,
        retracement,
    )
    return CandidateMethodologyEvaluation(
        analyzed_subject,
        "P004_NORMAL_IMPULSE_WAVE2_ORIGIN",
        candidate,
        check_p004(candidate),
        ("evaluation:p004",),
    )


def unresolved_dependency(
    analyzed_subject: AnalyzedWaveSubject,
) -> BoundedRecursiveAnalysisResolution:
    return BoundedRecursiveAnalysisResolution(
        analyzed_subject,
        AnalysisResolutionState.UNRESOLVED_METHODOLOGY_DEPENDENCY,
        "Required family producer remains unavailable.",
        dependency_code=MethodologyDependencyCode.FAMILY_PRODUCER_UNAVAILABLE,
        provenance_refs=("resolution:dependency",),
    )


def unresolved_finer_data(
    analyzed_subject: AnalyzedWaveSubject,
) -> BoundedRecursiveAnalysisResolution:
    visibility_input = P023VisibilityInput(P023VisibilityState.NOT_VISIBLE)
    visibility = evaluate_p023_visibility_for_subject(
        analyzed_subject,
        visibility_input,
    )
    return BoundedRecursiveAnalysisResolution(
        analyzed_subject,
        AnalysisResolutionState.UNRESOLVED_FINER_DATA_REQUIRED,
        "Required internals are not visible; finer data is required.",
        supporting_visibility_result=visibility,
        provenance_refs=("resolution:p023",),
    )


def invalidity_material(analyzed_subject: AnalyzedWaveSubject):
    child_binding = binding_for(analyzed_subject, 2)
    cardinality_input = P007SingleZigzagCardinalityInput(
        P007CandidateScope.SINGLE_ZIGZAG,
        child_binding,
    )
    origin = check_p007_single_zigzag_cardinality(cardinality_input)
    certificate = certify_structural_invalidity(origin)
    no_rescue = apply_structural_invalidity_evidence_no_rescue(certificate)
    evaluation = CandidateMethodologyEvaluation(
        analyzed_subject,
        "STRUCTURAL_INVALIDITY_EVIDENCE_NO_RESCUE",
        certificate,
        no_rescue,
        ("evaluation:no-rescue",),
    )
    return child_binding, origin, certificate, no_rescue, evaluation


def request_for(
    envelope: CandidateAnalysisEnvelope,
    request_id: str = "request-one",
) -> SingleCandidateAnalysisRequest:
    return SingleCandidateAnalysisRequest(
        request_id,
        "2026-09-03T12:00:00+00:00",
        envelope,
        ("request:live",),
    )


def methodology_kernel() -> MethodologyKernel:
    return MethodologyKernel(support.PROTECTED_ROOT)


def legacy_request(options=None) -> AnalysisRequest:
    timeframe = Timeframe("1H", 3600)
    observations = NormalizedMarketObservations(
        SymbolIdentity("TEST", MarketType.OTHER),
        timeframe,
        (),
        DataProvenance(
            "test",
            "memory",
            "0" * 64,
            timeframe,
            datetime.now(timezone.utc).isoformat(),
        ),
        DataQualityReport(),
    )
    return AnalysisRequest(
        observations,
        datetime.now(timezone.utc).isoformat(),
        "legacy-request",
        {} if options is None else options,
    )


class SingleCandidateOrchestrationTests(unittest.TestCase):
    def test_exact_request_envelope_and_request_id_are_retained(self) -> None:
        analyzed_subject = subject("request")
        envelope = CandidateAnalysisEnvelope(analyzed_subject, "candidate")
        request = request_for(envelope)
        self.assertIs(envelope, request.candidate_envelope)
        self.assertEqual("request-one", request.request_id)
        self.assertIs(request, copy.copy(request))
        self.assertIs(request, copy.deepcopy(request))
        with self.assertRaises(FrozenInstanceError):
            request.request_id = "changed"
        with self.assertRaises(TypeError):
            pickle.dumps(request)

    def test_mapping_duck_and_subclass_envelopes_are_rejected(self) -> None:
        class Duck:
            subject = subject("duck")

        with self.assertRaises(TypeError):
            type("EnvelopeSubclass", (CandidateAnalysisEnvelope,), {})
        for supplied in ({"candidate_id": "x"}, Duck(), object()):
            with self.subTest(kind=type(supplied).__name__):
                with self.assertRaises(SingleCandidateOrchestrationError):
                    SingleCandidateAnalysisRequest(
                        "request",
                        "2026-09-03T12:00:00Z",
                        supplied,
                    )

    def test_legacy_analyze_remains_not_implemented(self) -> None:
        result = methodology_kernel().analyze(legacy_request())
        self.assertIs(KernelStatus.NOT_IMPLEMENTED, result.status)
        self.assertIsNone(result.analysis)
        self.assertTrue(result.unresolved.items)

    def test_legacy_options_cannot_inject_candidate_authority(self) -> None:
        analyzed_subject = subject("options")
        injection = {
            "candidate_id": "pretend",
            "candidate_envelope": CandidateAnalysisEnvelope(
                analyzed_subject,
                "live-but-untrusted-in-options",
            ),
            "pattern": "IMPULSE",
        }
        result = methodology_kernel().analyze(legacy_request(injection))
        self.assertIs(KernelStatus.NOT_IMPLEMENTED, result.status)
        self.assertIsNone(result.analysis)

    def test_legacy_output_schema_validation_is_unchanged(self) -> None:
        output = json.loads(
            (support.PROTECTED_ROOT / "examples" / "EMPTY_ANALYSIS.json")
            .read_text(encoding="utf-8")
        )
        self.assertIsNone(methodology_kernel().validate_analysis_output(output))

    def test_nonempty_verified_evaluations_produce_reviewed_only(self) -> None:
        analyzed_subject = subject("reviewed")
        evaluations = (
            p004_evaluation(analyzed_subject, origin=1, retracement=1),
            p004_evaluation(analyzed_subject, origin=2, retracement=2),
        )
        envelope = CandidateAnalysisEnvelope(
            analyzed_subject,
            "reviewed",
            methodology_evaluations=evaluations,
        )
        result = methodology_kernel().analyze_candidate(request_for(envelope))
        self.assertIs(
            SingleCandidateExecutionSummary.SUPPLIED_EVALUATIONS_REVIEWED,
            result.execution_summary,
        )
        self.assertIs(evaluations, result.verified_evaluations)
        self.assertIs(envelope, result.candidate_envelope)
        self.assertIs(analyzed_subject, result.candidate_subject)
        self.assertEqual((), result.unresolved_reasons)
        for expected, observed in zip(evaluations, result.verified_evaluations, strict=True):
            self.assertIs(expected, observed)

    def test_execution_inventory_has_all_ten_presence_records(self) -> None:
        analyzed_subject = subject("inventory")
        evaluation = p004_evaluation(analyzed_subject)
        envelope = CandidateAnalysisEnvelope(
            analyzed_subject,
            "inventory",
            methodology_evaluations=(evaluation,),
        )
        result = methodology_kernel().analyze_candidate(request_for(envelope))
        self.assertEqual(10, len(result.execution_inventory))
        self.assertEqual(
            1,
            sum(item.presence is CandidateEvaluationPresence.SUPPLIED_AND_VERIFIED for item in result.execution_inventory),
        )
        self.assertEqual(
            9,
            sum(item.presence is CandidateEvaluationPresence.NOT_SUPPLIED for item in result.execution_inventory),
        )
        p004_record = result.execution_inventory[0]
        self.assertEqual("P004_NORMAL_IMPULSE_WAVE2_ORIGIN", p004_record.behavior_id)
        self.assertIs(CandidateEvaluationPresence.SUPPLIED_AND_VERIFIED, p004_record.presence)
        self.assertIs(evaluation, p004_record.evaluations[0])
        self.assertTrue(p004_record.verified)
        self.assertTrue(all(not item.verified for item in result.execution_inventory[1:]))

    def test_unknown_mismatched_cross_subject_and_mutated_evaluations_cannot_enter(self) -> None:
        analyzed_subject = subject("adversarial-evaluation")
        evaluation = p004_evaluation(analyzed_subject)
        envelope = CandidateAnalysisEnvelope(
            analyzed_subject,
            "adversarial",
            methodology_evaluations=(evaluation,),
        )
        object.__setattr__(evaluation, "behavior_id", "UNKNOWN_BEHAVIOR")
        with self.assertRaises(SingleCandidateOrchestrationError):
            methodology_kernel().analyze_candidate(request_for(envelope))

        other_subject = subject("other")
        other_evaluation = p004_evaluation(other_subject)
        forged_envelope = object.__new__(CandidateAnalysisEnvelope)
        for name, value in (
            ("subject", analyzed_subject),
            ("candidate_id", "forged"),
            ("child_binding", None),
            ("methodology_evaluations", (other_evaluation,)),
            ("observations", ()),
            ("operational_resolution", None),
            ("provenance_refs", ()),
            ("_envelope_snapshot", ()),
        ):
            object.__setattr__(forged_envelope, name, value)
        with self.assertRaises(SingleCandidateOrchestrationError):
            SingleCandidateAnalysisRequest(
                "forged-request",
                "2026-09-03T12:00:00Z",
                forged_envelope,
            )

    def test_genuine_no_rescue_certificate_has_invalidity_precedence(self) -> None:
        analyzed_subject = subject("invalid")
        child_binding, origin, certificate, _, invalid_evaluation = invalidity_material(analyzed_subject)
        other_evaluation = p004_evaluation(analyzed_subject)
        envelope = CandidateAnalysisEnvelope(
            analyzed_subject,
            "invalid",
            child_binding,
            (other_evaluation, invalid_evaluation),
            operational_resolution=unresolved_dependency(analyzed_subject),
        )
        result = methodology_kernel().analyze_candidate(request_for(envelope))
        self.assertIs(
            SingleCandidateExecutionSummary.STRUCTURALLY_INVALID,
            result.execution_summary,
        )
        self.assertIs(certificate, result.structural_invalidity_certificates[0])
        self.assertIs(origin, certificate.origin)
        self.assertTrue(result.unresolved_reasons)
        self.assertIs(envelope.operational_resolution, result.operational_resolution)

    def test_invalid_operational_resolution_retains_exact_certificate(self) -> None:
        analyzed_subject = subject("invalid-resolution")
        child_binding, _, certificate, _, evaluation = invalidity_material(analyzed_subject)
        resolution = BoundedRecursiveAnalysisResolution(
            analyzed_subject,
            AnalysisResolutionState.STRUCTURALLY_INVALID,
            "Certified invalidity stops the candidate.",
            supporting_structural_invalidity_certificate=certificate,
        )
        envelope = CandidateAnalysisEnvelope(
            analyzed_subject,
            "invalid-resolution",
            child_binding,
            (evaluation,),
            operational_resolution=resolution,
        )
        result = methodology_kernel().analyze_candidate(request_for(envelope))
        self.assertIs(
            SingleCandidateExecutionSummary.STRUCTURALLY_INVALID,
            result.execution_summary,
        )
        self.assertEqual(1, len(result.structural_invalidity_certificates))
        self.assertIs(certificate, result.structural_invalidity_certificates[0])

    def test_fake_manual_copied_and_lookalike_invalidity_cannot_enter(self) -> None:
        analyzed_subject = subject("fake-invalidity")
        child_binding, origin, certificate, _, _ = invalidity_material(analyzed_subject)

        class Duck:
            pass

        duck = Duck()
        duck.origin = origin

        copied_origin = copy.copy(origin)
        self.assertIsNot(origin, copied_origin)
        with self.assertRaises(Exception):
            certify_structural_invalidity(copied_origin)
        for supplied in (object(), asdict(origin), duck):
            with self.subTest(kind=type(supplied).__name__):
                with self.assertRaises(Exception):
                    apply_structural_invalidity_evidence_no_rescue(supplied)
        self.assertIs(certificate, copy.copy(certificate))
        self.assertIs(certificate, copy.deepcopy(certificate))
        self.assertIs(child_binding, certificate.origin.binding)

    def test_uncertified_fatal_result_is_unresolved_not_invalid(self) -> None:
        analyzed_subject = subject("uncertified")
        child_binding = binding_for(analyzed_subject, 2)
        candidate = P007SingleZigzagCardinalityInput(
            P007CandidateScope.SINGLE_ZIGZAG,
            child_binding,
        )
        evaluation = CandidateMethodologyEvaluation(
            analyzed_subject,
            "P007_SINGLE_ZIGZAG_DIRECT_CHILD_CARDINALITY",
            candidate,
            check_p007_single_zigzag_cardinality(candidate),
        )
        envelope = CandidateAnalysisEnvelope(
            analyzed_subject,
            "uncertified",
            child_binding,
            (evaluation,),
        )
        result = methodology_kernel().analyze_candidate(request_for(envelope))
        self.assertIs(SingleCandidateExecutionSummary.UNRESOLVED, result.execution_summary)
        self.assertIn(
            orchestration_module.UNCERTIFIED_FATAL_RESULT,
            result.unresolved_reasons,
        )
        self.assertEqual((), result.structural_invalidity_certificates)

    def test_each_operational_unresolved_state_is_preserved(self) -> None:
        for builder in (unresolved_finer_data, unresolved_dependency):
            with self.subTest(builder=builder.__name__):
                analyzed_subject = subject(builder.__name__)
                resolution = builder(analyzed_subject)
                envelope = CandidateAnalysisEnvelope(
                    analyzed_subject,
                    builder.__name__,
                    methodology_evaluations=(p004_evaluation(analyzed_subject),),
                    operational_resolution=resolution,
                )
                result = methodology_kernel().analyze_candidate(request_for(envelope))
                self.assertIs(SingleCandidateExecutionSummary.UNRESOLVED, result.execution_summary)
                self.assertIs(resolution, result.operational_resolution)
                self.assertIn(resolution.reason, result.unresolved_reasons)
                self.assertEqual((), result.structural_invalidity_certificates)

    def test_dependency_code_remains_available_on_exact_resolution(self) -> None:
        analyzed_subject = subject("dependency-code")
        resolution = unresolved_dependency(analyzed_subject)
        envelope = CandidateAnalysisEnvelope(
            analyzed_subject,
            "dependency-code",
            methodology_evaluations=(p004_evaluation(analyzed_subject),),
            operational_resolution=resolution,
        )
        result = methodology_kernel().analyze_candidate(request_for(envelope))
        self.assertIs(
            MethodologyDependencyCode.FAMILY_PRODUCER_UNAVAILABLE,
            result.operational_resolution.dependency_code,
        )

    def test_zero_evaluations_is_conservatively_unresolved(self) -> None:
        analyzed_subject = subject("zero")
        envelope = CandidateAnalysisEnvelope(analyzed_subject, "zero")
        result = methodology_kernel().analyze_candidate(request_for(envelope))
        self.assertIs(SingleCandidateExecutionSummary.UNRESOLVED, result.execution_summary)
        self.assertEqual(
            (orchestration_module.NO_METHODOLOGY_EVALUATIONS_SUPPLIED,),
            result.unresolved_reasons,
        )
        self.assertTrue(
            all(item.presence is CandidateEvaluationPresence.NOT_SUPPLIED for item in result.execution_inventory)
        )

    def test_reviewed_summary_has_no_validity_completion_or_requiredness_claim(self) -> None:
        analyzed_subject = subject("limited-review")
        envelope = CandidateAnalysisEnvelope(
            analyzed_subject,
            "limited-review",
            methodology_evaluations=(p004_evaluation(analyzed_subject),),
        )
        result = methodology_kernel().analyze_candidate(request_for(envelope))
        forbidden = {
            "valid_candidate", "family_valid", "structural_validity", "complete",
            "all_required_behaviors_supplied", "preferred", "confidence", "rank",
        }
        self.assertTrue(forbidden.isdisjoint(SingleCandidateAnalysisResult.__dataclass_fields__))
        self.assertIs(
            CandidateEvaluationPresence.NOT_SUPPLIED,
            result.execution_inventory[1].presence,
        )
        with self.assertRaises(Exception):
            certify_validated_internal_family(result)

    def test_observations_are_retained_and_do_not_change_summary(self) -> None:
        analyzed_subject = subject("observation")
        evaluation = p004_evaluation(analyzed_subject)
        observation = CandidateObservationAttachment(
            analyzed_subject,
            SubjectBoundObservedPriceObservation(analyzed_subject, 100, "price"),
            ("observation:transport",),
        )
        plain = CandidateAnalysisEnvelope(
            analyzed_subject,
            "plain",
            methodology_evaluations=(evaluation,),
        )
        observed = CandidateAnalysisEnvelope(
            analyzed_subject,
            "observed",
            methodology_evaluations=(evaluation,),
            observations=(observation,),
        )
        plain_result = methodology_kernel().analyze_candidate(request_for(plain, "plain"))
        observed_result = methodology_kernel().analyze_candidate(request_for(observed, "observed"))
        self.assertIs(plain_result.execution_summary, observed_result.execution_summary)
        self.assertIs(observation, observed_result.candidate_envelope.observations[0])
        self.assertTrue(
            {"pivot", "endpoint", "completion", "direction", "pattern"}
            .isdisjoint(SingleCandidateAnalysisResult.__dataclass_fields__)
        )

    def test_family_registry_remains_empty_and_orchestration_cannot_issue(self) -> None:
        analyzed_subject = subject("family")
        result = methodology_kernel().analyze_candidate(
            request_for(CandidateAnalysisEnvelope(analyzed_subject, "family"))
        )
        self.assertTrue(family_private._REGISTRY_SEALED)
        self.assertEqual(0, len(family_private._PRODUCERS))
        self.assertEqual(0, len(family_private._ISSUED))
        with self.assertRaises(Exception):
            certify_validated_internal_family(result)

    def test_result_is_factory_only_immutable_identity_and_nonserializable(self) -> None:
        analyzed_subject = subject("result-identity")
        envelope = CandidateAnalysisEnvelope(
            analyzed_subject,
            "result-identity",
            methodology_evaluations=(p004_evaluation(analyzed_subject),),
        )
        result = methodology_kernel().analyze_candidate(request_for(envelope))
        with self.assertRaises(TypeError):
            SingleCandidateAnalysisResult()
        with self.assertRaises(FrozenInstanceError):
            result.execution_summary = SingleCandidateExecutionSummary.UNRESOLVED
        self.assertIs(result, copy.copy(result))
        self.assertIs(result, copy.deepcopy(result))
        with self.assertRaises(TypeError):
            pickle.dumps(result)

    def test_arbitrary_subject_id_and_cross_subject_resolution_fail_closed(self) -> None:
        first = subject("same-id")
        recreated = subject("same-id")
        self.assertIsNot(first, recreated)
        resolution = unresolved_dependency(first)
        with self.assertRaises(Exception):
            CandidateAnalysisEnvelope(
                recreated,
                "same-id-is-not-authority",
                operational_resolution=resolution,
            )

    def test_low_level_request_result_and_nested_mutation_fail_closed(self) -> None:
        analyzed_subject = subject("mutation")
        evaluation = p004_evaluation(analyzed_subject)
        envelope = CandidateAnalysisEnvelope(
            analyzed_subject,
            "mutation",
            methodology_evaluations=(evaluation,),
        )
        request = request_for(envelope)
        object.__setattr__(request, "request_id", "mutated")
        with self.assertRaises(SingleCandidateOrchestrationError):
            methodology_kernel().analyze_candidate(request)

        clean_request = request_for(envelope, "clean")
        result = methodology_kernel().analyze_candidate(clean_request)
        object.__setattr__(result, "execution_summary", SingleCandidateExecutionSummary.UNRESOLVED)
        with self.assertRaises(SingleCandidateOrchestrationError):
            copy.copy(result)

        nested_request = request_for(envelope, "nested")
        object.__setattr__(evaluation.result_object, "reason", "mutated")
        with self.assertRaises(SingleCandidateOrchestrationError):
            methodology_kernel().analyze_candidate(nested_request)

    def test_public_surface_and_api_signatures_are_exact(self) -> None:
        expected = {
            "CandidateBehaviorExecution",
            "CandidateEvaluationPresence",
            "SingleCandidateAnalysisRequest",
            "SingleCandidateAnalysisResult",
            "SingleCandidateExecutionSummary",
            "SingleCandidateOrchestrationError",
        }
        self.assertTrue(expected.issubset(set(kernel_package.__all__)))
        self.assertEqual(
            ("self", "request"),
            tuple(inspect.signature(MethodologyKernel.analyze_candidate).parameters),
        )
        self.assertEqual(
            ("self", "request"),
            tuple(inspect.signature(MethodologyKernel.analyze).parameters),
        )

    def test_no_discovery_ranking_network_or_schema_capability_was_added(self) -> None:
        path = support.SRC / "elliott_methodology_kernel" / "single_candidate_orchestration.py"
        source_text = path.read_text(encoding="utf-8")
        tree = ast.parse(source_text, filename=str(path))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add("." * node.level + (node.module or ""))
        self.assertTrue(
            {"socket", "subprocess", "requests", "urllib", "pathlib", "importlib"}
            .isdisjoint(imports)
        )
        for forbidden in (
            "TradingView", "RSI", "MACD", "EWO", "Fibonacci", "volume analysis",
            "pivot generation", "wave label", "degree inference", "timeframe mapping",
            "PREFERRED", "ALTERNATIVE", "REMOTE", "scenario ranking", "trade decision",
            "ANALYSIS_OUTPUT_SCHEMA", "assert_valid", "certify_structural_invalidity(",
            "certify_validated_internal_family(",
        ):
            self.assertNotIn(forbidden, source_text)

    def test_methodology_inventory_and_registries_remain_exact(self) -> None:
        observed = set()
        for path in (support.SRC / "elliott_methodology_kernel").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                assignments = ()
                if isinstance(node, ast.Assign):
                    assignments = tuple(target for target in node.targets if isinstance(target, ast.Name))
                elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    assignments = (node.target,)
                for target in assignments:
                    if (
                        target.id.endswith(("BEHAVIOR_ID", "BEHAVIOR"))
                        and isinstance(node.value, ast.Constant)
                        and isinstance(node.value.value, str)
                    ):
                        observed.add(node.value.value)
        self.assertEqual(
            {
                "P004_NORMAL_IMPULSE_WAVE2_ORIGIN",
                "DEGREE_DIRECT_CHILD_PEER_CONSISTENCY",
                "PARENT_CHILD_DEGREE_ADJACENCY",
                "P023_INTERNAL_VISIBILITY_GUARD",
                "STRUCTURAL_INVALIDITY_EVIDENCE_NO_RESCUE",
                "P003_ONE_LARGER_DEGREE_SEARCH_THEME",
                "P007_SINGLE_ZIGZAG_DIRECT_CHILD_CARDINALITY",
                "P008_FLAT_DIRECT_CHILD_CARDINALITY",
                "P009_TRIANGLE_DIRECT_CHILD_CARDINALITY",
                "ENDING_DIAGONAL_DIRECT_CHILD_CARDINALITY",
            },
            observed,
        )
        self.assertTrue(structural_private._REGISTRY_SEALED)
        self.assertEqual(7, len(structural_private._PRODUCERS))
        self.assertTrue(family_private._REGISTRY_SEALED)
        self.assertEqual(0, len(family_private._PRODUCERS))
        self.assertEqual(0, len(family_private._ISSUED))
        self.assertIn(
            "status=KernelStatus.NOT_IMPLEMENTED",
            inspect.getsource(MethodologyKernel.analyze),
        )


if __name__ == "__main__":
    unittest.main()
