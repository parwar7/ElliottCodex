"""Human-assisted degree declarations over one exact recursive candidate tree.

This module is PROJECT_ANALYSIS_INFRASTRUCTURE.  Degree declarations are
untrusted caller hypotheses.  Existing degree behaviors remain the only
methodology authority, and observation timeframe is never interpreted as
degree.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Callable

from .degree_peer_consistency import (
    DEGREE_PEER_BEHAVIOR_ID,
    DegreePeerCheckStatus,
    DegreePeerConsistencyInput,
)
from .explicit_behavior_execution import (
    ExplicitBehaviorExecutionRequest,
    ExplicitBehaviorExecutionResult,
    ExplicitBehaviorInput,
)
from .models import DegreeStatus, DegreeTreeNode, InternalStatus
from .multi_timeframe_observation_transport import (
    MultiTimeframeObservationTransportResult,
    TIMEFRAME_IS_NOT_DEGREE,
)
from .parent_child_degree_adjacency import (
    PARENT_CHILD_DEGREE_BEHAVIOR_ID,
    ParentChildDegreeCheckStatus,
    ParentChildDegreeInput,
)
from .recursive_candidate_composition import RecursiveCandidateCompositionResult
from .subject_binding import AnalyzedWaveSubject


ARTIFACT_CLASSIFICATION = "PROJECT_ANALYSIS_INFRASTRUCTURE"
DEGREE_DECLARATION_CLASSIFICATION = "CALLER_SUPPLIED_DEGREE_DECLARATION"
WORKFLOW_POLICY_CLASSIFICATION = "PROJECT_OPERATIONAL_POLICY"


class MultiDegreeCandidateCompositionError(ValueError):
    """Raised when degree-composition transport fails closed."""


class DegreeCompositionDiagnosticState(StrEnum):
    DEGREE_DECLARATION_SUPPLIED = "DEGREE_DECLARATION_SUPPLIED"
    NO_DEGREE_DECLARATION_SUPPLIED = "NO_DEGREE_DECLARATION_SUPPLIED"
    PEER_DEGREE_EVALUATED = "PEER_DEGREE_EVALUATED"
    PARENT_CHILD_DEGREE_EVALUATED = "PARENT_CHILD_DEGREE_EVALUATED"
    PEER_DEGREE_VIOLATION_REPORTED_BY_EXISTING_VALIDATOR = (
        "PEER_DEGREE_VIOLATION_REPORTED_BY_EXISTING_BEHAVIOR"
    )
    PARENT_CHILD_DEGREE_VIOLATION_REPORTED_BY_EXISTING_VALIDATOR = (
        "PARENT_CHILD_DEGREE_VIOLATION_REPORTED_BY_EXISTING_BEHAVIOR"
    )


class _SealedCompositionType(type):
    def __new__(
        mcls: type,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
        **kwargs: object,
    ) -> type:
        if any(isinstance(base, mcls) for base in bases):
            raise TypeError("Multi-degree composition types cannot be subclassed.")
        return super().__new__(mcls, name, bases, namespace, **kwargs)


def _require_text(value: object, name: str) -> str:
    if type(value) is not str or value.strip() == "":
        raise MultiDegreeCandidateCompositionError(
            f"{name} must be an exact non-blank string."
        )
    return value


def _require_provenance(value: object, name: str = "provenance_refs") -> tuple[str, ...]:
    if type(value) is not tuple or any(
        type(item) is not str or item.strip() == "" for item in value
    ):
        raise MultiDegreeCandidateCompositionError(
            f"{name} must be an exact tuple of non-blank strings."
        )
    return value


def _validate_recursive_result(value: object) -> RecursiveCandidateCompositionResult:
    if type(value) is not RecursiveCandidateCompositionResult:
        raise MultiDegreeCandidateCompositionError(
            "recursive_candidate_result must have its exact live result type."
        )
    try:
        return copy.copy(value)
    except Exception as error:
        raise MultiDegreeCandidateCompositionError(
            "The recursive candidate result is malformed or changed."
        ) from error


def _subject_and_node_inventory(
    result: RecursiveCandidateCompositionResult,
) -> tuple[tuple[AnalyzedWaveSubject, ...], tuple[object, ...]]:
    checked = _validate_recursive_result(result)
    subjects: list[AnalyzedWaveSubject] = []
    nodes: list[object] = []
    active: set[int] = set()

    def visit(node: object) -> None:
        node_id = id(node)
        if node_id in active:
            raise MultiDegreeCandidateCompositionError(
                "The recursive candidate tree contains a cycle."
            )
        active.add(node_id)
        try:
            subject = node.subject
            if any(subject is item for item in subjects):
                raise MultiDegreeCandidateCompositionError(
                    "The recursive candidate tree repeats one exact subject."
                )
            subjects.append(subject)
            nodes.append(node)
            for child in node.children:
                visit(child)
        finally:
            active.remove(node_id)

    visit(checked.parent_node)
    return tuple(subjects), tuple(nodes)


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class CandidateDegreeDeclaration(metaclass=_SealedCompositionType):
    """One untrusted, caller-supplied degree hypothesis for one exact subject."""

    subject: AnalyzedWaveSubject
    degree: str | None
    degree_status: DegreeStatus
    provenance_refs: tuple[str, ...] = ()
    _identity_snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if type(self.subject) is not AnalyzedWaveSubject:
            raise MultiDegreeCandidateCompositionError(
                "subject must be one exact AnalyzedWaveSubject."
            )
        if self.degree is not None and type(self.degree) is not str:
            raise MultiDegreeCandidateCompositionError(
                "degree must be an exact string or None."
            )
        if type(self.degree_status) is not DegreeStatus:
            raise MultiDegreeCandidateCompositionError(
                "degree_status must use the existing exact DegreeStatus."
            )
        _require_provenance(self.provenance_refs)
        object.__setattr__(
            self,
            "_identity_snapshot",
            (self.subject, self.degree, self.degree_status, self.provenance_refs),
        )

    def _validated(self) -> CandidateDegreeDeclaration:
        if type(self) is not CandidateDegreeDeclaration:
            raise MultiDegreeCandidateCompositionError(
                "Degree declarations must have their exact reviewed type."
            )
        try:
            snapshot = object.__getattribute__(self, "_identity_snapshot")
        except AttributeError as error:
            raise MultiDegreeCandidateCompositionError(
                "The degree declaration is malformed."
            ) from error
        current = (self.subject, self.degree, self.degree_status, self.provenance_refs)
        if len(snapshot) != len(current) or any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            raise MultiDegreeCandidateCompositionError(
                "The degree declaration changed after construction."
            )
        self.__post_init__()
        return self

    def __copy__(self) -> CandidateDegreeDeclaration:
        return self._validated()

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> CandidateDegreeDeclaration:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Candidate degree declarations cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class SubjectDegreeInventoryEntry(metaclass=_SealedCompositionType):
    subject: AnalyzedWaveSubject
    declaration: CandidateDegreeDeclaration | None
    _identity_snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if type(self.subject) is not AnalyzedWaveSubject:
            raise MultiDegreeCandidateCompositionError(
                "Inventory subject must have its exact type."
            )
        if self.declaration is not None:
            self.declaration._validated()
            if self.declaration.subject is not self.subject:
                raise MultiDegreeCandidateCompositionError(
                    "Inventory declaration belongs to another subject."
                )
        object.__setattr__(self, "_identity_snapshot", (self.subject, self.declaration))

    def _validated(self) -> SubjectDegreeInventoryEntry:
        try:
            snapshot = object.__getattribute__(self, "_identity_snapshot")
        except AttributeError as error:
            raise MultiDegreeCandidateCompositionError(
                "The subject-degree inventory entry is malformed."
            ) from error
        if type(self) is not SubjectDegreeInventoryEntry or any(
            observed is not expected
            for observed, expected in zip(
                (self.subject, self.declaration), snapshot, strict=True
            )
        ):
            raise MultiDegreeCandidateCompositionError(
                "The subject-degree inventory entry changed after construction."
            )
        return self


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class DegreeCompositionEvaluation(metaclass=_SealedCompositionType):
    behavior_id: str
    parent_subject: AnalyzedWaveSubject
    child_subjects: tuple[AnalyzedWaveSubject, ...]
    input_object: DegreePeerConsistencyInput | ParentChildDegreeInput
    result_object: object
    execution_result: ExplicitBehaviorExecutionResult
    provenance_refs: tuple[str, ...]
    _identity_snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        _require_text(self.behavior_id, "behavior_id")
        if type(self.parent_subject) is not AnalyzedWaveSubject:
            raise MultiDegreeCandidateCompositionError(
                "Evaluation parent subject must have its exact type."
            )
        if type(self.child_subjects) is not tuple or any(
            type(item) is not AnalyzedWaveSubject for item in self.child_subjects
        ):
            raise MultiDegreeCandidateCompositionError(
                "Evaluation child subjects must be an exact subject tuple."
            )
        _require_provenance(self.provenance_refs)
        if type(self.execution_result) is not ExplicitBehaviorExecutionResult:
            raise MultiDegreeCandidateCompositionError(
                "Evaluation must retain an exact execution result."
            )
        checked = copy.copy(self.execution_result)
        records = checked.execution_records
        if len(records) != 1:
            raise MultiDegreeCandidateCompositionError(
                "A degree evaluation must retain exactly one execution record."
            )
        record = records[0]
        if (
            record.behavior_id != self.behavior_id
            or record.input_object is not self.input_object
            or record.result_object is not self.result_object
            or checked.subject is not self.parent_subject
        ):
            raise MultiDegreeCandidateCompositionError(
                "Degree evaluation identities differ from the existing execution record."
            )
        object.__setattr__(
            self,
            "_identity_snapshot",
            (
                self.behavior_id,
                self.parent_subject,
                self.child_subjects,
                self.input_object,
                self.result_object,
                self.execution_result,
                self.provenance_refs,
            ),
        )

    def _validated(self) -> DegreeCompositionEvaluation:
        try:
            snapshot = object.__getattribute__(self, "_identity_snapshot")
        except AttributeError as error:
            raise MultiDegreeCandidateCompositionError(
                "The degree evaluation is malformed."
            ) from error
        current = (
            self.behavior_id,
            self.parent_subject,
            self.child_subjects,
            self.input_object,
            self.result_object,
            self.execution_result,
            self.provenance_refs,
        )
        if type(self) is not DegreeCompositionEvaluation or any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            raise MultiDegreeCandidateCompositionError(
                "The degree evaluation changed after construction."
            )
        self.__post_init__()
        return self


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class DegreeCompositionDiagnostic(metaclass=_SealedCompositionType):
    state: DegreeCompositionDiagnosticState
    subject: AnalyzedWaveSubject
    related_subjects: tuple[AnalyzedWaveSubject, ...]
    behavior_id: str | None
    reason: str
    _identity_snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if type(self.state) is not DegreeCompositionDiagnosticState:
            raise MultiDegreeCandidateCompositionError("Invalid diagnostic state.")
        if type(self.subject) is not AnalyzedWaveSubject:
            raise MultiDegreeCandidateCompositionError("Invalid diagnostic subject.")
        if type(self.related_subjects) is not tuple or any(
            type(item) is not AnalyzedWaveSubject for item in self.related_subjects
        ):
            raise MultiDegreeCandidateCompositionError(
                "Diagnostic related subjects must be an exact tuple."
            )
        if self.behavior_id is not None:
            _require_text(self.behavior_id, "behavior_id")
        _require_text(self.reason, "reason")
        object.__setattr__(
            self,
            "_identity_snapshot",
            (
                self.state,
                self.subject,
                self.related_subjects,
                self.behavior_id,
                self.reason,
            ),
        )

    def _validated(self) -> DegreeCompositionDiagnostic:
        try:
            snapshot = object.__getattribute__(self, "_identity_snapshot")
        except AttributeError as error:
            raise MultiDegreeCandidateCompositionError(
                "The degree diagnostic is malformed."
            ) from error
        current = (
            self.state,
            self.subject,
            self.related_subjects,
            self.behavior_id,
            self.reason,
        )
        if type(self) is not DegreeCompositionDiagnostic or any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            raise MultiDegreeCandidateCompositionError(
                "The degree diagnostic changed after construction."
            )
        self.__post_init__()
        return self


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class MultiDegreeCandidateCompositionRequest(metaclass=_SealedCompositionType):
    request_id: str
    requested_at_utc: str
    recursive_candidate_result: RecursiveCandidateCompositionResult
    degree_declarations: tuple[CandidateDegreeDeclaration, ...]
    multi_timeframe_context: MultiTimeframeObservationTransportResult | None = None
    provenance_refs: tuple[str, ...] = ()
    _identity_snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        _require_text(self.request_id, "request_id")
        _require_text(self.requested_at_utc, "requested_at_utc")
        _require_provenance(self.provenance_refs)
        result = _validate_recursive_result(self.recursive_candidate_result)
        subjects, _ = _subject_and_node_inventory(result)
        if type(self.degree_declarations) is not tuple:
            raise MultiDegreeCandidateCompositionError(
                "degree_declarations must be one exact tuple."
            )
        seen: list[AnalyzedWaveSubject] = []
        for declaration in self.degree_declarations:
            if type(declaration) is not CandidateDegreeDeclaration:
                raise MultiDegreeCandidateCompositionError(
                    "Every degree declaration must have its exact reviewed type."
                )
            declaration._validated()
            if not any(declaration.subject is subject for subject in subjects):
                raise MultiDegreeCandidateCompositionError(
                    "A degree declaration subject is foreign to the recursive tree."
                )
            if any(declaration.subject is subject for subject in seen):
                raise MultiDegreeCandidateCompositionError(
                    "At most one degree declaration is allowed per exact subject."
                )
            seen.append(declaration.subject)
        if self.multi_timeframe_context is not None:
            if type(self.multi_timeframe_context) is not MultiTimeframeObservationTransportResult:
                raise MultiDegreeCandidateCompositionError(
                    "multi_timeframe_context must have its exact live result type."
                )
            try:
                context = copy.copy(self.multi_timeframe_context)
            except Exception as error:
                raise MultiDegreeCandidateCompositionError(
                    "The multi-timeframe context is malformed or changed."
                ) from error
            if context.recursive_candidate_result is not result:
                raise MultiDegreeCandidateCompositionError(
                    "The multi-timeframe context belongs to another recursive result."
                )
        object.__setattr__(
            self,
            "_identity_snapshot",
            (
                self.request_id,
                self.requested_at_utc,
                self.recursive_candidate_result,
                self.degree_declarations,
                self.multi_timeframe_context,
                self.provenance_refs,
            ),
        )

    def _validated(self) -> MultiDegreeCandidateCompositionRequest:
        if type(self) is not MultiDegreeCandidateCompositionRequest:
            raise MultiDegreeCandidateCompositionError(
                "Composition requests must have their exact reviewed type."
            )
        try:
            snapshot = object.__getattribute__(self, "_identity_snapshot")
        except AttributeError as error:
            raise MultiDegreeCandidateCompositionError(
                "The multi-degree request is malformed."
            ) from error
        current = (
            self.request_id,
            self.requested_at_utc,
            self.recursive_candidate_result,
            self.degree_declarations,
            self.multi_timeframe_context,
            self.provenance_refs,
        )
        if len(snapshot) != len(current) or any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            raise MultiDegreeCandidateCompositionError(
                "The multi-degree request changed after construction."
            )
        self.__post_init__()
        return self

    def __copy__(self) -> MultiDegreeCandidateCompositionRequest:
        return self._validated()

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> MultiDegreeCandidateCompositionRequest:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Multi-degree composition requests cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True, init=False)
class MultiDegreeCandidateCompositionResult(metaclass=_SealedCompositionType):
    request_id: str
    recursive_candidate_result: RecursiveCandidateCompositionResult
    multi_timeframe_context: MultiTimeframeObservationTransportResult | None
    degree_declarations: tuple[CandidateDegreeDeclaration, ...]
    degree_evaluations: tuple[DegreeCompositionEvaluation, ...]
    subject_degree_inventory: tuple[SubjectDegreeInventoryEntry, ...]
    degree_diagnostics: tuple[DegreeCompositionDiagnostic, ...]
    provenance_refs: tuple[str, ...]
    _request: MultiDegreeCandidateCompositionRequest
    _identity_snapshot: tuple[object, ...]

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("Multi-degree results are created only by MethodologyKernel.")

    def _validated(self) -> MultiDegreeCandidateCompositionResult:
        if type(self) is not MultiDegreeCandidateCompositionResult:
            raise MultiDegreeCandidateCompositionError(
                "Composition results must have their exact live type."
            )
        try:
            request = object.__getattribute__(self, "_request")
            snapshot = object.__getattribute__(self, "_identity_snapshot")
        except AttributeError as error:
            raise MultiDegreeCandidateCompositionError(
                "The multi-degree result is malformed."
            ) from error
        current = (
            self.request_id,
            self.recursive_candidate_result,
            self.multi_timeframe_context,
            self.degree_declarations,
            self.degree_evaluations,
            self.subject_degree_inventory,
            self.degree_diagnostics,
            self.provenance_refs,
            request,
        )
        if len(snapshot) != len(current) or any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            raise MultiDegreeCandidateCompositionError(
                "The multi-degree result changed after construction."
            )
        request._validated()
        if (
            self.request_id is not request.request_id
            or self.recursive_candidate_result is not request.recursive_candidate_result
            or self.multi_timeframe_context is not request.multi_timeframe_context
            or self.degree_declarations is not request.degree_declarations
            or self.provenance_refs is not request.provenance_refs
        ):
            raise MultiDegreeCandidateCompositionError(
                "The result no longer retains exact request identities."
            )
        for item in self.degree_evaluations:
            if type(item) is not DegreeCompositionEvaluation:
                raise MultiDegreeCandidateCompositionError(
                    "Degree evaluations must retain their exact type."
                )
            item._validated()
        for item in self.subject_degree_inventory:
            if type(item) is not SubjectDegreeInventoryEntry:
                raise MultiDegreeCandidateCompositionError(
                    "Subject-degree inventory entries must retain their exact type."
                )
            item._validated()
        for item in self.degree_diagnostics:
            if type(item) is not DegreeCompositionDiagnostic:
                raise MultiDegreeCandidateCompositionError(
                    "Degree diagnostics must retain their exact type."
                )
            item._validated()
        return self

    def __copy__(self) -> MultiDegreeCandidateCompositionResult:
        return self._validated()

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> MultiDegreeCandidateCompositionResult:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Multi-degree composition results cannot be pickled.")


def _declaration_for(
    subject: AnalyzedWaveSubject,
    declarations: tuple[CandidateDegreeDeclaration, ...],
) -> CandidateDegreeDeclaration | None:
    return next(
        (item for item in declarations if item.subject is subject),
        None,
    )


def _execute_one(
    request: MultiDegreeCandidateCompositionRequest,
    execute: Callable[[ExplicitBehaviorExecutionRequest], ExplicitBehaviorExecutionResult],
    behavior_id: str,
    parent_subject: AnalyzedWaveSubject,
    child_subjects: tuple[AnalyzedWaveSubject, ...],
    input_object: DegreePeerConsistencyInput | ParentChildDegreeInput,
    sequence: int,
    provenance_refs: tuple[str, ...],
) -> DegreeCompositionEvaluation:
    explicit = ExplicitBehaviorInput(behavior_id, input_object, provenance_refs)
    execution = execute(
        ExplicitBehaviorExecutionRequest(
            request_id=f"{request.request_id}:degree:{sequence}",
            requested_at_utc=request.requested_at_utc,
            subject=parent_subject,
            candidate_id=f"{request.request_id}:degree-context:{sequence}",
            behavior_inputs=(explicit,),
            provenance_refs=request.provenance_refs,
        )
    )
    if type(execution) is not ExplicitBehaviorExecutionResult:
        raise MultiDegreeCandidateCompositionError(
            "The established execution boundary returned an unexpected type."
        )
    checked = copy.copy(execution)
    if len(checked.execution_records) != 1:
        raise MultiDegreeCandidateCompositionError(
            "The established execution boundary returned an unexpected record count."
        )
    result_object = checked.execution_records[0].result_object
    return DegreeCompositionEvaluation(
        behavior_id,
        parent_subject,
        child_subjects,
        input_object,
        result_object,
        execution,
        provenance_refs,
    )


def _compose_multi_degree_candidate(
    request: object,
    execute: Callable[[ExplicitBehaviorExecutionRequest], ExplicitBehaviorExecutionResult],
) -> MultiDegreeCandidateCompositionResult:
    if type(request) is not MultiDegreeCandidateCompositionRequest:
        raise MultiDegreeCandidateCompositionError(
            "compose_multi_degree_candidate requires one exact composition request."
        )
    request._validated()
    subjects, nodes = _subject_and_node_inventory(request.recursive_candidate_result)
    inventory = tuple(
        SubjectDegreeInventoryEntry(
            subject,
            _declaration_for(subject, request.degree_declarations),
        )
        for subject in subjects
    )
    diagnostics: list[DegreeCompositionDiagnostic] = []
    for item in inventory:
        supplied = item.declaration is not None
        diagnostics.append(
            DegreeCompositionDiagnostic(
                DegreeCompositionDiagnosticState.DEGREE_DECLARATION_SUPPLIED
                if supplied
                else DegreeCompositionDiagnosticState.NO_DEGREE_DECLARATION_SUPPLIED,
                item.subject,
                (),
                None,
                "An exact caller degree declaration is retained."
                if supplied
                else "NO_DEGREE_DECLARATION_SUPPLIED",
            )
        )

    evaluations: list[DegreeCompositionEvaluation] = []
    sequence = 0
    for node in nodes:
        parent_subject = node.subject
        parent_declaration = _declaration_for(
            parent_subject, request.degree_declarations
        )
        child_subjects = tuple(child.subject for child in node.children)
        child_declarations = tuple(
            _declaration_for(subject, request.degree_declarations)
            for subject in child_subjects
        )

        if len(child_subjects) >= 2 and all(
            declaration is not None for declaration in child_declarations
        ):
            sequence += 1
            resolved_children = tuple(child_declarations)
            peer_input = DegreePeerConsistencyInput(
                parent_subject.subject_id,
                tuple(
                    DegreeTreeNode(
                        child.subject_id,
                        declaration.degree,
                        declaration.degree_status,
                        InternalStatus.UNRESOLVED,
                        parent_subject.subject_id,
                    )
                    for child, declaration in zip(
                        child_subjects, resolved_children, strict=True
                    )
                ),
            )
            provenance = tuple(
                ref
                for declaration in resolved_children
                for ref in declaration.provenance_refs
            )
            evaluation = _execute_one(
                request,
                execute,
                DEGREE_PEER_BEHAVIOR_ID,
                parent_subject,
                child_subjects,
                peer_input,
                sequence,
                provenance,
            )
            evaluations.append(evaluation)
            violation = (
                evaluation.result_object.status is DegreePeerCheckStatus.RULE_VIOLATED
            )
            diagnostics.append(
                DegreeCompositionDiagnostic(
                    DegreeCompositionDiagnosticState.PEER_DEGREE_VIOLATION_REPORTED_BY_EXISTING_VALIDATOR
                    if violation
                    else DegreeCompositionDiagnosticState.PEER_DEGREE_EVALUATED,
                    parent_subject,
                    child_subjects,
                    DEGREE_PEER_BEHAVIOR_ID,
                    "The existing peer-degree behavior reported its retained result.",
                )
            )

        if parent_declaration is not None:
            for child_subject, child_declaration in zip(
                child_subjects, child_declarations, strict=True
            ):
                if child_declaration is None:
                    continue
                sequence += 1
                adjacency_input = ParentChildDegreeInput(
                    parent_declaration.degree,
                    parent_declaration.degree_status,
                    child_declaration.degree,
                    child_declaration.degree_status,
                )
                provenance = (
                    parent_declaration.provenance_refs
                    + child_declaration.provenance_refs
                )
                evaluation = _execute_one(
                    request,
                    execute,
                    PARENT_CHILD_DEGREE_BEHAVIOR_ID,
                    parent_subject,
                    (child_subject,),
                    adjacency_input,
                    sequence,
                    provenance,
                )
                evaluations.append(evaluation)
                violation = (
                    evaluation.result_object.status
                    is ParentChildDegreeCheckStatus.RULE_VIOLATED
                )
                diagnostics.append(
                    DegreeCompositionDiagnostic(
                        DegreeCompositionDiagnosticState.PARENT_CHILD_DEGREE_VIOLATION_REPORTED_BY_EXISTING_VALIDATOR
                        if violation
                        else DegreeCompositionDiagnosticState.PARENT_CHILD_DEGREE_EVALUATED,
                        parent_subject,
                        (child_subject,),
                        PARENT_CHILD_DEGREE_BEHAVIOR_ID,
                        "The existing parent-child degree behavior reported its retained result.",
                    )
                )

    result = object.__new__(MultiDegreeCandidateCompositionResult)
    values = {
        "request_id": request.request_id,
        "recursive_candidate_result": request.recursive_candidate_result,
        "multi_timeframe_context": request.multi_timeframe_context,
        "degree_declarations": request.degree_declarations,
        "degree_evaluations": tuple(evaluations),
        "subject_degree_inventory": inventory,
        "degree_diagnostics": tuple(diagnostics),
        "provenance_refs": request.provenance_refs,
        "_request": request,
    }
    for name, value in values.items():
        object.__setattr__(result, name, value)
    object.__setattr__(result, "_identity_snapshot", tuple(values.values()))
    return result._validated()


__all__ = [
    "ARTIFACT_CLASSIFICATION",
    "DEGREE_DECLARATION_CLASSIFICATION",
    "WORKFLOW_POLICY_CLASSIFICATION",
    "CandidateDegreeDeclaration",
    "DegreeCompositionDiagnostic",
    "DegreeCompositionDiagnosticState",
    "DegreeCompositionEvaluation",
    "MultiDegreeCandidateCompositionError",
    "MultiDegreeCandidateCompositionRequest",
    "MultiDegreeCandidateCompositionResult",
    "SubjectDegreeInventoryEntry",
    "TIMEFRAME_IS_NOT_DEGREE",
]
