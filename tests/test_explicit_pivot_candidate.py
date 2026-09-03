import ast
import copy
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import FrozenInstanceError
import io
import json
from pathlib import Path
import pickle
import unittest

import support
import elliott_methodology_kernel._structural_invalidity_certification as structural_private
import elliott_methodology_kernel._validated_internal_family_certification as family_private
import elliott_methodology_kernel.explicit_behavior_execution as execution_private
from elliott_methodology_kernel import (
    EXPLICIT_PIVOT_INPUT_SCHEMA_VERSION,
    EXPLICIT_PIVOT_REPORT_SCHEMA_VERSION,
    AnalyzedWaveSubject,
    CandidateScope,
    ExplicitP004PivotRole,
    ExplicitPivotCandidateBuildResult,
    ExplicitPivotCandidateError,
    ExplicitPivotCandidateRequest,
    ExplicitPivotChildGroup,
    ExplicitPivotObservation,
    ImpulseDirection,
    ManualCardinalityBehavior,
    ManualDegreePeerFact,
    ManualDirectChildCardinalityFact,
    ManualP003OneLargerDegreeRelationFact,
    ManualP023VisibilityFact,
    ManualParentChildDegreeFact,
    MethodologyKernel,
    P003OneLargerDegreeRelation,
    P023VisibilityState,
    SubjectBoundObservedPriceEndpointPair,
    SubjectBoundObservedPriceObservation,
    parse_human_readable_explicit_pivot_candidate,
    render_explicit_pivot_report,
)
from elliott_methodology_kernel.models import DegreeStatus, DegreeTreeNode, InternalStatus
from elliott_runtime.manual_candidate_cli import load_manual_candidate_file, main


EXAMPLES = support.RUNTIME_ROOT / "examples" / "explicit_pivot_candidate"
MODULE = support.SRC / "elliott_methodology_kernel" / "explicit_pivot_candidate.py"
CLI_MODULE = support.SRC / "elliott_runtime" / "manual_candidate_cli.py"


def subject(name: str) -> AnalyzedWaveSubject:
    return AnalyzedWaveSubject(name, f"manual-chart:{name}")


def pivot(index: int, *, price=None, timestamp=None, pivot_id=None):
    return ExplicitPivotObservation(
        f"p{index}" if pivot_id is None else pivot_id,
        f"2026-09-03T{8 + index:02d}:00:00Z" if timestamp is None else timestamp,
        100 + index if price is None else price,
        (f"pivot:p{index}",),
    )


def base_request(*, pivots=None, groups=(), declarations=(), binding_id=None):
    parent = subject("parent")
    return ExplicitPivotCandidateRequest(
        request_id="pivot-request",
        requested_at_utc="2026-09-03T12:00:00Z",
        candidate_id="pivot-candidate",
        parent_subject=parent,
        ordered_pivots=tuple(pivot(i) for i in range(4)) if pivots is None else pivots,
        ordered_child_groups=groups,
        binding_id=binding_id,
        manual_fact_declarations=declarations,
        provenance_refs=("explicit-pivot:test",),
    )


def grouped_request(selector=ManualCardinalityBehavior.SINGLE_ZIGZAG):
    parent = subject("group-parent")
    pivots = tuple(pivot(i) for i in range(4))
    groups = tuple(
        ExplicitPivotChildGroup(
            f"g{index}",
            parent,
            subject(f"child-{index}"),
            pivots[index],
            pivots[index + 1],
            (f"group:g{index}",),
        )
        for index in range(3)
    )
    return ExplicitPivotCandidateRequest(
        "group-request",
        "2026-09-03T12:00:00Z",
        "group-candidate",
        parent,
        pivots,
        groups,
        "group-binding",
        (ManualDirectChildCardinalityFact(selector),),
        ("explicit-pivot:grouped",),
    )


def kernel() -> MethodologyKernel:
    return MethodologyKernel(support.PROTECTED_ROOT)


