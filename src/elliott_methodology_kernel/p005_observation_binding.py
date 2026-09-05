"""PROJECT_ANALYSIS_INFRASTRUCTURE: verified P005 observation transport.

Rechecks the existing bounded local-extrema geometry's factual window evidence.
Window sizes and FIRST/LAST tie selection are caller geometry parameters, not
Elliott methodology. Nondeveloping geometry is never Elliott completion.
"""
from dataclasses import dataclass, fields
from enum import StrEnum
from datetime import datetime, timezone
import math
import weakref

from .candidate_analysis_envelope import _snapshot, _snapshot_matches
from .contracts import NormalizedMarketObservations, Bar
from .models import BarProvenance, DataProvenance, DataQualityReport, SymbolIdentity, Timeframe
from .normal_impulse_five_slot_view import NormalImpulseFiveSlotCandidateView
from .subject_binding import OrderedChildBinding, AnalyzedWaveSubject


class P005ObservationBindingError(ValueError):
    """Foreign, fabricated, unsupported, or mutated observation evidence."""


class _Sealed(type):
    def __new__(mcls, name, bases, namespace, **kwargs):
        if any(isinstance(base, mcls) for base in bases):
            raise TypeError("P005 evidence contracts cannot be subclassed.")
        return super().__new__(mcls, name, bases, namespace, **kwargs)


class P005PriceBasis(StrEnum):
    HIGH = "high"
    LOW = "low"


@dataclass(frozen=True, slots=True, eq=False)
class P005GeometryWindow(metaclass=_Sealed):
    left_window_bars: int
    right_window_bars: int
    equal_extreme_policy: str
    scoped_bars: tuple[Bar, ...] | None = None
    # Optional opaque provenance is pinned, NEVER used to derive price/state.
    provenance_ref: object | None = None


@dataclass(frozen=True, slots=True, eq=False, init=False, weakref_slot=True)
class P005ObservationBinding(metaclass=_Sealed):
    five_slot_view: NormalImpulseFiveSlotCandidateView
    observation_snapshot: NormalizedMarketObservations
    endpoint_bars: tuple[Bar, ...]
    price_fields: tuple[P005PriceBasis, ...]
    geometry_windows: tuple[P005GeometryWindow | None, ...]
    endpoint_prices: tuple[int | float, ...]
    endpoint_eligibility: tuple[bool | None, ...]

    def __init__(self, *args, **kwargs):
        raise TypeError("Use bind_p005_observations; evidence is verified, not declared.")

    def validated(self):
        old = _ISSUED.get(self) if type(self) is P005ObservationBinding else None
        if old is None or not all(_snapshot_matches(getattr(self, f.name), value)
                                  for f, value in zip(fields(self), old, strict=True)):
            raise P005ObservationBindingError("Observation binding is unissued or mutated.")
        return self

    def __reduce_ex__(self, protocol):
        raise TypeError("Observation binding issuance cannot be serialized.")


_ISSUED = weakref.WeakKeyDictionary()
_VIEW_EVIDENCE = weakref.WeakKeyDictionary()


def _fail(message):
    raise P005ObservationBindingError(message)


def _number(value):
    return type(value) in (int, float) and (type(value) is int or math.isfinite(value))


def _snapshot_bars(snapshot):
    if type(snapshot) is not NormalizedMarketObservations:
        _fail("Exact normalized observation snapshot required.")
    if type(snapshot.provenance) is not DataProvenance or type(snapshot.quality) is not DataQualityReport:
        _fail("Exact snapshot provenance and quality required.")
    if type(snapshot.symbol) is not SymbolIdentity or type(snapshot.timeframe) is not Timeframe or type(snapshot.provenance.source_resolution) is not Timeframe:
        _fail("Exact market identity and observation-resolution contracts required.")
    if any(type(v) is not str or not v.strip() for v in (snapshot.provenance.source_type, snapshot.provenance.source_identifier)):
        _fail("Snapshot source identity is missing or malformed.")
    if type(snapshot.provenance.source_sha256) is not str or not snapshot.provenance.source_sha256:
        _fail("Snapshot source provenance is missing.")
    bars = snapshot.bars
    if type(bars) is not tuple or not bars:
        _fail("Nonempty exact bar tuple required.")
    previous = None
    for bar in bars:
        if type(bar) is not Bar or type(bar.provenance) is not BarProvenance:
            _fail("Exact bars and bar provenance required.")
        if type(bar.provenance.source_record_index) is not int or bar.provenance.source_record_index < 0 or type(bar.provenance.source_timestamp) is not str or not bar.provenance.source_timestamp.strip():
            _fail("Malformed source-record provenance.")
        if type(bar.timestamp_utc) is not datetime or bar.timestamp_utc.tzinfo is None or bar.timestamp_utc.utcoffset() != timezone.utc.utcoffset(bar.timestamp_utc):
            _fail("UTC bar timestamps required.")
        if previous is not None and bar.timestamp_utc <= previous:
            _fail("Snapshot bars must be strictly chronological.")
        previous = bar.timestamp_utc
        if not all(_number(v) for v in (bar.open, bar.high, bar.low, bar.close)) or bar.high < max(bar.open, bar.low, bar.close) or bar.low > min(bar.open, bar.high, bar.close):
            _fail("Malformed OHLC observation.")
    return bars


