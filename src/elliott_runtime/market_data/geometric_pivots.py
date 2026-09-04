"""Caller-configured geometric extrema with no Elliott endpoint authority.

This module is project data-analysis infrastructure.  It compares observed
OHLC bars; it does not infer waves, patterns, degrees, candidates, or trading
meaning.  Window sizes and tie handling are supplied by the caller and are
not protected methodology.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
import math

from elliott_methodology_kernel.contracts import (
    Bar,
    BarProvenance,
    DataProvenance,
    DataQualityReport,
    NormalizedMarketObservations,
    SymbolIdentity,
    Timeframe,
)


ARTIFACT_CLASSIFICATION = "PROJECT_DATA_ANALYSIS_INFRASTRUCTURE"
PARAMETER_CLASSIFICATION = "CALLER_SUPPLIED_GEOMETRY_PARAMETER"
TIMEFRAME_IS_NOT_DEGREE = True
ELLIOTT_ENDPOINT_AUTHORITY = False
_MAX_WINDOW_BARS = 10_000


class GeometricPivotDiscoveryError(ValueError):
    """Fail-closed input or configuration rejection."""


class GeometricPivotKind(StrEnum):
    HIGH = "HIGH"
    LOW = "LOW"


class GeometricPivotState(StrEnum):
    CONFIRMED_BY_GEOMETRY = "CONFIRMED_BY_GEOMETRY"
    DEVELOPING = "DEVELOPING"


class GeometricPivotDiscoveryMethod(StrEnum):
    WINDOWED_LOCAL_EXTREMA = "WINDOWED_LOCAL_EXTREMA"


class EqualExtremePolicy(StrEnum):
    FIRST = "FIRST"
    LAST = "LAST"


@dataclass(frozen=True, slots=True)
class GeometricPivotDiscoveryConfig:
    method: GeometricPivotDiscoveryMethod
    left_window_bars: int
    right_window_bars: int
    equal_extreme_policy: EqualExtremePolicy
    include_developing: bool

    def __post_init__(self) -> None:
        _validate_config(self)


@dataclass(frozen=True, slots=True)
class GeometricPivotDiscoveryRequest:
    request_id: str
    observations: NormalizedMarketObservations
    config: GeometricPivotDiscoveryConfig
    provenance_refs: tuple[str, ...]
    scoped_bars: tuple[Bar, ...] | None = None

    def __post_init__(self) -> None:
        _validate_request(self)


@dataclass(frozen=True, slots=True)
class GeometricPivotObservation:
    pivot_id: str
    timestamp_utc: datetime
    observed_price: float
    pivot_kind: GeometricPivotKind
    discovery_method: GeometricPivotDiscoveryMethod
    discovery_parameters: GeometricPivotDiscoveryConfig
    state: GeometricPivotState
    provenance_refs: tuple[str, ...]
    elliott_endpoint_authority: bool = False

    def __post_init__(self) -> None:
        if self.elliott_endpoint_authority is not False:
            raise GeometricPivotDiscoveryError(
                "A geometric pivot can never carry Elliott endpoint authority."
            )


@dataclass(frozen=True, slots=True)
class GeometricPivotDiscoveryResult:
    request_id: str
    input_observations: NormalizedMarketObservations
    pivots: tuple[GeometricPivotObservation, ...]
    config: GeometricPivotDiscoveryConfig
    diagnostics: tuple[str, ...]
    provenance_refs: tuple[str, ...]
    scoped_bars: tuple[Bar, ...] | None = None


def _fail(message: str) -> None:
    raise GeometricPivotDiscoveryError(message)


def _refs(value: object, name: str) -> tuple[str, ...]:
    if type(value) is not tuple:
        _fail(f"{name} must be one exact tuple of non-blank strings.")
    if any(type(item) is not str or item.strip() == "" for item in value):
        _fail(f"{name} must contain only exact non-blank strings.")
    return value


def _validate_config(config: object) -> GeometricPivotDiscoveryConfig:
    if type(config) is not GeometricPivotDiscoveryConfig:
        _fail("config must be one exact GeometricPivotDiscoveryConfig.")
    if type(config.method) is not GeometricPivotDiscoveryMethod:
        _fail("method must be one exact GeometricPivotDiscoveryMethod.")
    if config.method is not GeometricPivotDiscoveryMethod.WINDOWED_LOCAL_EXTREMA:
        _fail("Only WINDOWED_LOCAL_EXTREMA is supported in V1.")
    for name, value in (
        ("left_window_bars", config.left_window_bars),
        ("right_window_bars", config.right_window_bars),
    ):
        if type(value) is not int or value < 1 or value > _MAX_WINDOW_BARS:
            _fail(f"{name} must be an exact integer within [1, {_MAX_WINDOW_BARS}].")
    if type(config.equal_extreme_policy) is not EqualExtremePolicy:
        _fail("equal_extreme_policy must be one exact EqualExtremePolicy.")
    if type(config.include_developing) is not bool:
        _fail("include_developing must be one exact bool.")
    return config


def _validate_number(value: object, name: str, *, optional: bool = False) -> None:
    if optional and value is None:
        return
    if type(value) not in (int, float) or not math.isfinite(value):
        _fail(f"{name} must be one finite number.")


def _validate_observations(value: object) -> NormalizedMarketObservations:
    if type(value) is not NormalizedMarketObservations:
        _fail("observations must be one exact NormalizedMarketObservations.")
    if type(value.symbol) is not SymbolIdentity or type(value.timeframe) is not Timeframe:
        _fail("observations must contain exact symbol and timeframe contracts.")
    if type(value.provenance) is not DataProvenance or type(value.quality) is not DataQualityReport:
        _fail("observations must contain exact provenance and quality contracts.")
    if type(value.bars) is not tuple or not value.bars:
        _fail("observations.bars must be one non-empty exact tuple.")
    previous: datetime | None = None
    for index, bar in enumerate(value.bars):
        if type(bar) is not Bar or type(bar.provenance) is not BarProvenance:
            _fail(f"observations.bars[{index}] must be one exact Bar with exact provenance.")
        stamp = bar.timestamp_utc
        if type(stamp) is not datetime or stamp.tzinfo is None:
            _fail(f"observations.bars[{index}].timestamp_utc must be timezone-aware UTC.")
        offset = stamp.utcoffset()
        if offset is None or offset.total_seconds() != 0:
            _fail(f"observations.bars[{index}].timestamp_utc must use UTC.")
        if previous is not None and stamp <= previous:
            _fail("observations bars must have unique, strictly increasing timestamps.")
        previous = stamp
        for field in ("open", "high", "low", "close"):
            _validate_number(getattr(bar, field), f"bar[{index}].{field}")
        _validate_number(bar.volume, f"bar[{index}].volume", optional=True)
        if bar.high < max(bar.open, bar.low, bar.close):
            _fail(f"bar[{index}] high is below another OHLC value.")
        if bar.low > min(bar.open, bar.high, bar.close):
            _fail(f"bar[{index}] low is above another OHLC value.")
        if bar.volume is not None and bar.volume < 0:
            _fail(f"bar[{index}] volume cannot be negative.")
    return value


def _validate_request(value: object) -> GeometricPivotDiscoveryRequest:
    if type(value) is not GeometricPivotDiscoveryRequest:
        _fail("request must be one exact GeometricPivotDiscoveryRequest.")
    if type(value.request_id) is not str or value.request_id.strip() == "":
        _fail("request_id must be one exact non-blank string.")
    observations = _validate_observations(value.observations)
    _validate_config(value.config)
    _refs(value.provenance_refs, "provenance_refs")
    if value.scoped_bars is not None:
        if type(value.scoped_bars) is not tuple or not value.scoped_bars or any(
            type(bar) is not Bar for bar in value.scoped_bars
        ):
            _fail("scoped_bars must be None or one non-empty exact tuple of exact bars.")
        source_by_id = {id(bar): bar for bar in observations.bars}
        seen: set[int] = set()
        previous: datetime | None = None
        for bar in value.scoped_bars:
            if id(bar) not in source_by_id or source_by_id[id(bar)] is not bar:
                _fail("Every scoped bar must retain exact source-observation identity.")
            if id(bar) in seen:
                _fail("scoped_bars cannot repeat a bar identity.")
            if previous is not None and bar.timestamp_utc <= previous:
                _fail("scoped_bars must retain strict source chronology.")
            seen.add(id(bar))
            previous = bar.timestamp_utc
    return value


def _selected_index(
    values: list[int | float], *, high: bool, policy: EqualExtremePolicy
) -> int:
    extreme = max(values) if high else min(values)
    matching = [index for index, value in enumerate(values) if value == extreme]
    return matching[0] if policy is EqualExtremePolicy.FIRST else matching[-1]


def discover_geometric_pivots(
    request: GeometricPivotDiscoveryRequest,
) -> GeometricPivotDiscoveryResult:
    """Find bounded local extrema; output never has Elliott endpoint authority."""

    request = _validate_request(request)
    observations = request.observations
    config = request.config
    bars = observations.bars if request.scoped_bars is None else request.scoped_bars
    pivots: list[GeometricPivotObservation] = []
    ambiguous = 0

    for index in range(config.left_window_bars, len(bars)):
        full_right = index + config.right_window_bars < len(bars)
        if not full_right and not config.include_developing:
            continue
        end = index + config.right_window_bars + 1 if full_right else len(bars)
        start = index - config.left_window_bars
        window = bars[start:end]
        local_index = index - start
        highs = [bar.high for bar in window]
        lows = [bar.low for bar in window]
        high_selected = highs[local_index] == max(highs) and local_index == _selected_index(
            highs, high=True, policy=config.equal_extreme_policy
        )
        low_selected = lows[local_index] == min(lows) and local_index == _selected_index(
            lows, high=False, policy=config.equal_extreme_policy
        )
        if high_selected and low_selected:
            ambiguous += 1
            continue
        kind: GeometricPivotKind | None = None
        price: int | float | None = None
        if high_selected:
            kind = GeometricPivotKind.HIGH
            price = bars[index].high
        elif low_selected:
            kind = GeometricPivotKind.LOW
            price = bars[index].low
        if kind is None or price is None:
            continue
        state = (
            GeometricPivotState.CONFIRMED_BY_GEOMETRY
            if full_right
            else GeometricPivotState.DEVELOPING
        )
        bar = bars[index]
        pivot_refs = request.provenance_refs + (
            f"input_source_sha256:{observations.provenance.source_sha256}",
            f"source_record_index:{bar.provenance.source_record_index}",
            f"source_timestamp:{bar.provenance.source_timestamp}",
        )
        pivots.append(
            GeometricPivotObservation(
                pivot_id=f"{request.request_id}:{index}:{kind.value}",
                timestamp_utc=bar.timestamp_utc,
                observed_price=float(price),
                pivot_kind=kind,
                discovery_method=config.method,
                discovery_parameters=config,
                state=state,
                provenance_refs=pivot_refs,
                elliott_endpoint_authority=False,
            )
        )

    scope_diagnostics = (
        (
            f"SOURCE_DATASET_BAR_COUNT={len(observations.bars)}",
            "EXACT_BAR_SCOPE_APPLIED=True",
        )
        if request.scoped_bars is not None
        else ()
    )
    diagnostics = (
        f"INPUT_BAR_COUNT={len(bars)}",
        *scope_diagnostics,
        f"GEOMETRIC_PIVOT_COUNT={len(pivots)}",
        f"AMBIGUOUS_SAME_BAR_HIGH_LOW_EXCLUDED={ambiguous}",
        "GEOMETRIC_PIVOT_IS_NOT_ELLIOTT_WAVE_ENDPOINT",
        "TIMEFRAME_IS_NOT_DEGREE",
    )
    return GeometricPivotDiscoveryResult(
        request_id=request.request_id,
        input_observations=observations,
        pivots=tuple(pivots),
        config=config,
        diagnostics=diagnostics,
        provenance_refs=request.provenance_refs,
        scoped_bars=request.scoped_bars,
    )


__all__ = [
    "ARTIFACT_CLASSIFICATION",
    "ELLIOTT_ENDPOINT_AUTHORITY",
    "EqualExtremePolicy",
    "GeometricPivotDiscoveryConfig",
    "GeometricPivotDiscoveryError",
    "GeometricPivotDiscoveryMethod",
    "GeometricPivotDiscoveryRequest",
    "GeometricPivotDiscoveryResult",
    "GeometricPivotKind",
    "GeometricPivotObservation",
    "GeometricPivotState",
    "PARAMETER_CLASSIFICATION",
    "TIMEFRAME_IS_NOT_DEGREE",
    "discover_geometric_pivots",
]
