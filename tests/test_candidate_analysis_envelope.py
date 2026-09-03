import ast
import copy
from dataclasses import FrozenInstanceError, asdict
import inspect
import pickle
import unittest

import support
import elliott_methodology_kernel as kernel
import elliott_methodology_kernel._structural_invalidity_certification as structural_private
import elliott_methodology_kernel._validated_internal_family_certification as family_private
import elliott_methodology_kernel.candidate_analysis_envelope as envelope_module
from elliott_methodology_kernel import (
    AnalysisResolutionState,
    AnalyzedWaveSubject,
    BoundedRecursiveAnalysisResolution,
    CandidateAnalysisEnvelope,
    CandidateAnalysisEnvelopeError,
    CandidateMethodologyEvaluation,
    CandidateObservationAttachment,
    CandidateScope,
    DegreePeerConsistencyInput,
    EndingDiagonalCandidateScope,
    EndingDiagonalCardinalityInput,
    ImpulseDirection,
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
    StructuralInvalidityCertificationError,
    SubjectBoundObservedPriceEndpointPair,
    SubjectBoundObservedPriceObservation,
    ValidatedInternalFamilyCertificationError,
    apply_structural_invalidity_evidence_no_rescue,
    certify_structural_invalidity,
    certify_validated_internal_family,
    check_degree_peer_consistency,
    check_ending_diagonal_cardinality,
    check_p004,
    check_p007_single_zigzag_cardinality,
    check_p008_flat_cardinality,
    check_p009_triangle_cardinality,
    check_parent_child_degree_adjacency,
    check_p023_visibility_guard,
    evaluate_p023_visibility_for_subject,
    map_p003_one_larger_degree_theme,
)
from elliott_methodology_kernel.models import (
    DegreeStatus,
    DegreeTreeNode,
    InternalStatus,
)


def subject(name: str) -> AnalyzedWaveSubject:
    return AnalyzedWaveSubject(name, f"observations:{name}")


def binding_for(
    parent: AnalyzedWaveSubject,
    count: int = 5,
    name: str = "candidate-binding",
) -> OrderedChildBinding:
    return OrderedChildBinding(
        name,
        parent,
        tuple(subject(f"{name}-child-{index}") for index in range(count)),
    )


def provenance() -> tuple[str, ...]:
    return ("analysis-run:exact-live",)


def attach(
    analyzed_subject: AnalyzedWaveSubject,
    behavior_id: str,
    input_object: object,
    result_object: object,
) -> CandidateMethodologyEvaluation:
    return CandidateMethodologyEvaluation(
        analyzed_subject,
        behavior_id,
        input_object,
        result_object,
        provenance(),
    )


def degree_child(name: str, degree: str) -> DegreeTreeNode:
    return DegreeTreeNode(
        label=name,
        degree=degree,
        degree_status=DegreeStatus.RESOLVED,
        internal_status=InternalStatus.UNRESOLVED,
        parent_label="parent",
    )


def structural_certificate_for(
    analyzed_subject: AnalyzedWaveSubject,
    child_binding: OrderedChildBinding | None = None,
):
    binding = child_binding or binding_for(analyzed_subject, 2, "invalid-binding")
    origin = check_p007_single_zigzag_cardinality(
        P007SingleZigzagCardinalityInput(
            P007CandidateScope.SINGLE_ZIGZAG,
            binding,
        )
    )
    return certify_structural_invalidity(origin)


