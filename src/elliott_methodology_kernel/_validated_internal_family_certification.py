"""Private issuance for independently validated internal-family proofs.

The V1 registry is intentionally empty and sealed by package bootstrap.  The
private producer machinery is dormant until a genuine family validator and
its exact subject/provenance contract receive separate review.  This module
provides logical same-process API integrity only; it does not claim protection
against hostile reflection in the same interpreter or cryptographic security.
"""

from __future__ import annotations

from dataclasses import dataclass, is_dataclass
from enum import Enum, StrEnum
import hashlib
import json
import threading
from typing import Callable, Generic, TypeVar, cast
import uuid
import weakref


class InternalFamilyKind(StrEnum):
    MOTIVE_FIVE_WAVE_FAMILY = "MOTIVE_FIVE_WAVE_FAMILY"
    CORRECTIVE_THREE_WAVE_FAMILY = "CORRECTIVE_THREE_WAVE_FAMILY"


class InternalFamilyValidatorResult:
    """Nominal marker for a future reviewed family-validator result."""

    __slots__ = ()


class ValidatedInternalFamilyCertificationError(ValueError):
    """Raised when a positive family origin cannot be certified fail-closed."""


_TOrigin = TypeVar("_TOrigin", bound=InternalFamilyValidatorResult)


@dataclass(frozen=True, slots=True, eq=False)
class _SourceProvenanceView:
    principle_ids: tuple[str, ...]
    source_classes: tuple[Enum, ...]
    protected_sources: tuple[str, ...]


@dataclass(frozen=True, slots=True, eq=False)
class _SubjectBindingView:
    subject: object
    provenance_components: tuple[str, ...]
    nested_proofs: tuple[CertifiedValidatedInternalFamily[InternalFamilyValidatorResult], ...] = ()


_SourceProvenanceExtractor = Callable[
    [InternalFamilyValidatorResult], _SourceProvenanceView
]
_SourceProvenanceVerifier = Callable[
    [InternalFamilyValidatorResult, _SourceProvenanceView], bool
]
_SubjectBindingExtractor = Callable[
    [InternalFamilyValidatorResult], _SubjectBindingView
]
_SubjectProvenanceVerifier = Callable[
    [InternalFamilyValidatorResult, _SubjectBindingView], bool
]


@dataclass(frozen=True, slots=True, eq=False)
class _ProducerSpec:
    result_type: type[InternalFamilyValidatorResult]
    success_statuses: tuple[Enum, ...]
    family_kind: InternalFamilyKind
    execution_role: Enum
    behavior_id: str
    subject_type: type[object]
    source_provenance_extractor: _SourceProvenanceExtractor
    source_provenance_verifier: _SourceProvenanceVerifier
    subject_binding_extractor: _SubjectBindingExtractor
    subject_provenance_verifier: _SubjectProvenanceVerifier


@dataclass(frozen=True, slots=True, eq=False)
class _OriginView:
    status: Enum
    family_kind: InternalFamilyKind
    execution_role: Enum
    behavior_id: str
    outcome: str
    reason: str
    source_provenance: _SourceProvenanceView
    subject_binding: _SubjectBindingView


@dataclass(frozen=True, slots=True, eq=False)
class _OriginAttestation:
    origin_ref: weakref.ReferenceType[InternalFamilyValidatorResult]
    origin_id: str
    binding_id: str
    spec: _ProducerSpec
    subject: object
    nested_proofs: tuple[CertifiedValidatedInternalFamily[InternalFamilyValidatorResult], ...]
    subject_provenance_digest: str
    certified_fields_digest: str


@dataclass(frozen=True, slots=True, eq=False)
class _ProducerIssuer(Generic[_TOrigin]):
    _spec: _ProducerSpec

    def issue(self, origin: _TOrigin) -> _TOrigin:
        """Attest one genuine future producer success and return it unchanged."""
        return _issue_validated_internal_family(self, origin)


_REGISTRY_LOCK = threading.RLock()
_PRODUCERS: dict[type[InternalFamilyValidatorResult], _ProducerSpec] = {}
_BEHAVIOR_IDS: set[str] = set()
_ISSUED: dict[int, _OriginAttestation] = {}
_REGISTRY_SEALED = False


