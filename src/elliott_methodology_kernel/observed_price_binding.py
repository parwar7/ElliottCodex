"""Non-authoritative observed-price operands bound to one analyzed subject.

These objects transport caller-designated proposed endpoint observations only.
They do not establish wave endpoints, chronology, direction, pivots, extremes,
completion, movement size, pattern validity, or certification authority.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

from .subject_binding import AnalyzedWaveSubject


class _SealedObservedPriceBindingType(type):
    def __new__(
        mcls: type,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
        **kwargs: object,
    ) -> type:
        if any(isinstance(base, mcls) for base in bases):
            raise TypeError(
                "Subject-bound observed-price contracts cannot be subclassed."
            )
        return super().__new__(mcls, name, bases, namespace, **kwargs)


def _require_opaque_text(value: object, field_name: str) -> None:
    if type(value) is not str or value.strip() == "":
        raise ValueError(f"{field_name} must be an exact non-blank string.")


def _require_finite_price(value: object) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError("price must be a finite int or float without coercion.")
    try:
        finite = math.isfinite(value)
    except OverflowError as error:
        raise ValueError("price must fit the approved finite numeric domain.") from error
    if not finite:
        raise ValueError("price must be finite.")


def _reject_reinitialization(
    instance: object,
    field_name: str,
    contract_name: str,
) -> None:
    try:
        object.__getattribute__(instance, field_name)
    except AttributeError:
        return
    raise TypeError(f"{contract_name} cannot be reinitialized.")


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True, init=False)
class SubjectBoundObservedPriceObservation(
    metaclass=_SealedObservedPriceBindingType
):
    """One exact subject with one untrusted observed-price transport value."""

    subject: AnalyzedWaveSubject
    price: int | float
    observation_provenance_ref: str

    def __init__(
        self,
        subject: AnalyzedWaveSubject,
        price: int | float,
        observation_provenance_ref: str,
    ) -> None:
        _reject_reinitialization(
            self,
            "subject",
            "Subject-bound observed-price observations",
        )
        if type(subject) is not AnalyzedWaveSubject:
            raise TypeError("subject must be one exact AnalyzedWaveSubject.")
        _require_finite_price(price)
        _require_opaque_text(
            observation_provenance_ref,
            "observation_provenance_ref",
        )
        object.__setattr__(self, "subject", subject)
        object.__setattr__(self, "price", price)
        object.__setattr__(
            self,
            "observation_provenance_ref",
            observation_provenance_ref,
        )

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "Subject-bound observed-price observations cannot be subclassed."
        )

    def __copy__(self) -> SubjectBoundObservedPriceObservation:
        return self

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> SubjectBoundObservedPriceObservation:
        memo[id(self)] = self
        return self

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError(
            "Subject-bound observed-price observations cannot be pickled."
        )


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True, init=False)
class SubjectBoundObservedPriceEndpointPair(
    metaclass=_SealedObservedPriceBindingType
):
    """Two exact caller-designated operand roles for one exact subject."""

    proposed_start: SubjectBoundObservedPriceObservation
    proposed_end: SubjectBoundObservedPriceObservation

    def __init__(
        self,
        proposed_start: SubjectBoundObservedPriceObservation,
        proposed_end: SubjectBoundObservedPriceObservation,
    ) -> None:
        _reject_reinitialization(
            self,
            "proposed_start",
            "Subject-bound observed-price endpoint pairs",
        )
        if type(proposed_start) is not SubjectBoundObservedPriceObservation:
            raise TypeError(
                "proposed_start must be one exact observed-price observation."
            )
        if type(proposed_end) is not SubjectBoundObservedPriceObservation:
            raise TypeError(
                "proposed_end must be one exact observed-price observation."
            )
        if proposed_start.subject is not proposed_end.subject:
            raise ValueError(
                "Both endpoint observations must reference the same exact subject."
            )
        object.__setattr__(self, "proposed_start", proposed_start)
        object.__setattr__(self, "proposed_end", proposed_end)

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "Subject-bound observed-price endpoint pairs cannot be subclassed."
        )

    @property
    def subject(self) -> AnalyzedWaveSubject:
        """Return the exact common subject without adding endpoint meaning."""
        return self.proposed_start.subject

    def __copy__(self) -> SubjectBoundObservedPriceEndpointPair:
        return self

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> SubjectBoundObservedPriceEndpointPair:
        memo[id(self)] = self
        return self

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError(
            "Subject-bound observed-price endpoint pairs cannot be pickled."
        )


__all__ = [
    "SubjectBoundObservedPriceObservation",
    "SubjectBoundObservedPriceEndpointPair",
]
