"""Bounded enumeration of neutral candidate hypotheses.

This module is PROJECT_ANALYSIS_INFRASTRUCTURE.  Enumeration never establishes
an Elliott endpoint, family, label, degree, validity, preference, or forecast.
Existing methodology is invoked only through an exact caller-supplied bounded
analysis request for the exact generated candidate identity.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import StrEnum
from itertools import combinations
from math import comb
from typing import NoReturn
import weakref

from elliott_methodology_kernel import (
    AnalyzedWaveSubject,
    BoundedManualChartAnalysisRequest,
    BoundedManualChartAnalysisResult,
    BoundedManualChartFinalSummary,
    MethodologyKernel,
)
from elliott_methodology_kernel.contracts import NormalizedMarketObservations

from elliott_runtime.market_data.geometric_pivots import (
    GeometricPivotDiscoveryConfig,
    GeometricPivotDiscoveryRequest,
    GeometricPivotDiscoveryResult,
    GeometricPivotObservation,
    discover_geometric_pivots,
)


ARTIFACT_CLASSIFICATION = "PROJECT_ANALYSIS_INFRASTRUCTURE"
BOUND_CLASSIFICATION = "CALLER_SUPPLIED_OPERATIONAL_BOUND"
ENUMERATION_CLASSIFICATION = "PURE_COMBINATORIAL_INFRASTRUCTURE"
CANDIDATE_HYPOTHESIS_ONLY = True
ELLIOTT_VALIDITY_AUTHORITY = False
FAMILY_AUTHORITY = False
DEGREE_AUTHORITY = False
TIMEFRAME_IS_NOT_DEGREE = True
_MAX_PIVOTS_CONSIDERED = 10_000
_MAX_CANDIDATES_GENERATED = 100_000
_ISSUED_RESULTS: weakref.WeakKeyDictionary[
    CandidateGenerationResult, tuple[GeneratedCandidateHypothesis, ...]
] = weakref.WeakKeyDictionary()


class CandidateGenerationError(ValueError):
    """Fail-closed candidate-generation boundary error."""


class CandidateGenerationLimitExceeded(CandidateGenerationError):
    """Raised instead of returning a partial candidate set."""


class CandidateHypothesisShape(StrEnum):
    THREE_SEGMENT_HYPOTHESIS = "THREE_SEGMENT_HYPOTHESIS"
    FIVE_SEGMENT_HYPOTHESIS = "FIVE_SEGMENT_HYPOTHESIS"

    @property
    def selected_pivot_count(self) -> int:
        return 4 if self is self.THREE_SEGMENT_HYPOTHESIS else 6


class CandidatePivotWindow(StrEnum):
    EARLIEST = "EARLIEST"
    LATEST = "LATEST"


class GeneratedCandidateReviewState(StrEnum):
    STRUCTURALLY_INVALID = "STRUCTURALLY_INVALID"
    UNRESOLVED = "UNRESOLVED"
    CURRENT_SUPPLIED_SCOPE_REVIEWED = "CURRENT_SUPPLIED_SCOPE_REVIEWED"


class _SealedCandidateType(type):
    def __new__(
        mcls: type,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
        **kwargs: object,
    ) -> type:
        if any(isinstance(base, mcls) for base in bases):
            raise TypeError("Candidate-generation infrastructure cannot be subclassed.")
        return super().__new__(mcls, name, bases, namespace, **kwargs)


def _fail(message: str) -> NoReturn:
    raise CandidateGenerationError(message)


def _text(value: object, name: str) -> str:
    if type(value) is not str or value.strip() == "":
        _fail(f"{name} must be one exact non-blank string.")
    return value


def _refs(value: object, name: str = "provenance_refs") -> tuple[str, ...]:
    if type(value) is not tuple or any(
        type(item) is not str or item.strip() == "" for item in value
    ):
        _fail(f"{name} must be one exact tuple of non-blank strings.")
    return value


@dataclass(frozen=True, slots=True, eq=False)
class CandidateGenerationConfig(metaclass=_SealedCandidateType):
    max_pivots_considered: int
    max_candidate_span_pivots: int
    max_skipped_pivots: int
    max_candidates_generated: int
    allowed_candidate_shapes: tuple[CandidateHypothesisShape, ...]
    pivot_window: CandidatePivotWindow
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        for name, value, minimum, maximum in (
            ("max_pivots_considered", self.max_pivots_considered, 1, _MAX_PIVOTS_CONSIDERED),
            ("max_candidate_span_pivots", self.max_candidate_span_pivots, 1, _MAX_PIVOTS_CONSIDERED),
            ("max_skipped_pivots", self.max_skipped_pivots, 0, _MAX_PIVOTS_CONSIDERED),
            ("max_candidates_generated", self.max_candidates_generated, 1, _MAX_CANDIDATES_GENERATED),
        ):
            if type(value) is not int or not minimum <= value <= maximum:
                _fail(f"{name} must be one exact integer within [{minimum}, {maximum}].")
        if self.max_candidate_span_pivots > self.max_pivots_considered:
            _fail("max_candidate_span_pivots cannot exceed max_pivots_considered.")
        if type(self.allowed_candidate_shapes) is not tuple or not self.allowed_candidate_shapes:
            _fail("allowed_candidate_shapes must be one non-empty exact tuple.")
        if any(type(shape) is not CandidateHypothesisShape for shape in self.allowed_candidate_shapes):
            _fail("Every allowed shape must be one exact CandidateHypothesisShape.")
        if len(set(self.allowed_candidate_shapes)) != len(self.allowed_candidate_shapes):
            _fail("allowed_candidate_shapes cannot contain duplicates.")
        required = max(shape.selected_pivot_count for shape in self.allowed_candidate_shapes)
        if self.max_pivots_considered < required or self.max_candidate_span_pivots < required:
            _fail("Pivot and span bounds must accommodate every allowed candidate shape.")
        if type(self.pivot_window) is not CandidatePivotWindow:
            _fail("pivot_window must be one exact CandidatePivotWindow.")
        object.__setattr__(
            self,
            "_snapshot",
            (
                self.max_pivots_considered,
                self.max_candidate_span_pivots,
                self.max_skipped_pivots,
                self.max_candidates_generated,
                self.allowed_candidate_shapes,
                self.pivot_window,
            ),
        )

    def _validated(self) -> CandidateGenerationConfig:
        if type(self) is not CandidateGenerationConfig:
            _fail("config must have its exact reviewed type.")
        current = (
            self.max_pivots_considered,
            self.max_candidate_span_pivots,
            self.max_skipped_pivots,
            self.max_candidates_generated,
            self.allowed_candidate_shapes,
            self.pivot_window,
        )
        if current != self._snapshot:
            _fail("Candidate-generation config changed after construction.")
        self.__post_init__()
        return self


@dataclass(frozen=True, slots=True, eq=False)
class CandidateMethodologyDelegation(metaclass=_SealedCandidateType):
    candidate_id: str
    bounded_request: BoundedManualChartAnalysisRequest
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        _text(self.candidate_id, "candidate_id")
        if type(self.bounded_request) is not BoundedManualChartAnalysisRequest:
            _fail("bounded_request must be one exact BoundedManualChartAnalysisRequest.")
        if self.bounded_request.candidate_id != self.candidate_id:
            _fail("Delegation and bounded-request candidate IDs must match exactly.")
        try:
            copy.copy(self.bounded_request)
        except Exception as error:
            raise CandidateGenerationError("bounded_request is malformed or changed.") from error
        object.__setattr__(self, "_snapshot", (self.candidate_id, self.bounded_request))

    def _validated(self) -> CandidateMethodologyDelegation:
        if type(self) is not CandidateMethodologyDelegation:
            _fail("Methodology delegation must have its exact reviewed type.")
        current = (self.candidate_id, self.bounded_request)
        if len(current) != len(self._snapshot) or any(
            observed is not expected
            for observed, expected in zip(current, self._snapshot, strict=True)
        ):
            _fail("Methodology delegation changed after construction.")
        try:
            copy.copy(self.bounded_request)
        except Exception as error:
            raise CandidateGenerationError("bounded_request is malformed or changed.") from error
        return self


@dataclass(frozen=True, slots=True, eq=False)
class CandidateGenerationRequest(metaclass=_SealedCandidateType):
    request_id: str
    requested_at_utc: str
    subject: AnalyzedWaveSubject
    observations: NormalizedMarketObservations
    geometric_pivots: GeometricPivotDiscoveryResult
    config: CandidateGenerationConfig
    methodology_delegations: tuple[CandidateMethodologyDelegation, ...]
    provenance_refs: tuple[str, ...]
    scoped_pivots: tuple[GeometricPivotObservation, ...] | None = None
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        _text(self.request_id, "request_id")
        _text(self.requested_at_utc, "requested_at_utc")
        if type(self.subject) is not AnalyzedWaveSubject:
            _fail("subject must be one exact AnalyzedWaveSubject.")
        _validate_geometry_relationship(self.observations, self.geometric_pivots)
        _validate_scoped_pivots(self.scoped_pivots, self.geometric_pivots)
        if type(self.config) is not CandidateGenerationConfig:
            _fail("config must be one exact CandidateGenerationConfig.")
        self.config._validated()
        if type(self.methodology_delegations) is not tuple or any(
            type(item) is not CandidateMethodologyDelegation
            for item in self.methodology_delegations
        ):
            _fail("methodology_delegations must be one exact tuple of exact delegations.")
        seen: set[str] = set()
        for item in self.methodology_delegations:
            item._validated()
            if item.candidate_id in seen:
                _fail("At most one methodology delegation may target a candidate ID.")
            if item.bounded_request.subject is not self.subject:
                _fail("A methodology delegation belongs to another subject identity.")
            if item.bounded_request.candidate_id != item.candidate_id:
                _fail("Delegation and bounded-request candidate IDs must match exactly.")
            seen.add(item.candidate_id)
        _refs(self.provenance_refs)
        object.__setattr__(
            self,
            "_snapshot",
            (
                self.request_id,
                self.requested_at_utc,
                self.subject,
                self.observations,
                self.geometric_pivots,
                self.config,
                self.methodology_delegations,
                self.provenance_refs,
                self.scoped_pivots,
            ),
        )

    def _validated(self) -> CandidateGenerationRequest:
        if type(self) is not CandidateGenerationRequest:
            _fail("request must have its exact reviewed type.")
        current = (
            self.request_id,
            self.requested_at_utc,
            self.subject,
            self.observations,
            self.geometric_pivots,
            self.config,
            self.methodology_delegations,
            self.provenance_refs,
            self.scoped_pivots,
        )
        if len(current) != len(self._snapshot) or any(
            observed is not expected
            for observed, expected in zip(current, self._snapshot, strict=True)
        ):
            _fail("Candidate-generation request changed after construction.")
        self.__post_init__()
        return self


@dataclass(frozen=True, slots=True, eq=False)
class CandidateGenerationDiagnostic(metaclass=_SealedCandidateType):
    code: str
    count: int
    detail: str
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        _text(self.code, "diagnostic code")
        _text(self.detail, "diagnostic detail")
        if type(self.count) is not int or self.count < 0:
            _fail("diagnostic count must be one non-negative exact integer.")
        object.__setattr__(self, "_snapshot", (self.code, self.count, self.detail))

    def _validated(self) -> CandidateGenerationDiagnostic:
        if type(self) is not CandidateGenerationDiagnostic:
            _fail("Candidate diagnostic must have its exact reviewed type.")
        current = (self.code, self.count, self.detail)
        if len(current) != len(self._snapshot) or any(
            observed is not expected
            for observed, expected in zip(current, self._snapshot, strict=True)
        ):
            _fail("Candidate diagnostic changed after construction.")
        return self


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class GeneratedCandidateHypothesis(metaclass=_SealedCandidateType):
    candidate_id: str
    subject: AnalyzedWaveSubject
    source_observations: NormalizedMarketObservations
    source_geometric_pivots: GeometricPivotDiscoveryResult
    ordered_selected_pivots: tuple[GeometricPivotObservation, ...]
    candidate_shape: CandidateHypothesisShape
    generation_config: CandidateGenerationConfig
    generation_reason: str
    existing_behaviors_executed: tuple[str, ...]
    review_state: GeneratedCandidateReviewState
    unresolved_reasons: tuple[str, ...]
    downstream_methodology_result: BoundedManualChartAnalysisResult | None
    provenance_refs: tuple[str, ...]
    candidate_hypothesis_only: bool = True
    elliott_validity_authority: bool = False
    family_authority: bool = False
    degree_authority: bool = False
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.candidate_hypothesis_only is not True or any(
            value is not False
            for value in (
                self.elliott_validity_authority,
                self.family_authority,
                self.degree_authority,
            )
        ):
            _fail("Generated candidates cannot carry Elliott authority.")
        if type(self.candidate_id) is not str or self.candidate_id.strip() == "":
            _fail("Generated candidate_id must be one exact non-blank string.")
        if type(self.subject) is not AnalyzedWaveSubject:
            _fail("Generated candidate subject must have its exact reviewed type.")
        if type(self.source_observations) is not NormalizedMarketObservations:
            _fail("Generated candidate observations must have their exact type.")
        if type(self.source_geometric_pivots) is not GeometricPivotDiscoveryResult:
            _fail("Generated candidate geometric ancestry must have its exact type.")
        if type(self.ordered_selected_pivots) is not tuple or any(
            type(pivot) is not GeometricPivotObservation
            for pivot in self.ordered_selected_pivots
        ):
            _fail("Generated candidate pivots must be one exact tuple.")
        if type(self.candidate_shape) is not CandidateHypothesisShape:
            _fail("Generated candidate shape must have its exact reviewed type.")
        if len(self.ordered_selected_pivots) != self.candidate_shape.selected_pivot_count:
            _fail("Generated candidate shape and selected-pivot count differ.")
        if type(self.generation_config) is not CandidateGenerationConfig:
            _fail("Generated candidate config must have its exact reviewed type.")
        _text(self.generation_reason, "generation_reason")
        _refs(self.existing_behaviors_executed, "existing_behaviors_executed")
        if type(self.review_state) is not GeneratedCandidateReviewState:
            _fail("Generated candidate review state must have its exact reviewed type.")
        _refs(self.unresolved_reasons, "unresolved_reasons")
        if self.downstream_methodology_result is not None:
            if type(self.downstream_methodology_result) is not BoundedManualChartAnalysisResult:
                _fail("Downstream methodology result has an unexpected type.")
            try:
                copy.copy(self.downstream_methodology_result)
            except Exception as error:
                raise CandidateGenerationError("Downstream methodology result changed.") from error
        _refs(self.provenance_refs)
        object.__setattr__(
            self,
            "_snapshot",
            tuple(
                getattr(self, name)
                for name in self.__dataclass_fields__
                if name != "_snapshot"
            ),
        )

    def _validated(self) -> GeneratedCandidateHypothesis:
        if type(self) is not GeneratedCandidateHypothesis:
            _fail("Generated candidate must have its exact reviewed type.")
        current = tuple(
            getattr(self, name)
            for name in self.__dataclass_fields__
            if name != "_snapshot"
        )
        if len(current) != len(self._snapshot) or any(
            observed is not expected
            for observed, expected in zip(current, self._snapshot, strict=True)
        ):
            _fail("Generated candidate changed after creation.")
        if self.downstream_methodology_result is not None:
            try:
                copy.copy(self.downstream_methodology_result)
            except Exception as error:
                raise CandidateGenerationError("Downstream methodology result changed.") from error
        return self

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Generated candidate hypotheses cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False, init=False, weakref_slot=True)
class CandidateGenerationResult(metaclass=_SealedCandidateType):
    request: CandidateGenerationRequest
    input_observations: NormalizedMarketObservations
    input_geometric_pivots: GeometricPivotDiscoveryResult
    candidates: tuple[GeneratedCandidateHypothesis, ...]
    diagnostics: tuple[CandidateGenerationDiagnostic, ...]
    provenance_refs: tuple[str, ...]
    _snapshot: tuple[object, ...]

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("Candidate-generation results are created only by the generator.")

    def _validated(self) -> CandidateGenerationResult:
        if type(self) is not CandidateGenerationResult:
            _fail("Candidate-generation result must have its exact reviewed type.")
        try:
            snapshot = object.__getattribute__(self, "_snapshot")
            issued = _ISSUED_RESULTS.get(self)
        except Exception as error:
            raise CandidateGenerationError("Candidate-generation result is malformed.") from error
        current = (
            self.request,
            self.input_observations,
            self.input_geometric_pivots,
            self.candidates,
            self.diagnostics,
            self.provenance_refs,
        )
        if issued is None or len(current) != len(snapshot) or any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            _fail("Candidate-generation result is unissued or changed after creation.")
        if len(issued) != len(self.candidates) or any(
            observed is not expected
            for observed, expected in zip(self.candidates, issued, strict=True)
        ):
            _fail("Candidate membership differs from the issued generation result.")
        self.request._validated()
        if (
            self.input_observations is not self.request.observations
            or self.input_geometric_pivots is not self.request.geometric_pivots
            or self.provenance_refs is not self.request.provenance_refs
        ):
            _fail("Candidate-generation result lost exact request ancestry.")
        if type(self.candidates) is not tuple:
            _fail("Candidate-generation result candidates must be one exact tuple.")
        permitted = (
            self.input_geometric_pivots.pivots
            if self.request.scoped_pivots is None
            else self.request.scoped_pivots
        )
        permitted_by_id = {id(pivot): pivot for pivot in permitted}
        for candidate in self.candidates:
            candidate._validated()
            if any(
                id(pivot) not in permitted_by_id
                or permitted_by_id[id(pivot)] is not pivot
                for pivot in candidate.ordered_selected_pivots
            ):
                _fail("A generated candidate escaped the exact supplied pivot scope.")
        if type(self.diagnostics) is not tuple:
            _fail("Candidate-generation diagnostics must be one exact tuple.")
        for diagnostic in self.diagnostics:
            diagnostic._validated()
        return self

    def __copy__(self) -> CandidateGenerationResult:
        return self._validated()

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> CandidateGenerationResult:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Candidate-generation results cannot be pickled.")


def validate_candidate_generation_result(
    result: object,
) -> CandidateGenerationResult:
    """Return one exact live issued and unchanged generation result."""

    if type(result) is not CandidateGenerationResult:
        _fail("Expected one exact CandidateGenerationResult.")
    return result._validated()


def _new_generation_result(
    request: CandidateGenerationRequest,
    candidates: tuple[GeneratedCandidateHypothesis, ...],
    diagnostics: tuple[CandidateGenerationDiagnostic, ...],
) -> CandidateGenerationResult:
    result = object.__new__(CandidateGenerationResult)
    values = {
        "request": request,
        "input_observations": request.observations,
        "input_geometric_pivots": request.geometric_pivots,
        "candidates": candidates,
        "diagnostics": diagnostics,
        "provenance_refs": request.provenance_refs,
    }
    for name, value in values.items():
        object.__setattr__(result, name, value)
    object.__setattr__(result, "_snapshot", tuple(values.values()))
    _ISSUED_RESULTS[result] = candidates
    return result._validated()


def _validate_geometry_relationship(
    observations: object,
    result: object,
) -> GeometricPivotDiscoveryResult:
    if type(observations) is not NormalizedMarketObservations:
        _fail("observations must be one exact NormalizedMarketObservations.")
    if type(result) is not GeometricPivotDiscoveryResult:
        _fail("geometric_pivots must be one exact GeometricPivotDiscoveryResult.")
    if result.input_observations is not observations:
        _fail("Geometric pivots must retain the exact supplied observation identity.")
    if type(result.config) is not GeometricPivotDiscoveryConfig:
        _fail("Geometric pivot configuration has an unexpected type.")
    if type(result.pivots) is not tuple or any(
        type(pivot) is not GeometricPivotObservation for pivot in result.pivots
    ):
        _fail("Geometric pivots must be one exact tuple of exact observations.")
    try:
        expected = discover_geometric_pivots(
            GeometricPivotDiscoveryRequest(
                result.request_id,
                observations,
                result.config,
                result.provenance_refs,
            )
        )
    except Exception as error:
        raise CandidateGenerationError("Geometric pivot result failed revalidation.") from error
    if (
        result.pivots != expected.pivots
        or result.diagnostics != expected.diagnostics
        or result.provenance_refs != expected.provenance_refs
    ):
        _fail("Geometric pivot result differs from deterministic recomputation.")
    return result


def _validate_scoped_pivots(
    scoped_pivots: object,
    result: GeometricPivotDiscoveryResult,
) -> tuple[GeometricPivotObservation, ...] | None:
    if scoped_pivots is None:
        return None
    if type(scoped_pivots) is not tuple or any(
        type(pivot) is not GeometricPivotObservation for pivot in scoped_pivots
    ):
        _fail("scoped_pivots must be None or one exact tuple of exact pivots.")
    source_by_id = {id(pivot): pivot for pivot in result.pivots}
    seen: set[int] = set()
    previous = None
    for pivot in scoped_pivots:
        if id(pivot) not in source_by_id or source_by_id[id(pivot)] is not pivot:
            _fail("Every scoped pivot must retain exact source-result identity.")
        if id(pivot) in seen:
            _fail("scoped_pivots cannot contain duplicate pivot identities.")
        if previous is not None and pivot.timestamp_utc <= previous:
            _fail("scoped_pivots must retain strict source chronology.")
        seen.add(id(pivot))
        previous = pivot.timestamp_utc
    return scoped_pivots


def _candidate_specs(
    request: CandidateGenerationRequest,
) -> tuple[list[tuple[str, CandidateHypothesisShape, tuple[GeometricPivotObservation, ...]]], int, int]:
    source_pivots = request.geometric_pivots.pivots
    pivots = (
        source_pivots
        if request.scoped_pivots is None
        else request.scoped_pivots
    )
    source_indices = {id(pivot): index for index, pivot in enumerate(source_pivots)}
    considered_count = min(len(pivots), request.config.max_pivots_considered)
    offset = 0 if request.config.pivot_window is CandidatePivotWindow.EARLIEST else len(pivots) - considered_count
    specs: list[tuple[str, CandidateHypothesisShape, tuple[GeometricPivotObservation, ...]]] = []
    eligible, rejected = estimate_candidate_generation_demand(
        considered_count,
        request.config,
    )
    if eligible > request.config.max_candidates_generated:
        raise CandidateGenerationLimitExceeded(
            "Candidate enumeration exceeds max_candidates_generated; no candidate enumeration or partial result occurred."
        )

    for shape in request.config.allowed_candidate_shapes:
        required = shape.selected_pivot_count
        allowed_span = min(
            request.config.max_candidate_span_pivots,
            required + request.config.max_skipped_pivots,
        )
        for first in range(considered_count):
            end = min(considered_count, first + allowed_span)
            for tail in combinations(range(first + 1, end), required - 1):
                indices = (first,) + tail
                selected_indices = tuple(offset + index for index in indices)
                absolute = tuple(
                    source_indices[id(pivots[index])] for index in selected_indices
                )
                candidate_id = (
                    f"{request.request_id}:{shape.value}:"
                    + "-".join(str(index) for index in absolute)
                )
                selected = tuple(pivots[index] for index in selected_indices)
                specs.append((candidate_id, shape, selected))
    if len(specs) != eligible:
        _fail("Bounded candidate enumeration differed from its precomputed count.")
    excluded = len(source_pivots) - considered_count
    return specs, rejected, excluded


def estimate_candidate_generation_demand(
    pivot_count: int,
    config: CandidateGenerationConfig,
) -> tuple[int, int]:
    """Return exact eligible/rejected counts without materializing candidates."""

    if type(pivot_count) is not int or pivot_count < 0:
        _fail("pivot_count must be one exact non-negative integer.")
    if type(config) is not CandidateGenerationConfig:
        _fail("config must be one exact CandidateGenerationConfig.")
    config._validated()
    considered_count = min(pivot_count, config.max_pivots_considered)
    eligible = 0
    rejected = 0
    for shape in config.allowed_candidate_shapes:
        required = shape.selected_pivot_count
        allowed_span = min(
            config.max_candidate_span_pivots,
            required + config.max_skipped_pivots,
        )
        shape_eligible = sum(
            comb(min(considered_count - first - 1, allowed_span - 1), required - 1)
            for first in range(considered_count)
            if min(considered_count - first - 1, allowed_span - 1) >= required - 1
        )
        eligible += shape_eligible
        rejected += (
            comb(considered_count, required) - shape_eligible
            if considered_count >= required
            else 0
        )
    return eligible, rejected


def _review_state(
    result: BoundedManualChartAnalysisResult,
) -> GeneratedCandidateReviewState:
    mapping = {
        BoundedManualChartFinalSummary.STRUCTURALLY_INVALID:
            GeneratedCandidateReviewState.STRUCTURALLY_INVALID,
        BoundedManualChartFinalSummary.UNRESOLVED:
            GeneratedCandidateReviewState.UNRESOLVED,
        BoundedManualChartFinalSummary.CURRENT_SUPPLIED_SCOPE_REVIEWED:
            GeneratedCandidateReviewState.CURRENT_SUPPLIED_SCOPE_REVIEWED,
    }
    return mapping[result.final_summary]


def generate_candidate_hypotheses(
    request: CandidateGenerationRequest,
    methodology_kernel: MethodologyKernel | None = None,
) -> CandidateGenerationResult:
    """Enumerate bounded hypotheses and optionally delegate exact caller inputs."""

    request = request._validated() if type(request) is CandidateGenerationRequest else None
    if request is None:
        _fail("generate_candidate_hypotheses requires one exact request.")
    if request.methodology_delegations:
        if type(methodology_kernel) is not MethodologyKernel:
            _fail("Exact methodology delegations require one exact MethodologyKernel.")
    elif methodology_kernel is not None:
        _fail("A methodology kernel is accepted only when exact delegations are supplied.")

    specs, rejected, excluded = _candidate_specs(request)
    by_id = {item.candidate_id: item for item in request.methodology_delegations}
    generated_ids = {candidate_id for candidate_id, _, _ in specs}
    unknown = set(by_id) - generated_ids
    if unknown:
        _fail("A methodology delegation targets a candidate not produced by this request.")

    candidates = []
    for candidate_id, shape, selected in specs:
        delegation = by_id.get(candidate_id)
        if delegation is None:
            downstream = None
            state = GeneratedCandidateReviewState.UNRESOLVED
            behaviors: tuple[str, ...] = ()
            reasons = ("NO_EXACT_METHODOLOGY_INPUTS_SUPPLIED",)
        else:
            assert methodology_kernel is not None
            downstream = methodology_kernel.analyze_bounded_manual_chart(
                delegation.bounded_request
            )
            if type(downstream) is not BoundedManualChartAnalysisResult:
                _fail("Existing methodology returned an unexpected result type.")
            if downstream.subject is not request.subject or downstream.candidate_id != candidate_id:
                _fail("Existing methodology result lost exact candidate or subject identity.")
            state = _review_state(downstream)
            behaviors = tuple(trace.behavior_id for trace in downstream.traceability)
            reasons = downstream.unresolved_reasons
        candidates.append(
            GeneratedCandidateHypothesis(
                candidate_id=candidate_id,
                subject=request.subject,
                source_observations=request.observations,
                source_geometric_pivots=request.geometric_pivots,
                ordered_selected_pivots=selected,
                candidate_shape=shape,
                generation_config=request.config,
                generation_reason="DETERMINISTIC_BOUNDED_PIVOT_SUBSEQUENCE",
                existing_behaviors_executed=behaviors,
                review_state=state,
                unresolved_reasons=reasons,
                downstream_methodology_result=downstream,
                provenance_refs=request.provenance_refs
                + (f"geometric_pivot_request:{request.geometric_pivots.request_id}",),
            )
        )

    diagnostics = (
        CandidateGenerationDiagnostic(
            "INPUT_GEOMETRIC_PIVOTS",
            len(request.geometric_pivots.pivots),
            "Exact geometric observations supplied; none has Elliott endpoint authority.",
        ),
        CandidateGenerationDiagnostic(
            "PIVOTS_EXCLUDED_BY_CONSIDERATION_WINDOW",
            excluded,
            "Caller bound excluded these pivots before enumeration.",
        ),
        CandidateGenerationDiagnostic(
            "SUBSEQUENCES_REJECTED_BY_SPAN_OR_SKIP_BOUNDS",
            rejected,
            "Combinatorial count outside caller span or skip bounds; these combinations were never enumerated.",
        ),
        CandidateGenerationDiagnostic(
            "GENERATED_CANDIDATE_HYPOTHESES",
            len(candidates),
            "Enumeration count only; generation is not Elliott confirmation.",
        ),
    )
    return _new_generation_result(request, tuple(candidates), diagnostics)


__all__ = [
    "ARTIFACT_CLASSIFICATION",
    "BOUND_CLASSIFICATION",
    "CANDIDATE_HYPOTHESIS_ONLY",
    "DEGREE_AUTHORITY",
    "ELLIOTT_VALIDITY_AUTHORITY",
    "ENUMERATION_CLASSIFICATION",
    "FAMILY_AUTHORITY",
    "TIMEFRAME_IS_NOT_DEGREE",
    "CandidateGenerationConfig",
    "CandidateGenerationDiagnostic",
    "CandidateGenerationError",
    "CandidateGenerationLimitExceeded",
    "CandidateGenerationRequest",
    "CandidateGenerationResult",
    "CandidateHypothesisShape",
    "CandidateMethodologyDelegation",
    "CandidatePivotWindow",
    "GeneratedCandidateHypothesis",
    "GeneratedCandidateReviewState",
    "generate_candidate_hypotheses",
    "estimate_candidate_generation_demand",
    "validate_candidate_generation_result",
]