def _certification_error(
    message: str,
) -> ValidatedInternalFamilyCertificationError:
    return ValidatedInternalFamilyCertificationError(message)


def _require_exact_nonempty_text(value: object, field_name: str) -> str:
    if type(value) is not str or value == "":
        raise _certification_error(
            f"Validated internal family {field_name} must be an exact non-empty string."
        )
    return value


def _exact_text_equal(left: str, right: str) -> bool:
    return type(left) is str and type(right) is str and str.__eq__(left, right) is True


def _exact_text_tuple(
    value: object, field_name: str, *, require_principle_ids: bool = False
) -> tuple[str, ...]:
    if type(value) is not tuple or not value:
        raise _certification_error(
            f"Validated internal family {field_name} must be a non-empty exact tuple."
        )
    checked = cast(tuple[object, ...], value)
    if any(type(item) is not str or item == "" for item in checked):
        raise _certification_error(
            f"Validated internal family {field_name} contains malformed text."
        )
    strings = cast(tuple[str, ...], checked)
    if require_principle_ids and any(
        len(item) != 4 or item[0] != "P" or not item[1:].isdigit()
        for item in strings
    ):
        raise _certification_error(
            "Validated internal family principle IDs must use exact P### values."
        )
    return strings


def _enum_descriptor(value: Enum) -> dict[str, str]:
    enum_value = value.value
    if type(enum_value) is not str:
        raise _certification_error(
            "Validated internal family enums must have exact string values."
        )
    return {
        "module": type(value).__module__,
        "type": type(value).__qualname__,
        "name": value.name,
        "value": enum_value,
    }


def _callable_descriptor(value: Callable[..., object]) -> dict[str, str]:
    module = getattr(value, "__module__", None)
    name = getattr(value, "__qualname__", None)
    if type(module) is not str or module == "" or type(name) is not str or name == "":
        raise _certification_error(
            "A private family-producer callback has no stable descriptor."
        )
    return {"module": module, "name": name}


def _register_internal_family_validator(
    result_type: type[_TOrigin],
    *,
    success_statuses: tuple[Enum, ...],
    family_kind: InternalFamilyKind,
    execution_role: Enum,
    behavior_id: str,
    subject_type: type[object],
    source_provenance_extractor: _SourceProvenanceExtractor,
    source_provenance_verifier: _SourceProvenanceVerifier,
    subject_binding_extractor: _SubjectBindingExtractor,
    subject_provenance_verifier: _SubjectProvenanceVerifier,
) -> _ProducerIssuer[_TOrigin]:
    """Register one separately reviewed producer before bootstrap sealing."""
    global _REGISTRY_SEALED

    with _REGISTRY_LOCK:
        if _REGISTRY_SEALED:
            raise _certification_error(
                "The validated internal-family producer registry is sealed."
            )
        if not isinstance(result_type, type) or not issubclass(
            result_type, InternalFamilyValidatorResult
        ):
            raise _certification_error(
                "A family producer must use the nominal result marker."
            )
        if result_type is InternalFamilyValidatorResult:
            raise _certification_error("The nominal marker cannot be a producer.")
        if result_type in _PRODUCERS:
            raise _certification_error(
                "The internal-family result type is already registered."
            )
        if not is_dataclass(result_type):
            raise _certification_error(
                "An internal-family producer result must be a dataclass."
            )
        parameters = result_type.__dataclass_params__
        if (
            not parameters.frozen
            or not hasattr(result_type, "__slots__")
            or not hasattr(result_type, "__weakref__")
        ):
            raise _certification_error(
                "An internal-family producer result must be frozen, slotted, and weak-referenceable."
            )
        if type(success_statuses) is not tuple or not success_statuses:
            raise _certification_error(
                "A family producer must declare at least one exact success status."
            )
        if any(not isinstance(status, Enum) for status in success_statuses):
            raise _certification_error("Family success statuses must be enum members.")
        if any(
            left is right
            for index, left in enumerate(success_statuses)
            for right in success_statuses[index + 1 :]
        ):
            raise _certification_error(
                "Family success statuses must be unique by identity."
            )
        if type(family_kind) is not InternalFamilyKind:
            raise _certification_error(
                "A producer family must be one exact InternalFamilyKind."
            )
        if not isinstance(execution_role, Enum):
            raise _certification_error(
                "A family producer execution role must be an enum member."
            )
        registered_behavior_id = _require_exact_nonempty_text(
            behavior_id, "behavior ID"
        )
        if registered_behavior_id in _BEHAVIOR_IDS:
            raise _certification_error(
                "The internal-family behavior ID is already registered."
            )
        if (
            not isinstance(subject_type, type)
            or subject_type is object
            or subject_type is type(None)
        ):
            raise _certification_error(
                "A future producer must register one exact reviewed subject type."
            )
        callbacks = (
            source_provenance_extractor,
            source_provenance_verifier,
            subject_binding_extractor,
            subject_provenance_verifier,
        )
        if any(not callable(callback) for callback in callbacks):
            raise _certification_error(
                "Every family-producer provenance and subject callback is required."
            )
        for callback in callbacks:
            _callable_descriptor(callback)

        spec = _ProducerSpec(
            result_type=cast(type[InternalFamilyValidatorResult], result_type),
            success_statuses=success_statuses,
            family_kind=family_kind,
            execution_role=execution_role,
            behavior_id=registered_behavior_id,
            subject_type=subject_type,
            source_provenance_extractor=source_provenance_extractor,
            source_provenance_verifier=source_provenance_verifier,
            subject_binding_extractor=subject_binding_extractor,
            subject_provenance_verifier=subject_provenance_verifier,
        )
        _PRODUCERS[spec.result_type] = spec
        _BEHAVIOR_IDS.add(spec.behavior_id)
        return _ProducerIssuer(spec)


