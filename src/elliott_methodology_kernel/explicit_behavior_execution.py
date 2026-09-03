"""Execute exact caller-supplied inputs through reviewed methodology functions.

This module is PROJECT_ANALYSIS_INFRASTRUCTURE.  Its dispatch, ordering, and
dependency handling are PROJECT_OPERATIONAL_POLICY.  It neither determines
applicability nor creates methodology inputs, certificates, candidates, or
methodology semantics.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum

from ._structural_invalidity_certification import CertifiedStructuralInvalidity
from .bounded_recursive_analysis import (
    BoundedRecursiveAnalysisResolution,
    evaluate_p023_visibility_for_subject,
)
from .candidate_analysis_envelope import (
    CandidateAnalysisEnvelope,
    CandidateMethodologyEvaluation,
    CandidateObservationAttachment,
    _origin_binding_from_certificate,
    _snapshot,
    _snapshot_matches,
)
from .degree_peer_consistency import (
    DEGREE_PEER_BEHAVIOR_ID,
    DegreePeerConsistencyInput,
    check_degree_peer_consistency,
)
from .ending_diagonal_cardinality import (
    ENDING_DIAGONAL_BEHAVIOR_ID,
    EndingDiagonalCardinalityInput,
    check_ending_diagonal_cardinality,
)
from .p003_one_larger_degree_theme import (
    P003_BEHAVIOR,
    P003OneLargerDegreeThemeInput,
    map_p003_one_larger_degree_theme,
)
from .p004 import P004_BEHAVIOR_ID, P004Input, check_p004
from .p007_single_zigzag_cardinality import (
    P007_BEHAVIOR_ID,
    P007SingleZigzagCardinalityInput,
    check_p007_single_zigzag_cardinality,
)
from .p008_flat_cardinality import (
    P008_BEHAVIOR_ID,
    P008FlatCardinalityInput,
    check_p008_flat_cardinality,
)
from .p009_triangle_cardinality import (
    P009_BEHAVIOR_ID,
    P009TriangleCardinalityInput,
    check_p009_triangle_cardinality,
)
from .p023_visibility_guard import P023_BEHAVIOR_ID, P023VisibilityInput
from .parent_child_degree_adjacency import (
    PARENT_CHILD_DEGREE_BEHAVIOR_ID,
    ParentChildDegreeInput,
    check_parent_child_degree_adjacency,
)
from .single_candidate_orchestration import (
    SingleCandidateAnalysisRequest,
    SingleCandidateAnalysisResult,
)
from .structural_invalidity_evidence_no_rescue import (
    NO_RESCUE_BEHAVIOR,
    apply_structural_invalidity_evidence_no_rescue,
)
from .subject_binding import AnalyzedWaveSubject, OrderedChildBinding


ARTIFACT_CLASSIFICATION = "PROJECT_ANALYSIS_INFRASTRUCTURE"
WORKFLOW_POLICY_CLASSIFICATION = "PROJECT_OPERATIONAL_POLICY"
MISSING_TRUSTED_INVALIDITY_CERTIFICATE = (
    "MISSING_TRUSTED_STRUCTURAL_INVALIDITY_CERTIFICATE"
)


class ExplicitBehaviorExecutionState(StrEnum):
    EXECUTED = "EXECUTED"
    BLOCKED_MISSING_TRUSTED_DEPENDENCY = "BLOCKED_MISSING_TRUSTED_DEPENDENCY"


class ExplicitBehaviorExecutionError(ValueError):
    """Raised when explicit-input execution fails closed."""


class _SealedExecutionType(type):
    def __new__(
        mcls: type,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
        **kwargs: object,
    ) -> type:
        if any(isinstance(base, mcls) for base in bases):
            raise TypeError("Explicit behavior execution types cannot be subclassed.")
        return super().__new__(mcls, name, bases, namespace, **kwargs)


@dataclass(frozen=True, slots=True)
class _ExecutionDispatch:
    behavior_id: str
    input_type: type[object]
    validator: Callable[..., object]
    subject_bound: bool = False
    binding_consumer: bool = False
    certified_invalidity_input: bool = False


_EXECUTION_DISPATCH = (
    _ExecutionDispatch(P004_BEHAVIOR_ID, P004Input, check_p004),
    _ExecutionDispatch(
        DEGREE_PEER_BEHAVIOR_ID,
        DegreePeerConsistencyInput,
        check_degree_peer_consistency,
    ),
    _ExecutionDispatch(
        PARENT_CHILD_DEGREE_BEHAVIOR_ID,
        ParentChildDegreeInput,
        check_parent_child_degree_adjacency,
    ),
    _ExecutionDispatch(
        P023_BEHAVIOR_ID,
        P023VisibilityInput,
        evaluate_p023_visibility_for_subject,
        subject_bound=True,
    ),
    _ExecutionDispatch(
        NO_RESCUE_BEHAVIOR,
        CertifiedStructuralInvalidity,
        apply_structural_invalidity_evidence_no_rescue,
        certified_invalidity_input=True,
    ),
    _ExecutionDispatch(
        P003_BEHAVIOR,
        P003OneLargerDegreeThemeInput,
        map_p003_one_larger_degree_theme,
    ),
    _ExecutionDispatch(
        P007_BEHAVIOR_ID,
        P007SingleZigzagCardinalityInput,
        check_p007_single_zigzag_cardinality,
        binding_consumer=True,
    ),
    _ExecutionDispatch(
        P008_BEHAVIOR_ID,
        P008FlatCardinalityInput,
        check_p008_flat_cardinality,
        binding_consumer=True,
    ),
    _ExecutionDispatch(
        P009_BEHAVIOR_ID,
        P009TriangleCardinalityInput,
        check_p009_triangle_cardinality,
        binding_consumer=True,
    ),
    _ExecutionDispatch(
        ENDING_DIAGONAL_BEHAVIOR_ID,
        EndingDiagonalCardinalityInput,
        check_ending_diagonal_cardinality,
        binding_consumer=True,
    ),
)


def _require_text(value: object, name: str) -> str:
    if type(value) is not str or value.strip() == "":
        raise ExplicitBehaviorExecutionError(
            f"{name} must be an exact non-blank string."
        )
    return value


def _require_provenance(value: object, name: str = "provenance_refs") -> tuple[str, ...]:
    if type(value) is not tuple or any(
        type(item) is not str or item.strip() == "" for item in value
    ):
        raise ExplicitBehaviorExecutionError(
            f"{name} must be an exact tuple of non-blank strings."
        )
    return value


def _exact_behavior(value: object, expected: str) -> bool:
    return type(value) is str and str.__eq__(value, expected) is True


def _dispatch_for(behavior_id: object) -> _ExecutionDispatch:
    if type(behavior_id) is str:
        for item in _EXECUTION_DISPATCH:
            if str.__eq__(behavior_id, item.behavior_id) is True:
                return item
    raise ExplicitBehaviorExecutionError(
        "Unknown behavior_id has no reviewed execution dispatch."
    )


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class ExplicitBehaviorInput(metaclass=_SealedExecutionType):
    """One requested behavior and exact input, without caller-owned dispatch."""

    behavior_id: str
    input_object: object
    provenance_refs: tuple[str, ...] = ()
    _input_snapshot: tuple[object, ...] = field(init=False, repr=False)
    _identity_snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("Explicit behavior inputs cannot be subclassed.")

    def __post_init__(self) -> None:
        dispatch = _dispatch_for(self.behavior_id)
        _require_provenance(self.provenance_refs)
        if self.input_object is None:
            if not dispatch.certified_invalidity_input:
                raise ExplicitBehaviorExecutionError(
                    "Only no-rescue may explicitly report its missing trusted dependency."
                )
        elif type(self.input_object) is not dispatch.input_type:
            raise ExplicitBehaviorExecutionError(
                "The methodology input type does not match behavior_id."
            )
        object.__setattr__(self, "_input_snapshot", _snapshot(self.input_object))
        object.__setattr__(
            self,
            "_identity_snapshot",
            (self.behavior_id, self.input_object, self.provenance_refs),
        )

    def _validated(self) -> ExplicitBehaviorInput:
        if type(self) is not ExplicitBehaviorInput:
            raise ExplicitBehaviorExecutionError(
                "Behavior input must have its exact reviewed type."
            )
        try:
            identity = object.__getattribute__(self, "_identity_snapshot")
            input_snapshot = object.__getattribute__(self, "_input_snapshot")
        except AttributeError as error:
            raise ExplicitBehaviorExecutionError(
                "The behavior input is malformed."
            ) from error
        current = (self.behavior_id, self.input_object, self.provenance_refs)
        if len(identity) != len(current) or any(
            observed is not expected
            for observed, expected in zip(current, identity, strict=True)
        ):
            raise ExplicitBehaviorExecutionError(
                "The behavior input changed after construction."
            )
        dispatch = _dispatch_for(self.behavior_id)
        _require_provenance(self.provenance_refs)
        if self.input_object is None:
            if not dispatch.certified_invalidity_input:
                raise ExplicitBehaviorExecutionError(
                    "The behavior input lost its required methodology object."
                )
        elif type(self.input_object) is not dispatch.input_type:
            raise ExplicitBehaviorExecutionError(
                "The behavior input type changed or mismatches its behavior."
            )
        if not _snapshot_matches(self.input_object, input_snapshot):
            raise ExplicitBehaviorExecutionError(
                "The behavior input changed after construction."
            )
        return self

    def __copy__(self) -> ExplicitBehaviorInput:
        return self._validated()

    def __deepcopy__(self, memo: dict[int, object]) -> ExplicitBehaviorInput:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Explicit behavior inputs cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class ExplicitBehaviorExecutionRequest(metaclass=_SealedExecutionType):
    request_id: str
    requested_at_utc: str
    subject: AnalyzedWaveSubject
    candidate_id: str
    child_binding: OrderedChildBinding | None = None
    behavior_inputs: tuple[ExplicitBehaviorInput, ...] = ()
    observations: tuple[CandidateObservationAttachment, ...] = ()
    operational_resolution: BoundedRecursiveAnalysisResolution | None = None
    provenance_refs: tuple[str, ...] = ()
    _transport_probe: CandidateAnalysisEnvelope = field(init=False, repr=False)
    _identity_snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("Explicit behavior execution requests cannot be subclassed.")

    def __post_init__(self) -> None:
        _require_text(self.request_id, "request_id")
        _require_text(self.requested_at_utc, "requested_at_utc")
        _require_provenance(self.provenance_refs)
        if type(self.behavior_inputs) is not tuple or any(
            type(item) is not ExplicitBehaviorInput for item in self.behavior_inputs
        ):
            raise ExplicitBehaviorExecutionError(
                "behavior_inputs must be an exact tuple of exact execution inputs."
            )
        seen: list[tuple[str, object]] = []
        for item in self.behavior_inputs:
            item._validated()
            if any(
                _exact_behavior(item.behavior_id, behavior_id)
                and item.input_object is input_object
                for behavior_id, input_object in seen
            ):
                raise ExplicitBehaviorExecutionError(
                    "The same behavior and exact input identity cannot execute twice."
                )
            seen.append((item.behavior_id, item.input_object))
        probe = CandidateAnalysisEnvelope(
            subject=self.subject,
            candidate_id=self.candidate_id,
            child_binding=self.child_binding,
            observations=self.observations,
            operational_resolution=self.operational_resolution,
            provenance_refs=self.provenance_refs,
        )
        _validate_request_input_context(self)
        object.__setattr__(self, "_transport_probe", probe)
        object.__setattr__(
            self,
            "_identity_snapshot",
            (
                self.request_id,
                self.requested_at_utc,
                self.subject,
                self.candidate_id,
                self.child_binding,
                self.behavior_inputs,
                self.observations,
                self.operational_resolution,
                self.provenance_refs,
                probe,
            ),
        )

    def _validated(self) -> ExplicitBehaviorExecutionRequest:
        if type(self) is not ExplicitBehaviorExecutionRequest:
            raise ExplicitBehaviorExecutionError(
                "Execution request must have its exact reviewed type."
            )
        try:
            snapshot = object.__getattribute__(self, "_identity_snapshot")
            probe = object.__getattribute__(self, "_transport_probe")
        except AttributeError as error:
            raise ExplicitBehaviorExecutionError(
                "The execution request is malformed."
            ) from error
        current = (
            self.request_id,
            self.requested_at_utc,
            self.subject,
            self.candidate_id,
            self.child_binding,
            self.behavior_inputs,
            self.observations,
            self.operational_resolution,
            self.provenance_refs,
            probe,
        )
        if len(snapshot) != len(current) or any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            raise ExplicitBehaviorExecutionError(
                "The execution request changed after construction."
            )
        _require_text(self.request_id, "request_id")
        _require_text(self.requested_at_utc, "requested_at_utc")
        _require_provenance(self.provenance_refs)
        try:
            copy.copy(probe)
        except Exception as error:
            raise ExplicitBehaviorExecutionError(
                "The execution request transport context changed."
            ) from error
        for item in self.behavior_inputs:
            item._validated()
        _validate_request_input_context(self)
        return self

    def __copy__(self) -> ExplicitBehaviorExecutionRequest:
        return self._validated()

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> ExplicitBehaviorExecutionRequest:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Explicit behavior execution requests cannot be pickled.")


def _validate_request_input_context(request: ExplicitBehaviorExecutionRequest) -> None:
    for item in request.behavior_inputs:
        dispatch = _dispatch_for(item.behavior_id)
        if item.input_object is None:
            continue
        if dispatch.binding_consumer:
            binding = getattr(item.input_object, "binding", None)
            if binding is not request.child_binding:
                raise ExplicitBehaviorExecutionError(
                    "A cardinality input must consume the request's exact child binding."
                )
        if dispatch.certified_invalidity_input:
            try:
                binding = _origin_binding_from_certificate(item.input_object)
            except Exception as error:
                raise ExplicitBehaviorExecutionError(
                    "No-rescue requires one genuine live structural certificate."
                ) from error
            if binding is not None:
                if binding.parent_subject is not request.subject:
                    raise ExplicitBehaviorExecutionError(
                        "The certificate origin belongs to another subject."
                    )
                if binding is not request.child_binding:
                    raise ExplicitBehaviorExecutionError(
                        "The certificate origin binding differs from the request binding."
                    )


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class ExplicitBehaviorExecutionRecord(metaclass=_SealedExecutionType):
    behavior_id: str
    input_object: object
    result_object: object | None
    execution_state: ExplicitBehaviorExecutionState
    reason: str
    _identity_snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("Explicit behavior execution records cannot be subclassed.")

    def __post_init__(self) -> None:
        dispatch = _dispatch_for(self.behavior_id)
        if type(self.execution_state) is not ExplicitBehaviorExecutionState:
            raise ExplicitBehaviorExecutionError("Invalid execution-state type.")
        _require_text(self.reason, "reason")
        if self.execution_state is ExplicitBehaviorExecutionState.EXECUTED:
            if type(self.input_object) is not dispatch.input_type or self.result_object is None:
                raise ExplicitBehaviorExecutionError(
                    "EXECUTED requires the exact input and a genuine result."
                )
        elif (
            not dispatch.certified_invalidity_input
            or self.input_object is not None
            or self.result_object is not None
        ):
            raise ExplicitBehaviorExecutionError(
                "Only missing no-rescue certificate input may be dependency-blocked."
            )
        object.__setattr__(
            self,
            "_identity_snapshot",
            (
                self.behavior_id,
                self.input_object,
                self.result_object,
                self.execution_state,
                self.reason,
            ),
        )

    def _validated(self) -> ExplicitBehaviorExecutionRecord:
        if type(self) is not ExplicitBehaviorExecutionRecord:
            raise ExplicitBehaviorExecutionError(
                "Execution record must have its exact reviewed type."
            )
        try:
            snapshot = object.__getattribute__(self, "_identity_snapshot")
        except AttributeError as error:
            raise ExplicitBehaviorExecutionError(
                "Execution record is malformed."
            ) from error
        current = (
            self.behavior_id,
            self.input_object,
            self.result_object,
            self.execution_state,
            self.reason,
        )
        if len(snapshot) != len(current) or any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            raise ExplicitBehaviorExecutionError(
                "Execution record changed after creation."
            )
        return self

    def __copy__(self) -> ExplicitBehaviorExecutionRecord:
        return self._validated()

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> ExplicitBehaviorExecutionRecord:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Explicit behavior execution records cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True, init=False)
class ExplicitBehaviorExecutionResult(metaclass=_SealedExecutionType):
    request_id: str
    subject: AnalyzedWaveSubject
    candidate_envelope: CandidateAnalysisEnvelope
    methodology_evaluations: tuple[CandidateMethodologyEvaluation, ...]
    execution_records: tuple[ExplicitBehaviorExecutionRecord, ...]
    execution_unresolved_reasons: tuple[str, ...]
    single_candidate_analysis_result: SingleCandidateAnalysisResult | None
    provenance_refs: tuple[str, ...]
    _identity_snapshot: tuple[object, ...]

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError(
            "Explicit behavior execution results are created only by MethodologyKernel."
        )

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("Explicit behavior execution results cannot be subclassed.")

    def _validated(self) -> ExplicitBehaviorExecutionResult:
        if type(self) is not ExplicitBehaviorExecutionResult:
            raise ExplicitBehaviorExecutionError("Execution result has the wrong type.")
        try:
            snapshot = object.__getattribute__(self, "_identity_snapshot")
        except AttributeError as error:
            raise ExplicitBehaviorExecutionError("Execution result is malformed.") from error
        current = (
            self.request_id,
            self.subject,
            self.candidate_envelope,
            self.methodology_evaluations,
            self.execution_records,
            self.execution_unresolved_reasons,
            self.single_candidate_analysis_result,
            self.provenance_refs,
        )
        if len(snapshot) != len(current) or any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            raise ExplicitBehaviorExecutionError("Execution result changed after creation.")
        try:
            copy.copy(self.candidate_envelope)
            if self.single_candidate_analysis_result is not None:
                copy.copy(self.single_candidate_analysis_result)
        except Exception as error:
            raise ExplicitBehaviorExecutionError(
                "A nested execution result object changed."
            ) from error
        if self.subject is not self.candidate_envelope.subject:
            raise ExplicitBehaviorExecutionError("Result subject differs from envelope.")
        if self.methodology_evaluations is not self.candidate_envelope.methodology_evaluations:
            raise ExplicitBehaviorExecutionError("Result evaluation tuple was reconstructed.")
        if type(self.execution_records) is not tuple:
            raise ExplicitBehaviorExecutionError("Execution records must be an exact tuple.")
        executed_records = []
        blocked_reasons = []
        for record in self.execution_records:
            if type(record) is not ExplicitBehaviorExecutionRecord:
                raise ExplicitBehaviorExecutionError(
                    "Execution result contains a malformed record."
                )
            record._validated()
            if record.execution_state is ExplicitBehaviorExecutionState.EXECUTED:
                executed_records.append(record)
            else:
                blocked_reasons.append(record.reason)
        if len(executed_records) != len(self.methodology_evaluations):
            raise ExplicitBehaviorExecutionError(
                "Executed records and methodology evaluations differ."
            )
        for record, evaluation in zip(
            executed_records,
            self.methodology_evaluations,
            strict=True,
        ):
            if (
                not _exact_behavior(record.behavior_id, evaluation.behavior_id)
                or record.input_object is not evaluation.input_object
                or record.result_object is not evaluation.result_object
            ):
                raise ExplicitBehaviorExecutionError(
                    "Execution record and methodology evaluation identities differ."
                )
        if tuple(blocked_reasons) != self.execution_unresolved_reasons:
            raise ExplicitBehaviorExecutionError(
                "Dependency-block reasons differ from execution records."
            )
        if self.single_candidate_analysis_result is not None:
            if self.execution_unresolved_reasons:
                raise ExplicitBehaviorExecutionError(
                    "Dependency-blocked execution cannot claim completed orchestration."
                )
            if self.single_candidate_analysis_result.candidate_envelope is not self.candidate_envelope:
                raise ExplicitBehaviorExecutionError(
                    "Single-candidate analysis did not retain the exact envelope."
                )
        return self

    def __copy__(self) -> ExplicitBehaviorExecutionResult:
        return self._validated()

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> ExplicitBehaviorExecutionResult:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Explicit behavior execution results cannot be pickled.")


def _new_result(
    request: ExplicitBehaviorExecutionRequest,
    envelope: CandidateAnalysisEnvelope,
    records: tuple[ExplicitBehaviorExecutionRecord, ...],
    unresolved_reasons: tuple[str, ...],
    analysis: SingleCandidateAnalysisResult | None,
) -> ExplicitBehaviorExecutionResult:
    result = object.__new__(ExplicitBehaviorExecutionResult)
    values = {
        "request_id": request.request_id,
        "subject": request.subject,
        "candidate_envelope": envelope,
        "methodology_evaluations": envelope.methodology_evaluations,
        "execution_records": records,
        "execution_unresolved_reasons": unresolved_reasons,
        "single_candidate_analysis_result": analysis,
        "provenance_refs": request.provenance_refs,
    }
    for name, value in values.items():
        object.__setattr__(result, name, value)
    object.__setattr__(result, "_identity_snapshot", tuple(values.values()))
    return result._validated()


def _execute_candidate_inputs(
    request: object,
    analyze_candidate: Callable[[SingleCandidateAnalysisRequest], SingleCandidateAnalysisResult],
) -> ExplicitBehaviorExecutionResult:
    if type(request) is not ExplicitBehaviorExecutionRequest:
        raise ExplicitBehaviorExecutionError(
            "analyze_candidate_inputs requires one exact execution request."
        )
    request._validated()
    records: list[ExplicitBehaviorExecutionRecord] = []
    evaluations: list[CandidateMethodologyEvaluation] = []
    unresolved: list[str] = []
    for item in request.behavior_inputs:
        dispatch = _dispatch_for(item.behavior_id)
        if item.input_object is None:
            reason = MISSING_TRUSTED_INVALIDITY_CERTIFICATE
            records.append(
                ExplicitBehaviorExecutionRecord(
                    item.behavior_id,
                    None,
                    None,
                    ExplicitBehaviorExecutionState.BLOCKED_MISSING_TRUSTED_DEPENDENCY,
                    reason,
                )
            )
            unresolved.append(reason)
            continue
        result_object = (
            dispatch.validator(request.subject, item.input_object)
            if dispatch.subject_bound
            else dispatch.validator(item.input_object)
        )
        records.append(
            ExplicitBehaviorExecutionRecord(
                item.behavior_id,
                item.input_object,
                result_object,
                ExplicitBehaviorExecutionState.EXECUTED,
                "The exact reviewed validator executed with the supplied input.",
            )
        )
        evaluations.append(
            CandidateMethodologyEvaluation(
                subject=request.subject,
                behavior_id=item.behavior_id,
                input_object=item.input_object,
                result_object=result_object,
                provenance_refs=item.provenance_refs,
            )
        )
    envelope = CandidateAnalysisEnvelope(
        subject=request.subject,
        candidate_id=request.candidate_id,
        child_binding=request.child_binding,
        methodology_evaluations=tuple(evaluations),
        observations=request.observations,
        operational_resolution=request.operational_resolution,
        provenance_refs=request.provenance_refs,
    )
    analysis = None
    if not unresolved:
        analysis = analyze_candidate(
            SingleCandidateAnalysisRequest(
                request_id=request.request_id,
                requested_at_utc=request.requested_at_utc,
                candidate_envelope=envelope,
                provenance_refs=request.provenance_refs,
            )
        )
        if type(analysis) is not SingleCandidateAnalysisResult:
            raise ExplicitBehaviorExecutionError(
                "The existing candidate orchestrator returned an unexpected result."
            )
    return _new_result(
        request,
        envelope,
        tuple(records),
        tuple(unresolved),
        analysis,
    )


__all__ = [
    "ARTIFACT_CLASSIFICATION",
    "WORKFLOW_POLICY_CLASSIFICATION",
    "ExplicitBehaviorExecutionError",
    "ExplicitBehaviorExecutionRecord",
    "ExplicitBehaviorExecutionRequest",
    "ExplicitBehaviorExecutionResult",
    "ExplicitBehaviorExecutionState",
    "ExplicitBehaviorInput",
]
