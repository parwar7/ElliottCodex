"""Preserve certified structural invalidity against evidence override.

``EVIDENCE_OVERRIDE_PROHIBITED`` is Runtime policy vocabulary.  It records
only that evidence cannot reverse an invalidity already established by the
exact certified origin; it does not evaluate evidence or create invalidity.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import cast

from .contracts import (
    CertifiedStructuralInvalidity,
    SourceClassification,
    StructuralInvalidityCertificationError,
    StructuralValidity,
)


NO_RESCUE_BEHAVIOR = "STRUCTURAL_INVALIDITY_EVIDENCE_NO_RESCUE"
NO_RESCUE_PROTECTED_SOURCES = (
    "AGENTS.md#non-negotiable-operating-constraints",
    "docs/elliott/MASTER_PROTOCOL.md#step-5-apply-rules-and-definitions-first",
    "docs/elliott/EVIDENCE_BRAIN.md#opening-structural-evidence-boundary",
    "docs/elliott/SOURCE_POLICY.md#3-evidence-classes",
)
NO_RESCUE_REASON = (
    "Evidence has no authority to reverse the certified hard structural invalidity."
)


class StructuralInvalidityEvidenceNoRescuePolicyStatus(StrEnum):
    """Runtime-only diagnostic status for the preservation policy."""

    EVIDENCE_OVERRIDE_PROHIBITED = "EVIDENCE_OVERRIDE_PROHIBITED"


class StructuralInvalidityEvidenceNoRescueExecutionRole(StrEnum):
    HARD_VALIDATION = "HARD_VALIDATION"


def _validated_certificate(
    value: object,
) -> CertifiedStructuralInvalidity:
    if type(value) is not CertifiedStructuralInvalidity:
        raise StructuralInvalidityCertificationError(
            "The no-rescue policy requires one exact live "
            "CertifiedStructuralInvalidity."
        )

    certificate = cast(CertifiedStructuralInvalidity, value)
    # These public properties revalidate exact origin identity, issuance
    # attestation, producer invariants, and the certified-field digest.
    certificate.origin
    if certificate.structural_validity is not StructuralValidity.INVALID:
        raise StructuralInvalidityCertificationError(
            "The supplied certificate does not preserve structural invalidity."
        )
    if certificate.fatal_to_candidate is not True:
        raise StructuralInvalidityCertificationError(
            "The supplied certificate is not fatal to the candidate."
        )
    return certificate


@dataclass(frozen=True, slots=True, init=False, repr=False, eq=False)
class StructuralInvalidityEvidenceNoRescueResult:
    """Immutable two-layer policy result retaining the exact certificate."""

    _originating_invalidity: CertifiedStructuralInvalidity

    def __init__(
        self,
        originating_invalidity: CertifiedStructuralInvalidity,
    ) -> None:
        certificate = _validated_certificate(originating_invalidity)
        object.__setattr__(self, "_originating_invalidity", certificate)

    def _certificate(
        self,
    ) -> CertifiedStructuralInvalidity:
        try:
            certificate = object.__getattribute__(
                self, "_originating_invalidity"
            )
        except Exception as error:
            raise StructuralInvalidityCertificationError(
                "The no-rescue policy result is malformed."
            ) from error
        return _validated_certificate(certificate)

    @property
    def policy_status(
        self,
    ) -> StructuralInvalidityEvidenceNoRescuePolicyStatus:
        self._certificate()
        return (
            StructuralInvalidityEvidenceNoRescuePolicyStatus
            .EVIDENCE_OVERRIDE_PROHIBITED
        )

    @property
    def behavior_id(self) -> str:
        self._certificate()
        return NO_RESCUE_BEHAVIOR

    @property
    def source_principle_id(self) -> None:
        self._certificate()
        return None

    @property
    def source_class(self) -> SourceClassification:
        self._certificate()
        return SourceClassification.RULE

    @property
    def execution_role(
        self,
    ) -> StructuralInvalidityEvidenceNoRescueExecutionRole:
        self._certificate()
        return StructuralInvalidityEvidenceNoRescueExecutionRole.HARD_VALIDATION

    @property
    def protected_sources(self) -> tuple[str, ...]:
        self._certificate()
        return NO_RESCUE_PROTECTED_SOURCES

    @property
    def reason(self) -> str:
        self._certificate()
        return NO_RESCUE_REASON

    @property
    def originating_invalidity(
        self,
    ) -> CertifiedStructuralInvalidity:
        return self._certificate()

    @property
    def structural_validity(self) -> StructuralValidity:
        return self._certificate().structural_validity

    @property
    def fatal_to_candidate(self) -> bool:
        return self._certificate().fatal_to_candidate

    @property
    def evidence_override_allowed(self) -> bool:
        self._certificate()
        return False

    def __repr__(self) -> str:
        return (
            "StructuralInvalidityEvidenceNoRescueResult("
            f"policy_status={self.policy_status!r}, "
            f"behavior_id={self.behavior_id!r}, "
            f"originating_invalidity={self.originating_invalidity!r})"
        )


def apply_structural_invalidity_evidence_no_rescue(
    originating_invalidity: CertifiedStructuralInvalidity,
) -> StructuralInvalidityEvidenceNoRescueResult:
    """Apply only the categorical non-override policy to one certificate."""
    return StructuralInvalidityEvidenceNoRescueResult(originating_invalidity)


__all__ = [
    "StructuralInvalidityEvidenceNoRescueExecutionRole",
    "StructuralInvalidityEvidenceNoRescuePolicyStatus",
    "StructuralInvalidityEvidenceNoRescueResult",
    "apply_structural_invalidity_evidence_no_rescue",
]
