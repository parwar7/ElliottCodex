import ast
import copy
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import pickle
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
from elliott_runtime.analysis.candidate_generation import (
    CandidateGenerationConfig,
    CandidateGenerationRequest,
    CandidateHypothesisShape,
    CandidateMethodologyDelegation,
    CandidatePivotWindow,
    GeneratedCandidateReviewState,
    generate_candidate_hypotheses,
    validate_candidate_generation_result,
)
import elliott_runtime.analysis.competing_candidates as set_module
from elliott_runtime.analysis.competing_candidates import (
    ACTIVE_IS_NOT_VALIDITY,
    ARTIFACT_CLASSIFICATION,
    CONTAINER_ORDER_IS_NOT_RANK,
    MEMBERSHIP_CLASSIFICATION,
    MEMBERSHIP_IS_NOT_VALIDITY,
    ORDERING_CLASSIFICATION,
    TIMEFRAME_IS_NOT_DEGREE,
    CandidateSetDiagnosticCode,
    CompetingCandidateSetError,
    CompetingCandidateSetRequest,
    build_competing_candidate_set,
)
from elliott_runtime.market_data.geometric_pivots import (
    EqualExtremePolicy,
    GeometricPivotDiscoveryConfig,
    GeometricPivotDiscoveryMethod,
    GeometricPivotDiscoveryRequest,
    discover_geometric_pivots,
)
from elliott_runtime.market_data.ingestion import _normalize


def observations(label="1d", count=30):
    highs = [20 + ((index * 7) % 13) + (index % 2) for index in range(count)]
    records = []
    for index, high in enumerate(highs):
        low = high - 4
        middle = (high + low) / 2
        records.append({
            "timestamp": (datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(days=index)).isoformat(),
            "open": middle, "high": high, "low": low, "close": middle, "volume": 1000,
        })
    return _normalize(records, f"bars:{label}".encode(), "test", label, SymbolIdentity("NVDA", MarketType.STOCK), Timeframe(label, 86400 if label == "1d" else 604800))


def geometric(data):
    return discover_geometric_pivots(GeometricPivotDiscoveryRequest(
        f"geometry:{data.timeframe.label}", data,
        GeometricPivotDiscoveryConfig(GeometricPivotDiscoveryMethod.WINDOWED_LOCAL_EXTREMA, 1, 1, EqualExtremePolicy.LAST, True),
        (f"geometry:{data.timeframe.label}",),
    ))


def analyzed_subject(name="scope"):
    return AnalyzedWaveSubject(name, f"observations:{name}")


def config(*, one=False):
    return CandidateGenerationConfig(
        4 if one else 6,
        4 if one else 6,
        0,
        1 if one else 20,
        (CandidateHypothesisShape.THREE_SEGMENT_HYPOTHESIS,) if one else (
            CandidateHypothesisShape.THREE_SEGMENT_HYPOTHESIS,
            CandidateHypothesisShape.FIVE_SEGMENT_HYPOTHESIS,
        ),
        CandidatePivotWindow.LATEST,
    )


def generation(*, data=None, subject=None, one=False, delegations=(), kernel=None):
    data = data or observations()
    subject = subject or analyzed_subject()
    request = CandidateGenerationRequest(
        f"generation:{data.timeframe.label}",
        "2026-09-04T15:00:00Z",
        subject,
        data,
        geometric(data),
        config(one=one),
        delegations,
        ("generation:test",),
    )
    return generate_candidate_hypotheses(request, kernel)


def set_request(result, **changes):
    values = {
        "set_id": "competing-set:test",
        "analysis_scope_id": "NVDA:one-timeframe",
        "candidate_generation_result": result,
        "provenance_refs": ("set:test",),
    }
    values.update(changes)
    return CompetingCandidateSetRequest(**values)


def reviewed_request(subject, candidate_id):
    return BoundedManualChartAnalysisRequest(
        f"review:{candidate_id}", "2026-09-04T15:00:00Z", subject, candidate_id,
        manual_behavior_facts=(ManualP004Wave2OriginFact(CandidateScope.NORMAL_IMPULSE, ImpulseDirection.UP, 100, 101),),
        provenance_refs=("reviewed:p004",),
    )