def all_ten_evaluations(
    analyzed_subject: AnalyzedWaveSubject,
    child_binding: OrderedChildBinding,
) -> tuple[CandidateMethodologyEvaluation, ...]:
    p004_input = P004Input(
        CandidateScope.NORMAL_IMPULSE,
        ImpulseDirection.UP,
        100,
        100,
    )
    degree_input = DegreePeerConsistencyInput(
        "parent",
        (degree_child("1", "Minor"), degree_child("2", "Minor")),
    )
    parent_child_input = ParentChildDegreeInput(
        "Cycle",
        DegreeStatus.RESOLVED,
        "Primary",
        DegreeStatus.RESOLVED,
    )
    p023_input = P023VisibilityInput(P023VisibilityState.NOT_VISIBLE)
    p023_result = evaluate_p023_visibility_for_subject(
        analyzed_subject,
        p023_input,
    )
    certificate = structural_certificate_for(analyzed_subject, child_binding)
    no_rescue_result = apply_structural_invalidity_evidence_no_rescue(certificate)
    p003_input = P003OneLargerDegreeThemeInput(
        P003OneLargerDegreeRelation.AGAINST
    )
    p007_input = P007SingleZigzagCardinalityInput(
        P007CandidateScope.SINGLE_ZIGZAG,
        child_binding,
    )
    p008_input = P008FlatCardinalityInput(
        P008CandidateScope.FLAT,
        child_binding,
    )
    p009_input = P009TriangleCardinalityInput(
        P009CandidateScope.TRIANGLE,
        child_binding,
    )
    diagonal_input = EndingDiagonalCardinalityInput(
        EndingDiagonalCandidateScope.ENDING_DIAGONAL,
        child_binding,
    )
    return (
        attach(analyzed_subject, "P004_NORMAL_IMPULSE_WAVE2_ORIGIN", p004_input, check_p004(p004_input)),
        attach(analyzed_subject, "DEGREE_DIRECT_CHILD_PEER_CONSISTENCY", degree_input, check_degree_peer_consistency(degree_input)),
        attach(analyzed_subject, "PARENT_CHILD_DEGREE_ADJACENCY", parent_child_input, check_parent_child_degree_adjacency(parent_child_input)),
        attach(analyzed_subject, "P023_INTERNAL_VISIBILITY_GUARD", p023_input, p023_result),
        attach(analyzed_subject, "STRUCTURAL_INVALIDITY_EVIDENCE_NO_RESCUE", certificate, no_rescue_result),
        attach(analyzed_subject, "P003_ONE_LARGER_DEGREE_SEARCH_THEME", p003_input, map_p003_one_larger_degree_theme(p003_input)),
        attach(analyzed_subject, "P007_SINGLE_ZIGZAG_DIRECT_CHILD_CARDINALITY", p007_input, check_p007_single_zigzag_cardinality(p007_input)),
        attach(analyzed_subject, "P008_FLAT_DIRECT_CHILD_CARDINALITY", p008_input, check_p008_flat_cardinality(p008_input)),
        attach(analyzed_subject, "P009_TRIANGLE_DIRECT_CHILD_CARDINALITY", p009_input, check_p009_triangle_cardinality(p009_input)),
        attach(analyzed_subject, "ENDING_DIAGONAL_DIRECT_CHILD_CARDINALITY", diagonal_input, check_ending_diagonal_cardinality(diagonal_input)),
    )


def unresolved_resolution(
    analyzed_subject: AnalyzedWaveSubject,
) -> BoundedRecursiveAnalysisResolution:
    return BoundedRecursiveAnalysisResolution(
        analyzed_subject,
        AnalysisResolutionState.UNRESOLVED_METHODOLOGY_DEPENDENCY,
        "Required positive family authority remains unavailable.",
        dependency_code=MethodologyDependencyCode.FAMILY_PRODUCER_UNAVAILABLE,
        provenance_refs=provenance(),
    )


