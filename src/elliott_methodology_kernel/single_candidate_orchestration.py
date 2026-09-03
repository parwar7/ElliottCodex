"""Operational orchestration over one exact supplied candidate envelope.

This is PROJECT_ANALYSIS_INFRASTRUCTURE.  Summary precedence and presence
inventory are PROJECT_OPERATIONAL_POLICY, not Elliott methodology.  The
orchestrator verifies and organizes caller-supplied live objects only; it does
not discover candidates, invoke validators, infer missing evaluations, issue
certificates, or establish family validity, completion, rank, or correctness.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import StrEnum

from ._structural_invalidity_certification import (
    CertifiedStructuralInvalidity,
    StructuralValidatorResult,
)
from .bounded_recursive_analysis import (
    AnalysisResolutionState,
    BoundedRecursiveAnalysisResolution,
    SubjectBoundP023VisibilityResult,
)
from .candidate_analysis_envelope import (
    CandidateAnalysisEnvelope,
    CandidateMethodologyEvaluation,
    _BEHAVIOR_COMPATIBILITY,
)
from .p023_visibility_guard import P023VisibilityCheckStatus
from .structural_invalidity_evidence_no_rescue import (
    StructuralInvalidityEvidenceNoRescueResult,
)
from .subject_binding import AnalyzedWaveSubject


ARTIFACT_CLASSIFICATION = "PROJECT_ANALYSIS_INFRASTRUCTURE"
WORKFLOW_POLICY_CLASSIFICATION = "PROJECT_OPERATIONAL_POLICY"
NO_METHODOLOGY_EVALUATIONS_SUPPLIED = "NO_METHODOLOGY_EVALUATIONS_SUPPLIED"
UNCERTIFIED_FATAL_RESULT = "UNCERTIFIED_FATAL_RESULT_REQUIRES_CERTIFICATE"


class CandidateEvaluationPresence(StrEnum):
    SUPPLIED_AND_VERIFIED = "SUPPLIED_AND_VERIFIED"
    NOT_SUPPLIED = "NOT_SUPPLIED"


class SingleCandidateExecutionSummary(StrEnum):
    STRUCTURALLY_INVALID = "STRUCTURALLY_INVALID"
    UNRESOLVED = "UNRESOLVED"
    SUPPLIED_EVALUATIONS_REVIEWED = "SUPPLIED_EVALUATIONS_REVIEWED"


class SingleCandidateOrchestrationError(ValueError):
    """Raised when a single-candidate invocation fails closed."""


class _SealedOrchestrationType(type):
    def __new__(
        mcls: type,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
        **kwargs: object,
    ) -> type:
        if any(isinstance(base, mcls) for base in bases):
            raise TypeError("Single-candidate orchestration types cannot be subclassed.")
        return super().__new__(mcls, name, bases, namespace, **kwargs)


def _require_text(value: object, name: str) -> str:
    if type(value) is not str or value.strip() == "":
        raise SingleCandidateOrchestrationError(
            f"{name} must be an exact non-blank string."
        )
    return value


def _require_provenance(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or any(
        type(item) is not str or item.strip() == "" for item in value
    ):
        raise SingleCandidateOrchestrationError(
            "provenance_refs must be an exact tuple of non-blank strings."
        )
    return value


def _exact_behavior(value: object, expected: str) -> bool:
    return type(value) is str and str.__eq__(value, expected) is True


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class SingleCandidateAnalysisRequest(metaclass=_SealedOrchestrationType):
    """One exact live candidate request, separate from legacy AnalysisRequest."""

    request_id: str
    requested_at_utc: str
    candidate_envelope: CandidateAnalysisEnvelope
    provenance_refs: tuple[str, ...] = ()
    _identity_snapshot: tuple[object, ...] = field(
        init=False, repr=False, compare=False
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("Single-candidate analysis requests cannot be subclassed.")

    def __post_init__(self) -> None:
        _require_text(self.request_id, "request_id")
        _require_text(self.requested_at_utc, "requested_at_utc")
        _require_provenance(self.provenance_refs)
        if type(self.candidate_envelope) is not CandidateAnalysisEnvelope:
            raise SingleCandidateOrchestrationError(
                "candidate_envelope must be one exact CandidateAnalysisEnvelope."
            )
        try:
            if copy.copy(self.candidate_envelope) is not self.candidate_envelope:
                raise SingleCandidateOrchestrationError(
                    "The candidate envelope did not preserve live identity."
                )
        except SingleCandidateOrchestrationError:
            raise
        except Exception as error:
            raise SingleCandidateOrchestrationError(
                "The candidate envelope is malformed or changed."
            ) from error
        object.__setattr__(
            self,
            "_identity_snapshot",
            (
                self.request_id,
                self.requested_at_utc,
                self.candidate_envelope,
                self.provenance_refs,
            ),
        )

    def _validated(self) -> SingleCandidateAnalysisRequest:
        try:
            snapshot = object.__getattribute__(self, "_identity_snapshot")
        except AttributeError as error:
            raise SingleCandidateOrchestrationError(
                "The single-candidate request is malformed."
            ) from error
        current = (
            self.request_id,
            self.requested_at_utc,
            self.candidate_envelope,
            self.provenance_refs,
        )
        if len(snapshot) != len(current) or any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            raise SingleCandidateOrchestrationError(
                "The single-candidate request changed after construction."
            )
        _require_text(self.request_id, "request_id")
        _require_text(self.requested_at_utc, "requested_at_utc")
        _require_provenance(self.provenance_refs)
        try:
            copy.copy(self.candidate_envelope)
        except Exception as error:
            raise SingleCandidateOrchestrationError(
                "The candidate envelope is malformed or changed."
            ) from error
        return self

    def __copy__(self) -> SingleCandidateAnalysisRequest:
        return self._validated()

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> SingleCandidateAnalysisRequest:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Single-candidate analysis requests cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class CandidateBehaviorExecution(metaclass=_SealedOrchestrationType):
    """Presence facts for one reviewed behavior without outcome interpretation."""

    behavior_id: str
    presence: CandidateEvaluationPresence
    evaluations: tuple[CandidateMethodologyEvaluation, ...]

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("Candidate behavior execution records cannot be subclassed.")

    def __post_init__(self) -> None:
        if not any(
            _exact_behavior(self.behavior_id, item.behavior_id)
            for item in _BEHAVIOR_COMPATIBILITY
        ):
            raise SingleCandidateOrchestrationError(
                "Execution inventory contains an unknown behavior ID."
            )
        if type(self.presence) is not CandidateEvaluationPresence:
            raise SingleCandidateOrchestrationError(
                "presence must be one exact CandidateEvaluationPresence."
            )
        if type(self.evaluations) is not tuple or any(
            type(item) is not CandidateMethodologyEvaluation
            for item in self.evaluations
        ):
            raise SingleCandidateOrchestrationError(
                "evaluations must be one exact tuple of verified attachments."
            )
        for evaluation in self.evaluations:
            try:
                evaluation._validated()
            except Exception as error:
                raise SingleCandidateOrchestrationError(
                    "Execution inventory contains an invalid evaluation."
                ) from error
            if not _exact_behavior(evaluation.behavior_id, self.behavior_id):
                raise SingleCandidateOrchestrationError(
                    "Execution inventory behavior and evaluation differ."
                )
        expected_presence = (
            CandidateEvaluationPresence.SUPPLIED_AND_VERIFIED
            if self.evaluations
            else CandidateEvaluationPresence.NOT_SUPPLIED
        )
        if self.presence is not expected_presence:
            raise SingleCandidateOrchestrationError(
                "Execution presence does not match supplied evaluations."
            )

    @property
    def verified(self) -> bool:
        return self.presence is CandidateEvaluationPresence.SUPPLIED_AND_VERIFIED

    def __copy__(self) -> CandidateBehaviorExecution:
        self.__post_init__()
        return self

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> CandidateBehaviorExecution:
        self.__post_init__()
        memo[id(self)] = self
        return self

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Candidate behavior execution records cannot be pickled.")


@dataclass(
    frozen=True,
    slots=True,
    eq=False,
    weakref_slot=True,
    init=False,
)
class SingleCandidateAnalysisResult(metaclass=_SealedOrchestrationType):
    """One deterministic execution-fact summary with no validity authority."""

    request_id: str
    candidate_envelope: CandidateAnalysisEnvelope
    candidate_subject: AnalyzedWaveSubject
    verified_evaluations: tuple[CandidateMethodologyEvaluation, ...]
    execution_inventory: tuple[CandidateBehaviorExecution, ...]
    operational_resolution: BoundedRecursiveAnalysisResolution | None
    structural_invalidity_certificates: tuple[CertifiedStructuralInvalidity, ...]
    execution_summary: SingleCandidateExecutionSummary
    unresolved_reasons: tuple[str, ...]
    brain_manifest_reference: str
    kernel_version: str
    provenance_refs: tuple[str, ...]
    _identity_snapshot: tuple[object, ...]

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError(
            "Single-candidate results may be created only by MethodologyKernel.analyze_candidate()."
        )

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("Single-candidate analysis results cannot be subclassed.")

    def _validated(self) -> SingleCandidateAnalysisResult:
        if type(self) is not SingleCandidateAnalysisResult:
            raise SingleCandidateOrchestrationError(
                "The result must have its exact reviewed type."
            )
        try:
            snapshot = object.__getattribute__(self, "_identity_snapshot")
        except AttributeError as error:
            raise SingleCandidateOrchestrationError(
                "The single-candidate result is malformed."
            ) from error
        current = (
            self.request_id,
            self.candidate_envelope,
            self.candidate_subject,
            self.verified_evaluations,
            self.execution_inventory,
            self.operational_resolution,
            self.structural_invalidity_certificates,
            self.execution_summary,
            self.unresolved_reasons,
            self.brain_manifest_reference,
            self.kernel_version,
            self.provenance_refs,
        )
        if len(snapshot) != len(current) or any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            raise SingleCandidateOrchestrationError(
                "The single-candidate result changed after creation."
            )
        _validate_result_values(self)
        return self

    def __copy__(self) -> SingleCandidateAnalysisResult:
        return self._validated()

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> SingleCandidateAnalysisResult:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Single-candidate analysis results cannot be pickled.")


def _certificate_origin(
    certificate: object,
) -> object:
    if type(certificate) is not CertifiedStructuralInvalidity:
        raise SingleCandidateOrchestrationError(
            "Structural invalidity must use an exact live certificate."
        )
    try:
        origin = certificate.origin
        if certificate.fatal_to_candidate is not True:
            raise SingleCandidateOrchestrationError(
                "Structural certificate is not fatal to the candidate."
            )
        certificate.structural_validity
    except SingleCandidateOrchestrationError:
        raise
    except Exception as error:
        raise SingleCandidateOrchestrationError(
            "Structural invalidity certificate is malformed or changed."
        ) from error
    return origin


def _append_unique_identity(items: list[object], value: object) -> None:
    if not any(item is value for item in items):
        items.append(value)


def _append_unique_reason(items: list[str], value: object) -> None:
    reason = _require_text(value, "unresolved reason")
    if not any(str.__eq__(item, reason) is True for item in items):
        items.append(reason)


def _build_execution_inventory(
    evaluations: tuple[CandidateMethodologyEvaluation, ...],
) -> tuple[CandidateBehaviorExecution, ...]:
    records = []
    for compatibility in _BEHAVIOR_COMPATIBILITY:
        supplied = tuple(
            evaluation
            for evaluation in evaluations
            if _exact_behavior(evaluation.behavior_id, compatibility.behavior_id)
        )
        records.append(
            CandidateBehaviorExecution(
                behavior_id=compatibility.behavior_id,
                presence=(
                    CandidateEvaluationPresence.SUPPLIED_AND_VERIFIED
                    if supplied
                    else CandidateEvaluationPresence.NOT_SUPPLIED
                ),
                evaluations=supplied,
            )
        )
    return tuple(records)


def _validate_result_values(result: SingleCandidateAnalysisResult) -> None:
    _require_text(result.request_id, "request_id")
    _require_text(result.brain_manifest_reference, "brain_manifest_reference")
    _require_text(result.kernel_version, "kernel_version")
    _require_provenance(result.provenance_refs)
    if type(result.candidate_envelope) is not CandidateAnalysisEnvelope:
        raise SingleCandidateOrchestrationError(
            "Result envelope must have its exact reviewed type."
        )
    try:
        copy.copy(result.candidate_envelope)
    except Exception as error:
        raise SingleCandidateOrchestrationError(
            "Result candidate envelope is malformed or changed."
        ) from error
    if result.candidate_subject is not result.candidate_envelope.subject:
        raise SingleCandidateOrchestrationError(
            "Result subject differs from its candidate envelope."
        )
    if result.verified_evaluations is not result.candidate_envelope.methodology_evaluations:
        raise SingleCandidateOrchestrationError(
            "Result evaluations must retain the envelope's exact tuple."
        )
    expected_inventory = _build_execution_inventory(result.verified_evaluations)
    if type(result.execution_inventory) is not tuple or len(
        result.execution_inventory
    ) != len(expected_inventory):
        raise SingleCandidateOrchestrationError(
            "Result execution inventory is incomplete."
        )
    for observed, expected in zip(
        result.execution_inventory, expected_inventory, strict=True
    ):
        if (
            type(observed) is not CandidateBehaviorExecution
            or not _exact_behavior(observed.behavior_id, expected.behavior_id)
            or observed.presence is not expected.presence
            or len(observed.evaluations) != len(expected.evaluations)
            or any(
                left is not right
                for left, right in zip(
                    observed.evaluations, expected.evaluations, strict=True
                )
            )
        ):
            raise SingleCandidateOrchestrationError(
                "Result execution inventory changed or diverged."
            )
        observed.__post_init__()
    if result.operational_resolution is not result.candidate_envelope.operational_resolution:
        raise SingleCandidateOrchestrationError(
            "Result must retain the envelope's exact operational resolution."
        )
    if type(result.structural_invalidity_certificates) is not tuple:
        raise SingleCandidateOrchestrationError(
            "Structural certificates must be one exact tuple."
        )
    seen_certificates: list[CertifiedStructuralInvalidity] = []
    for certificate in result.structural_invalidity_certificates:
        _certificate_origin(certificate)
        if any(existing is certificate for existing in seen_certificates):
            raise SingleCandidateOrchestrationError(
                "Structural certificate identity cannot be repeated."
            )
        seen_certificates.append(certificate)
    if type(result.unresolved_reasons) is not tuple or any(
        type(reason) is not str or reason.strip() == ""
        for reason in result.unresolved_reasons
    ):
        raise SingleCandidateOrchestrationError(
            "unresolved_reasons must be an exact tuple of non-blank strings."
        )
    if type(result.execution_summary) is not SingleCandidateExecutionSummary:
        raise SingleCandidateOrchestrationError(
            "execution_summary must have its exact operational enum type."
        )
    if result.execution_summary is SingleCandidateExecutionSummary.STRUCTURALLY_INVALID:
        if not result.structural_invalidity_certificates:
            raise SingleCandidateOrchestrationError(
                "STRUCTURALLY_INVALID requires a genuine retained certificate."
            )
    elif result.execution_summary is SingleCandidateExecutionSummary.UNRESOLVED:
        if result.structural_invalidity_certificates or not result.unresolved_reasons:
            raise SingleCandidateOrchestrationError(
                "UNRESOLVED requires reasons and cannot override certified invalidity."
            )
    elif result.execution_summary is SingleCandidateExecutionSummary.SUPPLIED_EVALUATIONS_REVIEWED:
        if (
            not result.verified_evaluations
            or result.structural_invalidity_certificates
            or result.unresolved_reasons
        ):
            raise SingleCandidateOrchestrationError(
                "Reviewed evaluations require nonempty supplied input and no blocker."
            )


def _new_result(
    *,
    request: SingleCandidateAnalysisRequest,
    inventory: tuple[CandidateBehaviorExecution, ...],
    certificates: tuple[CertifiedStructuralInvalidity, ...],
    summary: SingleCandidateExecutionSummary,
    unresolved_reasons: tuple[str, ...],
    brain_manifest_reference: str,
    kernel_version: str,
) -> SingleCandidateAnalysisResult:
    result = object.__new__(SingleCandidateAnalysisResult)
    values = {
        "request_id": request.request_id,
        "candidate_envelope": request.candidate_envelope,
        "candidate_subject": request.candidate_envelope.subject,
        "verified_evaluations": request.candidate_envelope.methodology_evaluations,
        "execution_inventory": inventory,
        "operational_resolution": request.candidate_envelope.operational_resolution,
        "structural_invalidity_certificates": certificates,
        "execution_summary": summary,
        "unresolved_reasons": unresolved_reasons,
        "brain_manifest_reference": brain_manifest_reference,
        "kernel_version": kernel_version,
        "provenance_refs": request.provenance_refs,
    }
    for name, value in values.items():
        object.__setattr__(result, name, value)
    snapshot = tuple(values.values())
    object.__setattr__(result, "_identity_snapshot", snapshot)
    _validate_result_values(result)
    return result


def _orchestrate_single_candidate(
    request: object,
    *,
    brain_manifest_reference: str,
    kernel_version: str,
) -> SingleCandidateAnalysisResult:
    if type(request) is not SingleCandidateAnalysisRequest:
        raise SingleCandidateOrchestrationError(
            "analyze_candidate requires one exact SingleCandidateAnalysisRequest."
        )
    request._validated()
    _require_text(brain_manifest_reference, "brain_manifest_reference")
    _require_text(kernel_version, "kernel_version")
    envelope = request.candidate_envelope
    evaluations = envelope.methodology_evaluations
    inventory = _build_execution_inventory(evaluations)

    certificates: list[CertifiedStructuralInvalidity] = []
    resolution = envelope.operational_resolution
    if (
        resolution is not None
        and resolution.state is AnalysisResolutionState.STRUCTURALLY_INVALID
    ):
        certificate = resolution.supporting_structural_invalidity_certificate
        _certificate_origin(certificate)
        _append_unique_identity(certificates, certificate)

    for evaluation in evaluations:
        result_object = evaluation.result_object
        if type(result_object) is StructuralInvalidityEvidenceNoRescueResult:
            try:
                certificate = result_object.originating_invalidity
            except Exception as error:
                raise SingleCandidateOrchestrationError(
                    "A supplied no-rescue result is malformed or changed."
                ) from error
            _certificate_origin(certificate)
            _append_unique_identity(certificates, certificate)

    unresolved_reasons: list[str] = []
    if resolution is not None and resolution.state in (
        AnalysisResolutionState.UNRESOLVED_FINER_DATA_REQUIRED,
        AnalysisResolutionState.UNRESOLVED_METHODOLOGY_DEPENDENCY,
    ):
        _append_unique_reason(unresolved_reasons, resolution.reason)

    certified_origins = tuple(_certificate_origin(item) for item in certificates)
    for evaluation in evaluations:
        result_object = evaluation.result_object
        if type(result_object) is SubjectBoundP023VisibilityResult:
            raw_result = result_object.result
            if raw_result.status in (
                P023VisibilityCheckStatus.INTERNALS_UNRESOLVED,
                P023VisibilityCheckStatus.UNRESOLVED_MISSING_INPUT,
            ):
                _append_unique_reason(unresolved_reasons, raw_result.reason)
        if isinstance(result_object, StructuralValidatorResult) and getattr(
            result_object, "fatal_to_candidate", False
        ) is True:
            if not any(origin is result_object for origin in certified_origins):
                _append_unique_reason(unresolved_reasons, UNCERTIFIED_FATAL_RESULT)

    if not evaluations:
        _append_unique_reason(
            unresolved_reasons,
            NO_METHODOLOGY_EVALUATIONS_SUPPLIED,
        )

    if certificates:
        summary = SingleCandidateExecutionSummary.STRUCTURALLY_INVALID
    elif unresolved_reasons:
        summary = SingleCandidateExecutionSummary.UNRESOLVED
    else:
        summary = SingleCandidateExecutionSummary.SUPPLIED_EVALUATIONS_REVIEWED

    return _new_result(
        request=request,
        inventory=inventory,
        certificates=tuple(certificates),
        summary=summary,
        unresolved_reasons=tuple(unresolved_reasons),
        brain_manifest_reference=brain_manifest_reference,
        kernel_version=kernel_version,
    )


__all__ = [
    "ARTIFACT_CLASSIFICATION",
    "WORKFLOW_POLICY_CLASSIFICATION",
    "CandidateBehaviorExecution",
    "CandidateEvaluationPresence",
    "SingleCandidateAnalysisRequest",
    "SingleCandidateAnalysisResult",
    "SingleCandidateExecutionSummary",
    "SingleCandidateOrchestrationError",
]
