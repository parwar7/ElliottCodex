"""Exact parent-child adjacency in the protected degree hierarchy."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ._structural_invalidity_certification import (
    StructuralValidatorResult,
    _register_structural_validator,
)
from .models import DegreeStatus, SourceClassification


PARENT_CHILD_DEGREE_BEHAVIOR_ID = "PARENT_CHILD_DEGREE_ADJACENCY"
PARENT_CHILD_DEGREE_PROTECTED_SOURCES = (
    "docs/elliott/DEGREE_RECURSION_BRAIN.md#1-degree-sequence",
    "docs/elliott/DEGREE_RECURSION_BRAIN.md#5-recursive-validator",
    "docs/elliott/DEGREE_RECURSION_BRAIN.md#7-degree-consistency",
    "docs/elliott/MASTER_PROTOCOL.md#step-3",
    "docs/elliott/MASTER_PROTOCOL.md#step-4",
    "docs/elliott/MASTER_PROTOCOL.md#step-6",
)

_CANONICAL_DEGREES = (
    "Grand Supercycle",
    "Supercycle",
    "Cycle",
    "Primary",
    "Intermediate",
    "Minor",
    "Minute",
    "Minuette",
    "Subminuette",
)


class ParentChildDegreeExecutionRole(StrEnum):
    HARD_VALIDATION = "HARD_VALIDATION"


class ParentChildDegreeCheckStatus(StrEnum):
    RULE_SATISFIED = "RULE_SATISFIED"
    RULE_VIOLATED = "RULE_VIOLATED"
    UNRESOLVED_MISSING_INPUT = "UNRESOLVED_MISSING_INPUT"
    UNRESOLVED_UNKNOWN_DEGREE = "UNRESOLVED_UNKNOWN_DEGREE"
    UNRESOLVED_NO_DEFINED_SUBORDINATE = "UNRESOLVED_NO_DEFINED_SUBORDINATE"


@dataclass(frozen=True, slots=True)
class ParentChildDegreeInput:
    parent_degree: str | None
    parent_degree_status: DegreeStatus
    child_degree: str | None
    child_degree_status: DegreeStatus


@dataclass(frozen=True, slots=True, weakref_slot=True)
class ParentChildDegreeResult(StructuralValidatorResult):
    status: ParentChildDegreeCheckStatus
    source_principle_id: None
    source_class: SourceClassification
    execution_role: ParentChildDegreeExecutionRole
    protected_sources: tuple[str, ...]
    behavior_id: str
    outcome: str
    reason: str
    fatal_to_candidate: bool


_PARENT_CHILD_STRUCTURAL_INVALIDITY_ISSUER = _register_structural_validator(
    ParentChildDegreeResult,
    violation_statuses=(ParentChildDegreeCheckStatus.RULE_VIOLATED,),
    hard_validation_role=ParentChildDegreeExecutionRole.HARD_VALIDATION,
    principle_attribute="source_principle_id",
    behavior_id=PARENT_CHILD_DEGREE_BEHAVIOR_ID,
    principle_id=None,
    source_class=SourceClassification.DEFINITION,
    protected_sources=PARENT_CHILD_DEGREE_PROTECTED_SOURCES,
)


def _result(
    status: ParentChildDegreeCheckStatus,
    reason: str,
    *,
    fatal_to_candidate: bool = False,
) -> ParentChildDegreeResult:
    return ParentChildDegreeResult(
        status=status,
        source_principle_id=None,
        source_class=SourceClassification.DEFINITION,
        execution_role=ParentChildDegreeExecutionRole.HARD_VALIDATION,
        protected_sources=PARENT_CHILD_DEGREE_PROTECTED_SOURCES,
        behavior_id=PARENT_CHILD_DEGREE_BEHAVIOR_ID,
        outcome=status.value,
        reason=reason,
        fatal_to_candidate=fatal_to_candidate,
    )


def check_parent_child_degree_adjacency(
    candidate: ParentChildDegreeInput,
) -> ParentChildDegreeResult:
    """Validate one explicit pair without inference, traversal, or normalization."""
    if (
        candidate.parent_degree_status != DegreeStatus.RESOLVED
        or candidate.child_degree_status != DegreeStatus.RESOLVED
    ):
        return _result(
            ParentChildDegreeCheckStatus.UNRESOLVED_MISSING_INPUT,
            "Both parent and child degree statuses must be explicitly resolved.",
        )

    if (
        not isinstance(candidate.parent_degree, str)
        or candidate.parent_degree == ""
        or not isinstance(candidate.child_degree, str)
        or candidate.child_degree == ""
    ):
        return _result(
            ParentChildDegreeCheckStatus.UNRESOLVED_MISSING_INPUT,
            "Resolved parent and child degrees require explicit non-empty labels.",
        )

    if (
        candidate.parent_degree not in _CANONICAL_DEGREES
        or candidate.child_degree not in _CANONICAL_DEGREES
    ):
        return _result(
            ParentChildDegreeCheckStatus.UNRESOLVED_UNKNOWN_DEGREE,
            "A supplied resolved degree label is not in the protected hierarchy.",
        )

    parent_index = _CANONICAL_DEGREES.index(candidate.parent_degree)
    if parent_index == len(_CANONICAL_DEGREES) - 1:
        return _result(
            ParentChildDegreeCheckStatus.UNRESOLVED_NO_DEFINED_SUBORDINATE,
            "The protected hierarchy defines no subordinate degree below Subminuette.",
        )

    if _CANONICAL_DEGREES[parent_index + 1] != candidate.child_degree:
        return _PARENT_CHILD_STRUCTURAL_INVALIDITY_ISSUER.issue(
            _result(
                ParentChildDegreeCheckStatus.RULE_VIOLATED,
                "The supplied child degree is not exactly one protected hierarchy step below the supplied parent degree.",
                fatal_to_candidate=True,
            )
        )

    return _result(
        ParentChildDegreeCheckStatus.RULE_SATISFIED,
        "The supplied child degree is exactly one protected hierarchy step below the supplied parent degree; no broader candidate validity is established.",
    )
