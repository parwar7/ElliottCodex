"""Direct-child peer-degree consistency with no degree inference."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from ._structural_invalidity_certification import (
    StructuralValidatorResult,
    _register_structural_validator,
)
from .models import DegreeStatus, DegreeTreeNode, SourceClassification


DEGREE_PEER_BEHAVIOR_ID = "DEGREE_DIRECT_CHILD_PEER_CONSISTENCY"
DEGREE_PEER_PROTECTED_SOURCES = (
    "docs/elliott/DEGREE_RECURSION_BRAIN.md#7-degree-consistency",
    "docs/elliott/DEGREE_RECURSION_BRAIN.md#5-recursive-validator",
    "docs/elliott/MASTER_PROTOCOL.md#step-3",
    "docs/elliott/MASTER_PROTOCOL.md#step-4",
)


class DegreePeerExecutionRole(StrEnum):
    HARD_VALIDATION = "HARD_VALIDATION"


class DegreePeerCheckStatus(StrEnum):
    RULE_SATISFIED = "RULE_SATISFIED"
    RULE_VIOLATED = "RULE_VIOLATED"
    UNRESOLVED_MISSING_INPUT = "UNRESOLVED_MISSING_INPUT"
    UNRESOLVED_INSUFFICIENT_PEERS = "UNRESOLVED_INSUFFICIENT_PEERS"


@dataclass(frozen=True, slots=True)
class DegreePeerConsistencyInput:
    parent_node_id: str | None
    direct_child_degrees: tuple[DegreeTreeNode, ...]


@dataclass(frozen=True, slots=True, weakref_slot=True)
class DegreePeerConsistencyResult(StructuralValidatorResult):
    status: DegreePeerCheckStatus
    source_principle_id: None
    source_class: SourceClassification
    execution_role: DegreePeerExecutionRole
    protected_sources: tuple[str, ...]
    behavior_id: str
    outcome: str
    reason: str
    fatal_to_candidate: bool


_DEGREE_PEER_STRUCTURAL_INVALIDITY_ISSUER = _register_structural_validator(
    DegreePeerConsistencyResult,
    violation_statuses=(DegreePeerCheckStatus.RULE_VIOLATED,),
    hard_validation_role=DegreePeerExecutionRole.HARD_VALIDATION,
    principle_attribute="source_principle_id",
    behavior_id=DEGREE_PEER_BEHAVIOR_ID,
    principle_id=None,
    source_class=SourceClassification.DEFINITION,
    protected_sources=DEGREE_PEER_PROTECTED_SOURCES,
)


def _result(
    status: DegreePeerCheckStatus,
    reason: str,
    *,
    fatal_to_candidate: bool = False,
) -> DegreePeerConsistencyResult:
    return DegreePeerConsistencyResult(
        status=status,
        source_principle_id=None,
        source_class=SourceClassification.DEFINITION,
        execution_role=DegreePeerExecutionRole.HARD_VALIDATION,
        protected_sources=DEGREE_PEER_PROTECTED_SOURCES,
        behavior_id=DEGREE_PEER_BEHAVIOR_ID,
        outcome=status.value,
        reason=reason,
        fatal_to_candidate=fatal_to_candidate,
    )


def check_degree_peer_consistency(
    candidate: DegreePeerConsistencyInput,
) -> DegreePeerConsistencyResult:
    """Compare only explicit degree labels of caller-selected direct peers."""
    if not isinstance(candidate.parent_node_id, str) or candidate.parent_node_id == "":
        return _result(
            DegreePeerCheckStatus.UNRESOLVED_MISSING_INPUT,
            "Peer-degree consistency requires an explicit non-empty parent node identity.",
        )

    children = candidate.direct_child_degrees
    if not isinstance(children, tuple):
        return _result(
            DegreePeerCheckStatus.UNRESOLVED_MISSING_INPUT,
            "Direct-child degrees must be supplied as an ordered tuple.",
        )

    if len(children) < 2:
        return _result(
            DegreePeerCheckStatus.UNRESOLVED_INSUFFICIENT_PEERS,
            "At least two directly comparable direct children are required.",
        )

    resolved_degrees: list[str] = []
    for child in children:
        if (
            not isinstance(child, DegreeTreeNode)
            or child.degree_status != DegreeStatus.RESOLVED
            or not isinstance(child.degree, str)
            or child.degree == ""
        ):
            return _result(
                DegreePeerCheckStatus.UNRESOLVED_MISSING_INPUT,
                "Every supplied direct child must have an explicit resolved degree label.",
            )
        resolved_degrees.append(child.degree)

    if any(degree != resolved_degrees[0] for degree in resolved_degrees[1:]):
        return _DEGREE_PEER_STRUCTURAL_INVALIDITY_ISSUER.issue(
            _result(
                DegreePeerCheckStatus.RULE_VIOLATED,
                "The supplied directly comparable direct children do not share one degree label.",
                fatal_to_candidate=True,
            )
        )

    return _result(
        DegreePeerCheckStatus.RULE_SATISFIED,
        "The supplied directly comparable direct children share one degree label; no broader candidate validity is established.",
    )
