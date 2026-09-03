import ast
import copy
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import pickle
import unittest

import support
import elliott_methodology_kernel as kernel_package
import elliott_methodology_kernel._structural_invalidity_certification as structural_private
import elliott_methodology_kernel._validated_internal_family_certification as family_private
import elliott_methodology_kernel.multi_degree_candidate_composition as degree_module
from elliott_methodology_kernel import (
    AnalyzedWaveSubject,
    BoundedManualChartAnalysisRequest,
    CandidateDegreeDeclaration,
    CandidateScope,
    DegreeCompositionDiagnosticState,
    DegreePeerCheckStatus,
    DegreePeerConsistencyInput,
    ImpulseDirection,
    ManualP004Wave2OriginFact,
    MethodologyKernel,
    MultiDegreeCandidateCompositionError,
    MultiDegreeCandidateCompositionRequest,
    MultiDegreeCandidateCompositionResult,
    MultiTimeframeObservationBundle,
    MultiTimeframeObservationTransportRequest,
    ObservationAssociationRole,
    OrderedChildBinding,
    ParentChildDegreeCheckStatus,
    ParentChildDegreeInput,
    RecursiveCandidateCompositionRequest,
    SubjectObservationAttachment,
    TIMEFRAME_IS_NOT_DEGREE,
)
from elliott_methodology_kernel.models import (
    Bar,
    BarProvenance,
    DataProvenance,
    DataQualityReport,
    DegreeStatus,
    KernelStatus,
    MarketType,
    NormalizedMarketObservations,
    SymbolIdentity,
    Timeframe,
)


def subject(name: str) -> AnalyzedWaveSubject:
    return AnalyzedWaveSubject(name, f"observations:{name}")


def bounded(item: AnalyzedWaveSubject):
    return MethodologyKernel(support.PROTECTED_ROOT).analyze_bounded_manual_chart(
        BoundedManualChartAnalysisRequest(
            f"bounded:{item.subject_id}",
            "2026-09-03T12:00:00Z",
            item,
            f"candidate:{item.subject_id}",
            (
                ManualP004Wave2OriginFact(
                    CandidateScope.NORMAL_IMPULSE,
                    ImpulseDirection.UP,
                    100,
                    101,
                ),
            ),
            provenance_refs=(f"candidate:{item.subject_id}",),
        )
    )


def compose(parent_subject, children=(), name="tree"):
    parent = bounded(parent_subject)
    child_results = tuple(
        item if isinstance(item, kernel_package.RecursiveCandidateCompositionResult) else bounded(item)
        for item in children
    )
    child_subjects = tuple(
        item.parent_candidate_result.subject
        if isinstance(item, kernel_package.RecursiveCandidateCompositionResult)
        else item.subject
        for item in child_results
    )
    binding = OrderedChildBinding(f"binding:{name}", parent_subject, child_subjects)
    return MethodologyKernel(support.PROTECTED_ROOT).compose_recursive_candidate(
        RecursiveCandidateCompositionRequest(
            name,
            parent,
            child_results,
            binding,
            (f"composition:{name}",),
        )
    )


def declaration(item, degree, status=DegreeStatus.RESOLVED):
    return CandidateDegreeDeclaration(
        item,
        degree,
        status,
        (f"degree:{item.subject_id}:{degree}",),
    )


def request(tree, declarations=(), context=None, name="degrees"):
    return MultiDegreeCandidateCompositionRequest(
        name,
        "2026-09-03T12:00:00Z",
        tree,
        tuple(declarations),
        context,
        (f"multi-degree:{name}",),
    )


def run(tree, declarations=(), context=None, name="degrees"):
    kernel = MethodologyKernel(support.PROTECTED_ROOT)
    return kernel.compose_multi_degree_candidate(
        request(tree, declarations, context, name)
    )


def observations(timeframe: Timeframe):
    symbol_identity = SymbolIdentity("TEST", MarketType.OTHER, "X", "PX:TEST")
    return NormalizedMarketObservations(
        symbol_identity,
        timeframe,
        (
            Bar(
                datetime(2026, 1, 1, tzinfo=timezone.utc),
                100.0,
                102.0,
                99.0,
                101.0,
                None,
                BarProvenance(0, "2026-01-01T00:00:00Z"),
            ),
        ),
        DataProvenance(
            "test",
            f"memory:{timeframe.label}",
            (str(timeframe.resolution_seconds) * 64)[:64],
            timeframe,
            "2026-09-03T12:00:00Z",
        ),
        DataQualityReport(),
    )


