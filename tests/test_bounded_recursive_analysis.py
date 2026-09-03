import ast
import copy
from dataclasses import FrozenInstanceError, asdict, fields
import inspect
import pickle
import unittest

import support
import elliott_methodology_kernel as kernel
import elliott_methodology_kernel._structural_invalidity_certification as structural_private
import elliott_methodology_kernel._validated_internal_family_certification as family_private
from elliott_methodology_kernel import (
    ARTIFACT_CLASSIFICATION,
    OPERATIONAL_POLICY_CLASSIFICATION,
    AnalysisResolutionState,
    AnalyzedWaveSubject,
    BoundedRecursiveAnalysisContractError,
    BoundedRecursiveAnalysisNode,
    BoundedRecursiveAnalysisResolution,
    CertifiedStructuralInvalidity,
    CertifiedValidatedInternalFamily,
    KernelStatus,
    MethodologyDependencyCode,
    OperationalAggregationState,
    OrderedChildBinding,
    CandidateScope,
    ImpulseDirection,
    P004Input,
    P007CandidateScope,
    P007SingleZigzagCardinalityInput,
    P023VisibilityInput,
    P023VisibilityState,
    SubjectBoundP023VisibilityResult,
    aggregate_supplied_child_resolutions,
    certify_structural_invalidity,
    certify_validated_internal_family,
    check_p007_single_zigzag_cardinality,
    check_p004,
    check_p023_visibility_guard,
    evaluate_p023_visibility_for_subject,
)


def subject(name: str) -> AnalyzedWaveSubject:
    return AnalyzedWaveSubject(name, f"observation:{name}")


def dependency_resolution(
    analyzed_subject: AnalyzedWaveSubject,
    code: MethodologyDependencyCode = MethodologyDependencyCode.FAMILY_PRODUCER_UNAVAILABLE,
) -> BoundedRecursiveAnalysisResolution:
    return BoundedRecursiveAnalysisResolution(
        subject=analyzed_subject,
        state=AnalysisResolutionState.UNRESOLVED_METHODOLOGY_DEPENDENCY,
        reason=f"Operational proof is unavailable: {code.value}.",
        dependency_code=code,
        provenance_refs=("project-state:approved",),
    )


def p023_support(
    analyzed_subject: AnalyzedWaveSubject,
    state: P023VisibilityState,
) -> SubjectBoundP023VisibilityResult:
    return evaluate_p023_visibility_for_subject(
        analyzed_subject,
        P023VisibilityInput(state),
    )


def finer_resolution(
    analyzed_subject: AnalyzedWaveSubject,
    state: P023VisibilityState = P023VisibilityState.NOT_VISIBLE,
) -> BoundedRecursiveAnalysisResolution:
    return BoundedRecursiveAnalysisResolution(
        subject=analyzed_subject,
        state=AnalysisResolutionState.UNRESOLVED_FINER_DATA_REQUIRED,
        reason="Required internals are not presently available for validation.",
        supporting_visibility_result=p023_support(analyzed_subject, state),
        provenance_refs=("P023:unchanged",),
    )


def structural_certificate(
    analyzed_subject: AnalyzedWaveSubject,
) -> CertifiedStructuralInvalidity:
    binding = OrderedChildBinding(
        "single-zigzag-binding",
        analyzed_subject,
        (subject("cardinality-child-1"), subject("cardinality-child-2")),
    )
    result = check_p007_single_zigzag_cardinality(
        P007SingleZigzagCardinalityInput(
            P007CandidateScope.SINGLE_ZIGZAG,
            binding,
        )
    )
    return certify_structural_invalidity(result)


def invalid_resolution(
    analyzed_subject: AnalyzedWaveSubject,
) -> BoundedRecursiveAnalysisResolution:
    return BoundedRecursiveAnalysisResolution(
        subject=analyzed_subject,
        state=AnalysisResolutionState.STRUCTURALLY_INVALID,
        reason="A genuine structural origin is fatal to this candidate.",
        supporting_structural_invalidity_certificate=structural_certificate(
            analyzed_subject
        ),
        provenance_refs=("structural-certificate:live",),
    )


