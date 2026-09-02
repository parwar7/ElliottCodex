"""Private issuance and validation for certified structural invalidities.

The public contract is re-exported through ``elliott_methodology_kernel.contracts``.
This module provides logical, in-process integrity.  It does not claim protection
against hostile reflection in the same Python interpreter.
"""

from __future__ import annotations

from dataclasses import dataclass, is_dataclass
from enum import Enum
import hashlib
import json
import threading
from typing import Generic, TypeVar, cast
import uuid
import weakref

from .models import SourceClassification, StructuralValidity


class StructuralValidatorResult:
    """Nominal marker for a reviewed structural validator result type."""

    __slots__ = ()


class StructuralInvalidityCertificationError(ValueError):
    """Raised when an origin cannot be certified fail-closed."""


_TOrigin = TypeVar("_TOrigin", bound=StructuralValidatorResult)


@dataclass(frozen=True, slots=True, eq=False)
class _ProducerSpec:
    result_type: type[StructuralValidatorResult]
    violation_statuses: tuple[Enum, ...]
    hard_validation_role: Enum
    principle_attribute: str
    behavior_id: str
    principle_id: str | None
    source_class: SourceClassification
    protected_sources: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _OriginView:
    status: Enum
    principle_id: str | None
    source_class: SourceClassification
    execution_role: Enum
    protected_sources: tuple[str, ...]
    behavior_id: str
    outcome: str
    reason: str
    fatal_to_candidate: bool


@dataclass(frozen=True, slots=True, eq=False)
class _OriginAttestation:
    origin_ref: weakref.ReferenceType[StructuralValidatorResult]
    origin_id: str
    spec: _ProducerSpec
    digest: str


@dataclass(frozen=True, slots=True, eq=False)
class _ProducerIssuer(Generic[_TOrigin]):
    _spec: _ProducerSpec

    def issue(self, origin: _TOrigin) -> _TOrigin:
        """Issue one origin from this reviewed producer and return it unchanged."""
        return _issue_structural_invalidity(self, origin)


_REGISTRY_LOCK = threading.RLock()
_PRODUCERS: dict[type[StructuralValidatorResult], _ProducerSpec] = {}
_BEHAVIOR_IDS: set[str] = set()
_ISSUED: dict[int, _OriginAttestation] = {}
_REGISTRY_SEALED = False


def _certification_error(message: str) -> StructuralInvalidityCertificationError:
    return StructuralInvalidityCertificationError(message)


def _require_exact_nonempty_text(value: object, field_name: str) -> str:
    if type(value) is not str or value == "":
        raise _certification_error(
            f"Structural invalidity {field_name} must be an exact non-empty string."
        )
    return value


def _exact_text_equal(left: str, right: str) -> bool:
    return type(left) is str and type(right) is str and str.__eq__(left, right) is True


def _exact_text_tuple_equal(
    observed: tuple[str, ...], expected: tuple[str, ...]
) -> bool:
    if (
        type(observed) is not tuple
        or not observed
        or len(observed) != len(expected)
    ):
        return False
    if any(type(item) is not str or item == "" for item in observed):
        return False
    return all(
        _exact_text_equal(observed_item, expected_item)
        for observed_item, expected_item in zip(observed, expected, strict=True)
    )