def invalid_request(subject, candidate_id):
    children = tuple(analyzed_subject(f"child:{index}") for index in range(3))
    binding = OrderedChildBinding("binding:invalid", subject, children)
    origin = check_p009_triangle_cardinality(P009TriangleCardinalityInput(P009CandidateScope.TRIANGLE, binding))
    certificate = certify_structural_invalidity(origin)
    request = BoundedManualChartAnalysisRequest(
        f"invalid:{candidate_id}", "2026-09-04T15:00:00Z", subject, candidate_id,
        child_binding=binding,
        trusted_invalidity_certificates=(certificate,),
        no_rescue_requested=True,
        provenance_refs=("invalid:genuine-certificate",),
    )
    return request, certificate


def mixed_generation(*, one_invalid=False):
    data = observations()
    subject = analyzed_subject("mixed")
    preliminary = generation(data=data, subject=subject, one=one_invalid)
    first = preliminary.candidates[0].candidate_id
    invalid, certificate = invalid_request(subject, first)
    delegations = [CandidateMethodologyDelegation(first, invalid)]
    if not one_invalid:
        second = preliminary.candidates[1].candidate_id
        delegations.append(CandidateMethodologyDelegation(second, reviewed_request(subject, second)))
    result = generation(data=data, subject=subject, one=one_invalid, delegations=tuple(delegations), kernel=MethodologyKernel(support.PROTECTED_ROOT))
    return result, certificate


