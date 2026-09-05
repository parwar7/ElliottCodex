import ast
import copy
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
import json
import math
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import support
import elliott_methodology_kernel._structural_invalidity_certification as structural_private
import elliott_methodology_kernel._validated_internal_family_certification as family_private
from elliott_methodology_kernel import MethodologyKernel
from elliott_methodology_kernel.models import (
    AnalysisRequest,
    KernelStatus,
    MarketType,
    NormalizedMarketObservations,
)
import elliott_runtime.market_data.yahoo as yahoo_module
from elliott_runtime.market_data.yahoo import (
    RAW_PRICE_POLICY,
    TIMEFRAME_IS_NOT_DEGREE,
    YahooFinanceProvider,
    YahooFinanceProviderError,
    YahooHistoricalDataRequest,
    YahooHistoricalDataResult,
    YahooInterval,
    YahooProviderErrorCode,
    YahooProviderWarning,
)


START = datetime(2024, 1, 1, tzinfo=timezone.utc)
END = datetime(2024, 1, 3, tzinfo=timezone.utc)


def request(interval=YahooInterval.DAILY, **changes):
    values = {
        "symbol": "NVDA",
        "market_type": MarketType.STOCK,
        "interval": interval,
        "start_time_utc": START,
        "end_time_utc": END,
        "include_prepost": False,
        "exchange": "NASDAQ",
    }
    values.update(changes)
    return YahooHistoricalDataRequest(**values)


def payload(
    *,
    timestamps=None,
    opening=None,
    high=None,
    low=None,
    close=None,
    volume=None,
):
    timestamps = [1704067200, 1704153600] if timestamps is None else timestamps
    count = len(timestamps)
    quote = {
        "open": [100.0, 101.0][:count] if opening is None else opening,
        "high": [102.0, 103.0][:count] if high is None else high,
        "low": [99.0, 100.0][:count] if low is None else low,
        "close": [101.0, 102.0][:count] if close is None else close,
        "volume": [1000, 1100][:count] if volume is None else volume,
    }
    return {
        "chart": {
            "result": [
                {
                    "meta": {
                        "currency": "USD",
                        "exchangeName": "NMS",
                        "instrumentType": "EQUITY",
                        "exchangeTimezoneName": "America/New_York",
                        "gmtoffset": -18000,
                    },
                    "timestamp": timestamps,
                    "indicators": {"quote": [quote]},
                }
            ],
            "error": None,
        }
    }


class FakeResponse:
    def __init__(self, value):
        self.raw = value if type(value) is bytes else json.dumps(value).encode("utf-8")
        self.read_limit = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self, limit):
        self.read_limit = limit
        return self.raw


def fetch(value, provider=None, requested=None):
    response = FakeResponse(value)
    with patch.object(yahoo_module, "urlopen", return_value=response) as opened:
        result = (provider or YahooFinanceProvider()).fetch(requested or request())
    return result, response, opened