def context_for(tree, attachments=()):
    sets = tuple(
        attachment.observations
        for index, attachment in enumerate(attachments)
        if not any(
            attachment.observations is earlier.observations
            for earlier in attachments[:index]
        )
    )
    if not sets:
        sets = (observations(Timeframe("1D", 86400)),)
    bundle = MultiTimeframeObservationBundle(
        sets[0].symbol if sets else SymbolIdentity("TEST", MarketType.OTHER),
        sets,
        ("bundle:explicit",),
    )
    return MethodologyKernel(support.PROTECTED_ROOT).attach_multi_timeframe_observations(
        MultiTimeframeObservationTransportRequest(
            "transport",
            tree,
            bundle,
            tuple(attachments),
            ("transport:explicit",),
        )
    )


class MultiDegreeCandidateCompositionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.parent = subject("parent")
        self.first = subject("first")
        self.second = subject("second")
        self.tree = compose(self.parent, (self.first, self.second))

    def test_classification_and_core_invariant(self) -> None:
        self.assertEqual("PROJECT_ANALYSIS_INFRASTRUCTURE", degree_module.ARTIFACT_CLASSIFICATION)
        self.assertEqual("CALLER_SUPPLIED_DEGREE_DECLARATION", degree_module.DEGREE_DECLARATION_CLASSIFICATION)
        self.assertEqual("PROJECT_OPERATIONAL_POLICY", degree_module.WORKFLOW_POLICY_CLASSIFICATION)
        self.assertIs(True, TIMEFRAME_IS_NOT_DEGREE)

    def test_exact_declaration_is_immutable_identity_bound_and_unpicklable(self) -> None:
        item = declaration(self.parent, "Primary")
        self.assertIs(self.parent, item.subject)
        self.assertEqual("Primary", item.degree)
        self.assertIs(DegreeStatus.RESOLVED, item.degree_status)
        self.assertIs(item, copy.copy(item))
        self.assertIs(item, copy.deepcopy(item))
        with self.assertRaises(FrozenInstanceError):
            item.degree = "Cycle"
        with self.assertRaises(TypeError):
            pickle.dumps(item)

    def test_declaration_mapping_duck_and_subclass_are_rejected(self) -> None:
        with self.assertRaises(TypeError):
            type("DeclarationSubclass", (CandidateDegreeDeclaration,), {})
        for value in ({"subject": self.parent}, object()):
            with self.subTest(value=value):
                with self.assertRaises(MultiDegreeCandidateCompositionError):
                    request(self.tree, (value,))

    def test_parent_child_descendant_membership_and_declaration_order(self) -> None:
        grandchild = subject("grandchild")
        nested = compose(self.first, (grandchild,), "nested")
        tree = compose(self.parent, (nested, self.second), "root")
        declarations = (
            declaration(grandchild, "Minor"),
            declaration(self.parent, "Cycle"),
            declaration(self.first, "Primary"),
        )
        result = run(tree, declarations)
        self.assertIs(declarations[0], result.degree_declarations[0])
        self.assertEqual(
            ["parent", "first", "grandchild", "second"],
            [item.subject.subject_id for item in result.subject_degree_inventory],
        )

    def test_foreign_lookalike_and_duplicate_subjects_are_rejected(self) -> None:
        for foreign in (subject("foreign"), subject("parent")):
            with self.subTest(foreign=foreign.observation_provenance_ref):
                with self.assertRaises(MultiDegreeCandidateCompositionError):
                    request(self.tree, (declaration(foreign, "Cycle"),))
        one = declaration(self.parent, "Cycle")
        for duplicate in (one, declaration(self.parent, "Primary")):
            with self.subTest(duplicate=duplicate.degree):
                with self.assertRaises(MultiDegreeCandidateCompositionError):
                    request(self.tree, (one, duplicate))

    def test_partial_coverage_is_operational_only_and_creates_no_evaluation(self) -> None:
        result = run(self.tree, (declaration(self.parent, "Cycle"),))
        self.assertEqual((), result.degree_evaluations)
        missing = [
            item for item in result.degree_diagnostics
            if item.state is DegreeCompositionDiagnosticState.NO_DEGREE_DECLARATION_SUPPLIED
        ]
        self.assertEqual([self.first, self.second], [item.subject for item in missing])
        self.assertTrue(all(item.declaration is None for item in result.subject_degree_inventory[1:]))

    def test_matching_direct_children_execute_exact_existing_peer_behavior(self) -> None:
        result = run(
            self.tree,
            (declaration(self.first, "Primary"), declaration(self.second, "Primary")),
        )
        self.assertEqual(1, len(result.degree_evaluations))
        evaluation = result.degree_evaluations[0]
        self.assertEqual("DEGREE_DIRECT_CHILD_PEER_CONSISTENCY", evaluation.behavior_id)
        self.assertIs(DegreePeerConsistencyInput, type(evaluation.input_object))
        self.assertIs(DegreePeerCheckStatus.RULE_SATISFIED, evaluation.result_object.status)
        self.assertIs(evaluation.input_object, evaluation.execution_result.execution_records[0].input_object)
        self.assertIs(evaluation.result_object, evaluation.execution_result.execution_records[0].result_object)

    def test_peer_mismatch_retains_existing_violation_without_certificate(self) -> None:
        result = run(
            self.tree,
            (declaration(self.first, "Primary"), declaration(self.second, "Intermediate")),
        )
        evaluation = result.degree_evaluations[0]
        self.assertIs(DegreePeerCheckStatus.RULE_VIOLATED, evaluation.result_object.status)
        self.assertIs(True, evaluation.result_object.fatal_to_candidate)
        self.assertFalse(hasattr(result, "structural_invalidity_certificate"))
        self.assertIn(
            DegreeCompositionDiagnosticState.PEER_DEGREE_VIOLATION_REPORTED_BY_EXISTING_VALIDATOR,
            {item.state for item in result.degree_diagnostics},
        )

    def test_missing_one_child_prevents_peer_input_without_autofill(self) -> None:
        result = run(self.tree, (declaration(self.first, "Primary"),))
        self.assertEqual((), result.degree_evaluations)

    def test_parent_child_edges_execute_existing_adjacency_independently_in_order(self) -> None:
        result = run(
            self.tree,
            (
                declaration(self.parent, "Cycle"),
                declaration(self.first, "Primary"),
                declaration(self.second, "Primary"),
            ),
        )
        adjacency = [
            item for item in result.degree_evaluations
            if item.behavior_id == "PARENT_CHILD_DEGREE_ADJACENCY"
        ]
        self.assertEqual([self.first, self.second], [item.child_subjects[0] for item in adjacency])
        self.assertTrue(all(type(item.input_object) is ParentChildDegreeInput for item in adjacency))
        self.assertTrue(all(item.result_object.status is ParentChildDegreeCheckStatus.RULE_SATISFIED for item in adjacency))

    def test_invalid_adjacency_retains_exact_existing_violation(self) -> None:
        result = run(
            self.tree,
            (declaration(self.parent, "Cycle"), declaration(self.first, "Intermediate")),
        )
        evaluation = result.degree_evaluations[0]
        self.assertIs(ParentChildDegreeCheckStatus.RULE_VIOLATED, evaluation.result_object.status)
        self.assertIs(True, evaluation.result_object.fatal_to_candidate)
        self.assertIs(evaluation.result_object, evaluation.execution_result.execution_records[0].result_object)

    def test_grandparent_grandchild_is_not_a_direct_edge_and_peer_groups_do_not_cross_parents(self) -> None:
        grandchild = subject("grandchild")
        other_grandchild = subject("other-grandchild")
        nested = compose(self.first, (grandchild, other_grandchild), "nested")
        tree = compose(self.parent, (nested, self.second), "root")
        result = run(
            tree,
            tuple(
                declaration(item, degree)
                for item, degree in (
                    (self.parent, "Cycle"),
                    (self.first, "Primary"),
                    (self.second, "Primary"),
                    (grandchild, "Intermediate"),
                    (other_grandchild, "Intermediate"),
                )
            ),
        )
        adjacency_pairs = [
            (item.parent_subject.subject_id, item.child_subjects[0].subject_id)
            for item in result.degree_evaluations
            if item.behavior_id == "PARENT_CHILD_DEGREE_ADJACENCY"
        ]
        self.assertEqual(
            [("parent", "first"), ("parent", "second"), ("first", "grandchild"), ("first", "other-grandchild")],
            adjacency_pairs,
        )
        peer_groups = [
            tuple(child.subject_id for child in item.child_subjects)
            for item in result.degree_evaluations
            if item.behavior_id == "DEGREE_DIRECT_CHILD_PEER_CONSISTENCY"
        ]
        self.assertEqual([("first", "second"), ("grandchild", "other-grandchild")], peer_groups)

    def test_unresolved_declarations_are_passed_to_existing_validators(self) -> None:
        result = run(
            self.tree,
            (
                declaration(self.parent, None, DegreeStatus.UNRESOLVED),
                declaration(self.first, None, DegreeStatus.UNRESOLVED),
            ),
        )
        evaluation = result.degree_evaluations[0]
        self.assertIs(ParentChildDegreeCheckStatus.UNRESOLVED_MISSING_INPUT, evaluation.result_object.status)

    def test_exact_multi_timeframe_context_is_retained_and_not_interpreted(self) -> None:
        daily = observations(Timeframe("1D", 86400))
        attachments = (
            SubjectObservationAttachment(self.parent, daily, ObservationAssociationRole.REFERENCE_VIEW),
            SubjectObservationAttachment(self.first, daily, ObservationAssociationRole.REFERENCE_VIEW),
        )
        context = context_for(self.tree, attachments)
        result = run(
            self.tree,
            (declaration(self.parent, "Cycle"), declaration(self.first, "Primary")),
            context,
        )
        self.assertIs(context, result.multi_timeframe_context)
        self.assertEqual("Cycle", result.degree_declarations[0].degree)
        self.assertEqual("Primary", result.degree_declarations[1].degree)

    def test_different_timeframes_same_degree_do_not_change_degree(self) -> None:
        daily = observations(Timeframe("1D", 86400))
        weekly = observations(Timeframe("1W", 604800))
        context = context_for(
            self.tree,
            (
                SubjectObservationAttachment(self.first, daily, ObservationAssociationRole.REFERENCE_VIEW),
                SubjectObservationAttachment(self.second, weekly, ObservationAssociationRole.ADDITIONAL_VIEW),
            ),
        )
        result = run(
            self.tree,
            (declaration(self.first, "Primary"), declaration(self.second, "Primary")),
            context,
        )
        self.assertIs(DegreePeerCheckStatus.RULE_SATISFIED, result.degree_evaluations[0].result_object.status)

    def test_foreign_or_mapping_timeframe_context_is_rejected(self) -> None:
        other_parent = subject("other-parent")
        other_tree = compose(other_parent, (), "other-tree")
        other_context = context_for(other_tree)
        for value in ({"recursive_candidate_result": self.tree}, other_context):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(MultiDegreeCandidateCompositionError):
                    request(self.tree, context=value)

    def test_result_is_exact_immutable_unpicklable_and_not_a_certificate(self) -> None:
        result = run(self.tree)
        self.assertIs(MultiDegreeCandidateCompositionResult, type(result))
        self.assertIs(result, copy.copy(result))
        self.assertIs(result, copy.deepcopy(result))
        with self.assertRaises(FrozenInstanceError):
            result.request_id = "changed"
        with self.assertRaises(TypeError):
            pickle.dumps(result)
        self.assertFalse(isinstance(result, kernel_package.CertifiedStructuralInvalidity))

    def test_low_level_mutation_fails_closed(self) -> None:
        item = declaration(self.parent, "Cycle")
        built_request = request(self.tree, (item,))
        object.__setattr__(item, "degree", "Primary")
        with self.assertRaises(MultiDegreeCandidateCompositionError):
            MethodologyKernel(support.PROTECTED_ROOT).compose_multi_degree_candidate(built_request)
        result = run(self.tree)
        object.__setattr__(result.degree_diagnostics[0], "reason", "changed")
        with self.assertRaises(MultiDegreeCandidateCompositionError):
            copy.copy(result)

    def test_no_p023_family_ranking_label_indicator_or_trading_behavior(self) -> None:
        result = run(
            self.tree,
            (
                declaration(self.parent, "Cycle"),
                declaration(self.first, "Primary"),
                declaration(self.second, "Primary"),
            ),
        )
        self.assertEqual(
            {"DEGREE_DIRECT_CHILD_PEER_CONSISTENCY", "PARENT_CHILD_DEGREE_ADJACENCY"},
            {item.behavior_id for item in result.degree_evaluations},
        )
        source = (support.SRC / "elliott_methodology_kernel" / "multi_degree_candidate_composition.py").read_text(encoding="utf-8")
        for forbidden in (
            "P023VisibilityInput", "P003OneLarger", "P004Input", "P007Single",
            "P008Flat", "P009Triangle", "EndingDiagonal", "Fibonacci", "RSI",
            "MACD", "EWO", "PREFERRED", "ALTERNATIVE", "TRADE", "WAIT",
            "certify_structural_invalidity", "certify_validated_internal_family",
        ):
            self.assertNotIn(forbidden, source)
        tree = ast.parse(source)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add("." * node.level + (node.module or ""))
        self.assertTrue({"socket", "subprocess", "requests", "urllib", "importlib"}.isdisjoint(imports))

    def test_methodology_registries_and_legacy_analyze_remain_unchanged(self) -> None:
        self.assertEqual(10, len(kernel_package.explicit_behavior_execution._EXECUTION_DISPATCH))
        self.assertEqual(7, len(structural_private._PRODUCERS))
        self.assertEqual(0, len(family_private._PRODUCERS))
        self.assertEqual(0, len(family_private._ISSUED))
        legacy_observations = observations(Timeframe("1D", 86400))
        legacy = MethodologyKernel(support.PROTECTED_ROOT).analyze(
            kernel_package.AnalysisRequest(
                legacy_observations,
                "2026-09-03T12:00:00Z",
                "legacy",
            )
        )
        self.assertIs(KernelStatus.NOT_IMPLEMENTED, legacy.status)


if __name__ == "__main__":
    unittest.main()
