"""Narrow P004 check for an explicitly supplied normal-impulse candidate."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import math

from ._structural_invalidity_certification import (
    StructuralValidatorResult,
    _register_structural_validator,
)
from .models import SourceClassification


P004_BEHAVIOR_ID = "P004_NORMAL_IMPULSE_WAVE2_ORIGIN"
P004_PRINCIPLE_ID = "P004"
P004_PROTECTED_SOURCES = (
    "docs/elliott/PATTERN_BRAIN.md#A-normal-impulse-rule-1",
    "docs/elliott/SOURCE_EVIDENCE_MAP.json#P004",
    "docs/elliott/MASTER_PROTOCOL.md#step-5",
)


class CandidateScope(StrEnum):
    NORMAL_IMPULSE = "NORMAL_IMPULSE"


class ImpulseDirection(StrEnum):
    UP = "UP"
    DOWN = "DOWN"
    UNKNOWN = "UNKNOWN"


class ExecutionRole(StrEnum):
    HARD_VALIDATION = "HARD_VALIDATION"


class RuleCheckStatus(StrEnum):
    RULE_SATISFIED = "RULE_SATISFIED"
    RULE_VIOLATED = "RULE_VIOLATED"
    UNRESOLVED_MISSING_INPUT = "UNRESOLVED_MISSING_INPUT"
    UNRESOLVED_UNSUPPORTED_SCOPE = "UNRESOLVED_UNSUPPORTED_SCOPE"


@dataclass(frozen=True, slots=True)
class P004Input:
    candidate_scope: CandidateScope | str | None
    direction: ImpulseDirection | str | None
    wave1_origin: float | None
    wave2_retracement_extreme: float | None


@dataclass(frozen=True, slots=True, weakref_slot=True)
class P004Result(StructuralValidatorResult):
    status: RuleCheckStatus
    principle_id: str
    source_class: SourceClassification
    execution_role: ExecutionRole
    protected_sources: tuple[str, ...]
    behavior_id: str
    outcome: str
    reason: str
    fatal_to_candidate: bool


_P004_STRUCTURAL_INVALIDITY_ISSUER = _register_structural_validator(
    P004Result,
    violation_statuses=(RuleCheckStatus.RULE_VIOLATED,),
    hard_validation_role=ExecutionRole.HARD_VALIDATION,
    principle_attribute="principle_id",
    behavior_id=P004_BEHAVIOR_ID,
    principle_id=P004_PRINCIPLE_ID,
    source_class=SourceClassification.RULE,
    protected_sources=P004_PROTECTED_SOURCES,
)


def _result(
    status: RuleCheckStatus,
    reason: str,
    *,
    fatal_to_candidate: bool = False,
) -> P004Result:
    return P004Result(
        status=status,
        principle_id=P004_PRINCIPLE_ID,
        source_class=SourceClassification.RULE,
        execution_role=ExecutionRole.HARD_VALIDATION,
        protected_sources=P004_PROTECTED_SOURCES,
        behavior_id=P004_BEHAVIOR_ID,
        outcome=status.value,
        reason=reason,
        fatal_to_candidate=fatal_to_candidate,
    )


def _is_finite_price(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def check_p004(candidate: P004Input) -> P004Result:
    """Check only P004; inputs must already identify and measure the candidate."""
    if candidate.candidate_scope != CandidateScope.NORMAL_IMPULSE:
        return _result(
            RuleCheckStatus.UNRESOLVED_UNSUPPORTED_SCOPE,
            "P004 applies only to an explicitly supplied NORMAL_IMPULSE scope.",
        )

    if candidate.direction not in (ImpulseDirection.UP, ImpulseDirection.DOWN):
        return _result(
            RuleCheckStatus.UNRESOLVED_MISSING_INPUT,
            "P004 requires an explicit UP or DOWN direction.",
        )

    if not _is_finite_price(candidate.wave1_origin):
        return _result(
            RuleCheckStatus.UNRESOLVED_MISSING_INPUT,
            "P004 requires an explicitly supplied finite Wave 1 origin price.",
        )

    if not _is_finite_price(candidate.wave2_retracement_extreme):
        return _result(
            RuleCheckStatus.UNRESOLVED_MISSING_INPUT,
            "P004 requires an explicitly supplied finite Wave 2 retracement extreme.",
        )

    if candidate.direction == ImpulseDirection.UP:
        violated = candidate.wave2_retracement_extreme < candidate.wave1_origin
    else:
        violated = candidate.wave2_retracement_extreme > candidate.wave1_origin

    if violated:
        return _P004_STRUCTURAL_INVALIDITY_ISSUER.issue(
            _result(
                RuleCheckStatus.RULE_VIOLATED,
                "The supplied Wave 2 retracement extreme moved beyond the supplied Wave 1 origin.",
                fatal_to_candidate=True,
            )
        )

    return _result(
        RuleCheckStatus.RULE_SATISFIED,
        "The supplied Wave 2 retracement extreme did not move beyond the supplied Wave 1 origin.",
    )
