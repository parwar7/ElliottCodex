"""P009 direct-child cardinality for an explicitly proposed triangle."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ._structural_invalidity_certification import (
    StructuralValidatorResult,
    _register_structural_validator,
)
from .models import SourceClassification
from .subject_binding import OrderedChildBinding


P009_BEHAVIOR_ID = "P009_TRIANGLE_DIRECT_CHILD_CARDINALITY"
P009_PRINCIPLE_ID = "P009"
P009_PROTECTED_SOURCES = (
    "docs/elliott/SOURCE_EVIDENCE_MAP.json#P009",
    "docs/elliott/PATTERN_BRAIN.md#H-triangle",
    "docs/elliott/MASTER_PROTOCOL.md#step-4",
    "docs/elliott/MASTER_PROTOCOL.md#step-5",
    "Sources_LOCKED/volume_04/volume_04@00:25:03.650-00:25:22.670",
    "Sources_LOCKED/volume_04/volume_04@00:28:39.220-00:28:48.560",
)


class P009CandidateScope(StrEnum):
    TRIANGLE = "TRIANGLE"


class P009ExecutionRole(StrEnum):
    HARD_VALIDATION = "HARD_VALIDATION"


class P009CardinalityStatus(StrEnum):
    CARDINALITY_SATISFIED = "CARDINALITY_SATISFIED"
    CARDINALITY_VIOLATED = "CARDINALITY_VIOLATED"
    UNRESOLVED_MISSING_INPUT = "UNRESOLVED_MISSING_INPUT"
    UNRESOLVED_UNSUPPORTED_SCOPE = "UNRESOLVED_UNSUPPORTED_SCOPE"


@dataclass(frozen=True, slots=True)
class P009TriangleCardinalityInput:
    candidate_scope: P009CandidateScope | str | None
    binding: OrderedChildBinding | None


@dataclass(frozen=True, slots=True, weakref_slot=True)
class P009TriangleCardinalityResult(StructuralValidatorResult):
    status: P009CardinalityStatus
    principle_id: str
    source_class: SourceClassification
    execution_role: P009ExecutionRole
    protected_sources: tuple[str, ...]
    behavior_id: str
    outcome: str
    reason: str
    fatal_to_candidate: bool
    binding: OrderedChildBinding | None


_P009_STRUCTURAL_INVALIDITY_ISSUER = _register_structural_validator(
    P009TriangleCardinalityResult,
    violation_statuses=(P009CardinalityStatus.CARDINALITY_VIOLATED,),
    hard_validation_role=P009ExecutionRole.HARD_VALIDATION,
    principle_attribute="principle_id",
    behavior_id=P009_BEHAVIOR_ID,
    principle_id=P009_PRINCIPLE_ID,
    source_class=SourceClassification.DEFINITION,
    protected_sources=P009_PROTECTED_SOURCES,
)


def _result(
    status: P009CardinalityStatus,
    reason: str,
    *,
    binding: OrderedChildBinding | None = None,
    fatal_to_candidate: bool = False,
) -> P009TriangleCardinalityResult:
    return P009TriangleCardinalityResult(
        status=status,
        principle_id=P009_PRINCIPLE_ID,
        source_class=SourceClassification.DEFINITION,
        execution_role=P009ExecutionRole.HARD_VALIDATION,
        protected_sources=P009_PROTECTED_SOURCES,
        behavior_id=P009_BEHAVIOR_ID,
        outcome=status.value,
        reason=reason,
        fatal_to_candidate=fatal_to_candidate,
        binding=binding,
    )


def _is_supported_scope(value: object) -> bool:
    return value is P009CandidateScope.TRIANGLE or (
        type(value) is str
        and str.__eq__(value, P009CandidateScope.TRIANGLE.value) is True
    )


def check_p009_triangle_cardinality(
    candidate: object,
) -> P009TriangleCardinalityResult:
    """Check only exact direct-child cardinality; establish nothing broader."""
    if type(candidate) is not P009TriangleCardinalityInput:
        return _result(
            P009CardinalityStatus.UNRESOLVED_MISSING_INPUT,
            "P009 cardinality requires one exact behavior-local input.",
        )

    candidate_scope = candidate.candidate_scope
    if candidate_scope is None:
        return _result(
            P009CardinalityStatus.UNRESOLVED_MISSING_INPUT,
            "P009 cardinality requires an explicit TRIANGLE scope.",
        )
    if not _is_supported_scope(candidate_scope):
        return _result(
            P009CardinalityStatus.UNRESOLVED_UNSUPPORTED_SCOPE,
            "P009 cardinality supports only the exact TRIANGLE scope.",
        )

    binding = candidate.binding
    if type(binding) is not OrderedChildBinding:
        return _result(
            P009CardinalityStatus.UNRESOLVED_MISSING_INPUT,
            "P009 cardinality requires one exact OrderedChildBinding.",
        )

    if len(binding.ordered_children) != 5:
        return _P009_STRUCTURAL_INVALIDITY_ISSUER.issue(
            _result(
                P009CardinalityStatus.CARDINALITY_VIOLATED,
                "The supplied proposed triangle does not contain exactly five direct ordered children.",
                binding=binding,
                fatal_to_candidate=True,
            )
        )

    return _result(
        P009CardinalityStatus.CARDINALITY_SATISFIED,
        "The supplied proposed triangle contains exactly five direct ordered children; no child family, label, geometry, subtype, position, completion, degree, or broader pattern validity is established.",
        binding=binding,
    )


__all__ = [
    "P009CandidateScope",
    "P009CardinalityStatus",
    "P009ExecutionRole",
    "P009TriangleCardinalityInput",
    "P009TriangleCardinalityResult",
    "check_p009_triangle_cardinality",
]