def _seal_internal_family_validator_registry(
    *, expected_result_types: tuple[type[InternalFamilyValidatorResult], ...]
) -> None:
    """Seal the exact reviewed producer inventory; V1 supplies an empty tuple."""
    global _REGISTRY_SEALED

    if type(expected_result_types) is not tuple or any(
        not isinstance(result_type, type)
        or not issubclass(result_type, InternalFamilyValidatorResult)
        for result_type in expected_result_types
    ):
        raise _certification_error(
            "Expected family-producer types must be an exact marker tuple."
        )
    expected = set(expected_result_types)
    if len(expected) != len(expected_result_types):
        raise _certification_error(
            "Expected family-producer types must be unique."
        )

    with _REGISTRY_LOCK:
        if set(_PRODUCERS) != expected:
            raise _certification_error(
                "The reviewed internal-family producer set is incomplete or unexpected."
            )
        _REGISTRY_SEALED = True


def _read_source_provenance(
    origin: InternalFamilyValidatorResult, spec: _ProducerSpec
) -> _SourceProvenanceView:
    try:
        provenance = spec.source_provenance_extractor(origin)
    except Exception as error:
        raise _certification_error(
            "The registered family origin source provenance could not be read."
        ) from error
    if type(provenance) is not _SourceProvenanceView:
        raise _certification_error(
            "A family producer returned malformed source provenance."
        )
    principle_ids = _exact_text_tuple(
        provenance.principle_ids, "principle IDs", require_principle_ids=True
    )
    if type(provenance.source_classes) is not tuple or not provenance.source_classes:
        raise _certification_error(
            "Validated internal family source classes must be a non-empty exact tuple."
        )
    if any(not isinstance(item, Enum) for item in provenance.source_classes):
        raise _certification_error(
            "Validated internal family source classes must be enum members."
        )
    for source_class in provenance.source_classes:
        _enum_descriptor(source_class)
    protected_sources = _exact_text_tuple(
        provenance.protected_sources, "protected sources"
    )
    checked = _SourceProvenanceView(
        principle_ids=principle_ids,
        source_classes=provenance.source_classes,
        protected_sources=protected_sources,
    )
    try:
        verified = spec.source_provenance_verifier(origin, checked)
    except Exception as error:
        raise _certification_error(
            "The registered family origin source provenance failed verification."
        ) from error
    if verified is not True:
        raise _certification_error(
            "The registered family origin source provenance was not verified."
        )
    return checked


