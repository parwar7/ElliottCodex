"""Immutable neutral snapshot containing candidates from one generation run.

Membership, order, and active-view inclusion are project analysis
infrastructure.  They create no Elliott validity, family, degree, rank,
evidence, forecast, or trading authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import NoReturn
import weakref

from elliott_methodology_kernel.contracts import NormalizedMarketObservations

from .candidate_generation import (
    CandidateGenerationResult,
    GeneratedCandidateHypothesis,
    GeneratedCandidateReviewState,
    validate_candidate_generation_result,
)
from elliott_runtime.market_data.geometric_pivots import GeometricPivotDiscoveryResult


ARTIFACT_CLASSIFICATION = "PROJECT_ANALYSIS_INFRASTRUCTURE"
MEMBERSHIP_CLASSIFICATION = "CALLER_OR_GENERATOR_SUPPLIED_CANDIDATE_MEMBERSHIP"
ORDERING_CLASSIFICATION = "PROJECT_OPERATIONAL_POLICY"
MEMBERSHIP_IS_NOT_VALIDITY = True
ACTIVE_IS_NOT_VALIDITY = True
CONTAINER_ORDER_IS_NOT_RANK = True
TIMEFRAME_IS_NOT_DEGREE = True


class CompetingCandidateSetError(ValueError):
    """Fail-closed competing-set contract error."""


class CandidateSetDiagnosticCode(StrEnum):
    CANDIDATE_SET_CREATED = "CANDIDATE_SET_CREATED"
    SINGLE_CANDIDATE_SET = "SINGLE_CANDIDATE_SET"
    MULTIPLE_CANDIDATES_RETAINED = "MULTIPLE_CANDIDATES_RETAINED"
    STRUCTURAL_INVALIDITY_PRESENT = "STRUCTURAL_INVALIDITY_PRESENT"
    UNRESOLVED_CANDIDATES_PRESENT = "UNRESOLVED_CANDIDATES_PRESENT"
    REVIEWED_SCOPE_CANDIDATES_PRESENT = "REVIEWED_SCOPE_CANDIDATES_PRESENT"
    NO_ACTIVE_CANDIDATES = "NO_ACTIVE_CANDIDATES"


class _SealedSetType(type):
    def __new__(
        mcls: type,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
        **kwargs: object,
    ) -> type:
        if any(isinstance(base, mcls) for base in bases):
            raise TypeError("Competing-candidate set infrastructure cannot be subclassed.")
        return super().__new__(mcls, name, bases, namespace, **kwargs)


def _fail(message: str) -> NoReturn:
    raise CompetingCandidateSetError(message)


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


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class CompetingCandidateSetRequest(metaclass=_SealedSetType):
    set_id: str
    analysis_scope_id: str
    candidate_generation_result: CandidateGenerationResult
    provenance_refs: tuple[str, ...]
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        _text(self.set_id, "set_id")
        _text(self.analysis_scope_id, "analysis_scope_id")
        generation = validate_candidate_generation_result(
            self.candidate_generation_result
        )
        if not generation.candidates:
            _fail("A competing candidate set requires at least one candidate.")
        _refs(self.provenance_refs)
        object.__setattr__(
            self,
            "_snapshot",
            (
                self.set_id,
                self.analysis_scope_id,
                self.candidate_generation_result,
                self.provenance_refs,
            ),
        )

    def _validated(self) -> CompetingCandidateSetRequest:
        if type(self) is not CompetingCandidateSetRequest:
            _fail("Competing-set request must have its exact reviewed type.")
        current = (
            self.set_id,
            self.analysis_scope_id,
            self.candidate_generation_result,
            self.provenance_refs,
        )
        if len(current) != len(self._snapshot) or any(
            observed is not expected
            for observed, expected in zip(current, self._snapshot, strict=True)
        ):
            _fail("Competing-set request changed after construction.")
        validate_candidate_generation_result(self.candidate_generation_result)
        _refs(self.provenance_refs)
        return self

    def __copy__(self) -> CompetingCandidateSetRequest:
        return self._validated()

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> CompetingCandidateSetRequest:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Competing-set requests cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False)
class CandidateSetStateInventory(metaclass=_SealedSetType):
    total_candidates: int
    structurally_invalid: int
    unresolved: int
    current_supplied_scope_reviewed: int
    active_candidates: int

    def __post_init__(self) -> None:
        values = (
            self.total_candidates,
            self.structurally_invalid,
            self.unresolved,
            self.current_supplied_scope_reviewed,
            self.active_candidates,
        )
        if any(type(value) is not int or value < 0 for value in values):
            _fail("Candidate inventory values must be exact non-negative integers.")
        if self.total_candidates != sum(values[1:4]):
            _fail("Candidate state inventory does not partition total membership.")
        if self.active_candidates != self.unresolved + self.current_supplied_scope_reviewed:
            _fail("Active inventory must include only unresolved and reviewed candidates.")


@dataclass(frozen=True, slots=True, eq=False)
class CandidateSetDiagnostic(metaclass=_SealedSetType):
    code: CandidateSetDiagnosticCode
    count: int
    detail: str

    def __post_init__(self) -> None:
        if type(self.code) is not CandidateSetDiagnosticCode:
            _fail("Candidate-set diagnostic code must have its exact reviewed type.")
        if type(self.count) is not int or self.count < 0:
            _fail("Candidate-set diagnostic count must be a non-negative exact integer.")
        _text(self.detail, "diagnostic detail")


@dataclass(frozen=True, slots=True, eq=False, init=False, weakref_slot=True)
class CompetingCandidateSetResult(metaclass=_SealedSetType):
    set_id: str
    analysis_scope_id: str
    source_observations: NormalizedMarketObservations
    geometric_pivot_result: GeometricPivotDiscoveryResult
    candidate_generation_result: CandidateGenerationResult
    ordered_candidates: tuple[GeneratedCandidateHypothesis, ...]
    candidate_state_inventory: CandidateSetStateInventory
    structurally_invalid_candidates: tuple[GeneratedCandidateHypothesis, ...]
    unresolved_candidates: tuple[GeneratedCandidateHypothesis, ...]
    reviewed_scope_candidates: tuple[GeneratedCandidateHypothesis, ...]
    active_candidates: tuple[GeneratedCandidateHypothesis, ...]
    diagnostics: tuple[CandidateSetDiagnostic, ...]
    provenance_refs: tuple[str, ...]
    _snapshot: tuple[object, ...]

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("Competing-set results are created only by the builder.")

    def _validated(self) -> CompetingCandidateSetResult:
        if type(self) is not CompetingCandidateSetResult:
            _fail("Competing-set result must have its exact reviewed type.")
        try:
            snapshot = object.__getattribute__(self, "_snapshot")
            issued = _ISSUED_SETS.get(self)
        except Exception as error:
            raise CompetingCandidateSetError("Competing-set result is malformed.") from error
        current = tuple(
            getattr(self, name)
            for name in self.__dataclass_fields__
            if name != "_snapshot"
        )
        if issued is None or len(current) != len(snapshot) or any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            _fail("Competing-set result is unissued or changed after creation.")
        validate_candidate_generation_result(self.candidate_generation_result)
        if (
            self.source_observations
            is not self.candidate_generation_result.input_observations
            or self.geometric_pivot_result
            is not self.candidate_generation_result.input_geometric_pivots
        ):
            _fail("Competing-set source ancestry changed.")
        if len(issued) != len(self.ordered_candidates) or any(
            observed is not expected
            for observed, expected in zip(self.ordered_candidates, issued, strict=True)
        ):
            _fail("Competing-set membership differs from the issued snapshot.")
        expected_invalid = tuple(
            item for item in self.ordered_candidates
            if item.review_state is GeneratedCandidateReviewState.STRUCTURALLY_INVALID
        )
        expected_unresolved = tuple(
            item for item in self.ordered_candidates
            if item.review_state is GeneratedCandidateReviewState.UNRESOLVED
        )
        expected_reviewed = tuple(
            item for item in self.ordered_candidates
            if item.review_state
            is GeneratedCandidateReviewState.CURRENT_SUPPLIED_SCOPE_REVIEWED
        )
        expected_active = tuple(
            item for item in self.ordered_candidates
            if item.review_state is not GeneratedCandidateReviewState.STRUCTURALLY_INVALID
        )
        for observed, expected, name in (
            (self.structurally_invalid_candidates, expected_invalid, "invalid"),
            (self.unresolved_candidates, expected_unresolved, "unresolved"),
            (self.reviewed_scope_candidates, expected_reviewed, "reviewed"),
            (self.active_candidates, expected_active, "active"),
        ):
            if len(observed) != len(expected) or any(
                item is not reference
                for item, reference in zip(observed, expected, strict=True)
            ):
                _fail(f"Competing-set {name} view changed.")
        inventory = self.candidate_state_inventory
        if type(inventory) is not CandidateSetStateInventory:
            _fail("Candidate inventory has an unexpected type.")
        inventory.__post_init__()
        expected_counts = (
            len(self.ordered_candidates),
            len(expected_invalid),
            len(expected_unresolved),
            len(expected_reviewed),
            len(expected_active),
        )
        observed_counts = tuple(
            getattr(inventory, name)
            for name in inventory.__dataclass_fields__
        )
        if observed_counts != expected_counts:
            _fail("Candidate inventory differs from exact membership views.")
        if type(self.diagnostics) is not tuple or any(
            type(item) is not CandidateSetDiagnostic for item in self.diagnostics
        ):
            _fail("Competing-set diagnostics have an unexpected type.")
        for diagnostic in self.diagnostics:
            diagnostic.__post_init__()
        _refs(self.provenance_refs)
        return self

    def __copy__(self) -> CompetingCandidateSetResult:
        return self._validated()

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> CompetingCandidateSetResult:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Competing-set results cannot be pickled.")


_ISSUED_SETS: weakref.WeakKeyDictionary[
    CompetingCandidateSetResult, tuple[GeneratedCandidateHypothesis, ...]
] = weakref.WeakKeyDictionary()


def _diagnostics(
    total: int,
    invalid: int,
    unresolved: int,
    reviewed: int,
    active: int,
) -> tuple[CandidateSetDiagnostic, ...]:
    items = [
        CandidateSetDiagnostic(
            CandidateSetDiagnosticCode.CANDIDATE_SET_CREATED,
            total,
            "Immutable candidate-membership snapshot created without ranking.",
        )
    ]
    if total == 1:
        items.append(CandidateSetDiagnostic(
            CandidateSetDiagnosticCode.SINGLE_CANDIDATE_SET,
            1,
            "One member is retained without preferred or confirmed status.",
        ))
    else:
        items.append(CandidateSetDiagnostic(
            CandidateSetDiagnosticCode.MULTIPLE_CANDIDATES_RETAINED,
            total,
            "Original generation order retained with zero rank meaning.",
        ))
    for count, code, detail in (
        (invalid, CandidateSetDiagnosticCode.STRUCTURAL_INVALIDITY_PRESENT, "Invalid members remain in historical membership."),
        (unresolved, CandidateSetDiagnosticCode.UNRESOLVED_CANDIDATES_PRESENT, "Unresolved members remain active."),
        (reviewed, CandidateSetDiagnosticCode.REVIEWED_SCOPE_CANDIDATES_PRESENT, "Reviewed means only current supplied scope reviewed."),
    ):
        if count:
            items.append(CandidateSetDiagnostic(code, count, detail))
    if active == 0:
        items.append(CandidateSetDiagnostic(
            CandidateSetDiagnosticCode.NO_ACTIVE_CANDIDATES,
            0,
            "All members are structurally invalid; no validity conclusion follows.",
        ))
    return tuple(items)


def build_competing_candidate_set(
    request: CompetingCandidateSetRequest,
) -> CompetingCandidateSetResult:
    """Build one immutable, unranked snapshot from one exact generation run."""

    if type(request) is not CompetingCandidateSetRequest:
        _fail("build_competing_candidate_set requires one exact request.")
    request._validated()
    generation = request.candidate_generation_result
    ordered = generation.candidates
    invalid = tuple(
        item for item in ordered
        if item.review_state is GeneratedCandidateReviewState.STRUCTURALLY_INVALID
    )
    unresolved = tuple(
        item for item in ordered
        if item.review_state is GeneratedCandidateReviewState.UNRESOLVED
    )
    reviewed = tuple(
        item for item in ordered
        if item.review_state
        is GeneratedCandidateReviewState.CURRENT_SUPPLIED_SCOPE_REVIEWED
    )
    active = tuple(
        item for item in ordered
        if item.review_state is not GeneratedCandidateReviewState.STRUCTURALLY_INVALID
    )
    inventory = CandidateSetStateInventory(
        len(ordered), len(invalid), len(unresolved), len(reviewed), len(active)
    )
    values = {
        "set_id": request.set_id,
        "analysis_scope_id": request.analysis_scope_id,
        "source_observations": generation.input_observations,
        "geometric_pivot_result": generation.input_geometric_pivots,
        "candidate_generation_result": generation,
        "ordered_candidates": ordered,
        "candidate_state_inventory": inventory,
        "structurally_invalid_candidates": invalid,
        "unresolved_candidates": unresolved,
        "reviewed_scope_candidates": reviewed,
        "active_candidates": active,
        "diagnostics": _diagnostics(
            len(ordered), len(invalid), len(unresolved), len(reviewed), len(active)
        ),
        "provenance_refs": request.provenance_refs,
    }
    result = object.__new__(CompetingCandidateSetResult)
    for name, value in values.items():
        object.__setattr__(result, name, value)
    object.__setattr__(result, "_snapshot", tuple(values.values()))
    _ISSUED_SETS[result] = ordered
    return result._validated()


__all__ = [
    "ACTIVE_IS_NOT_VALIDITY",
    "ARTIFACT_CLASSIFICATION",
    "CONTAINER_ORDER_IS_NOT_RANK",
    "MEMBERSHIP_CLASSIFICATION",
    "MEMBERSHIP_IS_NOT_VALIDITY",
    "ORDERING_CLASSIFICATION",
    "TIMEFRAME_IS_NOT_DEGREE",
    "CandidateSetDiagnostic",
    "CandidateSetDiagnosticCode",
    "CandidateSetStateInventory",
    "CompetingCandidateSetError",
    "CompetingCandidateSetRequest",
    "CompetingCandidateSetResult",
    "build_competing_candidate_set",
]