def leaf(
    analyzed_subject: AnalyzedWaveSubject,
    resolution: BoundedRecursiveAnalysisResolution,
) -> BoundedRecursiveAnalysisNode:
    return BoundedRecursiveAnalysisNode(
        subject=analyzed_subject,
        child_binding=None,
        children=(),
        resolution=resolution,
    )


class BoundedRecursiveAnalysisContractTests(unittest.TestCase):
    def test_classification_and_exact_state_vocabularies(self) -> None:
        self.assertEqual("PROJECT_ANALYSIS_INFRASTRUCTURE", ARTIFACT_CLASSIFICATION)
        self.assertEqual("PROJECT_OPERATIONAL_POLICY", OPERATIONAL_POLICY_CLASSIFICATION)
        self.assertEqual(
            {
                "VALIDATED_FAMILY",
                "STRUCTURALLY_INVALID",
                "UNRESOLVED_FINER_DATA_REQUIRED",
                "UNRESOLVED_METHODOLOGY_DEPENDENCY",
            },
            {state.value for state in AnalysisResolutionState},
        )
        self.assertEqual(
            {
                "BLOCKED_BY_INVALID_CHILD",
                "BLOCKED_BY_UNRESOLVED_CHILD",
                "CHILDREN_OPERATIONALLY_RESOLVED",
            },
            {state.value for state in OperationalAggregationState},
        )

    def test_resolution_retains_exact_subject_and_is_immutable(self) -> None:
        analyzed_subject = subject("resolution")
        resolution = dependency_resolution(analyzed_subject)
        self.assertIs(analyzed_subject, resolution.subject)
        with self.assertRaises(FrozenInstanceError):
            resolution.reason = "changed"
        self.assertIs(resolution, copy.copy(resolution))
        self.assertIs(resolution, copy.deepcopy(resolution))
        with self.assertRaises(TypeError):
            pickle.dumps(resolution)

    def test_node_retains_exact_child_binding_identity_and_order(self) -> None:
        parent = subject("parent")
        child_subjects = (subject("child-1"), subject("child-2"))
        children = tuple(
            leaf(item, dependency_resolution(item)) for item in child_subjects
        )
        binding = OrderedChildBinding("children", parent, child_subjects)
        node = BoundedRecursiveAnalysisNode(
            parent,
            binding,
            children,
            dependency_resolution(parent),
        )
        self.assertIs(parent, node.subject)
        self.assertIs(binding, node.child_binding)
        self.assertIs(children, node.children)
        for expected, observed in zip(children, node.children, strict=True):
            self.assertIs(expected, observed)
        self.assertIs(node, copy.copy(node))
        self.assertIs(node, copy.deepcopy(node))
        with self.assertRaises(FrozenInstanceError):
            node.children = ()
        with self.assertRaises(TypeError):
            pickle.dumps(node)

    def test_node_rejects_wrong_parent_child_order_and_unbound_children(self) -> None:
        parent = subject("parent")
        first = subject("first")
        second = subject("second")
        first_node = leaf(first, dependency_resolution(first))
        second_node = leaf(second, dependency_resolution(second))
        binding = OrderedChildBinding("binding", parent, (first, second))
        for supplied_binding, supplied_children in (
            (binding, (second_node, first_node)),
            (None, (first_node, second_node)),
            (OrderedChildBinding("wrong-parent", subject("other"), (first, second)), (first_node, second_node)),
        ):
            with self.subTest(binding=supplied_binding):
                with self.assertRaises(BoundedRecursiveAnalysisContractError):
                    BoundedRecursiveAnalysisNode(
                        parent,
                        supplied_binding,
                        supplied_children,
                        dependency_resolution(parent),
                    )

    def test_genuine_bound_structural_certificate_creates_invalid_state(self) -> None:
        analyzed_subject = subject("invalid")
        certificate = structural_certificate(analyzed_subject)
        resolution = BoundedRecursiveAnalysisResolution(
            analyzed_subject,
            AnalysisResolutionState.STRUCTURALLY_INVALID,
            "Genuine fatal structural invalidity stops this branch.",
            supporting_structural_invalidity_certificate=certificate,
        )
        self.assertIs(certificate, resolution.supporting_structural_invalidity_certificate)
        self.assertIs(analyzed_subject, certificate.origin.binding.parent_subject)

    def test_structural_certificate_wrong_subject_is_rejected(self) -> None:
        certificate = structural_certificate(subject("origin-subject"))
        with self.assertRaises(BoundedRecursiveAnalysisContractError):
            BoundedRecursiveAnalysisResolution(
                subject("wrong-subject"),
                AnalysisResolutionState.STRUCTURALLY_INVALID,
                "Cross-subject authority is prohibited.",
                supporting_structural_invalidity_certificate=certificate,
            )

    def test_structural_origin_without_subject_binding_is_explicitly_applicable(self) -> None:
        origin = check_p004(
            P004Input(
                CandidateScope.NORMAL_IMPULSE,
                ImpulseDirection.UP,
                100,
                99,
            )
        )
        certificate = certify_structural_invalidity(origin)
        analyzed_subject = subject("p004-operational-subject")
        resolution = BoundedRecursiveAnalysisResolution(
            analyzed_subject,
            AnalysisResolutionState.STRUCTURALLY_INVALID,
            "P004 has no subject field; exact-origin subject matching is not applicable.",
            supporting_structural_invalidity_certificate=certificate,
        )
        self.assertIs(analyzed_subject, resolution.subject)
        self.assertFalse(hasattr(certificate.origin, "binding"))

    def test_manual_mapping_duck_and_subclass_structural_support_are_rejected(self) -> None:
        analyzed_subject = subject("invalid-support")
        genuine = structural_certificate(analyzed_subject)

        class Duck:
            origin = genuine.origin

        class CertificateSubclass(CertifiedStructuralInvalidity):
            pass

        malformed_exact = object.__new__(CertifiedStructuralInvalidity)
        subclass = object.__new__(CertificateSubclass)
        for supplied in (malformed_exact, asdict(genuine.origin), Duck(), subclass):
            with self.subTest(kind=type(supplied).__name__):
                with self.assertRaises(BoundedRecursiveAnalysisContractError):
                    BoundedRecursiveAnalysisResolution(
                        analyzed_subject,
                        AnalysisResolutionState.STRUCTURALLY_INVALID,
                        "Fake support must fail closed.",
                        supporting_structural_invalidity_certificate=supplied,
                    )

    def test_certificate_copy_identity_is_accepted_but_copied_origin_cannot_certify(self) -> None:
        analyzed_subject = subject("copy")
        certificate = structural_certificate(analyzed_subject)
        self.assertIs(certificate, copy.copy(certificate))
        self.assertIs(certificate, copy.deepcopy(certificate))
        copied_origin = copy.copy(certificate.origin)
        self.assertIsNot(certificate.origin, copied_origin)
        with self.assertRaises(Exception):
            certify_structural_invalidity(copied_origin)

    def test_contradictory_support_is_rejected(self) -> None:
        analyzed_subject = subject("contradiction")
        malformed_family = object.__new__(CertifiedValidatedInternalFamily)
        with self.assertRaises(BoundedRecursiveAnalysisContractError):
            BoundedRecursiveAnalysisResolution(
                analyzed_subject,
                AnalysisResolutionState.STRUCTURALLY_INVALID,
                "Contradictory support is prohibited.",
                supporting_family_certificate=malformed_family,
                supporting_structural_invalidity_certificate=structural_certificate(
                    analyzed_subject
                ),
            )

    def test_validated_family_requires_exact_genuine_live_matching_certificate(self) -> None:
        analyzed_subject = subject("family")

        class Duck:
            subject = analyzed_subject

        class FamilyCertificateSubclass(CertifiedValidatedInternalFamily):
            pass

        candidates = (
            None,
            object(),
            {"subject": analyzed_subject.subject_id},
            Duck(),
            object.__new__(CertifiedValidatedInternalFamily),
            object.__new__(FamilyCertificateSubclass),
        )
        for supplied in candidates:
            with self.subTest(kind=type(supplied).__name__):
                with self.assertRaises(BoundedRecursiveAnalysisContractError):
                    BoundedRecursiveAnalysisResolution(
                        analyzed_subject,
                        AnalysisResolutionState.VALIDATED_FAMILY,
                        "Only genuine positive proof is accepted.",
                        supporting_family_certificate=supplied,
                    )

    def test_wrong_subject_family_lookalike_cannot_cross_identity_boundary(self) -> None:
        wrong_subject = subject("wrong-family-subject")
        forged = object.__new__(CertifiedValidatedInternalFamily)
        for name, value in (("_origin", object()), ("_attestation", object())):
            object.__setattr__(forged, name, value)
        with self.assertRaises(BoundedRecursiveAnalysisContractError):
            BoundedRecursiveAnalysisResolution(
                wrong_subject,
                AnalysisResolutionState.VALIDATED_FAMILY,
                "A forged or wrong-subject family certificate is rejected.",
                supporting_family_certificate=forged,
            )
        source_text = inspect.getsource(
            kernel.bounded_recursive_analysis._validate_family_certificate
        )
        self.assertIn("certified_subject is not subject", source_text)

    def test_no_current_production_family_path_exists(self) -> None:
        self.assertIs(family_private._REGISTRY_SEALED, True)
        self.assertEqual({}, family_private._PRODUCERS)
        self.assertEqual(set(), family_private._BEHAVIOR_IDS)
        self.assertEqual({}, family_private._ISSUED)
        with self.assertRaises(Exception):
            certify_validated_internal_family(object())

    def test_not_visible_and_unknown_create_only_finer_data_unresolved(self) -> None:
        for visibility_state in (
            P023VisibilityState.NOT_VISIBLE,
            P023VisibilityState.UNKNOWN,
        ):
            with self.subTest(visibility_state=visibility_state):
                analyzed_subject = subject(visibility_state.value)
                support = p023_support(analyzed_subject, visibility_state)
                resolution = BoundedRecursiveAnalysisResolution(
                    analyzed_subject,
                    AnalysisResolutionState.UNRESOLVED_FINER_DATA_REQUIRED,
                    "P023 leaves required internals unresolved.",
                    supporting_visibility_result=support,
                )
                self.assertIs(analyzed_subject, support.subject)
                self.assertIs(support, resolution.supporting_visibility_result)
                self.assertIs(
                    AnalysisResolutionState.UNRESOLVED_FINER_DATA_REQUIRED,
                    resolution.state,
                )
                self.assertIsNone(resolution.supporting_family_certificate)

    def test_visible_p023_never_produces_validity_or_finer_data_stop(self) -> None:
        analyzed_subject = subject("visible")
        support = p023_support(analyzed_subject, P023VisibilityState.VISIBLE)
        with self.assertRaises(BoundedRecursiveAnalysisContractError):
            BoundedRecursiveAnalysisResolution(
                analyzed_subject,
                AnalysisResolutionState.UNRESOLVED_FINER_DATA_REQUIRED,
                "VISIBLE allows analysis to continue; it proves nothing.",
                supporting_visibility_result=support,
            )
        with self.assertRaises(BoundedRecursiveAnalysisContractError):
            BoundedRecursiveAnalysisResolution(
                analyzed_subject,
                AnalysisResolutionState.VALIDATED_FAMILY,
                "Visibility is not validity.",
                supporting_visibility_result=support,
            )

    def test_malformed_p023_missing_input_does_not_become_finer_data_stop(self) -> None:
        analyzed_subject = subject("malformed-visibility")
        support = evaluate_p023_visibility_for_subject(
            analyzed_subject,
            P023VisibilityInput("MALFORMED"),
        )
        with self.assertRaises(BoundedRecursiveAnalysisContractError):
            BoundedRecursiveAnalysisResolution(
                analyzed_subject,
                AnalysisResolutionState.UNRESOLVED_FINER_DATA_REQUIRED,
                "Malformed visibility is not the approved UNKNOWN boundary.",
                supporting_visibility_result=support,
            )

    def test_wrong_subject_and_fake_p023_support_are_rejected(self) -> None:
        first = subject("first")
        second = subject("second")
        genuine = p023_support(first, P023VisibilityState.NOT_VISIBLE)
        fake_wrapper = object.__new__(SubjectBoundP023VisibilityResult)
        raw_result = check_p023_visibility_guard(
            P023VisibilityInput(P023VisibilityState.NOT_VISIBLE)
        )
        for supplied in (genuine, fake_wrapper, raw_result, asdict(raw_result)):
            with self.subTest(kind=type(supplied).__name__):
                with self.assertRaises(BoundedRecursiveAnalysisContractError):
                    BoundedRecursiveAnalysisResolution(
                        second,
                        AnalysisResolutionState.UNRESOLVED_FINER_DATA_REQUIRED,
                        "Cross-subject or fake visibility is rejected.",
                        supporting_visibility_result=supplied,
                    )

    def test_p023_binding_copy_pickle_and_tamper_guards(self) -> None:
        analyzed_subject = subject("visibility-identity")
        support = p023_support(analyzed_subject, P023VisibilityState.NOT_VISIBLE)
        self.assertIs(support, copy.copy(support))
        self.assertIs(support, copy.deepcopy(support))
        with self.assertRaises(TypeError):
            pickle.dumps(support)
        object.__setattr__(support.result, "reason", "tampered")
        with self.assertRaises(BoundedRecursiveAnalysisContractError):
            _ = support.result

    def test_each_known_dependency_has_only_unresolved_semantics(self) -> None:
        expected = {
            "FAMILY_PRODUCER_UNAVAILABLE",
            "NESTED_FAMILY_CERTIFICATE_UNAVAILABLE",
            "COMPLETION_AUTHORITY_UNAVAILABLE",
            "POSITION_AUTHORITY_UNAVAILABLE",
            "ENDPOINT_AUTHORITY_UNAVAILABLE",
            "P005_P006_PROOF_BLOCKED",
        }
        self.assertEqual(expected, {code.value for code in MethodologyDependencyCode})
        for code in MethodologyDependencyCode:
            with self.subTest(code=code):
                resolution = dependency_resolution(subject(code.value), code)
                self.assertIs(
                    AnalysisResolutionState.UNRESOLVED_METHODOLOGY_DEPENDENCY,
                    resolution.state,
                )
                self.assertIsNone(resolution.supporting_family_certificate)
                self.assertIsNone(
                    resolution.supporting_structural_invalidity_certificate
                )

    def test_dependency_support_and_arbitrary_codes_cannot_create_validity(self) -> None:
        analyzed_subject = subject("dependency")
        with self.assertRaises(BoundedRecursiveAnalysisContractError):
            BoundedRecursiveAnalysisResolution(
                analyzed_subject,
                AnalysisResolutionState.UNRESOLVED_METHODOLOGY_DEPENDENCY,
                "Unknown codes fail closed.",
                dependency_code="ARBITRARY",
            )
        with self.assertRaises(BoundedRecursiveAnalysisContractError):
            BoundedRecursiveAnalysisResolution(
                analyzed_subject,
                AnalysisResolutionState.VALIDATED_FAMILY,
                "A dependency code is not positive proof.",
                dependency_code=MethodologyDependencyCode.FAMILY_PRODUCER_UNAVAILABLE,
            )

    def test_invalid_child_has_precedence_over_unresolved_child(self) -> None:
        invalid_subject = subject("invalid-child")
        unresolved_subject = subject("unresolved-child")
        invalid = leaf(invalid_subject, invalid_resolution(invalid_subject))
        unresolved = leaf(
            unresolved_subject,
            finer_resolution(unresolved_subject),
        )
        for children in ((invalid,), (unresolved, invalid), (invalid, unresolved)):
            with self.subTest(order=tuple(child.subject.subject_id for child in children)):
                self.assertIs(
                    OperationalAggregationState.BLOCKED_BY_INVALID_CHILD,
                    aggregate_supplied_child_resolutions(children),
                )

    def test_unresolved_child_blocks_without_becoming_invalid_or_valid(self) -> None:
        first = subject("dependency-child")
        second = subject("visibility-child")
        children = (
            leaf(first, dependency_resolution(first)),
            leaf(second, finer_resolution(second)),
        )
        self.assertIs(
            OperationalAggregationState.BLOCKED_BY_UNRESOLVED_CHILD,
            aggregate_supplied_child_resolutions(children),
        )

    def test_empty_supplied_tuple_is_vacuously_operationally_resolved_only(self) -> None:
        self.assertIs(
            OperationalAggregationState.CHILDREN_OPERATIONALLY_RESOLVED,
            aggregate_supplied_child_resolutions(()),
        )
        source_text = inspect.getsource(aggregate_supplied_child_resolutions)
        self.assertIn("cannot establish parent validity", source_text)
        self.assertIn("nothing about methodology-required children", source_text)

    def test_aggregation_and_operational_objects_cannot_issue_certificates(self) -> None:
        resolution = dependency_resolution(subject("no-certificate"))
        aggregation = aggregate_supplied_child_resolutions(
            (leaf(resolution.subject, resolution),)
        )
        for value in (resolution, aggregation):
            with self.subTest(value=value):
                with self.assertRaises(Exception):
                    certify_validated_internal_family(value)
                with self.assertRaises(Exception):
                    certify_structural_invalidity(value)

    def test_low_level_resolution_mutation_is_detected_by_node_and_aggregation(self) -> None:
        analyzed_subject = subject("tampered-resolution")
        resolution = dependency_resolution(analyzed_subject)
        node = leaf(analyzed_subject, resolution)
        object.__setattr__(resolution, "state", AnalysisResolutionState.VALIDATED_FAMILY)
        with self.assertRaises(BoundedRecursiveAnalysisContractError):
            aggregate_supplied_child_resolutions((node,))

    def test_arbitrary_ids_do_not_establish_subject_authority(self) -> None:
        original = subject("same-id")
        recreated = subject("same-id")
        self.assertIsNot(original, recreated)
        support = p023_support(original, P023VisibilityState.NOT_VISIBLE)
        with self.assertRaises(BoundedRecursiveAnalysisContractError):
            BoundedRecursiveAnalysisResolution(
                recreated,
                AnalysisResolutionState.UNRESOLVED_FINER_DATA_REQUIRED,
                "Equal opaque IDs are not identity authority.",
                supporting_visibility_result=support,
            )

    def test_operational_contract_does_not_change_p023_or_structural_results(self) -> None:
        analyzed_subject = subject("unchanged-methodology")
        p023_before = check_p023_visibility_guard(
            P023VisibilityInput(P023VisibilityState.NOT_VISIBLE)
        )
        support = p023_support(analyzed_subject, P023VisibilityState.NOT_VISIBLE)
        _ = finer_resolution(analyzed_subject)
        p023_after = check_p023_visibility_guard(
            P023VisibilityInput(P023VisibilityState.NOT_VISIBLE)
        )
        self.assertEqual(p023_before, p023_after)
        self.assertEqual(p023_before, support.result)
        certificate = structural_certificate(analyzed_subject)
        origin_fields = tuple(getattr(certificate.origin, field.name) for field in fields(certificate.origin))
        _ = BoundedRecursiveAnalysisResolution(
            analyzed_subject,
            AnalysisResolutionState.STRUCTURALLY_INVALID,
            "Transport only.",
            supporting_structural_invalidity_certificate=certificate,
        )
        self.assertEqual(
            origin_fields,
            tuple(getattr(certificate.origin, field.name) for field in fields(certificate.origin)),
        )

    def test_public_surface_is_narrow_and_contains_no_methodology_authority(self) -> None:
        expected = {
            "AnalysisResolutionState",
            "BoundedRecursiveAnalysisContractError",
            "BoundedRecursiveAnalysisNode",
            "BoundedRecursiveAnalysisResolution",
            "MethodologyDependencyCode",
            "OperationalAggregationState",
            "SubjectBoundP023VisibilityResult",
            "aggregate_supplied_child_resolutions",
            "evaluate_p023_visibility_for_subject",
        }
        self.assertTrue(expected.issubset(set(kernel.__all__)))
        fields_present = set(BoundedRecursiveAnalysisNode.__dataclass_fields__)
        self.assertEqual(
            {"subject", "child_binding", "children", "resolution"},
            fields_present,
        )
        forbidden = {
            "wave_label", "degree", "family", "completion", "direction",
            "parentage", "confidence", "rank", "preferred", "alternative",
        }
        self.assertTrue(forbidden.isdisjoint(fields_present))

    def test_module_dependency_and_capability_boundary(self) -> None:
        path = support.SRC / "elliott_methodology_kernel" / "bounded_recursive_analysis.py"
        source_text = path.read_text(encoding="utf-8")
        tree = ast.parse(source_text, filename=str(path))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add("." * node.level + (node.module or ""))
        self.assertEqual(
            {
                "__future__", "dataclasses", "enum", "threading", "weakref",
                "._structural_invalidity_certification",
                "._validated_internal_family_certification",
                ".p023_visibility_guard", ".subject_binding",
            },
            imports,
        )
        for forbidden in (
            "TradingView", "socket", "subprocess", "requests", "urllib",
            "provider", "alert", "RSI", "Fibonacci", "volume",
            "timeframe", "pivot", "wave discovery", "confidence percentage",
            "PREFERRED", "ALTERNATIVE", "TRADE", "WAIT", "STAND_ASIDE",
        ):
            self.assertNotIn(forbidden, source_text)

    def test_methodology_inventory_and_registries_remain_exact(self) -> None:
        kernel_root = support.SRC / "elliott_methodology_kernel"
        observed = set()
        for path in kernel_root.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if (
                            isinstance(target, ast.Name)
                            and target.id.endswith(("BEHAVIOR_ID", "BEHAVIOR"))
                            and isinstance(node.value, ast.Constant)
                            and isinstance(node.value.value, str)
                        ):
                            observed.add(node.value.value)
                elif (
                    isinstance(node, ast.AnnAssign)
                    and isinstance(node.target, ast.Name)
                    and node.target.id.endswith(("BEHAVIOR_ID", "BEHAVIOR"))
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

    def test_methodology_kernel_analyze_remains_not_implemented(self) -> None:
        source_text = inspect.getsource(kernel.MethodologyKernel.analyze)
        self.assertIn("status=KernelStatus.NOT_IMPLEMENTED", source_text)
        self.assertIs(KernelStatus.NOT_IMPLEMENTED, KernelStatus.NOT_IMPLEMENTED)
        self.assertNotIn("BoundedRecursiveAnalysis", source_text)


if __name__ == "__main__":
    unittest.main()
