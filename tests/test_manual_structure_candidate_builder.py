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
import elliott_methodology_kernel.manual_structure_candidate_builder as builder_module
from elliott_methodology_kernel import (
    AnalyzedWaveSubject,
    CandidateScope,
    ExplicitBehaviorExecutionResult,
    ExplicitBehaviorInput,
    ImpulseDirection,
    ManualCardinalityBehavior,
    ManualDegreePeerFact,
    ManualDirectChildCardinalityFact,
    ManualP003OneLargerDegreeRelationFact,
    ManualP004Wave2OriginFact,
    ManualP023VisibilityFact,
    ManualParentChildDegreeFact,
    ManualStructureCandidateBuildResult,
    ManualStructureCandidateBuilderError,
    ManualStructureCandidateRequest,
    MethodologyKernel,
    OrderedChildBinding,
    P003OneLargerDegreeRelation,
    P007CandidateScope,
    P007SingleZigzagCardinalityInput,
    P009CandidateScope,
    P009TriangleCardinalityInput,
    P023VisibilityState,
    SingleCandidateAnalysisResult,
    SingleCandidateExecutionSummary,
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


def children(parent: AnalyzedWaveSubject, count: int) -> tuple[AnalyzedWaveSubject, ...]:
    return tuple(subject(f"{parent.subject_id}:child:{index}") for index in range(count))


def binding_for(parent: AnalyzedWaveSubject, count: int = 3) -> OrderedChildBinding:
    return OrderedChildBinding(f"binding:{parent.subject_id}:{count}", parent, children(parent, count))


def kernel() -> MethodologyKernel:
    return MethodologyKernel(support.PROTECTED_ROOT)


def request_for(
    analyzed_subject: AnalyzedWaveSubject,
    facts=(),
    *,
    child_binding=None,
    ordered_child_subjects=None,
    constructed_binding_id=None,
    certificates=(),
    candidate_id="manual-candidate",
) -> ManualStructureCandidateRequest:
    return ManualStructureCandidateRequest(
        request_id="manual-request",
        requested_at_utc="2026-09-03T12:00:00Z",
        subject=analyzed_subject,
        candidate_id=candidate_id,
        manual_behavior_facts=facts,
        child_binding=child_binding,
        ordered_child_subjects=ordered_child_subjects,
        constructed_binding_id=constructed_binding_id,
        trusted_invalidity_certificates=certificates,
        provenance_refs=("manual:reviewed",),
    )


def p004_fact() -> ManualP004Wave2OriginFact:
    return ManualP004Wave2OriginFact(
        CandidateScope.NORMAL_IMPULSE,
        ImpulseDirection.UP,
        100,
        101,
    )


def peer_fact() -> ManualDegreePeerFact:
    peer_nodes = tuple(
        DegreeTreeNode(
            f"peer-{index}",
            "Primary",
            DegreeStatus.RESOLVED,
            InternalStatus.CONFIRMED,
        )
        for index in range(2)
    )
    return ManualDegreePeerFact("parent", peer_nodes)


class ManualStructureCandidateBuilderTests(unittest.TestCase):
    def test_exact_request_retains_subject_metadata_identity_and_is_nonserializable(self) -> None:
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

    def test_mapping_duck_subclass_and_unknown_request_or_fact_fail_closed(self) -> None:
        class Duck:
            manual_behavior_facts = ()

        with self.assertRaises(TypeError):
            type("RequestSubclass", (ManualStructureCandidateRequest,), {})
        for supplied in ({"manual_behavior_facts": ()}, Duck(), object()):
            with self.subTest(kind=type(supplied).__name__):
                with self.assertRaises(ManualStructureCandidateBuilderError):
                    kernel().analyze_manual_candidate(supplied)
        for fact in ({"direction": "UP"}, Duck(), object()):
            with self.subTest(fact=type(fact).__name__):
                with self.assertRaises(ManualStructureCandidateBuilderError):
                    request_for(subject("bad-fact"), (fact,))

    def test_fact_types_are_exact_sealed_classified_and_nonserializable(self) -> None:
        fact = p004_fact()
        self.assertEqual(
            "CALLER_SUPPLIED_STRUCTURAL_FACT",
            fact.fact_classification,
        )
        self.assertIs(fact, copy.copy(fact))
        with self.assertRaises(TypeError):
            pickle.dumps(fact)
        with self.assertRaises(TypeError):
            type("FactSubclass", (ManualP004Wave2OriginFact,), {})

    def test_p004_fact_builds_exact_input_values_and_existing_validator_result(self) -> None:
        analyzed_subject = subject("p004")
        fact = p004_fact()
        result = kernel().analyze_manual_candidate(request_for(analyzed_subject, (fact,)))
        explicit = result.constructed_explicit_behavior_inputs[0]
        self.assertEqual("P004_NORMAL_IMPULSE_WAVE2_ORIGIN", explicit.behavior_id)
        self.assertIs(kernel_package.P004Input, type(explicit.input_object))
        self.assertIs(fact.candidate_scope, explicit.input_object.candidate_scope)
        self.assertIs(fact.direction, explicit.input_object.direction)
        self.assertEqual(100, explicit.input_object.wave1_origin)
        self.assertEqual(101, explicit.input_object.wave2_retracement_extreme)
        evaluation = result.delegated_execution_result.methodology_evaluations[0]
        self.assertIs(explicit.input_object, evaluation.input_object)
        self.assertIs(kernel_package.P004Result, type(evaluation.result_object))

    def test_degree_peer_fact_builds_exact_input_without_inference(self) -> None:
        analyzed_subject = subject("peer")
        fact = peer_fact()
        result = kernel().analyze_manual_candidate(request_for(analyzed_subject, (fact,)))
        explicit = result.constructed_explicit_behavior_inputs[0]
        self.assertIs(kernel_package.DegreePeerConsistencyInput, type(explicit.input_object))
        self.assertIs(fact.direct_child_degrees, explicit.input_object.direct_child_degrees)
        self.assertEqual("RULE_SATISFIED", result.delegated_execution_result.execution_records[0].result_object.status.value)

    def test_parent_child_degree_fact_builds_exact_input_without_timeframe_mapping(self) -> None:
        analyzed_subject = subject("parent-child")
        fact = ManualParentChildDegreeFact(
            "Primary",
            DegreeStatus.RESOLVED,
            "Intermediate",
            DegreeStatus.RESOLVED,
        )
        result = kernel().analyze_manual_candidate(request_for(analyzed_subject, (fact,)))
        built = result.constructed_explicit_behavior_inputs[0].input_object
        self.assertIs(kernel_package.ParentChildDegreeInput, type(built))
        self.assertEqual("Primary", built.parent_degree)
        self.assertEqual("Intermediate", built.child_degree)
        self.assertEqual("RULE_SATISFIED", result.delegated_execution_result.execution_records[0].result_object.status.value)

    def test_p023_fact_uses_exact_visibility_and_subject_bound_execution(self) -> None:
        analyzed_subject = subject("p023")
        fact = ManualP023VisibilityFact(analyzed_subject, P023VisibilityState.UNKNOWN)
        result = kernel().analyze_manual_candidate(request_for(analyzed_subject, (fact,)))
        explicit = result.constructed_explicit_behavior_inputs[0]
        self.assertIs(kernel_package.P023VisibilityInput, type(explicit.input_object))
        self.assertIs(P023VisibilityState.UNKNOWN, explicit.input_object.visibility_state)
        wrapped = result.delegated_execution_result.execution_records[0].result_object
        self.assertIs(kernel_package.SubjectBoundP023VisibilityResult, type(wrapped))
        self.assertIs(analyzed_subject, wrapped.subject)

    def test_cross_subject_p023_manual_fact_fails_closed(self) -> None:
        with self.assertRaises(ManualStructureCandidateBuilderError):
            request_for(
                subject("p023-target"),
                (
                    ManualP023VisibilityFact(
                        subject("p023-other"),
                        P023VisibilityState.VISIBLE,
                    ),
                ),
            )

    def test_p003_fact_requires_exact_relation_and_builds_existing_input(self) -> None:
        analyzed_subject = subject("p003")
        fact = ManualP003OneLargerDegreeRelationFact(P003OneLargerDegreeRelation.AGAINST)
        result = kernel().analyze_manual_candidate(request_for(analyzed_subject, (fact,)))
        built = result.constructed_explicit_behavior_inputs[0].input_object
        self.assertIs(kernel_package.P003OneLargerDegreeThemeInput, type(built))
        self.assertIs(P003OneLargerDegreeRelation.AGAINST, built.relation_to_one_larger_degree)
        self.assertEqual("CORRECTIVE", result.delegated_execution_result.execution_records[0].result_object.theme.value)
        with self.assertRaises(ManualStructureCandidateBuilderError):
            ManualP003OneLargerDegreeRelationFact("AGAINST")

    def test_each_explicit_cardinality_selector_builds_only_its_one_input(self) -> None:
        expected = {
            ManualCardinalityBehavior.SINGLE_ZIGZAG: (
                "P007_SINGLE_ZIGZAG_DIRECT_CHILD_CARDINALITY",
                kernel_package.P007SingleZigzagCardinalityInput,
            ),
            ManualCardinalityBehavior.FLAT: (
                "P008_FLAT_DIRECT_CHILD_CARDINALITY",
                kernel_package.P008FlatCardinalityInput,
            ),
            ManualCardinalityBehavior.TRIANGLE: (
                "P009_TRIANGLE_DIRECT_CHILD_CARDINALITY",
                kernel_package.P009TriangleCardinalityInput,
            ),
            ManualCardinalityBehavior.ENDING_DIAGONAL: (
                "ENDING_DIAGONAL_DIRECT_CHILD_CARDINALITY",
                kernel_package.EndingDiagonalCardinalityInput,
            ),
        }
        for selector, (behavior_id, input_type) in expected.items():
            with self.subTest(selector=selector):
                analyzed_subject = subject(selector.value)
                binding = binding_for(analyzed_subject, 3)
                fact = ManualDirectChildCardinalityFact(selector)
                result = kernel().analyze_manual_candidate(
                    request_for(analyzed_subject, (fact,), child_binding=binding)
                )
                self.assertEqual(1, len(result.constructed_explicit_behavior_inputs))
                explicit = result.constructed_explicit_behavior_inputs[0]
                self.assertEqual(behavior_id, explicit.behavior_id)
                self.assertIs(input_type, type(explicit.input_object))
                self.assertIs(binding, explicit.input_object.binding)

    def test_child_count_alone_infers_no_behavior_for_three_or_five_children(self) -> None:
        for count in (3, 5):
            with self.subTest(count=count):
                analyzed_subject = subject(f"count-{count}")
                result = kernel().analyze_manual_candidate(
                    request_for(analyzed_subject, child_binding=binding_for(analyzed_subject, count))
                )
                self.assertEqual((), result.constructed_explicit_behavior_inputs)
                self.assertEqual((), result.delegated_execution_result.methodology_evaluations)
                self.assertIs(
                    SingleCandidateExecutionSummary.UNRESOLVED,
                    result.single_candidate_analysis_result.execution_summary,
                )

    def test_builder_constructs_binding_from_exact_ordered_children_without_reordering(self) -> None:
        analyzed_subject = subject("construct-binding")
        ordered = children(analyzed_subject, 3)
        fact = ManualDirectChildCardinalityFact(ManualCardinalityBehavior.SINGLE_ZIGZAG)
        result = kernel().analyze_manual_candidate(
            request_for(
                analyzed_subject,
                (fact,),
                ordered_child_subjects=ordered,
                constructed_binding_id="manual-binding",
            )
        )
        binding = result.constructed_child_binding
        self.assertIs(binding, result.effective_child_binding)
        self.assertIs(binding, result.delegated_execution_result.candidate_envelope.child_binding)
        self.assertIs(ordered, binding.ordered_children)
        self.assertEqual("manual-binding", binding.binding_id)
        self.assertIs(binding, result.constructed_explicit_behavior_inputs[0].input_object.binding)

    def test_existing_binding_is_retained_and_not_reported_as_constructed(self) -> None:
        analyzed_subject = subject("existing-binding")
        binding = binding_for(analyzed_subject, 3)
        result = kernel().analyze_manual_candidate(request_for(analyzed_subject, child_binding=binding))
        self.assertIs(binding, result.effective_child_binding)
        self.assertIsNone(result.constructed_child_binding)

    def test_ambiguous_or_cross_subject_binding_inputs_fail_closed(self) -> None:
        analyzed_subject = subject("binding-errors")
        binding = binding_for(analyzed_subject, 3)
        with self.assertRaises(ManualStructureCandidateBuilderError):
            request_for(
                analyzed_subject,
                child_binding=binding,
                ordered_child_subjects=binding.ordered_children,
                constructed_binding_id="duplicate-source",
            )
        with self.assertRaises(Exception):
            request_for(analyzed_subject, child_binding=binding_for(subject("other"), 3))
        with self.assertRaises(ManualStructureCandidateBuilderError):
            kernel().analyze_manual_candidate(
                request_for(
                    analyzed_subject,
                    (ManualDirectChildCardinalityFact(ManualCardinalityBehavior.FLAT),),
                )
            )

    def test_no_rescue_is_not_constructible_from_manual_facts(self) -> None:
        mapped_behaviors = {item.behavior_id for item in builder_module._MANUAL_FACT_BUILDERS}
        self.assertNotIn("STRUCTURAL_INVALIDITY_EVIDENCE_NO_RESCUE", mapped_behaviors)
        for fact_type in builder_module._MANUAL_FACT_TYPES:
            self.assertFalse(issubclass(fact_type, kernel_package.CertifiedStructuralInvalidity))

    def test_genuine_existing_certificate_passes_through_without_synthesis(self) -> None:
        analyzed_subject = subject("certificate")
        binding = binding_for(analyzed_subject, 3)
        triangle = P009TriangleCardinalityInput(P009CandidateScope.TRIANGLE, binding)
        certificate = certify_structural_invalidity(check_p009_triangle_cardinality(triangle))
        result = kernel().analyze_manual_candidate(
            request_for(analyzed_subject, child_binding=binding, certificates=(certificate,))
        )
        explicit = result.constructed_explicit_behavior_inputs[0]
        self.assertEqual("STRUCTURAL_INVALIDITY_EVIDENCE_NO_RESCUE", explicit.behavior_id)
        self.assertIs(certificate, explicit.input_object)
        self.assertIs(
            certificate,
            result.delegated_execution_result.execution_records[0].result_object.originating_invalidity,
        )
        self.assertIs(
            SingleCandidateExecutionSummary.STRUCTURALLY_INVALID,
            result.single_candidate_analysis_result.execution_summary,
        )

    def test_fake_and_cross_subject_certificate_fail_as_infrastructure(self) -> None:
        analyzed_subject = subject("certificate-target")
        with self.assertRaises(ManualStructureCandidateBuilderError):
            request_for(analyzed_subject, certificates=(object(),))
        other = subject("certificate-other")
        binding = binding_for(other, 3)
        certificate = certify_structural_invalidity(
            check_p009_triangle_cardinality(
                P009TriangleCardinalityInput(P009CandidateScope.TRIANGLE, binding)
            )
        )
        with self.assertRaises(ManualStructureCandidateBuilderError):
            request_for(analyzed_subject, child_binding=binding, certificates=(certificate,))

    def test_pipeline_retains_exact_explicit_execution_and_single_candidate_results(self) -> None:
        analyzed_subject = subject("pipeline")
        fact = p004_fact()
        request = request_for(analyzed_subject, (fact,))
        result = kernel().analyze_manual_candidate(request)
        self.assertIs(request, result.request)
        self.assertTrue(all(type(item) is ExplicitBehaviorInput for item in result.constructed_explicit_behavior_inputs))
        self.assertIs(ExplicitBehaviorExecutionResult, type(result.delegated_execution_result))
        self.assertIs(SingleCandidateAnalysisResult, type(result.single_candidate_analysis_result))
        self.assertIs(
            result.constructed_explicit_behavior_inputs[0].input_object,
            result.delegated_execution_result.execution_records[0].input_object,
        )

    def test_manual_request_observations_remain_downstream_transport_only(self) -> None:
        analyzed_subject = subject("observations")
        observation = kernel_package.CandidateObservationAttachment(
            analyzed_subject,
            kernel_package.SubjectBoundObservedPriceObservation(
                analyzed_subject,
                100,
                "manual:observed-price",
            ),
        )
        request = ManualStructureCandidateRequest(
            "observation-request",
            "2026-09-03T12:00:00Z",
            analyzed_subject,
            "observation-candidate",
            observations=(observation,),
        )
        result = kernel().analyze_manual_candidate(request)
        self.assertIs(
            observation,
            result.delegated_execution_result.candidate_envelope.observations[0],
        )
        self.assertEqual((), result.constructed_explicit_behavior_inputs)

    def test_malformed_missing_nonfinite_and_invalid_tokens_fail_before_methodology(self) -> None:
        with self.assertRaises(TypeError):
            ManualP004Wave2OriginFact(CandidateScope.NORMAL_IMPULSE)
        for price in (float("inf"), float("-inf"), float("nan"), "100", True):
            with self.subTest(price=price):
                with self.assertRaises(ManualStructureCandidateBuilderError):
                    ManualP004Wave2OriginFact(
                        CandidateScope.NORMAL_IMPULSE,
                        ImpulseDirection.UP,
                        price,
                        101,
                    )
        with self.assertRaises(ManualStructureCandidateBuilderError):
            ManualP023VisibilityFact(subject("visibility"), "VISIBLE")
        with self.assertRaises(ManualStructureCandidateBuilderError):
            ManualDirectChildCardinalityFact("FLAT")

    def test_manual_fact_is_not_result_certificate_or_family_authority(self) -> None:
        fact = p004_fact()
        self.assertNotIsInstance(fact, structural_private.StructuralValidatorResult)
        self.assertNotIsInstance(fact, kernel_package.CertifiedStructuralInvalidity)
        with self.assertRaises(Exception):
            certify_validated_internal_family(fact)
        result = kernel().analyze_manual_candidate(request_for(subject("no-authority"), (fact,)))
        forbidden = {"valid_candidate", "family_valid", "preferred", "confidence", "rank"}
        self.assertTrue(forbidden.isdisjoint(ManualStructureCandidateBuildResult.__dataclass_fields__))
        with self.assertRaises(Exception):
            certify_validated_internal_family(result)

    def test_zero_facts_delegates_to_existing_conservative_result(self) -> None:
        result = kernel().analyze_manual_candidate(request_for(subject("zero")))
        self.assertEqual((), result.constructed_explicit_behavior_inputs)
        self.assertIs(
            SingleCandidateExecutionSummary.UNRESOLVED,
            result.single_candidate_analysis_result.execution_summary,
        )
        self.assertEqual(
            ("NO_METHODOLOGY_EVALUATIONS_SUPPLIED",),
            result.single_candidate_analysis_result.unresolved_reasons,
        )

    def test_duplicate_fact_identity_rejected_but_distinct_facts_preserve_order(self) -> None:
        analyzed_subject = subject("duplicates")
        fact = p004_fact()
        with self.assertRaises(ManualStructureCandidateBuilderError):
            request_for(analyzed_subject, (fact, fact))
        second = p004_fact()
        result = kernel().analyze_manual_candidate(request_for(analyzed_subject, (fact, second)))
        self.assertEqual(2, len(result.constructed_explicit_behavior_inputs))
        self.assertIs(fact.candidate_scope, result.constructed_explicit_behavior_inputs[0].input_object.candidate_scope)
        self.assertNotIn("rank", ManualStructureCandidateBuildResult.__dataclass_fields__)

    def test_low_level_fact_binding_and_nested_result_mutation_fail_closed(self) -> None:
        analyzed_subject = subject("mutation")
        fact = p004_fact()
        request = request_for(analyzed_subject, (fact,))
        object.__setattr__(fact, "wave1_origin_price", 999)
        with self.assertRaises(ManualStructureCandidateBuilderError):
            kernel().analyze_manual_candidate(request)

        binding = binding_for(analyzed_subject, 3)
        binding_request = request_for(analyzed_subject, child_binding=binding)
        object.__setattr__(binding, "ordered_children", tuple(reversed(binding.ordered_children)))
        with self.assertRaises(ManualStructureCandidateBuilderError):
            kernel().analyze_manual_candidate(binding_request)

        result = kernel().analyze_manual_candidate(request_for(subject("result-mutation"), (p004_fact(),)))
        object.__setattr__(
            result.delegated_execution_result.execution_records[0].result_object,
            "reason",
            "changed",
        )
        with self.assertRaises(ManualStructureCandidateBuilderError):
            copy.copy(result)

    def test_result_is_factory_only_frozen_identity_and_nonserializable(self) -> None:
        result = kernel().analyze_manual_candidate(request_for(subject("result")))
        with self.assertRaises(TypeError):
            ManualStructureCandidateBuildResult()
        with self.assertRaises(FrozenInstanceError):
            result.provenance_refs = ()
        self.assertIs(result, copy.copy(result))
        self.assertIs(result, copy.deepcopy(result))
        with self.assertRaises(TypeError):
            pickle.dumps(result)

    def test_mapping_and_callable_constructor_or_dispatch_injection_is_impossible(self) -> None:
        public_fields = {item.name for item in fields(ManualStructureCandidateRequest)}
        for forbidden in ("constructor", "validator", "callable", "behavior_id", "module", "class_name"):
            self.assertNotIn(forbidden, public_fields)
        with self.assertRaises(TypeError):
            ManualP004Wave2OriginFact(
                CandidateScope.NORMAL_IMPULSE,
                ImpulseDirection.UP,
                100,
                101,
                validator=lambda value: value,
            )
        with self.assertRaises(ManualStructureCandidateBuilderError):
            kernel().analyze_manual_candidate(asdict(request_for(subject("mapping"))))

    def test_builder_mapping_is_finite_private_immutable_and_exact(self) -> None:
        self.assertIsInstance(builder_module._MANUAL_FACT_BUILDERS, tuple)
        self.assertEqual(9, len(builder_module._MANUAL_FACT_BUILDERS))
        self.assertEqual(6, len(builder_module._MANUAL_FACT_TYPES))
        expected_behaviors = {
            "P004_NORMAL_IMPULSE_WAVE2_ORIGIN",
            "DEGREE_DIRECT_CHILD_PEER_CONSISTENCY",
            "PARENT_CHILD_DEGREE_ADJACENCY",
            "P023_INTERNAL_VISIBILITY_GUARD",
            "P003_ONE_LARGER_DEGREE_SEARCH_THEME",
            "P007_SINGLE_ZIGZAG_DIRECT_CHILD_CARDINALITY",
            "P008_FLAT_DIRECT_CHILD_CARDINALITY",
            "P009_TRIANGLE_DIRECT_CHILD_CARDINALITY",
            "ENDING_DIAGONAL_DIRECT_CHILD_CARDINALITY",
        }
        self.assertEqual(expected_behaviors, {item.behavior_id for item in builder_module._MANUAL_FACT_BUILDERS})
        for item in builder_module._MANUAL_FACT_BUILDERS:
            with self.assertRaises(FrozenInstanceError):
                item.constructor = object()

    def test_api_delegation_boundaries_remain_distinct(self) -> None:
        self.assertEqual(("self", "request"), tuple(inspect.signature(MethodologyKernel.analyze_manual_candidate).parameters))
        self.assertEqual(("self", "request"), tuple(inspect.signature(MethodologyKernel.analyze_candidate_inputs).parameters))
        self.assertIn("status=KernelStatus.NOT_IMPLEMENTED", inspect.getsource(MethodologyKernel.analyze))

    def test_no_discovery_market_interpretation_or_external_capability(self) -> None:
        path = support.SRC / "elliott_methodology_kernel" / "manual_structure_candidate_builder.py"
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
            "NormalizedMarketObservations", "Bar", "OHLCV", "TradingView", "RSI",
            "MACD", "EWO", "Fibonacci", "pivot detection", "wave discovery",
            "family inference", "degree inference", "timeframe mapping", "PREFERRED",
            "ALTERNATIVE", "REMOTE", "certify_structural_invalidity(",
            "certify_validated_internal_family(",
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
        self.assertEqual(11, len(observed))
        self.assertTrue(structural_private._REGISTRY_SEALED)
        self.assertEqual(7, len(structural_private._PRODUCERS))
        self.assertTrue(family_private._REGISTRY_SEALED)
        self.assertEqual(0, len(family_private._PRODUCERS))
        self.assertEqual(0, len(family_private._ISSUED))


if __name__ == "__main__":
    unittest.main()