def _read_subject_binding(
    origin: InternalFamilyValidatorResult, spec: _ProducerSpec
) -> _SubjectBindingView:
    try:
        binding = spec.subject_binding_extractor(origin)
    except Exception as error:
        raise _certification_error(
            "The registered family origin subject binding could not be read."
        ) from error
    if type(binding) is not _SubjectBindingView:
        raise _certification_error(
            "A family producer returned a malformed subject binding."
        )
    if type(binding.subject) is not spec.subject_type:
        raise _certification_error(
            "The family origin subject does not have the registered exact type."
        )
    components = _exact_text_tuple(
        binding.provenance_components, "subject provenance components"
    )
    if type(binding.nested_proofs) is not tuple:
        raise _certification_error(
            "Nested family proofs must be supplied as an exact tuple."
        )
    for proof in binding.nested_proofs:
        if type(proof) is not CertifiedValidatedInternalFamily:
            raise _certification_error(
                "A nested family proof is not an exact live certificate."
            )
        proof._validated()
    checked = _SubjectBindingView(
        subject=binding.subject,
        provenance_components=components,
        nested_proofs=binding.nested_proofs,
    )
    try:
        verified = spec.subject_provenance_verifier(origin, checked)
    except Exception as error:
        raise _certification_error(
            "The registered family subject provenance failed verification."
        ) from error
    if verified is not True:
        raise _certification_error(
            "The registered family subject provenance was not verified."
        )
    return checked


def _read_origin_view(
    origin: InternalFamilyValidatorResult, spec: _ProducerSpec
) -> _OriginView:
    if type(origin) is not spec.result_type:
        raise _certification_error(
            "Validated family origins require an exact registered result type."
        )
    try:
        status = object.__getattribute__(origin, "status")
        execution_role = object.__getattribute__(origin, "execution_role")
        behavior_id = object.__getattribute__(origin, "behavior_id")
        outcome = object.__getattribute__(origin, "outcome")
        reason = object.__getattribute__(origin, "reason")
    except Exception as error:
        raise _certification_error(
            "The registered validated-family origin is malformed."
        ) from error
    if not any(status is success for success in spec.success_statuses):
        raise _certification_error(
            "The origin status is not a registered family-validation success."
        )
    if execution_role is not spec.execution_role:
        raise _certification_error(
            "The family origin execution role is inconsistent."
        )
    if not _exact_text_equal(behavior_id, spec.behavior_id):
        raise _certification_error("The family origin behavior ID is inconsistent.")
    checked_outcome = _require_exact_nonempty_text(outcome, "outcome")
    checked_reason = _require_exact_nonempty_text(reason, "reason")
    status_value = getattr(status, "value", None)
    if type(status_value) is not str or not _exact_text_equal(
        checked_outcome, status_value
    ):
        raise _certification_error(
            "The family origin status and outcome are inconsistent."
        )
    return _OriginView(
        status=cast(Enum, status),
        family_kind=spec.family_kind,
        execution_role=cast(Enum, execution_role),
        behavior_id=behavior_id,
        outcome=checked_outcome,
        reason=checked_reason,
        source_provenance=_read_source_provenance(origin, spec),
        subject_binding=_read_subject_binding(origin, spec),
    )


def _nested_origin_ids(binding: _SubjectBindingView) -> tuple[str, ...]:
    return tuple(proof.origin_id for proof in binding.nested_proofs)


def _subject_provenance_digest(
    binding: _SubjectBindingView, binding_id: str
) -> str:
    payload = {
        "binding_id": binding_id,
        "subject_identity": id(binding.subject),
        "subject_type": {
            "module": type(binding.subject).__module__,
            "type": type(binding.subject).__qualname__,
        },
        "provenance_components": list(binding.provenance_components),
        "nested_proof_origin_ids": list(_nested_origin_ids(binding)),
    }
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _certified_fields_digest(
    origin: InternalFamilyValidatorResult,
    origin_id: str,
    view: _OriginView,
    subject_digest: str,
    spec: _ProducerSpec,
) -> str:
    payload = {
        "origin_id": origin_id,
        "origin_type": {
            "module": type(origin).__module__,
            "type": type(origin).__qualname__,
        },
        "family_kind": _enum_descriptor(view.family_kind),
        "behavior_id": view.behavior_id,
        "execution_role": _enum_descriptor(view.execution_role),
        "status": _enum_descriptor(view.status),
        "outcome": view.outcome,
        "reason": view.reason,
        "principle_ids": list(view.source_provenance.principle_ids),
        "source_classes": [
            _enum_descriptor(item) for item in view.source_provenance.source_classes
        ],
        "protected_sources": list(view.source_provenance.protected_sources),
        "subject_provenance_digest": subject_digest,
        "callbacks": {
            "source_extractor": _callable_descriptor(
                spec.source_provenance_extractor
            ),
            "source_verifier": _callable_descriptor(spec.source_provenance_verifier),
            "subject_extractor": _callable_descriptor(spec.subject_binding_extractor),
            "subject_verifier": _callable_descriptor(
                spec.subject_provenance_verifier
            ),
        },
    }
    encoded = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _same_identity_tuple(left: tuple[object, ...], right: tuple[object, ...]) -> bool:
    return len(left) == len(right) and all(
        left_item is right_item
        for left_item, right_item in zip(left, right, strict=True)
    )


