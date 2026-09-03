import ast
import copy
from dataclasses import FrozenInstanceError, asdict, fields
import inspect
import pickle
import unittest

import support
import elliott_methodology_kernel as kernel_package
import elliott_methodology_kernel._structural_invalidity_certification as structural_private
import elliott_methodology_kernel._validated_internal_family_certification as family_private
import elliott_methodology_kernel.bounded_manual_chart_analysis as mvp_module
import elliott_methodology_kernel.candidate_analysis_envelope as envelope_module
from elliott_methodology_kernel import (
    AnalysisResolutionState,
    AnalyzedWaveSubject,
    BoundedManualChartAnalysisError,
    BoundedManualChartAnalysisRequest,
    BoundedManualChartAnalysisResult,
    BoundedManualChartCoverageState,
    BoundedManualChartFinalSummary,
    BoundedRecursiveAnalysisResolution,
    CandidateObservationAttachment,
    CandidateScope,
    DegreePeerConsistencyInput,
    ExplicitBehaviorExecutionResult,
    ImpulseDirection,
    ManualCardinalityBehavior,
    ManualDegreePeerFact,
    ManualDirectChildCardinalityFact,
    ManualP004Wave2OriginFact,
    ManualP023VisibilityFact,
    ManualParentChildDegreeFact,
    ManualStructureCandidateBuildResult,
    MethodologyDependencyCode,
    MethodologyKernel,
    OrderedChildBinding,
    P009CandidateScope,
    P009TriangleCardinalityInput,
    P023VisibilityInput,
    P023VisibilityState,
    SingleCandidateAnalysisResult,
    SubjectBoundObservedPriceObservation,
    certify_structural_invalidity,
    certify_validated_internal_family,
    check_p009_triangle_cardinality,
    evaluate_p023_visibility_for_subject,
)
from elliott_methodology_kernel.models import DegreeStatus, DegreeTreeNode, InternalStatus


def subject(name: str) -> AnalyzedWaveSubject:
    return AnalyzedWaveSubject(name, f"observations:{name}")


def children(parent: AnalyzedWaveSubject, count: int):
    return tuple(subject(f"{parent.subject_id}:child:{index}") for index in range(count))


def binding_for(parent: AnalyzedWaveSubject, count: int = 3) -> OrderedChildBinding:
    return OrderedChildBinding(f"binding:{parent.subject_id}:{count}", parent, children(parent, count))


def p004_fact() -> ManualP004Wave2OriginFact:
    return ManualP004Wave2OriginFact(
        CandidateScope.NORMAL_IMPULSE,
        ImpulseDirection.UP,
        100,
        101,
    )


def request_for(
    analyzed_subject: AnalyzedWaveSubject,
    facts=(),
    *,
    child_binding=None,
    ordered_child_subjects=None,
    constructed_binding_id=None,
    certificates=(),
    no_rescue_requested=False,
    observations=(),
    operational_resolution=None,
    candidate_id="bounded-candidate",
) -> BoundedManualChartAnalysisRequest:
    return BoundedManualChartAnalysisRequest(
        request_id="bounded-request",
        requested_at_utc="2026-09-03T12:00:00Z",
        subject=analyzed_subject,
        candidate_id=candidate_id,
        manual_behavior_facts=facts,
        child_binding=child_binding,
        ordered_child_subjects=ordered_child_subjects,
        constructed_binding_id=constructed_binding_id,
        trusted_invalidity_certificates=certificates,
        no_rescue_requested=no_rescue_requested,
        observations=observations,
        operational_resolution=operational_resolution,
        provenance_refs=("mvp:manual",),
    )


def kernel() -> MethodologyKernel:
    return MethodologyKernel(support.PROTECTED_ROOT)


