import ast
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import unittest

import support
import elliott_methodology_kernel._structural_invalidity_certification as structural_private
import elliott_methodology_kernel._validated_internal_family_certification as family_private
from elliott_methodology_kernel import (
    AnalyzedWaveSubject,
    BoundedManualChartAnalysisRequest,
    CandidateScope,
    ImpulseDirection,
    ManualP004Wave2OriginFact,
    MethodologyKernel,
    OrderedChildBinding,
    P009CandidateScope,
    P009TriangleCardinalityInput,
    certify_structural_invalidity,
    check_p009_triangle_cardinality,
)
from elliott_methodology_kernel.contracts import MarketType, SymbolIdentity, Timeframe
import elliott_runtime.analysis.candidate_generation as generation_module
from elliott_runtime.analysis.candidate_generation import (
    ARTIFACT_CLASSIFICATION,
    BOUND_CLASSIFICATION,
    CANDIDATE_HYPOTHESIS_ONLY,
    DEGREE_AUTHORITY,
    ELLIOTT_VALIDITY_AUTHORITY,
    ENUMERATION_CLASSIFICATION,
    FAMILY_AUTHORITY,
    TIMEFRAME_IS_NOT_DEGREE,
    CandidateGenerationConfig,
    CandidateGenerationError,
    CandidateGenerationLimitExceeded,
    CandidateGenerationRequest,
    CandidateHypothesisShape,
    CandidateMethodologyDelegation,
    CandidatePivotWindow,
    GeneratedCandidateReviewState,
    generate_candidate_hypotheses,
)
from elliott_runtime.market_data.geometric_pivots import (
    EqualExtremePolicy,
    GeometricPivotDiscoveryConfig,
    GeometricPivotDiscoveryMethod,
    GeometricPivotDiscoveryRequest,
    discover_geometric_pivots,
)
from elliott_runtime.market_data.ingestion import _normalize


def market_observations(count=24):
    values = [10 + ((index * 7) % 11) + (index % 3) for index in range(count)]
    records = []
    for index, high in enumerate(values):
        low = high - 3
        middle = (high + low) / 2
        records.append({
            "timestamp": (datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(days=index)).isoformat(),
            "open": middle, "high": high, "low": low, "close": middle, "volume": 1000,
        })
    return _normalize(records, b"candidate-bars", "test", "in-memory", SymbolIdentity("TEST", MarketType.STOCK), Timeframe("1d", 86400))


def geometry(data=None):
    data = data or market_observations()
    return discover_geometric_pivots(GeometricPivotDiscoveryRequest(
        "geometry-for-candidates",
        data,
        GeometricPivotDiscoveryConfig(
            GeometricPivotDiscoveryMethod.WINDOWED_LOCAL_EXTREMA,
            1,
            1,
            EqualExtremePolicy.LAST,
            True,
        ),
        ("test:geometry",),
    ))


def config(**changes):
    values = {
        "max_pivots_considered": 6,
        "max_candidate_span_pivots": 6,
        "max_skipped_pivots": 0,
        "max_candidates_generated": 20,
        "allowed_candidate_shapes": (
            CandidateHypothesisShape.THREE_SEGMENT_HYPOTHESIS,
            CandidateHypothesisShape.FIVE_SEGMENT_HYPOTHESIS,
        ),
        "pivot_window": CandidatePivotWindow.LATEST,
    }
    values.update(changes)
    return CandidateGenerationConfig(**values)


def subject(name="generated"):
    return AnalyzedWaveSubject(name, f"observations:{name}")


def request(data=None, pivots=None, analyzed_subject=None, configured=None, delegations=(), **changes):
    data = data or market_observations()
    pivots = pivots or geometry(data)
    analyzed_subject = analyzed_subject or subject()
    values = {
        "request_id": "candidate-generation-test",
        "requested_at_utc": "2026-09-04T12:00:00Z",
        "subject": analyzed_subject,
        "observations": data,
        "geometric_pivots": pivots,
        "config": configured or config(),
        "methodology_delegations": delegations,
        "provenance_refs": ("test:candidate-generation",),
    }
    values.update(changes)
    return CandidateGenerationRequest(**values)


