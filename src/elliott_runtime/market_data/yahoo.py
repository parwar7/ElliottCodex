"""Bounded Yahoo Finance chart transport into existing market-data models.

This module is PROJECT_DATA_INFRASTRUCTURE. Yahoo responses are untrusted
external market data and carry no Elliott methodology authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
import hashlib
import json
import math
import re
import socket
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from elliott_methodology_kernel.contracts import (
    MarketType,
    NormalizedMarketObservations,
    SymbolIdentity,
    Timeframe,
)

from .ingestion import MarketDataError, _normalize


ARTIFACT_CLASSIFICATION = "PROJECT_DATA_INFRASTRUCTURE"
EXTERNAL_DATA_CLASSIFICATION = "UNTRUSTED_EXTERNAL_MARKET_DATA"
NORMALIZED_OUTPUT_CLASSIFICATION = "NORMALIZED_MARKET_OBSERVATIONS"
PROVENANCE_CLASSIFICATION = "DATA_PROVENANCE"
TIMEFRAME_IS_NOT_DEGREE = True
RAW_PRICE_POLICY = "YAHOO_QUOTE_RAW_OHLC_NO_ADJCLOSE_MIXING"

_CHART_ENDPOINT = "https://query1.finance.yahoo.com/v8/finance/chart"
_DEFAULT_TIMEOUT_SECONDS = 30.0
_MAX_RESPONSE_BYTES = 64 * 1024 * 1024
_USER_AGENT = "ElliottCodex-YahooProvider/1.0"
_SAFE_SYMBOL = re.compile(r"[A-Za-z0-9.^=_-]+")


class YahooInterval(StrEnum):
    MONTHLY = "1mo"
    WEEKLY = "1wk"
    DAILY = "1d"
    HOURLY = "1h"
    FIFTEEN_MINUTE = "15m"


class YahooProviderErrorCode(StrEnum):
    YAHOO_NETWORK_ERROR = "YAHOO_NETWORK_ERROR"
    YAHOO_HTTP_ERROR = "YAHOO_HTTP_ERROR"
    YAHOO_INVALID_RESPONSE = "YAHOO_INVALID_RESPONSE"
    YAHOO_UNSUPPORTED_INTERVAL = "YAHOO_UNSUPPORTED_INTERVAL"
    YAHOO_EMPTY_RESULT = "YAHOO_EMPTY_RESULT"
    YAHOO_NORMALIZATION_ERROR = "YAHOO_NORMALIZATION_ERROR"


class YahooProviderWarning(StrEnum):
    YAHOO_INTRADAY_RETENTION_LIMIT = "YAHOO_INTRADAY_RETENTION_LIMIT"
    YAHOO_NULL_OHLC_ROWS_DROPPED = "YAHOO_NULL_OHLC_ROWS_DROPPED"
    YAHOO_MISSING_VOLUME_ROWS = "YAHOO_MISSING_VOLUME_ROWS"
    YAHOO_DUPLICATE_TIMESTAMPS_RETAINED = "YAHOO_DUPLICATE_TIMESTAMPS_RETAINED"
    YAHOO_OUT_OF_ORDER_ROWS_SORTED_BY_NORMALIZER = (
        "YAHOO_OUT_OF_ORDER_ROWS_SORTED_BY_NORMALIZER"
    )


class YahooFinanceProviderError(ValueError):
    """One provider-boundary failure, never a methodology state."""

    def __init__(self, code: YahooProviderErrorCode, message: str) -> None:
        self.code = code
        super().__init__(f"{code.value}: {message}")


_TIMEFRAMES = {
    YahooInterval.MONTHLY: Timeframe("1mo", 2_592_000),
    YahooInterval.WEEKLY: Timeframe("1wk", 604_800),
    YahooInterval.DAILY: Timeframe("1d", 86_400),
    YahooInterval.HOURLY: Timeframe("1h", 3_600),
    YahooInterval.FIFTEEN_MINUTE: Timeframe("15m", 900),
}


def _require_utc(value: object, name: str) -> datetime:
    if type(value) is not datetime or value.tzinfo is None:
        raise YahooFinanceProviderError(
            YahooProviderErrorCode.YAHOO_INVALID_RESPONSE,
            f"{name} must be one timezone-aware UTC datetime.",
        )
    offset = value.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise YahooFinanceProviderError(
            YahooProviderErrorCode.YAHOO_INVALID_RESPONSE,
            f"{name} must use UTC, not a local or non-zero-offset timezone.",
        )
    return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class YahooHistoricalDataRequest:
    symbol: str
    market_type: MarketType
    interval: YahooInterval
    start_time_utc: datetime
    end_time_utc: datetime
    include_prepost: bool = False
    exchange: str | None = None

    def __post_init__(self) -> None:
        if (
            type(self.symbol) is not str
            or self.symbol == ""
            or _SAFE_SYMBOL.fullmatch(self.symbol) is None
        ):
            raise YahooFinanceProviderError(
                YahooProviderErrorCode.YAHOO_INVALID_RESPONSE,
                "symbol must be an exact non-empty Yahoo symbol using safe characters.",
            )
        if type(self.market_type) is not MarketType:
            raise YahooFinanceProviderError(
                YahooProviderErrorCode.YAHOO_INVALID_RESPONSE,
                "market_type must use the existing exact MarketType.",
            )
        if type(self.interval) is not YahooInterval:
            raise YahooFinanceProviderError(
                YahooProviderErrorCode.YAHOO_UNSUPPORTED_INTERVAL,
                "interval must be one exact supported YahooInterval; 4h is not supported in V1.",
            )
        start = _require_utc(self.start_time_utc, "start_time_utc")
        end = _require_utc(self.end_time_utc, "end_time_utc")
        if start >= end:
            raise YahooFinanceProviderError(
                YahooProviderErrorCode.YAHOO_INVALID_RESPONSE,
                "start_time_utc must be earlier than end_time_utc.",
            )
        if type(self.include_prepost) is not bool:
            raise YahooFinanceProviderError(
                YahooProviderErrorCode.YAHOO_INVALID_RESPONSE,
                "include_prepost must be an exact bool.",
            )
        if self.exchange is not None and (
            type(self.exchange) is not str or self.exchange.strip() == ""
        ):
            raise YahooFinanceProviderError(
                YahooProviderErrorCode.YAHOO_INVALID_RESPONSE,
                "exchange must be None or an exact non-blank string.",
            )


@dataclass(frozen=True, slots=True)
class YahooProviderMetadata:
    provider: str
    provider_symbol: str
    requested_interval: YahooInterval
    requested_url: str
    exchange_name: str | None
    exchange_timezone_name: str
    exchange_gmt_offset_seconds: int
    currency: str | None
    instrument_type: str | None
    raw_price_policy: str
    raw_row_count: int
    normalized_bar_count: int
    dropped_null_ohlc_row_indices: tuple[int, ...]
    missing_volume_row_count: int
    out_of_order_pair_count: int
    first_timestamp_utc: str
    last_timestamp_utc: str
    response_sha256: str


@dataclass(frozen=True, slots=True)
class YahooHistoricalDataResult:
    normalized_observations: NormalizedMarketObservations
    provider_metadata: YahooProviderMetadata
    warnings: tuple[YahooProviderWarning, ...]


def _invalid(message: str) -> YahooFinanceProviderError:
    return YahooFinanceProviderError(
        YahooProviderErrorCode.YAHOO_INVALID_RESPONSE,
        message,
    )


def _exact_mapping(value: object, name: str) -> Mapping[str, Any]:
    if type(value) is not dict:
        raise _invalid(f"{name} must be a JSON object.")
    return value


def _metadata_text(meta: Mapping[str, Any], name: str) -> str | None:
    value = meta.get(name)
    if value is None:
        return None
    if type(value) is not str or value.strip() == "":
        raise _invalid(f"Yahoo metadata {name} must be a non-blank string when present.")
    return value


def _number(value: object, name: str) -> int | float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise _invalid(f"{name} must be one finite JSON number.")
    return value


def _url_for(request: YahooHistoricalDataRequest) -> str:
    query = urlencode(
        (
            ("period1", int(request.start_time_utc.timestamp())),
            ("period2", int(request.end_time_utc.timestamp())),
            ("interval", request.interval.value),
            ("includePrePost", "true" if request.include_prepost else "false"),
            ("events", "div,splits"),
            ("includeAdjustedClose", "false"),
        )
    )
    return f"{_CHART_ENDPOINT}/{quote(request.symbol, safe='')}?{query}"


def _read_bounded(response: Any) -> bytes:
    raw = response.read(_MAX_RESPONSE_BYTES + 1)
    if type(raw) is not bytes:
        raise _invalid("Yahoo HTTP response body must be bytes.")
    if len(raw) > _MAX_RESPONSE_BYTES:
        raise _invalid("Yahoo HTTP response exceeded the bounded response limit.")
    return raw


def _parse_payload(
    raw: bytes,
) -> tuple[Mapping[str, Any], list[int], Mapping[str, Any]]:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise _invalid("Yahoo response must be valid UTF-8 JSON.") from error
    root = _exact_mapping(payload, "Yahoo response")
    chart = _exact_mapping(root.get("chart"), "chart")
    result = chart.get("result")
    if result is None:
        provider_error = chart.get("error")
        if provider_error is not None:
            raise YahooFinanceProviderError(
                YahooProviderErrorCode.YAHOO_EMPTY_RESULT,
                "Yahoo returned no chart result.",
            )
        raise _invalid("chart.result is missing.")
    if type(result) is not list:
        raise _invalid("chart.result must be a JSON array.")
    if len(result) == 0:
        raise YahooFinanceProviderError(
            YahooProviderErrorCode.YAHOO_EMPTY_RESULT,
            "Yahoo returned an empty chart result.",
        )
    if len(result) != 1:
        raise _invalid("Yahoo chart response must contain exactly one result.")
    chart_result = _exact_mapping(result[0], "chart.result[0]")
    timestamps = chart_result.get("timestamp")
    if type(timestamps) is not list:
        raise _invalid("Yahoo timestamps must be a JSON array.")
    if not timestamps:
        raise YahooFinanceProviderError(
            YahooProviderErrorCode.YAHOO_EMPTY_RESULT,
            "Yahoo returned no timestamps.",
        )
    for index, stamp in enumerate(timestamps):
        if type(stamp) is not int:
            raise _invalid(f"timestamp[{index}] must be one integer epoch second.")
    indicators = _exact_mapping(chart_result.get("indicators"), "indicators")
    quotes = indicators.get("quote")
    if type(quotes) is not list or len(quotes) != 1:
        raise _invalid("indicators.quote must contain exactly one quote object.")
    quote_data = _exact_mapping(quotes[0], "indicators.quote[0]")
    meta = _exact_mapping(chart_result.get("meta"), "meta")
    return chart_result, timestamps, {"quote": quote_data, "meta": meta}


def _records(
    timestamps: list[int],
    quote_data: Mapping[str, Any],
) -> tuple[list[dict[str, object]], tuple[int, ...], int, int]:
    count = len(timestamps)
    arrays: dict[str, list[Any]] = {}
    for name in ("open", "high", "low", "close"):
        value = quote_data.get(name)
        if type(value) is not list or len(value) != count:
            raise _invalid(f"quote.{name} length must equal timestamp length.")
        arrays[name] = value
    volume = quote_data.get("volume")
    if volume is None:
        arrays["volume"] = [None] * count
    elif type(volume) is not list or len(volume) != count:
        raise _invalid("quote.volume length must equal timestamp length when present.")
    else:
        arrays["volume"] = volume

    records: list[dict[str, object]] = []
    dropped: list[int] = []
    missing_volume = 0
    out_of_order = sum(
        current < previous
        for previous, current in zip(timestamps, timestamps[1:])
    )
    for index, stamp in enumerate(timestamps):
        required = tuple(arrays[name][index] for name in ("open", "high", "low", "close"))
        if any(value is None for value in required):
            dropped.append(index)
            continue
        opening, high, low, close = (
            _number(value, f"quote row {index} OHLC") for value in required
        )
        volume_value = arrays["volume"][index]
        if volume_value is None:
            missing_volume += 1
        else:
            volume_value = _number(volume_value, f"quote.volume[{index}]")
        records.append(
            {
                "timestamp": datetime.fromtimestamp(stamp, timezone.utc).isoformat(),
                "open": opening,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume_value,
            }
        )
    if not records:
        raise YahooFinanceProviderError(
            YahooProviderErrorCode.YAHOO_EMPTY_RESULT,
            "Yahoo returned no rows with complete OHLC values.",
        )
    return records, tuple(dropped), missing_volume, out_of_order


class YahooFinanceProvider:
    """Fetch Yahoo chart data with one bounded HTTPS request and no retries."""

    def __init__(self, timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS) -> None:
        if (
            type(timeout_seconds) not in (int, float)
            or isinstance(timeout_seconds, bool)
            or not math.isfinite(timeout_seconds)
            or timeout_seconds <= 0
            or timeout_seconds > 120
        ):
            raise ValueError("timeout_seconds must be finite and within (0, 120].")
        self._timeout_seconds = float(timeout_seconds)

    def fetch(self, request: YahooHistoricalDataRequest) -> YahooHistoricalDataResult:
        if type(request) is not YahooHistoricalDataRequest:
            raise YahooFinanceProviderError(
                YahooProviderErrorCode.YAHOO_INVALID_RESPONSE,
                "fetch requires one exact YahooHistoricalDataRequest.",
            )
        request.__post_init__()
        url = _url_for(request)
        http_request = Request(
            url,
            headers={"Accept": "application/json", "User-Agent": _USER_AGENT},
            method="GET",
        )
        try:
            with urlopen(http_request, timeout=self._timeout_seconds) as response:
                raw = _read_bounded(response)
        except HTTPError as error:
            raise YahooFinanceProviderError(
                YahooProviderErrorCode.YAHOO_HTTP_ERROR,
                f"Yahoo returned HTTP {error.code}.",
            ) from error
        except (URLError, TimeoutError, socket.timeout, OSError) as error:
            raise YahooFinanceProviderError(
                YahooProviderErrorCode.YAHOO_NETWORK_ERROR,
                "Yahoo request failed at the network boundary.",
            ) from error

        _, timestamps, parsed = _parse_payload(raw)
        quote_data = parsed["quote"]
        meta = parsed["meta"]
        records, dropped, missing_volume, out_of_order = _records(
            timestamps, quote_data
        )

        timezone_name = _metadata_text(meta, "exchangeTimezoneName")
        if timezone_name is None:
            raise _invalid("Yahoo metadata exchangeTimezoneName is required.")
        gmt_offset = meta.get("gmtoffset")
        if type(gmt_offset) is not int:
            raise _invalid("Yahoo metadata gmtoffset must be an integer.")

        symbol_identity = SymbolIdentity(
            symbol=request.symbol,
            market_type=request.market_type,
            exchange=request.exchange,
            provider_symbol=request.symbol,
        )
        timeframe = _TIMEFRAMES[request.interval]
        try:
            observations = _normalize(
                records,
                raw,
                "yahoo_finance_chart_api",
                url,
                symbol_identity,
                timeframe,
            )
        except (MarketDataError, ValueError) as error:
            raise YahooFinanceProviderError(
                YahooProviderErrorCode.YAHOO_NORMALIZATION_ERROR,
                "Yahoo rows failed the existing market-data normalization contract.",
            ) from error

        warnings: list[YahooProviderWarning] = []
        if request.interval in (
            YahooInterval.HOURLY,
            YahooInterval.FIFTEEN_MINUTE,
        ):
            warnings.append(YahooProviderWarning.YAHOO_INTRADAY_RETENTION_LIMIT)
        if dropped:
            warnings.append(YahooProviderWarning.YAHOO_NULL_OHLC_ROWS_DROPPED)
        if missing_volume:
            warnings.append(YahooProviderWarning.YAHOO_MISSING_VOLUME_ROWS)
        if observations.quality.duplicate_timestamps_utc:
            warnings.append(
                YahooProviderWarning.YAHOO_DUPLICATE_TIMESTAMPS_RETAINED
            )
        if out_of_order:
            warnings.append(
                YahooProviderWarning.YAHOO_OUT_OF_ORDER_ROWS_SORTED_BY_NORMALIZER
            )

        metadata = YahooProviderMetadata(
            provider="YAHOO_FINANCE_CHART",
            provider_symbol=request.symbol,
            requested_interval=request.interval,
            requested_url=url,
            exchange_name=_metadata_text(meta, "exchangeName"),
            exchange_timezone_name=timezone_name,
            exchange_gmt_offset_seconds=gmt_offset,
            currency=_metadata_text(meta, "currency"),
            instrument_type=_metadata_text(meta, "instrumentType"),
            raw_price_policy=RAW_PRICE_POLICY,
            raw_row_count=len(timestamps),
            normalized_bar_count=len(observations.bars),
            dropped_null_ohlc_row_indices=dropped,
            missing_volume_row_count=missing_volume,
            out_of_order_pair_count=out_of_order,
            first_timestamp_utc=observations.bars[0].timestamp_utc.isoformat(),
            last_timestamp_utc=observations.bars[-1].timestamp_utc.isoformat(),
            response_sha256=hashlib.sha256(raw).hexdigest(),
        )
        return YahooHistoricalDataResult(observations, metadata, tuple(warnings))


__all__ = [
    "ARTIFACT_CLASSIFICATION",
    "EXTERNAL_DATA_CLASSIFICATION",
    "NORMALIZED_OUTPUT_CLASSIFICATION",
    "PROVENANCE_CLASSIFICATION",
    "RAW_PRICE_POLICY",
    "TIMEFRAME_IS_NOT_DEGREE",
    "YahooFinanceProvider",
    "YahooFinanceProviderError",
    "YahooHistoricalDataRequest",
    "YahooHistoricalDataResult",
    "YahooInterval",
    "YahooProviderErrorCode",
    "YahooProviderMetadata",
    "YahooProviderWarning",
]