class CandidateAnalysisEnvelopeTests(unittest.TestCase):
    def test_exact_identity_and_tuple_order_are_retained(self) -> None:
        analyzed_subject = subject("candidate")
        child_binding = binding_for(analyzed_subject)
        evaluations = all_ten_evaluations(analyzed_subject, child_binding)
        observation = SubjectBoundObservedPriceObservation(
            analyzed_subject, 100, "price:one"
        )
        observations = (
            CandidateObservationAttachment(
                analyzed_subject,
                observation,
                provenance(),
            ),
        )
        resolution = unresolved_resolution(analyzed_subject)
        envelope = CandidateAnalysisEnvelope(
            analyzed_subject,
            "candidate-metadata-only",
            child_binding,
            evaluations,
            observations,
            resolution,
            provenance(),
        )
        self.assertIs(analyzed_subject, envelope.subject)
        self.assertIs(child_binding, envelope.child_binding)
        self.assertIs(evaluations, envelope.methodology_evaluations)
        self.assertIs(observations, envelope.observations)
        self.assertIs(resolution, envelope.operational_resolution)
        for expected, observed in zip(evaluations, envelope.methodology_evaluations, strict=True):
            self.assertIs(expected, observed)

    def test_candidate_id_is_metadata_and_surface_has_no_authority_fields(self) -> None:
        analyzed_subject = subject("metadata")
        envelope = CandidateAnalysisEnvelope(
            analyzed_subject,
            "IMPULSE-WAVE-3-PRIMARY",
        )
        self.assertEqual("IMPULSE-WAVE-3-PRIMARY", envelope.candidate_id)
        fields_present = set(CandidateAnalysisEnvelope.__dataclass_fields__)
        self.assertTrue(
            {
                "pattern", "wave", "wave_label", "degree", "parentage",
                "timeframe", "completion", "direction", "family", "validity",
                "status", "rank", "confidence",
            }.isdisjoint(fields_present)
        )

    def test_all_three_public_records_are_immutable_identity_objects(self) -> None:
        analyzed_subject = subject("immutability")
        p004_input = P004Input(CandidateScope.NORMAL_IMPULSE, ImpulseDirection.UP, 1, 1)
        evaluation = attach(
            analyzed_subject,
            "P004_NORMAL_IMPULSE_WAVE2_ORIGIN",
            p004_input,
            check_p004(p004_input),
        )
        observation = CandidateObservationAttachment(
            analyzed_subject,
            SubjectBoundObservedPriceObservation(analyzed_subject, 1, "price"),
        )
        envelope = CandidateAnalysisEnvelope(
            analyzed_subject,
            "candidate",
            methodology_evaluations=(evaluation,),
            observations=(observation,),
        )
        for value, attribute in (
            (evaluation, "behavior_id"),
            (observation, "subject"),
            (envelope, "candidate_id"),
        ):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(FrozenInstanceError):
                    setattr(value, attribute, "changed")
                self.assertIs(value, copy.copy(value))
                self.assertIs(value, copy.deepcopy(value))
                with self.assertRaises(TypeError):
                    pickle.dumps(value)

    def test_compatibility_table_is_exact_private_and_has_ten_entries(self) -> None:
        expected = {
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
        }
        table = envelope_module._BEHAVIOR_COMPATIBILITY
        self.assertEqual(10, len(table))
        self.assertEqual(expected, {item.behavior_id for item in table})
        self.assertNotIn("_BEHAVIOR_COMPATIBILITY", envelope_module.__all__)

    def test_each_exact_behavior_pair_is_accepted_without_ranking(self) -> None:
        analyzed_subject = subject("all-ten")
        child_binding = binding_for(analyzed_subject)
        evaluations = all_ten_evaluations(analyzed_subject, child_binding)
        envelope = CandidateAnalysisEnvelope(
            analyzed_subject,
            "all-ten",
            child_binding,
            evaluations,
        )
        self.assertEqual(10, len(envelope.methodology_evaluations))
        self.assertFalse(hasattr(envelope, "preferred"))
        self.assertFalse(hasattr(envelope, "winner"))

    def test_mismatched_unknown_duck_mapping_and_result_subclass_fail_closed(self) -> None:
        analyzed_subject = subject("mismatch")
        p004_input = P004Input(CandidateScope.NORMAL_IMPULSE, ImpulseDirection.UP, 1, 1)
        p004_result = check_p004(p004_input)
        p003_input = P003OneLargerDegreeThemeInput(P003OneLargerDegreeRelation.WITH)
        p003_result = map_p003_one_larger_degree_theme(p003_input)

        class Duck:
            behavior_id = "P004_NORMAL_IMPULSE_WAVE2_ORIGIN"

        class ResultSubclass(type(p004_result)):
            __slots__ = ()

        subclass = ResultSubclass(
            **{
                name: getattr(p004_result, name)
                for name in p004_result.__dataclass_fields__
            }
        )
        cases = (
            ("P004_NORMAL_IMPULSE_WAVE2_ORIGIN", p004_input, p003_result),
            ("P003_ONE_LARGER_DEGREE_SEARCH_THEME", p004_input, p003_result),
            ("UNKNOWN_BEHAVIOR", p004_input, p004_result),
            ("P004_NORMAL_IMPULSE_WAVE2_ORIGIN", p004_input, Duck()),
            ("P004_NORMAL_IMPULSE_WAVE2_ORIGIN", p004_input, asdict(p004_result)),
            ("P004_NORMAL_IMPULSE_WAVE2_ORIGIN", p004_input, subclass),
        )
        for behavior_id, supplied_input, supplied_result in cases:
            with self.subTest(behavior_id=behavior_id, result=type(supplied_result).__name__):
                with self.assertRaises(CandidateAnalysisEnvelopeError):
                    attach(
                        analyzed_subject,
                        behavior_id,
                        supplied_input,
                        supplied_result,
                    )

    def test_arbitrary_string_and_class_name_matching_are_not_compatibility(self) -> None:
        analyzed_subject = subject("class-name")
        fake_type = type("P004Result", (), {"behavior_id": "P004_NORMAL_IMPULSE_WAVE2_ORIGIN"})
        p004_input = P004Input(CandidateScope.NORMAL_IMPULSE, ImpulseDirection.UP, 1, 1)
        with self.assertRaises(CandidateAnalysisEnvelopeError):
            attach(
                analyzed_subject,
                "P004_NORMAL_IMPULSE_WAVE2_ORIGIN",
                p004_input,
                fake_type(),
            )
        source_text = inspect.getsource(envelope_module)
        self.assertNotIn("__name__", source_text)
        self.assertNotIn("import_module", source_text)

    def test_legacy_subjectless_result_is_transport_only(self) -> None:
        analyzed_subject = subject("legacy")
        p004_input = P004Input(CandidateScope.NORMAL_IMPULSE, ImpulseDirection.UP, 1, 1)
        result = check_p004(p004_input)
        evaluation = attach(
            analyzed_subject,
            "P004_NORMAL_IMPULSE_WAVE2_ORIGIN",
            p004_input,
            result,
        )
        self.assertIs(analyzed_subject, evaluation.subject)
        self.assertFalse(hasattr(result, "subject"))
        self.assertIsNone(evaluation.consumed_binding)

    def test_p023_requires_live_exact_subject_bound_result(self) -> None:
        first = subject("p023-first")
        second = subject("p023-second")
        candidate = P023VisibilityInput(P023VisibilityState.NOT_VISIBLE)
        support = evaluate_p023_visibility_for_subject(first, candidate)
        accepted = attach(
            first,
            "P023_INTERNAL_VISIBILITY_GUARD",
            candidate,
            support,
        )
        self.assertIs(first, accepted.subject)
        with self.assertRaises(CandidateAnalysisEnvelopeError):
            attach(
                second,
                "P023_INTERNAL_VISIBILITY_GUARD",
                candidate,
                support,
            )
        alternate_input = P023VisibilityInput(P023VisibilityState.NOT_VISIBLE)
        alternate = attach(
            first,
            "P023_INTERNAL_VISIBILITY_GUARD",
            alternate_input,
            support,
        )
        self.assertIs(alternate_input, alternate.input_object)
        raw_result = check_p023_visibility_guard(candidate)
        for fake in (raw_result, asdict(raw_result), object()):
            with self.assertRaises(CandidateAnalysisEnvelopeError):
                attach(
                    first,
                    "P023_INTERNAL_VISIBILITY_GUARD",
                    candidate,
                    fake,
                )

    def test_cardinality_binding_identity_and_order_are_enforced(self) -> None:
        analyzed_subject = subject("binding")
        original = binding_for(analyzed_subject, 3, "original")
        lookalike = OrderedChildBinding(
            "lookalike",
            analyzed_subject,
            original.ordered_children,
        )
        candidate = P007SingleZigzagCardinalityInput(
            P007CandidateScope.SINGLE_ZIGZAG,
            original,
        )
        evaluation = attach(
            analyzed_subject,
            "P007_SINGLE_ZIGZAG_DIRECT_CHILD_CARDINALITY",
            candidate,
            check_p007_single_zigzag_cardinality(candidate),
        )
        accepted = CandidateAnalysisEnvelope(
            analyzed_subject,
            "binding",
            original,
            (evaluation,),
        )
        self.assertIs(original, accepted.child_binding)
        self.assertIs(original, evaluation.consumed_binding)
        with self.assertRaises(CandidateAnalysisEnvelopeError):
            CandidateAnalysisEnvelope(
                analyzed_subject,
                "lookalike",
                lookalike,
                (evaluation,),
            )
        reversed_binding = OrderedChildBinding(
            "reversed",
            analyzed_subject,
            tuple(reversed(original.ordered_children)),
        )
        self.assertIsNot(original, reversed_binding)
        self.assertEqual(
            tuple(reversed(original.ordered_children)),
            reversed_binding.ordered_children,
        )

    def test_cross_subject_binding_and_no_rescue_origin_are_rejected(self) -> None:
        first = subject("binding-first")
        second = subject("binding-second")
        child_binding = binding_for(first, 2, "cross-binding")
        p007_input = P007SingleZigzagCardinalityInput(
            P007CandidateScope.SINGLE_ZIGZAG,
            child_binding,
        )
        with self.assertRaises(CandidateAnalysisEnvelopeError):
            attach(
                second,
                "P007_SINGLE_ZIGZAG_DIRECT_CHILD_CARDINALITY",
                p007_input,
                check_p007_single_zigzag_cardinality(p007_input),
            )
        certificate = structural_certificate_for(first, child_binding)
        no_rescue = apply_structural_invalidity_evidence_no_rescue(certificate)
        with self.assertRaises(CandidateAnalysisEnvelopeError):
            attach(
                second,
                "STRUCTURAL_INVALIDITY_EVIDENCE_NO_RESCUE",
                certificate,
                no_rescue,
            )

    def test_observation_and_endpoint_pair_remain_exact_transport(self) -> None:
        analyzed_subject = subject("observations")
        start = SubjectBoundObservedPriceObservation(analyzed_subject, 10, "start")
        end = SubjectBoundObservedPriceObservation(analyzed_subject, 20, "end")
        pair = SubjectBoundObservedPriceEndpointPair(start, end)
        attachments = (
            CandidateObservationAttachment(analyzed_subject, start, provenance()),
            CandidateObservationAttachment(analyzed_subject, pair, provenance()),
        )
        envelope = CandidateAnalysisEnvelope(
            analyzed_subject,
            "observations",
            observations=attachments,
        )
        self.assertIs(attachments, envelope.observations)
        self.assertIs(start, attachments[0].observation)
        self.assertIs(pair, attachments[1].observation)
        self.assertTrue(
            {"pivot", "orthodox_end", "completion", "wave_origin", "wave_end"}
            .isdisjoint(CandidateObservationAttachment.__dataclass_fields__)
        )

    def test_cross_subject_observation_and_duck_are_rejected(self) -> None:
        first = subject("observation-first")
        second = subject("observation-second")
        observation = SubjectBoundObservedPriceObservation(first, 10, "price")

        class Duck:
            subject = second

        for supplied in (observation, Duck(), {"subject": second.subject_id}):
            with self.subTest(kind=type(supplied).__name__):
                with self.assertRaises(CandidateAnalysisEnvelopeError):
                    CandidateObservationAttachment(second, supplied)

    def test_duplicate_behavior_input_identity_is_rejected(self) -> None:
        analyzed_subject = subject("duplicate")
        p004_input = P004Input(CandidateScope.NORMAL_IMPULSE, ImpulseDirection.UP, 1, 1)
        result = check_p004(p004_input)
        first = attach(analyzed_subject, "P004_NORMAL_IMPULSE_WAVE2_ORIGIN", p004_input, result)
        second = attach(analyzed_subject, "P004_NORMAL_IMPULSE_WAVE2_ORIGIN", p004_input, result)
        for evaluations in ((first, first), (first, second)):
            with self.assertRaises(CandidateAnalysisEnvelopeError):
                CandidateAnalysisEnvelope(
                    analyzed_subject,
                    "duplicate",
                    methodology_evaluations=evaluations,
                )

    def test_same_behavior_different_input_identities_are_ordered_not_ranked(self) -> None:
        analyzed_subject = subject("multiple")
        first_input = P004Input(CandidateScope.NORMAL_IMPULSE, ImpulseDirection.UP, 1, 1)
        second_input = P004Input(CandidateScope.NORMAL_IMPULSE, ImpulseDirection.UP, 2, 2)
        evaluations = (
            attach(analyzed_subject, "P004_NORMAL_IMPULSE_WAVE2_ORIGIN", first_input, check_p004(first_input)),
            attach(analyzed_subject, "P004_NORMAL_IMPULSE_WAVE2_ORIGIN", second_input, check_p004(second_input)),
        )
        envelope = CandidateAnalysisEnvelope(
            analyzed_subject,
            "multiple",
            methodology_evaluations=evaluations,
        )
        self.assertIs(evaluations, envelope.methodology_evaluations)
        self.assertIs(first_input, envelope.methodology_evaluations[0].input_object)
        self.assertIs(second_input, envelope.methodology_evaluations[1].input_object)
        self.assertFalse(hasattr(envelope, "ranking"))

    def test_exact_operational_resolution_attaches_without_transformation(self) -> None:
        analyzed_subject = subject("resolution")
        resolution = unresolved_resolution(analyzed_subject)
        envelope = CandidateAnalysisEnvelope(
            analyzed_subject,
            "resolution",
            operational_resolution=resolution,
        )
        self.assertIs(resolution, envelope.operational_resolution)
        self.assertIs(
            AnalysisResolutionState.UNRESOLVED_METHODOLOGY_DEPENDENCY,
            envelope.operational_resolution.state,
        )
        self.assertFalse(hasattr(envelope, "state"))

    def test_cross_subject_and_fake_operational_resolution_are_rejected(self) -> None:
        first = subject("resolution-first")
        second = subject("resolution-second")
        resolution = unresolved_resolution(first)
        for supplied in (resolution, {"state": "VALIDATED_FAMILY"}, object()):
            with self.subTest(kind=type(supplied).__name__):
                with self.assertRaises(CandidateAnalysisEnvelopeError):
                    CandidateAnalysisEnvelope(
                        second,
                        "wrong-resolution",
                        operational_resolution=supplied,
                    )

    def test_envelope_and_attachments_cannot_mint_certificates(self) -> None:
        analyzed_subject = subject("authority")
        p004_input = P004Input(CandidateScope.NORMAL_IMPULSE, ImpulseDirection.UP, 1, 1)
        evaluation = attach(
            analyzed_subject,
            "P004_NORMAL_IMPULSE_WAVE2_ORIGIN",
            p004_input,
            check_p004(p004_input),
        )
        envelope = CandidateAnalysisEnvelope(
            analyzed_subject,
            "authority",
            methodology_evaluations=(evaluation,),
        )
        for value in (evaluation, envelope):
            with self.subTest(kind=type(value).__name__):
                with self.assertRaises(StructuralInvalidityCertificationError):
                    certify_structural_invalidity(value)
                with self.assertRaises(ValidatedInternalFamilyCertificationError):
                    certify_validated_internal_family(value)

    def test_low_level_evaluation_and_observation_mutation_fail_at_envelope_boundary(self) -> None:
        analyzed_subject = subject("tamper")
        p004_input = P004Input(CandidateScope.NORMAL_IMPULSE, ImpulseDirection.UP, 1, 1)
        evaluation = attach(
            analyzed_subject,
            "P004_NORMAL_IMPULSE_WAVE2_ORIGIN",
            p004_input,
            check_p004(p004_input),
        )
        object.__setattr__(evaluation, "behavior_id", "P009_TRIANGLE_DIRECT_CHILD_CARDINALITY")
        with self.assertRaises(CandidateAnalysisEnvelopeError):
            CandidateAnalysisEnvelope(
                analyzed_subject,
                "tampered-evaluation",
                methodology_evaluations=(evaluation,),
            )

        fresh_input = P004Input(CandidateScope.NORMAL_IMPULSE, ImpulseDirection.UP, 2, 2)
        fresh_result = check_p004(fresh_input)
        result_attachment = attach(
            analyzed_subject,
            "P004_NORMAL_IMPULSE_WAVE2_ORIGIN",
            fresh_input,
            fresh_result,
        )
        object.__setattr__(fresh_result, "reason", "tampered result status context")
        with self.assertRaises(CandidateAnalysisEnvelopeError):
            CandidateAnalysisEnvelope(
                analyzed_subject,
                "tampered-result",
                methodology_evaluations=(result_attachment,),
            )

        observation = SubjectBoundObservedPriceObservation(analyzed_subject, 1, "price")
        attachment = CandidateObservationAttachment(analyzed_subject, observation)
        object.__setattr__(observation, "price", 2)
        with self.assertRaises(CandidateAnalysisEnvelopeError):
            CandidateAnalysisEnvelope(
                analyzed_subject,
                "tampered-observation",
                observations=(attachment,),
            )

        intact = CandidateAnalysisEnvelope(analyzed_subject, "intact")
        object.__setattr__(intact, "candidate_id", "mutated")
        with self.assertRaises(CandidateAnalysisEnvelopeError):
            copy.copy(intact)

    def test_public_surface_is_minimal(self) -> None:
        expected = {
            "CandidateAnalysisEnvelope",
            "CandidateAnalysisEnvelopeError",
            "CandidateMethodologyEvaluation",
            "CandidateObservationAttachment",
        }
        self.assertTrue(expected.issubset(set(kernel.__all__)))
        self.assertEqual(
            expected | {"ARTIFACT_CLASSIFICATION", "WORKFLOW_POLICY_CLASSIFICATION"},
            set(envelope_module.__all__),
        )

    def test_no_prohibited_capability_or_dynamic_compatibility_import(self) -> None:
        path = support.SRC / "elliott_methodology_kernel" / "candidate_analysis_envelope.py"
        source_text = path.read_text(encoding="utf-8")
        tree = ast.parse(source_text, filename=str(path))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add("." * node.level + (node.module or ""))
        self.assertTrue(
            {"socket", "subprocess", "requests", "urllib", "importlib"}
            .isdisjoint(imports)
        )
        for forbidden in (
            "TradingView", "RSI", "MACD", "EWO", "Fibonacci", "channeling",
            "breadth", "psychology", "fundamentals", "pivot detection",
            "wave segmentation", "candidate generation", "pattern recognition",
            "PREFERRED", "ALTERNATIVE", "TRADE", "STAND_ASIDE",
        ):
            self.assertNotIn(forbidden, source_text)

    def test_methodology_inventory_registries_and_analyze_remain_unchanged(self) -> None:
        observed = set()
        for path in (support.SRC / "elliott_methodology_kernel").glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                assignments = ()
                if isinstance(node, ast.Assign):
                    assignments = tuple(
                        target for target in node.targets if isinstance(target, ast.Name)
                    )
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
            inspect.getsource(kernel.MethodologyKernel.analyze),
        )


if __name__ == "__main__":
    unittest.main()
