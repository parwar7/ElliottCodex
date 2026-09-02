"""Direct-child cardinality for an explicitly proposed ending diagonal."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ._structural_invalidity_certification import (
    StructuralValidatorResult,
    _register_structural_validator,
)
from .models import SourceClassification
from .subject_binding import OrderedChildBinding


ENDING_DIAGONAL_BEHAVIOR_ID = "ENDING_DIAGONAL_DIRECT_CHILD_CARDINALITY"
ENDING_DIAGONAL_PROTECTED_SOURCES = (
    "docs/elliott/PATTERN_BRAIN.md#D-ending-diagonal",
    "docs/elliott/MASTER_PROTOCOL.md#step-4",
    "docs/elliott/MASTER_PROTOCOL.md#step-5",
    "Sources_LOCKED/volume_03/volume_03.srt@00:13:18.990-00:13:30.710",
)


class EndingDiagonalCandidateScope(StrEnum):
    ENDING_DIAGONAL = "ENDING_DIAGONAL"


class EndingDiagonalExecutionRole(StrEnum):
    HARD_VALIDATION = "HARD_VALIDATION"


class EndingDiagonalCardinalityStatus(StrEnum):
    CARDINALITY_SATISFIED = "CARDINALITY_SATISFIED"
    CARDINALITY_VIOLATED = "CARDINALITY_VIOLATED"
    UNRESOLVED_MISSING_INPUT = "UNRESOLVED_MISSING_INPUT"
    UNRESOLVED_UNSUPPORTED_SCOPE = "UNRESOLVED_UNSUPPORTED_SCOPE"


@dataclass(frozen=True, slots=True)
class EndingDiagonalCardinalityInput:
    candidate_scope: EndingDiagonalCandidateScope | str | None
    binding: OrderedChildBinding | None


@dataclass(frozen=True, slots=True, weakref_slot=True)
class EndingDiagonalCardinalityResult(StructuralValidatorResult):
    status: EndingDiagonalCardinalityStatus
    source_principle_id: None
    source_class: SourceClassification
    execution_role: EndingDiagonalExecutionRole
    protected_sources: tuple[str, ...]
    behavior_id: str
    outcome: str
    reason: str
    fatal_to_candidate: bool
    binding: OrderedChildBinding | None


_ENDING_DIAGONAL_STRUCTURAL_INVALIDITY_ISSUER = _register_structural_validator(
    EndingDiagonalCardinalityResult,
    violation_statuses=(EndingDiagonalCardinalityStatus.CARDINALITY_VIOLATED,),
    hard_validation_role=EndingDiagonalExecutionRole.HARD_VALIDATION,
    principle_attribute="source_principle_id",
    behavior_id=ENDING_DIAGONAL_BEHAVIOR_ID,
    principle_id=None,
    source_class=SourceClassification.DEFINITION,
    protected_sources=ENDING_DIAGONAL_PROTECTED_SOURCES,
)


def _result(
    status: EndingDiagonalCardinalityStatus,
    reason: str,
    *,
    binding: OrderedChildBinding | None = None,
    fatal_to_candidate: bool = False,
) -> EndingDiagonalCardinalityResult:
    return EndingDiagonalCardinalityResult(
        status=status,
        source_principle_id=None,
        source_class=SourceClassification.DEFINITION,
        execution_role=EndingDiagonalExecutionRole.HARD_VALIDATION,
        protected_sources=ENDING_DIAGONAL_PROTECTED_SOURCES,
        behavior_id=ENDING_DIAGONAL_BEHAVIOR_ID,
        outcome=status.value,
        reason=reason,
        fatal_to_candidate=fatal_to_candidate,
        binding=binding,
    )


def _is_supported_scope(value: object) -> bool:
    return value is EndingDiagonalCandidateScope.ENDING_DIAGONAL or (
        type(value) is str
        and str.__eq__(value, EndingDiagonalCandidateScope.ENDING_DIAGONAL.value)
        is True
    )


def check_ending_diagonal_cardinality(
    candidate: object,
) -> EndingDiagonalCardinalityResult:
    """Check only exact direct-child cardinality; establish nothing broader."""
    if type(candidate) is not EndingDiagonalCardinalityInput:
        return _result(
            EndingDiagonalCardinalityStatus.UNRESOLVED_MISSING_INPUT,
            "Ending-diagonal cardinality requires one exact behavior-local input.",
        )

    candidate_scope = candidate.candidate_scope
    if candidate_scope is None:
        return _result(
            EndingDiagonalCardinalityStatus.UNRESOLVED_MISSING_INPUT,
            "Ending-diagonal cardinality requires an explicit ENDING_DIAGONAL scope.",
        )
    if not _is_supported_scope(candidate_scope):
        return _result(
            EndingDiagonalCardinalityStatus.UNRESOLVED_UNSUPPORTED_SCOPE,
            "Ending-diagonal cardinality supports only the exact ENDING_DIAGONAL scope.",
        )

    binding = candidate.binding
    if type(binding) is not OrderedChildBinding:
        return _result(
            EndingDiagonalCardinalityStatus.UNRESOLVED_MISSING_INPUT,
            "Ending-diagonal cardinality requires one exact OrderedChildBinding.",
        )

    if len(binding.ordered_children) != 5:
        return _ENDING_DIAGONAL_STRUCTURAL_INVALIDITY_ISSUER.issue(
            _result(
                EndingDiagonalCardinalityStatus.CARDINALITY_VIOLATED,
                "The supplied proposed ending diagonal does not contain exactly five direct ordered children.",
                binding=binding,
                fatal_to_candidate=True,
            )
        )

    return _result(
        EndingDiagonalCardinalityStatus.CARDINALITY_SATISFIED,
        "The supplied proposed ending diagonal contains exactly five direct ordered children; no child family, wave label, geometry, overlap, convergence, position, completion, degree, leading-diagonal, or broader pattern validity is established.",
        binding=binding,
    )


__all__ = [
    "EndingDiagonalCandidateScope",
    "EndingDiagonalCardinalityInput",
    "EndingDiagonalCardinalityResult",
    "EndingDiagonalCardinalityStatus",
    "EndingDiagonalExecutionRole",
    "check_ending_diagonal_cardinality",
]
