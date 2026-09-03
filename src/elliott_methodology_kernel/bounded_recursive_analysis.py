"""Bounded recursive-analysis resolution infrastructure.

This module is PROJECT_ANALYSIS_INFRASTRUCTURE.  Its child aggregation is
PROJECT_OPERATIONAL_POLICY.  Neither creates Elliott validity, structural
invalidity, family completion, parentage, degree, or methodology authority.
Only the exact child tuple supplied by a caller is summarized; an empty tuple
therefore means only that zero supplied children remain unresolved or invalid.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import threading
import weakref

from ._structural_invalidity_certification import CertifiedStructuralInvalidity
from ._validated_internal_family_certification import (
    CertifiedValidatedInternalFamily,
)
from .p023_visibility_guard import (
    P023VisibilityCheckStatus,
    P023VisibilityInput,
    P023VisibilityResult,
    P023VisibilityState,
    check_p023_visibility_guard,
)
from .subject_binding import AnalyzedWaveSubject, OrderedChildBinding


ARTIFACT_CLASSIFICATION = "PROJECT_ANALYSIS_INFRASTRUCTURE"
OPERATIONAL_POLICY_CLASSIFICATION = "PROJECT_OPERATIONAL_POLICY"


class AnalysisResolutionState(StrEnum):
    VALIDATED_FAMILY = "VALIDATED_FAMILY"
    STRUCTURALLY_INVALID = "STRUCTURALLY_INVALID"
    UNRESOLVED_FINER_DATA_REQUIRED = "UNRESOLVED_FINER_DATA_REQUIRED"
    UNRESOLVED_METHODOLOGY_DEPENDENCY = "UNRESOLVED_METHODOLOGY_DEPENDENCY"
    CURRENT_SUPPLIED_SCOPE_UNRESOLVED = "CURRENT_SUPPLIED_SCOPE_UNRESOLVED"
    CURRENT_SUPPLIED_SCOPE_REVIEWED = "CURRENT_SUPPLIED_SCOPE_REVIEWED"


class MethodologyDependencyCode(StrEnum):
    FAMILY_PRODUCER_UNAVAILABLE = "FAMILY_PRODUCER_UNAVAILABLE"
    NESTED_FAMILY_CERTIFICATE_UNAVAILABLE = (
        "NESTED_FAMILY_CERTIFICATE_UNAVAILABLE"
    )
    COMPLETION_AUTHORITY_UNAVAILABLE = "COMPLETION_AUTHORITY_UNAVAILABLE"
    POSITION_AUTHORITY_UNAVAILABLE = "POSITION_AUTHORITY_UNAVAILABLE"
    ENDPOINT_AUTHORITY_UNAVAILABLE = "ENDPOINT_AUTHORITY_UNAVAILABLE"
    P005_P006_PROOF_BLOCKED = "P005_P006_PROOF_BLOCKED"


class OperationalAggregationState(StrEnum):
    BLOCKED_BY_INVALID_CHILD = "BLOCKED_BY_INVALID_CHILD"
    BLOCKED_BY_UNRESOLVED_CHILD = "BLOCKED_BY_UNRESOLVED_CHILD"
    CHILDREN_OPERATIONALLY_RESOLVED = "CHILDREN_OPERATIONALLY_RESOLVED"


class BoundedRecursiveAnalysisContractError(ValueError):
    """Raised when operational analysis input fails closed."""


class _SealedInfrastructureType(type):
    def __new__(
        mcls: type,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
        **kwargs: object,
    ) -> type:
        if any(isinstance(base, mcls) for base in bases):
            raise TypeError("Bounded recursive-analysis contracts cannot be subclassed.")
        return super().__new__(mcls, name, bases, namespace, **kwargs)


def _require_exact_subject(subject: object) -> AnalyzedWaveSubject:
    if type(subject) is not AnalyzedWaveSubject:
        raise BoundedRecursiveAnalysisContractError(
            "subject must be one exact AnalyzedWaveSubject."
        )
    return subject


def _require_nonblank_text(value: object, name: str) -> str:
    if type(value) is not str or value.strip() == "":
        raise BoundedRecursiveAnalysisContractError(
            f"{name} must be an exact non-blank string."
        )
    return value


def _require_provenance_refs(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise BoundedRecursiveAnalysisContractError(
            "provenance_refs must be one exact tuple."
        )
    if any(type(item) is not str or item.strip() == "" for item in value):
        raise BoundedRecursiveAnalysisContractError(
            "provenance_refs must contain only exact non-blank strings."
        )
    return value


def _visibility_snapshot(result: P023VisibilityResult) -> tuple[object, ...]:
    return (
        result.status,
        result.principle_id,
        result.source_class,
        result.execution_role,
        result.protected_sources,
        result.behavior_id,
        result.outcome,
        result.reason,
        result.fatal_to_candidate,
        result.finer_data_required,
    )


def _visibility_snapshot_matches(
    result: P023VisibilityResult,
    snapshot: tuple[object, ...],
) -> bool:
    current = _visibility_snapshot(result)
    if len(snapshot) != len(current):
        return False
    identity_indexes = (0, 2, 3, 8, 9)
    if any(current[index] is not snapshot[index] for index in identity_indexes):
        return False
    text_indexes = (1, 5, 6, 7)
    if any(
        type(current[index]) is not str
        or type(snapshot[index]) is not str
        or str.__eq__(current[index], snapshot[index]) is not True
        for index in text_indexes
    ):
        return False
    protected_sources = current[4]
    expected_sources = snapshot[4]
    return (
        type(protected_sources) is tuple
        and protected_sources is expected_sources
        and all(type(item) is str and item != "" for item in protected_sources)
    )


def _visibility_token_is(value: object, expected: str) -> bool:
    expected_member = P023VisibilityState(expected)
    return value is expected_member or (
        type(value) is str and str.__eq__(value, expected) is True
    )


@dataclass(frozen=True, slots=True, eq=False)
class _VisibilityAttestation:
    subject: AnalyzedWaveSubject
    visibility_state: object
    result: P023VisibilityResult
    snapshot: tuple[object, ...]
    nonce: object


_VISIBILITY_LOCK = threading.RLock()
_VISIBILITY_ISSUED: weakref.WeakKeyDictionary[
    SubjectBoundP023VisibilityResult, _VisibilityAttestation
] = weakref.WeakKeyDictionary()


@dataclass(
    frozen=True,
    slots=True,
    eq=False,
    weakref_slot=True,
    init=False,
)
class SubjectBoundP023VisibilityResult(metaclass=_SealedInfrastructureType):
    """A live infrastructure binding around one unchanged P023 evaluation."""

    _subject: AnalyzedWaveSubject
    _result: P023VisibilityResult
    _nonce: object

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError(
            "Subject-bound P023 results must be created by "
            "evaluate_p023_visibility_for_subject()."
        )

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("Subject-bound P023 results cannot be subclassed.")

    def _validated(self) -> _VisibilityAttestation:
        if type(self) is not SubjectBoundP023VisibilityResult:
            raise BoundedRecursiveAnalysisContractError(
                "A P023 support object must have the exact infrastructure type."
            )
        with _VISIBILITY_LOCK:
            attestation = _VISIBILITY_ISSUED.get(self)
        if attestation is None:
            raise BoundedRecursiveAnalysisContractError(
                "The P023 support object has no live issuance attestation."
            )
        try:
            subject = object.__getattribute__(self, "_subject")
            result = object.__getattribute__(self, "_result")
            nonce = object.__getattribute__(self, "_nonce")
        except AttributeError as error:
            raise BoundedRecursiveAnalysisContractError(
                "The P023 support object is malformed."
            ) from error
        if (
            subject is not attestation.subject
            or result is not attestation.result
            or nonce is not attestation.nonce
            or type(result) is not P023VisibilityResult
            or not _visibility_snapshot_matches(result, attestation.snapshot)
        ):
            raise BoundedRecursiveAnalysisContractError(
                "The P023 support identity or certified fields changed."
            )
        return attestation

    @property
    def subject(self) -> AnalyzedWaveSubject:
        return self._validated().subject

    @property
    def result(self) -> P023VisibilityResult:
        return self._validated().result

    @property
    def visibility_state(self) -> object:
        return self._validated().visibility_state

    def __copy__(self) -> SubjectBoundP023VisibilityResult:
        self._validated()
        return self

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> SubjectBoundP023VisibilityResult:
        self._validated()
        memo[id(self)] = self
        return self

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Subject-bound P023 results cannot be pickled.")


def evaluate_p023_visibility_for_subject(
    subject: AnalyzedWaveSubject,
    candidate: P023VisibilityInput,
) -> SubjectBoundP023VisibilityResult:
    """Evaluate unchanged P023 and bind its result to one exact subject."""
    checked_subject = _require_exact_subject(subject)
    if type(candidate) is not P023VisibilityInput:
        raise BoundedRecursiveAnalysisContractError(
            "candidate must be one exact P023VisibilityInput."
        )
    result = check_p023_visibility_guard(candidate)
    wrapper = object.__new__(SubjectBoundP023VisibilityResult)
    nonce = object()
    object.__setattr__(wrapper, "_subject", checked_subject)
    object.__setattr__(wrapper, "_result", result)
    object.__setattr__(wrapper, "_nonce", nonce)
    attestation = _VisibilityAttestation(
        subject=checked_subject,
        visibility_state=candidate.visibility_state,
        result=result,
        snapshot=_visibility_snapshot(result),
        nonce=nonce,
    )
    with _VISIBILITY_LOCK:
        _VISIBILITY_ISSUED[wrapper] = attestation
    return wrapper


def _validate_family_certificate(
    subject: AnalyzedWaveSubject,
    certificate: object,
) -> None:
    if type(certificate) is not CertifiedValidatedInternalFamily:
        raise BoundedRecursiveAnalysisContractError(
            "VALIDATED_FAMILY requires one exact certified family object."
        )
    try:
        certified_subject = certificate.subject
    except Exception as error:
        raise BoundedRecursiveAnalysisContractError(
            "The family certificate is not genuine, live, and unchanged."
        ) from error
    if certified_subject is not subject:
        raise BoundedRecursiveAnalysisContractError(
            "The family certificate belongs to a different subject identity."
        )


def _validate_structural_certificate_subject(
    subject: AnalyzedWaveSubject,
    certificate: object,
) -> None:
    if type(certificate) is not CertifiedStructuralInvalidity:
        raise BoundedRecursiveAnalysisContractError(
            "STRUCTURALLY_INVALID requires one exact structural certificate."
        )
    try:
        origin = certificate.origin
        fatal = certificate.fatal_to_candidate
        validity = certificate.structural_validity
    except Exception as error:
        raise BoundedRecursiveAnalysisContractError(
            "The structural certificate is not genuine, live, and unchanged."
        ) from error
    if fatal is not True or getattr(validity, "value", None) != "INVALID":
        raise BoundedRecursiveAnalysisContractError(
            "The structural certificate does not attest fatal invalidity."
        )

    binding = getattr(origin, "binding", None)
    if binding is not None:
        if type(binding) is not OrderedChildBinding:
            raise BoundedRecursiveAnalysisContractError(
                "The structural origin has malformed subject binding."
            )
        if binding.parent_subject is not subject:
            raise BoundedRecursiveAnalysisContractError(
                "The structural certificate origin belongs to a different subject."
            )


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class BoundedRecursiveAnalysisResolution(metaclass=_SealedInfrastructureType):
    """One immutable, subject-bound operational resolution, never methodology."""

    subject: AnalyzedWaveSubject
    state: AnalysisResolutionState
    reason: str
    supporting_family_certificate: CertifiedValidatedInternalFamily | None = None
    supporting_structural_invalidity_certificate: (
        CertifiedStructuralInvalidity | None
    ) = None
    supporting_visibility_result: SubjectBoundP023VisibilityResult | None = None
    dependency_code: MethodologyDependencyCode | None = None
    provenance_refs: tuple[str, ...] = ()

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("Bounded recursive-analysis resolutions cannot be subclassed.")

    def __post_init__(self) -> None:
        subject = _require_exact_subject(self.subject)
        if type(self.state) is not AnalysisResolutionState:
            raise BoundedRecursiveAnalysisContractError(
                "state must be one exact AnalysisResolutionState."
            )
        _require_nonblank_text(self.reason, "reason")
        _require_provenance_refs(self.provenance_refs)

        supports = (
            self.supporting_family_certificate,
            self.supporting_structural_invalidity_certificate,
            self.supporting_visibility_result,
        )
        supplied_support_count = sum(value is not None for value in supports)

        if self.state is AnalysisResolutionState.VALIDATED_FAMILY:
            if supplied_support_count != 1 or self.dependency_code is not None:
                raise BoundedRecursiveAnalysisContractError(
                    "VALIDATED_FAMILY requires only one family certificate."
                )
            _validate_family_certificate(
                subject, self.supporting_family_certificate
            )
            return

        if self.state is AnalysisResolutionState.STRUCTURALLY_INVALID:
            if supplied_support_count != 1 or self.dependency_code is not None:
                raise BoundedRecursiveAnalysisContractError(
                    "STRUCTURALLY_INVALID requires only one structural certificate."
                )
            _validate_structural_certificate_subject(
                subject,
                self.supporting_structural_invalidity_certificate,
            )
            return

        if self.state is AnalysisResolutionState.UNRESOLVED_FINER_DATA_REQUIRED:
            if supplied_support_count != 1 or self.dependency_code is not None:
                raise BoundedRecursiveAnalysisContractError(
                    "Finer-data resolution requires only one subject-bound P023 result."
                )
            visibility = self.supporting_visibility_result
            if type(visibility) is not SubjectBoundP023VisibilityResult:
                raise BoundedRecursiveAnalysisContractError(
                    "Finer-data resolution requires exact subject-bound P023 support."
                )
            if visibility.subject is not subject:
                raise BoundedRecursiveAnalysisContractError(
                    "The P023 support belongs to a different subject identity."
                )
            result = visibility.result
            visibility_state = visibility.visibility_state
            not_visible = _visibility_token_is(
                visibility_state, "NOT_VISIBLE"
            ) and result.status is P023VisibilityCheckStatus.INTERNALS_UNRESOLVED
            unknown = _visibility_token_is(
                visibility_state, "UNKNOWN"
            ) and result.status is P023VisibilityCheckStatus.UNRESOLVED_MISSING_INPUT
            if not (not_visible or unknown):
                raise BoundedRecursiveAnalysisContractError(
                    "Only exact P023 NOT_VISIBLE or UNKNOWN can create a finer-data stop."
                )
            return

        if self.state is AnalysisResolutionState.UNRESOLVED_METHODOLOGY_DEPENDENCY:
            if supplied_support_count != 0:
                raise BoundedRecursiveAnalysisContractError(
                    "Methodology-dependency resolution cannot carry a certificate or P023 support."
                )
            if type(self.dependency_code) is not MethodologyDependencyCode:
                raise BoundedRecursiveAnalysisContractError(
                    "Methodology-dependency resolution requires one exact dependency code."
                )
            return

        if self.state in (
            AnalysisResolutionState.CURRENT_SUPPLIED_SCOPE_UNRESOLVED,
            AnalysisResolutionState.CURRENT_SUPPLIED_SCOPE_REVIEWED,
        ):
            if supplied_support_count != 0 or self.dependency_code is not None:
                raise BoundedRecursiveAnalysisContractError(
                    "Current-scope operational states cannot carry methodology support."
                )
            return

        raise BoundedRecursiveAnalysisContractError("Unsupported resolution state.")

    def __copy__(self) -> BoundedRecursiveAnalysisResolution:
        return self

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> BoundedRecursiveAnalysisResolution:
        memo[id(self)] = self
        return self

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Bounded recursive-analysis resolutions cannot be pickled.")


def _validate_resolution_instance(
    resolution: object,
) -> BoundedRecursiveAnalysisResolution:
    if type(resolution) is not BoundedRecursiveAnalysisResolution:
        raise BoundedRecursiveAnalysisContractError(
            "resolution must be one exact operational resolution."
        )
    resolution.__post_init__()
    return resolution


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class BoundedRecursiveAnalysisNode(metaclass=_SealedInfrastructureType):
    """One operational node over only the exact caller-supplied child tuple."""

    subject: AnalyzedWaveSubject
    child_binding: OrderedChildBinding | None
    children: tuple[BoundedRecursiveAnalysisNode, ...]
    resolution: BoundedRecursiveAnalysisResolution

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("Bounded recursive-analysis nodes cannot be subclassed.")

    def __post_init__(self) -> None:
        subject = _require_exact_subject(self.subject)
        _validate_resolution_instance(self.resolution)
        if self.resolution.subject is not subject:
            raise BoundedRecursiveAnalysisContractError(
                "Node and resolution must retain the same exact subject."
            )
        if type(self.children) is not tuple or any(
            type(child) is not BoundedRecursiveAnalysisNode
            for child in self.children
        ):
            raise BoundedRecursiveAnalysisContractError(
                "children must be one exact tuple of exact analysis nodes."
            )
        if self.child_binding is None:
            if self.children:
                raise BoundedRecursiveAnalysisContractError(
                    "Non-empty children require one exact OrderedChildBinding."
                )
            return
        if type(self.child_binding) is not OrderedChildBinding:
            raise BoundedRecursiveAnalysisContractError(
                "child_binding must be one exact OrderedChildBinding or None."
            )
        if self.child_binding.parent_subject is not subject:
            raise BoundedRecursiveAnalysisContractError(
                "The child binding belongs to a different parent subject."
            )
        if len(self.children) != len(self.child_binding.ordered_children) or any(
            node.subject is not child_subject
            for node, child_subject in zip(
                self.children,
                self.child_binding.ordered_children,
                strict=True,
            )
        ):
            raise BoundedRecursiveAnalysisContractError(
                "Child nodes must exactly match binding identities and order."
            )

    def __copy__(self) -> BoundedRecursiveAnalysisNode:
        return self

    def __deepcopy__(self, memo: dict[int, object]) -> BoundedRecursiveAnalysisNode:
        memo[id(self)] = self
        return self

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Bounded recursive-analysis nodes cannot be pickled.")


def aggregate_supplied_child_resolutions(
    children: tuple[BoundedRecursiveAnalysisNode, ...],
) -> OperationalAggregationState:
    """Summarize supplied children with invalid-before-unresolved precedence.

    An empty exact tuple returns CHILDREN_OPERATIONALLY_RESOLVED by vacuous
    operational policy.  It says nothing about methodology-required children
    and cannot establish parent validity, completion, family, or certification.
    """
    if type(children) is not tuple or any(
        type(child) is not BoundedRecursiveAnalysisNode for child in children
    ):
        raise BoundedRecursiveAnalysisContractError(
            "children must be one exact tuple of exact analysis nodes."
        )
    def subtree_flags(
        node: BoundedRecursiveAnalysisNode,
        active_node_ids: set[int],
    ) -> tuple[bool, bool]:
        node_id = id(node)
        if node_id in active_node_ids:
            raise BoundedRecursiveAnalysisContractError(
                "Recursive analysis nodes cannot contain a cycle."
            )
        active_node_ids.add(node_id)
        try:
            node.__post_init__()
            invalid = (
                node.resolution.state
                is AnalysisResolutionState.STRUCTURALLY_INVALID
            )
            unresolved = node.resolution.state in (
                AnalysisResolutionState.UNRESOLVED_FINER_DATA_REQUIRED,
                AnalysisResolutionState.UNRESOLVED_METHODOLOGY_DEPENDENCY,
                AnalysisResolutionState.CURRENT_SUPPLIED_SCOPE_UNRESOLVED,
            )
            for descendant in node.children:
                child_invalid, child_unresolved = subtree_flags(
                    descendant,
                    active_node_ids,
                )
                invalid = invalid or child_invalid
                unresolved = unresolved or child_unresolved
            return invalid, unresolved
        finally:
            active_node_ids.remove(node_id)

    subtree_states = tuple(subtree_flags(child, set()) for child in children)
    if any(invalid for invalid, _ in subtree_states):
        return OperationalAggregationState.BLOCKED_BY_INVALID_CHILD
    if any(unresolved for _, unresolved in subtree_states):
        return OperationalAggregationState.BLOCKED_BY_UNRESOLVED_CHILD
    return OperationalAggregationState.CHILDREN_OPERATIONALLY_RESOLVED


__all__ = [
    "ARTIFACT_CLASSIFICATION",
    "OPERATIONAL_POLICY_CLASSIFICATION",
    "AnalysisResolutionState",
    "BoundedRecursiveAnalysisContractError",
    "BoundedRecursiveAnalysisNode",
    "BoundedRecursiveAnalysisResolution",
    "MethodologyDependencyCode",
    "OperationalAggregationState",
    "SubjectBoundP023VisibilityResult",
    "aggregate_supplied_child_resolutions",
    "evaluate_p023_visibility_for_subject",
]