def _register_structural_validator(
    result_type: type[_TOrigin],
    *,
    violation_statuses: tuple[Enum, ...],
    hard_validation_role: Enum,
    principle_attribute: str,
    behavior_id: str,
    principle_id: str | None,
    source_class: SourceClassification,
    protected_sources: tuple[str, ...],
) -> _ProducerIssuer[_TOrigin]:
    """Privately register one reviewed producer before package bootstrap seals."""
    global _REGISTRY_SEALED

    with _REGISTRY_LOCK:
        if _REGISTRY_SEALED:
            raise _certification_error(
                "The structural invalidity producer registry is sealed."
            )
        if not isinstance(result_type, type) or not issubclass(
            result_type, StructuralValidatorResult
        ):
            raise _certification_error(
                "A structural invalidity producer must use the nominal result marker."
            )
        if result_type is StructuralValidatorResult:
            raise _certification_error("The nominal marker cannot be a producer.")
        if result_type in _PRODUCERS:
            raise _certification_error(
                "The structural invalidity result type is already registered."
            )
        if not is_dataclass(result_type):
            raise _certification_error(
                "A structural invalidity producer result must be a dataclass."
            )
        dataclass_parameters = result_type.__dataclass_params__
        if not dataclass_parameters.frozen or not hasattr(result_type, "__slots__"):
            raise _certification_error(
                "A structural invalidity producer result must be frozen and slotted."
            )
        if type(violation_statuses) is not tuple or not violation_statuses:
            raise _certification_error(
                "A producer must declare at least one exact violation status."
            )
        if any(not isinstance(status, Enum) for status in violation_statuses):
            raise _certification_error("Violation statuses must be enum members.")
        if any(
            left is right
            for index, left in enumerate(violation_statuses)
            for right in violation_statuses[index + 1 :]
        ):
            raise _certification_error("Violation statuses must be unique by identity.")
        if not isinstance(hard_validation_role, Enum):
            raise _certification_error(
                "The producer hard-validation role must be an enum member."
            )
        _require_exact_nonempty_text(principle_attribute, "principle attribute")
        registered_behavior_id = _require_exact_nonempty_text(
            behavior_id, "behavior ID"
        )
        if registered_behavior_id in _BEHAVIOR_IDS:
            raise _certification_error(
                "The structural invalidity behavior ID is already registered."
            )
        if principle_id is not None:
            _require_exact_nonempty_text(principle_id, "principle ID")
        if type(source_class) is not SourceClassification:
            raise _certification_error(
                "The producer source class must be a protected SourceClassification."
            )
        if not _exact_text_tuple_equal(protected_sources, protected_sources):
            raise _certification_error(
                "Producer protected sources must be an exact tuple of non-empty strings."
            )

        spec = _ProducerSpec(
            result_type=cast(type[StructuralValidatorResult], result_type),
            violation_statuses=violation_statuses,
            hard_validation_role=hard_validation_role,
            principle_attribute=principle_attribute,
            behavior_id=registered_behavior_id,
            principle_id=principle_id,
            source_class=source_class,
            protected_sources=protected_sources,
        )
        _PRODUCERS[spec.result_type] = spec
        _BEHAVIOR_IDS.add(spec.behavior_id)
        return _ProducerIssuer(spec)


def _seal_structural_validator_registry(
    *, expected_result_types: tuple[type[StructuralValidatorResult], ...]
) -> None:
    """Seal the reviewed bootstrap set without changing certification semantics."""
    global _REGISTRY_SEALED

    if type(expected_result_types) is not tuple or any(
        not isinstance(result_type, type) for result_type in expected_result_types
    ):
        raise _certification_error("Expected producer types must be an exact tuple.")
    expected = set(expected_result_types)
    if len(expected) != len(expected_result_types):
        raise _certification_error("Expected producer types must be unique.")

    with _REGISTRY_LOCK:
        if set(_PRODUCERS) != expected:
            raise _certification_error(
                "The reviewed structural invalidity producer set is incomplete or unexpected."
            )
        _REGISTRY_SEALED = True


def _read_origin_view(
    origin: StructuralValidatorResult, spec: _ProducerSpec
) -> _OriginView:
    if type(origin) is not spec.result_type:
        raise _certification_error(
            "Structural invalidity origins require an exact registered result type."
        )

    try:
        status = object.__getattribute__(origin, "status")
        principle_id = object.__getattribute__(origin, spec.principle_attribute)
        source_class = object.__getattribute__(origin, "source_class")
        execution_role = object.__getattribute__(origin, "execution_role")
        protected_sources = object.__getattribute__(origin, "protected_sources")
        behavior_id = object.__getattribute__(origin, "behavior_id")
        outcome = object.__getattribute__(origin, "outcome")
        reason = object.__getattribute__(origin, "reason")
        fatal_to_candidate = object.__getattribute__(origin, "fatal_to_candidate")
    except Exception as error:
        raise _certification_error(
            "The registered structural invalidity origin is malformed."
        ) from error

    if not any(status is violation_status for violation_status in spec.violation_statuses):
        raise _certification_error(
            "The origin status is not a registered structural violation."
        )
    if execution_role is not spec.hard_validation_role:
        raise _certification_error(
            "The origin execution role is not the registered hard-validation role."
        )
    if fatal_to_candidate is not True:
        raise _certification_error(
            "A certified structural invalidity must already be fatal to the candidate."
        )
    if source_class is not spec.source_class:
        raise _certification_error("The origin source classification is inconsistent.")
    if principle_id is not None and type(principle_id) is not str:
        raise _certification_error("The origin principle ID is malformed.")
    if principle_id != spec.principle_id:
        raise _certification_error("The origin principle ID is inconsistent.")
    if not _exact_text_equal(behavior_id, spec.behavior_id):
        raise _certification_error("The origin behavior ID is inconsistent.")
    if not _exact_text_tuple_equal(protected_sources, spec.protected_sources):
        raise _certification_error("The origin protected sources are inconsistent.")
    checked_outcome = _require_exact_nonempty_text(outcome, "outcome")
    checked_reason = _require_exact_nonempty_text(reason, "reason")
    status_value = getattr(status, "value", None)
    if type(status_value) is not str or not _exact_text_equal(
        checked_outcome, status_value
    ):
        raise _certification_error("The origin status and outcome are inconsistent.")

    return _OriginView(
        status=status,
        principle_id=principle_id,
        source_class=source_class,
        execution_role=execution_role,
        protected_sources=protected_sources,
        behavior_id=behavior_id,
        outcome=checked_outcome,
        reason=checked_reason,
        fatal_to_candidate=True,
    )


