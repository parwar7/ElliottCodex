"""Explicit bounded finer-observation selection for proposed child windows.

This module is PROJECT_ANALYSIS_INFRASTRUCTURE. Resolution comparison is an
operational chart-data relation only. Selection cannot establish Elliott
degree, visibility, family, validity, confirmation, or endpoint authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import NoReturn
import weakref

from elliott_methodology_kernel import (
    MultiTimeframeObservationTransportResult,
    ObservationResolutionRelation,
    compare_observation_resolutions,
)
from elliott_methodology_kernel.contracts import Bar, NormalizedMarketObservations
from elliott_runtime.market_data.geometric_pivots import (
    GeometricPivotDiscoveryConfig,
    GeometricPivotDiscoveryRequest,
    GeometricPivotDiscoveryResult,
    discover_geometric_pivots,
)

from .family_internal_subdivisions import FamilyInternalSubdivisionRequirement
from .recursive_child_candidate_generation import ProposedChildEvaluationWindow


ARTIFACT_CLASSIFICATION = "PROJECT_ANALYSIS_INFRASTRUCTURE"
SELECTION_CLASSIFICATION = "CALLER_SUPPLIED_OBSERVATION_SELECTION"
RESOLUTION_CLASSIFICATION = "PROJECT_OPERATIONAL_POLICY"
GEOMETRY_PARAMETER_CLASSIFICATION = "CALLER_SUPPLIED_GEOMETRY_PARAMETER"
FINER_TIMEFRAME_IS_NOT_LOWER_DEGREE = True
FINER_DATA_AVAILABLE_IS_NOT_INTERNALS_VISIBLE = True
FINER_DATA_SELECTED_IS_NOT_CHILD_FAMILY_VALIDATED = True
CROSS_TIMEFRAME_OBSERVATION_IS_NOT_CONFIRMATION = True
WINDOW_IS_NOT_ELLIOTT_ENDPOINT_AUTHORITY = True


class ChildObservationCoverageState(StrEnum):
    FULL_WINDOW_COVERAGE = "FULL_WINDOW_COVERAGE"
    PARTIAL_WINDOW_COVERAGE = "PARTIAL_WINDOW_COVERAGE"
    NO_WINDOW_COVERAGE = "NO_WINDOW_COVERAGE"


class ChildObservationSelectionDiagnosticCode(StrEnum):
    EXPLICIT_FINER_RESOLUTION_SELECTED = "EXPLICIT_FINER_RESOLUTION_SELECTED"
    FULL_WINDOW_COVERAGE = "FULL_WINDOW_COVERAGE"
    PARTIAL_WINDOW_COVERAGE = "PARTIAL_WINDOW_COVERAGE"
    NO_WINDOW_COVERAGE = "NO_WINDOW_COVERAGE"
    FINER_GEOMETRIC_PIVOTS_DISCOVERED = "FINER_GEOMETRIC_PIVOTS_DISCOVERED"
    COVERAGE_IS_NOT_STRUCTURAL_VALIDITY = "COVERAGE_IS_NOT_STRUCTURAL_VALIDITY"


class FinerChildObservationSelectionError(ValueError):
    """Fail-closed selection or contract error."""


class FinerWindowResourceBoundExceeded(FinerChildObservationSelectionError):
    """Raised before geometry discovery when a selected view exceeds its cap."""


class _SealedSelectionType(type):
    def __new__(mcls, name, bases, namespace, **kwargs):
        if any(isinstance(base, mcls) for base in bases):
            raise TypeError("Finer child-observation selection types cannot be subclassed.")
        return super().__new__(mcls, name, bases, namespace, **kwargs)


def _fail(message: str) -> NoReturn:
    raise FinerChildObservationSelectionError(message)


def _text(value: object, name: str) -> str:
    if type(value) is not str or value.strip() == "":
        _fail(f"{name} must be one exact non-blank string.")
    return value


def _refs(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or any(
        type(item) is not str or item.strip() == "" for item in value
    ):
        _fail("provenance_refs must be one exact tuple of non-blank strings.")
    return value


def _symbol_key(observations: NormalizedMarketObservations) -> tuple[object, ...]:
    symbol = observations.symbol
    return (symbol.symbol, symbol.market_type, symbol.exchange, symbol.provider_symbol)


@dataclass(frozen=True, slots=True, eq=False)
class ChildObservationSelectionConfig(metaclass=_SealedSelectionType):
    max_bars_per_selected_window: int
    max_geometric_pivots_per_window: int
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        for name, value, maximum in (
            ("max_bars_per_selected_window", self.max_bars_per_selected_window, 1_000_000),
            ("max_geometric_pivots_per_window", self.max_geometric_pivots_per_window, 1_000_000),
        ):
            if type(value) is not int or not 1 <= value <= maximum:
                _fail(f"{name} must be one exact integer within [1, {maximum}].")
        object.__setattr__(self, "_snapshot", (
            self.max_bars_per_selected_window,
            self.max_geometric_pivots_per_window,
        ))

    def _validated(self):
        if type(self) is not ChildObservationSelectionConfig:
            _fail("Selection config must have its exact type.")
        if (self.max_bars_per_selected_window, self.max_geometric_pivots_per_window) != self._snapshot:
            _fail("Selection config changed after construction.")
        return self


@dataclass(frozen=True, slots=True, eq=False)
class SelectedChildObservationWindow(metaclass=_SealedSelectionType):
    source_observations: NormalizedMarketObservations
    parent_window_start_utc: datetime
    parent_window_end_utc: datetime
    ordered_bars: tuple[Bar, ...]
    coverage_state: ChildObservationCoverageState
    provenance_refs: tuple[str, ...]
    elliott_endpoint_authority: bool = False
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if type(self.source_observations) is not NormalizedMarketObservations:
            _fail("Selected window requires exact NormalizedMarketObservations.")
        for name, value in (
            ("parent_window_start_utc", self.parent_window_start_utc),
            ("parent_window_end_utc", self.parent_window_end_utc),
        ):
            if (
                type(value) is not datetime
                or value.tzinfo is None
                or value.utcoffset() is None
                or value.utcoffset().total_seconds() != 0
            ):
                _fail(f"{name} must be one exact timezone-aware UTC datetime.")
        if self.parent_window_start_utc >= self.parent_window_end_utc:
            _fail("Selected child interval must be strictly chronological.")
        if type(self.ordered_bars) is not tuple or any(type(bar) is not Bar for bar in self.ordered_bars):
            _fail("ordered_bars must be one exact tuple of exact source bars.")
        expected = tuple(
            bar for bar in self.source_observations.bars
            if self.parent_window_start_utc <= bar.timestamp_utc <= self.parent_window_end_utc
        )
        if len(expected) != len(self.ordered_bars) or any(
            observed is not source
            for observed, source in zip(self.ordered_bars, expected, strict=True)
        ):
            _fail("Selected bars must be every and only exact source bar inside the UTC interval.")
        expected_state = _coverage_state(
            self.source_observations,
            self.parent_window_start_utc,
            self.parent_window_end_utc,
            expected,
        )
        if self.coverage_state is not expected_state:
            _fail("Selected-window coverage state differs from deterministic recomputation.")
        if self.elliott_endpoint_authority is not False:
            _fail("An observation window cannot carry Elliott endpoint authority.")
        _refs(self.provenance_refs)
        object.__setattr__(self, "_snapshot", tuple(
            getattr(self, name) for name in self.__dataclass_fields__ if name != "_snapshot"
        ))

    def _validated(self):
        if type(self) is not SelectedChildObservationWindow:
            _fail("Selected child window must have its exact type.")
        current = tuple(getattr(self, name) for name in self.__dataclass_fields__ if name != "_snapshot")
        if len(current) != len(self._snapshot) or any(
            observed is not expected for observed, expected in zip(current, self._snapshot, strict=True)
        ):
            _fail("Selected child window changed after construction.")
        self.__post_init__()
        return self


@dataclass(frozen=True, slots=True, eq=False)
class ChildObservationSelectionDiagnostic(metaclass=_SealedSelectionType):
    code: ChildObservationSelectionDiagnosticCode
    count: int
    detail: str
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if type(self.code) is not ChildObservationSelectionDiagnosticCode:
            _fail("Selection diagnostic code has an unexpected type.")
        if type(self.count) is not int or self.count < 0:
            _fail("Selection diagnostic count must be one non-negative integer.")
        _text(self.detail, "diagnostic detail")
        current = (self.code, self.count, self.detail)
        if hasattr(self, "_snapshot"):
            if current != self._snapshot:
                _fail("Selection diagnostic changed after construction.")
        else:
            object.__setattr__(self, "_snapshot", current)


@dataclass(frozen=True, slots=True, eq=False)
class ChildObservationSelectionRequest(metaclass=_SealedSelectionType):
    selection_id: str
    internal_requirement: FamilyInternalSubdivisionRequirement
    proposed_child_window: ProposedChildEvaluationWindow
    multi_timeframe_context: MultiTimeframeObservationTransportResult
    selected_observations: NormalizedMarketObservations
    geometry_config: GeometricPivotDiscoveryConfig
    config: ChildObservationSelectionConfig
    provenance_refs: tuple[str, ...]
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        _text(self.selection_id, "selection_id")
        if type(self.internal_requirement) is not FamilyInternalSubdivisionRequirement:
            _fail("Selection requires one exact internal requirement.")
        self.internal_requirement.__post_init__()
        if type(self.proposed_child_window) is not ProposedChildEvaluationWindow:
            _fail("Selection requires one exact proposed child window.")
        self.proposed_child_window._validated()
        if self.proposed_child_window.internal_requirement is not self.internal_requirement:
            _fail("Selection requirement and proposed window identities differ.")
        if type(self.multi_timeframe_context) is not MultiTimeframeObservationTransportResult:
            _fail("Selection requires one exact live multi-timeframe transport result.")
        self.multi_timeframe_context._validated()
        if type(self.selected_observations) is not NormalizedMarketObservations:
            _fail("selected_observations must have its exact normalized type.")
        if not any(
            self.selected_observations is item
            for item in self.multi_timeframe_context.observation_bundle.observation_sets
        ):
            _fail("Selected observations are foreign to the exact supplied bundle.")
        parent = self.internal_requirement.parent_candidate.source_observations
        if _symbol_key(self.selected_observations) != _symbol_key(parent):
            _fail("Selected observations represent a different exact market identity.")
        relation = compare_observation_resolutions(
            self.selected_observations.timeframe,
            parent.timeframe,
        )
        if relation is not ObservationResolutionRelation.FINER_THAN:
            _fail("This V1 accepts only an explicitly selected finer chart resolution.")
        if type(self.geometry_config) is not GeometricPivotDiscoveryConfig:
            _fail("geometry_config must have its exact existing type.")
        if type(self.config) is not ChildObservationSelectionConfig:
            _fail("config must have its exact selection type.")
        self.config._validated()
        _refs(self.provenance_refs)
        object.__setattr__(self, "_snapshot", tuple(
            getattr(self, name) for name in self.__dataclass_fields__ if name != "_snapshot"
        ))

    def _validated(self):
        if type(self) is not ChildObservationSelectionRequest:
            _fail("Selection request must have its exact type.")
        current = tuple(getattr(self, name) for name in self.__dataclass_fields__ if name != "_snapshot")
        if len(current) != len(self._snapshot) or any(
            observed is not expected for observed, expected in zip(current, self._snapshot, strict=True)
        ):
            _fail("Selection request changed after construction.")
        self.__post_init__()
        return self


@dataclass(frozen=True, slots=True, eq=False, init=False, weakref_slot=True)
class ChildObservationSelectionResult(metaclass=_SealedSelectionType):
    request: ChildObservationSelectionRequest
    selected_window: SelectedChildObservationWindow
    resolution_relation_to_parent: ObservationResolutionRelation
    finer_geometric_pivots: GeometricPivotDiscoveryResult | None
    coverage_diagnostics: tuple[ChildObservationSelectionDiagnostic, ...]
    provenance_refs: tuple[str, ...]
    _snapshot: tuple[object, ...]

    def __init__(self, *args, **kwargs):
        raise TypeError("Selection results are factory-only.")

    def _validated(self):
        if type(self) is not ChildObservationSelectionResult:
            _fail("Selection result must have its exact type.")
        issued = _ISSUED_RESULTS.get(self)
        current = tuple(getattr(self, name) for name in self.__dataclass_fields__ if name != "_snapshot")
        if issued is None or len(current) != len(self._snapshot) or any(
            observed is not expected for observed, expected in zip(current, self._snapshot, strict=True)
        ):
            _fail("Selection result is unissued or changed after creation.")
        self.request._validated()
        self.selected_window._validated()
        if self.selected_window is not issued or self.selected_window.source_observations is not self.request.selected_observations:
            _fail("Selection result lost its exact issued observation-window identity.")
        if self.resolution_relation_to_parent is not ObservationResolutionRelation.FINER_THAN:
            _fail("Selection result lost its explicit finer-resolution relation.")
        if self.selected_window.coverage_state is ChildObservationCoverageState.FULL_WINDOW_COVERAGE:
            if type(self.finer_geometric_pivots) is not GeometricPivotDiscoveryResult:
                _fail("Full coverage must retain its exact finer geometric result.")
            if (
                self.finer_geometric_pivots.input_observations is not self.request.selected_observations
                or self.finer_geometric_pivots.scoped_bars is not self.selected_window.ordered_bars
            ):
                _fail("Finer geometry lost exact observation-window ancestry.")
            expected_geometry = discover_geometric_pivots(GeometricPivotDiscoveryRequest(
                f"{self.request.selection_id}:finer-geometry",
                self.request.selected_observations,
                self.request.geometry_config,
                self.request.provenance_refs + ("explicit-finer-geometry",),
                self.selected_window.ordered_bars,
            ))
            if (
                self.finer_geometric_pivots.pivots != expected_geometry.pivots
                or self.finer_geometric_pivots.diagnostics != expected_geometry.diagnostics
                or self.finer_geometric_pivots.provenance_refs != expected_geometry.provenance_refs
            ):
                _fail("Finer geometric result differs from deterministic recomputation.")
        elif self.finer_geometric_pivots is not None:
            _fail("Partial or absent coverage cannot carry geometric results.")
        if type(self.coverage_diagnostics) is not tuple:
            _fail("coverage_diagnostics must be one exact tuple.")
        for diagnostic in self.coverage_diagnostics:
            diagnostic.__post_init__()
        _refs(self.provenance_refs)
        return self


_ISSUED_RESULTS: weakref.WeakKeyDictionary[
    ChildObservationSelectionResult,
    SelectedChildObservationWindow,
] = weakref.WeakKeyDictionary()


def _coverage_state(observations, start, end, bars) -> ChildObservationCoverageState:
    if not bars:
        return ChildObservationCoverageState.NO_WINDOW_COVERAGE
    if observations.bars[0].timestamp_utc <= start and observations.bars[-1].timestamp_utc >= end:
        return ChildObservationCoverageState.FULL_WINDOW_COVERAGE
    return ChildObservationCoverageState.PARTIAL_WINDOW_COVERAGE


def select_finer_child_observations(
    request: ChildObservationSelectionRequest,
) -> ChildObservationSelectionResult:
    """Select one exact caller-chosen finer observation set and bounded interval."""

    if type(request) is not ChildObservationSelectionRequest:
        _fail("select_finer_child_observations requires one exact request.")
    request._validated()
    start = request.proposed_child_window.start_pivot.timestamp_utc
    end = request.proposed_child_window.end_pivot.timestamp_utc
    bars = tuple(
        bar for bar in request.selected_observations.bars
        if start <= bar.timestamp_utc <= end
    )
    if len(bars) > request.config.max_bars_per_selected_window:
        raise FinerWindowResourceBoundExceeded(
            "FINER_WINDOW_RESOURCE_BOUND_EXCEEDED: max_bars_per_selected_window; no bars were truncated."
        )
    state = _coverage_state(request.selected_observations, start, end, bars)
    window = SelectedChildObservationWindow(
        request.selected_observations,
        start,
        end,
        bars,
        state,
        request.provenance_refs + ("exact-inclusive-utc-child-observation-view",),
        False,
    )
    geometry = None
    if state is ChildObservationCoverageState.FULL_WINDOW_COVERAGE:
        geometry = discover_geometric_pivots(GeometricPivotDiscoveryRequest(
            f"{request.selection_id}:finer-geometry",
            request.selected_observations,
            request.geometry_config,
            request.provenance_refs + ("explicit-finer-geometry",),
            bars,
        ))
        if len(geometry.pivots) > request.config.max_geometric_pivots_per_window:
            raise FinerWindowResourceBoundExceeded(
                "FINER_WINDOW_RESOURCE_BOUND_EXCEEDED: max_geometric_pivots_per_window; no pivots were truncated."
            )
    coverage_code = {
        ChildObservationCoverageState.FULL_WINDOW_COVERAGE: ChildObservationSelectionDiagnosticCode.FULL_WINDOW_COVERAGE,
        ChildObservationCoverageState.PARTIAL_WINDOW_COVERAGE: ChildObservationSelectionDiagnosticCode.PARTIAL_WINDOW_COVERAGE,
        ChildObservationCoverageState.NO_WINDOW_COVERAGE: ChildObservationSelectionDiagnosticCode.NO_WINDOW_COVERAGE,
    }[state]
    diagnostics = (
        ChildObservationSelectionDiagnostic(
            ChildObservationSelectionDiagnosticCode.EXPLICIT_FINER_RESOLUTION_SELECTED,
            1,
            "Caller selected one exact finer chart-resolution dataset; this has no degree meaning.",
        ),
        ChildObservationSelectionDiagnostic(
            coverage_code,
            len(bars),
            "Coverage is determined from exact source timestamp extent and inclusive UTC interval bars.",
        ),
        ChildObservationSelectionDiagnostic(
            ChildObservationSelectionDiagnosticCode.FINER_GEOMETRIC_PIVOTS_DISCOVERED,
            0 if geometry is None else len(geometry.pivots),
            "Existing geometric discovery reused with caller-supplied parameters and exact bar scope.",
        ),
        ChildObservationSelectionDiagnostic(
            ChildObservationSelectionDiagnosticCode.COVERAGE_IS_NOT_STRUCTURAL_VALIDITY,
            1,
            "Coverage and finer data availability cannot establish Elliott validity or visibility.",
        ),
    )
    values = {
        "request": request,
        "selected_window": window,
        "resolution_relation_to_parent": ObservationResolutionRelation.FINER_THAN,
        "finer_geometric_pivots": geometry,
        "coverage_diagnostics": diagnostics,
        "provenance_refs": request.provenance_refs,
    }
    result = object.__new__(ChildObservationSelectionResult)
    for name, value in values.items():
        object.__setattr__(result, name, value)
    object.__setattr__(result, "_snapshot", tuple(values.values()))
    _ISSUED_RESULTS[result] = window
    return result._validated()


def validate_child_observation_selection_result(value: object) -> ChildObservationSelectionResult:
    if type(value) is not ChildObservationSelectionResult:
        _fail("Expected one exact ChildObservationSelectionResult.")
    return value._validated()


__all__ = [
    "ARTIFACT_CLASSIFICATION",
    "CROSS_TIMEFRAME_OBSERVATION_IS_NOT_CONFIRMATION",
    "FINER_DATA_AVAILABLE_IS_NOT_INTERNALS_VISIBLE",
    "FINER_DATA_SELECTED_IS_NOT_CHILD_FAMILY_VALIDATED",
    "FINER_TIMEFRAME_IS_NOT_LOWER_DEGREE",
    "GEOMETRY_PARAMETER_CLASSIFICATION",
    "RESOLUTION_CLASSIFICATION",
    "SELECTION_CLASSIFICATION",
    "WINDOW_IS_NOT_ELLIOTT_ENDPOINT_AUTHORITY",
    "ChildObservationCoverageState",
    "ChildObservationSelectionConfig",
    "ChildObservationSelectionDiagnostic",
    "ChildObservationSelectionDiagnosticCode",
    "ChildObservationSelectionRequest",
    "ChildObservationSelectionResult",
    "FinerChildObservationSelectionError",
    "FinerWindowResourceBoundExceeded",
    "SelectedChildObservationWindow",
    "select_finer_child_observations",
    "validate_child_observation_selection_result",
]
