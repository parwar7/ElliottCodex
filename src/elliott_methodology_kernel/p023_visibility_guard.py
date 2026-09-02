"""P023 visibility guard for caller-supplied required-internals visibility."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .models import SourceClassification


P023_BEHAVIOR_ID = "P023_INTERNAL_VISIBILITY_GUARD"
P023_PRINCIPLE_ID = "P023"
P023_PROTECTED_SOURCES = (
    "docs/elliott/SOURCE_EVIDENCE_MAP.json#P023",
    "docs/elliott/DEGREE_RECURSION_BRAIN.md#5-recursive-validator",
    "docs/elliott/DEGREE_RECURSION_BRAIN.md#6-data-resolution-rule",
    "docs/elliott/MASTER_PROTOCOL.md#step-6",
    "AGENTS.md#non-negotiable-operating-constraints",
)


class P023VisibilityState(StrEnum):
    VISIBLE = "VISIBLE"
    NOT_VISIBLE = "NOT_VISIBLE"
    UNKNOWN = "UNKNOWN"


class P023VisibilityCheckStatus(StrEnum):
    VISIBILITY_GUARD_PASSED = "VISIBILITY_GUARD_PASSED"
    INTERNALS_UNRESOLVED = "INTERNALS_UNRESOLVED"
    UNRESOLVED_MISSING_INPUT = "UNRESOLVED_MISSING_INPUT"


class P023VisibilityExecutionRole(StrEnum):
    HARD_VALIDATION = "HARD_VALIDATION"


@dataclass(frozen=True, slots=True)
class P023VisibilityInput:
    visibility_state: P023VisibilityState | str | None = None


@dataclass(frozen=True, slots=True)
class P023VisibilityResult:
    status: P023VisibilityCheckStatus
    principle_id: str
    source_class: SourceClassification
    execution_role: P023VisibilityExecutionRole
    protected_sources: tuple[str, ...]
    behavior_id: str
    outcome: str
    reason: str
    fatal_to_candidate: bool
    finer_data_required: bool | None


def _result(
    status: P023VisibilityCheckStatus,
    reason: str,
    *,
    finer_data_required: bool | None,
) -> P023VisibilityResult:
    return P023VisibilityResult(
        status=status,
        principle_id=P023_PRINCIPLE_ID,
        source_class=SourceClassification.DEFINITION,
        execution_role=P023VisibilityExecutionRole.HARD_VALIDATION,
        protected_sources=P023_PROTECTED_SOURCES,
        behavior_id=P023_BEHAVIOR_ID,
        outcome=status.value,
        reason=reason,
        fatal_to_candidate=False,
        finer_data_required=finer_data_required,
    )


def check_p023_visibility_guard(
    candidate: P023VisibilityInput,
) -> P023VisibilityResult:
    """Apply only P023 to an explicit caller-supplied visibility fact."""
    visibility = candidate.visibility_state

    if visibility is None:
        return _result(
            P023VisibilityCheckStatus.UNRESOLVED_MISSING_INPUT,
            "P023 requires a caller-supplied visibility state.",
            finer_data_required=None,
        )

    if not issubclass(type(visibility), str):
        return _result(
            P023VisibilityCheckStatus.UNRESOLVED_MISSING_INPUT,
            "P023 visibility must be exactly VISIBLE, NOT_VISIBLE, or UNKNOWN; the supplied value is malformed.",
            finer_data_required=None,
        )

    if str.__eq__(visibility, P023VisibilityState.UNKNOWN.value) is True:
        return _result(
            P023VisibilityCheckStatus.UNRESOLVED_MISSING_INPUT,
            "P023 received explicit UNKNOWN visibility; inspection availability is unresolved.",
            finer_data_required=None,
        )

    if str.__eq__(visibility, P023VisibilityState.VISIBLE.value) is True:
        return _result(
            P023VisibilityCheckStatus.VISIBILITY_GUARD_PASSED,
            "The caller supplied VISIBLE; inspection is available, but P023 does not confirm or validate internals.",
            finer_data_required=False,
        )

    if str.__eq__(visibility, P023VisibilityState.NOT_VISIBLE.value) is True:
        return _result(
            P023VisibilityCheckStatus.INTERNALS_UNRESOLVED,
            "The caller supplied NOT_VISIBLE; internals remain unresolved and finer data is required without inventing hidden pivots or waves.",
            finer_data_required=True,
        )

    return _result(
        P023VisibilityCheckStatus.UNRESOLVED_MISSING_INPUT,
        "P023 visibility must be exactly VISIBLE, NOT_VISIBLE, or UNKNOWN; the supplied value is malformed.",
        finer_data_required=None,
    )
