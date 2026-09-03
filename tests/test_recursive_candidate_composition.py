import ast
import copy
from dataclasses import FrozenInstanceError, fields
import pickle
import unittest

import support
import elliott_methodology_kernel as kernel_package
import elliott_methodology_kernel._structural_invalidity_certification as structural_private
import elliott_methodology_kernel._validated_internal_family_certification as family_private
import elliott_methodology_kernel.candidate_analysis_envelope as envelope_module
import elliott_methodology_kernel.recursive_candidate_composition as composition_module
from elliott_methodology_kernel import (
    AnalysisResolutionState,
    AnalyzedWaveSubject,
    BoundedManualChartAnalysisRequest,
    BoundedManualChartFinalSummary,
    BoundedRecursiveAnalysisNode,
    BoundedRecursiveAnalysisResolution,
    CandidateScope,
    CertifiedStructuralInvalidity,
    CertifiedValidatedInternalFamily,
    ImpulseDirection,
    ManualCardinalityBehavior,
    ManualDirectChildCardinalityFact,
    ManualP004Wave2OriginFact,
    MethodologyKernel,
    MethodologyDependencyCode,
    OperationalAggregationState,
    OrderedChildBinding,
    P009CandidateScope,
    P009TriangleCardinalityInput,
    RecursiveCandidateCompositionError,
    RecursiveCandidateCompositionRequest,
    RecursiveCandidateCompositionResult,
    RecursiveCandidateCompositionSummary,
    certify_structural_invalidity,
    check_p009_triangle_cardinality,
)


def subject(name: str) -> AnalyzedWaveSubject:
    return AnalyzedWaveSubject(name, f"observations:{name}")


def reviewed_candidate(analyzed_subject: AnalyzedWaveSubject):
    request = BoundedManualChartAnalysisRequest(
        request_id=f"reviewed:{analyzed_subject.subject_id}",
        requested_at_utc="2026-09-03T12:00:00Z",
        subject=analyzed_subject,
        candidate_id=f"candidate:{analyzed_subject.subject_id}",
        manual_behavior_facts=(
            ManualP004Wave2OriginFact(
                CandidateScope.NORMAL_IMPULSE,
                ImpulseDirection.UP,
                100,
                101,
            ),
        ),
        provenance_refs=(f"candidate:{analyzed_subject.subject_id}",),
    )
    return MethodologyKernel(support.PROTECTED_ROOT).analyze_bounded_manual_chart(request)


def unresolved_candidate(analyzed_subject: AnalyzedWaveSubject):
    request = BoundedManualChartAnalysisRequest(
        request_id=f"unresolved:{analyzed_subject.subject_id}",
        requested_at_utc="2026-09-03T12:00:00Z",
        subject=analyzed_subject,
        candidate_id=f"candidate:{analyzed_subject.subject_id}",
        provenance_refs=(f"candidate:{analyzed_subject.subject_id}",),
    )
    return MethodologyKernel(support.PROTECTED_ROOT).analyze_bounded_manual_chart(request)


def invalid_candidate(analyzed_subject: AnalyzedWaveSubject):
    children = tuple(subject(f"{analyzed_subject.subject_id}:child:{index}") for index in range(3))
    binding = OrderedChildBinding(
        f"invalid-binding:{analyzed_subject.subject_id}",
        analyzed_subject,
        children,
    )
    certificate = certify_structural_invalidity(
        check_p009_triangle_cardinality(
            P009TriangleCardinalityInput(P009CandidateScope.TRIANGLE, binding)
        )
    )
    request = BoundedManualChartAnalysisRequest(
        request_id=f"invalid:{analyzed_subject.subject_id}",
        requested_at_utc="2026-09-03T12:00:00Z",
        subject=analyzed_subject,
        candidate_id=f"candidate:{analyzed_subject.subject_id}",
        manual_behavior_facts=(
            ManualDirectChildCardinalityFact(ManualCardinalityBehavior.TRIANGLE),
        ),
        child_binding=binding,
        trusted_invalidity_certificates=(certificate,),
        no_rescue_requested=True,
        provenance_refs=(f"candidate:{analyzed_subject.subject_id}",),
    )
    result = MethodologyKernel(support.PROTECTED_ROOT).analyze_bounded_manual_chart(request)
    assert result.final_summary is BoundedManualChartFinalSummary.STRUCTURALLY_INVALID
    return result


