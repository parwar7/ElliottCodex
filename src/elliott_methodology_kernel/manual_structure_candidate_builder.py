"""Build reviewed input objects from explicit manual structural declarations.

This is PROJECT_ANALYSIS_INFRASTRUCTURE.  Builder conventions are
PROJECT_OPERATIONAL_POLICY.  Manual declarations are untrusted caller facts,
not methodology results, source authority, certificates, or family proof.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
import math

from ._structural_invalidity_certification import CertifiedStructuralInvalidity
from .bounded_recursive_analysis import BoundedRecursiveAnalysisResolution
from .candidate_analysis_envelope import (
    CandidateAnalysisEnvelope,
    CandidateObservationAttachment,
    _origin_binding_from_certificate,
    _snapshot,
    _snapshot_matches,
)
from .degree_peer_consistency import (
    DEGREE_PEER_BEHAVIOR_ID,
    DegreePeerConsistencyInput,
)
from .ending_diagonal_cardinality import (
    ENDING_DIAGONAL_BEHAVIOR_ID,
    EndingDiagonalCandidateScope,
    EndingDiagonalCardinalityInput,
)
from .explicit_behavior_execution import (
    ExplicitBehaviorExecutionRequest,
    ExplicitBehaviorExecutionResult,
    ExplicitBehaviorInput,
)
from .models import DegreeStatus, DegreeTreeNode
from .p003_one_larger_degree_theme import (
    P003_BEHAVIOR,
    P003OneLargerDegreeRelation,
    P003OneLargerDegreeThemeInput,
)
from .p004 import CandidateScope, ImpulseDirection, P004_BEHAVIOR_ID, P004Input
from .p007_single_zigzag_cardinality import (
    P007_BEHAVIOR_ID,
    P007CandidateScope,
    P007SingleZigzagCardinalityInput,
)
from .p008_flat_cardinality import (
    P008_BEHAVIOR_ID,
    P008CandidateScope,
    P008FlatCardinalityInput,
)
from .p009_triangle_cardinality import (
    P009_BEHAVIOR_ID,
    P009CandidateScope,
    P009TriangleCardinalityInput,
)
from .p023_visibility_guard import (
    P023_BEHAVIOR_ID,
    P023VisibilityInput,
    P023VisibilityState,
)
from .parent_child_degree_adjacency import (
    PARENT_CHILD_DEGREE_BEHAVIOR_ID,
    ParentChildDegreeInput,
)
from .structural_invalidity_evidence_no_rescue import NO_RESCUE_BEHAVIOR
from .single_candidate_orchestration import SingleCandidateAnalysisResult
from .subject_binding import AnalyzedWaveSubject, OrderedChildBinding


ARTIFACT_CLASSIFICATION = "PROJECT_ANALYSIS_INFRASTRUCTURE"
WORKFLOW_POLICY_CLASSIFICATION = "PROJECT_OPERATIONAL_POLICY"
CALLER_SUPPLIED_STRUCTURAL_FACT = "CALLER_SUPPLIED_STRUCTURAL_FACT"


class ManualStructureCandidateBuilderError(ValueError):
    """Raised when a manual declaration or build request fails closed."""


class ManualCardinalityBehavior(StrEnum):
    SINGLE_ZIGZAG = "SINGLE_ZIGZAG"
    FLAT = "FLAT"
    TRIANGLE = "TRIANGLE"
    ENDING_DIAGONAL = "ENDING_DIAGONAL"


class _SealedManualType(type):
    def __new__(
        mcls: type,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
        **kwargs: object,
    ) -> type:
        if any(isinstance(base, mcls) for base in bases):
            raise TypeError("Manual-structure infrastructure cannot be subclassed.")
        return super().__new__(mcls, name, bases, namespace, **kwargs)


class _ManualFact:
    @property
    def fact_classification(self) -> str:
        return CALLER_SUPPLIED_STRUCTURAL_FACT

    def __copy__(self) -> _ManualFact:
        return self

    def __deepcopy__(self, memo: dict[int, object]) -> _ManualFact:
        memo[id(self)] = self
        return self

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Manual structural facts cannot be pickled.")


def _require_text(value: object, name: str) -> str:
    if type(value) is not str or value.strip() == "":
        raise ManualStructureCandidateBuilderError(
            f"{name} must be an exact non-blank string."
        )
    return value


def _require_provenance(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or any(
        type(item) is not str or item.strip() == "" for item in value
    ):
        raise ManualStructureCandidateBuilderError(
            "provenance_refs must be an exact tuple of non-blank strings."
        )
    return value


def _require_price(value: object, name: str) -> int | float:
    try:
        valid = (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
        )
    except OverflowError:
        valid = False
    if not valid:
        raise ManualStructureCandidateBuilderError(
            f"{name} must be an explicit finite numeric observation."
        )
    return value


@dataclass(frozen=True, slots=True, eq=False)
class ManualP004Wave2OriginFact(_ManualFact, metaclass=_SealedManualType):
    candidate_scope: CandidateScope
    direction: ImpulseDirection
    wave1_origin_price: int | float
    wave2_end_price: int | float

    def __post_init__(self) -> None:
        if type(self.candidate_scope) is not CandidateScope:
            raise ManualStructureCandidateBuilderError(
                "candidate_scope must be the exact existing CandidateScope enum."
            )
        if type(self.direction) is not ImpulseDirection:
            raise ManualStructureCandidateBuilderError(
                "direction must be the exact existing ImpulseDirection enum."
            )
        _require_price(self.wave1_origin_price, "wave1_origin_price")
        _require_price(self.wave2_end_price, "wave2_end_price")


@dataclass(frozen=True, slots=True, eq=False)
class ManualDegreePeerFact(_ManualFact, metaclass=_SealedManualType):
    parent_node_id: str
    direct_child_degrees: tuple[DegreeTreeNode, ...]

    def __post_init__(self) -> None:
        _require_text(self.parent_node_id, "parent_node_id")
        if type(self.direct_child_degrees) is not tuple or any(
            type(item) is not DegreeTreeNode for item in self.direct_child_degrees
        ):
            raise ManualStructureCandidateBuilderError(
                "direct_child_degrees must be an exact tuple of DegreeTreeNode values."
            )


@dataclass(frozen=True, slots=True, eq=False)
class ManualParentChildDegreeFact(_ManualFact, metaclass=_SealedManualType):
    parent_degree: str
    parent_degree_status: DegreeStatus
    child_degree: str
    child_degree_status: DegreeStatus

    def __post_init__(self) -> None:
        _require_text(self.parent_degree, "parent_degree")
        _require_text(self.child_degree, "child_degree")
        if type(self.parent_degree_status) is not DegreeStatus or type(
            self.child_degree_status
        ) is not DegreeStatus:
            raise ManualStructureCandidateBuilderError(
                "Degree statuses must use the exact existing DegreeStatus enum."
            )


@dataclass(frozen=True, slots=True, eq=False)
class ManualP023VisibilityFact(_ManualFact, metaclass=_SealedManualType):
    subject: AnalyzedWaveSubject
    visibility_state: P023VisibilityState

    def __post_init__(self) -> None:
        if type(self.subject) is not AnalyzedWaveSubject:
            raise ManualStructureCandidateBuilderError(
                "subject must be one exact AnalyzedWaveSubject."
            )
        if type(self.visibility_state) is not P023VisibilityState:
            raise ManualStructureCandidateBuilderError(
                "visibility_state must use the exact existing P023 token."
            )


@dataclass(frozen=True, slots=True, eq=False)
class ManualP003OneLargerDegreeRelationFact(
    _ManualFact,
    metaclass=_SealedManualType,
):
    relation: P003OneLargerDegreeRelation

    def __post_init__(self) -> None:
        if type(self.relation) is not P003OneLargerDegreeRelation:
            raise ManualStructureCandidateBuilderError(
                "relation must use the exact existing P003 relation token."
            )


@dataclass(frozen=True, slots=True, eq=False)
class ManualDirectChildCardinalityFact(_ManualFact, metaclass=_SealedManualType):
    behavior: ManualCardinalityBehavior

    def __post_init__(self) -> None:
        if type(self.behavior) is not ManualCardinalityBehavior:
            raise ManualStructureCandidateBuilderError(
                "behavior must use one exact explicit cardinality selector."
            )


def _build_p004(fact: object, binding: OrderedChildBinding | None) -> P004Input:
    assert type(fact) is ManualP004Wave2OriginFact
    return P004Input(
        fact.candidate_scope,
        fact.direction,
        fact.wave1_origin_price,
        fact.wave2_end_price,
    )


def _build_peer(
    fact: object,
    binding: OrderedChildBinding | None,
) -> DegreePeerConsistencyInput:
    assert type(fact) is ManualDegreePeerFact
    return DegreePeerConsistencyInput(fact.parent_node_id, fact.direct_child_degrees)


def _build_parent_child(
    fact: object,
    binding: OrderedChildBinding | None,
) -> ParentChildDegreeInput:
    assert type(fact) is ManualParentChildDegreeFact
    return ParentChildDegreeInput(
        fact.parent_degree,
        fact.parent_degree_status,
        fact.child_degree,
        fact.child_degree_status,
    )


def _build_visibility(
    fact: object,
    binding: OrderedChildBinding | None,
) -> P023VisibilityInput:
    assert type(fact) is ManualP023VisibilityFact
    return P023VisibilityInput(fact.visibility_state)


def _build_relation(
    fact: object,
    binding: OrderedChildBinding | None,
) -> P003OneLargerDegreeThemeInput:
    assert type(fact) is ManualP003OneLargerDegreeRelationFact
    return P003OneLargerDegreeThemeInput(fact.relation)


def _require_binding(binding: OrderedChildBinding | None) -> OrderedChildBinding:
    if type(binding) is not OrderedChildBinding:
        raise ManualStructureCandidateBuilderError(
            "A cardinality declaration requires an exact supplied or constructed binding."
        )
    return binding


def _build_zigzag(
    fact: object,
    binding: OrderedChildBinding | None,
) -> P007SingleZigzagCardinalityInput:
    return P007SingleZigzagCardinalityInput(
        P007CandidateScope.SINGLE_ZIGZAG,
        _require_binding(binding),
    )


def _build_flat(
    fact: object,
    binding: OrderedChildBinding | None,
) -> P008FlatCardinalityInput:
    return P008FlatCardinalityInput(
        P008CandidateScope.FLAT,
        _require_binding(binding),
    )


def _build_triangle(
    fact: object,
    binding: OrderedChildBinding | None,
) -> P009TriangleCardinalityInput:
    return P009TriangleCardinalityInput(
        P009CandidateScope.TRIANGLE,
        _require_binding(binding),
    )


def _build_ending_diagonal(
    fact: object,
    binding: OrderedChildBinding | None,
) -> EndingDiagonalCardinalityInput:
    return EndingDiagonalCardinalityInput(
        EndingDiagonalCandidateScope.ENDING_DIAGONAL,
        _require_binding(binding),
    )


@dataclass(frozen=True, slots=True)
class _ManualFactBuilder:
    fact_type: type[object]
    behavior_id: str
    constructor: Callable[[object, OrderedChildBinding | None], object]
    cardinality_selector: ManualCardinalityBehavior | None = None


_MANUAL_FACT_BUILDERS = (
    _ManualFactBuilder(ManualP004Wave2OriginFact, P004_BEHAVIOR_ID, _build_p004),
    _ManualFactBuilder(ManualDegreePeerFact, DEGREE_PEER_BEHAVIOR_ID, _build_peer),
    _ManualFactBuilder(
        ManualParentChildDegreeFact,
        PARENT_CHILD_DEGREE_BEHAVIOR_ID,
        _build_parent_child,
    ),
    _ManualFactBuilder(
        ManualP023VisibilityFact,
        P023_BEHAVIOR_ID,
        _build_visibility,
    ),
    _ManualFactBuilder(
        ManualP003OneLargerDegreeRelationFact,
        P003_BEHAVIOR,
        _build_relation,
    ),
    _ManualFactBuilder(
        ManualDirectChildCardinalityFact,
        P007_BEHAVIOR_ID,
        _build_zigzag,
        ManualCardinalityBehavior.SINGLE_ZIGZAG,
    ),
    _ManualFactBuilder(
        ManualDirectChildCardinalityFact,
        P008_BEHAVIOR_ID,
        _build_flat,
        ManualCardinalityBehavior.FLAT,
    ),
    _ManualFactBuilder(
        ManualDirectChildCardinalityFact,
        P009_BEHAVIOR_ID,
        _build_triangle,
        ManualCardinalityBehavior.TRIANGLE,
    ),
    _ManualFactBuilder(
        ManualDirectChildCardinalityFact,
        ENDING_DIAGONAL_BEHAVIOR_ID,
        _build_ending_diagonal,
        ManualCardinalityBehavior.ENDING_DIAGONAL,
    ),
)


def _builder_for(fact: object) -> _ManualFactBuilder:
    for builder in _MANUAL_FACT_BUILDERS:
        if type(fact) is builder.fact_type and (
            builder.cardinality_selector is None
            or fact.behavior is builder.cardinality_selector
        ):
            return builder
    raise ManualStructureCandidateBuilderError(
        "Unknown manual fact type or unsupported explicit selector."
    )


_MANUAL_FACT_TYPES = (
    ManualP004Wave2OriginFact,
    ManualDegreePeerFact,
    ManualParentChildDegreeFact,
    ManualP023VisibilityFact,
    ManualP003OneLargerDegreeRelationFact,
    ManualDirectChildCardinalityFact,
)


def _validate_fact(fact: object, subject: AnalyzedWaveSubject) -> None:
    if type(fact) not in _MANUAL_FACT_TYPES:
        raise ManualStructureCandidateBuilderError(
            "manual_behavior_facts contains an unapproved fact type."
        )
    fact.__post_init__()
    _builder_for(fact)
    if type(fact) is ManualP023VisibilityFact and fact.subject is not subject:
        raise ManualStructureCandidateBuilderError(
            "The manual P023 fact belongs to another subject identity."
        )


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class ManualStructureCandidateRequest(metaclass=_SealedManualType):
    request_id: str
    requested_at_utc: str
    subject: AnalyzedWaveSubject
    candidate_id: str
    manual_behavior_facts: tuple[object, ...] = ()
    child_binding: OrderedChildBinding | None = None
    ordered_child_subjects: tuple[AnalyzedWaveSubject, ...] | None = None
    constructed_binding_id: str | None = None
    trusted_invalidity_certificates: tuple[CertifiedStructuralInvalidity, ...] = ()
    observations: tuple[CandidateObservationAttachment, ...] = ()
    operational_resolution: BoundedRecursiveAnalysisResolution | None = None
    provenance_refs: tuple[str, ...] = ()
    _effective_child_binding: OrderedChildBinding | None = field(init=False, repr=False)
    _constructed_child_binding: OrderedChildBinding | None = field(init=False, repr=False)
    _transport_probe: CandidateAnalysisEnvelope = field(init=False, repr=False)
    _binding_snapshot: tuple[object, ...] = field(init=False, repr=False)
    _fact_snapshots: tuple[tuple[object, ...], ...] = field(init=False, repr=False)
    _identity_snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("Manual structure requests cannot be subclassed.")

    def __post_init__(self) -> None:
        _require_text(self.request_id, "request_id")
        _require_text(self.requested_at_utc, "requested_at_utc")
        _require_provenance(self.provenance_refs)
        if type(self.subject) is not AnalyzedWaveSubject:
            raise ManualStructureCandidateBuilderError(
                "subject must be one exact AnalyzedWaveSubject."
            )
        if type(self.manual_behavior_facts) is not tuple:
            raise ManualStructureCandidateBuilderError(
                "manual_behavior_facts must be one exact tuple."
            )
        seen_facts: set[int] = set()
        for fact in self.manual_behavior_facts:
            _validate_fact(fact, self.subject)
            if id(fact) in seen_facts:
                raise ManualStructureCandidateBuilderError(
                    "The same exact manual fact identity cannot be supplied twice."
                )
            seen_facts.add(id(fact))
        effective, constructed = _resolve_binding(self)
        _validate_certificates(self, effective)
        probe = CandidateAnalysisEnvelope(
            self.subject,
            self.candidate_id,
            effective,
            observations=self.observations,
            operational_resolution=self.operational_resolution,
            provenance_refs=self.provenance_refs,
        )
        object.__setattr__(self, "_effective_child_binding", effective)
        object.__setattr__(self, "_constructed_child_binding", constructed)
        object.__setattr__(
            self,
            "_fact_snapshots",
            tuple(_snapshot(fact) for fact in self.manual_behavior_facts),
        )
        object.__setattr__(self, "_transport_probe", probe)
        object.__setattr__(self, "_binding_snapshot", _snapshot(effective))
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
                self.observations,
                self.operational_resolution,
                self.provenance_refs,
                effective,
                constructed,
                probe,
            ),
        )

    def _validated(self) -> ManualStructureCandidateRequest:
        if type(self) is not ManualStructureCandidateRequest:
            raise ManualStructureCandidateBuilderError(
                "Manual request must have its exact reviewed type."
            )
        try:
            snapshot = object.__getattribute__(self, "_identity_snapshot")
            fact_snapshots = object.__getattribute__(self, "_fact_snapshots")
            effective = object.__getattribute__(self, "_effective_child_binding")
            constructed = object.__getattribute__(self, "_constructed_child_binding")
            probe = object.__getattribute__(self, "_transport_probe")
            binding_snapshot = object.__getattribute__(self, "_binding_snapshot")
        except AttributeError as error:
            raise ManualStructureCandidateBuilderError(
                "The manual request is malformed."
            ) from error
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
            self.observations,
            self.operational_resolution,
            self.provenance_refs,
            effective,
            constructed,
            probe,
        )
        if len(snapshot) != len(current) or any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            raise ManualStructureCandidateBuilderError(
                "The manual request changed after construction."
            )
        if len(fact_snapshots) != len(self.manual_behavior_facts) or any(
            not _snapshot_matches(fact, expected)
            for fact, expected in zip(
                self.manual_behavior_facts,
                fact_snapshots,
                strict=True,
            )
        ):
            raise ManualStructureCandidateBuilderError(
                "A manual fact changed after request construction."
            )
        if not _snapshot_matches(effective, binding_snapshot):
            raise ManualStructureCandidateBuilderError(
                "The effective child binding changed after request construction."
            )
        for fact in self.manual_behavior_facts:
            _validate_fact(fact, self.subject)
        _validate_certificates(self, effective)
        try:
            copy.copy(probe)
        except Exception as error:
            raise ManualStructureCandidateBuilderError(
                "The request transport context changed."
            ) from error
        return self

    @property
    def effective_child_binding(self) -> OrderedChildBinding | None:
        return self._validated()._effective_child_binding

    def __copy__(self) -> ManualStructureCandidateRequest:
        return self._validated()

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> ManualStructureCandidateRequest:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Manual structure requests cannot be pickled.")


def _resolve_binding(
    request: ManualStructureCandidateRequest,
) -> tuple[OrderedChildBinding | None, OrderedChildBinding | None]:
    if request.child_binding is not None and request.ordered_child_subjects is not None:
        raise ManualStructureCandidateBuilderError(
            "Supply either an existing binding or explicit ordered children, not both."
        )
    if request.ordered_child_subjects is None:
        if request.constructed_binding_id is not None:
            raise ManualStructureCandidateBuilderError(
                "constructed_binding_id requires explicit ordered child subjects."
            )
        return request.child_binding, None
    if type(request.ordered_child_subjects) is not tuple or any(
        type(child) is not AnalyzedWaveSubject
        for child in request.ordered_child_subjects
    ):
        raise ManualStructureCandidateBuilderError(
            "ordered_child_subjects must be an exact tuple of exact subjects."
        )
    _require_text(request.constructed_binding_id, "constructed_binding_id")
    constructed = OrderedChildBinding(
        request.constructed_binding_id,
        request.subject,
        request.ordered_child_subjects,
    )
    return constructed, constructed


def _validate_certificates(
    request: ManualStructureCandidateRequest,
    binding: OrderedChildBinding | None,
) -> None:
    if type(request.trusted_invalidity_certificates) is not tuple:
        raise ManualStructureCandidateBuilderError(
            "trusted_invalidity_certificates must be one exact tuple."
        )
    seen: set[int] = set()
    for certificate in request.trusted_invalidity_certificates:
        if type(certificate) is not CertifiedStructuralInvalidity:
            raise ManualStructureCandidateBuilderError(
                "Only genuine exact structural-invalidity certificates may pass through."
            )
        try:
            origin_binding = _origin_binding_from_certificate(certificate)
        except Exception as error:
            raise ManualStructureCandidateBuilderError(
                "A trusted certificate is not genuine, live, and unchanged."
            ) from error
        if id(certificate) in seen:
            raise ManualStructureCandidateBuilderError(
                "The same exact certificate identity cannot be supplied twice."
            )
        seen.add(id(certificate))
        if origin_binding is not None and (
            origin_binding.parent_subject is not request.subject
            or origin_binding is not binding
        ):
            raise ManualStructureCandidateBuilderError(
                "A certificate origin differs from the request subject or binding."
            )


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True, init=False)
class ManualStructureCandidateBuildResult(metaclass=_SealedManualType):
    request: ManualStructureCandidateRequest
    effective_child_binding: OrderedChildBinding | None
    constructed_child_binding: OrderedChildBinding | None
    constructed_explicit_behavior_inputs: tuple[ExplicitBehaviorInput, ...]
    delegated_execution_result: ExplicitBehaviorExecutionResult
    provenance_refs: tuple[str, ...]
    _identity_snapshot: tuple[object, ...]

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("Manual build results are created only by MethodologyKernel.")

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("Manual build results cannot be subclassed.")

    def _validated(self) -> ManualStructureCandidateBuildResult:
        if type(self) is not ManualStructureCandidateBuildResult:
            raise ManualStructureCandidateBuilderError("Build result has the wrong type.")
        try:
            snapshot = object.__getattribute__(self, "_identity_snapshot")
        except AttributeError as error:
            raise ManualStructureCandidateBuilderError("Build result is malformed.") from error
        current = (
            self.request,
            self.effective_child_binding,
            self.constructed_child_binding,
            self.constructed_explicit_behavior_inputs,
            self.delegated_execution_result,
            self.provenance_refs,
        )
        if len(snapshot) != len(current) or any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            raise ManualStructureCandidateBuilderError(
                "The manual build result changed after creation."
            )
        self.request._validated()
        try:
            copy.copy(self.delegated_execution_result)
            for item in self.constructed_explicit_behavior_inputs:
                copy.copy(item)
        except Exception as error:
            raise ManualStructureCandidateBuilderError(
                "A nested build result object changed."
            ) from error
        envelope = self.delegated_execution_result.candidate_envelope
        if envelope.subject is not self.request.subject:
            raise ManualStructureCandidateBuilderError(
                "The delegated result belongs to another subject."
            )
        if envelope.child_binding is not self.effective_child_binding:
            raise ManualStructureCandidateBuilderError(
                "The delegated result does not retain the effective binding."
            )
        records = self.delegated_execution_result.execution_records
        if len(records) != len(self.constructed_explicit_behavior_inputs):
            raise ManualStructureCandidateBuilderError(
                "Built inputs and delegated execution records differ."
            )
        for explicit_input, record in zip(
            self.constructed_explicit_behavior_inputs,
            records,
            strict=True,
        ):
            if (
                explicit_input.behavior_id != record.behavior_id
                or explicit_input.input_object is not record.input_object
            ):
                raise ManualStructureCandidateBuilderError(
                    "Delegated execution did not retain an exact built input."
                )
        return self

    @property
    def single_candidate_analysis_result(
        self,
    ) -> SingleCandidateAnalysisResult | None:
        return self.delegated_execution_result.single_candidate_analysis_result

    def __copy__(self) -> ManualStructureCandidateBuildResult:
        return self._validated()

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> ManualStructureCandidateBuildResult:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Manual structure build results cannot be pickled.")


def _new_result(
    request: ManualStructureCandidateRequest,
    explicit_inputs: tuple[ExplicitBehaviorInput, ...],
    delegated: ExplicitBehaviorExecutionResult,
) -> ManualStructureCandidateBuildResult:
    result = object.__new__(ManualStructureCandidateBuildResult)
    values = {
        "request": request,
        "effective_child_binding": request._effective_child_binding,
        "constructed_child_binding": request._constructed_child_binding,
        "constructed_explicit_behavior_inputs": explicit_inputs,
        "delegated_execution_result": delegated,
        "provenance_refs": request.provenance_refs,
    }
    for name, value in values.items():
        object.__setattr__(result, name, value)
    object.__setattr__(result, "_identity_snapshot", tuple(values.values()))
    return result._validated()


def _build_manual_candidate(
    request: object,
    analyze_candidate_inputs: Callable[
        [ExplicitBehaviorExecutionRequest],
        ExplicitBehaviorExecutionResult,
    ],
) -> ManualStructureCandidateBuildResult:
    if type(request) is not ManualStructureCandidateRequest:
        raise ManualStructureCandidateBuilderError(
            "analyze_manual_candidate requires one exact manual request."
        )
    request._validated()
    explicit_inputs = []
    for fact in request.manual_behavior_facts:
        builder = _builder_for(fact)
        input_object = builder.constructor(fact, request._effective_child_binding)
        explicit_inputs.append(
            ExplicitBehaviorInput(
                builder.behavior_id,
                input_object,
                request.provenance_refs,
            )
        )
    for certificate in request.trusted_invalidity_certificates:
        explicit_inputs.append(
            ExplicitBehaviorInput(
                NO_RESCUE_BEHAVIOR,
                certificate,
                request.provenance_refs,
            )
        )
    explicit_tuple = tuple(explicit_inputs)
    execution_request = ExplicitBehaviorExecutionRequest(
        request_id=request.request_id,
        requested_at_utc=request.requested_at_utc,
        subject=request.subject,
        candidate_id=request.candidate_id,
        child_binding=request._effective_child_binding,
        behavior_inputs=explicit_tuple,
        observations=request.observations,
        operational_resolution=request.operational_resolution,
        provenance_refs=request.provenance_refs,
    )
    delegated = analyze_candidate_inputs(execution_request)
    if type(delegated) is not ExplicitBehaviorExecutionResult:
        raise ManualStructureCandidateBuilderError(
            "The existing explicit-input executor returned an unexpected result."
        )
    return _new_result(request, explicit_tuple, delegated)


__all__ = [
    "ARTIFACT_CLASSIFICATION",
    "CALLER_SUPPLIED_STRUCTURAL_FACT",
    "WORKFLOW_POLICY_CLASSIFICATION",
    "ManualCardinalityBehavior",
    "ManualDegreePeerFact",
    "ManualDirectChildCardinalityFact",
    "ManualP003OneLargerDegreeRelationFact",
    "ManualP004Wave2OriginFact",
    "ManualP023VisibilityFact",
    "ManualParentChildDegreeFact",
    "ManualStructureCandidateBuildResult",
    "ManualStructureCandidateBuilderError",
    "ManualStructureCandidateRequest",
]
