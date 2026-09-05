"""One-sided P005 sufficiency; source rule plus approved measurement convention.

No result from this module asserts invalidity, completion, or family validity.
Fractions describe exact represented inputs, not inferred decimal precision.
"""

from dataclasses import dataclass, fields
from enum import StrEnum
from fractions import Fraction
import math
import weakref

from .candidate_analysis_envelope import _snapshot, _snapshot_matches
from .contracts import NormalizedMarketObservations
from .normal_impulse_five_slot_view import NormalImpulseFiveSlotCandidateView
from .observed_price_binding import SubjectBoundObservedPriceEndpointPair, SubjectBoundObservedPriceObservation
from .p004 import ImpulseDirection
from .subject_binding import OrderedChildBinding, AnalyzedWaveSubject

P005_BEHAVIOR_ID = "P005_NORMAL_IMPULSE_PERCENTAGE_SUFFICIENCY"
POLICY_SHA256 = "605a5dc2f4819816ead3c81aa945579eb4f439e139bf50715b93a30d15adc018"
PROTECTED_SOURCES = (
    "docs/elliott/SOURCE_EVIDENCE_MAP.json#P005",
    "docs/elliott/SOURCE_POLICY.md#P005-approved-measurement-contract",
    "Sources_LOCKED/book_frost_prechter/Elliott_Wave_Principle_Frost_Prechter_20th_Anniversary_1998.pdf#page=31",
)
PROJECT_CONVENTION = "USER_APPROVED_PROJECT_CONVENTIONS"


class P005PercentageSufficiencyError(ValueError):
    """Malformed or mutated snapshot: no result may be relied upon."""


class P005PercentageSufficiencyStatus(StrEnum):
    SUFFICIENT_CONDITION_ESTABLISHED = "SUFFICIENT_CONDITION_ESTABLISHED"
    UNRESOLVED = "UNRESOLVED"