class BoundedManualChartAnalysisTests(unittest.TestCase):
    def test_exact_request_identity_metadata_immutability_and_pickle_boundary(self) -> None:
        analyzed_subject = subject("request")
        request = request_for(analyzed_subject, candidate_id="opaque-only")
        self.assertIs(analyzed_subject, request.subject)
        self.assertEqual("opaque-only", request.candidate_id)
        self.assertIs(request, copy.copy(request))
        self.assertIs(request, copy.deepcopy(request))
        with self.assertRaises(FrozenInstanceError):
            request.candidate_id = "changed"
        with self.assertRaises(TypeError):
            pickle.dumps(request)

    def test_mapping_duck_and_subclass_requests_fail_closed(self) -> None:
        class Duck:
            manual_behavior_facts = ()

        with self.assertRaises(TypeError):
            type("MvpSubclass", (BoundedManualChartAnalysisRequest,), {})
        for value in ({"manual_behavior_facts": ()}, Duck(), object()):
            with self.subTest(kind=type(value).__name__):
                with self.assertRaises(BoundedManualChartAnalysisError):
                    kernel().analyze_bounded_manual_chart(value)

    def test_delegation_retains_all_three_exact_downstream_results(self) -> None:
        result = kernel().analyze_bounded_manual_chart(
            request_for(subject("delegation"), (p004_fact(),))
        )
        self.assertIs(ManualStructureCandidateBuildResult, type(result.manual_build_result))
        self.assertIs(ExplicitBehaviorExecutionResult, type(result.explicit_execution_result))
        self.assertIs(SingleCandidateAnalysisResult, type(result.candidate_analysis_result))
        self.assertIs(
            result.manual_build_result.delegated_execution_result,
            result.explicit_execution_result,
        )
        self.assertIs(
            result.explicit_execution_result.single_candidate_analysis_result,
            result.candidate_analysis_result,
        )

    def test_mvp_has_no_methodology_dispatch_or_input_constructor_table(self) -> None:
        source_text = (support.SRC / "elliott_methodology_kernel" / "bounded_manual_chart_analysis.py").read_text(encoding="utf-8")
        self.assertNotIn("_EXECUTION_DISPATCH", source_text)
        self.assertNotIn("_MANUAL_FACT_BUILDERS", source_text)
        self.assertNotIn("check_p004", source_text)
        self.assertNotIn("check_p0", source_text)
        self.assertNotIn("map_p003", source_text)
        self.assertIn("analyze_manual_candidate(request._manual_request)", source_text)

    def test_p004_flows_end_to_end_with_exact_existing_input_and_result(self) -> None:
        fact = p004_fact()
        result = kernel().analyze_bounded_manual_chart(request_for(subject("p004"), (fact,)))
        trace = result.traceability[0]
        self.assertIs(fact, trace.manual_fact)
        self.assertIs(kernel_package.P004Input, type(trace.explicit_input.input_object))
        self.assertIs(kernel_package.P004Result, type(trace.result_object))
        self.assertIs(trace.result_object, trace.evaluation.result_object)
        self.assertIs(
            BoundedManualChartFinalSummary.CURRENT_SUPPLIED_SCOPE_REVIEWED,
            result.final_summary,
        )

    def test_each_p023_state_flows_without_validity_promotion(self) -> None:
        expected = {
            P023VisibilityState.NOT_VISIBLE: BoundedManualChartFinalSummary.UNRESOLVED,
            P023VisibilityState.UNKNOWN: BoundedManualChartFinalSummary.UNRESOLVED,
            P023VisibilityState.VISIBLE: BoundedManualChartFinalSummary.CURRENT_SUPPLIED_SCOPE_REVIEWED,
        }
        for state, summary in expected.items():
            with self.subTest(state=state):
                analyzed_subject = subject(state.value)
                fact = ManualP023VisibilityFact(analyzed_subject, state)
                result = kernel().analyze_bounded_manual_chart(request_for(analyzed_subject, (fact,)))
                self.assertIs(summary, result.final_summary)
                wrapped = result.traceability[0].result_object
                self.assertIs(analyzed_subject, wrapped.subject)
                self.assertNotIn("valid", BoundedManualChartFinalSummary.CURRENT_SUPPLIED_SCOPE_REVIEWED.value.lower())

    def test_each_cardinality_selector_runs_only_its_selected_behavior(self) -> None:
        expected = {
            ManualCardinalityBehavior.SINGLE_ZIGZAG: "P007_SINGLE_ZIGZAG_DIRECT_CHILD_CARDINALITY",
            ManualCardinalityBehavior.FLAT: "P008_FLAT_DIRECT_CHILD_CARDINALITY",
            ManualCardinalityBehavior.TRIANGLE: "P009_TRIANGLE_DIRECT_CHILD_CARDINALITY",
            ManualCardinalityBehavior.ENDING_DIAGONAL: "ENDING_DIAGONAL_DIRECT_CHILD_CARDINALITY",
        }
        for selector, behavior_id in expected.items():
            with self.subTest(selector=selector):
                analyzed_subject = subject(selector.value)
                binding = binding_for(analyzed_subject, 3)
                result = kernel().analyze_bounded_manual_chart(
                    request_for(
                        analyzed_subject,
                        (ManualDirectChildCardinalityFact(selector),),
                        child_binding=binding,
                    )
                )
                supplied = [item for item in result.methodology_coverage if item.state is BoundedManualChartCoverageState.SUPPLIED_AND_EXECUTED]
                self.assertEqual([behavior_id], [item.behavior_id for item in supplied])

    def test_child_count_alone_infers_no_behavior(self) -> None:
        for count in (3, 5):
            analyzed_subject = subject(f"count-{count}")
            result = kernel().analyze_bounded_manual_chart(
                request_for(analyzed_subject, child_binding=binding_for(analyzed_subject, count))
            )
            self.assertTrue(all(item.state is BoundedManualChartCoverageState.NOT_SUPPLIED for item in result.methodology_coverage))
            self.assertIs(BoundedManualChartFinalSummary.UNRESOLVED, result.final_summary)

    def test_degree_behaviors_flow_only_from_explicit_degree_facts(self) -> None:
        analyzed_subject = subject("degree")
        nodes = tuple(
            DegreeTreeNode(f"peer-{index}", "Primary", DegreeStatus.RESOLVED, InternalStatus.CONFIRMED)
            for index in range(2)
        )
        facts = (
            ManualDegreePeerFact("parent", nodes),
            ManualParentChildDegreeFact("Primary", DegreeStatus.RESOLVED, "Intermediate", DegreeStatus.RESOLVED),
        )
        result = kernel().analyze_bounded_manual_chart(request_for(analyzed_subject, facts))
        self.assertIs(DegreePeerConsistencyInput, type(result.traceability[0].explicit_input.input_object))
        self.assertIs(kernel_package.ParentChildDegreeInput, type(result.traceability[1].explicit_input.input_object))
        self.assertIs(BoundedManualChartFinalSummary.CURRENT_SUPPLIED_SCOPE_REVIEWED, result.final_summary)

    def test_genuine_certified_invalidity_has_precedence_and_exact_identity(self) -> None:
        analyzed_subject = subject("invalid")
        binding = binding_for(analyzed_subject, 3)
        triangle = P009TriangleCardinalityInput(P009CandidateScope.TRIANGLE, binding)
        certificate = certify_structural_invalidity(check_p009_triangle_cardinality(triangle))
        observation = CandidateObservationAttachment(
            analyzed_subject,
            SubjectBoundObservedPriceObservation(analyzed_subject, 100, "observed:manual"),
        )
        resolution = BoundedRecursiveAnalysisResolution(
            analyzed_subject,
            AnalysisResolutionState.UNRESOLVED_METHODOLOGY_DEPENDENCY,
            "A separate dependency remains unresolved.",
            dependency_code=MethodologyDependencyCode.FAMILY_PRODUCER_UNAVAILABLE,
        )
        result = kernel().analyze_bounded_manual_chart(
            request_for(
                analyzed_subject,
                child_binding=binding,
                certificates=(certificate,),
                no_rescue_requested=True,
                observations=(observation,),
                operational_resolution=resolution,
            )
        )
        self.assertIs(BoundedManualChartFinalSummary.STRUCTURALLY_INVALID, result.final_summary)
        self.assertIs(certificate, result.structural_invalidity_certificates[0])
        self.assertTrue(result.unresolved_reasons)

    def test_fake_certificate_rejected_by_existing_nested_boundaries(self) -> None:
        with self.assertRaises(Exception):
            request_for(
                subject("fake"),
                certificates=(object(),),
                no_rescue_requested=True,
            )

    def test_zero_facts_is_unresolved_with_exact_existing_reason(self) -> None:
        result = kernel().analyze_bounded_manual_chart(request_for(subject("zero")))
        self.assertIs(BoundedManualChartFinalSummary.UNRESOLVED, result.final_summary)
        self.assertIn("NO_METHODOLOGY_EVALUATIONS_SUPPLIED", result.unresolved_reasons)
        self.assertEqual(0, len(result.candidate_analysis_result.verified_evaluations))

    def test_missing_trusted_dependency_is_unresolved_and_coverage_blocked(self) -> None:
        result = kernel().analyze_bounded_manual_chart(
            request_for(subject("missing-dependency"), (p004_fact(),), no_rescue_requested=True)
        )
        self.assertIs(BoundedManualChartFinalSummary.UNRESOLVED, result.final_summary)
        self.assertIn(
            "MISSING_TRUSTED_STRUCTURAL_INVALIDITY_CERTIFICATE",
            result.unresolved_reasons,
        )
        no_rescue = next(item for item in result.methodology_coverage if item.behavior_id == "STRUCTURAL_INVALIDITY_EVIDENCE_NO_RESCUE")
        self.assertIs(BoundedManualChartCoverageState.BLOCKED_MISSING_TRUSTED_DEPENDENCY, no_rescue.state)

    def test_finer_data_and_methodology_dependency_reasons_are_retained(self) -> None:
        for state, code in (
            (AnalysisResolutionState.UNRESOLVED_FINER_DATA_REQUIRED, None),
            (AnalysisResolutionState.UNRESOLVED_METHODOLOGY_DEPENDENCY, MethodologyDependencyCode.FAMILY_PRODUCER_UNAVAILABLE),
        ):
            with self.subTest(state=state):
                analyzed_subject = subject(state.value)
                kwargs = {}
                if code is not None:
                    kwargs["dependency_code"] = code
                else:
                    kwargs["supporting_visibility_result"] = (
                        evaluate_p023_visibility_for_subject(
                            analyzed_subject,
                            P023VisibilityInput(P023VisibilityState.NOT_VISIBLE),
                        )
                    )
                resolution = BoundedRecursiveAnalysisResolution(
                    analyzed_subject,
                    state,
                    f"Exact downstream reason for {state.value}.",
                    **kwargs,
                )
                result = kernel().analyze_bounded_manual_chart(
                    request_for(analyzed_subject, (p004_fact(),), operational_resolution=resolution)
                )
                self.assertIs(BoundedManualChartFinalSummary.UNRESOLVED, result.final_summary)
                self.assertIn(resolution.reason, result.unresolved_reasons)

    def test_uncertified_fatal_result_remains_unresolved(self) -> None:
        analyzed_subject = subject("uncertified")
        binding = binding_for(analyzed_subject, 3)
        result = kernel().analyze_bounded_manual_chart(
            request_for(
                analyzed_subject,
                (ManualDirectChildCardinalityFact(ManualCardinalityBehavior.TRIANGLE),),
                child_binding=binding,
            )
        )
        self.assertTrue(result.traceability[0].result_object.fatal_to_candidate)
        self.assertIs(BoundedManualChartFinalSummary.UNRESOLVED, result.final_summary)
        self.assertEqual((), result.structural_invalidity_certificates)
        self.assertIn("UNCERTIFIED_FATAL_RESULT_REQUIRES_CERTIFICATE", result.unresolved_reasons)

    def test_reviewed_state_requires_evaluation_and_has_no_validity_authority(self) -> None:
        reviewed = kernel().analyze_bounded_manual_chart(request_for(subject("reviewed"), (p004_fact(),)))
        zero = kernel().analyze_bounded_manual_chart(request_for(subject("not-reviewed")))
        self.assertIs(BoundedManualChartFinalSummary.CURRENT_SUPPLIED_SCOPE_REVIEWED, reviewed.final_summary)
        self.assertTrue(reviewed.candidate_analysis_result.verified_evaluations)
        self.assertIs(BoundedManualChartFinalSummary.UNRESOLVED, zero.final_summary)
        forbidden = {"valid", "complete", "family_valid", "preferred", "confidence", "rank"}
        self.assertTrue(forbidden.isdisjoint(BoundedManualChartAnalysisResult.__dataclass_fields__))
        with self.assertRaises(Exception):
            certify_validated_internal_family(reviewed)

    def test_coverage_is_canonical_exact_ten_and_not_supplied_is_never_pass(self) -> None:
        result = kernel().analyze_bounded_manual_chart(request_for(subject("coverage"), (p004_fact(),)))
        self.assertEqual(10, len(result.methodology_coverage))
        self.assertEqual(
            tuple(item.behavior_id for item in envelope_module._BEHAVIOR_COMPATIBILITY),
            tuple(item.behavior_id for item in result.methodology_coverage),
        )
        self.assertIs(BoundedManualChartCoverageState.SUPPLIED_AND_EXECUTED, result.methodology_coverage[0].state)
        self.assertTrue(all(item.state is BoundedManualChartCoverageState.NOT_SUPPLIED for item in result.methodology_coverage[1:]))
        self.assertEqual(
            {"behavior_id", "state", "_identity_snapshot"},
            set(kernel_package.BoundedManualChartCoverage.__dataclass_fields__),
        )
        self.assertNotIn("PASS", {state.value for state in BoundedManualChartCoverageState})

    def test_traceability_preserves_every_exact_identity(self) -> None:
        fact = p004_fact()
        result = kernel().analyze_bounded_manual_chart(request_for(subject("trace"), (fact,)))
        trace = result.traceability[0]
        build_input = result.manual_build_result.constructed_explicit_behavior_inputs[0]
        execution_record = result.explicit_execution_result.execution_records[0]
        evaluation = result.explicit_execution_result.methodology_evaluations[0]
        self.assertIs(fact, trace.manual_fact)
        self.assertIs(build_input, trace.explicit_input)
        self.assertIs(execution_record.result_object, trace.result_object)
        self.assertIs(evaluation, trace.evaluation)
        self.assertIs(result.explicit_execution_result.candidate_envelope, result.candidate_analysis_result.candidate_envelope)

    def test_cross_subject_fact_wrong_binding_and_unknown_fact_fail_as_infrastructure(self) -> None:
        analyzed_subject = subject("malformed")
        with self.assertRaises(Exception):
            request_for(
                analyzed_subject,
                (ManualP023VisibilityFact(subject("other"), P023VisibilityState.VISIBLE),),
            )
        with self.assertRaises(Exception):
            request_for(analyzed_subject, child_binding=binding_for(subject("other-binding"), 3))
        with self.assertRaises(Exception):
            request_for(analyzed_subject, (object(),))

    def test_low_level_mutation_fails_closed(self) -> None:
        fact = p004_fact()
        request = request_for(subject("mutation"), (fact,))
        object.__setattr__(fact, "wave1_origin_price", 999)
        with self.assertRaises(BoundedManualChartAnalysisError):
            kernel().analyze_bounded_manual_chart(request)
        result = kernel().analyze_bounded_manual_chart(request_for(subject("result-mutation"), (p004_fact(),)))
        object.__setattr__(result.candidate_analysis_result, "unresolved_reasons", ("changed",))
        with self.assertRaises(BoundedManualChartAnalysisError):
            copy.copy(result)

        coverage_result = kernel().analyze_bounded_manual_chart(
            request_for(subject("coverage-mutation"), (p004_fact(),))
        )
        object.__setattr__(
            coverage_result.methodology_coverage[0],
            "state",
            BoundedManualChartCoverageState.NOT_SUPPLIED,
        )
        with self.assertRaises(BoundedManualChartAnalysisError):
            copy.copy(coverage_result)

    def test_result_is_factory_only_immutable_and_nonserializable(self) -> None:
        result = kernel().analyze_bounded_manual_chart(request_for(subject("result")))
        with self.assertRaises(TypeError):
            BoundedManualChartAnalysisResult()
        with self.assertRaises(FrozenInstanceError):
            result.final_summary = BoundedManualChartFinalSummary.STRUCTURALLY_INVALID
        self.assertIs(result, copy.copy(result))
        self.assertIs(result, copy.deepcopy(result))
        with self.assertRaises(TypeError):
            pickle.dumps(result)

    def test_mapping_serialization_and_final_summary_injection_are_rejected(self) -> None:
        request = request_for(subject("mapping"), (p004_fact(),))
        with self.assertRaises(BoundedManualChartAnalysisError):
            kernel().analyze_bounded_manual_chart(asdict(request))
        field_names = {item.name for item in fields(BoundedManualChartAnalysisRequest)}
        for forbidden in ("validator", "constructor", "final_summary", "behavior_id", "module"):
            self.assertNotIn(forbidden, field_names)

    def test_api_boundaries_remain_distinct_and_legacy_is_unchanged(self) -> None:
        self.assertEqual(("self", "request"), tuple(inspect.signature(MethodologyKernel.analyze_bounded_manual_chart).parameters))
        self.assertEqual(("self", "request"), tuple(inspect.signature(MethodologyKernel.analyze_manual_candidate).parameters))
        self.assertIn("status=KernelStatus.NOT_IMPLEMENTED", inspect.getsource(MethodologyKernel.analyze))

    def test_no_discovery_external_capability_or_prohibited_vocabulary(self) -> None:
        path = support.SRC / "elliott_methodology_kernel" / "bounded_manual_chart_analysis.py"
        source_text = path.read_text(encoding="utf-8")
        tree = ast.parse(source_text, filename=str(path))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add("." * node.level + (node.module or ""))
        self.assertTrue({"socket", "subprocess", "requests", "urllib", "pathlib", "importlib"}.isdisjoint(imports))
        for forbidden in (
            "NormalizedMarketObservations", "Bar", "OHLCV", "TradingView", "RSI", "MACD",
            "EWO", "Fibonacci", "pivot detection", "wave discovery", "pattern inference",
            "family inference", "degree inference", "timeframe mapping", "PREFERRED",
            "ALTERNATIVE", "REMOTE", "certify_structural_invalidity(",
        ):
            self.assertNotIn(forbidden, source_text)

    def test_methodology_and_registry_inventories_remain_exact(self) -> None:
        observed = set()
        for path in (support.SRC / "elliott_methodology_kernel").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, (ast.Assign, ast.AnnAssign)):
                    targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
                    for target in targets:
                        if isinstance(target, ast.Name) and target.id.endswith(("BEHAVIOR_ID", "BEHAVIOR")) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                            observed.add(node.value.value)
        self.assertEqual(10, len(observed))
        self.assertTrue(structural_private._REGISTRY_SEALED)
        self.assertEqual(7, len(structural_private._PRODUCERS))
        self.assertTrue(family_private._REGISTRY_SEALED)
        self.assertEqual(0, len(family_private._PRODUCERS))
        self.assertEqual(0, len(family_private._ISSUED))


if __name__ == "__main__":
    unittest.main()
