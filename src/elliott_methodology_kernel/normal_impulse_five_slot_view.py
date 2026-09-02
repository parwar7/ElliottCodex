"""Non-authoritative five-position view over one ordered child binding.

The view records only that a caller has supplied one existing binding with
exactly five ordered child subjects for later normal-impulse validation.  Its
positions are proposed ordinal slots, not validated Elliott waves.  It does
not establish pattern, family, completion, structural validity, or any
certification authority.
"""

from __future__ import annotations

from dataclasses import dataclass

from .subject_binding import AnalyzedWaveSubject, OrderedChildBinding


class NormalImpulseFiveSlotCardinalityError(ValueError):
    """Raised when an ordered binding cannot form an exact five-slot view."""


class _SealedFiveSlotViewType(type):
    def __new__(
        mcls: type,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
        **kwargs: object,
    ) -> type:
        if any(isinstance(base, mcls) for base in bases):
            raise TypeError(
                "Normal-impulse five-slot candidate views cannot be subclassed."
            )
        return super().__new__(mcls, name, bases, namespace, **kwargs)


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class NormalImpulseFiveSlotCandidateView(metaclass=_SealedFiveSlotViewType):
    """One immutable, non-authoritative view of five proposed positions."""

    binding: OrderedChildBinding

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "Normal-impulse five-slot candidate views cannot be subclassed."
        )

    def __post_init__(self) -> None:
        if type(self.binding) is not OrderedChildBinding:
            raise TypeError("binding must be one exact OrderedChildBinding.")
        if len(self.binding.ordered_children) != 5:
            raise NormalImpulseFiveSlotCardinalityError(
                "A normal-impulse five-slot candidate view requires exactly "
                "five ordered child subjects."
            )

    @property
    def position_1(self) -> AnalyzedWaveSubject:
        """Return caller-proposed position 1 without asserting wave validity."""
        return self.binding.ordered_children[0]

    @property
    def position_2(self) -> AnalyzedWaveSubject:
        """Return caller-proposed position 2 without asserting wave validity."""
        return self.binding.ordered_children[1]

    @property
    def position_3(self) -> AnalyzedWaveSubject:
        """Return caller-proposed position 3 without asserting wave validity."""
        return self.binding.ordered_children[2]

    @property
    def position_4(self) -> AnalyzedWaveSubject:
        """Return caller-proposed position 4 without asserting wave validity."""
        return self.binding.ordered_children[3]

    @property
    def position_5(self) -> AnalyzedWaveSubject:
        """Return caller-proposed position 5 without asserting wave validity."""
        return self.binding.ordered_children[4]

    def __copy__(self) -> NormalImpulseFiveSlotCandidateView:
        return self

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> NormalImpulseFiveSlotCandidateView:
        memo[id(self)] = self
        return self

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError(
            "Normal-impulse five-slot candidate views cannot be pickled."
        )


__all__ = [
    "NormalImpulseFiveSlotCandidateView",
    "NormalImpulseFiveSlotCardinalityError",
]