class _Sealed(type):
    def __new__(mcls, name, bases, namespace, **kwargs):
        if any(isinstance(base, mcls) for base in bases):
            raise TypeError("P005 contracts cannot be subclassed.")
        return super().__new__(mcls, name, bases, namespace, **kwargs)


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class P005PercentageSufficiencyInput(metaclass=_Sealed):
    five_slot_view: NormalImpulseFiveSlotCandidateView
    direction: ImpulseDirection
    # Exact role 1, 3, 5 pairs, in that order. None is missing evidence.
    endpoint_pairs: tuple[SubjectBoundObservedPriceEndpointPair | None, ...]
    observation_snapshot: NormalizedMarketObservations | None
    # Six endpoint eligibility facts: True only means nondeveloping geometry.
    endpoint_eligibility: tuple[bool | None, ...]
    provenance_refs: tuple[str, ...]
    endpoint_identity_refs: tuple[object, ...]

    def __post_init__(self):
        if self in _INPUTS:
            raise P005PercentageSufficiencyError("Input cannot be reinitialized.")
        if type(self.five_slot_view) is not NormalImpulseFiveSlotCandidateView:
            raise P005PercentageSufficiencyError("Exact five-slot view required.")
        binding = self.five_slot_view.binding
        if (type(binding) is not OrderedChildBinding
            or type(binding.parent_subject) is not AnalyzedWaveSubject
            or type(binding.ordered_children) is not tuple
            or len(binding.ordered_children) != 5
            or any(type(v) is not AnalyzedWaveSubject for v in binding.ordered_children)
            or len({id(v) for v in binding.ordered_children}) != 5):
            raise P005PercentageSufficiencyError("Exact five-child binding required.")
        if type(self.endpoint_pairs) is not tuple or len(self.endpoint_pairs) != 3:
            raise P005PercentageSufficiencyError("Exactly three role pairs required.")
        for index, pair in zip((0, 2, 4), self.endpoint_pairs, strict=True):
            if pair is not None and (
                type(pair) is not SubjectBoundObservedPriceEndpointPair
                or type(pair.proposed_start) is not SubjectBoundObservedPriceObservation
                or type(pair.proposed_end) is not SubjectBoundObservedPriceObservation
                or pair.proposed_start.subject is not binding.ordered_children[index]
                or pair.proposed_end.subject is not binding.ordered_children[index]
            ):
                raise P005PercentageSufficiencyError("Foreign or malformed role pair.")
            if pair is not None and any(type(v.observation_provenance_ref) is not str or not v.observation_provenance_ref.strip()
                                        for v in (pair.proposed_start, pair.proposed_end)):
                raise P005PercentageSufficiencyError("Endpoint provenance is missing or malformed.")
        if self.observation_snapshot is not None and type(self.observation_snapshot) is not NormalizedMarketObservations:
            raise P005PercentageSufficiencyError("Exact observation snapshot required.")
        if type(self.endpoint_eligibility) is not tuple or len(self.endpoint_eligibility) != 6 or any(
            value is not None and type(value) is not bool for value in self.endpoint_eligibility
        ):
            raise P005PercentageSufficiencyError("Six exact eligibility facts required.")
        if type(self.provenance_refs) is not tuple or any(type(v) is not str or not v.strip() for v in self.provenance_refs):
            raise P005PercentageSufficiencyError("Exact provenance tuple required.")
        if type(self.endpoint_identity_refs) is not tuple or len(self.endpoint_identity_refs) != 6 or any(v is None for v in self.endpoint_identity_refs) or len({id(v) for v in self.endpoint_identity_refs}) != 6:
            raise P005PercentageSufficiencyError("Six distinct source endpoint identities required.")
        # Stored externally once. Validation never refreshes this identity evidence.
        _INPUTS[self] = tuple(_snapshot(getattr(self, f.name)) for f in fields(self))

    def validated(self):
        expected = _INPUTS.get(self) if type(self) is P005PercentageSufficiencyInput else None
        if expected is None or not all(
            _snapshot_matches(getattr(self, f.name), old)
            for f, old in zip(fields(self), expected, strict=True)
        ):
            raise P005PercentageSufficiencyError("P005 input is unissued or mutated.")
        return self

    def __reduce_ex__(self, protocol):
        raise TypeError("P005 snapshot inputs cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False, init=False, weakref_slot=True)
class P005PercentageSufficiencyResult(metaclass=_Sealed):
    input_snapshot: P005PercentageSufficiencyInput
    status: P005PercentageSufficiencyStatus
    reason: str
    percentage_movements: tuple[Fraction, ...]
    behavior_id: str
    source_principle_id: str
    source_class: str
    measurement_class: str
    protected_sources: tuple[str, ...]
    fatal_to_candidate: bool
    family_validity_authority: bool
    completion_authority: bool

    def __init__(self, *args, **kwargs):
        raise TypeError("P005 results are issued only by the Kernel.")

    def validated(self):
        expected = _RESULTS.get(self) if type(self) is P005PercentageSufficiencyResult else None
        if expected is None or any(
            getattr(self, f.name) is not old for f, old in zip(fields(self), expected, strict=True)
        ):
            raise P005PercentageSufficiencyError("P005 result is unissued or mutated.")
        self.input_snapshot.validated()
        return self

    def __reduce_ex__(self, protocol):
        raise TypeError("P005 results cannot be pickled.")


_INPUTS = weakref.WeakKeyDictionary()
_RESULTS = weakref.WeakKeyDictionary()


def _issue(request, status, reason, movements=()):
    values = (request, status, reason, movements, P005_BEHAVIOR_ID, "P005",
              "SOURCE_RULE", PROJECT_CONVENTION, PROTECTED_SOURCES, False, False, False)
    result = object.__new__(P005PercentageSufficiencyResult)
    for f, value in zip(fields(result), values, strict=True):
        object.__setattr__(result, f.name, value)
    _RESULTS[result] = values
    return result.validated()


def _evaluate_p005_percentage_sufficiency(request):
    if type(request) is not P005PercentageSufficiencyInput:
        raise P005PercentageSufficiencyError("One exact P005 input required.")
    request.validated()
    unresolved = P005PercentageSufficiencyStatus.UNRESOLVED
    if request.observation_snapshot is None or not request.provenance_refs or any(p is None for p in request.endpoint_pairs):
        return _issue(request, unresolved, "MISSING_ENDPOINT_OR_OBSERVATION_PROVENANCE")
    if any(v is None for v in request.endpoint_eligibility):
        return _issue(request, unresolved, "MISSING_ENDPOINT_ELIGIBILITY")
    if any(v is False for v in request.endpoint_eligibility):
        return _issue(request, unresolved, "DEVELOPING_REQUIRED_ENDPOINT")
    if type(request.direction) is not ImpulseDirection or request.direction not in (ImpulseDirection.UP, ImpulseDirection.DOWN):
        return _issue(request, unresolved, "MISSING_EXPLICIT_SUPPORTED_DIRECTION")
    movements = []
    for pair in request.endpoint_pairs:
        start, end = pair.proposed_start.price, pair.proposed_end.price
        if any(type(v) not in (int, float) or (type(v) is float and not math.isfinite(v)) or v <= 0 for v in (start, end)):
            return _issue(request, unresolved, "FINITE_STRICTLY_POSITIVE_PRICES_REQUIRED")
        # Convert BEFORE subtraction/division. Fraction(float) uses as_integer_ratio.
        start, end = Fraction(start), Fraction(end)
        difference = end - start
        if difference == 0 or (request.direction is ImpulseDirection.UP and difference < 0) or (request.direction is ImpulseDirection.DOWN and difference > 0):
            return _issue(request, unresolved, "ZERO_OR_OPPOSING_ROLE_MOVEMENT")
        movements.append(100 * abs(difference) / start)
    r1, r3, r5 = movements
    if r3 > r1 or r3 > r5:
        return _issue(request, P005PercentageSufficiencyStatus.SUFFICIENT_CONDITION_ESTABLISHED,
                      "BOOK_PERCENTAGE_SUFFICIENT_CONDITION_ONLY_NOT_FULL_P005_OR_FAMILY_VALIDATION", tuple(movements))
    return _issue(request, unresolved, "SUFFICIENCY_NOT_ESTABLISHED_NO_NEGATIVE_INFERENCE", tuple(movements))