def _validate_attestation(
    origin: InternalFamilyValidatorResult,
    attestation: _OriginAttestation,
    view: _OriginView,
) -> None:
    if attestation.subject is not view.subject_binding.subject:
        raise _certification_error(
            "The validated-family subject identity changed after issuance."
        )
    if not _same_identity_tuple(
        cast(tuple[object, ...], attestation.nested_proofs),
        cast(tuple[object, ...], view.subject_binding.nested_proofs),
    ):
        raise _certification_error(
            "The validated-family nested-proof identities changed after issuance."
        )
    subject_digest = _subject_provenance_digest(
        view.subject_binding, attestation.binding_id
    )
    if not _exact_text_equal(
        attestation.subject_provenance_digest, subject_digest
    ):
        raise _certification_error(
            "The validated-family subject provenance changed after issuance."
        )
    fields_digest = _certified_fields_digest(
        origin, attestation.origin_id, view, subject_digest, attestation.spec
    )
    if not _exact_text_equal(attestation.certified_fields_digest, fields_digest):
        raise _certification_error(
            "The validated-family certified fields changed after issuance."
        )


def _issue_validated_internal_family(
    issuer: _ProducerIssuer[_TOrigin], origin: _TOrigin
) -> _TOrigin:
    with _REGISTRY_LOCK:
        if not _REGISTRY_SEALED:
            raise _certification_error(
                "Validated internal-family issuance is unavailable before sealing."
            )
        spec = _PRODUCERS.get(type(origin))
        if spec is None or spec is not issuer._spec:
            raise _certification_error(
                "The origin was not issued by its registered family validator."
            )
        view = _read_origin_view(origin, spec)
        origin_key = id(origin)
        existing = _ISSUED.get(origin_key)
        if existing is not None:
            if existing.origin_ref() is not origin or existing.spec is not spec:
                raise _certification_error(
                    "Validated-family origin identity is inconsistent."
                )
            _validate_attestation(origin, existing, view)
            return origin

        origin_id = uuid.uuid4().hex
        binding_id = uuid.uuid4().hex

        def remove_dead_origin(
            dead_reference: weakref.ReferenceType[InternalFamilyValidatorResult],
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
                "A validated-family origin must support weak references."
            ) from error
        subject_digest = _subject_provenance_digest(view.subject_binding, binding_id)
        fields_digest = _certified_fields_digest(
            origin, origin_id, view, subject_digest, spec
        )
        attestation = _OriginAttestation(
            origin_ref=origin_reference,
            origin_id=origin_id,
            binding_id=binding_id,
            spec=spec,
            subject=view.subject_binding.subject,
            nested_proofs=view.subject_binding.nested_proofs,
            subject_provenance_digest=subject_digest,
            certified_fields_digest=fields_digest,
        )
        _ISSUED[origin_key] = attestation
        return origin