def bounded(analyzed_subject, candidate_id, wave2_end):
    return BoundedManualChartAnalysisRequest(
        request_id=f"review:{candidate_id}",
        requested_at_utc="2026-09-04T12:00:00Z",
        subject=analyzed_subject,
        candidate_id=candidate_id,
        manual_behavior_facts=(ManualP004Wave2OriginFact(
            CandidateScope.NORMAL_IMPULSE,
            ImpulseDirection.UP,
            100,
            wave2_end,
        ),),
        provenance_refs=("caller:exact-p004-fact",),
    )


class CandidateGenerationTests(unittest.TestCase):
    def test_classification_and_authority_flags_are_exact(self):
        self.assertEqual("PROJECT_ANALYSIS_INFRASTRUCTURE", ARTIFACT_CLASSIFICATION)
        self.assertEqual("CALLER_SUPPLIED_OPERATIONAL_BOUND", BOUND_CLASSIFICATION)
        self.assertEqual("PURE_COMBINATORIAL_INFRASTRUCTURE", ENUMERATION_CLASSIFICATION)
        self.assertIs(True, CANDIDATE_HYPOTHESIS_ONLY)
        self.assertEqual((False, False, False, True), (ELLIOTT_VALIDITY_AUTHORITY, FAMILY_AUTHORITY, DEGREE_AUTHORITY, TIMEFRAME_IS_NOT_DEGREE))

    def test_exact_geometry_and_observation_identities_are_preserved(self):
        data = market_observations()
        pivots = geometry(data)
        result = generate_candidate_hypotheses(request(data, pivots))
        self.assertIs(data, result.input_observations)
        self.assertIs(pivots, result.input_geometric_pivots)
        self.assertIs(data, result.candidates[0].source_observations)
        self.assertIs(pivots, result.candidates[0].source_geometric_pivots)

    def test_deterministic_shape_and_enumeration_order(self):
        value = request()
        first = generate_candidate_hypotheses(value)
        second = generate_candidate_hypotheses(value)
        self.assertEqual([c.candidate_id for c in first.candidates], [c.candidate_id for c in second.candidates])
        self.assertEqual([c.candidate_shape for c in first.candidates], [c.candidate_shape for c in second.candidates])
        self.assertEqual(4, len(first.candidates))

    def test_selected_pivots_are_chronological_unique_exact_identities(self):
        result = generate_candidate_hypotheses(request())
        source_ids = {id(pivot) for pivot in result.input_geometric_pivots.pivots}
        for candidate in result.candidates:
            stamps = [pivot.timestamp_utc for pivot in candidate.ordered_selected_pivots]
            self.assertEqual(sorted(stamps), stamps)
            self.assertEqual(len(stamps), len(set(stamps)))
            self.assertTrue(all(id(pivot) in source_ids for pivot in candidate.ordered_selected_pivots))

    def test_three_and_five_segments_are_only_neutral_shape_counts(self):
        result = generate_candidate_hypotheses(request())
        for candidate in result.candidates:
            expected = candidate.candidate_shape.selected_pivot_count
            self.assertEqual(expected, len(candidate.ordered_selected_pivots))
            self.assertIs(True, candidate.candidate_hypothesis_only)
            self.assertEqual((False, False, False), (candidate.elliott_validity_authority, candidate.family_authority, candidate.degree_authority))

    def test_no_methodology_input_means_every_candidate_is_retained_unresolved(self):
        result = generate_candidate_hypotheses(request())
        self.assertTrue(result.candidates)
        self.assertTrue(all(item.review_state is GeneratedCandidateReviewState.UNRESOLVED for item in result.candidates))
        self.assertTrue(all(item.unresolved_reasons == ("NO_EXACT_METHODOLOGY_INPUTS_SUPPLIED",) for item in result.candidates))
        self.assertTrue(all(item.downstream_methodology_result is None for item in result.candidates))

    def test_caller_window_selects_earliest_or_latest_without_importance_claim(self):
        data = market_observations(36)
        pivots = geometry(data)
        earliest = generate_candidate_hypotheses(request(data, pivots, configured=config(pivot_window=CandidatePivotWindow.EARLIEST)))
        latest = generate_candidate_hypotheses(request(data, pivots, configured=config(pivot_window=CandidatePivotWindow.LATEST)))
        self.assertNotEqual(earliest.candidates[0].ordered_selected_pivots, latest.candidates[0].ordered_selected_pivots)

    def test_skip_and_span_bounds_are_enforced_and_diagnosed(self):
        value = request(configured=config(max_skipped_pivots=1))
        result = generate_candidate_hypotheses(value)
        self.assertGreater(len(result.candidates), 4)
        for candidate in result.candidates:
            positions = [result.input_geometric_pivots.pivots.index(p) for p in candidate.ordered_selected_pivots]
            span = positions[-1] - positions[0] + 1
            self.assertLessEqual(span, value.config.max_candidate_span_pivots)
            self.assertLessEqual(span - len(positions), value.config.max_skipped_pivots)

    def test_candidate_cap_fails_closed_without_partial_output(self):
        with self.assertRaises(CandidateGenerationLimitExceeded):
            generate_candidate_hypotheses(request(configured=config(max_skipped_pivots=1, max_candidates_generated=1)))

    def test_configuration_bounds_and_types_fail_closed(self):
        cases = (
            {"max_pivots_considered": 0}, {"max_pivots_considered": True},
            {"max_candidate_span_pivots": 7}, {"max_skipped_pivots": -1},
            {"max_candidates_generated": 0}, {"allowed_candidate_shapes": ()},
            {"allowed_candidate_shapes": (CandidateHypothesisShape.THREE_SEGMENT_HYPOTHESIS,) * 2},
            {"pivot_window": "LATEST"},
        )
        for changes in cases:
            with self.subTest(changes=changes):
                with self.assertRaises(CandidateGenerationError):
                    config(**changes)

    def test_mapping_duck_and_subclass_fail_closed(self):
        for value in ({"request_id": "x"}, object()):
            with self.assertRaises(CandidateGenerationError):
                generate_candidate_hypotheses(value)
        with self.assertRaises(TypeError):
            type("ConfigSubclass", (CandidateGenerationConfig,), {})

    def test_wrong_observation_relationship_is_rejected(self):
        one = market_observations()
        two = market_observations()
        with self.assertRaises(CandidateGenerationError):
            request(two, geometry(one))

    def test_mutated_geometry_and_config_fail_closed(self):
        value = request()
        object.__setattr__(value.geometric_pivots, "diagnostics", ())
        with self.assertRaises(CandidateGenerationError):
            generate_candidate_hypotheses(value)
        value = request()
        object.__setattr__(value.config, "max_candidates_generated", 999)
        with self.assertRaises(CandidateGenerationError):
            generate_candidate_hypotheses(value)

    def test_candidates_and_config_are_immutable(self):
        result = generate_candidate_hypotheses(request())
        with self.assertRaises(FrozenInstanceError):
            result.candidates[0].candidate_id = "changed"
        with self.assertRaises(FrozenInstanceError):
            result.request.config.max_skipped_pivots = 9

    def test_dataset_start_has_no_origin_semantics(self):
        result = generate_candidate_hypotheses(request())
        candidate = result.candidates[0]
        self.assertFalse(hasattr(candidate, "wave1_origin"))
        self.assertFalse(hasattr(candidate, "cycle_origin"))
        self.assertFalse(hasattr(candidate, "start_of_impulse"))
        self.assertNotEqual(result.input_observations.bars[0].timestamp_utc, candidate.ordered_selected_pivots[0].timestamp_utc)

    def test_geometric_kind_creates_no_slot_or_wave_label(self):
        candidate = generate_candidate_hypotheses(request()).candidates[0]
        self.assertFalse(hasattr(candidate, "wave_labels"))
        self.assertFalse(hasattr(candidate, "slot_labels"))
        self.assertFalse(hasattr(candidate, "pattern_family"))

    def test_no_degree_timeframe_ranking_or_confidence_fields(self):
        candidate = generate_candidate_hypotheses(request()).candidates[0]
        for name in ("degree", "rank", "confidence", "preferred", "timeframe_degree"):
            self.assertFalse(hasattr(candidate, name))

    def test_exact_existing_certified_invalidity_is_delegated_and_retained(self):
        base_request = request(configured=config(allowed_candidate_shapes=(CandidateHypothesisShape.THREE_SEGMENT_HYPOTHESIS,)))
        candidate_id = generate_candidate_hypotheses(base_request).candidates[0].candidate_id
        child_subjects = tuple(subject(f"invalid-child-{index}") for index in range(3))
        binding = OrderedChildBinding("invalid-binding", base_request.subject, child_subjects)
        origin = check_p009_triangle_cardinality(
            P009TriangleCardinalityInput(P009CandidateScope.TRIANGLE, binding)
        )
        certificate = certify_structural_invalidity(origin)
        exact_request = BoundedManualChartAnalysisRequest(
            request_id=f"review:{candidate_id}",
            requested_at_utc="2026-09-04T12:00:00Z",
            subject=base_request.subject,
            candidate_id=candidate_id,
            child_binding=binding,
            trusted_invalidity_certificates=(certificate,),
            no_rescue_requested=True,
            provenance_refs=("caller:genuine-existing-certificate",),
        )
        delegated = CandidateMethodologyDelegation(candidate_id, exact_request)
        reviewed_request = request(
            base_request.observations, base_request.geometric_pivots, base_request.subject,
            base_request.config, (delegated,),
        )
        result = generate_candidate_hypotheses(reviewed_request, MethodologyKernel(support.PROTECTED_ROOT))
        candidate = next(item for item in result.candidates if item.candidate_id == candidate_id)
        self.assertIs(GeneratedCandidateReviewState.STRUCTURALLY_INVALID, candidate.review_state)
        self.assertIs(exact_request.subject, candidate.downstream_methodology_result.subject)
        self.assertEqual(1, len(candidate.downstream_methodology_result.structural_invalidity_certificates))
        self.assertEqual(("STRUCTURAL_INVALIDITY_EVIDENCE_NO_RESCUE",), candidate.existing_behaviors_executed)
        self.assertIs(certificate, candidate.downstream_methodology_result.structural_invalidity_certificates[0])

    def test_satisfied_existing_scope_is_reviewed_not_valid(self):
        base = request(configured=config(allowed_candidate_shapes=(CandidateHypothesisShape.THREE_SEGMENT_HYPOTHESIS,)))
        candidate_id = generate_candidate_hypotheses(base).candidates[0].candidate_id
        delegation = CandidateMethodologyDelegation(candidate_id, bounded(base.subject, candidate_id, 101))
        value = request(base.observations, base.geometric_pivots, base.subject, base.config, (delegation,))
        candidate = next(item for item in generate_candidate_hypotheses(value, MethodologyKernel(support.PROTECTED_ROOT)).candidates if item.candidate_id == candidate_id)
        self.assertIs(GeneratedCandidateReviewState.CURRENT_SUPPLIED_SCOPE_REVIEWED, candidate.review_state)
        self.assertIs(False, candidate.elliott_validity_authority)

    def test_undelegated_competing_candidates_remain_present(self):
        base = request(configured=config(allowed_candidate_shapes=(CandidateHypothesisShape.THREE_SEGMENT_HYPOTHESIS,)))
        preliminary = generate_candidate_hypotheses(base)
        candidate_id = preliminary.candidates[0].candidate_id
        delegation = CandidateMethodologyDelegation(candidate_id, bounded(base.subject, candidate_id, 99))
        value = request(base.observations, base.geometric_pivots, base.subject, base.config, (delegation,))
        result = generate_candidate_hypotheses(value, MethodologyKernel(support.PROTECTED_ROOT))
        self.assertEqual(len(preliminary.candidates), len(result.candidates))
        self.assertGreater(sum(c.review_state is GeneratedCandidateReviewState.UNRESOLVED for c in result.candidates), 0)

    def test_unknown_mismatched_and_kernel_less_delegations_fail_closed(self):
        base = request(configured=config(allowed_candidate_shapes=(CandidateHypothesisShape.THREE_SEGMENT_HYPOTHESIS,)))
        candidate_id = generate_candidate_hypotheses(base).candidates[0].candidate_id
        with self.assertRaises(CandidateGenerationError):
            CandidateMethodologyDelegation(candidate_id, bounded(base.subject, "other", 101))
        unknown = CandidateMethodologyDelegation("not-generated", bounded(base.subject, "not-generated", 101))
        with self.assertRaises(CandidateGenerationError):
            generate_candidate_hypotheses(request(base.observations, base.geometric_pivots, base.subject, base.config, (unknown,)), MethodologyKernel(support.PROTECTED_ROOT))
        valid = CandidateMethodologyDelegation(candidate_id, bounded(base.subject, candidate_id, 101))
        with self.assertRaises(CandidateGenerationError):
            generate_candidate_hypotheses(request(base.observations, base.geometric_pivots, base.subject, base.config, (valid,)))

    def test_low_level_delegation_mutation_fails_closed(self):
        base = request(configured=config(allowed_candidate_shapes=(CandidateHypothesisShape.THREE_SEGMENT_HYPOTHESIS,)))
        candidate_id = generate_candidate_hypotheses(base).candidates[0].candidate_id
        delegation = CandidateMethodologyDelegation(candidate_id, bounded(base.subject, candidate_id, 101))
        value = request(base.observations, base.geometric_pivots, base.subject, base.config, (delegation,))
        object.__setattr__(delegation, "candidate_id", "changed")
        with self.assertRaises(CandidateGenerationError):
            generate_candidate_hypotheses(value, MethodologyKernel(support.PROTECTED_ROOT))

    def test_kernel_without_delegation_is_rejected(self):
        with self.assertRaises(CandidateGenerationError):
            generate_candidate_hypotheses(request(), MethodologyKernel(support.PROTECTED_ROOT))

    def test_generator_does_not_issue_methodology_certificates(self):
        source = (support.SRC / "elliott_runtime" / "analysis" / "candidate_generation.py").read_text(encoding="utf-8")
        self.assertNotIn("certify_structural_invalidity", source)
        self.assertNotIn("certify_validated_internal_family", source)
        self.assertNotIn("_structural_invalidity", source)
        self.assertNotIn("_validated_internal_family", source)

    def test_no_candidate_family_label_indicator_trap_fundamental_or_trading_logic(self):
        source = (support.SRC / "elliott_runtime" / "analysis" / "candidate_generation.py").read_text(encoding="utf-8")
        for forbidden in ("RSI", "MACD", "EWO", "Fibonacci", "bull trap", "bear trap", "fundamental analysis", "PREFERRED", "ALTERNATIVE", "confidence_score", "trade_signal"):
            self.assertNotIn(forbidden, source)

    def test_only_public_kernel_imports_and_no_network_process_or_dynamic_code(self):
        path = support.SRC / "elliott_runtime" / "analysis" / "candidate_generation.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = set()
        calls = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import): imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom): imports.add(node.module or "")
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name): calls.add(node.func.id)
        self.assertTrue({"socket", "urllib", "requests", "http", "subprocess"}.isdisjoint(imports))
        self.assertTrue({"eval", "exec", "compile", "__import__"}.isdisjoint(calls))
        self.assertTrue(all(name in {"elliott_methodology_kernel", "elliott_methodology_kernel.contracts"} for name in imports if name.startswith("elliott_methodology_kernel")))

    def test_enumeration_precomputes_cap_and_only_visits_bounded_local_spans(self):
        source = (support.SRC / "elliott_runtime" / "analysis" / "candidate_generation.py").read_text(encoding="utf-8")
        self.assertIn("from itertools import combinations", source)
        self.assertIn("from math import comb", source)
        self.assertIn("if eligible > request.config.max_candidates_generated", source)
        self.assertIn("for tail in combinations(range(first + 1, end)", source)
        self.assertIn("no candidate enumeration or partial result occurred", source)

    def test_methodology_and_registries_remain_exact(self):
        observed = set()
        root = support.SRC / "elliott_methodology_kernel"
        for path in root.glob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, (ast.Assign, ast.AnnAssign)):
                    targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
                    if any(isinstance(item, ast.Name) and item.id.endswith(("BEHAVIOR_ID", "BEHAVIOR")) for item in targets) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        observed.add(node.value.value)
        self.assertEqual(11, len(observed))
        self.assertEqual(7, len(structural_private._PRODUCERS))
        self.assertEqual(0, len(family_private._PRODUCERS))
        self.assertEqual(0, len(family_private._ISSUED))


if __name__ == "__main__":
    unittest.main()
