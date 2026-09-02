"""Typed transport models; no Elliott interpretation is implemented here."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
import re
from typing import Any, Mapping


class MarketType(StrEnum):
    STOCK = "stock"
    STOCK_INDEX = "stock_index"
    CURRENCY = "currency"
    COMMODITY = "commodity"
    CRYPTO = "crypto"
    FUTURES = "futures"
    OTHER = "other"


class CountRank(StrEnum):
    PREFERRED = "PREFERRED"
    ALTERNATIVE = "ALTERNATIVE"
    REMOTE = "REMOTE"


class DegreeStatus(StrEnum):
    RESOLVED = "RESOLVED"
    UNRESOLVED = "DEGREE_UNRESOLVED"


class InternalStatus(StrEnum):
    CONFIRMED = "INTERNALS_CONFIRMED"
    VIOLATED = "INTERNALS_VIOLATED"
    UNRESOLVED = "INTERNALS_UNRESOLVED"


class StructuralValidity(StrEnum):
    VALID = "VALID"
    INVALID = "INVALID"
    UNRESOLVED = "UNRESOLVED"


class RightLook(StrEnum):
    GOOD_FIT = "GOOD_FIT"
    ACCEPTABLE = "ACCEPTABLE"
    POOR_FIT = "POOR_FIT"
    UNRESOLVED = "UNRESOLVED"


class EvidenceState(StrEnum):
    SUPPORTS = "SUPPORTS"
    NEUTRAL = "NEUTRAL"
    ARGUES_AGAINST = "ARGUES_AGAINST"
    NOT_AVAILABLE = "NOT_AVAILABLE"


class SourceClassification(StrEnum):
    RULE = "SOURCE_RULE"
    DEFINITION = "SOURCE_DEFINITION"
    GUIDELINE = "SOURCE_GUIDELINE"
    OBSERVATION = "SOURCE_OBSERVATION"
    TRADING_PRACTICE = "SOURCE_TRADING_PRACTICE"
    UNRESOLVED_CONFLICT = "UNRESOLVED_CONFLICT"


class KernelStatus(StrEnum):
    COMPLETED = "COMPLETED"
    NOT_IMPLEMENTED = "NOT_IMPLEMENTED"


@dataclass(frozen=True, slots=True)
class SymbolIdentity:
    symbol: str
    market_type: MarketType
    exchange: str | None = None
    provider_symbol: str | None = None

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("Symbol cannot be empty.")


@dataclass(frozen=True, slots=True)
class Timeframe:
    label: str
    resolution_seconds: int

    def __post_init__(self) -> None:
        if not self.label.strip() or self.resolution_seconds <= 0:
            raise ValueError("Timeframe requires a label and positive resolution_seconds.")


@dataclass(frozen=True, slots=True)
class BarProvenance:
    source_record_index: int
    source_timestamp: str
    naive_timezone_assumed_utc: bool = False


@dataclass(frozen=True, slots=True)
class Bar:
    timestamp_utc: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None
    provenance: BarProvenance


@dataclass(frozen=True, slots=True)
class DataProvenance:
    source_type: str
    source_identifier: str
    source_sha256: str
    source_resolution: Timeframe
    ingested_at_utc: str
    resampled: bool = False
    parent_source_hashes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MissingBarInterval:
    after_timestamp_utc: str
    before_timestamp_utc: str
    missing_bar_count: int


@dataclass(frozen=True, slots=True)
class DataQualityReport:
    duplicate_timestamps_utc: tuple[str, ...] = ()
    missing_intervals: tuple[MissingBarInterval, ...] = ()
    volume_available: bool = False
    volume_complete: bool = False


@dataclass(frozen=True, slots=True)
class NormalizedMarketObservations:
    symbol: SymbolIdentity
    timeframe: Timeframe
    bars: tuple[Bar, ...]
    provenance: DataProvenance
    quality: DataQualityReport


@dataclass(frozen=True, slots=True)
class DegreeTreeNode:
    label: str
    degree: str | None
    degree_status: DegreeStatus
    internal_status: InternalStatus
    parent_label: str | None = None


@dataclass(frozen=True, slots=True)
class SourcePrincipleReference:
    principle_id: str
    protected_source_file: str
    classification: SourceClassification

    def __post_init__(self) -> None:
        if not re.fullmatch(r"P[0-9]{3}", self.principle_id):
            raise ValueError("Source principle ID must match P followed by three digits.")


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    category: str
    state: EvidenceState
    note: str
    source_principles: tuple[SourcePrincipleReference, ...] = ()


@dataclass(frozen=True, slots=True)
class ForecastContract:
    expected_next_structure: str
    confirmation: str
    downgrade_condition: str
    structural_invalidation: str
    alternative_promotion_trigger: str
    target_area: str | None = None


@dataclass(frozen=True, slots=True)
class CountRepresentation:
    rank: CountRank
    pattern: str
    current_position: str
    structural_validity: StructuralValidity
    internal_status: InternalStatus
    right_look: RightLook
    forecast: ForecastContract
    evidence: tuple[EvidenceRecord, ...] = ()


@dataclass(frozen=True, slots=True)
class UnresolvedState:
    items: tuple[str, ...]
    next_required_timeframe: str | None = None
    missing_data: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class AnalysisRequest:
    observations: NormalizedMarketObservations
    requested_at_utc: str
    request_id: str
    options: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AnalysisResultEnvelope:
    request_id: str
    status: KernelStatus
    unresolved: UnresolvedState
    analysis: Mapping[str, Any] | None
    brain_manifest_reference: str
    kernel_version: str
