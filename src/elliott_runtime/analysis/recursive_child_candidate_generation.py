"""One-level bounded neutral child-candidate evidence generation.

This is PROJECT_ANALYSIS_INFRASTRUCTURE. Proposed child intervals are transport
windows over exact existing pivots, not orthodox Elliott endpoints. Generated
children remain neutral hypotheses and cannot satisfy an internal-family
requirement, establish degree, or create family certification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import NoReturn
import weakref

from elliott_methodology_kernel import (
    AnalysisResolutionState,
    BoundedRecursiveAnalysisNode,
    BoundedRecursiveAnalysisResolution,
)
from elliott_runtime.market_data.geometric_pivots import (
    GeometricPivotDiscoveryResult,
    GeometricPivotObservation,
    GeometricPivotState,
)

from .candidate_generation import (
    CandidateGenerationConfig,
    CandidateGenerationRequest,
    CandidateGenerationResult,
    CandidateHypothesisShape,
    CandidatePivotWindow,
    estimate_candidate_generation_demand,
    generate_candidate_hypotheses,
    validate_candidate_generation_result,
)
from .competing_candidates import (
    CompetingCandidateSetRequest,
    CompetingCandidateSetResult,
    build_competing_candidate_set,
    validate_competing_candidate_set_result,
)
from .family_internal_subdivisions import (
    FamilyChildCandidateEvidence,
    FamilyInternalSubdivisionEvaluationRequest,
    FamilyInternalSubdivisionEvaluationResult,
    FamilyInternalSubdivisionRequirement,
    SOURCE_DERIVED_BASE_CASE_NOT_FOUND,
    evaluate_family_internal_subdivisions,
    validate_family_internal_subdivision_evaluation_result,
)


ARTIFACT_CLASSIFICATION = "PROJECT_ANALYSIS_INFRASTRUCTURE"
BOUND_CLASSIFICATION = "CALLER_SUPPLIED_OPERATIONAL_BOUND"
WINDOW_CLASSIFICATION = "PROPOSED_CHILD_EVALUATION_WINDOW"
CHILD_EVIDENCE_CLASSIFICATION = "NEUTRAL_CHILD_CANDIDATE_EVIDENCE"
EXACT_AUTOMATIC_CHILD_LEVELS = 1
CHILD_CANDIDATE_IS_NOT_VALIDATED_CHILD_WAVE = True
WINDOW_IS_NOT_ELLIOTT_ENDPOINT_AUTHORITY = True
RECURSIVE_DEPTH_IS_NOT_DEGREE = True
FINER_TIMEFRAME_IS_NOT_LOWER_DEGREE = True
MORE_CHILD_EVIDENCE_IS_NOT_FAMILY_VALIDITY = True

_MAX_REQUIREMENTS = 100_000
_MAX_WINDOWS = 100_000
_MAX_TOTAL_CANDIDATES = 1_000_000


class RecursiveChildCandidateGenerationError(ValueError):
    """Fail-closed child-generation infrastructure error."""


class RecursiveChildCandidateGenerationLimitExceeded(
    RecursiveChildCandidateGenerationError
):
    """Raised before candidate materialization when an explicit bound is exceeded."""


class ChildRequirementGenerationStatus(StrEnum):
    NEUTRAL_CHILD_CANDIDATE_EVIDENCE_AVAILABLE = (
        "NEUTRAL_CHILD_CANDIDATE_EVIDENCE_AVAILABLE"
    )
    INSUFFICIENT_GEOMETRIC_PIVOTS = "INSUFFICIENT_GEOMETRIC_PIVOTS"
    FINER_RESOLUTION_NEUTRAL_CHILD_EVIDENCE_AVAILABLE = (
        "FINER_RESOLUTION_NEUTRAL_CHILD_EVIDENCE_AVAILABLE"
    )
    PARTIAL_FINER_OBSERVATION_COVERAGE = "PARTIAL_FINER_OBSERVATION_COVERAGE"
    NO_FINER_OBSERVATION_COVERAGE = "NO_FINER_OBSERVATION_COVERAGE"


class ChildCandidateGenerationDiagnosticCode(StrEnum):
    REQUIREMENTS_PROCESSED = "REQUIREMENTS_PROCESSED"
    CHILD_WINDOWS_CREATED = "CHILD_WINDOWS_CREATED"
    SUFFICIENT_INTERVAL_PIVOTS = "SUFFICIENT_INTERVAL_PIVOTS"
    INSUFFICIENT_INTERVAL_PIVOTS = "INSUFFICIENT_INTERVAL_PIVOTS"
    NEUTRAL_CHILD_EVIDENCE_CREATED = "NEUTRAL_CHILD_EVIDENCE_CREATED"
    NEUTRAL_CHILD_CANDIDATES_CREATED = "NEUTRAL_CHILD_CANDIDATES_CREATED"
    DEVELOPING_WINDOWS_PRESENT = "DEVELOPING_WINDOWS_PRESENT"
    BASE_CASE_REMAINS_BLOCKED = "BASE_CASE_REMAINS_BLOCKED"
    FINER_SELECTIONS_APPLIED = "FINER_SELECTIONS_APPLIED"
    FINER_COVERAGE_FAILURES = "FINER_COVERAGE_FAILURES"


class _SealedChildType(type):
    def __new__(mcls, name, bases, namespace, **kwargs):
        if any(isinstance(base, mcls) for base in bases):
            raise TypeError("Recursive child-generation infrastructure cannot be subclassed.")
        return super().__new__(mcls, name, bases, namespace, **kwargs)


def _fail(message: str) -> NoReturn:
    raise RecursiveChildCandidateGenerationError(message)


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


@dataclass(frozen=True, slots=True, eq=False)
class ChildCandidateGenerationConfig(metaclass=_SealedChildType):
    max_requirements_processed: int
    max_total_child_windows: int
    max_pivots_per_child_window: int
    max_child_candidate_span_pivots: int
    max_child_skipped_pivots: int
    max_child_candidates_per_requirement: int
    max_total_child_candidates: int
    allowed_child_candidate_shapes: tuple[CandidateHypothesisShape, ...]
    max_requirements_with_finer_selection: int = 100_000
    max_total_finer_geometric_pivots: int = 1_000_000
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        for name, value, maximum in (
            ("max_requirements_processed", self.max_requirements_processed, _MAX_REQUIREMENTS),
            ("max_total_child_windows", self.max_total_child_windows, _MAX_WINDOWS),
            ("max_pivots_per_child_window", self.max_pivots_per_child_window, 10_000),
            ("max_child_candidate_span_pivots", self.max_child_candidate_span_pivots, 10_000),
            ("max_child_candidates_per_requirement", self.max_child_candidates_per_requirement, 100_000),
            ("max_total_child_candidates", self.max_total_child_candidates, _MAX_TOTAL_CANDIDATES),
            ("max_requirements_with_finer_selection", self.max_requirements_with_finer_selection, _MAX_REQUIREMENTS),
            ("max_total_finer_geometric_pivots", self.max_total_finer_geometric_pivots, 1_000_000),
        ):
            if type(value) is not int or not 1 <= value <= maximum:
                _fail(f"{name} must be one exact integer within [1, {maximum}].")
        if (
            type(self.max_child_skipped_pivots) is not int
            or not 0 <= self.max_child_skipped_pivots <= 10_000
        ):
            _fail("max_child_skipped_pivots must be one exact integer within [0, 10000].")
        if self.max_child_candidate_span_pivots > self.max_pivots_per_child_window:
            _fail("Child candidate span cannot exceed the per-window pivot bound.")
        if type(self.allowed_child_candidate_shapes) is not tuple or not self.allowed_child_candidate_shapes:
            _fail("allowed_child_candidate_shapes must be one non-empty exact tuple.")
        if any(type(item) is not CandidateHypothesisShape for item in self.allowed_child_candidate_shapes):
            _fail("Every allowed child shape must be one exact neutral shape.")
        if len(set(self.allowed_child_candidate_shapes)) != len(self.allowed_child_candidate_shapes):
            _fail("allowed_child_candidate_shapes cannot contain duplicates.")
        required = max(item.selected_pivot_count for item in self.allowed_child_candidate_shapes)
        if self.max_pivots_per_child_window < required or self.max_child_candidate_span_pivots < required:
            _fail("Child pivot and span bounds must accommodate every allowed neutral shape.")
        object.__setattr__(self, "_snapshot", tuple(
            getattr(self, name) for name in self.__dataclass_fields__ if name != "_snapshot"
        ))

    def _validated(self):
        if type(self) is not ChildCandidateGenerationConfig:
            _fail("Child generation config must have its exact type.")
        current = tuple(getattr(self, name) for name in self.__dataclass_fields__ if name != "_snapshot")
        if current != self._snapshot:
            _fail("Child generation config changed after construction.")
        return self


@dataclass(frozen=True, slots=True, eq=False)
class ProposedChildEvaluationWindow(metaclass=_SealedChildType):
    internal_requirement: FamilyInternalSubdivisionRequirement
    source_pivot_result: GeometricPivotDiscoveryResult
    start_pivot: GeometricPivotObservation
    end_pivot: GeometricPivotObservation
    ordered_interval_pivots: tuple[GeometricPivotObservation, ...]
    provenance_refs: tuple[str, ...]
    elliott_endpoint_authority: bool = False
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if type(self.internal_requirement) is not FamilyInternalSubdivisionRequirement:
            _fail("Window requires one exact internal requirement.")
        self.internal_requirement.__post_init__()
        candidate = self.internal_requirement.parent_candidate
        selected = candidate.ordered_selected_pivots
        expected_start = selected[self.internal_requirement.child_index]
        expected_end = selected[self.internal_requirement.child_index + 1]
        if self.start_pivot is not expected_start or self.end_pivot is not expected_end:
            _fail("Window boundaries differ from exact parent candidate pivot identities.")
        if self.source_pivot_result is not candidate.source_geometric_pivots:
            _fail("Window lost exact parent geometric-result ancestry.")
        if self.start_pivot.timestamp_utc >= self.end_pivot.timestamp_utc:
            _fail("Proposed child window must be strictly chronological.")
        expected = tuple(
            pivot for pivot in self.source_pivot_result.pivots
            if self.start_pivot.timestamp_utc <= pivot.timestamp_utc <= self.end_pivot.timestamp_utc
        )
        if len(expected) != len(self.ordered_interval_pivots) or any(
            observed is not reference
            for observed, reference in zip(self.ordered_interval_pivots, expected, strict=True)
        ):
            _fail("Window must include every and only exact source pivot inside inclusive boundaries.")
        if not expected or expected[0] is not self.start_pivot or expected[-1] is not self.end_pivot:
            _fail("Inclusive window must retain both exact boundary pivots.")
        if self.elliott_endpoint_authority is not False:
            _fail("A proposed child window cannot carry Elliott endpoint authority.")
        _refs(self.provenance_refs)
        object.__setattr__(self, "_snapshot", tuple(
            getattr(self, name) for name in self.__dataclass_fields__ if name != "_snapshot"
        ))

    def _validated(self):
        if type(self) is not ProposedChildEvaluationWindow:
            _fail("Child window must have its exact type.")
        current = tuple(getattr(self, name) for name in self.__dataclass_fields__ if name != "_snapshot")
        if len(current) != len(self._snapshot) or any(
            observed is not expected for observed, expected in zip(current, self._snapshot, strict=True)
        ):
            _fail("Child window changed after construction.")
        self.internal_requirement.__post_init__()
        return self


@dataclass(frozen=True, slots=True, eq=False)
class GeneratedChildCandidateEvidence(metaclass=_SealedChildType):
    internal_requirement: FamilyInternalSubdivisionRequirement
    evaluation_window: ProposedChildEvaluationWindow
    candidate_generation_result: CandidateGenerationResult
    competing_candidate_set: CompetingCandidateSetResult
    provenance_refs: tuple[str, ...]
    validated_child_wave: bool = False
    validated_internal_family: bool = False
    requirement_satisfied: bool = False
    degree_authority: bool = False
    finer_observation_selection: object | None = None
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if type(self.internal_requirement) is not FamilyInternalSubdivisionRequirement:
            _fail("Generated evidence requires one exact internal requirement.")
        self.internal_requirement.__post_init__()
        if type(self.evaluation_window) is not ProposedChildEvaluationWindow:
            _fail("Generated evidence requires one exact child window.")
        self.evaluation_window._validated()
        if self.evaluation_window.internal_requirement is not self.internal_requirement:
            _fail("Generated evidence and window requirement identities differ.")
        generation = validate_candidate_generation_result(self.candidate_generation_result)
        candidates = validate_competing_candidate_set_result(self.competing_candidate_set)
        if candidates.candidate_generation_result is not generation:
            _fail("Competing child set lost exact generation-result identity.")
        if generation.request.subject is not self.internal_requirement.child_subject:
            _fail("Child generation belongs to another subject identity.")
        if self.finer_observation_selection is None:
            if generation.request.scoped_pivots is not self.evaluation_window.ordered_interval_pivots:
                _fail("Child generation lost exact interval-pivot tuple identity.")
        else:
            from .finer_child_observation_selection import (
                ChildObservationCoverageState,
                ChildObservationSelectionResult,
                validate_child_observation_selection_result,
            )
            if type(self.finer_observation_selection) is not ChildObservationSelectionResult:
                _fail("Finer child evidence requires one exact selection result.")
            selection = validate_child_observation_selection_result(
                self.finer_observation_selection
            )
            if (
                selection.request.internal_requirement is not self.internal_requirement
                or selection.request.proposed_child_window is not self.evaluation_window
                or selection.selected_window.coverage_state
                is not ChildObservationCoverageState.FULL_WINDOW_COVERAGE
                or generation.request.observations is not selection.request.selected_observations
                or generation.request.geometric_pivots is not selection.finer_geometric_pivots
                or generation.request.scoped_pivots is not selection.finer_geometric_pivots.pivots
            ):
                _fail("Finer child evidence lost exact selection ancestry or full coverage.")
        if any((self.validated_child_wave, self.validated_internal_family, self.requirement_satisfied, self.degree_authority)):
            _fail("Neutral child evidence cannot carry wave, family, satisfaction, or degree authority.")
        _refs(self.provenance_refs)
        object.__setattr__(self, "_snapshot", tuple(
            getattr(self, name) for name in self.__dataclass_fields__ if name != "_snapshot"
        ))

    def _validated(self):
        if type(self) is not GeneratedChildCandidateEvidence:
            _fail("Generated child evidence must have its exact type.")
        current = tuple(getattr(self, name) for name in self.__dataclass_fields__ if name != "_snapshot")
        if len(current) != len(self._snapshot) or any(
            observed is not expected for observed, expected in zip(current, self._snapshot, strict=True)
        ):
            _fail("Generated child evidence changed after construction.")
        self.evaluation_window._validated()
        validate_candidate_generation_result(self.candidate_generation_result)
        validate_competing_candidate_set_result(self.competing_candidate_set)
        return self


@dataclass(frozen=True, slots=True, eq=False)
class ChildRequirementGenerationOutcome(metaclass=_SealedChildType):
    internal_requirement: FamilyInternalSubdivisionRequirement
    evaluation_window: ProposedChildEvaluationWindow
    status: ChildRequirementGenerationStatus
    generated_evidence: GeneratedChildCandidateEvidence | None
    diagnostic: str
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if type(self.internal_requirement) is not FamilyInternalSubdivisionRequirement:
            _fail("Outcome requires one exact internal requirement.")
        self.internal_requirement.__post_init__()
        if type(self.evaluation_window) is not ProposedChildEvaluationWindow:
            _fail("Outcome requires one exact child window.")
        self.evaluation_window._validated()
        if self.evaluation_window.internal_requirement is not self.internal_requirement:
            _fail("Outcome and window requirement identities differ.")
        if type(self.status) is not ChildRequirementGenerationStatus:
            _fail("Outcome status has an unexpected type.")
        if self.status in (
            ChildRequirementGenerationStatus.NEUTRAL_CHILD_CANDIDATE_EVIDENCE_AVAILABLE,
            ChildRequirementGenerationStatus.FINER_RESOLUTION_NEUTRAL_CHILD_EVIDENCE_AVAILABLE,
        ):
            if type(self.generated_evidence) is not GeneratedChildCandidateEvidence:
                _fail("Available status requires exact generated child evidence.")
            self.generated_evidence._validated()
        elif self.generated_evidence is not None:
            _fail("Insufficient status cannot carry generated evidence.")
        _text(self.diagnostic, "diagnostic")
        current = (
            self.internal_requirement,
            self.evaluation_window,
            self.status,
            self.generated_evidence,
            self.diagnostic,
        )
        if hasattr(self, "_snapshot"):
            if len(current) != len(self._snapshot) or any(
                observed is not expected
                for observed, expected in zip(current, self._snapshot, strict=True)
            ):
                _fail("Child requirement outcome changed after construction.")
        else:
            object.__setattr__(self, "_snapshot", current)


@dataclass(frozen=True, slots=True, eq=False)
class ChildCandidateGenerationDiagnostic(metaclass=_SealedChildType):
    code: ChildCandidateGenerationDiagnosticCode
    count: int
    detail: str
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if type(self.code) is not ChildCandidateGenerationDiagnosticCode:
            _fail("Diagnostic code has an unexpected type.")
        if type(self.count) is not int or self.count < 0:
            _fail("Diagnostic count must be one non-negative integer.")
        _text(self.detail, "diagnostic detail")
        current = (self.code, self.count, self.detail)
        if hasattr(self, "_snapshot"):
            if len(current) != len(self._snapshot) or any(
                observed is not expected
                for observed, expected in zip(current, self._snapshot, strict=True)
            ):
                _fail("Child-generation diagnostic changed after construction.")
        else:
            object.__setattr__(self, "_snapshot", current)


@dataclass(frozen=True, slots=True, eq=False)
class RecursiveChildCandidateGenerationRequest(metaclass=_SealedChildType):
    request_id: str
    requested_at_utc: str
    internal_subdivision_result: FamilyInternalSubdivisionEvaluationResult
    config: ChildCandidateGenerationConfig
    provenance_refs: tuple[str, ...]
    finer_observation_selections: tuple[object, ...] = ()
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        _text(self.request_id, "request_id")
        _text(self.requested_at_utc, "requested_at_utc")
        validate_family_internal_subdivision_evaluation_result(self.internal_subdivision_result)
        if type(self.config) is not ChildCandidateGenerationConfig:
            _fail("Request config must have its exact type.")
        self.config._validated()
        _refs(self.provenance_refs)
        if type(self.finer_observation_selections) is not tuple:
            _fail("finer_observation_selections must be one exact tuple.")
        from .finer_child_observation_selection import (
            ChildObservationSelectionResult,
            validate_child_observation_selection_result,
        )
        seen_requirements: set[int] = set()
        for selection in self.finer_observation_selections:
            if type(selection) is not ChildObservationSelectionResult:
                _fail("Every finer observation selection must have its exact result type.")
            validate_child_observation_selection_result(selection)
            requirement = selection.request.internal_requirement
            if not any(requirement is item for item in self.internal_subdivision_result.internal_requirements):
                _fail("A finer selection belongs to a foreign internal requirement.")
            if requirement.supplied_child_evidence is not None:
                _fail("A finer selection cannot replace already supplied child evidence.")
            if id(requirement) in seen_requirements:
                _fail("Only one explicit finer observation selection is allowed per requirement.")
            seen_requirements.add(id(requirement))
        object.__setattr__(self, "_snapshot", (
            self.request_id, self.requested_at_utc, self.internal_subdivision_result,
            self.config, self.provenance_refs, self.finer_observation_selections,
        ))

    def _validated(self):
        if type(self) is not RecursiveChildCandidateGenerationRequest:
            _fail("Child-generation request must have its exact type.")
        current = (self.request_id, self.requested_at_utc, self.internal_subdivision_result, self.config, self.provenance_refs, self.finer_observation_selections)
        if len(current) != len(self._snapshot) or any(
            observed is not expected for observed, expected in zip(current, self._snapshot, strict=True)
        ):
            _fail("Child-generation request changed after construction.")
        validate_family_internal_subdivision_evaluation_result(self.internal_subdivision_result)
        self.config._validated()
        return self


@dataclass(frozen=True, slots=True, eq=False, init=False, weakref_slot=True)
class RecursiveChildCandidateGenerationResult(metaclass=_SealedChildType):
    request: RecursiveChildCandidateGenerationRequest
    processed_requirements: tuple[FamilyInternalSubdivisionRequirement, ...]
    evaluation_windows: tuple[ProposedChildEvaluationWindow, ...]
    requirement_outcomes: tuple[ChildRequirementGenerationOutcome, ...]
    generated_child_evidence: tuple[GeneratedChildCandidateEvidence, ...]
    requirements_still_missing_evidence: tuple[FamilyInternalSubdivisionRequirement, ...]
    integrated_internal_subdivision_result: FamilyInternalSubdivisionEvaluationResult
    diagnostics: tuple[ChildCandidateGenerationDiagnostic, ...]
    provenance_refs: tuple[str, ...]
    _snapshot: tuple[object, ...]

    def __init__(self, *args, **kwargs):
        raise TypeError("Recursive child-generation results are factory-only.")

    def _validated(self):
        if type(self) is not RecursiveChildCandidateGenerationResult:
            _fail("Child-generation result must have its exact type.")
        issued = _ISSUED_RESULTS.get(self)
        current = tuple(getattr(self, name) for name in self.__dataclass_fields__ if name != "_snapshot")
        if issued is None or len(current) != len(self._snapshot) or any(
            observed is not expected for observed, expected in zip(current, self._snapshot, strict=True)
        ):
            _fail("Child-generation result is unissued or changed after creation.")
        self.request._validated()
        if len(issued) != len(self.requirement_outcomes) or any(
            observed is not expected for observed, expected in zip(self.requirement_outcomes, issued, strict=True)
        ):
            _fail("Child-generation outcome issuance changed.")
        expected_processed = tuple(
            requirement
            for requirement in self.request.internal_subdivision_result.internal_requirements
            if requirement.supplied_child_evidence is None
        )
        if len(self.processed_requirements) != len(expected_processed) or any(
            observed is not expected
            for observed, expected in zip(
                self.processed_requirements,
                expected_processed,
                strict=True,
            )
        ):
            _fail("Processed requirement identity or order changed.")
        if (
            len(self.evaluation_windows) != len(self.processed_requirements)
            or len(self.requirement_outcomes) != len(self.processed_requirements)
        ):
            _fail("Requirement, window, and outcome counts differ.")
        for requirement, window, outcome in zip(
            self.processed_requirements,
            self.evaluation_windows,
            self.requirement_outcomes,
            strict=True,
        ):
            window._validated()
            outcome.__post_init__()
            if (
                window.internal_requirement is not requirement
                or outcome.internal_requirement is not requirement
                or outcome.evaluation_window is not window
            ):
                _fail("Requirement, window, and outcome identities differ.")
        expected_generated = tuple(
            outcome.generated_evidence
            for outcome in self.requirement_outcomes
            if outcome.generated_evidence is not None
        )
        if len(self.generated_child_evidence) != len(expected_generated) or any(
            observed is not expected
            for observed, expected in zip(
                self.generated_child_evidence,
                expected_generated,
                strict=True,
            )
        ):
            _fail("Generated child evidence view changed.")
        for evidence in self.generated_child_evidence:
            evidence._validated()
        expected_missing = tuple(
            outcome.internal_requirement
            for outcome in self.requirement_outcomes
            if outcome.generated_evidence is None
        )
        if len(self.requirements_still_missing_evidence) != len(expected_missing) or any(
            observed is not expected
            for observed, expected in zip(
                self.requirements_still_missing_evidence,
                expected_missing,
                strict=True,
            )
        ):
            _fail("Missing-evidence requirement view changed.")
        validate_family_internal_subdivision_evaluation_result(self.integrated_internal_subdivision_result)
        if (
            self.integrated_internal_subdivision_result.family_hypothesis_result
            is not self.request.internal_subdivision_result.family_hypothesis_result
        ):
            _fail("Integrated internal result lost exact family-bridge ancestry.")
        if type(self.diagnostics) is not tuple or any(
            type(item) is not ChildCandidateGenerationDiagnostic
            for item in self.diagnostics
        ):
            _fail("Child-generation diagnostics have an unexpected type.")
        for diagnostic in self.diagnostics:
            diagnostic.__post_init__()
        _refs(self.provenance_refs)
        return self


_ISSUED_RESULTS: weakref.WeakKeyDictionary[
    RecursiveChildCandidateGenerationResult,
    tuple[ChildRequirementGenerationOutcome, ...],
] = weakref.WeakKeyDictionary()


def _window(requirement: FamilyInternalSubdivisionRequirement, refs: tuple[str, ...]) -> ProposedChildEvaluationWindow:
    candidate = requirement.parent_candidate
    start = candidate.ordered_selected_pivots[requirement.child_index]
    end = candidate.ordered_selected_pivots[requirement.child_index + 1]
    interval = tuple(
        pivot for pivot in candidate.source_geometric_pivots.pivots
        if start.timestamp_utc <= pivot.timestamp_utc <= end.timestamp_utc
    )
    return ProposedChildEvaluationWindow(
        requirement, candidate.source_geometric_pivots, start, end, interval,
        refs + requirement.provenance_refs + ("inclusive-child-window",),
    )


def _candidate_config(config: ChildCandidateGenerationConfig) -> CandidateGenerationConfig:
    return CandidateGenerationConfig(
        config.max_pivots_per_child_window,
        config.max_child_candidate_span_pivots,
        config.max_child_skipped_pivots,
        config.max_child_candidates_per_requirement,
        config.allowed_child_candidate_shapes,
        CandidatePivotWindow.EARLIEST,
    )


def generate_child_candidate_evidence(
    request: RecursiveChildCandidateGenerationRequest,
) -> RecursiveChildCandidateGenerationResult:
    """Generate exactly one bounded same-timeframe neutral child layer."""

    if type(request) is not RecursiveChildCandidateGenerationRequest:
        _fail("generate_child_candidate_evidence requires one exact request.")
    request._validated()
    source = request.internal_subdivision_result
    pending = tuple(
        requirement for requirement in source.internal_requirements
        if requirement.supplied_child_evidence is None
    )
    if len(pending) > request.config.max_requirements_processed:
        raise RecursiveChildCandidateGenerationLimitExceeded(
            "CHILD_GENERATION_BOUND_EXCEEDED: max_requirements_processed; no child candidates were materialized."
        )
    if len(pending) > request.config.max_total_child_windows:
        raise RecursiveChildCandidateGenerationLimitExceeded(
            "CHILD_GENERATION_BOUND_EXCEEDED: max_total_child_windows; no child candidates were materialized."
        )
    selection_by_requirement = {
        id(selection.request.internal_requirement): selection
        for selection in request.finer_observation_selections
    }
    if len(selection_by_requirement) > request.config.max_requirements_with_finer_selection:
        raise RecursiveChildCandidateGenerationLimitExceeded(
            "CHILD_GENERATION_BOUND_EXCEEDED: max_requirements_with_finer_selection; no child candidates were materialized."
        )
    windows = tuple(
        selection_by_requirement[id(item)].request.proposed_child_window
        if id(item) in selection_by_requirement
        else _window(item, request.provenance_refs)
        for item in pending
    )
    if any(
        len(window.ordered_interval_pivots) > request.config.max_pivots_per_child_window
        for window in windows
        if id(window.internal_requirement) not in selection_by_requirement
    ):
        raise RecursiveChildCandidateGenerationLimitExceeded(
            "CHILD_GENERATION_BOUND_EXCEEDED: max_pivots_per_child_window; no child candidates were materialized."
        )
    finer_pivot_total = sum(
        0 if selection.finer_geometric_pivots is None else len(selection.finer_geometric_pivots.pivots)
        for selection in request.finer_observation_selections
    )
    if finer_pivot_total > request.config.max_total_finer_geometric_pivots:
        raise RecursiveChildCandidateGenerationLimitExceeded(
            "CHILD_GENERATION_BOUND_EXCEEDED: max_total_finer_geometric_pivots; no child candidates were materialized."
        )
    candidate_config = _candidate_config(request.config)
    demands = tuple(
        estimate_candidate_generation_demand(
            len(selection_by_requirement[id(window.internal_requirement)].finer_geometric_pivots.pivots)
            if (
                id(window.internal_requirement) in selection_by_requirement
                and selection_by_requirement[id(window.internal_requirement)].finer_geometric_pivots is not None
            )
            else (
                0
                if id(window.internal_requirement) in selection_by_requirement
                else len(window.ordered_interval_pivots)
            ),
            candidate_config,
        )[0]
        for window in windows
    )
    if any(count > request.config.max_child_candidates_per_requirement for count in demands):
        raise RecursiveChildCandidateGenerationLimitExceeded(
            "CHILD_GENERATION_BOUND_EXCEEDED: max_child_candidates_per_requirement; no child candidates were materialized."
        )
    if sum(demands) > request.config.max_total_child_candidates:
        raise RecursiveChildCandidateGenerationLimitExceeded(
            "CHILD_GENERATION_BOUND_EXCEEDED: max_total_child_candidates; no child candidates were materialized."
        )

    outcomes = []
    generated = []
    integration_evidence = tuple(
        requirement.supplied_child_evidence
        for requirement in source.internal_requirements
        if requirement.supplied_child_evidence is not None
    )
    new_integration = []
    for window, demand in zip(windows, demands, strict=True):
        requirement = window.internal_requirement
        selection = selection_by_requirement.get(id(requirement))
        if selection is not None and selection.finer_geometric_pivots is None:
            from .finer_child_observation_selection import ChildObservationCoverageState
            state = selection.selected_window.coverage_state
            status = (
                ChildRequirementGenerationStatus.PARTIAL_FINER_OBSERVATION_COVERAGE
                if state is ChildObservationCoverageState.PARTIAL_WINDOW_COVERAGE
                else ChildRequirementGenerationStatus.NO_FINER_OBSERVATION_COVERAGE
            )
            outcomes.append(ChildRequirementGenerationOutcome(
                requirement,
                window,
                status,
                None,
                "The explicit finer observation selection lacks full UTC-window coverage; no geometry or child candidates were created.",
            ))
            continue
        if demand == 0:
            outcomes.append(ChildRequirementGenerationOutcome(
                requirement, window,
                ChildRequirementGenerationStatus.INSUFFICIENT_GEOMETRIC_PIVOTS,
                None,
                "The inclusive child interval cannot form any allowed bounded neutral shape; the window was not expanded.",
            ))
            continue
        generation_observations = (
            requirement.parent_candidate.source_observations
            if selection is None
            else selection.request.selected_observations
        )
        generation_geometry = (
            requirement.parent_candidate.source_geometric_pivots
            if selection is None
            else selection.finer_geometric_pivots
        )
        generation_scope = (
            window.ordered_interval_pivots
            if selection is None
            else selection.finer_geometric_pivots.pivots
        )
        generation_request = CandidateGenerationRequest(
            request_id=f"{request.request_id}:{requirement.requirement_id}:neutral-children",
            requested_at_utc=request.requested_at_utc,
            subject=requirement.child_subject,
            observations=generation_observations,
            geometric_pivots=generation_geometry,
            config=candidate_config,
            methodology_delegations=(),
            provenance_refs=request.provenance_refs + requirement.provenance_refs + ("one-level-neutral-child-generation",),
            scoped_pivots=generation_scope,
        )
        generation = generate_candidate_hypotheses(generation_request)
        child_set = build_competing_candidate_set(CompetingCandidateSetRequest(
            f"{request.request_id}:{requirement.requirement_id}:competing-neutral-children",
            requirement.child_subject.subject_id,
            generation,
            request.provenance_refs + requirement.provenance_refs + ("unranked-child-set",),
        ))
        evidence = GeneratedChildCandidateEvidence(
            requirement, window, generation, child_set,
            request.provenance_refs + requirement.provenance_refs + ("neutral-child-evidence-available",),
            finer_observation_selection=selection,
        )
        generated.append(evidence)
        outcomes.append(ChildRequirementGenerationOutcome(
            requirement, window,
            (
                ChildRequirementGenerationStatus.NEUTRAL_CHILD_CANDIDATE_EVIDENCE_AVAILABLE
                if selection is None
                else ChildRequirementGenerationStatus.FINER_RESOLUTION_NEUTRAL_CHILD_EVIDENCE_AVAILABLE
            ),
            evidence,
            "Neutral child candidates exist; the internal-family requirement remains unresolved.",
        ))
        node = BoundedRecursiveAnalysisNode(
            requirement.child_subject,
            None,
            (),
            BoundedRecursiveAnalysisResolution(
                requirement.child_subject,
                AnalysisResolutionState.CURRENT_SUPPLIED_SCOPE_UNRESOLVED,
                "Neutral child candidate evidence is available but supplies no validated-family proof.",
                provenance_refs=evidence.provenance_refs + (SOURCE_DERIVED_BASE_CASE_NOT_FOUND,),
            ),
        )
        new_integration.append(FamilyChildCandidateEvidence(
            requirement.family_hypothesis,
            requirement.child_index,
            requirement.child_subject,
            node,
            evidence.provenance_refs,
        ))
    all_integration = integration_evidence + tuple(new_integration)
    integrated = evaluate_family_internal_subdivisions(
        FamilyInternalSubdivisionEvaluationRequest(
            f"{request.request_id}:integrated-internal-review",
            source.family_hypothesis_result,
            all_integration,
            request.provenance_refs + ("neutral-child-evidence-integration",),
        )
    )
    outcomes_tuple = tuple(outcomes)
    generated_tuple = tuple(generated)
    missing = tuple(
        item.internal_requirement for item in outcomes_tuple
        if item.generated_evidence is None
    )
    developing = sum(
        any(
            pivot.state is GeometricPivotState.DEVELOPING
            for pivot in (
                window.ordered_interval_pivots
                if id(window.internal_requirement) not in selection_by_requirement
                or selection_by_requirement[id(window.internal_requirement)].finer_geometric_pivots is None
                else selection_by_requirement[id(window.internal_requirement)].finer_geometric_pivots.pivots
            )
        )
        for window in windows
    )
    finer_coverage_failures = sum(
        selection.finer_geometric_pivots is None
        for selection in request.finer_observation_selections
    )
    diagnostics = tuple(
        ChildCandidateGenerationDiagnostic(code, count, detail)
        for code, count, detail in (
            (ChildCandidateGenerationDiagnosticCode.REQUIREMENTS_PROCESSED, len(pending), "Exact missing-evidence requirements processed once."),
            (ChildCandidateGenerationDiagnosticCode.CHILD_WINDOWS_CREATED, len(windows), "Inclusive exact-pivot transport windows created."),
            (ChildCandidateGenerationDiagnosticCode.SUFFICIENT_INTERVAL_PIVOTS, len(generated_tuple), "Windows supporting at least one neutral child candidate set."),
            (ChildCandidateGenerationDiagnosticCode.INSUFFICIENT_INTERVAL_PIVOTS, len(missing), "Windows left unresolved without expansion."),
            (ChildCandidateGenerationDiagnosticCode.NEUTRAL_CHILD_EVIDENCE_CREATED, len(generated_tuple), "Evidence availability only; no requirement satisfaction."),
            (ChildCandidateGenerationDiagnosticCode.NEUTRAL_CHILD_CANDIDATES_CREATED, sum(len(item.candidate_generation_result.candidates) for item in generated_tuple), "Neutral candidates retained without family, degree, or rank."),
            (ChildCandidateGenerationDiagnosticCode.DEVELOPING_WINDOWS_PRESENT, developing, "Developing geometric status retained without confirmation."),
            (ChildCandidateGenerationDiagnosticCode.BASE_CASE_REMAINS_BLOCKED, len(generated_tuple), SOURCE_DERIVED_BASE_CASE_NOT_FOUND),
            (ChildCandidateGenerationDiagnosticCode.FINER_SELECTIONS_APPLIED, len(request.finer_observation_selections), "Exact caller-supplied finer observation selections applied without degree inference."),
            (ChildCandidateGenerationDiagnosticCode.FINER_COVERAGE_FAILURES, finer_coverage_failures, "Partial/no coverage remained infrastructure-unresolved without structural invalidity."),
        )
    )
    values = {
        "request": request,
        "processed_requirements": pending,
        "evaluation_windows": windows,
        "requirement_outcomes": outcomes_tuple,
        "generated_child_evidence": generated_tuple,
        "requirements_still_missing_evidence": missing,
        "integrated_internal_subdivision_result": integrated,
        "diagnostics": diagnostics,
        "provenance_refs": request.provenance_refs,
    }
    result = object.__new__(RecursiveChildCandidateGenerationResult)
    for name, value in values.items():
        object.__setattr__(result, name, value)
    object.__setattr__(result, "_snapshot", tuple(values.values()))
    _ISSUED_RESULTS[result] = outcomes_tuple
    return result._validated()


__all__ = [
    "ARTIFACT_CLASSIFICATION",
    "BOUND_CLASSIFICATION",
    "CHILD_CANDIDATE_IS_NOT_VALIDATED_CHILD_WAVE",
    "CHILD_EVIDENCE_CLASSIFICATION",
    "EXACT_AUTOMATIC_CHILD_LEVELS",
    "FINER_TIMEFRAME_IS_NOT_LOWER_DEGREE",
    "MORE_CHILD_EVIDENCE_IS_NOT_FAMILY_VALIDITY",
    "RECURSIVE_DEPTH_IS_NOT_DEGREE",
    "WINDOW_CLASSIFICATION",
    "WINDOW_IS_NOT_ELLIOTT_ENDPOINT_AUTHORITY",
    "ChildCandidateGenerationConfig",
    "ChildCandidateGenerationDiagnostic",
    "ChildCandidateGenerationDiagnosticCode",
    "ChildRequirementGenerationOutcome",
    "ChildRequirementGenerationStatus",
    "GeneratedChildCandidateEvidence",
    "ProposedChildEvaluationWindow",
    "RecursiveChildCandidateGenerationError",
    "RecursiveChildCandidateGenerationLimitExceeded",
    "RecursiveChildCandidateGenerationRequest",
    "RecursiveChildCandidateGenerationResult",
    "generate_child_candidate_evidence",
]