def _enum_descriptor(value: Enum) -> dict[str, str]:
    enum_value = value.value
    if type(enum_value) is not str:
        raise _certification_error(
            "Certified structural invalidity enums must have exact string values."
        )
    return {
        "module": type(value).__module__,
        "type": type(value).__qualname__,
        "name": value.name,
        "value": enum_value,
    }


def _origin_digest(
    origin: StructuralValidatorResult,
    origin_id: str,
    view: _OriginView,
) -> str:
    payload = {
        "origin_id": origin_id,
        "origin_type": {
            "module": type(origin).__module__,
            "type": type(origin).__qualname__,
        },
        "behavior_id": view.behavior_id,
        "principle_id": view.principle_id,
        "source_class": _enum_descriptor(view.source_class),
        "execution_role": _enum_descriptor(view.execution_role),
        "status": _enum_descriptor(view.status),
        "outcome": view.outcome,
        "reason": view.reason,
        "protected_sources": list(view.protected_sources),
        "fatal_to_candidate": view.fatal_to_candidate,
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _issue_structural_invalidity(
    issuer: _ProducerIssuer[_TOrigin], origin: _TOrigin
) -> _TOrigin:
    with _REGISTRY_LOCK:
        if not _REGISTRY_SEALED:
            raise _certification_error(
                "Structural invalidity issuance is unavailable before registry sealing."
            )
        spec = _PRODUCERS.get(type(origin))
        if spec is None or spec is not issuer._spec:
            raise _certification_error(
                "The origin was not issued by its registered structural validator."
            )
        view = _read_origin_view(origin, spec)
        origin_key = id(origin)
        existing = _ISSUED.get(origin_key)
        if existing is not None:
            if existing.origin_ref() is not origin or existing.spec is not spec:
                raise _certification_error(
                    "Structural invalidity origin identity is inconsistent."
                )
            if existing.digest != _origin_digest(
                origin, existing.origin_id, view
            ):
                raise _certification_error(
                    "Structural invalidity origin changed after issuance."
                )
            return origin

        origin_id = uuid.uuid4().hex

        def remove_dead_origin(
            dead_reference: weakref.ReferenceType[StructuralValidatorResult],
            *,
            key: int = origin_key,
        ) -> None:
            with _REGISTRY_LOCK:
                current = _ISSUED.get(key)
                if current is not None and current.origin_ref is dead_reference:
                    _ISSUED.pop(key, None)

        try:
            origin_reference = weakref.ref(origin, remove_dead_origin)
        except TypeError as error:
            raise _certification_error(
                "A structural invalidity origin must support weak references."
            ) from error
        attestation = _OriginAttestation(
            origin_ref=origin_reference,
            origin_id=origin_id,
            spec=spec,
            digest=_origin_digest(origin, origin_id, view),
        )
        _ISSUED[origin_key] = attestation
        return origin


def _validated_origin(
    origin: object,
) -> tuple[_OriginAttestation, _OriginView]:
    with _REGISTRY_LOCK:
        if not _REGISTRY_SEALED:
            raise _certification_error(
                "Structural invalidity certification is unavailable before sealing."
            )
        origin_type = type(origin)
        spec = _PRODUCERS.get(origin_type)
        if spec is None or not isinstance(origin, StructuralValidatorResult):
            raise _certification_error(
                "The origin is not an exact registered structural validator result."
            )
        attestation = _ISSUED.get(id(origin))
        if (
            type(attestation) is not _OriginAttestation
            or attestation.origin_ref() is not origin
            or attestation.spec is not spec
        ):
            raise _certification_error(
                "The origin was not issued as a certified structural violation."
            )
        typed_origin = cast(StructuralValidatorResult, origin)
        view = _read_origin_view(typed_origin, spec)
        if attestation.digest != _origin_digest(
            typed_origin, attestation.origin_id, view
        ):
            raise _certification_error(
                "The structural invalidity origin changed after issuance."
            )
        return attestation, view


@dataclass(frozen=True, slots=True, init=False, repr=False, eq=False)
class CertifiedStructuralInvalidity(Generic[_TOrigin]):
    """Immutable certificate retaining one exact, live structural violation."""

    _origin: _TOrigin
    _attestation: _OriginAttestation

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError(
            "CertifiedStructuralInvalidity instances are created only by "
            "certify_structural_invalidity()."
        )

    def _validated(self) -> tuple[_OriginAttestation, _OriginView]:
        if type(self) is not CertifiedStructuralInvalidity:
            raise _certification_error(
                "Structural invalidity certificate subclasses are not accepted."
            )
        try:
            origin = object.__getattribute__(self, "_origin")
            expected_attestation = object.__getattribute__(self, "_attestation")
        except Exception as error:
            raise _certification_error(
                "The structural invalidity certificate is malformed."
            ) from error
        attestation, view = _validated_origin(origin)
        if attestation is not expected_attestation:
            raise _certification_error(
                "The structural invalidity attestation does not match its origin."
            )
        return attestation, view

    @property
    def origin(self) -> _TOrigin:
        self._validated()
        return object.__getattribute__(self, "_origin")

    @property
    def origin_id(self) -> str:
        attestation, _ = self._validated()
        return attestation.origin_id

    @property
    def origin_behavior_id(self) -> str:
        _, view = self._validated()
        return view.behavior_id

    @property
    def origin_principle_id(self) -> str | None:
        _, view = self._validated()
        return view.principle_id

    @property
    def origin_source_class(self) -> SourceClassification:
        _, view = self._validated()
        return view.source_class

    @property
    def origin_execution_role(self) -> Enum:
        _, view = self._validated()
        return view.execution_role

    @property
    def origin_status(self) -> Enum:
        _, view = self._validated()
        return view.status

    @property
    def origin_outcome(self) -> str:
        _, view = self._validated()
        return view.outcome

    @property
    def origin_reason(self) -> str:
        _, view = self._validated()
        return view.reason

    @property
    def origin_protected_sources(self) -> tuple[str, ...]:
        _, view = self._validated()
        return view.protected_sources

    @property
    def fatal_to_candidate(self) -> bool:
        _, view = self._validated()
        return view.fatal_to_candidate

    @property
    def structural_validity(self) -> StructuralValidity:
        self._validated()
        return StructuralValidity.INVALID

    def __repr__(self) -> str:
        return (
            "CertifiedStructuralInvalidity("
            f"origin_id={self.origin_id!r}, "
            f"origin_behavior_id={self.origin_behavior_id!r}, "
            f"structural_validity={self.structural_validity!r})"
        )

    def __copy__(self) -> CertifiedStructuralInvalidity[_TOrigin]:
        self._validated()
        return self

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> CertifiedStructuralInvalidity[_TOrigin]:
        self._validated()
        memo[id(self)] = self
        return self

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Certified structural invalidities cannot be pickled.")


def _new_certificate(
    origin: _TOrigin, attestation: _OriginAttestation
) -> CertifiedStructuralInvalidity[_TOrigin]:
    certificate = object.__new__(CertifiedStructuralInvalidity)
    object.__setattr__(certificate, "_origin", origin)
    object.__setattr__(certificate, "_attestation", attestation)
    return cast(CertifiedStructuralInvalidity[_TOrigin], certificate)


def certify_structural_invalidity(
    origin: _TOrigin,
) -> CertifiedStructuralInvalidity[_TOrigin]:
    """Certify one genuine producer-issued fatal structural violation."""
    attestation, _ = _validated_origin(origin)
    certificate = _new_certificate(origin, attestation)
    certificate._validated()
    return certificate


__all__ = [
    "CertifiedStructuralInvalidity",
    "StructuralInvalidityCertificationError",
    "StructuralValidatorResult",
    "certify_structural_invalidity",
]
