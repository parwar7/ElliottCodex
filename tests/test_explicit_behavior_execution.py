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
import elliott_methodology_kernel.explicit_behavior_execution as execution_module
from elliott_methodology_kernel import (
    AnalysisResolutionState,
    AnalyzedWaveSubject,
    CandidateAnalysisEnvelope,
    CandidateObservationAttachment,
    CandidateScope,
    DegreePeerConsistencyInput,
    EndingDiagonalCandidateScope,
    EndingDiagonalCardinalityInput,
    ExplicitBehaviorExecutionError,
    ExplicitBehaviorExecutionRequest,
    ExplicitBehaviorExecutionResult,
    ExplicitBehaviorExecutionState,
    ExplicitBehaviorInput,
    ImpulseDirection,
    MethodologyKernel,
    MethodologyDependencyCode,
    OrderedChildBinding,
    P003OneLargerDegreeRelation,
    P003OneLargerDegreeThemeInput,
    P004Input,
    P007CandidateScope,
    P007SingleZigzagCardinalityInput,
    P008CandidateScope,
    P008FlatCardinalityInput,
    P009CandidateScope,
    P009TriangleCardinalityInput,
    P023VisibilityInput,
    P023VisibilityState,
    ParentChildDegreeInput,
    SingleCandidateExecutionSummary,
    SubjectBoundObservedPriceObservation,
    certify_structural_invalidity,
    certify_validated_internal_family,
    check_p009_triangle_cardinality,
)
from elliott_methodology_kernel.models import (
    DegreeStatus,
    DegreeTreeNode,
    InternalStatus,
)


def subject(name: str) -> AnalyzedWaveSubject:
    return AnalyzedWaveSubject(name, f"observations:{name}")


def binding_for(parent: AnalyzedWaveSubject, count: int = 3) -> OrderedChildBinding:
    return OrderedChildBinding(
        f"binding:{parent.subject_id}:{count}",
        parent,
        tuple(subject(f"{parent.subject_id}:child:{index}") for index in range(count)),
    )


def kernel() -> MethodologyKernel:
    return MethodologyKernel(support.PROTECTED_ROOT)


def request_for(
    analyzed_subject: AnalyzedWaveSubject,
    behavior_inputs: tuple[ExplicitBehaviorInput, ...] = (),
    *,
    child_binding: OrderedChildBinding | None = None,
    observations=(),
    operational_resolution=None,
    candidate_id: str = "candidate-one",
) -> ExplicitBehaviorExecutionRequest:
    return ExplicitBehaviorExecutionRequest(
        request_id="execution-request",
        requested_at_utc="2026-09-03T12:00:00Z",
        subject=analyzed_subject,
        candidate_id=candidate_id,
        child_binding=child_binding,
        behavior_inputs=behavior_inputs,
        observations=observations,
        operational_resolution=operational_resolution,
        provenance_refs=("request:explicit",),
    )


def p004_input() -> P004Input:
    return P004Input(CandidateScope.NORMAL_IMPULSE, ImpulseDirection.UP, 100, 101)


def peer_input() -> DegreePeerConsistencyInput:
    children = tuple(
        DegreeTreeNode(
            f"child-{index}",
            "Primary",
            DegreeStatus.RESOLVED,
            InternalStatus.CONFIRMED,
        )
        for index in range(2)
    )
    return DegreePeerConsistencyInput("parent", children)


