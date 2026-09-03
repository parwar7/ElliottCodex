"""Bounded end-to-end analysis of one explicitly described manual candidate.

This module is PROJECT_ANALYSIS_INFRASTRUCTURE.  Its final-summary, coverage,
and dependency-request conventions are PROJECT_OPERATIONAL_POLICY.  It only
organizes exact existing downstream objects and never discovers or interprets
chart structure.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum

from ._structural_invalidity_certification import CertifiedStructuralInvalidity
from .bounded_recursive_analysis import BoundedRecursiveAnalysisResolution
from .candidate_analysis_envelope import (
    CandidateMethodologyEvaluation,
    CandidateObservationAttachment,
    _BEHAVIOR_COMPATIBILITY,
)
from .explicit_behavior_execution import (
    ExplicitBehaviorExecutionRecord,
    ExplicitBehaviorExecutionResult,
    ExplicitBehaviorExecutionState,
    ExplicitBehaviorInput,
    MISSING_TRUSTED_INVALIDITY_CERTIFICATE,
)
from .manual_structure_candidate_builder import (
    ManualStructureCandidateBuildResult,
    ManualStructureCandidateRequest,
)
from .single_candidate_orchestration import (
    SingleCandidateAnalysisResult,
    SingleCandidateExecutionSummary,
)
from .structural_invalidity_evidence_no_rescue import NO_RESCUE_BEHAVIOR
from .subject_binding import AnalyzedWaveSubject, OrderedChildBinding


ARTIFACT_CLASSIFICATION = "PROJECT_ANALYSIS_INFRASTRUCTURE"
WORKFLOW_POLICY_CLASSIFICATION = "PROJECT_OPERATIONAL_POLICY"


class BoundedManualChartFinalSummary(StrEnum):
    STRUCTURALLY_INVALID = "STRUCTURALLY_INVALID"
    UNRESOLVED = "UNRESOLVED"
    CURRENT_SUPPLIED_SCOPE_REVIEWED = "CURRENT_SUPPLIED_SCOPE_REVIEWED"


class BoundedManualChartCoverageState(StrEnum):
    SUPPLIED_AND_EXECUTED = "SUPPLIED_AND_EXECUTED"
    NOT_SUPPLIED = "NOT_SUPPLIED"
    BLOCKED_MISSING_TRUSTED_DEPENDENCY = "BLOCKED_MISSING_TRUSTED_DEPENDENCY"


class BoundedManualChartAnalysisError(ValueError):
    """Raised when the bounded MVP request or result fails closed."""


class _SealedMvpType(type):
    def __new__(
        mcls: type,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
        **kwargs: object,
    ) -> type:
        if any(isinstance(base, mcls) for base in bases):
            raise TypeError("Bounded manual-chart types cannot be subclassed.")
        return super().__new__(mcls, name, bases, namespace, **kwargs)


def _require_text(value: object, name: str) -> str:
    if type(value) is not str or value.strip() == "":
        raise BoundedManualChartAnalysisError(
            f"{name} must be an exact non-blank string."
        )
    return value


def _require_provenance(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or any(
        type(item) is not str or item.strip() == "" for item in value
    ):
        raise BoundedManualChartAnalysisError(
            "provenance_refs must be an exact tuple of non-blank strings."
        )
    return value


def _exact_behavior(value: object, expected: str) -> bool:
    return type(value) is str and str.__eq__(value, expected) is True


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class BoundedManualChartAnalysisRequest(metaclass=_SealedMvpType):
    request_id: str
    requested_at_utc: str
    subject: AnalyzedWaveSubject
    candidate_id: str
    manual_behavior_facts: tuple[object, ...] = ()
    child_binding: OrderedChildBinding | None = None
    ordered_child_subjects: tuple[AnalyzedWaveSubject, ...] | None = None
    constructed_binding_id: str | None = None
    trusted_invalidity_certificates: tuple[CertifiedStructuralInvalidity, ...] = ()
    no_rescue_requested: bool = False
    observations: tuple[CandidateObservationAttachment, ...] = ()
    operational_resolution: BoundedRecursiveAnalysisResolution | None = None
    provenance_refs: tuple[str, ...] = ()
    _manual_request: ManualStructureCandidateRequest = field(init=False, repr=False)
    _identity_snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("Bounded manual-chart requests cannot be subclassed.")

    def __post_init__(self) -> None:
        _require_text(self.request_id, "request_id")
        _require_text(self.requested_at_utc, "requested_at_utc")
        _require_provenance(self.provenance_refs)
        if type(self.no_rescue_requested) is not bool:
            raise BoundedManualChartAnalysisError(
                "no_rescue_requested must be one exact boolean."
            )
        if self.trusted_invalidity_certificates and not self.no_rescue_requested:
            raise BoundedManualChartAnalysisError(
                "Trusted invalidity certificates require an explicit no-rescue request."
            )
        manual_request = ManualStructureCandidateRequest(
            request_id=self.request_id,
            requested_at_utc=self.requested_at_utc,
            subject=self.subject,
            candidate_id=self.candidate_id,
            manual_behavior_facts=self.manual_behavior_facts,
            child_binding=self.child_binding,
            ordered_child_subjects=self.ordered_child_subjects,
            constructed_binding_id=self.constructed_binding_id,
            trusted_invalidity_certificates=self.trusted_invalidity_certificates,
            observations=self.observations,
            operational_resolution=self.operational_resolution,
            provenance_refs=self.provenance_refs,
        )
        object.__setattr__(self, "_manual_request", manual_request)
        object.__setattr__(
            self,
            "_identity_snapshot",
            (
                self.request_id,
                self.requested_at_utc,
                self.subject,
                self.candidate_id,
                self.manual_behavior_facts,
                self.child_binding,
                self.ordered_child_subjects,
                self.constructed_binding_id,
                self.trusted_invalidity_certificates,
                self.no_rescue_requested,
                self.observations,
                self.operational_resolution,
                self.provenance_refs,
                manual_request,
            ),
        )

    def _validated(self) -> BoundedManualChartAnalysisRequest:
        if type(self) is not BoundedManualChartAnalysisRequest:
            raise BoundedManualChartAnalysisError(
                "MVP request must have its exact reviewed type."
            )
        try:
            snapshot = object.__getattribute__(self, "_identity_snapshot")
            manual_request = object.__getattribute__(self, "_manual_request")
        except AttributeError as error:
            raise BoundedManualChartAnalysisError("The MVP request is malformed.") from error
        current = (
            self.request_id,
            self.requested_at_utc,
            self.subject,
            self.candidate_id,
            self.manual_behavior_facts,
            self.child_binding,
            self.ordered_child_subjects,
            self.constructed_binding_id,
            self.trusted_invalidity_certificates,
            self.no_rescue_requested,
            self.observations,
            self.operational_resolution,
            self.provenance_refs,
            manual_request,
        )
        if len(snapshot) != len(current) or any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            raise BoundedManualChartAnalysisError(
                "The MVP request changed after construction."
            )
        try:
            copy.copy(manual_request)
        except Exception as error:
            raise BoundedManualChartAnalysisError(
                "The nested manual request changed."
            ) from error
        return self

    def __copy__(self) -> BoundedManualChartAnalysisRequest:
        return self._validated()

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> BoundedManualChartAnalysisRequest:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Bounded manual-chart requests cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class BoundedManualChartCoverage(metaclass=_SealedMvpType):
    behavior_id: str
    state: BoundedManualChartCoverageState
    _identity_snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not any(
            _exact_behavior(self.behavior_id, item.behavior_id)
            for item in _BEHAVIOR_COMPATIBILITY
        ):
            raise BoundedManualChartAnalysisError("Coverage has an unknown behavior ID.")
        if type(self.state) is not BoundedManualChartCoverageState:
            raise BoundedManualChartAnalysisError("Coverage has an invalid state type.")
        object.__setattr__(
            self,
            "_identity_snapshot",
            (self.behavior_id, self.state),
        )

    def _validated(self) -> BoundedManualChartCoverage:
        try:
            snapshot = object.__getattribute__(self, "_identity_snapshot")
        except AttributeError as error:
            raise BoundedManualChartAnalysisError("Coverage is malformed.") from error
        current = (self.behavior_id, self.state)
        if any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            raise BoundedManualChartAnalysisError("Coverage changed after creation.")
        return self

    def __copy__(self) -> BoundedManualChartCoverage:
        return self._validated()

    def __deepcopy__(self, memo: dict[int, object]) -> BoundedManualChartCoverage:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Coverage records cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class BoundedManualChartTrace(metaclass=_SealedMvpType):
    behavior_id: str
    manual_fact: object | None
    explicit_input: ExplicitBehaviorInput
    result_object: object
    evaluation: CandidateMethodologyEvaluation
    _identity_snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        copy.copy(self.explicit_input)
        copy.copy(self.evaluation)
        if (
            not _exact_behavior(self.behavior_id, self.explicit_input.behavior_id)
            or not _exact_behavior(self.behavior_id, self.evaluation.behavior_id)
            or self.explicit_input.input_object is not self.evaluation.input_object
            or self.result_object is not self.evaluation.result_object
        ):
            raise BoundedManualChartAnalysisError(
                "Traceability identities or behavior IDs differ."
            )
        object.__setattr__(
            self,
            "_identity_snapshot",
            (
                self.behavior_id,
                self.manual_fact,
                self.explicit_input,
                self.result_object,
                self.evaluation,
            ),
        )

    def _validated(self) -> BoundedManualChartTrace:
        try:
            snapshot = object.__getattribute__(self, "_identity_snapshot")
        except AttributeError as error:
            raise BoundedManualChartAnalysisError("Traceability is malformed.") from error
        current = (
            self.behavior_id,
            self.manual_fact,
            self.explicit_input,
            self.result_object,
            self.evaluation,
        )
        if any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            raise BoundedManualChartAnalysisError(
                "Traceability changed after creation."
            )
        self.__post_init__()
        return self

    def __copy__(self) -> BoundedManualChartTrace:
        return self._validated()

    def __deepcopy__(self, memo: dict[int, object]) -> BoundedManualChartTrace:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Traceability records cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True, init=False)
class BoundedManualChartAnalysisResult(metaclass=_SealedMvpType):
    request_id: str
    subject: AnalyzedWaveSubject
    candidate_id: str
    manual_build_result: ManualStructureCandidateBuildResult
    explicit_execution_result: ExplicitBehaviorExecutionResult
    candidate_analysis_result: SingleCandidateAnalysisResult
    final_summary: BoundedManualChartFinalSummary
    methodology_coverage: tuple[BoundedManualChartCoverage, ...]
    traceability: tuple[BoundedManualChartTrace, ...]
    unresolved_reasons: tuple[str, ...]
    structural_invalidity_certificates: tuple[CertifiedStructuralInvalidity, ...]
    provenance_refs: tuple[str, ...]
    _identity_snapshot: tuple[object, ...]

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("Bounded manual-chart results are created only by MethodologyKernel.")

    def _validated(self) -> BoundedManualChartAnalysisResult:
        if type(self) is not BoundedManualChartAnalysisResult:
            raise BoundedManualChartAnalysisError("MVP result has the wrong type.")
        try:
            snapshot = object.__getattribute__(self, "_identity_snapshot")
        except AttributeError as error:
            raise BoundedManualChartAnalysisError("The MVP result is malformed.") from error
        current = (
            self.request_id,
            self.subject,
            self.candidate_id,
            self.manual_build_result,
            self.explicit_execution_result,
            self.candidate_analysis_result,
            self.final_summary,
            self.methodology_coverage,
            self.traceability,
            self.unresolved_reasons,
            self.structural_invalidity_certificates,
            self.provenance_refs,
        )
        if len(snapshot) != len(current) or any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            raise BoundedManualChartAnalysisError("The MVP result changed after creation.")
        try:
            copy.copy(self.manual_build_result)
            copy.copy(self.explicit_execution_result)
            copy.copy(self.candidate_analysis_result)
            for item in self.methodology_coverage:
                copy.copy(item)
            for item in self.traceability:
                copy.copy(item)
        except Exception as error:
            raise BoundedManualChartAnalysisError(
                "A nested MVP result object changed."
            ) from error
        if self.explicit_execution_result is not self.manual_build_result.delegated_execution_result:
            raise BoundedManualChartAnalysisError("Explicit execution identity was not retained.")
        if self.candidate_analysis_result is not self.explicit_execution_result.single_candidate_analysis_result:
            raise BoundedManualChartAnalysisError("Candidate analysis identity was not retained.")
        if self.subject is not self.candidate_analysis_result.candidate_subject:
            raise BoundedManualChartAnalysisError("Result subject identity differs downstream.")
        if len(self.methodology_coverage) != len(_BEHAVIOR_COMPATIBILITY):
            raise BoundedManualChartAnalysisError("Coverage must contain all ten behaviors.")
        return self

    def __copy__(self) -> BoundedManualChartAnalysisResult:
        return self._validated()

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> BoundedManualChartAnalysisResult:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Bounded manual-chart results cannot be pickled.")


def _coverage(
    execution: ExplicitBehaviorExecutionResult,
    missing_no_rescue: bool,
) -> tuple[BoundedManualChartCoverage, ...]:
    coverage = []
    for compatibility in _BEHAVIOR_COMPATIBILITY:
        records = tuple(
            record
            for record in execution.execution_records
            if _exact_behavior(record.behavior_id, compatibility.behavior_id)
        )
        blocked = any(
            record.execution_state
            is ExplicitBehaviorExecutionState.BLOCKED_MISSING_TRUSTED_DEPENDENCY
            for record in records
        ) or (
            missing_no_rescue
            and _exact_behavior(compatibility.behavior_id, NO_RESCUE_BEHAVIOR)
        )
        if blocked:
            state = BoundedManualChartCoverageState.BLOCKED_MISSING_TRUSTED_DEPENDENCY
        elif records:
            state = BoundedManualChartCoverageState.SUPPLIED_AND_EXECUTED
        else:
            state = BoundedManualChartCoverageState.NOT_SUPPLIED
        coverage.append(
            BoundedManualChartCoverage(compatibility.behavior_id, state)
        )
    return tuple(coverage)


def _traces(
    build: ManualStructureCandidateBuildResult,
) -> tuple[BoundedManualChartTrace, ...]:
    facts = build.request.manual_behavior_facts
    inputs = build.constructed_explicit_behavior_inputs
    execution = build.delegated_execution_result
    traces = []
    for index, (explicit_input, record, evaluation) in enumerate(
        zip(
            inputs,
            execution.execution_records,
            execution.methodology_evaluations,
            strict=True,
        )
    ):
        manual_fact = facts[index] if index < len(facts) else None
        traces.append(
            BoundedManualChartTrace(
                explicit_input.behavior_id,
                manual_fact,
                explicit_input,
                record.result_object,
                evaluation,
            )
        )
    return tuple(traces)


def _new_result(
    request: BoundedManualChartAnalysisRequest,
    build: ManualStructureCandidateBuildResult,
) -> BoundedManualChartAnalysisResult:
    execution = build.delegated_execution_result
    analysis = execution.single_candidate_analysis_result
    if type(analysis) is not SingleCandidateAnalysisResult:
        raise BoundedManualChartAnalysisError(
            "The delegated pipeline did not produce an exact candidate result."
        )
    missing_no_rescue = request.no_rescue_requested and not request.trusted_invalidity_certificates
    reasons = list(execution.execution_unresolved_reasons)
    for reason in analysis.unresolved_reasons:
        if reason not in reasons:
            reasons.append(reason)
    if missing_no_rescue and MISSING_TRUSTED_INVALIDITY_CERTIFICATE not in reasons:
        reasons.append(MISSING_TRUSTED_INVALIDITY_CERTIFICATE)
    certificates = analysis.structural_invalidity_certificates
    if certificates:
        summary = BoundedManualChartFinalSummary.STRUCTURALLY_INVALID
    elif reasons or analysis.execution_summary is SingleCandidateExecutionSummary.UNRESOLVED:
        summary = BoundedManualChartFinalSummary.UNRESOLVED
    elif (
        analysis.execution_summary
        is SingleCandidateExecutionSummary.SUPPLIED_EVALUATIONS_REVIEWED
        and analysis.verified_evaluations
    ):
        summary = BoundedManualChartFinalSummary.CURRENT_SUPPLIED_SCOPE_REVIEWED
    else:
        raise BoundedManualChartAnalysisError(
            "The downstream result has no safe bounded MVP interpretation."
        )
    result = object.__new__(BoundedManualChartAnalysisResult)
    values = {
        "request_id": request.request_id,
        "subject": request.subject,
        "candidate_id": request.candidate_id,
        "manual_build_result": build,
        "explicit_execution_result": execution,
        "candidate_analysis_result": analysis,
        "final_summary": summary,
        "methodology_coverage": _coverage(execution, missing_no_rescue),
        "traceability": _traces(build),
        "unresolved_reasons": tuple(reasons),
        "structural_invalidity_certificates": certificates,
        "provenance_refs": request.provenance_refs,
    }
    for name, value in values.items():
        object.__setattr__(result, name, value)
    object.__setattr__(result, "_identity_snapshot", tuple(values.values()))
    return result._validated()


def _analyze_bounded_manual_chart(
    request: object,
    analyze_manual_candidate: Callable[
        [ManualStructureCandidateRequest],
        ManualStructureCandidateBuildResult,
    ],
) -> BoundedManualChartAnalysisResult:
    if type(request) is not BoundedManualChartAnalysisRequest:
        raise BoundedManualChartAnalysisError(
            "analyze_bounded_manual_chart requires one exact MVP request."
        )
    request._validated()
    build = analyze_manual_candidate(request._manual_request)
    if type(build) is not ManualStructureCandidateBuildResult:
        raise BoundedManualChartAnalysisError(
            "The existing manual builder returned an unexpected result."
        )
    return _new_result(request, build)


__all__ = [
    "ARTIFACT_CLASSIFICATION",
    "WORKFLOW_POLICY_CLASSIFICATION",
    "BoundedManualChartAnalysisError",
    "BoundedManualChartAnalysisRequest",
    "BoundedManualChartAnalysisResult",
    "BoundedManualChartCoverage",
    "BoundedManualChartCoverageState",
    "BoundedManualChartFinalSummary",
    "BoundedManualChartTrace",
]
