import ast
from dataclasses import FrozenInstanceError
import inspect
import unittest

import support
import elliott_methodology_kernel._structural_invalidity_certification as structural_private
import elliott_methodology_kernel._validated_internal_family_certification as family_private
from elliott_methodology_kernel import MethodologyKernel
from elliott_runtime.analysis.candidate_generation import (
    CandidateGenerationConfig,
    CandidateGenerationError,
    CandidateGenerationRequest,
    CandidateHypothesisShape,
    CandidatePivotWindow,
    generate_candidate_hypotheses,
)
from elliott_runtime.analysis.competing_candidates import (
    CompetingCandidateSetRequest,
    build_competing_candidate_set,
)
from elliott_runtime.analysis.family_hypotheses import (
    FamilyEvaluationKind,
    FamilyHypothesisBridgeRequest,
    build_family_evaluation_hypotheses,
)
from elliott_runtime.analysis.family_internal_subdivisions import (
    FamilyInternalSubdivisionEvaluationRequest,
    InternalRequirementStatus,
    SOURCE_DERIVED_BASE_CASE_NOT_FOUND,
    evaluate_family_internal_subdivisions,
)
import elliott_runtime.analysis.recursive_child_candidate_generation as child_module
from elliott_runtime.analysis.recursive_child_candidate_generation import (
    ARTIFACT_CLASSIFICATION,
    BOUND_CLASSIFICATION,
    CHILD_CANDIDATE_IS_NOT_VALIDATED_CHILD_WAVE,
    CHILD_EVIDENCE_CLASSIFICATION,
    EXACT_AUTOMATIC_CHILD_LEVELS,
    FINER_TIMEFRAME_IS_NOT_LOWER_DEGREE,
    MORE_CHILD_EVIDENCE_IS_NOT_FAMILY_VALIDITY,
    RECURSIVE_DEPTH_IS_NOT_DEGREE,
    WINDOW_CLASSIFICATION,
    WINDOW_IS_NOT_ELLIOTT_ENDPOINT_AUTHORITY,
    ChildCandidateGenerationConfig,
    ChildCandidateGenerationDiagnosticCode,
    ChildRequirementGenerationStatus,
    GeneratedChildCandidateEvidence,
    ProposedChildEvaluationWindow,
    RecursiveChildCandidateGenerationError,
    RecursiveChildCandidateGenerationLimitExceeded,
    RecursiveChildCandidateGenerationRequest,
    RecursiveChildCandidateGenerationResult,
    generate_child_candidate_evidence,
)
from elliott_runtime.market_data.geometric_pivots import GeometricPivotState
from test_candidate_generation import geometry, market_observations, subject


SHAPES = (
    CandidateHypothesisShape.THREE_SEGMENT_HYPOTHESIS,
    CandidateHypothesisShape.FIVE_SEGMENT_HYPOTHESIS,
)


def upstream(*, sparse=True, tail=False, gap=5):
    observations = market_observations(80)
    pivots = geometry(observations)
    if tail:
        selected = (pivots.pivots[-16], pivots.pivots[-11], pivots.pivots[-6], pivots.pivots[-1])
    elif sparse:
        selected = tuple(pivots.pivots[index * gap] for index in range(4))
    else:
        selected = pivots.pivots[:4]
    parent_subject = subject("recursive-child-parent")
    generation = generate_candidate_hypotheses(CandidateGenerationRequest(
        "parent-scoped-generation",
        "2026-09-04T00:00:00Z",
        parent_subject,
        observations,
        pivots,
        CandidateGenerationConfig(
            4, 4, 0, 1,
            (CandidateHypothesisShape.THREE_SEGMENT_HYPOTHESIS,),
            CandidatePivotWindow.EARLIEST,
        ),
        (),
        ("test:parent",),
        selected,
    ))
    competing = build_competing_candidate_set(CompetingCandidateSetRequest(
        "parent-set", "parent-scope", generation, ("test:parent-set",)
    ))
    families = build_family_evaluation_hypotheses(FamilyHypothesisBridgeRequest(
        "parent-family",
        "2026-09-04T00:00:00Z",
        competing,
        (FamilyEvaluationKind.SINGLE_ZIGZAG, FamilyEvaluationKind.FLAT),
        ("test:parent-family",),
    ), MethodologyKernel(support.PROTECTED_ROOT))
    return evaluate_family_internal_subdivisions(
        FamilyInternalSubdivisionEvaluationRequest(
            "parent-internals", families, (), ("test:parent-internals",)
        )
    )


def config(**changes):
    values = {
        "max_requirements_processed": 20,
        "max_total_child_windows": 20,
        "max_pivots_per_child_window": 8,
        "max_child_candidate_span_pivots": 6,
        "max_child_skipped_pivots": 1,
        "max_child_candidates_per_requirement": 50,
        "max_total_child_candidates": 300,
        "allowed_child_candidate_shapes": SHAPES,
    }
    values.update(changes)
    return ChildCandidateGenerationConfig(**values)


