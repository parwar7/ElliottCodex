"""P008 direct-child cardinality for an explicitly proposed flat."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ._structural_invalidity_certification import (
    StructuralValidatorResult,
    _register_structural_validator,
)
from .models import SourceClassification
from .subject_binding import OrderedChildBinding


P008_BEHAVIOR_ID = "P008_FLAT_DIRECT_CHILD_CARDINALITY"
P008_PRINCIPLE_ID = "P008"
P008_PROTECTED_SOURCES = (
    "docs/elliott/SOURCE_EVIDENCE_MAP.json#P008",
    "docs/elliott/PATTERN_BRAIN.md#G-flat-family",
    "docs/elliott/MASTER_PROTOCOL.md#step-4",
    "docs/elliott/MASTER_PROTOCOL.md#step-5",
    "Sources_LOCKED/volume_04/volume_04@00:14:43.830-00:15:30.450",
)


class P008CandidateScope(StrEnum):
    FLAT = "FLAT"


class P008ExecutionRole(StrEnum):
    HARD_VALIDATION = "HARD_VALIDATION"


class P008CardinalityStatus(StrEnum):
    CARDINALITY_SATISFIED = "CARDINALITY_SATISFIED"
    CARDINALITY_VIOLATED = "CARDINALITY_VIOLATED"
    UNRESOLVED_MISSING_INPUT = "UNRESOLVED_MISSING_INPUT"
    UNRESOLVED_UNSUPPORTED_SCOPE = "UNRESOLVED_UNSUPPORTED_SCOPE"


@dataclass(frozen=True, slots=True)
class P008FlatCardinalityInput:
    candidate_scope: P008CandidateScope | str | None
    binding: OrderedChildBinding | None


@dataclass(frozen=True, slots=True, weakref_slot=True)
class P008FlatCardinalityResult(StructuralValidatorResult):
    status: P008CardinalityStatus
    principle_id: str
    source_class: SourceClassification
    execution_role: P008ExecutionRole
    protected_sources: tuple[str, ...]
    behavior_id: str
    outcome: str
    reason: str
    fatal_to_candidate: bool
    binding: OrderedChildBinding | None


_P008_STRUCTURAL_INVALIDITY_ISSUER = _register_structural_validator(
    P008FlatCardinalityResult,
    violation_statuses=(P008CardinalityStatus.CARDINALITY_VIOLATED,),
    hard_validation_role=P008ExecutionRole.HARD_VALIDATION,
    principle_attribute="principle_id",
    behavior_id=P008_BEHAVIOR_ID,
    principle_id=P008_PRINCIPLE_ID,
    source_class=SourceClassification.DEFINITION,
    protected_sources=P008_PROTECTED_SOURCES,
)


def _result(
    status: P008CardinalityStatus,
    reason: str,
    *,
    binding: OrderedChildBinding | None = None,
    fatal_to_candidate: bool = False,
) -> P008FlatCardinalityResult:
    return P008FlatCardinalityResult(
        status=status,
        principle_id=P008_PRINCIPLE_ID,
        source_class=SourceClassification.DEFINITION,
        execution_role=P008ExecutionRole.HARD_VALIDATION,
        protected_sources=P008_PROTECTED_SOURCES,
        behavior_id=P008_BEHAVIOR_ID,
        outcome=status.value,
        reason=reason,
        fatal_to_candidate=fatal_to_candidate,
        binding=binding,
    )


def _is_supported_scope(value: object) -> bool:
    return value is P008CandidateScope.FLAT or (
        type(value) is str
        and str.__eq__(value, P008CandidateScope.FLAT.value) is True
    )


def check_p008_flat_cardinality(candidate: object) -> P008FlatCardinalityResult:
    """Check only exact direct-child cardinality; establish nothing broader."""
    if type(candidate) is not P008FlatCardinalityInput:
        return _result(
            P008CardinalityStatus.UNRESOLVED_MISSING_INPUT,
            "P008 cardinality requires one exact behavior-local input.",
        )

    candidate_scope = candidate.candidate_scope
    if candidate_scope is None:
        return _result(
            P008CardinalityStatus.UNRESOLVED_MISSING_INPUT,
            "P008 cardinality requires an explicit FLAT scope.",
        )
    if not _is_supported_scope(candidate_scope):
        return _result(
            P008CardinalityStatus.UNRESOLVED_UNSUPPORTED_SCOPE,
            "P008 cardinality supports only the exact FLAT scope.",
        )

    binding = candidate.binding
    if type(binding) is not OrderedChildBinding:
        return _result(
            P008CardinalityStatus.UNRESOLVED_MISSING_INPUT,
            "P008 cardinality requires one exact OrderedChildBinding.",
        )

    if len(binding.ordered_children) != 3:
        return _P008_STRUCTURAL_INVALIDITY_ISSUER.issue(
            _result(
                P008CardinalityStatus.CARDINALITY_VIOLATED,
                "The supplied proposed flat does not contain exactly three direct ordered children.",
                binding=binding,
                fatal_to_candidate=True,
            )
        )

    return _result(
        P008CardinalityStatus.CARDINALITY_SATISFIED,
        "The supplied proposed flat contains exactly three direct ordered children; no child family, label, subtype, or broader pattern validity is established.",
        binding=binding,
    )


__all__ = [
    "P008CandidateScope",
    "P008CardinalityStatus",
    "P008ExecutionRole",
    "P008FlatCardinalityInput",
    "P008FlatCardinalityResult",
    "check_p008_flat_cardinality",
]