def all_inputs(
    analyzed_subject: AnalyzedWaveSubject,
    child_binding: OrderedChildBinding,
) -> tuple[ExplicitBehaviorInput, ...]:
    triangle_input = P009TriangleCardinalityInput(
        P009CandidateScope.TRIANGLE,
        child_binding,
    )
    certificate = certify_structural_invalidity(
        check_p009_triangle_cardinality(triangle_input)
    )
    return (
        ExplicitBehaviorInput("P004_NORMAL_IMPULSE_WAVE2_ORIGIN", p004_input()),
        ExplicitBehaviorInput("DEGREE_DIRECT_CHILD_PEER_CONSISTENCY", peer_input()),
        ExplicitBehaviorInput(
            "PARENT_CHILD_DEGREE_ADJACENCY",
            ParentChildDegreeInput(
                "Primary",
                DegreeStatus.RESOLVED,
                "Intermediate",
                DegreeStatus.RESOLVED,
            ),
        ),
        ExplicitBehaviorInput(
            "P023_INTERNAL_VISIBILITY_GUARD",
            P023VisibilityInput(P023VisibilityState.VISIBLE),
        ),
        ExplicitBehaviorInput(
            "STRUCTURAL_INVALIDITY_EVIDENCE_NO_RESCUE",
            certificate,
        ),
        ExplicitBehaviorInput(
            "P003_ONE_LARGER_DEGREE_SEARCH_THEME",
            P003OneLargerDegreeThemeInput(P003OneLargerDegreeRelation.WITH),
        ),
        ExplicitBehaviorInput(
            "P007_SINGLE_ZIGZAG_DIRECT_CHILD_CARDINALITY",
            P007SingleZigzagCardinalityInput(
                P007CandidateScope.SINGLE_ZIGZAG,
                child_binding,
            ),
        ),
        ExplicitBehaviorInput(
            "P008_FLAT_DIRECT_CHILD_CARDINALITY",
            P008FlatCardinalityInput(P008CandidateScope.FLAT, child_binding),
        ),
        ExplicitBehaviorInput(
            "P009_TRIANGLE_DIRECT_CHILD_CARDINALITY",
            triangle_input,
        ),
        ExplicitBehaviorInput(
            "ENDING_DIAGONAL_DIRECT_CHILD_CARDINALITY",
            EndingDiagonalCardinalityInput(
                EndingDiagonalCandidateScope.ENDING_DIAGONAL,
                child_binding,
            ),
        ),
    )


