"""Human-assisted candidate grouping from caller-supplied explicit pivots.

This is PROJECT_ANALYSIS_INFRASTRUCTURE. Pivots and groupings are untrusted
caller declarations, not discovered pivots, Elliott endpoints, family proof,
degree authority, methodology results, or certificates.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import datetime, timezone
import math
from typing import Callable, NoReturn

from .bounded_manual_chart_analysis import (
    BoundedManualChartAnalysisRequest,
    BoundedManualChartAnalysisResult,
)
from .candidate_analysis_envelope import CandidateObservationAttachment
from .human_readable_manual_candidate import (
    HumanReadableManualCandidateError,
    _enum,
    _exact_object,
    _fact,
    _list,
    _number,
    _subject,
    _text,
    render_manual_candidate_snapshot,
)
from .manual_structure_candidate_builder import (
    ManualDegreePeerFact,
    ManualDirectChildCardinalityFact,
    ManualP003OneLargerDegreeRelationFact,
    ManualP004Wave2OriginFact,
    ManualP023VisibilityFact,
    ManualParentChildDegreeFact,
)
from .observed_price_binding import (
    SubjectBoundObservedPriceEndpointPair,
    SubjectBoundObservedPriceObservation,
)
from .p004 import CandidateScope, ImpulseDirection
from .subject_binding import AnalyzedWaveSubject, OrderedChildBinding


ARTIFACT_CLASSIFICATION = "PROJECT_ANALYSIS_INFRASTRUCTURE"
WORKFLOW_POLICY_CLASSIFICATION = "PROJECT_OPERATIONAL_POLICY"
PIVOT_CLASSIFICATION = "CALLER_SUPPLIED_PIVOT_OBSERVATION"
GROUPING_CLASSIFICATION = "CALLER_SUPPLIED_STRUCTURE_DECLARATION"
EXPLICIT_PIVOT_INPUT_SCHEMA_VERSION = "HUMAN_READABLE_EXPLICIT_PIVOT_CANDIDATE_V1"
EXPLICIT_PIVOT_REPORT_SCHEMA_VERSION = "EXPLICIT_PIVOT_CANDIDATE_REPORT_V1"


class ExplicitPivotCandidateError(ValueError):
    """Raised when explicit-pivot infrastructure fails closed."""


class _SealedPivotType(type):
    def __new__(
        mcls: type,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
        **kwargs: object,
    ) -> type:
        if any(isinstance(base, mcls) for base in bases):
            raise TypeError("Explicit-pivot infrastructure cannot be subclassed.")
        return super().__new__(mcls, name, bases, namespace, **kwargs)


def _fail(message: str) -> NoReturn:
    raise ExplicitPivotCandidateError(message)


def _require_text(value: object, name: str) -> str:
    if type(value) is not str or value.strip() == "":
        _fail(f"{name} must be one exact non-blank string.")
    return value


def _require_provenance(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or any(
        type(item) is not str or item.strip() == "" for item in value
    ):
        _fail("provenance_refs must be an exact tuple of non-blank strings.")
    return value


def _require_price(value: object) -> int | float:
    if (
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(value)
    ):
        _fail("observed_price must be one explicit finite int or float.")
    return value


def _parse_timestamp(value: object) -> datetime:
    timestamp = _require_text(value, "timestamp_utc")
    if "T" not in timestamp or not timestamp.endswith("Z"):
        _fail("timestamp_utc must be an explicit ISO-8601 UTC value ending in Z.")
    try:
        instant = datetime.fromisoformat(timestamp[:-1] + "+00:00")
    except ValueError as error:
        raise ExplicitPivotCandidateError(
            "timestamp_utc must be a valid ISO-8601 UTC value."
        ) from error
    if instant.tzinfo is None or instant.utcoffset() != timezone.utc.utcoffset(instant):
        _fail("timestamp_utc must resolve exactly to UTC.")
    return instant


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class ExplicitPivotObservation(metaclass=_SealedPivotType):
    pivot_id: str
    timestamp_utc: str
    observed_price: int | float
    provenance_refs: tuple[str, ...] = ()
    _instant_utc: datetime = field(init=False, repr=False)
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        _require_text(self.pivot_id, "pivot_id")
        instant = _parse_timestamp(self.timestamp_utc)
        _require_price(self.observed_price)
        _require_provenance(self.provenance_refs)
        object.__setattr__(self, "_instant_utc", instant)
        object.__setattr__(
            self,
            "_snapshot",
            (self.pivot_id, self.timestamp_utc, self.observed_price, self.provenance_refs),
        )

    @property
    def classification(self) -> str:
        return PIVOT_CLASSIFICATION

    def _validated(self) -> ExplicitPivotObservation:
        if type(self) is not ExplicitPivotObservation:
            _fail("Pivot must have its exact reviewed type.")
        try:
            snapshot = object.__getattribute__(self, "_snapshot")
            instant = object.__getattribute__(self, "_instant_utc")
        except AttributeError as error:
            raise ExplicitPivotCandidateError("Pivot is malformed.") from error
        current = (self.pivot_id, self.timestamp_utc, self.observed_price, self.provenance_refs)
        if current != snapshot or _parse_timestamp(self.timestamp_utc) != instant:
            _fail("Pivot changed after construction.")
        _require_price(self.observed_price)
        _require_provenance(self.provenance_refs)
        return self

    def __copy__(self) -> ExplicitPivotObservation:
        return self._validated()

    def __deepcopy__(self, memo: dict[int, object]) -> ExplicitPivotObservation:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Explicit pivot observations cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class ExplicitPivotChildGroup(metaclass=_SealedPivotType):
    group_id: str
    parent_subject: AnalyzedWaveSubject
    child_subject: AnalyzedWaveSubject
    start_pivot: ExplicitPivotObservation
    end_pivot: ExplicitPivotObservation
    provenance_refs: tuple[str, ...] = ()
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        _require_text(self.group_id, "group_id")
        if type(self.parent_subject) is not AnalyzedWaveSubject:
            _fail("parent_subject must be one exact AnalyzedWaveSubject.")
        if type(self.child_subject) is not AnalyzedWaveSubject:
            _fail("child_subject must be one exact AnalyzedWaveSubject.")
        if type(self.start_pivot) is not ExplicitPivotObservation or type(
            self.end_pivot
        ) is not ExplicitPivotObservation:
            _fail("Group boundaries must be exact explicit pivots.")
        self.start_pivot._validated()
        self.end_pivot._validated()
        if self.start_pivot is self.end_pivot:
            _fail("A child group requires distinct start and end pivots.")
        _require_provenance(self.provenance_refs)
        object.__setattr__(
            self,
            "_snapshot",
            (
                self.group_id,
                self.parent_subject,
                self.child_subject,
                self.start_pivot,
                self.end_pivot,
                self.provenance_refs,
            ),
        )

    @property
    def classification(self) -> str:
        return GROUPING_CLASSIFICATION

    def _validated(self) -> ExplicitPivotChildGroup:
        if type(self) is not ExplicitPivotChildGroup:
            _fail("Child group must have its exact reviewed type.")
        try:
            snapshot = object.__getattribute__(self, "_snapshot")
        except AttributeError as error:
            raise ExplicitPivotCandidateError("Child group is malformed.") from error
        current = (
            self.group_id,
            self.parent_subject,
            self.child_subject,
            self.start_pivot,
            self.end_pivot,
            self.provenance_refs,
        )
        if len(snapshot) != len(current) or any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            _fail("Child group changed after construction.")
        self.start_pivot._validated()
        self.end_pivot._validated()
        _require_provenance(self.provenance_refs)
        return self

    def __copy__(self) -> ExplicitPivotChildGroup:
        return self._validated()

    def __deepcopy__(self, memo: dict[int, object]) -> ExplicitPivotChildGroup:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Explicit pivot child groups cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class ExplicitP004PivotRole(metaclass=_SealedPivotType):
    candidate_scope: CandidateScope
    direction: ImpulseDirection
    wave1_origin_pivot: ExplicitPivotObservation
    wave2_end_pivot: ExplicitPivotObservation
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if type(self.candidate_scope) is not CandidateScope:
            _fail("candidate_scope must use the exact existing CandidateScope token.")
        if type(self.direction) is not ImpulseDirection:
            _fail("direction must use the exact existing ImpulseDirection token.")
        if type(self.wave1_origin_pivot) is not ExplicitPivotObservation or type(
            self.wave2_end_pivot
        ) is not ExplicitPivotObservation:
            _fail("P004 roles must reference exact explicit pivots.")
        self.wave1_origin_pivot._validated()
        self.wave2_end_pivot._validated()
        object.__setattr__(
            self,
            "_snapshot",
            (
                self.candidate_scope,
                self.direction,
                self.wave1_origin_pivot,
                self.wave2_end_pivot,
            ),
        )

    def _validated(self) -> ExplicitP004PivotRole:
        if type(self) is not ExplicitP004PivotRole:
            _fail("P004 pivot role must have its exact reviewed type.")
        try:
            snapshot = object.__getattribute__(self, "_snapshot")
        except AttributeError as error:
            raise ExplicitPivotCandidateError("P004 pivot role is malformed.") from error
        current = (
            self.candidate_scope,
            self.direction,
            self.wave1_origin_pivot,
            self.wave2_end_pivot,
        )
        if len(snapshot) != len(current) or any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            _fail("P004 pivot role changed after construction.")
        self.wave1_origin_pivot._validated()
        self.wave2_end_pivot._validated()
        return self

    def __copy__(self) -> ExplicitP004PivotRole:
        return self._validated()

    def __deepcopy__(self, memo: dict[int, object]) -> ExplicitP004PivotRole:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Explicit P004 pivot roles cannot be pickled.")


_PASSTHROUGH_FACT_TYPES = (
    ManualDegreePeerFact,
    ManualParentChildDegreeFact,
    ManualP023VisibilityFact,
    ManualP003OneLargerDegreeRelationFact,
    ManualDirectChildCardinalityFact,
)


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class ExplicitPivotCandidateRequest(metaclass=_SealedPivotType):
    request_id: str
    requested_at_utc: str
    candidate_id: str
    parent_subject: AnalyzedWaveSubject
    ordered_pivots: tuple[ExplicitPivotObservation, ...]
    ordered_child_groups: tuple[ExplicitPivotChildGroup, ...] = ()
    binding_id: str | None = None
    manual_fact_declarations: tuple[object, ...] = ()
    provenance_refs: tuple[str, ...] = ()
    _child_binding: OrderedChildBinding | None = field(init=False, repr=False)
    _value_snapshot: tuple[object, ...] = field(init=False, repr=False)
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        _require_text(self.request_id, "request_id")
        _require_text(self.requested_at_utc, "requested_at_utc")
        _require_text(self.candidate_id, "candidate_id")
        if type(self.parent_subject) is not AnalyzedWaveSubject:
            _fail("parent_subject must be one exact AnalyzedWaveSubject.")
        _require_provenance(self.provenance_refs)
        if type(self.ordered_pivots) is not tuple:
            _fail("ordered_pivots must be one exact tuple.")
        pivot_ids: set[str] = set()
        pivot_objects: set[int] = set()
        previous: datetime | None = None
        for pivot in self.ordered_pivots:
            if type(pivot) is not ExplicitPivotObservation:
                _fail("Every pivot must have the exact explicit-pivot type.")
            pivot._validated()
            if id(pivot) in pivot_objects:
                _fail("The same exact pivot identity cannot appear twice.")
            if pivot.pivot_id in pivot_ids:
                _fail("Pivot IDs must be unique within one candidate request.")
            if previous is not None and pivot._instant_utc <= previous:
                _fail("Pivot timestamps must be strictly increasing in supplied order.")
            pivot_objects.add(id(pivot))
            pivot_ids.add(pivot.pivot_id)
            previous = pivot._instant_utc
        if type(self.ordered_child_groups) is not tuple:
            _fail("ordered_child_groups must be one exact tuple.")
        index_by_identity = {id(pivot): index for index, pivot in enumerate(self.ordered_pivots)}
        group_ids: set[str] = set()
        previous_end = -1
        for group in self.ordered_child_groups:
            if type(group) is not ExplicitPivotChildGroup:
                _fail("Every child group must have its exact reviewed type.")
            group._validated()
            if group.parent_subject is not self.parent_subject:
                _fail("A child group belongs to another parent subject identity.")
            if group.group_id in group_ids:
                _fail("Child group IDs must be unique within one request.")
            try:
                start_index = index_by_identity[id(group.start_pivot)]
                end_index = index_by_identity[id(group.end_pivot)]
            except KeyError as error:
                raise ExplicitPivotCandidateError(
                    "Every group boundary must reference a pivot from this exact request."
                ) from error
            if start_index >= end_index:
                _fail("Each child group start pivot must precede its end pivot.")
            if start_index < previous_end:
                _fail("Child groups must be ordered and cannot overlap beyond a shared boundary.")
            group_ids.add(group.group_id)
            previous_end = end_index
        if self.ordered_child_groups:
            _require_text(self.binding_id, "binding_id")
            child_binding = OrderedChildBinding(
                self.binding_id,
                self.parent_subject,
                tuple(group.child_subject for group in self.ordered_child_groups),
            )
        else:
            if self.binding_id is not None:
                _fail("binding_id requires at least one explicit child group.")
            child_binding = None
        if type(self.manual_fact_declarations) is not tuple:
            _fail("manual_fact_declarations must be one exact tuple.")
        seen: set[int] = set()
        pivot_identity = set(index_by_identity)
        for declaration in self.manual_fact_declarations:
            if id(declaration) in seen:
                _fail("The same exact manual declaration cannot appear twice.")
            seen.add(id(declaration))
            if type(declaration) is ExplicitP004PivotRole:
                declaration._validated()
                if (
                    id(declaration.wave1_origin_pivot) not in pivot_identity
                    or id(declaration.wave2_end_pivot) not in pivot_identity
                ):
                    _fail("P004 roles must reference pivots from this exact request.")
            elif type(declaration) in _PASSTHROUGH_FACT_TYPES:
                declaration.__post_init__()
                if (
                    type(declaration) is ManualP023VisibilityFact
                    and declaration.subject is not self.parent_subject
                ):
                    _fail("The explicit P023 declaration belongs to another subject.")
            else:
                _fail("Unsupported explicit-pivot manual declaration type.")
        object.__setattr__(self, "_child_binding", child_binding)
        object.__setattr__(
            self,
            "_value_snapshot",
            (
                repr(self.parent_subject),
                tuple(repr(group) for group in self.ordered_child_groups),
                tuple(repr(item) for item in self.manual_fact_declarations),
                repr(child_binding),
            ),
        )
        object.__setattr__(
            self,
            "_snapshot",
            (
                self.request_id,
                self.requested_at_utc,
                self.candidate_id,
                self.parent_subject,
                self.ordered_pivots,
                self.ordered_child_groups,
                self.binding_id,
                self.manual_fact_declarations,
                self.provenance_refs,
                child_binding,
            ),
        )

    @property
    def child_binding(self) -> OrderedChildBinding | None:
        return self._validated()._child_binding

    def _validated(self) -> ExplicitPivotCandidateRequest:
        if type(self) is not ExplicitPivotCandidateRequest:
            _fail("Explicit-pivot request must have its exact reviewed type.")
        try:
            snapshot = object.__getattribute__(self, "_snapshot")
            child_binding = object.__getattribute__(self, "_child_binding")
            value_snapshot = object.__getattribute__(self, "_value_snapshot")
        except AttributeError as error:
            raise ExplicitPivotCandidateError("Explicit-pivot request is malformed.") from error
        current = (
            self.request_id,
            self.requested_at_utc,
            self.candidate_id,
            self.parent_subject,
            self.ordered_pivots,
            self.ordered_child_groups,
            self.binding_id,
            self.manual_fact_declarations,
            self.provenance_refs,
            child_binding,
        )
        if len(snapshot) != len(current) or any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            _fail("Explicit-pivot request changed after construction.")
        for pivot in self.ordered_pivots:
            pivot._validated()
        for group in self.ordered_child_groups:
            group._validated()
        for declaration in self.manual_fact_declarations:
            if type(declaration) is ExplicitP004PivotRole:
                declaration._validated()
            else:
                declaration.__post_init__()
        current_values = (
            repr(self.parent_subject),
            tuple(repr(group) for group in self.ordered_child_groups),
            tuple(repr(item) for item in self.manual_fact_declarations),
            repr(child_binding),
        )
        if current_values != value_snapshot:
            _fail("An explicit-pivot request value changed after construction.")
        if child_binding is not None and (
            child_binding.parent_subject is not self.parent_subject
            or child_binding.binding_id != self.binding_id
            or len(child_binding.ordered_children) != len(self.ordered_child_groups)
            or any(
                child is not group.child_subject
                for child, group in zip(
                    child_binding.ordered_children,
                    self.ordered_child_groups,
                    strict=True,
                )
            )
        ):
            _fail("The constructed child binding changed after request construction.")
        return self

    def __copy__(self) -> ExplicitPivotCandidateRequest:
        return self._validated()

    def __deepcopy__(self, memo: dict[int, object]) -> ExplicitPivotCandidateRequest:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Explicit-pivot candidate requests cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True, init=False)
class ExplicitPivotCandidateBuildResult(metaclass=_SealedPivotType):
    request: ExplicitPivotCandidateRequest
    child_binding: OrderedChildBinding | None
    parent_pivot_observations: tuple[SubjectBoundObservedPriceObservation, ...]
    child_endpoint_pairs: tuple[SubjectBoundObservedPriceEndpointPair, ...]
    generated_manual_facts: tuple[object, ...]
    bounded_request: BoundedManualChartAnalysisRequest
    bounded_result: BoundedManualChartAnalysisResult
    provenance_refs: tuple[str, ...]
    _snapshot: tuple[object, ...]

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("Explicit-pivot build results are created only by MethodologyKernel.")

    def _validated(self) -> ExplicitPivotCandidateBuildResult:
        if type(self) is not ExplicitPivotCandidateBuildResult:
            _fail("Explicit-pivot result must have its exact reviewed type.")
        try:
            snapshot = object.__getattribute__(self, "_snapshot")
        except AttributeError as error:
            raise ExplicitPivotCandidateError("Explicit-pivot result is malformed.") from error
        current = (
            self.request,
            self.child_binding,
            self.parent_pivot_observations,
            self.child_endpoint_pairs,
            self.generated_manual_facts,
            self.bounded_request,
            self.bounded_result,
            self.provenance_refs,
        )
        if len(snapshot) != len(current) or any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            _fail("Explicit-pivot result changed after creation.")
        self.request._validated()
        try:
            copy.copy(self.bounded_request)
            copy.copy(self.bounded_result)
        except Exception as error:
            raise ExplicitPivotCandidateError(
                "A nested explicit-pivot result object changed."
            ) from error
        if self.bounded_request.subject is not self.request.parent_subject:
            _fail("The bounded request retained another subject.")
        if self.bounded_result.subject is not self.request.parent_subject:
            _fail("The bounded result retained another subject.")
        if self.bounded_request.child_binding is not self.child_binding:
            _fail("The bounded request did not retain the constructed binding.")
        if len(self.parent_pivot_observations) != len(self.request.ordered_pivots):
            _fail("Parent pivot observations no longer align with supplied pivots.")
        for pivot, observation in zip(
            self.request.ordered_pivots,
            self.parent_pivot_observations,
            strict=True,
        ):
            if (
                type(observation) is not SubjectBoundObservedPriceObservation
                or observation.subject is not self.request.parent_subject
                or observation.price != pivot.observed_price
            ):
                _fail("A parent pivot observation changed or lost its exact alignment.")
        if len(self.child_endpoint_pairs) != len(self.request.ordered_child_groups):
            _fail("Child endpoint pairs no longer align with explicit groups.")
        for group, pair in zip(
            self.request.ordered_child_groups,
            self.child_endpoint_pairs,
            strict=True,
        ):
            if (
                type(pair) is not SubjectBoundObservedPriceEndpointPair
                or pair.subject is not group.child_subject
                or pair.proposed_start.price != group.start_pivot.observed_price
                or pair.proposed_end.price != group.end_pivot.observed_price
            ):
                _fail("A child endpoint pair changed or lost its exact group alignment.")
        return self

    def __copy__(self) -> ExplicitPivotCandidateBuildResult:
        return self._validated()

    def __deepcopy__(self, memo: dict[int, object]) -> ExplicitPivotCandidateBuildResult:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Explicit-pivot build results cannot be pickled.")


def _generated_facts(request: ExplicitPivotCandidateRequest) -> tuple[object, ...]:
    generated = []
    for declaration in request.manual_fact_declarations:
        if type(declaration) is ExplicitP004PivotRole:
            generated.append(
                ManualP004Wave2OriginFact(
                    declaration.candidate_scope,
                    declaration.direction,
                    declaration.wave1_origin_pivot.observed_price,
                    declaration.wave2_end_pivot.observed_price,
                )
            )
        else:
            generated.append(declaration)
    return tuple(generated)


def _new_result(
    request: ExplicitPivotCandidateRequest,
    observations: tuple[SubjectBoundObservedPriceObservation, ...],
    endpoint_pairs: tuple[SubjectBoundObservedPriceEndpointPair, ...],
    facts: tuple[object, ...],
    bounded_request: BoundedManualChartAnalysisRequest,
    bounded_result: BoundedManualChartAnalysisResult,
) -> ExplicitPivotCandidateBuildResult:
    result = object.__new__(ExplicitPivotCandidateBuildResult)
    values = {
        "request": request,
        "child_binding": request._child_binding,
        "parent_pivot_observations": observations,
        "child_endpoint_pairs": endpoint_pairs,
        "generated_manual_facts": facts,
        "bounded_request": bounded_request,
        "bounded_result": bounded_result,
        "provenance_refs": request.provenance_refs,
    }
    for name, value in values.items():
        object.__setattr__(result, name, value)
    object.__setattr__(result, "_snapshot", tuple(values.values()))
    return result._validated()


def _analyze_explicit_pivot_candidate(
    request: object,
    analyze_bounded_manual_chart: Callable[
        [BoundedManualChartAnalysisRequest], BoundedManualChartAnalysisResult
    ],
) -> ExplicitPivotCandidateBuildResult:
    if type(request) is not ExplicitPivotCandidateRequest:
        _fail("analyze_explicit_pivot_candidate requires one exact request.")
    request._validated()
    observations = tuple(
        SubjectBoundObservedPriceObservation(
            request.parent_subject,
            pivot.observed_price,
            (
                pivot.provenance_refs[0]
                if pivot.provenance_refs
                else request.parent_subject.observation_provenance_ref
            ),
        )
        for pivot in request.ordered_pivots
    )
    attachments = tuple(
        CandidateObservationAttachment(
            request.parent_subject,
            observation,
            request.provenance_refs + pivot.provenance_refs,
        )
        for pivot, observation in zip(request.ordered_pivots, observations, strict=True)
    )
    endpoint_pairs = tuple(
        SubjectBoundObservedPriceEndpointPair(
            SubjectBoundObservedPriceObservation(
                group.child_subject,
                group.start_pivot.observed_price,
                (
                    group.provenance_refs[0]
                    if group.provenance_refs
                    else group.child_subject.observation_provenance_ref
                ),
            ),
            SubjectBoundObservedPriceObservation(
                group.child_subject,
                group.end_pivot.observed_price,
                (
                    group.provenance_refs[0]
                    if group.provenance_refs
                    else group.child_subject.observation_provenance_ref
                ),
            ),
        )
        for group in request.ordered_child_groups
    )
    facts = _generated_facts(request)
    bounded_request = BoundedManualChartAnalysisRequest(
        request_id=request.request_id,
        requested_at_utc=request.requested_at_utc,
        subject=request.parent_subject,
        candidate_id=request.candidate_id,
        manual_behavior_facts=facts,
        child_binding=request._child_binding,
        observations=attachments,
        provenance_refs=request.provenance_refs,
    )
    bounded_result = analyze_bounded_manual_chart(bounded_request)
    if type(bounded_result) is not BoundedManualChartAnalysisResult:
        _fail("The bounded manual-chart API returned an unexpected result type.")
    return _new_result(
        request,
        observations,
        endpoint_pairs,
        facts,
        bounded_request,
        bounded_result,
    )


def render_explicit_pivot_report(
    result: ExplicitPivotCandidateBuildResult,
) -> dict[str, object]:
    """Return one non-authoritative reporting view of exact retained state."""
    if type(result) is not ExplicitPivotCandidateBuildResult:
        _fail("Pivot reporting requires one exact build result.")
    result._validated()
    downstream = render_manual_candidate_snapshot(result.bounded_result)
    return {
        "schema_version": EXPLICIT_PIVOT_REPORT_SCHEMA_VERSION,
        "artifact_classification": ARTIFACT_CLASSIFICATION,
        "authority": "NON_AUTHORITATIVE_REPORTING_VIEW",
        "candidate_id": result.request.candidate_id,
        "parent_subject_id": result.request.parent_subject.subject_id,
        "pivot_count": len(result.request.ordered_pivots),
        "child_group_count": len(result.request.ordered_child_groups),
        "constructed_binding": result.child_binding is not None,
        "generated_manual_fact_types": [
            type(item).__name__ for item in result.generated_manual_facts
        ],
        "final_summary": downstream["final_summary"],
        "reviewed_is_valid": False,
        "unresolved_reasons": downstream["unresolved_reasons"],
        "methodology_coverage": downstream["methodology_coverage"],
        "downstream_snapshot": downstream,
    }


def parse_human_readable_explicit_pivot_candidate(
    document: object,
) -> ExplicitPivotCandidateRequest:
    """Resolve one closed JSON-shaped pivot document to exact live objects."""
    try:
        root = _exact_object(
            document,
            "document",
            required=frozenset(
                {
                    "schema_version",
                    "request_id",
                    "requested_at_utc",
                    "candidate_id",
                    "subject",
                    "pivots",
                    "child_groups",
                    "facts",
                    "provenance_refs",
                }
            ),
            optional=frozenset({"binding_id"}),
        )
        if _text(root["schema_version"], "schema_version") != EXPLICIT_PIVOT_INPUT_SCHEMA_VERSION:
            _fail(
                "schema_version must be exactly "
                f"{EXPLICIT_PIVOT_INPUT_SCHEMA_VERSION}."
            )
        parent = _subject(root["subject"], "subject")

        def refs(value: object, name: str) -> tuple[str, ...]:
            return tuple(
                _text(item, f"{name}[{index}]")
                for index, item in enumerate(_list(value, name))
            )

        pivots = []
        pivot_by_id: dict[str, ExplicitPivotObservation] = {}
        for index, raw in enumerate(_list(root["pivots"], "pivots")):
            name = f"pivots[{index}]"
            item = _exact_object(
                raw,
                name,
                required=frozenset({"pivot_id", "timestamp_utc", "observed_price"}),
                optional=frozenset({"provenance_refs"}),
            )
            pivot_id = _text(item["pivot_id"], f"{name}.pivot_id")
            if pivot_id in pivot_by_id:
                _fail("Pivot IDs must be unique within one document.")
            pivot = ExplicitPivotObservation(
                pivot_id,
                _text(item["timestamp_utc"], f"{name}.timestamp_utc"),
                _number(item["observed_price"], f"{name}.observed_price"),
                refs(item.get("provenance_refs", []), f"{name}.provenance_refs"),
            )
            pivots.append(pivot)
            pivot_by_id[pivot_id] = pivot

        def pivot_ref(value: object, name: str) -> ExplicitPivotObservation:
            pivot_id = _text(value, name)
            try:
                return pivot_by_id[pivot_id]
            except KeyError as error:
                raise ExplicitPivotCandidateError(
                    f"{name} references unknown pivot_id: {pivot_id}."
                ) from error

        groups = []
        for index, raw in enumerate(_list(root["child_groups"], "child_groups")):
            name = f"child_groups[{index}]"
            item = _exact_object(
                raw,
                name,
                required=frozenset(
                    {"group_id", "subject", "start_pivot_id", "end_pivot_id"}
                ),
                optional=frozenset({"provenance_refs"}),
            )
            groups.append(
                ExplicitPivotChildGroup(
                    _text(item["group_id"], f"{name}.group_id"),
                    parent,
                    _subject(item["subject"], f"{name}.subject"),
                    pivot_ref(item["start_pivot_id"], f"{name}.start_pivot_id"),
                    pivot_ref(item["end_pivot_id"], f"{name}.end_pivot_id"),
                    refs(item.get("provenance_refs", []), f"{name}.provenance_refs"),
                )
            )

        declarations = []
        for index, raw in enumerate(_list(root["facts"], "facts")):
            name = f"facts[{index}]"
            discriminator = _exact_object(
                raw,
                name,
                required=frozenset({"type"}),
                optional=frozenset(
                    {
                        "candidate_scope",
                        "direction",
                        "wave1_origin_pivot_id",
                        "wave2_end_pivot_id",
                        "parent_node_id",
                        "direct_child_degrees",
                        "parent_degree",
                        "parent_degree_status",
                        "child_degree",
                        "child_degree_status",
                        "visibility_state",
                        "relation",
                        "behavior",
                    }
                ),
            )
            fact_type = _text(discriminator["type"], f"{name}.type")
            if fact_type == "P004_PIVOT_ROLE":
                item = _exact_object(
                    raw,
                    name,
                    required=frozenset(
                        {
                            "type",
                            "candidate_scope",
                            "direction",
                            "wave1_origin_pivot_id",
                            "wave2_end_pivot_id",
                        }
                    ),
                )
                declarations.append(
                    ExplicitP004PivotRole(
                        _enum(
                            item["candidate_scope"],
                            CandidateScope,
                            f"{name}.candidate_scope",
                        ),
                        _enum(item["direction"], ImpulseDirection, f"{name}.direction"),
                        pivot_ref(
                            item["wave1_origin_pivot_id"],
                            f"{name}.wave1_origin_pivot_id",
                        ),
                        pivot_ref(
                            item["wave2_end_pivot_id"],
                            f"{name}.wave2_end_pivot_id",
                        ),
                    )
                )
            else:
                fact = _fact(raw, parent, index)
                if type(fact) is ManualP004Wave2OriginFact:
                    _fail("Pivot documents require explicit P004 pivot-role references.")
                declarations.append(fact)
        binding_id_value = root.get("binding_id")
        binding_id = None if binding_id_value is None else _text(binding_id_value, "binding_id")
        return ExplicitPivotCandidateRequest(
            request_id=_text(root["request_id"], "request_id"),
            requested_at_utc=_text(root["requested_at_utc"], "requested_at_utc"),
            candidate_id=_text(root["candidate_id"], "candidate_id"),
            parent_subject=parent,
            ordered_pivots=tuple(pivots),
            ordered_child_groups=tuple(groups),
            binding_id=binding_id,
            manual_fact_declarations=tuple(declarations),
            provenance_refs=refs(root["provenance_refs"], "provenance_refs"),
        )
    except HumanReadableManualCandidateError as error:
        raise ExplicitPivotCandidateError(str(error)) from error


__all__ = [
    "ARTIFACT_CLASSIFICATION",
    "EXPLICIT_PIVOT_INPUT_SCHEMA_VERSION",
    "EXPLICIT_PIVOT_REPORT_SCHEMA_VERSION",
    "ExplicitP004PivotRole",
    "ExplicitPivotCandidateBuildResult",
    "ExplicitPivotCandidateError",
    "ExplicitPivotCandidateRequest",
    "ExplicitPivotChildGroup",
    "ExplicitPivotObservation",
    "GROUPING_CLASSIFICATION",
    "PIVOT_CLASSIFICATION",
    "WORKFLOW_POLICY_CLASSIFICATION",
    "parse_human_readable_explicit_pivot_candidate",
    "render_explicit_pivot_report",
]
