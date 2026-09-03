import ast
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import math
import unittest

import support
import elliott_methodology_kernel._structural_invalidity_certification as structural_private
import elliott_methodology_kernel._validated_internal_family_certification as family_private
from elliott_methodology_kernel.contracts import MarketType, NormalizedMarketObservations, SymbolIdentity, Timeframe
from elliott_runtime.market_data.geometric_pivots import (
    ARTIFACT_CLASSIFICATION,
    ELLIOTT_ENDPOINT_AUTHORITY,
    PARAMETER_CLASSIFICATION,
    TIMEFRAME_IS_NOT_DEGREE,
    EqualExtremePolicy,
    GeometricPivotDiscoveryConfig,
    GeometricPivotDiscoveryError,
    GeometricPivotDiscoveryMethod,
    GeometricPivotDiscoveryRequest,
    GeometricPivotKind,
    GeometricPivotObservation,
    GeometricPivotState,
    discover_geometric_pivots,
)
from elliott_runtime.market_data.ingestion import _normalize


def observations(highs, lows=None, *, timestamps=None):
    lows = [value - 2.0 for value in highs] if lows is None else lows
    timestamps = timestamps or [
        datetime(2024, 1, 1, tzinfo=timezone.utc) + timedelta(days=index)
        for index in range(len(highs))
    ]
    records = []
    for stamp, high, low in zip(timestamps, highs, lows):
        middle = (high + low) / 2
        records.append(
            {
                "timestamp": stamp.isoformat(),
                "open": middle,
                "high": high,
                "low": low,
                "close": middle,
                "volume": 1000,
            }
        )
    return _normalize(
        records,
        b"test-bars",
        "test",
        "in-memory",
        SymbolIdentity("TEST", MarketType.STOCK),
        Timeframe("1d", 86400),
    )


def config(**changes):
    values = {
        "method": GeometricPivotDiscoveryMethod.WINDOWED_LOCAL_EXTREMA,
        "left_window_bars": 1,
        "right_window_bars": 1,
        "equal_extreme_policy": EqualExtremePolicy.FIRST,
        "include_developing": False,
    }
    values.update(changes)
    return GeometricPivotDiscoveryConfig(**values)


def request(data=None, configured=None, **changes):
    values = {
        "request_id": "geometry-test",
        "observations": data or observations([2, 5, 3, 1, 4, 2]),
        "config": configured or config(),
        "provenance_refs": ("test:caller-configured",),
    }
    values.update(changes)
    return GeometricPivotDiscoveryRequest(**values)


class SubclassedRequest(GeometricPivotDiscoveryRequest):
    pass


