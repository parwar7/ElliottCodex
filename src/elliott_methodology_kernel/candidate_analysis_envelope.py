"""Live transport for one caller-proposed analysis candidate.

This module is PROJECT_ANALYSIS_INFRASTRUCTURE.  Its consistency conventions
are PROJECT_OPERATIONAL_POLICY, not Elliott methodology.  Construction proves
only that a same-process transport package is internally well formed; it does
not discover a candidate or establish pattern, wave, degree, parentage,
timeframe, completion, direction, family, validity, evidence, or rank.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from ._structural_invalidity_certification import CertifiedStructuralInvalidity
from .bounded_recursive_analysis import (
    BoundedRecursiveAnalysisResolution,
    SubjectBoundP023VisibilityResult,
)
from .degree_peer_consistency import (
    DEGREE_PEER_BEHAVIOR_ID,
    DegreePeerConsistencyInput,
    DegreePeerConsistencyResult,
)
from .ending_diagonal_cardinality import (
    ENDING_DIAGONAL_BEHAVIOR_ID,
    EndingDiagonalCardinalityInput,
    EndingDiagonalCardinalityResult,
)
from .observed_price_binding import (
    SubjectBoundObservedPriceEndpointPair,
    SubjectBoundObservedPriceObservation,
)
from .p003_one_larger_degree_theme import (
    P003_BEHAVIOR,
    P003OneLargerDegreeThemeInput,
    P003OneLargerDegreeThemeResult,
)
from .p004 import P004_BEHAVIOR_ID, P004Input, P004Result
from .p007_single_zigzag_cardinality import (
    P007_BEHAVIOR_ID,
    P007SingleZigzagCardinalityInput,
    P007SingleZigzagCardinalityResult,
)
from .p008_flat_cardinality import (
    P008_BEHAVIOR_ID,
    P008FlatCardinalityInput,
    P008FlatCardinalityResult,
)
from .p009_triangle_cardinality import (
    P009_BEHAVIOR_ID,
    P009TriangleCardinalityInput,
    P009TriangleCardinalityResult,
)
from .p023_visibility_guard import P023_BEHAVIOR_ID, P023VisibilityInput
from .parent_child_degree_adjacency import (
    PARENT_CHILD_DEGREE_BEHAVIOR_ID,
    ParentChildDegreeInput,
    ParentChildDegreeResult,
)
from .structural_invalidity_evidence_no_rescue import (
    NO_RESCUE_BEHAVIOR,
    StructuralInvalidityEvidenceNoRescueResult,
)
from .subject_binding import AnalyzedWaveSubject, OrderedChildBinding


ARTIFACT_CLASSIFICATION = "PROJECT_ANALYSIS_INFRASTRUCTURE"
WORKFLOW_POLICY_CLASSIFICATION = "PROJECT_OPERATIONAL_POLICY"


class CandidateAnalysisEnvelopeError(ValueError):
    """Raised when candidate transport consistency fails closed."""


class _SealedCandidateEnvelopeType(type):
    def __new__(
        mcls: type,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
        **kwargs: object,
    ) -> type:
        if any(isinstance(base, mcls) for base in bases):
            raise TypeError("Candidate-analysis infrastructure cannot be subclassed.")
        return super().__new__(mcls, name, bases, namespace, **kwargs)


@dataclass(frozen=True, slots=True, eq=False)
class _BehaviorCompatibility:
    behavior_id: str
    input_type: type[object]
    result_type: type[object]
    subject_bound_p023: bool = False
    binding_consumer: bool = False
    certified_invalidity_input: bool = False


_BEHAVIOR_COMPATIBILITY = (
    _BehaviorCompatibility(P004_BEHAVIOR_ID, P004Input, P004Result),
    _BehaviorCompatibility(
        DEGREE_PEER_BEHAVIOR_ID,
        DegreePeerConsistencyInput,
        DegreePeerConsistencyResult,
    ),
    _BehaviorCompatibility(
        PARENT_CHILD_DEGREE_BEHAVIOR_ID,
        ParentChildDegreeInput,
        ParentChildDegreeResult,
    ),
    _BehaviorCompatibility(
        P023_BEHAVIOR_ID,
        P023VisibilityInput,
        SubjectBoundP023VisibilityResult,
        subject_bound_p023=True,
    ),
    _BehaviorCompatibility(
        NO_RESCUE_BEHAVIOR,
        CertifiedStructuralInvalidity,
        StructuralInvalidityEvidenceNoRescueResult,
        certified_invalidity_input=True,
    ),
    _BehaviorCompatibility(
        P003_BEHAVIOR,
        P003OneLargerDegreeThemeInput,
        P003OneLargerDegreeThemeResult,
    ),
    _BehaviorCompatibility(
        P007_BEHAVIOR_ID,
        P007SingleZigzagCardinalityInput,
        P007SingleZigzagCardinalityResult,
        binding_consumer=True,
    ),
    _BehaviorCompatibility(
        P008_BEHAVIOR_ID,
        P008FlatCardinalityInput,
        P008FlatCardinalityResult,
        binding_consumer=True,
    ),
    _BehaviorCompatibility(
        P009_BEHAVIOR_ID,
        P009TriangleCardinalityInput,
        P009TriangleCardinalityResult,
        binding_consumer=True,
    ),
    _BehaviorCompatibility(
        ENDING_DIAGONAL_BEHAVIOR_ID,
        EndingDiagonalCardinalityInput,
        EndingDiagonalCardinalityResult,
        binding_consumer=True,
    ),
)


def _require_nonblank_text(value: object, name: str) -> str:
    if type(value) is not str or value.strip() == "":
        raise CandidateAnalysisEnvelopeError(
            f"{name} must be an exact non-blank string."
        )
    return value


def _require_subject(value: object) -> AnalyzedWaveSubject:
    if type(value) is not AnalyzedWaveSubject:
        raise CandidateAnalysisEnvelopeError(
            "subject must be one exact AnalyzedWaveSubject."
        )
    return value


def _require_provenance(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or any(
        type(item) is not str or item.strip() == "" for item in value
    ):
        raise CandidateAnalysisEnvelopeError(
            "provenance_refs must be an exact tuple of exact non-blank strings."
        )
    return value


def _exact_text_equal(left: object, right: str) -> bool:
    return type(left) is str and str.__eq__(left, right) is True


def _snapshot(
    value: object,
    active_ids: frozenset[int] = frozenset(),
) -> tuple[object, ...]:
    if id(value) in active_ids:
        return ("ATOM", value)
    nested_active_ids = active_ids | {id(value)}
    if type(value) is tuple:
        return (
            "TUPLE",
            value,
            tuple(_snapshot(item, nested_active_ids) for item in value),
        )
    if is_dataclass(value) and not isinstance(value, type):
        return (
            "DATACLASS",
            type(value),
            value,
            tuple(
                (item.name, _snapshot(getattr(value, item.name), nested_active_ids))
                for item in fields(value)
            ),
        )
    return ("ATOM", value)


def _snapshot_matches(
    value: object,
    expected: tuple[object, ...],
) -> bool:
    if not expected:
        return False
    kind = expected[0]
    if kind == "ATOM":
        return len(expected) == 2 and value is expected[1]
    if kind == "TUPLE":
        if len(expected) != 3 or type(value) is not tuple or value is not expected[1]:
            return False
        item_snapshots = expected[2]
        return type(item_snapshots) is tuple and len(value) == len(item_snapshots) and all(
            _snapshot_matches(item, item_snapshot)
            for item, item_snapshot in zip(value, item_snapshots, strict=True)
        )
    if kind == "DATACLASS":
        if (
            len(expected) != 4
            or type(value) is not expected[1]
            or value is not expected[2]
        ):
            return False
        field_snapshots = expected[3]
        try:
            current_fields = fields(value)
        except TypeError:
            return False
        if type(field_snapshots) is not tuple or tuple(
            item.name for item in current_fields
        ) != tuple(item[0] for item in field_snapshots):
            return False
        return all(
            _snapshot_matches(getattr(value, name), field_snapshot)
            for name, field_snapshot in field_snapshots
        )
    return False


def _compatibility_for(behavior_id: object) -> _BehaviorCompatibility:
    if type(behavior_id) is not str:
        raise CandidateAnalysisEnvelopeError(
            "behavior_id must be one exact reviewed behavior string."
        )
    for compatibility in _BEHAVIOR_COMPATIBILITY:
        if str.__eq__(behavior_id, compatibility.behavior_id) is True:
            return compatibility
    raise CandidateAnalysisEnvelopeError(
        "Unknown behavior_id has no reviewed candidate-envelope compatibility."
    )


def _origin_binding_from_certificate(
    certificate: CertifiedStructuralInvalidity,
) -> OrderedChildBinding | None:
    if type(certificate) is not CertifiedStructuralInvalidity:
        raise CandidateAnalysisEnvelopeError(
            "No-rescue input must be one exact structural-invalidity certificate."
        )
    try:
        origin = certificate.origin
        certificate.structural_validity
        certificate.fatal_to_candidate
    except Exception as error:
        raise CandidateAnalysisEnvelopeError(
            "The structural-invalidity certificate is not genuine and live."
        ) from error
    binding = getattr(origin, "binding", None)
    if binding is not None and type(binding) is not OrderedChildBinding:
        raise CandidateAnalysisEnvelopeError(
            "The certificate origin exposes a malformed binding."
        )
    return binding


def _validate_evaluation_values(
    subject: AnalyzedWaveSubject,
    behavior_id: str,
    input_object: object,
    result_object: object,
) -> OrderedChildBinding | None:
    compatibility = _compatibility_for(behavior_id)
    if type(input_object) is not compatibility.input_type:
        raise CandidateAnalysisEnvelopeError(
            "The methodology input type does not match behavior_id."
        )
    if type(result_object) is not compatibility.result_type:
        raise CandidateAnalysisEnvelopeError(
            "The methodology result type does not match behavior_id."
        )

    if compatibility.subject_bound_p023:
        try:
            result_subject = result_object.subject
            raw_result = result_object.result
            visibility_state = result_object.visibility_state
        except Exception as error:
            raise CandidateAnalysisEnvelopeError(
                "P023 support is not genuine, live, and unchanged."
            ) from error
        if result_subject is not subject:
            raise CandidateAnalysisEnvelopeError(
                "The P023 evaluation belongs to a different subject identity."
            )
        if input_object.visibility_state is not visibility_state:
            raise CandidateAnalysisEnvelopeError(
                "The P023 input token does not match its subject-bound result."
            )
        if not _exact_text_equal(raw_result.behavior_id, behavior_id):
            raise CandidateAnalysisEnvelopeError(
                "The subject-bound P023 result has the wrong behavior ID."
            )
        return None

    if compatibility.certified_invalidity_input:
        binding = _origin_binding_from_certificate(input_object)
        try:
            if result_object.originating_invalidity is not input_object:
                raise CandidateAnalysisEnvelopeError(
                    "The no-rescue result does not retain the exact input certificate."
                )
            result_behavior_id = result_object.behavior_id
        except CandidateAnalysisEnvelopeError:
            raise
        except Exception as error:
            raise CandidateAnalysisEnvelopeError(
                "The no-rescue result is not genuine, live, and unchanged."
            ) from error
        if not _exact_text_equal(result_behavior_id, behavior_id):
            raise CandidateAnalysisEnvelopeError(
                "The no-rescue result has the wrong behavior ID."
            )
        if binding is not None and binding.parent_subject is not subject:
            raise CandidateAnalysisEnvelopeError(
                "The certified structural origin belongs to another subject."
            )
        return binding

    result_behavior_id = getattr(result_object, "behavior_id", None)
    if not _exact_text_equal(result_behavior_id, behavior_id):
        raise CandidateAnalysisEnvelopeError(
            "The result's exact behavior ID does not match its attachment."
        )

    if compatibility.binding_consumer:
        input_binding = getattr(input_object, "binding", None)
        result_binding = getattr(result_object, "binding", None)
        for value in (input_binding, result_binding):
            if value is not None and type(value) is not OrderedChildBinding:
                raise CandidateAnalysisEnvelopeError(
                    "A cardinality evaluation exposes a malformed binding."
                )
        if result_binding is not None and result_binding is not input_binding:
            raise CandidateAnalysisEnvelopeError(
                "The result binding is not the exact input binding."
            )
        binding = result_binding if result_binding is not None else input_binding
        if binding is not None and binding.parent_subject is not subject:
            raise CandidateAnalysisEnvelopeError(
                "The cardinality binding belongs to another subject."
            )
        return binding

    # These legacy contracts expose no analyzed-subject identity.  The exact
    # envelope subject is retained as transport context but is not inferred to
    # have been validated by the result.
    return None


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class CandidateMethodologyEvaluation(metaclass=_SealedCandidateEnvelopeType):
    """One exact behavior input/result attachment without added authority."""

    subject: AnalyzedWaveSubject
    behavior_id: str
    input_object: object
    result_object: object
    provenance_refs: tuple[str, ...] = ()
    _input_snapshot: tuple[object, ...] = field(
        init=False, repr=False, compare=False
    )
    _result_snapshot: tuple[object, ...] = field(
        init=False, repr=False, compare=False
    )
    _attachment_snapshot: tuple[object, ...] = field(
        init=False, repr=False, compare=False
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("Candidate methodology evaluations cannot be subclassed.")

    def __post_init__(self) -> None:
        subject = _require_subject(self.subject)
        _require_nonblank_text(self.behavior_id, "behavior_id")
        _require_provenance(self.provenance_refs)
        _validate_evaluation_values(
            subject,
            self.behavior_id,
            self.input_object,
            self.result_object,
        )
        object.__setattr__(self, "_input_snapshot", _snapshot(self.input_object))
        object.__setattr__(self, "_result_snapshot", _snapshot(self.result_object))
        object.__setattr__(
            self,
            "_attachment_snapshot",
            (
                self.subject,
                self.behavior_id,
                self.input_object,
                self.result_object,
                self.provenance_refs,
            ),
        )

    def _validated(self) -> CandidateMethodologyEvaluation:
        if type(self) is not CandidateMethodologyEvaluation:
            raise CandidateAnalysisEnvelopeError(
                "Evaluation attachment must have its exact reviewed type."
            )
        try:
            input_snapshot = object.__getattribute__(self, "_input_snapshot")
            result_snapshot = object.__getattribute__(self, "_result_snapshot")
            attachment_snapshot = object.__getattribute__(
                self, "_attachment_snapshot"
            )
        except AttributeError as error:
            raise CandidateAnalysisEnvelopeError(
                "Evaluation attachment is malformed."
            ) from error
        if any(
            current is not expected
            for current, expected in zip(
                (
                    self.subject,
                    self.behavior_id,
                    self.input_object,
                    self.result_object,
                    self.provenance_refs,
                ),
                attachment_snapshot,
                strict=True,
            )
        ):
            raise CandidateAnalysisEnvelopeError(
                "The evaluation attachment changed after construction."
            )
        if not _snapshot_matches(self.input_object, input_snapshot):
            raise CandidateAnalysisEnvelopeError(
                "The attached methodology input changed after construction."
            )
        if not _snapshot_matches(self.result_object, result_snapshot):
            raise CandidateAnalysisEnvelopeError(
                "The attached methodology result changed after construction."
            )
        _validate_evaluation_values(
            _require_subject(self.subject),
            self.behavior_id,
            self.input_object,
            self.result_object,
        )
        _require_provenance(self.provenance_refs)
        return self

    @property
    def consumed_binding(self) -> OrderedChildBinding | None:
        self._validated()
        return _validate_evaluation_values(
            self.subject,
            self.behavior_id,
            self.input_object,
            self.result_object,
        )

    def __copy__(self) -> CandidateMethodologyEvaluation:
        return self._validated()

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> CandidateMethodologyEvaluation:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Candidate methodology evaluations cannot be pickled.")


_OBSERVATION_TYPES = (
    SubjectBoundObservedPriceObservation,
    SubjectBoundObservedPriceEndpointPair,
)


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class CandidateObservationAttachment(metaclass=_SealedCandidateEnvelopeType):
    """One exact existing observation object retained as transport only."""

    subject: AnalyzedWaveSubject
    observation: (
        SubjectBoundObservedPriceObservation
        | SubjectBoundObservedPriceEndpointPair
    )
    provenance_refs: tuple[str, ...] = ()
    _observation_snapshot: tuple[object, ...] = field(
        init=False, repr=False, compare=False
    )
    _attachment_snapshot: tuple[object, ...] = field(
        init=False, repr=False, compare=False
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("Candidate observation attachments cannot be subclassed.")

    def __post_init__(self) -> None:
        subject = _require_subject(self.subject)
        if type(self.observation) not in _OBSERVATION_TYPES:
            raise CandidateAnalysisEnvelopeError(
                "observation must use one exact approved observation contract."
            )
        if self.observation.subject is not subject:
            raise CandidateAnalysisEnvelopeError(
                "The observation belongs to a different subject identity."
            )
        _require_provenance(self.provenance_refs)
        object.__setattr__(
            self,
            "_observation_snapshot",
            _snapshot(self.observation),
        )
        object.__setattr__(
            self,
            "_attachment_snapshot",
            (self.subject, self.observation, self.provenance_refs),
        )

    def _validated(self) -> CandidateObservationAttachment:
        if type(self) is not CandidateObservationAttachment:
            raise CandidateAnalysisEnvelopeError(
                "Observation attachment must have its exact reviewed type."
            )
        try:
            snapshot = object.__getattribute__(self, "_observation_snapshot")
            attachment_snapshot = object.__getattribute__(
                self, "_attachment_snapshot"
            )
        except AttributeError as error:
            raise CandidateAnalysisEnvelopeError(
                "Observation attachment is malformed."
            ) from error
        if any(
            current is not expected
            for current, expected in zip(
                (self.subject, self.observation, self.provenance_refs),
                attachment_snapshot,
                strict=True,
            )
        ):
            raise CandidateAnalysisEnvelopeError(
                "The observation attachment changed after construction."
            )
        if not _snapshot_matches(self.observation, snapshot):
            raise CandidateAnalysisEnvelopeError(
                "The attached observation changed after construction."
            )
        if self.observation.subject is not _require_subject(self.subject):
            raise CandidateAnalysisEnvelopeError(
                "The observation subject identity changed."
            )
        _require_provenance(self.provenance_refs)
        return self

    def __copy__(self) -> CandidateObservationAttachment:
        return self._validated()

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> CandidateObservationAttachment:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Candidate observation attachments cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class CandidateAnalysisEnvelope(metaclass=_SealedCandidateEnvelopeType):
    """One live, non-authoritative package for a caller-proposed candidate."""

    subject: AnalyzedWaveSubject
    candidate_id: str
    child_binding: OrderedChildBinding | None = None
    methodology_evaluations: tuple[CandidateMethodologyEvaluation, ...] = ()
    observations: tuple[CandidateObservationAttachment, ...] = ()
    operational_resolution: BoundedRecursiveAnalysisResolution | None = None
    provenance_refs: tuple[str, ...] = ()
    _envelope_snapshot: tuple[object, ...] = field(
        init=False, repr=False, compare=False
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("Candidate analysis envelopes cannot be subclassed.")

    def __post_init__(self) -> None:
        self._validate_values()
        object.__setattr__(
            self,
            "_envelope_snapshot",
            (
                self.subject,
                self.candidate_id,
                self.child_binding,
                self.methodology_evaluations,
                self.observations,
                self.operational_resolution,
                self.provenance_refs,
            ),
        )

    def _validate_values(self) -> None:
        subject = _require_subject(self.subject)
        _require_nonblank_text(self.candidate_id, "candidate_id")
        _require_provenance(self.provenance_refs)

        if self.child_binding is not None:
            if type(self.child_binding) is not OrderedChildBinding:
                raise CandidateAnalysisEnvelopeError(
                    "child_binding must be one exact OrderedChildBinding or None."
                )
            if self.child_binding.parent_subject is not subject:
                raise CandidateAnalysisEnvelopeError(
                    "The supplied child binding belongs to another subject."
                )

        if type(self.methodology_evaluations) is not tuple or any(
            type(item) is not CandidateMethodologyEvaluation
            for item in self.methodology_evaluations
        ):
            raise CandidateAnalysisEnvelopeError(
                "methodology_evaluations must be one exact tuple of exact attachments."
            )
        seen_behavior_inputs: list[tuple[str, object]] = []
        for evaluation in self.methodology_evaluations:
            evaluation._validated()
            if evaluation.subject is not subject:
                raise CandidateAnalysisEnvelopeError(
                    "A methodology evaluation belongs to another subject."
                )
            for behavior_id, input_object in seen_behavior_inputs:
                if (
                    str.__eq__(behavior_id, evaluation.behavior_id) is True
                    and input_object is evaluation.input_object
                ):
                    raise CandidateAnalysisEnvelopeError(
                        "The same behavior and exact input identity cannot be attached twice."
                    )
            seen_behavior_inputs.append(
                (evaluation.behavior_id, evaluation.input_object)
            )
            consumed_binding = evaluation.consumed_binding
            if consumed_binding is not None and consumed_binding is not self.child_binding:
                raise CandidateAnalysisEnvelopeError(
                    "A binding-consuming evaluation must use the envelope's exact binding."
                )

        if type(self.observations) is not tuple or any(
            type(item) is not CandidateObservationAttachment
            for item in self.observations
        ):
            raise CandidateAnalysisEnvelopeError(
                "observations must be one exact tuple of exact attachments."
            )
        for observation in self.observations:
            observation._validated()
            if observation.subject is not subject:
                raise CandidateAnalysisEnvelopeError(
                    "An observation attachment belongs to another subject."
                )

        if self.operational_resolution is not None:
            if type(self.operational_resolution) is not BoundedRecursiveAnalysisResolution:
                raise CandidateAnalysisEnvelopeError(
                    "operational_resolution must use its exact existing contract."
                )
            try:
                self.operational_resolution.__post_init__()
            except Exception as error:
                raise CandidateAnalysisEnvelopeError(
                    "The operational resolution is malformed or no longer valid."
                ) from error
            if self.operational_resolution.subject is not subject:
                raise CandidateAnalysisEnvelopeError(
                    "The operational resolution belongs to another subject."
                )

    def _validated(self) -> CandidateAnalysisEnvelope:
        try:
            snapshot = object.__getattribute__(self, "_envelope_snapshot")
        except AttributeError as error:
            raise CandidateAnalysisEnvelopeError(
                "The candidate analysis envelope is malformed."
            ) from error
        if any(
            current is not expected
            for current, expected in zip(
                (
                    self.subject,
                    self.candidate_id,
                    self.child_binding,
                    self.methodology_evaluations,
                    self.observations,
                    self.operational_resolution,
                    self.provenance_refs,
                ),
                snapshot,
                strict=True,
            )
        ):
            raise CandidateAnalysisEnvelopeError(
                "The candidate analysis envelope changed after construction."
            )
        self._validate_values()
        return self

    def __copy__(self) -> CandidateAnalysisEnvelope:
        return self._validated()

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> CandidateAnalysisEnvelope:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Candidate analysis envelopes cannot be pickled.")


__all__ = [
    "ARTIFACT_CLASSIFICATION",
    "WORKFLOW_POLICY_CLASSIFICATION",
    "CandidateAnalysisEnvelope",
    "CandidateAnalysisEnvelopeError",
    "CandidateMethodologyEvaluation",
    "CandidateObservationAttachment",
]
