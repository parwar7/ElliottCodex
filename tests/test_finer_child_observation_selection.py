import ast
from datetime import datetime, timedelta, timezone
import inspect
import unittest

import support
import elliott_methodology_kernel._structural_invalidity_certification as structural_private
import elliott_methodology_kernel._validated_internal_family_certification as family_private
from elliott_methodology_kernel import (
    MethodologyKernel,
    MultiTimeframeObservationBundle,
    ObservationResolutionRelation,
)
from elliott_methodology_kernel.contracts import MarketType, SymbolIdentity, Timeframe
from elliott_runtime.analysis.candidate_generation import CandidateHypothesisShape
from elliott_runtime.analysis.finer_child_observation_selection import (
    ARTIFACT_CLASSIFICATION,
    CROSS_TIMEFRAME_OBSERVATION_IS_NOT_CONFIRMATION,
    FINER_DATA_AVAILABLE_IS_NOT_INTERNALS_VISIBLE,
    FINER_DATA_SELECTED_IS_NOT_CHILD_FAMILY_VALIDATED,
    FINER_TIMEFRAME_IS_NOT_LOWER_DEGREE,
    GEOMETRY_PARAMETER_CLASSIFICATION,
    RESOLUTION_CLASSIFICATION,
    SELECTION_CLASSIFICATION,
    WINDOW_IS_NOT_ELLIOTT_ENDPOINT_AUTHORITY,
    ChildObservationCoverageState,
    ChildObservationSelectionConfig,
    ChildObservationSelectionRequest,
    ChildObservationSelectionResult,
    FinerChildObservationSelectionError,
    FinerWindowResourceBoundExceeded,
    SelectedChildObservationWindow,
    select_finer_child_observations,
)
import elliott_runtime.analysis.finer_child_observation_selection as selection_module
from elliott_runtime.analysis.recursive_child_candidate_generation import (
    ChildCandidateGenerationConfig,
    ChildRequirementGenerationStatus,
    RecursiveChildCandidateGenerationLimitExceeded,
    RecursiveChildCandidateGenerationRequest,
    generate_child_candidate_evidence,
)
from elliott_runtime.market_data.geometric_pivots import (
    EqualExtremePolicy,
    GeometricPivotDiscoveryConfig,
    GeometricPivotDiscoveryMethod,
)
from elliott_runtime.market_data.ingestion import _normalize
from test_multi_timeframe_observation_transport import attach, recursive_candidate
from test_recursive_child_candidate_generation import SHAPES, upstream


def finer_observations(parent, *, start=None, end=None, seconds=3600, symbol=None):
    start = start or parent.bars[0].timestamp_utc - timedelta(days=2)
    end = end or parent.bars[-1].timestamp_utc + timedelta(days=2)
    records = []
    current = start
    index = 0
    while current <= end:
        high = 100 + ((index * 7) % 13) + (index % 2)
        low = high - 4
        middle = (high + low) / 2
        records.append({
            "timestamp": current.isoformat(),
            "open": middle,
            "high": high,
            "low": low,
            "close": middle,
            "volume": 1000 + index,
        })
        current += timedelta(seconds=seconds)
        index += 1
    return _normalize(
        records,
        f"finer:{start}:{end}:{seconds}".encode(),
        "test",
        "exact-finer-source",
        symbol or parent.symbol,
        Timeframe(f"{seconds}s", seconds),
    )


def context_for(parent, selected):
    observation_sets = (
        (selected,)
        if parent.timeframe.resolution_seconds == selected.timeframe.resolution_seconds
        else (parent, selected)
    )
    bundle = MultiTimeframeObservationBundle(
        parent.symbol,
        observation_sets,
        ("test:finer-bundle",),
    )
    return attach(recursive_candidate(), bundle, (), "finer-selection-context")


def geometry_config():
    return GeometricPivotDiscoveryConfig(
        GeometricPivotDiscoveryMethod.WINDOWED_LOCAL_EXTREMA,
        1,
        1,
        EqualExtremePolicy.LAST,
        True,
    )