class ExplicitPivotCandidateTests(unittest.TestCase):
    def test_exact_pivot_is_immutable_finite_explicit_and_non_authoritative(self) -> None:
        item = pivot(0, price=100.5)
        self.assertEqual("CALLER_SUPPLIED_PIVOT_OBSERVATION", item.classification)
        self.assertEqual(100.5, item.observed_price)
        self.assertIs(item, copy.copy(item))
        self.assertIs(item, copy.deepcopy(item))
        with self.assertRaises(FrozenInstanceError):
            item.observed_price = 5
        with self.assertRaises(TypeError):
            pickle.dumps(item)
        for value in (True, "100", float("inf"), float("-inf"), float("nan")):
            with self.subTest(value=value):
                with self.assertRaises(ExplicitPivotCandidateError):
                    pivot(0, price=value)
        for timestamp in ("", "2026-09-03", "2026-09-03T08:00:00", "badZ"):
            with self.subTest(timestamp=timestamp):
                with self.assertRaises(ExplicitPivotCandidateError):
                    pivot(0, timestamp=timestamp)

    def test_pivot_exact_type_subclass_duck_and_mapping_boundaries(self) -> None:
        with self.assertRaises(TypeError):
            type("PivotSubclass", (ExplicitPivotObservation,), {})
        for value in ({"pivot_id": "p0"}, object()):
            with self.subTest(value=value):
                with self.assertRaises(ExplicitPivotCandidateError):
                    base_request(pivots=(value,))

    def test_order_is_preserved_and_must_be_strictly_increasing(self) -> None:
        ordered = tuple(pivot(i) for i in range(3))
        request = base_request(pivots=ordered)
        self.assertIs(ordered, request.ordered_pivots)
        for invalid in (
            (ordered[0], ordered[0]),
            (ordered[1], ordered[0]),
            (ordered[0], pivot(9, timestamp=ordered[0].timestamp_utc)),
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ExplicitPivotCandidateError):
                    base_request(pivots=invalid)

    def test_duplicate_pivot_ids_are_rejected_without_sorting(self) -> None:
        with self.assertRaises(ExplicitPivotCandidateError):
            base_request(pivots=(pivot(0), pivot(1, pivot_id="p0")))

    def test_explicit_groups_preserve_child_order_and_build_existing_binding(self) -> None:
        request = grouped_request()
        self.assertEqual(
            "CALLER_SUPPLIED_STRUCTURE_DECLARATION",
            request.ordered_child_groups[0].classification,
        )
        self.assertIs(request.parent_subject, request.child_binding.parent_subject)
        self.assertEqual(
            tuple(group.child_subject for group in request.ordered_child_groups),
            request.child_binding.ordered_children,
        )
        self.assertEqual("group-binding", request.child_binding.binding_id)

    def test_no_group_is_inferred_from_pivot_count(self) -> None:
        request = base_request()
        self.assertEqual(4, len(request.ordered_pivots))
        self.assertEqual((), request.ordered_child_groups)
        self.assertIsNone(request.child_binding)

    def test_group_boundaries_must_belong_to_request_and_parent_must_match(self) -> None:
        parent = subject("expected")
        pivots = (pivot(0), pivot(1))
        foreign_pivot = pivot(2)
        foreign_parent = subject("foreign")
        invalid_groups = (
            ExplicitPivotChildGroup("g", parent, subject("child"), pivots[0], foreign_pivot),
            ExplicitPivotChildGroup("g", foreign_parent, subject("child2"), pivots[0], pivots[1]),
        )
        for group in invalid_groups:
            with self.subTest(group=group):
                with self.assertRaises(ExplicitPivotCandidateError):
                    ExplicitPivotCandidateRequest(
                        "r", "2026-09-03T12:00:00Z", "c", parent, pivots, (group,), "b"
                    )

    def test_groups_must_be_ordered_and_nonoverlapping_except_shared_boundary(self) -> None:
        parent = subject("overlap-parent")
        pivots = tuple(pivot(i) for i in range(4))
        first = ExplicitPivotChildGroup("g1", parent, subject("c1"), pivots[0], pivots[2])
        overlapping = ExplicitPivotChildGroup("g2", parent, subject("c2"), pivots[1], pivots[3])
        with self.assertRaises(ExplicitPivotCandidateError):
            ExplicitPivotCandidateRequest(
                "r", "2026-09-03T12:00:00Z", "c", parent, pivots,
                (first, overlapping), "b"
            )

    def test_parent_observations_and_child_endpoint_pairs_retain_exact_prices(self) -> None:
        request = grouped_request()
        result = kernel().analyze_explicit_pivot_candidate(request)
        self.assertIs(ExplicitPivotCandidateBuildResult, type(result))
        self.assertEqual(len(request.ordered_pivots), len(result.parent_pivot_observations))
        for source, observation in zip(
            request.ordered_pivots, result.parent_pivot_observations, strict=True
        ):
            self.assertIs(SubjectBoundObservedPriceObservation, type(observation))
            self.assertIs(request.parent_subject, observation.subject)
            self.assertIs(source.observed_price, observation.price)
        for group, pair in zip(
            request.ordered_child_groups, result.child_endpoint_pairs, strict=True
        ):
            self.assertIs(SubjectBoundObservedPriceEndpointPair, type(pair))
            self.assertIs(group.child_subject, pair.subject)
            self.assertIs(group.start_pivot.observed_price, pair.proposed_start.price)
            self.assertIs(group.end_pivot.observed_price, pair.proposed_end.price)
        self.assertNotIn("authority", request.ordered_pivots[0].__dataclass_fields__)

    def test_p004_requires_explicit_roles_and_transports_exact_referenced_prices(self) -> None:
        pivots = tuple(pivot(i, price=100 + i * 5) for i in range(3))
        role = ExplicitP004PivotRole(
            CandidateScope.NORMAL_IMPULSE,
            ImpulseDirection.UP,
            pivots[0],
            pivots[2],
        )
        request = base_request(pivots=pivots, declarations=(role,))
        result = kernel().analyze_explicit_pivot_candidate(request)
        fact = result.generated_manual_facts[0]
        self.assertEqual("ManualP004Wave2OriginFact", type(fact).__name__)
        self.assertIs(pivots[0].observed_price, fact.wave1_origin_price)
        self.assertIs(pivots[2].observed_price, fact.wave2_end_price)
        no_role = kernel().analyze_explicit_pivot_candidate(base_request(pivots=pivots))
        self.assertEqual((), no_role.generated_manual_facts)

    def test_cross_request_p004_pivot_reference_fails_closed(self) -> None:
        pivots = tuple(pivot(i) for i in range(2))
        role = ExplicitP004PivotRole(
            CandidateScope.NORMAL_IMPULSE, ImpulseDirection.UP, pivots[0], pivot(3)
        )
        with self.assertRaises(ExplicitPivotCandidateError):
            base_request(pivots=pivots, declarations=(role,))

    def test_each_explicit_cardinality_selector_runs_only_selected_behavior(self) -> None:
        expected = {
            ManualCardinalityBehavior.SINGLE_ZIGZAG: "P007_SINGLE_ZIGZAG_DIRECT_CHILD_CARDINALITY",
            ManualCardinalityBehavior.FLAT: "P008_FLAT_DIRECT_CHILD_CARDINALITY",
            ManualCardinalityBehavior.TRIANGLE: "P009_TRIANGLE_DIRECT_CHILD_CARDINALITY",
            ManualCardinalityBehavior.ENDING_DIAGONAL: "ENDING_DIAGONAL_DIRECT_CHILD_CARDINALITY",
        }
        for selector, behavior_id in expected.items():
            with self.subTest(selector=selector):
                result = kernel().analyze_explicit_pivot_candidate(grouped_request(selector))
                supplied = [
                    item.behavior_id
                    for item in result.bounded_result.methodology_coverage
                    if item.state.value == "SUPPLIED_AND_EXECUTED"
                ]
                self.assertEqual([behavior_id], supplied)

    def test_child_count_without_selector_generates_no_cardinality_fact(self) -> None:
        request = grouped_request()
        request = ExplicitPivotCandidateRequest(
            request.request_id,
            request.requested_at_utc,
            request.candidate_id,
            request.parent_subject,
            request.ordered_pivots,
            request.ordered_child_groups,
            request.binding_id,
            (),
            request.provenance_refs,
        )
        result = kernel().analyze_explicit_pivot_candidate(request)
        self.assertEqual((), result.generated_manual_facts)
        self.assertEqual("UNRESOLVED", result.bounded_result.final_summary.value)

    def test_explicit_p023_degree_and_p003_pass_through_without_pivot_inference(self) -> None:
        parent = subject("facts-parent")
        pivots = (pivot(0, price=200), pivot(1, price=100))
        declarations = (
            ManualP023VisibilityFact(parent, P023VisibilityState.UNKNOWN),
            ManualDegreePeerFact(
                "parent-node",
                (
                    DegreeTreeNode(
                        "child", "Primary", DegreeStatus.RESOLVED, InternalStatus.CONFIRMED
                    ),
                ),
            ),
            ManualParentChildDegreeFact(
                "Primary", DegreeStatus.RESOLVED, "Intermediate", DegreeStatus.RESOLVED
            ),
            ManualP003OneLargerDegreeRelationFact(P003OneLargerDegreeRelation.AGAINST),
        )
        request = ExplicitPivotCandidateRequest(
            "r", "2026-09-03T12:00:00Z", "c", parent, pivots,
            manual_fact_declarations=declarations
        )
        result = kernel().analyze_explicit_pivot_candidate(request)
        self.assertEqual(declarations, result.generated_manual_facts)
        without = kernel().analyze_explicit_pivot_candidate(
            ExplicitPivotCandidateRequest(
                "r2", "2026-09-03T12:00:00Z", "c2", parent, pivots
            )
        )
        self.assertEqual((), without.generated_manual_facts)

    def test_exact_delegation_and_downstream_identity_are_retained(self) -> None:
        result = kernel().analyze_explicit_pivot_candidate(grouped_request())
        self.assertIs(
            result.bounded_request._manual_request,
            result.bounded_result.manual_build_result.request,
        )
        self.assertIs(
            result.bounded_result.candidate_analysis_result,
            result.bounded_result.explicit_execution_result
            .single_candidate_analysis_result,
        )
        self.assertIs(result.child_binding, result.bounded_request.child_binding)
        self.assertIs(result.request.parent_subject, result.bounded_result.subject)

    def test_constructor_mapping_duck_subclass_pickle_and_mutation_fail_closed(self) -> None:
        with self.assertRaises(TypeError):
            ExplicitPivotCandidateBuildResult()
        with self.assertRaises(TypeError):
            type("RequestSubclass", (ExplicitPivotCandidateRequest,), {})
        request = base_request()
        with self.assertRaises(TypeError):
            pickle.dumps(request)
        with self.assertRaises(ExplicitPivotCandidateError):
            kernel().analyze_explicit_pivot_candidate({"ordered_pivots": []})
        object.__setattr__(request.ordered_pivots[0], "observed_price", 999)
        with self.assertRaises(ExplicitPivotCandidateError):
            kernel().analyze_explicit_pivot_candidate(request)
        grouped = grouped_request()
        object.__setattr__(
            grouped.child_binding,
            "ordered_children",
            tuple(reversed(grouped.child_binding.ordered_children)),
        )
        with self.assertRaises(ExplicitPivotCandidateError):
            kernel().analyze_explicit_pivot_candidate(grouped)

    def test_result_mutation_and_serialized_lookalikes_cannot_report_authority(self) -> None:
        result = kernel().analyze_explicit_pivot_candidate(base_request())
        with self.assertRaises(TypeError):
            pickle.dumps(result)
        object.__setattr__(result, "provenance_refs", ("mutated",))
        with self.assertRaises(ExplicitPivotCandidateError):
            render_explicit_pivot_report(result)
        with self.assertRaises(ExplicitPivotCandidateError):
            render_explicit_pivot_report({"candidate_id": "fake"})
        grouped_result = kernel().analyze_explicit_pivot_candidate(grouped_request())
        pair = grouped_result.child_endpoint_pairs[0]
        object.__setattr__(
            pair,
            "proposed_start",
            SubjectBoundObservedPriceObservation(pair.subject, 999, "mutated"),
        )
        with self.assertRaises(ExplicitPivotCandidateError):
            render_explicit_pivot_report(grouped_result)

    def test_new_json_schema_resolves_exact_live_pivots_groups_and_roles(self) -> None:
        request = load_manual_candidate_file(EXAMPLES / "grouped_p004_zigzag.json")
        self.assertIs(ExplicitPivotCandidateRequest, type(request))
        self.assertEqual(EXPLICIT_PIVOT_INPUT_SCHEMA_VERSION, json.loads(
            (EXAMPLES / "grouped_p004_zigzag.json").read_text(encoding="utf-8")
        )["schema_version"])
        group = request.ordered_child_groups[0]
        self.assertIs(request.ordered_pivots[0], group.start_pivot)
        self.assertIs(request.ordered_pivots[1], group.end_pivot)
        role = request.manual_fact_declarations[0]
        self.assertIs(request.ordered_pivots[0], role.wave1_origin_pivot)

    def test_json_unknown_fields_references_discriminators_and_authority_fail_closed(self) -> None:
        base = json.loads(
            (EXAMPLES / "grouped_p004_zigzag.json").read_text(encoding="utf-8")
        )
        variants = []
        extra = copy.deepcopy(base)
        extra["unknown"] = True
        variants.append(extra)
        unknown_pivot = copy.deepcopy(base)
        unknown_pivot["child_groups"][0]["start_pivot_id"] = "missing"
        variants.append(unknown_pivot)
        missing_boundary = copy.deepcopy(base)
        del missing_boundary["child_groups"][0]["end_pivot_id"]
        variants.append(missing_boundary)
        missing_p004_reference = copy.deepcopy(base)
        missing_p004_reference["facts"][0]["wave2_end_pivot_id"] = "missing"
        variants.append(missing_p004_reference)
        unknown_fact = copy.deepcopy(base)
        unknown_fact["facts"][0]["type"] = "INVENTED"
        variants.append(unknown_fact)
        certificate = copy.deepcopy(base)
        certificate["trusted_invalidity_certificates"] = []
        variants.append(certificate)
        direct_p004 = copy.deepcopy(base)
        direct_p004["facts"][0] = {
            "type": "P004_WAVE2_ORIGIN",
            "candidate_scope": "NORMAL_IMPULSE",
            "direction": "UP",
            "wave1_origin_price": 100,
            "wave2_end_price": 101,
        }
        variants.append(direct_p004)
        for document in variants:
            with self.subTest(document=document):
                with self.assertRaises(ExplicitPivotCandidateError):
                    parse_human_readable_explicit_pivot_candidate(document)

    def test_cli_new_schema_report_and_old_schema_backward_compatibility(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(0, main([str(EXAMPLES / "grouped_p004_zigzag.json")]))
        report = json.loads(stdout.getvalue())
        self.assertEqual(EXPLICIT_PIVOT_REPORT_SCHEMA_VERSION, report["schema_version"])
        self.assertEqual("NON_AUTHORITATIVE_REPORTING_VIEW", report["authority"])
        self.assertEqual(4, report["pivot_count"])
        self.assertEqual(3, report["child_group_count"])
        self.assertTrue(report["constructed_binding"])
        self.assertFalse(report["reviewed_is_valid"])
        old_stdout = io.StringIO()
        old_example = support.RUNTIME_ROOT / "examples" / "manual_candidate" / "p004_reviewed.json"
        with redirect_stdout(old_stdout):
            self.assertEqual(0, main([str(old_example)]))
        self.assertEqual(
            "MANUAL_CANDIDATE_ANALYSIS_SNAPSHOT_V1",
            json.loads(old_stdout.getvalue())["schema_version"],
        )

    def test_pivots_only_cli_proves_no_automatic_grouping_or_fact_generation(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(0, main([str(EXAMPLES / "pivots_only_no_inference.json")]))
        report = json.loads(stdout.getvalue())
        self.assertEqual(0, report["child_group_count"])
        self.assertEqual([], report["generated_manual_fact_types"])
        self.assertEqual("UNRESOLVED", report["final_summary"])
        self.assertIn("NO_METHODOLOGY_EVALUATIONS_SUPPLIED", report["unresolved_reasons"])

    def test_pivot_module_has_no_dispatch_certification_or_external_capability(self) -> None:
        source = MODULE.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertTrue(
            {"socket", "urllib", "requests", "http", "subprocess", "importlib"}.isdisjoint(imports)
        )
        forbidden = (
            "_EXECUTION_DISPATCH",
            "_MANUAL_FACT_BUILDERS",
            "certify_structural_invalidity",
            "certify_validated_internal_family",
            "check_p004",
            "eval(",
            "exec(",
            "__import__",
        )
        for token in forbidden:
            self.assertNotIn(token, source)
        self.assertIn("analyze_bounded_manual_chart(bounded_request)", source)

    def test_no_discovery_inference_indicator_ranking_or_trading_implementation(self) -> None:
        source = MODULE.read_text(encoding="utf-8")
        for token in (
            "local_high", "local_low", "swing_high", "swing_low", "ATR",
            "percentage_reversal", "Fibonacci", "MACD", "EWO", "PREFERRED",
            "ALTERNATIVE", "STAND_ASIDE", "take_profit", "stop_loss",
        ):
            self.assertNotIn(token, source)
        self.assertNotIn("timeframe", source.lower())
        self.assertNotIn("wave_label", source.lower())

    def test_cli_retains_no_callable_module_or_output_file_injection_surface(self) -> None:
        source = CLI_MODULE.read_text(encoding="utf-8")
        for token in ("--output", "module_path", "callable", "eval(", "exec(", "write_text(", "write_bytes("):
            self.assertNotIn(token, source)
        self.assertNotIn("certif", source.lower())

    def test_inventories_and_legacy_api_remain_unchanged(self) -> None:
        self.assertEqual(10, len(execution_private._EXECUTION_DISPATCH))
        self.assertEqual(7, len(structural_private._PRODUCERS))
        self.assertTrue(structural_private._REGISTRY_SEALED)
        self.assertEqual(0, len(family_private._PRODUCERS))
        self.assertEqual(0, len(family_private._ISSUED))
        self.assertTrue(family_private._REGISTRY_SEALED)
        legacy = kernel().analyze
        self.assertIn("NOT_IMPLEMENTED", legacy.__func__.__code__.co_names)


if __name__ == "__main__":
    unittest.main()