class YahooMarketDataProviderTests(unittest.TestCase):
    def test_classification_and_timeframe_is_not_degree(self) -> None:
        self.assertEqual("PROJECT_DATA_INFRASTRUCTURE", yahoo_module.ARTIFACT_CLASSIFICATION)
        self.assertEqual("UNTRUSTED_EXTERNAL_MARKET_DATA", yahoo_module.EXTERNAL_DATA_CLASSIFICATION)
        self.assertEqual("NORMALIZED_MARKET_OBSERVATIONS", yahoo_module.NORMALIZED_OUTPUT_CLASSIFICATION)
        self.assertEqual("DATA_PROVENANCE", yahoo_module.PROVENANCE_CLASSIFICATION)
        self.assertIs(True, TIMEFRAME_IS_NOT_DEGREE)

    def test_valid_nvda_request_is_exact_immutable_and_utc(self) -> None:
        value = request()
        self.assertEqual("NVDA", value.symbol)
        self.assertIs(MarketType.STOCK, value.market_type)
        self.assertIs(YahooInterval.DAILY, value.interval)
        self.assertEqual(timedelta(0), value.start_time_utc.utcoffset())
        with self.assertRaises(FrozenInstanceError):
            value.symbol = "AMD"

    def test_invalid_symbols_fail_closed_without_rewriting(self) -> None:
        for symbol in ("", " NVDA", "NVDA ", "NVDA?x=1", "NVDA/USD", 7):
            with self.subTest(symbol=symbol):
                with self.assertRaises(YahooFinanceProviderError) as raised:
                    request(symbol=symbol)
                self.assertIs(YahooProviderErrorCode.YAHOO_INVALID_RESPONSE, raised.exception.code)

    def test_invalid_and_4h_intervals_are_explicitly_unsupported(self) -> None:
        for interval in ("4h", "1m", object()):
            with self.subTest(interval=interval):
                with self.assertRaises(YahooFinanceProviderError) as raised:
                    request(interval=interval)
                self.assertIs(YahooProviderErrorCode.YAHOO_UNSUPPORTED_INTERVAL, raised.exception.code)

    def test_invalid_time_range_and_non_utc_datetimes_are_rejected(self) -> None:
        cases = (
            {"start_time_utc": END, "end_time_utc": START},
            {"start_time_utc": START, "end_time_utc": START},
            {"start_time_utc": datetime(2024, 1, 1)},
            {"start_time_utc": datetime(2024, 1, 1, tzinfo=timezone(timedelta(hours=1)))},
        )
        for changes in cases:
            with self.subTest(changes=changes):
                with self.assertRaises(YahooFinanceProviderError):
                    request(**changes)

    def test_url_query_is_deterministic_bounded_and_raw_ohlc_only(self) -> None:
        result, response, opened = fetch(payload())
        call = opened.call_args
        built_request = call.args[0]
        self.assertIn("/NVDA?period1=1704067200&period2=1704240000&interval=1d", built_request.full_url)
        self.assertIn("includePrePost=false", built_request.full_url)
        self.assertIn("includeAdjustedClose=false", built_request.full_url)
        self.assertEqual(30.0, call.kwargs["timeout"])
        self.assertEqual(64 * 1024 * 1024 + 1, response.read_limit)
        self.assertEqual(RAW_PRICE_POLICY, result.provider_metadata.raw_price_policy)

    def test_valid_payload_normalizes_exact_ohlcv_and_symbol_identity(self) -> None:
        result, _, _ = fetch(payload())
        self.assertIs(YahooHistoricalDataResult, type(result))
        self.assertIs(NormalizedMarketObservations, type(result.normalized_observations))
        bars = result.normalized_observations.bars
        self.assertEqual(2, len(bars))
        self.assertEqual((100.0, 102.0, 99.0, 101.0, 1000.0), (bars[0].open, bars[0].high, bars[0].low, bars[0].close, bars[0].volume))
        identity = result.normalized_observations.symbol
        self.assertEqual(("NVDA", MarketType.STOCK, "NASDAQ", "NVDA"), (identity.symbol, identity.market_type, identity.exchange, identity.provider_symbol))

    def test_missing_chart_result_and_malformed_json_fail_closed(self) -> None:
        cases = (
            b"not-json",
            {},
            {"chart": {}},
            {"chart": {"result": "wrong", "error": None}},
        )
        for value in cases:
            with self.subTest(value=value):
                with self.assertRaises(YahooFinanceProviderError) as raised:
                    fetch(value)
                self.assertIs(YahooProviderErrorCode.YAHOO_INVALID_RESPONSE, raised.exception.code)

    def test_empty_result_and_no_complete_rows_are_explicit(self) -> None:
        cases = (
            {"chart": {"result": [], "error": None}},
            {"chart": {"result": None, "error": {"code": "Not Found"}}},
            payload(opening=[None, None]),
        )
        for value in cases:
            with self.subTest(value=value):
                with self.assertRaises(YahooFinanceProviderError) as raised:
                    fetch(value)
                self.assertIs(YahooProviderErrorCode.YAHOO_EMPTY_RESULT, raised.exception.code)

    def test_array_length_and_timezone_metadata_mismatches_are_rejected(self) -> None:
        bad_length = payload(opening=[100.0])
        missing_timezone = payload()
        del missing_timezone["chart"]["result"][0]["meta"]["exchangeTimezoneName"]
        bad_offset = payload()
        bad_offset["chart"]["result"][0]["meta"]["gmtoffset"] = "-18000"
        for value in (bad_length, missing_timezone, bad_offset):
            with self.subTest(value=value):
                with self.assertRaises(YahooFinanceProviderError) as raised:
                    fetch(value)
                self.assertIs(YahooProviderErrorCode.YAHOO_INVALID_RESPONSE, raised.exception.code)

    def test_malformed_non_null_numeric_values_fail_closed(self) -> None:
        for opening in (["100", 101.0], [True, 101.0], [math.inf, 101.0]):
            with self.subTest(opening=opening):
                with self.assertRaises(YahooFinanceProviderError) as raised:
                    fetch(payload(opening=opening))
                self.assertIs(YahooProviderErrorCode.YAHOO_INVALID_RESPONSE, raised.exception.code)

    def test_null_ohlc_rows_are_dropped_counted_and_never_interpolated(self) -> None:
        value = payload(
            timestamps=[1704067200, 1704153600, 1704240000],
            opening=[100.0, None, 120.0],
            high=[102.0, None, 122.0],
            low=[99.0, None, 119.0],
            close=[101.0, None, 121.0],
            volume=[1000, 1050, 1200],
        )
        result, _, _ = fetch(value)
        self.assertEqual(3, result.provider_metadata.raw_row_count)
        self.assertEqual(2, result.provider_metadata.normalized_bar_count)
        self.assertEqual((1,), result.provider_metadata.dropped_null_ohlc_row_indices)
        self.assertEqual([100.0, 120.0], [bar.open for bar in result.normalized_observations.bars])
        self.assertIn(YahooProviderWarning.YAHOO_NULL_OHLC_ROWS_DROPPED, result.warnings)

    def test_out_of_order_rows_are_explicitly_sorted_by_existing_normalizer(self) -> None:
        value = payload(
            timestamps=[1704153600, 1704067200],
            opening=[101.0, 100.0],
            high=[103.0, 102.0],
            low=[100.0, 99.0],
            close=[102.0, 101.0],
        )
        result, _, _ = fetch(value)
        self.assertEqual(1, result.provider_metadata.out_of_order_pair_count)
        self.assertLess(result.normalized_observations.bars[0].timestamp_utc, result.normalized_observations.bars[1].timestamp_utc)
        self.assertIn(YahooProviderWarning.YAHOO_OUT_OF_ORDER_ROWS_SORTED_BY_NORMALIZER, result.warnings)

    def test_duplicate_timestamps_are_retained_and_reported(self) -> None:
        result, _, _ = fetch(payload(timestamps=[1704067200, 1704067200]))
        self.assertEqual(2, len(result.normalized_observations.bars))
        self.assertEqual(("2024-01-01T00:00:00+00:00",), result.normalized_observations.quality.duplicate_timestamps_utc)
        self.assertIn(YahooProviderWarning.YAHOO_DUPLICATE_TIMESTAMPS_RETAINED, result.warnings)

    def test_missing_volume_is_metadata_only(self) -> None:
        result, _, _ = fetch(payload(volume=[None, 1100]))
        self.assertEqual(1, result.provider_metadata.missing_volume_row_count)
        self.assertTrue(result.normalized_observations.quality.volume_available)
        self.assertFalse(result.normalized_observations.quality.volume_complete)
        self.assertIn(YahooProviderWarning.YAHOO_MISSING_VOLUME_ROWS, result.warnings)

    def test_supported_intervals_map_to_existing_timeframes(self) -> None:
        expected = {
            YahooInterval.MONTHLY: ("1mo", 2592000),
            YahooInterval.WEEKLY: ("1wk", 604800),
            YahooInterval.DAILY: ("1d", 86400),
            YahooInterval.HOURLY: ("1h", 3600),
            YahooInterval.FIFTEEN_MINUTE: ("15m", 900),
        }
        for interval, expected_timeframe in expected.items():
            with self.subTest(interval=interval):
                result, _, _ = fetch(payload(), requested=request(interval))
                timeframe = result.normalized_observations.timeframe
                self.assertEqual(expected_timeframe, (timeframe.label, timeframe.resolution_seconds))
                self.assertFalse(result.normalized_observations.provenance.resampled)

    def test_intraday_retention_warning_is_transport_only(self) -> None:
        for interval in (YahooInterval.HOURLY, YahooInterval.FIFTEEN_MINUTE):
            result, _, _ = fetch(payload(), requested=request(interval))
            self.assertIn(YahooProviderWarning.YAHOO_INTRADAY_RETENTION_LIMIT, result.warnings)
        for interval in (YahooInterval.MONTHLY, YahooInterval.WEEKLY, YahooInterval.DAILY):
            result, _, _ = fetch(payload(), requested=request(interval))
            self.assertNotIn(YahooProviderWarning.YAHOO_INTRADAY_RETENTION_LIMIT, result.warnings)

    def test_provenance_and_coverage_are_exact_and_resampled_false(self) -> None:
        result, _, _ = fetch(payload())
        observations = result.normalized_observations
        self.assertEqual("yahoo_finance_chart_api", observations.provenance.source_type)
        self.assertEqual(result.provider_metadata.requested_url, observations.provenance.source_identifier)
        self.assertEqual(result.provider_metadata.response_sha256, observations.provenance.source_sha256)
        self.assertFalse(observations.provenance.resampled)
        self.assertEqual("2024-01-01T00:00:00+00:00", result.provider_metadata.first_timestamp_utc)
        self.assertEqual("2024-01-02T00:00:00+00:00", result.provider_metadata.last_timestamp_utc)

    def test_http_network_and_response_size_errors_are_bounded(self) -> None:
        http_error = HTTPError("https://example.invalid", 429, "rate", {}, None)
        for error, code in (
            (http_error, YahooProviderErrorCode.YAHOO_HTTP_ERROR),
            (URLError("offline"), YahooProviderErrorCode.YAHOO_NETWORK_ERROR),
        ):
            with self.subTest(code=code):
                with patch.object(yahoo_module, "urlopen", side_effect=error):
                    with self.assertRaises(YahooFinanceProviderError) as raised:
                        YahooFinanceProvider().fetch(request())
                self.assertIs(code, raised.exception.code)
        oversized = FakeResponse(b"x" * (64 * 1024 * 1024 + 1))
        with patch.object(yahoo_module, "urlopen", return_value=oversized):
            with self.assertRaises(YahooFinanceProviderError) as raised:
                YahooFinanceProvider().fetch(request())
        self.assertIs(YahooProviderErrorCode.YAHOO_INVALID_RESPONSE, raised.exception.code)

    def test_timeout_is_positive_finite_and_bounded(self) -> None:
        for value in (0, -1, math.inf, True, 121, "30"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    YahooFinanceProvider(value)

    def test_exact_request_required_and_low_level_mutation_fails_closed(self) -> None:
        provider = YahooFinanceProvider()
        for value in ({"symbol": "NVDA"}, object()):
            with self.subTest(value=value):
                with self.assertRaises(YahooFinanceProviderError):
                    provider.fetch(value)
        changed = request()
        object.__setattr__(changed, "interval", "1d")
        with self.assertRaises(YahooFinanceProviderError):
            provider.fetch(changed)

    def test_module_has_no_interpretation_shell_eval_exec_or_dynamic_import(self) -> None:
        source = (support.SRC / "elliott_runtime" / "market_data" / "yahoo.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported = set()
        calls = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add("." * node.level + (node.module or ""))
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                calls.add(node.func.id)
        self.assertTrue({"subprocess", "importlib", "requests", "yfinance"}.isdisjoint(imported))
        self.assertTrue({"eval", "exec", "compile", "__import__"}.isdisjoint(calls))
        for forbidden in (
            "pivot detection", "wave detection", "degree inference", "pattern inference",
            "RSI", "MACD", "EWO", "Fibonacci", "PREFERRED", "ALTERNATIVE",
            "TRADE", "WAIT", "STAND_ASIDE", "target", "invalidation",
        ):
            self.assertNotIn(forbidden, source)

    def test_methodology_and_registries_remain_exact(self) -> None:
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

    def test_legacy_analyze_remains_not_implemented(self) -> None:
        observations = fetch(payload())[0].normalized_observations
        result = MethodologyKernel(support.PROTECTED_ROOT).analyze(
            AnalysisRequest(observations, "2026-09-03T00:00:00Z", "legacy")
        )
        self.assertIs(KernelStatus.NOT_IMPLEMENTED, result.status)


if __name__ == "__main__":
    unittest.main()