def request(source=None, configured=None, **changes):
    values = {
        "request_id": "child-generation:test",
        "requested_at_utc": "2026-09-04T00:00:00Z",
        "internal_subdivision_result": source or upstream(),
        "config": configured or config(),
        "provenance_refs": ("test:child-generation",),
    }
    values.update(changes)
    return RecursiveChildCandidateGenerationRequest(**values)


class RecursiveChildCandidateGenerationTests(unittest.TestCase):
    def test_classification_and_core_invariants_are_exact(self):
        self.assertEqual("PROJECT_ANALYSIS_INFRASTRUCTURE", ARTIFACT_CLASSIFICATION)
        self.assertEqual("CALLER_SUPPLIED_OPERATIONAL_BOUND", BOUND_CLASSIFICATION)
        self.assertEqual("PROPOSED_CHILD_EVALUATION_WINDOW", WINDOW_CLASSIFICATION)
        self.assertEqual("NEUTRAL_CHILD_CANDIDATE_EVIDENCE", CHILD_EVIDENCE_CLASSIFICATION)
        self.assertEqual(1, EXACT_AUTOMATIC_CHILD_LEVELS)
        self.assertEqual((True, True, True, True), (
            CHILD_CANDIDATE_IS_NOT_VALIDATED_CHILD_WAVE,
            WINDOW_IS_NOT_ELLIOTT_ENDPOINT_AUTHORITY,
            RECURSIVE_DEPTH_IS_NOT_DEGREE,
            FINER_TIMEFRAME_IS_NOT_LOWER_DEGREE,
        ))
        self.assertIs(True, MORE_CHILD_EVIDENCE_IS_NOT_FAMILY_VALIDITY)

    def test_exact_upstream_family_and_requirement_identities_are_retained(self):
        source = upstream()
        result = generate_child_candidate_evidence(request(source))
        self.assertIs(source, result.request.internal_subdivision_result)
        self.assertEqual(len(source.internal_requirements), len(result.processed_requirements))
        for expected, observed, window in zip(
            source.internal_requirements,
            result.processed_requirements,
            result.evaluation_windows,
            strict=True,
        ):
            self.assertIs(expected, observed)
            self.assertIs(expected, window.internal_requirement)
            self.assertIs(expected.family_hypothesis, window.internal_requirement.family_hypothesis)

    def test_inclusive_window_retains_exact_boundaries_and_excludes_outside_pivots(self):
        result = generate_child_candidate_evidence(request())
        for window in result.evaluation_windows:
            requirement = window.internal_requirement
            parent_pivots = requirement.parent_candidate.ordered_selected_pivots
            self.assertIs(parent_pivots[requirement.child_index], window.start_pivot)
            self.assertIs(parent_pivots[requirement.child_index + 1], window.end_pivot)
            self.assertIs(window.start_pivot, window.ordered_interval_pivots[0])
            self.assertIs(window.end_pivot, window.ordered_interval_pivots[-1])
            self.assertTrue(all(
                window.start_pivot.timestamp_utc <= item.timestamp_utc <= window.end_pivot.timestamp_utc
                for item in window.ordered_interval_pivots
            ))
            source_ids = {id(item) for item in window.source_pivot_result.pivots}
            self.assertTrue(all(id(item) in source_ids for item in window.ordered_interval_pivots))
            self.assertFalse(window.elliott_endpoint_authority)

    def test_existing_generator_and_competing_set_are_reused_with_exact_scope(self):
        result = generate_child_candidate_evidence(request())
        self.assertTrue(result.generated_child_evidence)
        for evidence in result.generated_child_evidence:
            self.assertIs(
                evidence.evaluation_window.ordered_interval_pivots,
                evidence.candidate_generation_result.request.scoped_pivots,
            )
            self.assertIs(
                evidence.candidate_generation_result,
                evidence.competing_candidate_set.candidate_generation_result,
            )
            self.assertEqual(
                evidence.candidate_generation_result.candidates,
                evidence.competing_candidate_set.ordered_candidates,
            )
            self.assertTrue(all(
                candidate.candidate_shape in SHAPES
                for candidate in evidence.competing_candidate_set.ordered_candidates
            ))
            self.assertTrue(all(
                candidate.family_authority is False and candidate.degree_authority is False
                for candidate in evidence.competing_candidate_set.ordered_candidates
            ))

    def test_requirement_shape_does_not_narrow_neutral_search_or_satisfy_requirement(self):
        result = generate_child_candidate_evidence(request())
        self.assertTrue(result.generated_child_evidence)
        for evidence in result.generated_child_evidence:
            self.assertEqual(SHAPES, evidence.candidate_generation_result.request.config.allowed_candidate_shapes)
            self.assertEqual((False, False, False, False), (
                evidence.validated_child_wave,
                evidence.validated_internal_family,
                evidence.requirement_satisfied,
                evidence.degree_authority,
            ))
        self.assertTrue(all(
            item.execution_status is InternalRequirementStatus.CHILD_EVIDENCE_UNRESOLVED
            for item in result.integrated_internal_subdivision_result.internal_requirements
        ))
        self.assertEqual((), result.integrated_internal_subdivision_result.reviewed_internal_scope_hypotheses)

    def test_insufficient_windows_remain_missing_and_never_expand_or_invalidate(self):
        source = upstream(sparse=False)
        result = generate_child_candidate_evidence(request(source))
        self.assertEqual((), result.generated_child_evidence)
        self.assertEqual(source.internal_requirements, result.requirements_still_missing_evidence)
        self.assertTrue(all(
            item.status is ChildRequirementGenerationStatus.INSUFFICIENT_GEOMETRIC_PIVOTS
            for item in result.requirement_outcomes
        ))
        for window in result.evaluation_windows:
            self.assertEqual(2, len(window.ordered_interval_pivots))
        self.assertEqual((), result.integrated_internal_subdivision_result.structurally_blocked_hypotheses)

    def test_developing_pivot_status_is_retained_and_diagnosed(self):
        source = upstream(tail=True)
        self.assertIs(GeometricPivotState.DEVELOPING, source.internal_requirements[-1].parent_candidate.ordered_selected_pivots[-1].state)
        result = generate_child_candidate_evidence(request(source))
        developing = next(
            item for item in result.diagnostics
            if item.code is ChildCandidateGenerationDiagnosticCode.DEVELOPING_WINDOWS_PRESENT
        )
        self.assertGreater(developing.count, 0)
        self.assertTrue(any(
            pivot.state is GeometricPivotState.DEVELOPING
            for window in result.evaluation_windows
            for pivot in window.ordered_interval_pivots
        ))

    def test_scoped_generator_rejects_foreign_duplicate_reversed_and_mutated_scope(self):
        source = upstream()
        parent_request = source.family_hypothesis_result.competing_candidate_set.candidate_generation_result.request
        good = parent_request.scoped_pivots
        with self.assertRaises(CandidateGenerationError):
            CandidateGenerationRequest(
                parent_request.request_id, parent_request.requested_at_utc, parent_request.subject,
                parent_request.observations, parent_request.geometric_pivots, parent_request.config,
                (), parent_request.provenance_refs, (good[0], good[0], good[2], good[3]),
            )
        with self.assertRaises(CandidateGenerationError):
            CandidateGenerationRequest(
                parent_request.request_id, parent_request.requested_at_utc, parent_request.subject,
                parent_request.observations, parent_request.geometric_pivots, parent_request.config,
                (), parent_request.provenance_refs, tuple(reversed(good)),
            )
        foreign = geometry(market_observations(80)).pivots[0]
        with self.assertRaises(CandidateGenerationError):
            CandidateGenerationRequest(
                parent_request.request_id, parent_request.requested_at_utc, parent_request.subject,
                parent_request.observations, parent_request.geometric_pivots, parent_request.config,
                (), parent_request.provenance_refs, (foreign,),
            )

    def test_all_global_and_per_window_bounds_fail_before_result(self):
        source = upstream()
        cases = (
            {"max_requirements_processed": 1},
            {"max_total_child_windows": 1},
            {"max_child_candidates_per_requirement": 1},
            {"max_total_child_candidates": 1},
        )
        for changes in cases:
            with self.subTest(changes=changes):
                with self.assertRaisesRegex(
                    RecursiveChildCandidateGenerationLimitExceeded,
                    "CHILD_GENERATION_BOUND_EXCEEDED",
                ):
                    generate_child_candidate_evidence(request(source, config(**changes)))

    def test_per_window_pivot_bound_fails_without_silent_truncation(self):
        source = upstream(gap=6)
        limited = config(
            max_pivots_per_child_window=6,
            max_child_candidate_span_pivots=6,
        )
        with self.assertRaisesRegex(
            RecursiveChildCandidateGenerationLimitExceeded,
            "max_pivots_per_child_window",
        ):
            generate_child_candidate_evidence(request(source, limited))

    def test_mapping_duck_subclass_mutation_and_unissued_result_fail_closed(self):
        for supplied in ({"internal_subdivision_result": upstream()}, object()):
            with self.assertRaises(RecursiveChildCandidateGenerationError):
                generate_child_candidate_evidence(supplied)
        with self.assertRaises(TypeError):
            type("WindowSubclass", (ProposedChildEvaluationWindow,), {})
        with self.assertRaises(TypeError):
            type("EvidenceSubclass", (GeneratedChildCandidateEvidence,), {})
        with self.assertRaises(TypeError):
            RecursiveChildCandidateGenerationResult()
        malformed = object.__new__(RecursiveChildCandidateGenerationResult)
        with self.assertRaises(Exception):
            malformed._validated()
        value = request()
        object.__setattr__(value.config, "max_total_child_candidates", 999)
        with self.assertRaises(RecursiveChildCandidateGenerationError):
            generate_child_candidate_evidence(value)

    def test_nested_outcome_diagnostic_window_and_evidence_mutation_fail_closed(self):
        for target_name, field_name, changed in (
            ("outcome", "diagnostic", "changed but nonblank"),
            ("diagnostic", "detail", "changed but nonblank"),
            ("window", "provenance_refs", ("changed",)),
            ("evidence", "provenance_refs", ("changed",)),
        ):
            with self.subTest(target=target_name):
                result = generate_child_candidate_evidence(request())
                target = {
                    "outcome": result.requirement_outcomes[0],
                    "diagnostic": result.diagnostics[0],
                    "window": result.evaluation_windows[0],
                    "evidence": result.generated_child_evidence[0],
                }[target_name]
                object.__setattr__(target, field_name, changed)
                with self.assertRaises(RecursiveChildCandidateGenerationError):
                    result._validated()

    def test_exactly_one_level_no_degree_timeframe_or_p023_selection(self):
        result = generate_child_candidate_evidence(request())
        self.assertEqual(1, EXACT_AUTOMATIC_CHILD_LEVELS)
        self.assertTrue(result.generated_child_evidence)
        source = inspect.getsource(child_module)
        self.assertEqual(1, source.count("def generate_child_candidate_evidence"))
        self.assertNotIn("generate_child_candidate_evidence(", source.split("def generate_child_candidate_evidence", 1)[1])
        for name in ("degree", "timeframe", "finer_observations", "visibility_state"):
            self.assertNotIn(name, RecursiveChildCandidateGenerationRequest.__dataclass_fields__)
        self.assertNotIn("evaluate_p023", source)

    def test_family_hypotheses_remain_independent_and_unranked(self):
        result = generate_child_candidate_evidence(request())
        by_parent = {}
        for outcome in result.requirement_outcomes:
            by_parent.setdefault(id(outcome.internal_requirement.parent_candidate), set()).add(
                outcome.internal_requirement.family_hypothesis.family_kind
            )
        self.assertTrue(all(
            kinds == {FamilyEvaluationKind.SINGLE_ZIGZAG, FamilyEvaluationKind.FLAT}
            for kinds in by_parent.values()
        ))
        for evidence in result.generated_child_evidence:
            fields = evidence.competing_candidate_set.__dataclass_fields__
            self.assertNotIn("rank", fields)
            self.assertNotIn("preferred", fields)

    def test_base_case_and_protected_blockers_remain_active(self):
        result = generate_child_candidate_evidence(request())
        diagnostic = next(
            item for item in result.diagnostics
            if item.code is ChildCandidateGenerationDiagnosticCode.BASE_CASE_REMAINS_BLOCKED
        )
        self.assertEqual(len(result.generated_child_evidence), diagnostic.count)
        self.assertEqual(SOURCE_DERIVED_BASE_CASE_NOT_FOUND, diagnostic.detail)
        self.assertEqual(7, len(structural_private._PRODUCERS))
        self.assertEqual(0, len(family_private._PRODUCERS))
        self.assertEqual(0, len(family_private._ISSUED))

    def test_no_methodology_labels_ranking_indicators_traps_fundamentals_forecast_or_trading(self):
        source = inspect.getsource(child_module)
        tree = ast.parse(source)
        imports = {
            alias.name for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in node.names
        }
        self.assertTrue({"socket", "urllib", "requests", "http", "subprocess"}.isdisjoint(imports))
        for forbidden in (
            "certify_validated_internal_family", "evaluate_p023", "P005", "P006",
            "WXY", "WXYXZ", "PREFERRED", "ALTERNATIVE", "REMOTE", "RSI", "MACD",
            "EWO", "Fibonacci", "bull_trap", "bear_trap", "trade_signal",
        ):
            self.assertNotIn(f'"{forbidden}"', source)

    def test_legacy_analyze_and_methodology_inventory_remain_unchanged(self):
        self.assertIn("KernelStatus.NOT_IMPLEMENTED", inspect.getsource(MethodologyKernel.analyze))
        observed = set()
        for path in (support.SRC / "elliott_methodology_kernel").glob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, (ast.Assign, ast.AnnAssign)):
                    targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
                    if any(isinstance(item, ast.Name) and item.id.endswith(("BEHAVIOR_ID", "BEHAVIOR")) for item in targets) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        observed.add(node.value.value)
        self.assertEqual(10, len(observed))


if __name__ == "__main__":
    unittest.main()