def setup_case(*, selected=None):
    source = upstream()
    coarse = generate_child_candidate_evidence(RecursiveChildCandidateGenerationRequest(
        "coarse-window-source",
        "2026-09-04T00:00:00Z",
        source,
        ChildCandidateGenerationConfig(20, 20, 8, 6, 1, 50, 300, SHAPES),
        ("test:coarse-window-source",),
    ))
    requirement = source.internal_requirements[0]
    window = coarse.evaluation_windows[0]
    parent = requirement.parent_candidate.source_observations
    selected = selected or finer_observations(parent, seconds=21600)
    context = context_for(parent, selected)
    request = ChildObservationSelectionRequest(
        "selection:test",
        requirement,
        window,
        context,
        selected,
        geometry_config(),
        ChildObservationSelectionConfig(1000, 1000),
        ("test:finer-selection",),
    )
    return source, requirement, window, parent, selected, context, request


def child_config(**changes):
    values = dict(
        max_requirements_processed=20,
        max_total_child_windows=20,
        max_pivots_per_child_window=30,
        max_child_candidate_span_pivots=6,
        max_child_skipped_pivots=1,
        max_child_candidates_per_requirement=1000,
        max_total_child_candidates=5000,
        allowed_child_candidate_shapes=SHAPES,
        max_requirements_with_finer_selection=10,
        max_total_finer_geometric_pivots=1000,
    )
    values.update(changes)
    return ChildCandidateGenerationConfig(**values)


