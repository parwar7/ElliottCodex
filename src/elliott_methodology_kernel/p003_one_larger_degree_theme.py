"""P003 mapping from caller-established relative context to search theme.

The uppercase relation, theme, status, and execution-role tokens in this
module are behavior-local Runtime vocabulary.  MOTIVE and CORRECTIVE mean
only the structural theme to search first; they never claim pattern validity.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .models import SourceClassification


P003_BEHAVIOR = "P003_ONE_LARGER_DEGREE_SEARCH_THEME"
P003_PRINCIPLE_ID = "P003"
P003_PROTECTED_SOURCES = (
    "docs/elliott/SOURCE_EVIDENCE_MAP.json#P003",
    "docs/elliott/MASTER_PROTOCOL.md#step-2-determine-the-one-larger-degree-direction",
    "docs/elliott/DEGREE_RECURSION_BRAIN.md#2-timeframe-is-not-degree",
    "docs/elliott/DEGREE_RECURSION_BRAIN.md#4-all-degrees-operate-simultaneously",
    "docs/elliott/SOURCE_POLICY.md#1-authoritative-source-set",
    "docs/elliott/SOURCE_POLICY.md#3-evidence-classes",
    "docs/elliott/OUTPUT_CONTRACT.md#structural-message",
    "schemas/ANALYSIS_OUTPUT_SCHEMA.json#properties-structural_message",
    "examples/EMPTY_ANALYSIS.json#structural_message",
)


class P003OneLargerDegreeRelation(StrEnum):
    WITH = "WITH"
    AGAINST = "AGAINST"
    UNRESOLVED = "UNRESOLVED"


class P003SearchTheme(StrEnum):
    MOTIVE = "MOTIVE"
    CORRECTIVE = "CORRECTIVE"
    UNRESOLVED = "UNRESOLVED"


class P003ThemeMappingStatus(StrEnum):
    SEARCH_THEME_MAPPED = "SEARCH_THEME_MAPPED"
    SEARCH_THEME_UNRESOLVED = "SEARCH_THEME_UNRESOLVED"
    UNRESOLVED_MISSING_INPUT = "UNRESOLVED_MISSING_INPUT"


class P003ExecutionRole(StrEnum):
    STRUCTURAL_CONTEXT = "STRUCTURAL_CONTEXT"


@dataclass(frozen=True, slots=True)
class P003OneLargerDegreeThemeInput:
    relation_to_one_larger_degree: P003OneLargerDegreeRelation | str | None = None


@dataclass(frozen=True, slots=True)
class P003OneLargerDegreeThemeResult:
    status: P003ThemeMappingStatus
    principle_id: str
    source_class: SourceClassification
    execution_role: P003ExecutionRole
    protected_sources: tuple[str, ...]
    behavior_id: str
    outcome: str
    reason: str
    fatal_to_candidate: bool
    theme: P003SearchTheme


def _result(
    status: P003ThemeMappingStatus,
    theme: P003SearchTheme,
    reason: str,
) -> P003OneLargerDegreeThemeResult:
    return P003OneLargerDegreeThemeResult(
        status=status,
        principle_id=P003_PRINCIPLE_ID,
        source_class=SourceClassification.DEFINITION,
        execution_role=P003ExecutionRole.STRUCTURAL_CONTEXT,
        protected_sources=P003_PROTECTED_SOURCES,
        behavior_id=P003_BEHAVIOR,
        outcome=status.value,
        reason=reason,
        fatal_to_candidate=False,
        theme=theme,
    )


def map_p003_one_larger_degree_theme(
    candidate: P003OneLargerDegreeThemeInput,
) -> P003OneLargerDegreeThemeResult:
    """Map only an already-established relative relation to a search theme."""
    if type(candidate) is not P003OneLargerDegreeThemeInput:
        return _result(
            P003ThemeMappingStatus.UNRESOLVED_MISSING_INPUT,
            P003SearchTheme.UNRESOLVED,
            "P003 requires its behavior-local input contract; no relation, direction, degree, or pattern was inferred.",
        )

    relation = candidate.relation_to_one_larger_degree
    if not issubclass(type(relation), str):
        return _result(
            P003ThemeMappingStatus.UNRESOLVED_MISSING_INPUT,
            P003SearchTheme.UNRESOLVED,
            "P003 requires exactly WITH, AGAINST, or UNRESOLVED as a caller-supplied relation; no normalization or direction inference was applied.",
        )

    if str.__eq__(relation, P003OneLargerDegreeRelation.WITH.value) is True:
        return _result(
            P003ThemeMappingStatus.SEARCH_THEME_MAPPED,
            P003SearchTheme.MOTIVE,
            "P003 maps caller-supplied WITH to the MOTIVE search theme only; no motive pattern is identified or validated.",
        )

    if str.__eq__(relation, P003OneLargerDegreeRelation.AGAINST.value) is True:
        return _result(
            P003ThemeMappingStatus.SEARCH_THEME_MAPPED,
            P003SearchTheme.CORRECTIVE,
            "P003 maps caller-supplied AGAINST to the CORRECTIVE search theme only; no corrective pattern is identified or validated.",
        )

    if str.__eq__(relation, P003OneLargerDegreeRelation.UNRESOLVED.value) is True:
        return _result(
            P003ThemeMappingStatus.SEARCH_THEME_UNRESOLVED,
            P003SearchTheme.UNRESOLVED,
            "P003 received caller-supplied UNRESOLVED relation; the search theme remains UNRESOLVED without inferring direction, degree, or pattern.",
        )

    return _result(
        P003ThemeMappingStatus.UNRESOLVED_MISSING_INPUT,
        P003SearchTheme.UNRESOLVED,
        "P003 requires exactly WITH, AGAINST, or UNRESOLVED as a caller-supplied relation; no normalization or direction inference was applied.",
    )


__all__ = [
    "P003ExecutionRole",
    "P003OneLargerDegreeRelation",
    "P003OneLargerDegreeThemeInput",
    "P003OneLargerDegreeThemeResult",
    "P003SearchTheme",
    "P003ThemeMappingStatus",
    "map_p003_one_larger_degree_theme",
]
