"""Non-authoritative analyzed-subject and ordered-child identity inputs.

These objects record caller-established identity, provenance references, and
tuple order only.  They do not establish parentage, Elliott positions,
cardinality, degree, completion, validity, family membership, or certification
authority.  Exact live object identity is available to a future reviewed
validator, but construction of either type is only untrusted analysis input.
"""

from __future__ import annotations

from dataclasses import dataclass


def _require_opaque_text(value: object, field_name: str) -> None:
    if type(value) is not str or value.strip() == "":
        raise ValueError(f"{field_name} must be an exact non-blank string.")


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class AnalyzedWaveSubject:
    """One untrusted analyzed-subject identity with opaque audit provenance."""

    subject_id: str
    observation_provenance_ref: str

    def __post_init__(self) -> None:
        _require_opaque_text(self.subject_id, "subject_id")
        _require_opaque_text(
            self.observation_provenance_ref,
            "observation_provenance_ref",
        )

    def __copy__(self) -> AnalyzedWaveSubject:
        return self

    def __deepcopy__(self, memo: dict[int, object]) -> AnalyzedWaveSubject:
        memo[id(self)] = self
        return self

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Analyzed wave subjects cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class OrderedChildBinding:
    """One immutable, parent-specific, non-authoritative child ordering."""

    binding_id: str
    parent_subject: AnalyzedWaveSubject
    ordered_children: tuple[AnalyzedWaveSubject, ...]

    def __post_init__(self) -> None:
        _require_opaque_text(self.binding_id, "binding_id")
        if type(self.parent_subject) is not AnalyzedWaveSubject:
            raise TypeError(
                "parent_subject must be one exact AnalyzedWaveSubject."
            )
        if type(self.ordered_children) is not tuple:
            raise TypeError("ordered_children must be one exact tuple.")

        seen_objects = {id(self.parent_subject)}
        seen_subject_ids = {self.parent_subject.subject_id}
        for child in self.ordered_children:
            if type(child) is not AnalyzedWaveSubject:
                raise TypeError(
                    "Every ordered child must be one exact AnalyzedWaveSubject."
                )
            if id(child) in seen_objects:
                raise ValueError(
                    "A parent or child object cannot occupy more than one "
                    "position in one binding."
                )
            if child.subject_id in seen_subject_ids:
                raise ValueError(
                    "Parent and child subject IDs must be unique within one "
                    "binding."
                )
            seen_objects.add(id(child))
            seen_subject_ids.add(child.subject_id)

    def __copy__(self) -> OrderedChildBinding:
        return self

    def __deepcopy__(self, memo: dict[int, object]) -> OrderedChildBinding:
        memo[id(self)] = self
        return self

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Ordered child bindings cannot be pickled.")


__all__ = [
    "AnalyzedWaveSubject",
    "OrderedChildBinding",
]