class CompetingCandidateSetTests(unittest.TestCase):
    def test_classifications_and_invariants_are_exact(self):
        self.assertEqual("PROJECT_ANALYSIS_INFRASTRUCTURE", ARTIFACT_CLASSIFICATION)
        self.assertEqual("CALLER_OR_GENERATOR_SUPPLIED_CANDIDATE_MEMBERSHIP", MEMBERSHIP_CLASSIFICATION)
        self.assertEqual("PROJECT_OPERATIONAL_POLICY", ORDERING_CLASSIFICATION)
        self.assertEqual((True, True, True, True), (MEMBERSHIP_IS_NOT_VALIDITY, ACTIVE_IS_NOT_VALIDITY, CONTAINER_ORDER_IS_NOT_RANK, TIMEFRAME_IS_NOT_DEGREE))

    def test_exact_generation_result_and_full_ancestry_are_retained(self):
        generated = generation()
        request = set_request(generated)
        result = build_competing_candidate_set(request)
        self.assertIs(generated, result.candidate_generation_result)
        self.assertIs(generated.input_observations, result.source_observations)
        self.assertIs(generated.input_geometric_pivots, result.geometric_pivot_result)
        self.assertIs(request.provenance_refs, result.provenance_refs)

    def test_exact_candidate_identities_and_original_order_are_retained(self):
        generated = generation()
        result = build_competing_candidate_set(set_request(generated))
        self.assertIs(generated.candidates, result.ordered_candidates)
        self.assertTrue(all(a is b for a, b in zip(generated.candidates, result.ordered_candidates, strict=True)))
        self.assertEqual([c.candidate_id for c in generated.candidates], [c.candidate_id for c in result.ordered_candidates])

    def test_set_and_result_are_immutable_factory_guarded_and_nonserializable(self):
        request = set_request(generation())
        result = build_competing_candidate_set(request)
        with self.assertRaises(FrozenInstanceError):
            request.set_id = "changed"
        with self.assertRaises(FrozenInstanceError):
            result.analysis_scope_id = "changed"
        with self.assertRaises(TypeError):
            type(result)(result)
        with self.assertRaises(TypeError):
            pickle.dumps(request)
        with self.assertRaises(TypeError):
            pickle.dumps(result)

    def test_empty_generation_result_is_rejected(self):
        data = observations(count=4)
        generated = generation(data=data)
        self.assertEqual((), generated.candidates)
        with self.assertRaises(CompetingCandidateSetError):
            set_request(generated)

    def test_one_candidate_is_allowed_without_preference_or_confirmation(self):
        result = build_competing_candidate_set(set_request(generation(one=True)))
        self.assertEqual(1, result.candidate_state_inventory.total_candidates)
        self.assertIn(CandidateSetDiagnosticCode.SINGLE_CANDIDATE_SET, [item.code for item in result.diagnostics])
        candidate = result.ordered_candidates[0]
        self.assertIs(False, candidate.elliott_validity_authority)

    def test_multiple_candidates_and_both_neutral_shapes_coexist(self):
        result = build_competing_candidate_set(set_request(generation()))
        self.assertGreater(len(result.ordered_candidates), 1)
        self.assertEqual({CandidateHypothesisShape.THREE_SEGMENT_HYPOTHESIS, CandidateHypothesisShape.FIVE_SEGMENT_HYPOTHESIS}, {item.candidate_shape for item in result.ordered_candidates})
        self.assertIn(CandidateSetDiagnosticCode.MULTIPLE_CANDIDATES_RETAINED, [item.code for item in result.diagnostics])

    def test_unresolved_candidates_remain_active_and_unranked(self):
        result = build_competing_candidate_set(set_request(generation()))
        self.assertEqual(result.ordered_candidates, result.unresolved_candidates)
        self.assertEqual(result.ordered_candidates, result.active_candidates)
        self.assertEqual(len(result.ordered_candidates), result.candidate_state_inventory.active_candidates)

    def test_invalid_is_retained_historically_but_excluded_only_from_active_view(self):
        generated, certificate = mixed_generation()
        result = build_competing_candidate_set(set_request(generated))
        invalid = result.structurally_invalid_candidates[0]
        self.assertIn(invalid, result.ordered_candidates)
        self.assertNotIn(invalid, result.active_candidates)
        self.assertIs(certificate, invalid.downstream_methodology_result.structural_invalidity_certificates[0])
        self.assertGreater(len(result.active_candidates), 0)

    def test_reviewed_scope_remains_active_but_never_valid(self):
        generated, _ = mixed_generation()
        result = build_competing_candidate_set(set_request(generated))
        reviewed = result.reviewed_scope_candidates[0]
        self.assertIn(reviewed, result.active_candidates)
        self.assertIs(GeneratedCandidateReviewState.CURRENT_SUPPLIED_SCOPE_REVIEWED, reviewed.review_state)
        self.assertIs(False, reviewed.elliott_validity_authority)

    def test_one_candidate_failure_does_not_validate_siblings(self):
        generated, _ = mixed_generation()
        result = build_competing_candidate_set(set_request(generated))
        self.assertEqual(1, len(result.structurally_invalid_candidates))
        self.assertTrue(any(item.review_state is GeneratedCandidateReviewState.UNRESOLVED for item in result.active_candidates))
        self.assertFalse(any(item.elliott_validity_authority for item in result.active_candidates))

    def test_all_invalid_allows_empty_active_view_with_diagnostic(self):
        generated, _ = mixed_generation(one_invalid=True)
        result = build_competing_candidate_set(set_request(generated))
        self.assertEqual((), result.active_candidates)
        self.assertIn(CandidateSetDiagnosticCode.NO_ACTIVE_CANDIDATES, [item.code for item in result.diagnostics])

    def test_state_inventory_is_exact_partition(self):
        generated, _ = mixed_generation()
        result = build_competing_candidate_set(set_request(generated))
        inventory = result.candidate_state_inventory
        self.assertEqual(len(result.ordered_candidates), inventory.total_candidates)
        self.assertEqual(len(result.structurally_invalid_candidates), inventory.structurally_invalid)
        self.assertEqual(len(result.unresolved_candidates), inventory.unresolved)
        self.assertEqual(len(result.reviewed_scope_candidates), inventory.current_supplied_scope_reviewed)
        self.assertEqual(len(result.active_candidates), inventory.active_candidates)

    def test_duplicate_identity_and_duplicate_id_mutations_fail_closed(self):
        generated = generation()
        original = generated.candidates
        object.__setattr__(generated, "candidates", (original[0], original[0]) + original[2:])
        with self.assertRaises(Exception):
            build_competing_candidate_set(set_request(generated))
        generated = generation()
        object.__setattr__(generated.candidates[1], "candidate_id", generated.candidates[0].candidate_id)
        with self.assertRaises(Exception):
            build_competing_candidate_set(set_request(generated))

    def test_foreign_candidate_and_wrong_ancestry_mutations_fail_closed(self):
        generated = generation()
        foreign = generation(data=observations("1wk"), subject=analyzed_subject("foreign"))
        object.__setattr__(generated, "candidates", (foreign.candidates[0],) + generated.candidates[1:])
        with self.assertRaises(Exception):
            set_request(generated)
        generated = generation()
        object.__setattr__(generated.candidates[0], "source_geometric_pivots", foreign.input_geometric_pivots)
        with self.assertRaises(Exception):
            set_request(generated)

    def test_mapping_duck_and_subclass_are_rejected(self):
        class Duck:
            candidates = ()
        for value in ({"set_id": "x"}, Duck(), object()):
            with self.assertRaises(CompetingCandidateSetError):
                build_competing_candidate_set(value)
        with self.assertRaises(TypeError):
            type("RequestSubclass", (CompetingCandidateSetRequest,), {})

    def test_low_level_request_result_and_inventory_mutation_fail_closed(self):
        request = set_request(generation())
        result = build_competing_candidate_set(request)
        object.__setattr__(request, "analysis_scope_id", "changed")
        with self.assertRaises(CompetingCandidateSetError):
            build_competing_candidate_set(request)
        result = build_competing_candidate_set(set_request(generation()))
        object.__setattr__(result.candidate_state_inventory, "active_candidates", 0)
        with self.assertRaises(CompetingCandidateSetError):
            copy.copy(result)

    def test_generation_result_constructor_copy_pickle_and_substitute_boundaries(self):
        generated = generation()
        self.assertIs(generated, validate_candidate_generation_result(generated))
        self.assertIs(generated, copy.copy(generated))
        with self.assertRaises(TypeError):
            pickle.dumps(generated)
        with self.assertRaises(TypeError):
            type(generated)()

    def test_single_generation_run_prevents_cross_timeframe_mix(self):
        daily = generation(data=observations("1d"))
        weekly = generation(data=observations("1wk"), subject=analyzed_subject("weekly"))
        daily_result = build_competing_candidate_set(set_request(daily))
        weekly_result = build_competing_candidate_set(set_request(weekly, analysis_scope_id="NVDA:weekly"))
        self.assertIsNot(daily_result.source_observations, weekly_result.source_observations)
        self.assertTrue(all(item.source_observations is daily_result.source_observations for item in daily_result.ordered_candidates))
        self.assertTrue(all(item.source_observations is weekly_result.source_observations for item in weekly_result.ordered_candidates))

    def test_diagnostics_are_neutral_and_state_specific(self):
        generated, _ = mixed_generation()
        result = build_competing_candidate_set(set_request(generated))
        codes = {item.code for item in result.diagnostics}
        self.assertIn(CandidateSetDiagnosticCode.CANDIDATE_SET_CREATED, codes)
        self.assertIn(CandidateSetDiagnosticCode.STRUCTURAL_INVALIDITY_PRESENT, codes)
        self.assertIn(CandidateSetDiagnosticCode.UNRESOLVED_CANDIDATES_PRESENT, codes)
        self.assertIn(CandidateSetDiagnosticCode.REVIEWED_SCOPE_CANDIDATES_PRESENT, codes)

    def test_result_surface_has_no_ranking_validity_family_degree_or_forecast(self):
        fields = set(set_module.CompetingCandidateSetResult.__dataclass_fields__)
        forbidden = {"preferred_candidate", "winning_candidate", "rank", "confidence", "probability", "valid", "family", "degree", "forecast", "target", "trade"}
        self.assertTrue(fields.isdisjoint(forbidden))

    def test_module_has_no_labels_scoring_traps_indicators_fundamentals_or_trading(self):
        source = (support.SRC / "elliott_runtime" / "analysis" / "competing_candidates.py").read_text(encoding="utf-8")
        for forbidden in ("PREFERRED", "ALTERNATIVE", "REMOTE", "confidence %", "probability", "Fibonacci score", "RSI score", "MACD score", "bull trap", "bear trap", "fundamental score", "TRADE", "STAND_ASIDE"):
            self.assertNotIn(forbidden, source)

    def test_container_does_not_rerun_methodology_or_import_certification(self):
        path = support.SRC / "elliott_runtime" / "analysis" / "competing_candidates.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        calls = {node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        imports = {node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        self.assertNotIn("analyze_bounded_manual_chart", calls)
        self.assertNotIn("MethodologyKernel", source)
        self.assertFalse(any("certification" in item for item in imports))

    def test_no_eval_exec_dynamic_import_network_or_process_capability(self):
        source = (support.SRC / "elliott_runtime" / "analysis" / "competing_candidates.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import): names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom): names.add(node.module or "")
        self.assertTrue({"socket", "urllib", "requests", "http", "subprocess", "importlib"}.isdisjoint(names))
        self.assertTrue(all(not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec", "compile", "__import__"}) for node in ast.walk(tree)))

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