def _geometry_eligibility(bar, basis, window, bars, index_by_identity):
    if window is None:
        return None  # Genuine missing geometry evidence, not a positive flag.
    if type(window) is not P005GeometryWindow:
        _fail("Exact geometry window evidence required.")
    for value in (window.left_window_bars, window.right_window_bars):
        if type(value) is not int or not 1 <= value <= 10000:
            _fail("Geometry window exceeds existing operational limits.")
    if type(window.equal_extreme_policy) is not str or window.equal_extreme_policy not in ("FIRST", "LAST"):
        _fail("Explicit FIRST/LAST geometry tie policy required.")
    scope = bars if window.scoped_bars is None else window.scoped_bars
    if type(scope) is not tuple or not scope:
        _fail("Exact nonempty geometry scope required.")
    positions = []
    for scoped_bar in scope:
        position = index_by_identity.get(id(scoped_bar))
        if position is None or bars[position] is not scoped_bar:
            _fail("Geometry scope contains a foreign observation.")
        positions.append(position)
    if any(b <= a for a, b in zip(positions, positions[1:])):
        _fail("Geometry scope order or identity duplicated.")
    index = next((i for i, value in enumerate(scope) if value is bar), None)
    if index is None or index < window.left_window_bars:
        _fail("Endpoint lacks its exact left-window observations.")
    full_right = index + window.right_window_bars < len(scope)
    end = index + window.right_window_bars + 1 if full_right else len(scope)
    observed = scope[index - window.left_window_bars:end]
    local_index = window.left_window_bars
    def selected(field, high):
        values = [getattr(v, field) for v in observed]
        extreme = max(values) if high else min(values)
        matches = [i for i, value in enumerate(values) if value == extreme]
        chosen = matches[0] if window.equal_extreme_policy == "FIRST" else matches[-1]
        return chosen == local_index
    high_selected, low_selected = selected("high", True), selected("low", False)
    if high_selected == low_selected or (basis is P005PriceBasis.HIGH) != high_selected:
        _fail("Claimed endpoint basis is not supported by its geometry observations.")
    return full_right


def bind_p005_observations(five_slot_view, observation_snapshot, endpoint_bars, price_fields, geometry_windows):
    """Resolve prices and eligibility from real bars; never accept supplied prices/flags.

    The six chronological boundaries define the five caller-proposed slots.
    This records a hypothesis declaration, never orthodox endpoint authority.
    """
    if type(five_slot_view) is not NormalImpulseFiveSlotCandidateView:
        _fail("Exact five-slot view required.")
    binding = five_slot_view.binding
    if (type(binding) is not OrderedChildBinding or type(binding.parent_subject) is not AnalyzedWaveSubject
        or type(binding.ordered_children) is not tuple or len(binding.ordered_children) != 5
        or any(type(v) is not AnalyzedWaveSubject for v in binding.ordered_children)
        or len({id(v) for v in binding.ordered_children}) != 5):
        _fail("Exact five-slot subject ancestry required.")
    bars = _snapshot_bars(observation_snapshot)
    index_by_identity = {id(bar): i for i, bar in enumerate(bars)}
    if any(type(v) is not tuple or len(v) != 6 for v in (endpoint_bars, price_fields, geometry_windows)):
        _fail("Exactly six ordered endpoint observations, bases and windows required.")
    positions = []
    for bar, basis in zip(endpoint_bars, price_fields, strict=True):
        i = index_by_identity.get(id(bar))
        if i is None or bars[i] is not bar or type(basis) is not P005PriceBasis:
            _fail("Foreign observation or unsupported explicit price basis.")
        positions.append(i)
    if any(b <= a for a, b in zip(positions, positions[1:])):
        _fail("Five-slot endpoint chronology or uniqueness violated.")
    eligibility = tuple(_geometry_eligibility(bar, basis, window, bars, index_by_identity)
                        for bar, basis, window in zip(endpoint_bars, price_fields, geometry_windows, strict=True))
    prices = tuple(getattr(bar, basis.value) for bar, basis in zip(endpoint_bars, price_fields, strict=True))
    ancestry = (binding, observation_snapshot, endpoint_bars, price_fields, geometry_windows)
    prior = _VIEW_EVIDENCE.get(five_slot_view)
    if prior is not None and not all(_snapshot_matches(value, old) for value, old in zip(ancestry, prior, strict=True)):
        _fail("Issued view cannot be rebound or refreshed from altered evidence.")
    values = (five_slot_view, observation_snapshot, endpoint_bars, price_fields, geometry_windows, prices, eligibility)
    result = object.__new__(P005ObservationBinding)
    for f, value in zip(fields(result), values, strict=True):
        object.__setattr__(result, f.name, value)
    _ISSUED[result] = tuple(_snapshot(value) for value in values)
    if prior is None:
        _VIEW_EVIDENCE[five_slot_view] = tuple(_snapshot(value) for value in ancestry)
    return result.validated()