class FinerChildObservationSelectionTests(unittest.TestCase):
    def test_authority_classifications_and_invariants_are_exact(self):
        self.assertEqual("PROJECT_ANALYSIS_INFRASTRUCTURE", ARTIFACT_CLASSIFICATION)
        self.assertEqual("CALLER_SUPPLIED_OBSERVATION_SELECTION", SELECTION_CLASSIFICATION)
        self.assertEqual("PROJECT_OPERATIONAL_POLICY", RESOLUTION_CLASSIFICATION)
        self.assertEqual("CALLER_SUPPLIED_GEOMETRY_PARAMETER", GEOMETRY_PARAMETER_CLASSIFICATION)
        self.assertEqual((True, True, True, True, True), (
            FINER_TIMEFRAME_IS_NOT_LOWER_DEGREE,
            FINER_DATA_AVAILABLE_IS_NOT_INTERNALS_VISIBLE,
            FINER_DATA_SELECTED_IS_NOT_CHILD_FAMILY_VALIDATED,
            CROSS_TIMEFRAME_OBSERVATION_IS_NOT_CONFIRMATION,
            WINDOW_IS_NOT_ELLIOTT_ENDPOINT_AUTHORITY,
        ))

    def test_exact_context_observations_requirement_and_window_are_retained(self):
        _, requirement, window, _, selected, context, request = setup_case()
        result = select_finer_child_observations(request)
        self.assertIsInstance(result, ChildObservationSelectionResult)
        self.assertIs(requirement, result.request.internal_requirement)
        self.assertIs(window, result.request.proposed_child_window)
        self.assertIs(context, result.request.multi_timeframe_context)
        self.assertIs(selected, result.selected_window.source_observations)
        self.assertIs(ObservationResolutionRelation.FINER_THAN, result.resolution_relation_to_parent)

    def test_full_coverage_exact_view_and_geometry_preserve_identities(self):
        _, _, window, _, selected, _, request = setup_case()
        result = select_finer_child_observations(request)
        view = result.selected_window
        self.assertIs(ChildObservationCoverageState.FULL_WINDOW_COVERAGE, view.coverage_state)
        self.assertEqual(window.start_pivot.timestamp_utc, view.parent_window_start_utc)
        self.assertEqual(window.end_pivot.timestamp_utc, view.parent_window_end_utc)
        expected = tuple(bar for bar in selected.bars if view.parent_window_start_utc <= bar.timestamp_utc <= view.parent_window_end_utc)
        self.assertTrue(all(a is b for a, b in zip(view.ordered_bars, expected, strict=True)))
        self.assertIs(selected, result.finer_geometric_pivots.input_observations)
        self.assertIs(view.ordered_bars, result.finer_geometric_pivots.scoped_bars)
        self.assertFalse(view.elliott_endpoint_authority)

    def test_partial_and_no_coverage_are_diagnostics_not_geometry_or_invalidity(self):
        source, requirement, window, parent, _, _, _ = setup_case()
        for state, start, end in (
            (ChildObservationCoverageState.PARTIAL_WINDOW_COVERAGE, window.start_pivot.timestamp_utc + timedelta(hours=6), window.end_pivot.timestamp_utc + timedelta(days=2)),
            (ChildObservationCoverageState.NO_WINDOW_COVERAGE, window.end_pivot.timestamp_utc + timedelta(days=2), window.end_pivot.timestamp_utc + timedelta(days=3)),
        ):
            with self.subTest(state=state):
                selected = finer_observations(parent, start=start, end=end, seconds=21600)
                request = ChildObservationSelectionRequest(
                    "selection:coverage", requirement, window, context_for(parent, selected),
                    selected, geometry_config(), ChildObservationSelectionConfig(1000, 1000),
                    ("test:coverage",),
                )
                result = select_finer_child_observations(request)
                self.assertIs(state, result.selected_window.coverage_state)
                self.assertIsNone(result.finer_geometric_pivots)
                self.assertFalse(hasattr(result, "structural_invalidity"))
                integrated = generate_child_candidate_evidence(RecursiveChildCandidateGenerationRequest(
                    "coverage-integration", "2026-09-04T00:00:00Z", source,
                    child_config(), ("test:coverage-integration",), (result,),
                ))
                outcome = next(item for item in integrated.requirement_outcomes if item.internal_requirement is requirement)
                self.assertIsNone(outcome.generated_evidence)
                self.assertIn(outcome.status, {
                    ChildRequirementGenerationStatus.PARTIAL_FINER_OBSERVATION_COVERAGE,
                    ChildRequirementGenerationStatus.NO_FINER_OBSERVATION_COVERAGE,
                })

    def test_foreign_symbol_bundle_rejected_without_rewrite(self):
        _, requirement, window, parent, _, _, _ = setup_case()
        foreign = finer_observations(
            parent,
            seconds=21600,
            symbol=SymbolIdentity("OTHER", MarketType.STOCK),
        )
        foreign_context = attach(
            recursive_candidate(),
            MultiTimeframeObservationBundle(
                foreign.symbol,
                (foreign,),
                ("test:foreign-bundle",),
            ),
            (),
            "foreign-context",
        )
        with self.assertRaises(FinerChildObservationSelectionError):
            ChildObservationSelectionRequest(
                "foreign", requirement, window, foreign_context, foreign,
                geometry_config(), ChildObservationSelectionConfig(1000, 1000), ("test:foreign",),
            )
        self.assertEqual("OTHER", foreign.symbol.symbol)

    def test_same_and_coarser_resolutions_are_rejected(self):
        _, requirement, window, parent, _, _, _ = setup_case()
        for seconds in (parent.timeframe.resolution_seconds, parent.timeframe.resolution_seconds * 2):
            selected = finer_observations(parent, seconds=seconds)
            with self.assertRaises(FinerChildObservationSelectionError):
                ChildObservationSelectionRequest(
                    "not-finer", requirement, window, context_for(parent, selected), selected,
                    geometry_config(), ChildObservationSelectionConfig(1000, 1000), ("test:not-finer",),
                )

    def test_mapping_duck_subclass_unissued_and_mutation_fail_closed(self):
        *_, request = setup_case()
        for value in ({"selection_id": "x"}, object()):
            with self.assertRaises(FinerChildObservationSelectionError):
                select_finer_child_observations(value)
        with self.assertRaises(TypeError):
            type("WindowSubclass", (SelectedChildObservationWindow,), {})
        malformed = object.__new__(ChildObservationSelectionResult)
        with self.assertRaises(Exception):
            malformed._validated()
        result = select_finer_child_observations(request)
        object.__setattr__(result.selected_window, "provenance_refs", ("changed",))
        with self.assertRaises(FinerChildObservationSelectionError):
            result._validated()

    def test_bar_and_pivot_resource_bounds_fail_without_truncation(self):
        *_, request = setup_case()
        with self.assertRaisesRegex(FinerWindowResourceBoundExceeded, "max_bars"):
            select_finer_child_observations(ChildObservationSelectionRequest(
                request.selection_id, request.internal_requirement, request.proposed_child_window,
                request.multi_timeframe_context, request.selected_observations, request.geometry_config,
                ChildObservationSelectionConfig(1, 1000), request.provenance_refs,
            ))
        with self.assertRaisesRegex(FinerWindowResourceBoundExceeded, "max_geometric_pivots"):
            select_finer_child_observations(ChildObservationSelectionRequest(
                request.selection_id, request.internal_requirement, request.proposed_child_window,
                request.multi_timeframe_context, request.selected_observations, request.geometry_config,
                ChildObservationSelectionConfig(1000, 1), request.provenance_refs,
            ))

    def test_full_selection_reuses_existing_child_generator_and_competing_set(self):
        source, requirement, window, _, _, _, request = setup_case()
        selection = select_finer_child_observations(request)
        result = generate_child_candidate_evidence(RecursiveChildCandidateGenerationRequest(
            "finer-integration", "2026-09-04T00:00:00Z", source,
            child_config(), ("test:finer-integration",), (selection,),
        ))
        outcome = next(item for item in result.requirement_outcomes if item.internal_requirement is requirement)
        self.assertIs(ChildRequirementGenerationStatus.FINER_RESOLUTION_NEUTRAL_CHILD_EVIDENCE_AVAILABLE, outcome.status)
        evidence = outcome.generated_evidence
        self.assertIs(selection, evidence.finer_observation_selection)
        self.assertIs(window, evidence.evaluation_window)
        self.assertIs(selection.finer_geometric_pivots, evidence.candidate_generation_result.input_geometric_pivots)
        self.assertTrue(evidence.candidate_generation_result.candidates)
        self.assertIs(evidence.candidate_generation_result, evidence.competing_candidate_set.candidate_generation_result)
        self.assertFalse(evidence.requirement_satisfied)
        self.assertFalse(evidence.validated_child_wave)
        self.assertFalse(evidence.validated_internal_family)

    def test_three_and_five_shapes_create_no_family_or_degree_proof(self):
        source, requirement, _, _, _, _, request = setup_case()
        selection = select_finer_child_observations(request)
        result = generate_child_candidate_evidence(RecursiveChildCandidateGenerationRequest(
            "shape-nonproof", "2026-09-04T00:00:00Z", source,
            child_config(), ("test:shape-nonproof",), (selection,),
        ))
        evidence = next(item for item in result.generated_child_evidence if item.internal_requirement is requirement)
        shapes = {item.candidate_shape for item in evidence.candidate_generation_result.candidates}
        self.assertEqual(set(SHAPES), shapes)
        for candidate in evidence.candidate_generation_result.candidates:
            self.assertFalse(candidate.elliott_validity_authority)
            self.assertFalse(candidate.family_authority)
            self.assertFalse(candidate.degree_authority)

    def test_duplicate_foreign_and_over_limit_finer_selections_fail(self):
        source, _, _, _, _, _, request = setup_case()
        selection = select_finer_child_observations(request)
        with self.assertRaises(Exception):
            RecursiveChildCandidateGenerationRequest(
                "duplicate", "2026-09-04T00:00:00Z", source, child_config(),
                ("test:duplicate",), (selection, selection),
            )
        with self.assertRaises(RecursiveChildCandidateGenerationLimitExceeded):
            generate_child_candidate_evidence(RecursiveChildCandidateGenerationRequest(
                "selection-cap", "2026-09-04T00:00:00Z", source,
                child_config(max_requirements_with_finer_selection=1, max_total_finer_geometric_pivots=1),
                ("test:selection-cap",), (selection,),
            ))

    def test_no_automatic_selection_resampling_4h_p023_or_extra_features(self):
        source = inspect.getsource(selection_module)
        tree = ast.parse(source)
        calls = {node.func.id for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
        self.assertIn("discover_geometric_pivots", calls)
        for forbidden in (
            "YahooFinanceProvider", "resample", "4h", "evaluate_p023", "PREFERRED",
            "ALTERNATIVE", "REMOTE", "RSI", "MACD", "EWO", "Fibonacci",
            "bull_trap", "bear_trap", "forecast", "trade_signal",
        ):
            self.assertNotIn(forbidden, source)

    def test_cross_family_confirmation_ranking_and_labels_are_absent(self):
        fields = ChildObservationSelectionResult.__dataclass_fields__
        for forbidden in (
            "degree", "visibility", "family_result", "rank", "confidence",
            "confirmation", "wave_label", "target", "trade",
        ):
            self.assertNotIn(forbidden, fields)

    def test_inventories_blockers_and_legacy_kernel_remain_unchanged(self):
        self.assertEqual(7, len(structural_private._PRODUCERS))
        self.assertEqual(0, len(family_private._PRODUCERS))
        self.assertEqual(0, len(family_private._ISSUED))
        self.assertIn("NOT_IMPLEMENTED", inspect.getsource(MethodologyKernel.analyze))
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
