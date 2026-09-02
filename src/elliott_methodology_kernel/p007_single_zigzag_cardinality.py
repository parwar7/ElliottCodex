"""P007 direct-child cardinality for an explicitly proposed single zigzag."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ._structural_invalidity_certification import (
    StructuralValidatorResult,
    _register_structural_validator,
)
from .models import SourceClassification
from .subject_binding import OrderedChildBinding


P007_BEHAVIOR_ID = "P007_SINGLE_ZIGZAG_DIRECT_CHILD_CARDINALITY"
P007_PRINCIPLE_ID = "P007"
P007_PROTECTED_SOURCES = (
    "docs/elliott/SOURCE_EVIDENCE_MAP.json#P007",
    "docs/elliott/PATTERN_BRAIN.md#F-zigzag-family",
    "docs/elliott/MASTER_PROTOCOL.md#step-4",
    "docs/elliott/MASTER_PROTOCOL.md#step-5",
    "Sources_LOCKED/volume_04/volume_04@00:01:56.790-00:02:26.850",
)


class P007CandidateScope(StrEnum):
    SINGLE_ZIGZAG = "SINGLE_ZIGZAG"


class P007ExecutionRole(StrEnum):
    HARD_VALIDATION = "HARD_VALIDATION"


class P007CardinalityStatus(StrEnum):
    CARDINALITY_SATISFIED = "CARDINALITY_SATISFIED"
    CARDINALITY_VIOLATED = "CARDINALITY_VIOLATED"
    UNRESOLVED_MISSING_INPUT = "UNRESOLVED_MISSING_INPUT"
    UNRESOLVED_UNSUPPORTED_SCOPE = "UNRESOLVED_UNSUPPORTED_SCOPE"


@dataclass(frozen=True, slots=True)
class P007SingleZigzagCardinalityInput:
    candidate_scope: P007CandidateScope | str | None
    binding: OrderedChildBinding | None


@dataclass(frozen=True, slots=True, weakref_slot=True)
class P007SingleZigzagCardinalityResult(StructuralValidatorResult):
    status: P007CardinalityStatus
    principle_id: str
    source_class: SourceClassification
    execution_role: P007ExecutionRole
    protected_sources: tuple[str, ...]
    behavior_id: str
    outcome: str
    reason: str
    fatal_to_candidate: bool
    binding: OrderedChildBinding | None


_P007_STRUCTURAL_INVALIDITY_ISSUER = _register_structural_validator(
    P007SingleZigzagCardinalityResult,
    violation_statuses=(P007CardinalityStatus.CARDINALITY_VIOLATED,),
    hard_validation_role=P007ExecutionRole.HARD_VALIDATION,
    principle_attribute="principle_id",
    behavior_id=P007_BEHAVIOR_ID,
    principle_id=P007_PRINCIPLE_ID,
    source_class=SourceClassification.DEFINITION,
    protected_sources=P007_PROTECTED_SOURCES,
)


def _result(
    status: P007CardinalityStatus,
    reason: str,
    *,
    binding: OrderedChildBinding | None = None,
    fatal_to_candidate: bool = False,
) -> P007SingleZigzagCardinalityResult:
    return P007SingleZigzagCardinalityResult(
        status=status,
        principle_id=P007_PRINCIPLE_ID,
        source_class=SourceClassification.DEFINITION,
        execution_role=P007ExecutionRole.HARD_VALIDATION,
        protected_sources=P007_PROTECTED_SOURCES,
        behavior_id=P007_BEHAVIOR_ID,
        outcome=status.value,
        reason=reason,
        fatal_to_candidate=fatal_to_candidate,
        binding=binding,
    )


def _is_supported_scope(value: object) -> bool:
    return value is P007CandidateScope.SINGLE_ZIGZAG or (
        type(value) is str
        and str.__eq__(value, P007CandidateScope.SINGLE_ZIGZAG.value) is True
    )


def check_p007_single_zigzag_cardinality(
    candidate: object,
) -> P007SingleZigzagCardinalityResult:
    """Check only exact direct-child cardinality; establish nothing broader."""
    if type(candidate) is not P007SingleZigzagCardinalityInput:
        return _result(
            P007CardinalityStatus.UNRESOLVED_MISSING_INPUT,
            "P007 cardinality requires one exact behavior-local input.",
        )

    candidate_scope = candidate.candidate_scope
    if candidate_scope is None:
        return _result(
            P007CardinalityStatus.UNRESOLVED_MISSING_INPUT,
            "P007 cardinality requires an explicit SINGLE_ZIGZAG scope.",
        )
    if not _is_supported_scope(candidate_scope):
        return _result(
            P007CardinalityStatus.UNRESOLVED_UNSUPPORTED_SCOPE,
            "P007 cardinality supports only the exact SINGLE_ZIGZAG scope.",
        )

    binding = candidate.binding
    if type(binding) is not OrderedChildBinding:
        return _result(
            P007CardinalityStatus.UNRESOLVED_MISSING_INPUT,
            "P007 cardinality requires one exact OrderedChildBinding.",
        )

    if len(binding.ordered_children) != 3:
        return _P007_STRUCTURAL_INVALIDITY_ISSUER.issue(
            _result(
                P007CardinalityStatus.CARDINALITY_VIOLATED,
                "The supplied proposed single zigzag does not contain exactly three direct ordered children.",
                binding=binding,
                fatal_to_candidate=True,
            )
        )

    return _result(
        P007CardinalityStatus.CARDINALITY_SATISFIED,
        "The supplied proposed single zigzag contains exactly three direct ordered children; no child family, label, or broader pattern validity is established.",
        binding=binding,
    )


__all__ = [
    "P007CandidateScope",
    "P007CardinalityStatus",
    "P007ExecutionRole",
    "P007SingleZigzagCardinalityInput",
    "P007SingleZigzagCardinalityResult",
    "check_p007_single_zigzag_cardinality",
]