def composition_request(parent, children=(), request_id="composition"):
    child_tuple = tuple(children)
    binding = OrderedChildBinding(
        f"binding:{request_id}",
        parent.subject,
        tuple(
            child.subject
            if type(child) is not RecursiveCandidateCompositionResult
            else child.parent_candidate_result.subject
            for child in child_tuple
        ),
    )
    return RecursiveCandidateCompositionRequest(
        request_id=request_id,
        parent_candidate_result=parent,
        ordered_child_candidate_results=child_tuple,
        child_binding=binding,
        provenance_refs=(f"composition:{request_id}",),
    )


def compose(parent, children=(), request_id="composition"):
    request = composition_request(parent, children, request_id)
    return MethodologyKernel(support.PROTECTED_ROOT).compose_recursive_candidate(request)


class RecursiveCandidateCompositionTests(unittest.TestCase):
    def test_classification_and_exact_summary_vocabulary(self) -> None:
        self.assertEqual("PROJECT_ANALYSIS_INFRASTRUCTURE", composition_module.ARTIFACT_CLASSIFICATION)
        self.assertEqual("PROJECT_OPERATIONAL_POLICY", composition_module.WORKFLOW_POLICY_CLASSIFICATION)
        self.assertEqual("CALLER_SUPPLIED_STRUCTURE_DECLARATION", composition_module.RELATIONSHIP_CLASSIFICATION)
        self.assertEqual(
            {
                "BLOCKED_BY_STRUCTURAL_INVALIDITY",
                "BLOCKED_BY_UNRESOLVED_DESCENDANT",
                "RECURSIVE_SCOPE_OPERATIONALLY_REVIEWED",
            },
            {item.value for item in RecursiveCandidateCompositionSummary},
        )

    def test_exact_request_is_immutable_and_retains_live_identities(self) -> None:
        parent = reviewed_candidate(subject("request-parent"))
        first = reviewed_candidate(subject("request-first"))
        second = reviewed_candidate(subject("request-second"))
        request = composition_request(parent, (first, second), "request-exact")
        self.assertIs(parent, request.parent_candidate_result)
        self.assertIs(first, request.ordered_child_candidate_results[0])
        self.assertIs(second, request.ordered_child_candidate_results[1])
        self.assertIs(request, copy.copy(request))
        self.assertIs(request, copy.deepcopy(request))
        with self.assertRaises(FrozenInstanceError):
            request.request_id = "changed"
        with self.assertRaises(TypeError):
            pickle.dumps(request)

    def test_mapping_duck_and_subclass_requests_are_rejected(self) -> None:
        class Duck:
            parent_candidate_result = object()

        with self.assertRaises(TypeError):
            type("RequestSubclass", (RecursiveCandidateCompositionRequest,), {})
        for value in ({"request_id": "mapping"}, Duck(), object()):
            with self.subTest(kind=type(value).__name__):
                with self.assertRaises(RecursiveCandidateCompositionError):
                    MethodologyKernel(support.PROTECTED_ROOT).compose_recursive_candidate(value)

    def test_parent_and_child_result_lookalikes_are_rejected(self) -> None:
        parent = reviewed_candidate(subject("exact-parent"))
        child = reviewed_candidate(subject("exact-child"))
        binding = OrderedChildBinding("exact-binding", parent.subject, (child.subject,))
        for supplied_parent, supplied_children in (
            ({"subject": parent.subject}, (child,)),
            (parent, ({"subject": child.subject},)),
            (parent, (object(),)),
        ):
            with self.subTest(parent=type(supplied_parent), child=type(supplied_children[0])):
                with self.assertRaises(RecursiveCandidateCompositionError):
                    RecursiveCandidateCompositionRequest(
                        "exact-types",
                        supplied_parent,
                        supplied_children,
                        binding,
                    )

    def test_subject_binding_parent_child_and_order_are_exact(self) -> None:
        parent = reviewed_candidate(subject("binding-parent"))
        first = reviewed_candidate(subject("binding-first"))
        second = reviewed_candidate(subject("binding-second"))
        valid = composition_request(parent, (first, second), "binding-valid")
        result = MethodologyKernel(support.PROTECTED_ROOT).compose_recursive_candidate(valid)
        self.assertIs(parent.subject, result.child_binding.parent_subject)
        self.assertIs(first.subject, result.child_binding.ordered_children[0])
        self.assertIs(second.subject, result.child_binding.ordered_children[1])
        for binding in (
            OrderedChildBinding("wrong-parent", subject("other-parent"), (first.subject, second.subject)),
            OrderedChildBinding("reordered", parent.subject, (second.subject, first.subject)),
            OrderedChildBinding("missing", parent.subject, (first.subject,)),
            OrderedChildBinding("extra", parent.subject, (first.subject, second.subject, subject("extra"))),
        ):
            with self.subTest(binding=binding.binding_id):
                with self.assertRaises(RecursiveCandidateCompositionError):
                    RecursiveCandidateCompositionRequest(
                        "bad-binding",
                        parent,
                        (first, second),
                        binding,
                    )

    def test_lookalike_subject_identity_cannot_match_binding(self) -> None:
        parent = reviewed_candidate(subject("lookalike-parent"))
        child = reviewed_candidate(subject("lookalike-child"))
        lookalike = AnalyzedWaveSubject(child.subject.subject_id, child.subject.observation_provenance_ref)
        binding = OrderedChildBinding("lookalike", parent.subject, (lookalike,))
        with self.assertRaises(RecursiveCandidateCompositionError):
            RecursiveCandidateCompositionRequest("lookalike", parent, (child,), binding)

    def test_duplicate_child_result_or_subject_is_rejected_without_deduplication(self) -> None:
        parent = reviewed_candidate(subject("duplicate-parent"))
        child = reviewed_candidate(subject("duplicate-child"))
        malformed_binding = object.__new__(OrderedChildBinding)
        object.__setattr__(malformed_binding, "binding_id", "duplicate")
        object.__setattr__(malformed_binding, "parent_subject", parent.subject)
        object.__setattr__(malformed_binding, "ordered_children", (child.subject, child.subject))
        with self.assertRaises(RecursiveCandidateCompositionError):
            RecursiveCandidateCompositionRequest(
                "duplicate",
                parent,
                (child, child),
                malformed_binding,
            )

    def test_parent_as_child_is_rejected(self) -> None:
        parent = reviewed_candidate(subject("self-parent"))
        binding = object.__new__(OrderedChildBinding)
        object.__setattr__(binding, "binding_id", "self")
        object.__setattr__(binding, "parent_subject", parent.subject)
        object.__setattr__(binding, "ordered_children", (parent.subject,))
        with self.assertRaises(RecursiveCandidateCompositionError):
            RecursiveCandidateCompositionRequest("self", parent, (parent,), binding)

    def test_nodes_reuse_exact_contract_and_retain_order_without_inference(self) -> None:
        parent = reviewed_candidate(subject("node-parent"))
        children = (
            reviewed_candidate(subject("node-first")),
            reviewed_candidate(subject("node-second")),
        )
        result = compose(parent, children, "nodes")
        self.assertIs(BoundedRecursiveAnalysisNode, type(result.parent_node))
        self.assertTrue(all(type(node) is BoundedRecursiveAnalysisNode for node in result.child_nodes))
        self.assertIs(parent.subject, result.parent_node.subject)
        self.assertIs(result.child_nodes, result.parent_node.children)
        self.assertEqual(tuple(item.subject for item in children), tuple(node.subject for node in result.child_nodes))
        forbidden = {"label", "degree", "family", "timeframe", "rank", "complete"}
        self.assertTrue(forbidden.isdisjoint(RecursiveCandidateCompositionResult.__dataclass_fields__))

    def test_existing_exact_parent_operational_resolution_is_retained(self) -> None:
        parent_subject = subject("exact-resolution-parent")
        resolution = BoundedRecursiveAnalysisResolution(
            subject=parent_subject,
            state=AnalysisResolutionState.UNRESOLVED_METHODOLOGY_DEPENDENCY,
            reason="An exact existing project dependency remains unresolved.",
            dependency_code=MethodologyDependencyCode.FAMILY_PRODUCER_UNAVAILABLE,
            provenance_refs=("resolution:exact",),
        )
        parent = MethodologyKernel(support.PROTECTED_ROOT).analyze_bounded_manual_chart(
            BoundedManualChartAnalysisRequest(
                request_id="exact-resolution",
                requested_at_utc="2026-09-03T12:00:00Z",
                subject=parent_subject,
                candidate_id="exact-resolution-candidate",
                manual_behavior_facts=(
                    ManualP004Wave2OriginFact(
                        CandidateScope.NORMAL_IMPULSE,
                        ImpulseDirection.UP,
                        100,
                        101,
                    ),
                ),
                operational_resolution=resolution,
                provenance_refs=("candidate:exact-resolution",),
            )
        )
        result = compose(parent, (), "exact-resolution-composition")
        self.assertIs(resolution, result.parent_node.resolution)
        self.assertIs(
            RecursiveCandidateCompositionSummary.BLOCKED_BY_UNRESOLVED_DESCENDANT,
            result.composed_summary,
        )

    def test_invalid_unresolved_and_reviewed_child_aggregation(self) -> None:
        parent = reviewed_candidate(subject("aggregation-parent"))
        invalid = invalid_candidate(subject("aggregation-invalid"))
        unresolved = unresolved_candidate(subject("aggregation-unresolved"))
        reviewed = reviewed_candidate(subject("aggregation-reviewed"))
        cases = (
            ((invalid,), OperationalAggregationState.BLOCKED_BY_INVALID_CHILD),
            ((unresolved,), OperationalAggregationState.BLOCKED_BY_UNRESOLVED_CHILD),
            ((reviewed,), OperationalAggregationState.CHILDREN_OPERATIONALLY_RESOLVED),
            ((unresolved, invalid), OperationalAggregationState.BLOCKED_BY_INVALID_CHILD),
        )
        for index, (children, expected) in enumerate(cases):
            with self.subTest(expected=expected):
                self.assertIs(expected, compose(parent, children, f"aggregation-{index}").child_aggregation)

    def test_parent_and_child_precedence_are_separate_and_conservative(self) -> None:
        cases = (
            (
                invalid_candidate(subject("parent-invalid")),
                (unresolved_candidate(subject("child-unresolved-for-invalid-parent")),),
                RecursiveCandidateCompositionSummary.BLOCKED_BY_STRUCTURAL_INVALIDITY,
            ),
            (
                unresolved_candidate(subject("parent-unresolved")),
                (reviewed_candidate(subject("child-reviewed-for-unresolved-parent")),),
                RecursiveCandidateCompositionSummary.BLOCKED_BY_UNRESOLVED_DESCENDANT,
            ),
            (
                reviewed_candidate(subject("parent-reviewed")),
                (reviewed_candidate(subject("child-reviewed")),),
                RecursiveCandidateCompositionSummary.RECURSIVE_SCOPE_OPERATIONALLY_REVIEWED,
            ),
        )
        for index, (parent, children, expected) in enumerate(cases):
            with self.subTest(expected=expected):
                result = compose(parent, children, f"precedence-{index}")
                self.assertIs(expected, result.composed_summary)
                self.assertIs(parent.final_summary, result.parent_candidate_result.final_summary)

    def test_recursive_reviewed_state_has_no_validity_completion_or_family_meaning(self) -> None:
        result = compose(
            reviewed_candidate(subject("meaning-parent")),
            (reviewed_candidate(subject("meaning-child")),),
            "meaning",
        )
        self.assertIs(
            RecursiveCandidateCompositionSummary.RECURSIVE_SCOPE_OPERATIONALLY_REVIEWED,
            result.composed_summary,
        )
        self.assertNotIn("VALID", result.composed_summary.value)
        self.assertNotIn("COMPLETE", result.composed_summary.value)
        self.assertNotIsInstance(result, CertifiedValidatedInternalFamily)
        with self.assertRaises(Exception):
            kernel_package.certify_validated_internal_family(result)

    def test_invalidity_evidence_identity_is_retained_and_no_parent_certificate_is_synthesized(self) -> None:
        parent = reviewed_candidate(subject("evidence-parent"))
        invalid = invalid_candidate(subject("evidence-child"))
        certificate = invalid.structural_invalidity_certificates[0]
        before = tuple(structural_private._PRODUCERS)
        result = compose(parent, (invalid,), "evidence")
        after = tuple(structural_private._PRODUCERS)
        self.assertIs(certificate, result.structural_invalidity_evidence_refs[0])
        self.assertEqual(1, len(result.structural_invalidity_evidence_refs))
        self.assertEqual(before, after)
        self.assertIs(
            RecursiveCandidateCompositionSummary.BLOCKED_BY_STRUCTURAL_INVALIDITY,
            result.composed_summary,
        )

    def test_parent_invalidity_evidence_is_retained_without_rescue(self) -> None:
        parent = invalid_candidate(subject("invalid-parent"))
        child = reviewed_candidate(subject("reviewed-child-of-invalid"))
        result = compose(parent, (child,), "parent-no-rescue")
        self.assertIs(parent.structural_invalidity_certificates[0], result.structural_invalidity_evidence_refs[0])
        self.assertIs(
            RecursiveCandidateCompositionSummary.BLOCKED_BY_STRUCTURAL_INVALIDITY,
            result.composed_summary,
        )

    def test_all_parent_and_child_unresolved_reasons_are_retained_in_order(self) -> None:
        parent = unresolved_candidate(subject("reasons-parent"))
        first = unresolved_candidate(subject("reasons-first"))
        second = unresolved_candidate(subject("reasons-second"))
        result = compose(parent, (first, second), "reasons")
        expected = parent.unresolved_reasons + first.unresolved_reasons + second.unresolved_reasons
        self.assertEqual(expected, result.unresolved_reasons)
        self.assertIs(
            RecursiveCandidateCompositionSummary.BLOCKED_BY_UNRESOLVED_DESCENDANT,
            result.composed_summary,
        )

    def test_zero_children_is_vacuously_resolved_only_not_terminal_or_complete(self) -> None:
        parent = reviewed_candidate(subject("leaf-parent"))
        result = compose(parent, (), "leaf")
        self.assertEqual((), result.child_nodes)
        self.assertIs(OperationalAggregationState.CHILDREN_OPERATIONALLY_RESOLVED, result.child_aggregation)
        self.assertIs(RecursiveCandidateCompositionSummary.RECURSIVE_SCOPE_OPERATIONALLY_REVIEWED, result.composed_summary)
        self.assertTrue({"terminal", "primitive", "complete"}.isdisjoint(RecursiveCandidateCompositionResult.__dataclass_fields__))

    def test_one_and_two_level_explicit_nesting_preserve_exact_nodes(self) -> None:
        leaf = reviewed_candidate(subject("nested-leaf"))
        inner_parent = reviewed_candidate(subject("nested-inner"))
        inner = compose(inner_parent, (leaf,), "inner")
        outer_parent = reviewed_candidate(subject("nested-outer"))
        outer = compose(outer_parent, (inner,), "outer")
        self.assertIs(inner, outer.ordered_child_candidate_results[0])
        self.assertIs(inner.parent_node, outer.child_nodes[0])
        self.assertIs(leaf.subject, outer.parent_node.children[0].children[0].subject)
        self.assertIs(RecursiveCandidateCompositionSummary.RECURSIVE_SCOPE_OPERATIONALLY_REVIEWED, outer.composed_summary)

    def test_descendant_invalidity_and_unresolved_state_propagate(self) -> None:
        invalid_inner = compose(
            reviewed_candidate(subject("invalid-inner-parent")),
            (invalid_candidate(subject("invalid-descendant")),),
            "invalid-inner",
        )
        unresolved_inner = compose(
            reviewed_candidate(subject("unresolved-inner-parent")),
            (unresolved_candidate(subject("unresolved-descendant")),),
            "unresolved-inner",
        )
        invalid_outer = compose(
            reviewed_candidate(subject("invalid-outer-parent")),
            (invalid_inner,),
            "invalid-outer",
        )
        unresolved_outer = compose(
            reviewed_candidate(subject("unresolved-outer-parent")),
            (unresolved_inner,),
            "unresolved-outer",
        )
        self.assertIs(OperationalAggregationState.BLOCKED_BY_INVALID_CHILD, invalid_outer.child_aggregation)
        self.assertIs(RecursiveCandidateCompositionSummary.BLOCKED_BY_STRUCTURAL_INVALIDITY, invalid_outer.composed_summary)
        self.assertIs(invalid_inner.structural_invalidity_evidence_refs[0], invalid_outer.structural_invalidity_evidence_refs[0])
        self.assertIs(OperationalAggregationState.BLOCKED_BY_UNRESOLVED_CHILD, unresolved_outer.child_aggregation)
        self.assertIs(RecursiveCandidateCompositionSummary.BLOCKED_BY_UNRESOLVED_DESCENDANT, unresolved_outer.composed_summary)
        self.assertEqual(unresolved_inner.unresolved_reasons, unresolved_outer.unresolved_reasons)

    def test_low_level_recursive_cycle_and_node_reuse_fail_closed(self) -> None:
        inner = compose(
            reviewed_candidate(subject("cycle-inner")),
            (reviewed_candidate(subject("cycle-leaf")),),
            "cycle-inner",
        )
        object.__setattr__(inner.parent_node, "children", (inner.parent_node,))
        with self.assertRaises(RecursiveCandidateCompositionError):
            compose(
                reviewed_candidate(subject("cycle-outer")),
                (inner,),
                "cycle-outer",
            )

    def test_low_level_request_and_result_mutation_fail_closed(self) -> None:
        parent = reviewed_candidate(subject("mutation-parent"))
        child = reviewed_candidate(subject("mutation-child"))
        request = composition_request(parent, (child,), "mutation")
        object.__setattr__(request, "request_id", "changed")
        with self.assertRaises(RecursiveCandidateCompositionError):
            MethodologyKernel(support.PROTECTED_ROOT).compose_recursive_candidate(request)

        result = compose(parent, (child,), "result-mutation")
        object.__setattr__(result, "composed_summary", RecursiveCandidateCompositionSummary.BLOCKED_BY_STRUCTURAL_INVALIDITY)
        with self.assertRaises(RecursiveCandidateCompositionError):
            copy.copy(result)

        binding_request = composition_request(parent, (child,), "binding-mutation")
        object.__setattr__(binding_request.child_binding, "binding_id", "")
        with self.assertRaises(RecursiveCandidateCompositionError):
            MethodologyKernel(support.PROTECTED_ROOT).compose_recursive_candidate(
                binding_request
            )

    def test_serialized_and_arbitrary_id_lookalikes_create_no_authority(self) -> None:
        parent = reviewed_candidate(subject("serialized-parent"))
        child = reviewed_candidate(subject("serialized-child"))
        request = composition_request(parent, (child,), "serialized")
        result = MethodologyKernel(support.PROTECTED_ROOT).compose_recursive_candidate(request)
        with self.assertRaises(TypeError):
            pickle.dumps(result)
        with self.assertRaises(RecursiveCandidateCompositionError):
            MethodologyKernel(support.PROTECTED_ROOT).compose_recursive_candidate(
                {
                    "request_id": result.request_id,
                    "parent_candidate_result": {"candidate_id": parent.candidate_id},
                }
            )

    def test_result_is_factory_only_immutable_and_not_methodology_or_certificate(self) -> None:
        result = compose(reviewed_candidate(subject("result-parent")), (), "result")
        self.assertIs(RecursiveCandidateCompositionResult, type(result))
        self.assertIs(result, copy.copy(result))
        self.assertIs(result, copy.deepcopy(result))
        with self.assertRaises(TypeError):
            RecursiveCandidateCompositionResult()
        with self.assertRaises(TypeError):
            type("ResultSubclass", (RecursiveCandidateCompositionResult,), {})
        with self.assertRaises(FrozenInstanceError):
            result.provenance_refs = ()
        self.assertNotIsInstance(result, CertifiedStructuralInvalidity)
        self.assertNotIsInstance(result, CertifiedValidatedInternalFamily)

    def test_public_result_surface_is_exact_and_has_no_authority_fields(self) -> None:
        self.assertEqual(
            {
                "request_id",
                "parent_candidate_result",
                "ordered_child_candidate_results",
                "child_binding",
                "parent_node",
                "child_nodes",
                "child_aggregation",
                "composed_summary",
                "unresolved_reasons",
                "structural_invalidity_evidence_refs",
                "provenance_refs",
                "_request",
                "_identity_snapshot",
            },
            {item.name for item in fields(RecursiveCandidateCompositionResult)},
        )
        forbidden = {"source_class", "source_principle_id", "execution_role", "rank", "confidence", "trade"}
        self.assertTrue(forbidden.isdisjoint(RecursiveCandidateCompositionResult.__dataclass_fields__))

    def test_no_dynamic_dispatch_discovery_external_capability_or_forbidden_imports(self) -> None:
        path = support.SRC / "elliott_methodology_kernel" / "recursive_candidate_composition.py"
        source_text = path.read_text(encoding="utf-8")
        tree = ast.parse(source_text)
        imports = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        } | {
            (node.module or "").split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.level == 0
        }
        self.assertTrue(
            imports.isdisjoint(
                {"socket", "urllib", "requests", "http", "subprocess", "selenium", "playwright", "tradingview"}
            )
        )
        calls = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertTrue({"eval", "exec", "__import__"}.isdisjoint(calls))
        self.assertNotIn("check_p004", source_text)
        self.assertNotIn("check_p00", source_text)
        self.assertNotIn("certify_structural_invalidity(", source_text)
        self.assertNotIn("certify_validated_internal_family(", source_text)

    def test_no_family_issuance_and_inventories_remain_exact(self) -> None:
        before = (
            tuple(family_private._PRODUCERS),
            len(family_private._ISSUED),
            family_private._REGISTRY_SEALED,
        )
        compose(
            reviewed_candidate(subject("inventory-parent")),
            (reviewed_candidate(subject("inventory-child")),),
            "inventory",
        )
        after = (
            tuple(family_private._PRODUCERS),
            len(family_private._ISSUED),
            family_private._REGISTRY_SEALED,
        )
        self.assertEqual(before, after)
        self.assertEqual((), after[0])
        self.assertEqual(0, after[1])
        self.assertIs(True, after[2])
        self.assertEqual(7, len(structural_private._PRODUCERS))
        self.assertEqual(10, len(envelope_module._BEHAVIOR_COMPATIBILITY))

    def test_legacy_analyze_remains_not_implemented(self) -> None:
        source_text = (support.SRC / "elliott_methodology_kernel" / "api.py").read_text(encoding="utf-8")
        self.assertIn("status=KernelStatus.NOT_IMPLEMENTED", source_text)
        self.assertIn("def compose_recursive_candidate(", source_text)


if __name__ == "__main__":
    unittest.main()