def _validated_origin(
    origin: object,
) -> tuple[_OriginAttestation, _OriginView]:
    with _REGISTRY_LOCK:
        if not _REGISTRY_SEALED:
            raise _certification_error(
                "Validated internal-family certification is unavailable before sealing."
            )
        spec = _PRODUCERS.get(type(origin))
        if spec is None or not isinstance(origin, InternalFamilyValidatorResult):
            raise _certification_error(
                "The origin is not an exact registered family-validator result."
            )
        attestation = _ISSUED.get(id(origin))
        if (
            type(attestation) is not _OriginAttestation
            or attestation.origin_ref() is not origin
            or attestation.spec is not spec
        ):
            raise _certification_error(
                "The origin was not issued as a validated internal-family success."
            )
        typed_origin = cast(InternalFamilyValidatorResult, origin)
        view = _read_origin_view(typed_origin, spec)
        _validate_attestation(typed_origin, attestation, view)
        return attestation, view


@dataclass(frozen=True, slots=True, init=False, repr=False, eq=False)
class CertifiedValidatedInternalFamily(Generic[_TOrigin]):
    """Immutable certificate retaining one exact live validated-family origin."""

    _origin: _TOrigin
    _attestation: _OriginAttestation

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError(
            "CertifiedValidatedInternalFamily instances are created only by "
            "certify_validated_internal_family()."
        )

    def _validated(self) -> tuple[_OriginAttestation, _OriginView]:
        if type(self) is not CertifiedValidatedInternalFamily:
            raise _certification_error(
                "Validated internal-family certificate subclasses are not accepted."
            )
        try:
            origin = object.__getattribute__(self, "_origin")
            expected_attestation = object.__getattribute__(self, "_attestation")
        except Exception as error:
            raise _certification_error(
                "The validated internal-family certificate is malformed."
            ) from error
        attestation, view = _validated_origin(origin)
        if attestation is not expected_attestation:
            raise _certification_error(
                "The validated-family attestation does not match its origin."
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
    def family_kind(self) -> InternalFamilyKind:
        _, view = self._validated()
        return view.family_kind

    @property
    def subject(self) -> object:
        _, view = self._validated()
        return view.subject_binding.subject

    @property
    def subject_provenance_components(self) -> tuple[str, ...]:
        _, view = self._validated()
        return view.subject_binding.provenance_components

    @property
    def nested_proofs(
        self,
    ) -> tuple[CertifiedValidatedInternalFamily[InternalFamilyValidatorResult], ...]:
        _, view = self._validated()
        return view.subject_binding.nested_proofs

    @property
    def origin_behavior_id(self) -> str:
        _, view = self._validated()
        return view.behavior_id

    @property
    def origin_principle_ids(self) -> tuple[str, ...]:
        _, view = self._validated()
        return view.source_provenance.principle_ids

    @property
    def origin_source_classes(self) -> tuple[Enum, ...]:
        _, view = self._validated()
        return view.source_provenance.source_classes

    @property
    def origin_protected_sources(self) -> tuple[str, ...]:
        _, view = self._validated()
        return view.source_provenance.protected_sources

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

    def __repr__(self) -> str:
        return (
            "CertifiedValidatedInternalFamily("
            f"origin_id={self.origin_id!r}, "
            f"family_kind={self.family_kind!r}, "
            f"origin_behavior_id={self.origin_behavior_id!r})"
        )

    def __copy__(self) -> CertifiedValidatedInternalFamily[_TOrigin]:
        self._validated()
        return self

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> CertifiedValidatedInternalFamily[_TOrigin]:
        self._validated()
        memo[id(self)] = self
        return self

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Validated internal-family certificates cannot be pickled.")


def _new_certificate(
    origin: _TOrigin, attestation: _OriginAttestation
) -> CertifiedValidatedInternalFamily[_TOrigin]:
    certificate = object.__new__(CertifiedValidatedInternalFamily)
    object.__setattr__(certificate, "_origin", origin)
    object.__setattr__(certificate, "_attestation", attestation)
    return cast(CertifiedValidatedInternalFamily[_TOrigin], certificate)


def certify_validated_internal_family(
    origin: _TOrigin,
) -> CertifiedValidatedInternalFamily[_TOrigin]:
    """Certify one genuine future producer success; V1 rejects every input."""
    attestation, _ = _validated_origin(origin)
    certificate = _new_certificate(origin, attestation)
    certificate._validated()
    return certificate


__all__ = [
    "CertifiedValidatedInternalFamily",
    "InternalFamilyKind",
    "InternalFamilyValidatorResult",
    "ValidatedInternalFamilyCertificationError",
    "certify_validated_internal_family",
]
