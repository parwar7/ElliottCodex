"""Deterministic CSV/JSON OHLCV ingestion without analytical heuristics."""

from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping

from elliott_methodology_kernel.contracts import (
    Bar,
    BarProvenance,
    DataProvenance,
    DataQualityReport,
    MissingBarInterval,
    NormalizedMarketObservations,
    SymbolIdentity,
    Timeframe,
)


class MarketDataError(ValueError):
    pass


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _timestamp(value: Any) -> tuple[datetime, bool]:
    if not isinstance(value, str) or not value.strip():
        raise MarketDataError("timestamp must be a non-empty ISO-8601 string")
    candidate = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise MarketDataError(f"invalid timestamp {value!r}") from exc
    naive_timezone_assumed_utc = parsed.tzinfo is None
    if naive_timezone_assumed_utc:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc), naive_timezone_assumed_utc


def _number(value: Any, field: str, *, optional: bool = False) -> float | None:
    if optional and (value is None or value == ""):
        return None
    if isinstance(value, bool):
        raise MarketDataError(f"{field} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise MarketDataError(f"{field} must be numeric") from exc
    if not math.isfinite(result):
        raise MarketDataError(f"{field} must be finite")
    return result


def _bar(record: Mapping[str, Any], index: int) -> Bar:
    missing = [name for name in ("timestamp", "open", "high", "low", "close") if name not in record]
    if missing:
        raise MarketDataError(f"record {index} missing fields: {', '.join(missing)}")
    timestamp, naive_timezone_assumed_utc = _timestamp(record["timestamp"])
    opening = _number(record["open"], "open")
    high = _number(record["high"], "high")
    low = _number(record["low"], "low")
    close = _number(record["close"], "close")
    volume = _number(record.get("volume"), "volume", optional=True)
    assert opening is not None and high is not None and low is not None and close is not None
    if high < max(opening, low, close):
        raise MarketDataError(f"record {index} high is below an OHLC value")
    if low > min(opening, high, close):
        raise MarketDataError(f"record {index} low is above an OHLC value")
    if volume is not None and volume < 0:
        raise MarketDataError(f"record {index} volume cannot be negative")
    return Bar(
        timestamp_utc=timestamp,
        open=opening,
        high=high,
        low=low,
        close=close,
        volume=volume,
        provenance=BarProvenance(
            source_record_index=index,
            source_timestamp=str(record["timestamp"]),
            naive_timezone_assumed_utc=naive_timezone_assumed_utc,
        ),
    )


def _normalize(
    records: Iterable[Mapping[str, Any]],
    raw_data: bytes,
    source_type: str,
    source_identifier: str,
    symbol: SymbolIdentity,
    timeframe: Timeframe,
) -> NormalizedMarketObservations:
    bars = sorted(
        (_bar(record, index) for index, record in enumerate(records, start=1)),
        key=lambda item: item.timestamp_utc,
    )
    if not bars:
        raise MarketDataError("market-data input contains no bars")

    seen: set[datetime] = set()
    duplicate_values: set[str] = set()
    for bar in bars:
        if bar.timestamp_utc in seen:
            duplicate_values.add(bar.timestamp_utc.isoformat())
        seen.add(bar.timestamp_utc)

    unique_times = sorted(seen)
    missing_intervals: list[MissingBarInterval] = []
    for previous, current in zip(unique_times, unique_times[1:]):
        elapsed = int((current - previous).total_seconds())
        missing_count = max(0, elapsed // timeframe.resolution_seconds - 1)
        if missing_count:
            missing_intervals.append(
                MissingBarInterval(
                    after_timestamp_utc=previous.isoformat(),
                    before_timestamp_utc=current.isoformat(),
                    missing_bar_count=missing_count,
                )
            )

    volumes = [bar.volume for bar in bars]
    quality = DataQualityReport(
        duplicate_timestamps_utc=tuple(sorted(duplicate_values)),
        missing_intervals=tuple(missing_intervals),
        volume_available=any(value is not None for value in volumes),
        volume_complete=all(value is not None for value in volumes),
    )
    provenance = DataProvenance(
        source_type=source_type,
        source_identifier=source_identifier,
        source_sha256=_sha256(raw_data),
        source_resolution=timeframe,
        ingested_at_utc=datetime.now(timezone.utc).isoformat(),
        resampled=False,
    )
    return NormalizedMarketObservations(
        symbol=symbol,
        timeframe=timeframe,
        bars=tuple(bars),
        provenance=provenance,
        quality=quality,
    )


def load_csv(
    path: str | Path,
    symbol: SymbolIdentity,
    timeframe: Timeframe,
) -> NormalizedMarketObservations:
    source = Path(path).resolve(strict=True)
    raw = source.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise MarketDataError("CSV must be UTF-8 encoded") from exc
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise MarketDataError("CSV header is missing")
    return _normalize(reader, raw, "csv", str(source), symbol, timeframe)


def load_json(
    path: str | Path,
    symbol: SymbolIdentity,
    timeframe: Timeframe,
) -> NormalizedMarketObservations:
    source = Path(path).resolve(strict=True)
    raw = source.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MarketDataError("JSON must be valid UTF-8 JSON") from exc
    records = payload.get("bars") if isinstance(payload, dict) else payload
    if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
        raise MarketDataError("JSON must be an array of bar objects or an object with a bars array")
    return _normalize(records, raw, "json", str(source), symbol, timeframe)