class GeometricPivotTests(unittest.TestCase):
    def test_classification_is_infrastructure_without_endpoint_authority(self):
        self.assertEqual("PROJECT_DATA_ANALYSIS_INFRASTRUCTURE", ARTIFACT_CLASSIFICATION)
        self.assertEqual("CALLER_SUPPLIED_GEOMETRY_PARAMETER", PARAMETER_CLASSIFICATION)
        self.assertIs(False, ELLIOTT_ENDPOINT_AUTHORITY)
        self.assertIs(True, TIMEFRAME_IS_NOT_DEGREE)

    def test_exact_normalized_input_is_accepted_and_identity_preserved(self):
        source = observations([2, 5, 3])
        result = discover_geometric_pivots(request(source))
        self.assertIs(source, result.input_observations)
        self.assertEqual("geometry-test", result.request_id)

    def test_high_low_detection_and_order_are_deterministic(self):
        value = request(observations([2, 5, 3, 1, 4, 2]))
        first = discover_geometric_pivots(value)
        second = discover_geometric_pivots(value)
        self.assertEqual(first, second)
        self.assertEqual(
            [GeometricPivotKind.HIGH, GeometricPivotKind.LOW, GeometricPivotKind.HIGH],
            [pivot.pivot_kind for pivot in first.pivots],
        )
        self.assertEqual(sorted(p.timestamp_utc for p in first.pivots), [p.timestamp_utc for p in first.pivots])

    def test_window_parameter_controls_only_geometric_comparison(self):
        data = observations([1, 4, 3, 5, 2, 1])
        narrow = discover_geometric_pivots(request(data, config(left_window_bars=1, right_window_bars=1)))
        wide = discover_geometric_pivots(request(data, config(left_window_bars=2, right_window_bars=2)))
        self.assertEqual(2, sum(p.pivot_kind is GeometricPivotKind.HIGH for p in narrow.pivots))
        self.assertEqual(1, sum(p.pivot_kind is GeometricPivotKind.HIGH for p in wide.pivots))

    def test_equal_extremes_first_and_last_are_exact(self):
        data = observations([1, 5, 5, 1])
        first = discover_geometric_pivots(request(data, config(equal_extreme_policy=EqualExtremePolicy.FIRST)))
        last = discover_geometric_pivots(request(data, config(equal_extreme_policy=EqualExtremePolicy.LAST)))
        self.assertEqual(data.bars[1].timestamp_utc, first.pivots[0].timestamp_utc)
        self.assertEqual(data.bars[2].timestamp_utc, last.pivots[0].timestamp_utc)

    def test_same_bar_high_and_low_is_excluded_without_duplicate_timestamp(self):
        data = observations([2, 10, 3], [1, -10, 0])
        result = discover_geometric_pivots(request(data))
        self.assertEqual((), result.pivots)
        self.assertIn("AMBIGUOUS_SAME_BAR_HIGH_LOW_EXCLUDED=1", result.diagnostics)
        self.assertEqual(len({p.timestamp_utc for p in result.pivots}), len(result.pivots))

    def test_developing_tail_is_explicit_and_can_change(self):
        partial = observations([1, 2, 3])
        configured = config(include_developing=True)
        before = discover_geometric_pivots(request(partial, configured))
        self.assertEqual(GeometricPivotState.DEVELOPING, before.pivots[-1].state)
        extended = observations([1, 2, 3, 4])
        after = discover_geometric_pivots(request(extended, configured))
        self.assertNotIn(partial.bars[-1].timestamp_utc, [p.timestamp_utc for p in after.pivots])

    def test_confirmed_history_is_stable_when_future_bars_are_appended(self):
        configured = config(include_developing=True)
        before = discover_geometric_pivots(request(observations([1, 4, 2, 1]), configured))
        confirmed_before = tuple(p for p in before.pivots if p.state is GeometricPivotState.CONFIRMED_BY_GEOMETRY)
        after = discover_geometric_pivots(request(observations([1, 4, 2, 1, 8]), configured))
        by_identity = {(p.timestamp_utc, p.pivot_kind, p.observed_price) for p in after.pivots}
        self.assertTrue(all((p.timestamp_utc, p.pivot_kind, p.observed_price) in by_identity for p in confirmed_before))

    def test_all_complete_window_pivots_are_geometry_confirmed(self):
        result = discover_geometric_pivots(request())
        self.assertTrue(result.pivots)
        self.assertTrue(all(p.state is GeometricPivotState.CONFIRMED_BY_GEOMETRY for p in result.pivots))

    def test_provenance_is_carried_to_each_pivot(self):
        source = observations([2, 5, 3])
        result = discover_geometric_pivots(request(source))
        pivot = result.pivots[0]
        self.assertIn("test:caller-configured", pivot.provenance_refs)
        self.assertIn(f"input_source_sha256:{source.provenance.source_sha256}", pivot.provenance_refs)
        self.assertTrue(any(item.startswith("source_record_index:") for item in pivot.provenance_refs))

    def test_configuration_is_required_exact_and_bounded(self):
        bad = (0, -1, True, 10001, 1.5, "2")
        for field in ("left_window_bars", "right_window_bars"):
            for value in bad:
                with self.subTest(field=field, value=value):
                    with self.assertRaises(GeometricPivotDiscoveryError):
                        config(**{field: value})
        with self.assertRaises(GeometricPivotDiscoveryError):
            config(equal_extreme_policy="FIRST")
        with self.assertRaises(GeometricPivotDiscoveryError):
            config(include_developing=1)

    def test_mapping_duck_and_subclassed_requests_fail_closed(self):
        valid = request()
        for value in ({"request_id": "geometry-test"}, object()):
            with self.subTest(value=type(value).__name__):
                with self.assertRaises(GeometricPivotDiscoveryError):
                    discover_geometric_pivots(value)
        with self.assertRaises(GeometricPivotDiscoveryError):
            SubclassedRequest(
                valid.request_id,
                valid.observations,
                valid.config,
                valid.provenance_refs,
            )

    def test_low_level_mutation_is_revalidated(self):
        value = request()
        object.__setattr__(value.config, "left_window_bars", 0)
        with self.assertRaises(GeometricPivotDiscoveryError):
            discover_geometric_pivots(value)

    def test_malformed_duplicate_timestamp_and_nonfinite_input_rejected(self):
        duplicate = observations([1, 2], timestamps=[datetime(2024, 1, 1, tzinfo=timezone.utc)] * 2)
        with self.assertRaises(GeometricPivotDiscoveryError):
            discover_geometric_pivots(request(duplicate))
        bad = observations([1, 2, 3])
        object.__setattr__(bad.bars[1], "high", math.inf)
        with self.assertRaises(GeometricPivotDiscoveryError):
            discover_geometric_pivots(request(bad))

    def test_objects_are_immutable_and_authority_cannot_be_enabled(self):
        result = discover_geometric_pivots(request(observations([2, 5, 3])))
        with self.assertRaises(FrozenInstanceError):
            result.pivots[0].observed_price = 99
        pivot = result.pivots[0]
        with self.assertRaises(GeometricPivotDiscoveryError):
            GeometricPivotObservation(
                pivot.pivot_id, pivot.timestamp_utc, pivot.observed_price,
                pivot.pivot_kind, pivot.discovery_method, pivot.discovery_parameters,
                pivot.state, pivot.provenance_refs, True,
            )

    def test_yahoo_normalized_contract_feeds_without_provider_dependency(self):
        source = observations([2, 5, 3])
        object.__setattr__(source.provenance, "source_type", "yahoo_finance_chart_api")
        result = discover_geometric_pivots(request(source))
        self.assertIs(NormalizedMarketObservations, type(result.input_observations))
        source_text = (support.SRC / "elliott_runtime" / "market_data" / "geometric_pivots.py").read_text(encoding="utf-8")
        self.assertNotIn("import yahoo", source_text.lower())
        self.assertNotIn("from .yahoo", source_text.lower())

    def test_no_methodology_candidate_indicator_or_trading_capability(self):
        path = support.SRC / "elliott_runtime" / "market_data" / "geometric_pivots.py"
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = {
            node.module for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        }
        self.assertTrue({"requests", "subprocess", "socket", "urllib"}.isdisjoint(imports))
        for forbidden in (
            "wave label", "candidate family", "degree inference", "pattern inference",
            "RSI", "MACD", "EWO", "Fibonacci", "PREFERRED", "ALTERNATIVE",
            "certify_structural", "certify_validated", "forecast", "trade decision",
        ):
            self.assertNotIn(forbidden, source)

    def test_methodology_and_certificate_inventories_remain_unchanged(self):
        observed = set()
        root = support.SRC / "elliott_methodology_kernel"
        for path in root.glob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, (ast.Assign, ast.AnnAssign)):
                    targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
                    if any(isinstance(item, ast.Name) and item.id.endswith(("BEHAVIOR_ID", "BEHAVIOR")) for item in targets) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        observed.add(node.value.value)
        self.assertEqual(10, len(observed))
        self.assertEqual(7, len(structural_private._PRODUCERS))
        self.assertEqual(0, len(family_private._PRODUCERS))
        self.assertEqual(0, len(family_private._ISSUED))


if __name__ == "__main__":
    unittest.main()