class ExplicitBehaviorExecutionTests(unittest.TestCase):
    def test_exact_request_identity_metadata_immutability_and_pickle_boundary(self) -> None:
        analyzed_subject = subject("request")
        request = request_for(analyzed_subject, candidate_id="opaque-candidate")
        self.assertIs(analyzed_subject, request.subject)
        self.assertEqual("opaque-candidate", request.candidate_id)
        self.assertIs(request, copy.copy(request))
        self.assertIs(request, copy.deepcopy(request))
        with self.assertRaises(FrozenInstanceError):
            request.candidate_id = "changed"
        with self.assertRaises(TypeError):
            pickle.dumps(request)

    def test_mapping_duck_and_subclass_request_cannot_execute(self) -> None:
        class Duck:
            behavior_inputs = ()

        with self.assertRaises(TypeError):
            type("RequestSubclass", (ExplicitBehaviorExecutionRequest,), {})
        for value in ({"behavior_inputs": ()}, Duck(), object()):
            with self.subTest(kind=type(value).__name__):
                with self.assertRaises(ExplicitBehaviorExecutionError):
                    kernel().analyze_candidate_inputs(value)

    def test_dispatch_is_exact_complete_immutable_and_uses_reviewed_callables(self) -> None:
        import elliott_methodology_kernel.bounded_recursive_analysis as bounded
        import elliott_methodology_kernel.degree_peer_consistency as peer
        import elliott_methodology_kernel.ending_diagonal_cardinality as diagonal
        import elliott_methodology_kernel.p003_one_larger_degree_theme as p003
        import elliott_methodology_kernel.p004 as p004
        import elliott_methodology_kernel.p007_single_zigzag_cardinality as p007
        import elliott_methodology_kernel.p008_flat_cardinality as p008
        import elliott_methodology_kernel.p009_triangle_cardinality as p009
        import elliott_methodology_kernel.parent_child_degree_adjacency as parent_child
        import elliott_methodology_kernel.structural_invalidity_evidence_no_rescue as no_rescue

        expected = (
            ("P004_NORMAL_IMPULSE_WAVE2_ORIGIN", P004Input, p004.check_p004),
            ("DEGREE_DIRECT_CHILD_PEER_CONSISTENCY", DegreePeerConsistencyInput, peer.check_degree_peer_consistency),
            ("PARENT_CHILD_DEGREE_ADJACENCY", ParentChildDegreeInput, parent_child.check_parent_child_degree_adjacency),
            ("P023_INTERNAL_VISIBILITY_GUARD", P023VisibilityInput, bounded.evaluate_p023_visibility_for_subject),
            ("STRUCTURAL_INVALIDITY_EVIDENCE_NO_RESCUE", kernel_package.CertifiedStructuralInvalidity, no_rescue.apply_structural_invalidity_evidence_no_rescue),
            ("P003_ONE_LARGER_DEGREE_SEARCH_THEME", P003OneLargerDegreeThemeInput, p003.map_p003_one_larger_degree_theme),
            ("P007_SINGLE_ZIGZAG_DIRECT_CHILD_CARDINALITY", P007SingleZigzagCardinalityInput, p007.check_p007_single_zigzag_cardinality),
            ("P008_FLAT_DIRECT_CHILD_CARDINALITY", P008FlatCardinalityInput, p008.check_p008_flat_cardinality),
            ("P009_TRIANGLE_DIRECT_CHILD_CARDINALITY", P009TriangleCardinalityInput, p009.check_p009_triangle_cardinality),
            ("ENDING_DIAGONAL_DIRECT_CHILD_CARDINALITY", EndingDiagonalCardinalityInput, diagonal.check_ending_diagonal_cardinality),
        )
        self.assertIsInstance(execution_module._EXECUTION_DISPATCH, tuple)
        self.assertEqual(10, len(execution_module._EXECUTION_DISPATCH))
        for observed, (behavior_id, input_type, validator) in zip(
            execution_module._EXECUTION_DISPATCH,
            expected,
            strict=True,
        ):
            self.assertEqual(behavior_id, observed.behavior_id)
            self.assertIs(input_type, observed.input_type)
            self.assertIs(validator, observed.validator)
            with self.assertRaises(FrozenInstanceError):
                observed.validator = object()

    def test_unknown_wrong_mapping_duck_and_subclass_input_fail_closed(self) -> None:
        class Duck:
            candidate_scope = CandidateScope.NORMAL_IMPULSE

        class P004Subclass(P004Input):
            pass

        cases = (
            ("UNKNOWN", p004_input()),
            ("P004_NORMAL_IMPULSE_WAVE2_ORIGIN", {"wave1_origin": 100}),
            ("P004_NORMAL_IMPULSE_WAVE2_ORIGIN", Duck()),
            ("P004_NORMAL_IMPULSE_WAVE2_ORIGIN", P004Subclass(*p004_input().__dict__.values()) if hasattr(p004_input(), "__dict__") else P004Subclass(CandidateScope.NORMAL_IMPULSE, ImpulseDirection.UP, 100, 101)),
        )
        for behavior_id, input_object in cases:
            with self.subTest(behavior_id=behavior_id, kind=type(input_object).__name__):
                with self.assertRaises(ExplicitBehaviorExecutionError):
                    ExplicitBehaviorInput(behavior_id, input_object)

    def test_callers_cannot_supply_validator_result_type_or_dynamic_name(self) -> None:
        field_names = {item.name for item in fields(ExplicitBehaviorInput)}
        self.assertEqual(
            {"behavior_id", "input_object", "provenance_refs", "_input_snapshot", "_identity_snapshot"},
            field_names,
        )
        for forbidden in ("validator", "callable", "module", "class_name", "result_type", "certifier"):
            self.assertNotIn(forbidden, field_names)
        with self.assertRaises(TypeError):
            ExplicitBehaviorInput(
                "P004_NORMAL_IMPULSE_WAVE2_ORIGIN",
                p004_input(),
                validator="evil.module.callable",
            )

    def test_all_ten_inputs_execute_in_caller_order_with_exact_identities(self) -> None:
        analyzed_subject = subject("all-ten")
        child_binding = binding_for(analyzed_subject, 3)
        inputs = all_inputs(analyzed_subject, child_binding)
        result = kernel().analyze_candidate_inputs(
            request_for(analyzed_subject, inputs, child_binding=child_binding)
        )
        self.assertEqual(10, len(result.execution_records))
        self.assertEqual(10, len(result.methodology_evaluations))
        self.assertEqual(
            tuple(item.behavior_id for item in inputs),
            tuple(item.behavior_id for item in result.execution_records),
        )
        for supplied, record, evaluation in zip(
            inputs,
            result.execution_records,
            result.methodology_evaluations,
            strict=True,
        ):
            self.assertIs(ExplicitBehaviorExecutionState.EXECUTED, record.execution_state)
            self.assertIs(supplied.input_object, record.input_object)
            self.assertIs(record.result_object, evaluation.result_object)
            self.assertIs(supplied.input_object, evaluation.input_object)
        self.assertIs(result.candidate_envelope.methodology_evaluations, result.methodology_evaluations)
        self.assertIs(result.candidate_envelope, result.single_candidate_analysis_result.candidate_envelope)
        self.assertIs(
            SingleCandidateExecutionSummary.STRUCTURALLY_INVALID,
            result.single_candidate_analysis_result.execution_summary,
        )

    def test_p023_uses_exact_existing_subject_bound_wrapper(self) -> None:
        analyzed_subject = subject("p023")
        supplied = ExplicitBehaviorInput(
            "P023_INTERNAL_VISIBILITY_GUARD",
            P023VisibilityInput(P023VisibilityState.VISIBLE),
        )
        result = kernel().analyze_candidate_inputs(request_for(analyzed_subject, (supplied,)))
        wrapped = result.execution_records[0].result_object
        self.assertIs(kernel_package.SubjectBoundP023VisibilityResult, type(wrapped))
        self.assertIs(analyzed_subject, wrapped.subject)
        self.assertIs(wrapped, result.methodology_evaluations[0].result_object)

    def test_no_rescue_executes_only_with_genuine_exact_certificate(self) -> None:
        analyzed_subject = subject("no-rescue")
        child_binding = binding_for(analyzed_subject, 3)
        triangle = P009TriangleCardinalityInput(P009CandidateScope.TRIANGLE, child_binding)
        certificate = certify_structural_invalidity(check_p009_triangle_cardinality(triangle))
        supplied = ExplicitBehaviorInput(
            "STRUCTURAL_INVALIDITY_EVIDENCE_NO_RESCUE",
            certificate,
        )
        result = kernel().analyze_candidate_inputs(
            request_for(analyzed_subject, (supplied,), child_binding=child_binding)
        )
        self.assertIs(certificate, result.execution_records[0].input_object)
        self.assertIs(
            certificate,
            result.execution_records[0].result_object.originating_invalidity,
        )
        for invalid in (object(), asdict(check_p009_triangle_cardinality(triangle))):
            with self.assertRaises(ExplicitBehaviorExecutionError):
                ExplicitBehaviorInput("STRUCTURAL_INVALIDITY_EVIDENCE_NO_RESCUE", invalid)

    def test_missing_no_rescue_certificate_is_dependency_block_not_methodology(self) -> None:
        analyzed_subject = subject("missing-certificate")
        supplied = ExplicitBehaviorInput(
            "STRUCTURAL_INVALIDITY_EVIDENCE_NO_RESCUE",
            None,
        )
        result = kernel().analyze_candidate_inputs(request_for(analyzed_subject, (supplied,)))
        record = result.execution_records[0]
        self.assertIs(
            ExplicitBehaviorExecutionState.BLOCKED_MISSING_TRUSTED_DEPENDENCY,
            record.execution_state,
        )
        self.assertIsNone(record.result_object)
        self.assertEqual(
            (execution_module.MISSING_TRUSTED_INVALIDITY_CERTIFICATE,),
            result.execution_unresolved_reasons,
        )
        self.assertIsNone(result.single_candidate_analysis_result)
        self.assertEqual((), result.methodology_evaluations)

    def test_missing_input_is_not_accepted_for_other_behaviors(self) -> None:
        with self.assertRaises(ExplicitBehaviorExecutionError):
            ExplicitBehaviorInput("P004_NORMAL_IMPULSE_WAVE2_ORIGIN", None)

    def test_cross_subject_binding_and_certificate_fail_before_validator_execution(self) -> None:
        analyzed_subject = subject("target")
        other = subject("other")
        other_binding = binding_for(other, 3)
        cardinality = ExplicitBehaviorInput(
            "P007_SINGLE_ZIGZAG_DIRECT_CHILD_CARDINALITY",
            P007SingleZigzagCardinalityInput(P007CandidateScope.SINGLE_ZIGZAG, other_binding),
        )
        with self.assertRaises(Exception):
            request_for(analyzed_subject, (cardinality,), child_binding=other_binding)

        triangle = P009TriangleCardinalityInput(P009CandidateScope.TRIANGLE, other_binding)
        certificate = certify_structural_invalidity(check_p009_triangle_cardinality(triangle))
        no_rescue = ExplicitBehaviorInput(
            "STRUCTURAL_INVALIDITY_EVIDENCE_NO_RESCUE",
            certificate,
        )
        with self.assertRaises(Exception):
            request_for(analyzed_subject, (no_rescue,), child_binding=other_binding)

    def test_cardinality_requires_request_exact_binding_and_order(self) -> None:
        analyzed_subject = subject("binding")
        binding = binding_for(analyzed_subject, 3)
        lookalike = OrderedChildBinding(
            binding.binding_id,
            analyzed_subject,
            binding.ordered_children,
        )
        supplied = ExplicitBehaviorInput(
            "P007_SINGLE_ZIGZAG_DIRECT_CHILD_CARDINALITY",
            P007SingleZigzagCardinalityInput(P007CandidateScope.SINGLE_ZIGZAG, binding),
        )
        with self.assertRaises(ExplicitBehaviorExecutionError):
            request_for(analyzed_subject, (supplied,), child_binding=lookalike)
        reversed_binding = OrderedChildBinding(
            "reversed",
            analyzed_subject,
            tuple(reversed(binding.ordered_children)),
        )
        with self.assertRaises(ExplicitBehaviorExecutionError):
            request_for(analyzed_subject, (supplied,), child_binding=reversed_binding)

    def test_binding_is_never_synthesized(self) -> None:
        analyzed_subject = subject("no-binding")
        binding = binding_for(analyzed_subject, 3)
        supplied = ExplicitBehaviorInput(
            "P008_FLAT_DIRECT_CHILD_CARDINALITY",
            P008FlatCardinalityInput(P008CandidateScope.FLAT, binding),
        )
        with self.assertRaises(ExplicitBehaviorExecutionError):
            request_for(analyzed_subject, (supplied,))

    def test_duplicate_identity_rejected_distinct_inputs_preserve_order_without_ranking(self) -> None:
        analyzed_subject = subject("duplicates")
        first_input = p004_input()
        duplicate = ExplicitBehaviorInput("P004_NORMAL_IMPULSE_WAVE2_ORIGIN", first_input)
        with self.assertRaises(ExplicitBehaviorExecutionError):
            request_for(analyzed_subject, (duplicate, duplicate))
        second = ExplicitBehaviorInput("P004_NORMAL_IMPULSE_WAVE2_ORIGIN", p004_input())
        result = kernel().analyze_candidate_inputs(request_for(analyzed_subject, (duplicate, second)))
        self.assertIs(first_input, result.execution_records[0].input_object)
        self.assertIs(second.input_object, result.execution_records[1].input_object)
        self.assertNotIn("rank", ExplicitBehaviorExecutionResult.__dataclass_fields__)

    def test_observation_and_operational_resolution_are_exact_transport(self) -> None:
        analyzed_subject = subject("transport")
        observation = CandidateObservationAttachment(
            analyzed_subject,
            SubjectBoundObservedPriceObservation(analyzed_subject, 100, "price:manual"),
        )
        supplied = ExplicitBehaviorInput("P004_NORMAL_IMPULSE_WAVE2_ORIGIN", p004_input())
        resolution = kernel_package.BoundedRecursiveAnalysisResolution(
            analyzed_subject,
            AnalysisResolutionState.UNRESOLVED_METHODOLOGY_DEPENDENCY,
            "An explicit methodology dependency remains unresolved.",
            dependency_code=MethodologyDependencyCode.FAMILY_PRODUCER_UNAVAILABLE,
        )
        result = kernel().analyze_candidate_inputs(
            request_for(
                analyzed_subject,
                (supplied,),
                observations=(observation,),
                operational_resolution=resolution,
            )
        )
        self.assertIs(observation, result.candidate_envelope.observations[0])
        self.assertIs(resolution, result.candidate_envelope.operational_resolution)
        self.assertIs(
            SingleCandidateExecutionSummary.UNRESOLVED,
            result.single_candidate_analysis_result.execution_summary,
        )

    def test_zero_inputs_delegates_to_existing_conservative_summary(self) -> None:
        analyzed_subject = subject("zero")
        result = kernel().analyze_candidate_inputs(request_for(analyzed_subject))
        self.assertEqual((), result.methodology_evaluations)
        self.assertEqual((), result.execution_records)
        self.assertIs(
            SingleCandidateExecutionSummary.UNRESOLVED,
            result.single_candidate_analysis_result.execution_summary,
        )
        self.assertEqual(
            ("NO_METHODOLOGY_EVALUATIONS_SUPPLIED",),
            result.single_candidate_analysis_result.unresolved_reasons,
        )

    def test_structural_violation_is_not_automatically_certified(self) -> None:
        analyzed_subject = subject("no-auto-cert")
        binding = binding_for(analyzed_subject, 3)
        supplied = ExplicitBehaviorInput(
            "P009_TRIANGLE_DIRECT_CHILD_CARDINALITY",
            P009TriangleCardinalityInput(P009CandidateScope.TRIANGLE, binding),
        )
        result = kernel().analyze_candidate_inputs(
            request_for(analyzed_subject, (supplied,), child_binding=binding)
        )
        self.assertTrue(result.execution_records[0].result_object.fatal_to_candidate)
        self.assertEqual(
            (),
            result.single_candidate_analysis_result.structural_invalidity_certificates,
        )
        self.assertIs(
            SingleCandidateExecutionSummary.UNRESOLVED,
            result.single_candidate_analysis_result.execution_summary,
        )

    def test_low_level_input_and_result_mutation_fail_closed(self) -> None:
        analyzed_subject = subject("mutation")
        methodology_input = p004_input()
        supplied = ExplicitBehaviorInput("P004_NORMAL_IMPULSE_WAVE2_ORIGIN", methodology_input)
        request = request_for(analyzed_subject, (supplied,))
        object.__setattr__(methodology_input, "wave1_origin", 999)
        with self.assertRaises(ExplicitBehaviorExecutionError):
            kernel().analyze_candidate_inputs(request)

        clean = ExplicitBehaviorInput("P004_NORMAL_IMPULSE_WAVE2_ORIGIN", p004_input())
        result = kernel().analyze_candidate_inputs(request_for(analyzed_subject, (clean,)))
        object.__setattr__(result.execution_records[0].result_object, "reason", "changed")
        with self.assertRaises(ExplicitBehaviorExecutionError):
            copy.copy(result)

    def test_result_is_factory_only_immutable_identity_and_nonserializable(self) -> None:
        result = kernel().analyze_candidate_inputs(request_for(subject("result")))
        with self.assertRaises(TypeError):
            ExplicitBehaviorExecutionResult()
        with self.assertRaises(FrozenInstanceError):
            result.request_id = "changed"
        self.assertIs(result, copy.copy(result))
        self.assertIs(result, copy.deepcopy(result))
        with self.assertRaises(TypeError):
            pickle.dumps(result)

        blocked = kernel().analyze_candidate_inputs(
            request_for(
                subject("blocked-record"),
                (
                    ExplicitBehaviorInput(
                        "STRUCTURAL_INVALIDITY_EVIDENCE_NO_RESCUE",
                        None,
                    ),
                ),
            )
        )
        object.__setattr__(blocked.execution_records[0], "reason", "changed")
        with self.assertRaises(ExplicitBehaviorExecutionError):
            copy.copy(blocked)

    def test_candidate_id_and_serialized_data_create_no_authority(self) -> None:
        analyzed_subject = subject("metadata")
        first = request_for(analyzed_subject, candidate_id="same")
        second = request_for(subject("other-metadata"), candidate_id="same")
        self.assertEqual(first.candidate_id, second.candidate_id)
        self.assertIsNot(first.subject, second.subject)
        with self.assertRaises(ExplicitBehaviorExecutionError):
            kernel().analyze_candidate_inputs(asdict(first))

    def test_legacy_api_and_existing_candidate_orchestration_are_not_overloaded(self) -> None:
        self.assertEqual(("self", "request"), tuple(inspect.signature(MethodologyKernel.analyze).parameters))
        self.assertEqual(("self", "request"), tuple(inspect.signature(MethodologyKernel.analyze_candidate).parameters))
        self.assertEqual(("self", "request"), tuple(inspect.signature(MethodologyKernel.analyze_candidate_inputs).parameters))
        self.assertIn("status=KernelStatus.NOT_IMPLEMENTED", inspect.getsource(MethodologyKernel.analyze))

    def test_public_surface_is_narrow_and_cannot_certify_family(self) -> None:
        expected = {
            "ExplicitBehaviorExecutionError",
            "ExplicitBehaviorExecutionRecord",
            "ExplicitBehaviorExecutionRequest",
            "ExplicitBehaviorExecutionResult",
            "ExplicitBehaviorExecutionState",
            "ExplicitBehaviorInput",
        }
        self.assertTrue(expected.issubset(set(kernel_package.__all__)))
        result = kernel().analyze_candidate_inputs(request_for(subject("family")))
        with self.assertRaises(Exception):
            certify_validated_internal_family(result)
        self.assertTrue(family_private._REGISTRY_SEALED)
        self.assertEqual(0, len(family_private._PRODUCERS))
        self.assertEqual(0, len(family_private._ISSUED))

    def test_no_discovery_external_capability_or_methodology_vocabulary_added(self) -> None:
        path = support.SRC / "elliott_methodology_kernel" / "explicit_behavior_execution.py"
        source_text = path.read_text(encoding="utf-8")
        tree = ast.parse(source_text, filename=str(path))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add("." * node.level + (node.module or ""))
        self.assertTrue(
            {"socket", "subprocess", "requests", "urllib", "pathlib", "importlib"}.isdisjoint(imports)
        )
        for forbidden in (
            "TradingView", "RSI", "MACD", "EWO", "Fibonacci", "OHLCV",
            "pivot detection", "wave discovery", "wave label", "degree inference",
            "timeframe mapping", "PREFERRED", "ALTERNATIVE", "REMOTE", "trade",
            "certify_structural_invalidity(", "certify_validated_internal_family(",
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
                        if (
                            isinstance(target, ast.Name)
                            and target.id.endswith(("BEHAVIOR_ID", "BEHAVIOR"))
                            and isinstance(node.value, ast.Constant)
                            and isinstance(node.value.value, str)
                        ):
                            observed.add(node.value.value)
        self.assertEqual(10, len(observed))
        self.assertTrue(structural_private._REGISTRY_SEALED)
        self.assertEqual(7, len(structural_private._PRODUCERS))
        self.assertTrue(family_private._REGISTRY_SEALED)
        self.assertEqual(0, len(family_private._PRODUCERS))
        self.assertEqual(0, len(family_private._ISSUED))


if __name__ == "__main__":
    unittest.main()
