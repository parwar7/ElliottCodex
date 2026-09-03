"""Exact multi-timeframe observation transport for one recursive candidate.

This is PROJECT_ANALYSIS_INFRASTRUCTURE governed by PROJECT_OPERATIONAL_POLICY.
Associations are caller-supplied observation associations.  Chart resolution
is never Elliott degree, and this module performs no methodology evaluation,
data fetching, resampling, bar interpretation, or recursive discovery.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import StrEnum

from .models import (
    Bar,
    BarProvenance,
    DataProvenance,
    DataQualityReport,
    MarketType,
    MissingBarInterval,
    NormalizedMarketObservations,
    SymbolIdentity,
    Timeframe,
)
from .recursive_candidate_composition import RecursiveCandidateCompositionResult
from .subject_binding import AnalyzedWaveSubject


ARTIFACT_CLASSIFICATION = "PROJECT_ANALYSIS_INFRASTRUCTURE"
ASSOCIATION_CLASSIFICATION = "CALLER_SUPPLIED_OBSERVATION_ASSOCIATION"
WORKFLOW_POLICY_CLASSIFICATION = "PROJECT_OPERATIONAL_POLICY"
TIMEFRAME_IS_NOT_DEGREE = True


class ObservationAssociationRole(StrEnum):
    REFERENCE_VIEW = "REFERENCE_VIEW"
    ADDITIONAL_VIEW = "ADDITIONAL_VIEW"
    FINER_RESOLUTION_VIEW = "FINER_RESOLUTION_VIEW"


class ObservationResolutionRelation(StrEnum):
    COARSER_THAN = "COARSER_THAN"
    FINER_THAN = "FINER_THAN"
    SAME_RESOLUTION = "SAME_RESOLUTION"


class ObservationTransportDiagnosticState(StrEnum):
    SUBJECT_ATTACHED = "SUBJECT_ATTACHED"
    SUBJECT_NO_OBSERVATIONS = "SUBJECT_NO_OBSERVATIONS"
    MULTIPLE_RESOLUTIONS_ATTACHED = "MULTIPLE_RESOLUTIONS_ATTACHED"
    FINER_RESOLUTION_AVAILABLE = "FINER_RESOLUTION_AVAILABLE"
    COARSER_RESOLUTION_AVAILABLE = "COARSER_RESOLUTION_AVAILABLE"


class MultiTimeframeObservationTransportError(ValueError):
    """Raised when exact observation transport fails closed."""


class _SealedTransportType(type):
    def __new__(
        mcls: type,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
        **kwargs: object,
    ) -> type:
        if any(isinstance(base, mcls) for base in bases):
            raise TypeError("Multi-timeframe transport types cannot be subclassed.")
        return super().__new__(mcls, name, bases, namespace, **kwargs)


def _require_text(value: object, name: str) -> str:
    if type(value) is not str or value.strip() == "":
        raise MultiTimeframeObservationTransportError(
            f"{name} must be an exact non-blank string."
        )
    return value


def _require_optional_text(value: object, name: str) -> str | None:
    if value is not None:
        _require_text(value, name)
    return value


def _require_provenance(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or any(
        type(item) is not str or item.strip() == "" for item in value
    ):
        raise MultiTimeframeObservationTransportError(
            "provenance_refs must be one exact tuple of non-blank strings."
        )
    return value


def _validate_symbol(value: object) -> SymbolIdentity:
    if type(value) is not SymbolIdentity:
        raise MultiTimeframeObservationTransportError(
            "symbol must be one exact SymbolIdentity."
        )
    if type(value.symbol) is not str or value.symbol.strip() == "":
        raise MultiTimeframeObservationTransportError("Symbol identity is malformed.")
    if type(value.market_type) is not MarketType:
        raise MultiTimeframeObservationTransportError(
            "Symbol market_type must retain the exact MarketType."
        )
    _require_optional_text(value.exchange, "symbol.exchange")
    _require_optional_text(value.provider_symbol, "symbol.provider_symbol")
    return value


def _symbol_key(value: SymbolIdentity) -> tuple[object, ...]:
    checked = _validate_symbol(value)
    return (
        checked.symbol,
        checked.market_type,
        checked.exchange,
        checked.provider_symbol,
    )


def _validate_timeframe(value: object) -> Timeframe:
    if type(value) is not Timeframe:
        raise MultiTimeframeObservationTransportError(
            "timeframe must be one exact Timeframe."
        )
    if type(value.label) is not str or value.label.strip() == "":
        raise MultiTimeframeObservationTransportError("Timeframe label is malformed.")
    if type(value.resolution_seconds) is not int or value.resolution_seconds <= 0:
        raise MultiTimeframeObservationTransportError(
            "Timeframe resolution_seconds must be one exact positive integer."
        )
    return value


def compare_observation_resolutions(
    left: Timeframe,
    right: Timeframe,
) -> ObservationResolutionRelation:
    """Compare chart sampling resolution only; this carries no degree meaning."""
    left_checked = _validate_timeframe(left)
    right_checked = _validate_timeframe(right)
    if left_checked.resolution_seconds > right_checked.resolution_seconds:
        return ObservationResolutionRelation.COARSER_THAN
    if left_checked.resolution_seconds < right_checked.resolution_seconds:
        return ObservationResolutionRelation.FINER_THAN
    return ObservationResolutionRelation.SAME_RESOLUTION


def _observation_snapshot(
    value: NormalizedMarketObservations,
) -> tuple[object, ...]:
    if type(value) is not NormalizedMarketObservations:
        raise MultiTimeframeObservationTransportError(
            "Each observation set must have the exact NormalizedMarketObservations type."
        )
    symbol = _validate_symbol(value.symbol)
    timeframe = _validate_timeframe(value.timeframe)
    if type(value.bars) is not tuple:
        raise MultiTimeframeObservationTransportError(
            "Normalized bars must retain one exact tuple."
        )
    bar_snapshots: list[tuple[object, ...]] = []
    for bar in value.bars:
        if type(bar) is not Bar or type(bar.provenance) is not BarProvenance:
            raise MultiTimeframeObservationTransportError(
                "Normalized observations contain an unexpected bar type."
            )
        bar_snapshots.append(
            (
                bar,
                bar.timestamp_utc,
                bar.open,
                bar.high,
                bar.low,
                bar.close,
                bar.volume,
                bar.provenance,
                bar.provenance.source_record_index,
                bar.provenance.source_timestamp,
                bar.provenance.naive_timezone_assumed_utc,
            )
        )
    provenance = value.provenance
    if type(provenance) is not DataProvenance:
        raise MultiTimeframeObservationTransportError(
            "Observation provenance must retain the exact DataProvenance type."
        )
    _validate_timeframe(provenance.source_resolution)
    if provenance.source_resolution != timeframe:
        raise MultiTimeframeObservationTransportError(
            "Provenance source_resolution must equal the observation timeframe."
        )
    if type(provenance.resampled) is not bool:
        raise MultiTimeframeObservationTransportError(
            "Provenance resampled must retain one exact boolean."
        )
    if type(provenance.parent_source_hashes) is not tuple:
        raise MultiTimeframeObservationTransportError(
            "parent_source_hashes must retain one exact tuple."
        )
    quality = value.quality
    if type(quality) is not DataQualityReport:
        raise MultiTimeframeObservationTransportError(
            "Observation quality must retain the exact DataQualityReport type."
        )
    if type(quality.duplicate_timestamps_utc) is not tuple or type(
        quality.missing_intervals
    ) is not tuple:
        raise MultiTimeframeObservationTransportError(
            "Data-quality collections must retain exact tuples."
        )
    if type(quality.volume_available) is not bool or type(
        quality.volume_complete
    ) is not bool:
        raise MultiTimeframeObservationTransportError(
            "Data-quality volume flags must retain exact booleans."
        )
    interval_snapshots: list[tuple[object, ...]] = []
    for interval in quality.missing_intervals:
        if type(interval) is not MissingBarInterval:
            raise MultiTimeframeObservationTransportError(
                "Missing intervals must retain the exact existing type."
            )
        interval_snapshots.append(
            (
                interval,
                interval.after_timestamp_utc,
                interval.before_timestamp_utc,
                interval.missing_bar_count,
            )
        )
    return (
        value,
        symbol,
        _symbol_key(symbol),
        timeframe,
        timeframe.label,
        timeframe.resolution_seconds,
        value.bars,
        tuple(bar_snapshots),
        provenance,
        provenance.source_type,
        provenance.source_identifier,
        provenance.source_sha256,
        provenance.source_resolution,
        provenance.ingested_at_utc,
        provenance.resampled,
        provenance.parent_source_hashes,
        quality,
        quality.duplicate_timestamps_utc,
        tuple(interval_snapshots),
        quality.volume_available,
        quality.volume_complete,
    )


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class MultiTimeframeObservationBundle(metaclass=_SealedTransportType):
    symbol: SymbolIdentity
    observation_sets: tuple[NormalizedMarketObservations, ...]
    provenance_refs: tuple[str, ...] = ()
    _identity_snapshot: tuple[object, ...] = field(init=False, repr=False)
    _observation_snapshots: tuple[tuple[object, ...], ...] = field(
        init=False,
        repr=False,
    )

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("Multi-timeframe observation bundles cannot be subclassed.")

    def __post_init__(self) -> None:
        symbol = _validate_symbol(self.symbol)
        _require_provenance(self.provenance_refs)
        if type(self.observation_sets) is not tuple:
            raise MultiTimeframeObservationTransportError(
                "observation_sets must be one exact tuple."
            )
        snapshots = tuple(_observation_snapshot(item) for item in self.observation_sets)
        expected_symbol = _symbol_key(symbol)
        seen_resolutions: set[int] = set()
        for observation in self.observation_sets:
            if _symbol_key(observation.symbol) != expected_symbol:
                raise MultiTimeframeObservationTransportError(
                    "All observation sets must have the bundle's exact symbol field values."
                )
            resolution = observation.timeframe.resolution_seconds
            if resolution in seen_resolutions:
                raise MultiTimeframeObservationTransportError(
                    "Each chart resolution_seconds value must be unique within a bundle."
                )
            seen_resolutions.add(resolution)
        object.__setattr__(
            self,
            "_identity_snapshot",
            (self.symbol, self.observation_sets, self.provenance_refs),
        )
        object.__setattr__(self, "_observation_snapshots", snapshots)

    def _validated(self) -> MultiTimeframeObservationBundle:
        if type(self) is not MultiTimeframeObservationBundle:
            raise MultiTimeframeObservationTransportError(
                "Observation bundles must have the exact reviewed type."
            )
        try:
            identity_snapshot = object.__getattribute__(self, "_identity_snapshot")
            observation_snapshots = object.__getattribute__(
                self,
                "_observation_snapshots",
            )
        except AttributeError as error:
            raise MultiTimeframeObservationTransportError(
                "The observation bundle is malformed."
            ) from error
        current = (self.symbol, self.observation_sets, self.provenance_refs)
        if any(
            observed is not expected
            for observed, expected in zip(current, identity_snapshot, strict=True)
        ):
            raise MultiTimeframeObservationTransportError(
                "The observation bundle changed after construction."
            )
        current_observations = tuple(
            _observation_snapshot(item) for item in self.observation_sets
        )
        if current_observations != observation_snapshots:
            raise MultiTimeframeObservationTransportError(
                "An observation set or nested factual field changed after bundling."
            )
        self.__post_init__()
        return self

    def ordered_by_resolution(self) -> tuple[NormalizedMarketObservations, ...]:
        self._validated()
        return tuple(
            sorted(
                self.observation_sets,
                key=lambda item: item.timeframe.resolution_seconds,
            )
        )

    def __copy__(self) -> MultiTimeframeObservationBundle:
        return self._validated()

    def __deepcopy__(
        self,
        memo: dict[int, object],
    ) -> MultiTimeframeObservationBundle:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Multi-timeframe observation bundles cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class SubjectObservationAttachment(metaclass=_SealedTransportType):
    subject: AnalyzedWaveSubject
    observations: NormalizedMarketObservations
    association_role: ObservationAssociationRole
    provenance_refs: tuple[str, ...] = ()
    _identity_snapshot: tuple[object, ...] = field(init=False, repr=False)
    _observation_snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("Subject observation attachments cannot be subclassed.")

    def __post_init__(self) -> None:
        if type(self.subject) is not AnalyzedWaveSubject:
            raise MultiTimeframeObservationTransportError(
                "Attachment subject must be one exact AnalyzedWaveSubject."
            )
        try:
            self.subject.__post_init__()
        except Exception as error:
            raise MultiTimeframeObservationTransportError(
                "The attachment subject is malformed or changed."
            ) from error
        observation_snapshot = _observation_snapshot(self.observations)
        if type(self.association_role) is not ObservationAssociationRole:
            raise MultiTimeframeObservationTransportError(
                "association_role must be one exact operational role."
            )
        _require_provenance(self.provenance_refs)
        object.__setattr__(
            self,
            "_identity_snapshot",
            (
                self.subject,
                self.observations,
                self.association_role,
                self.provenance_refs,
            ),
        )
        object.__setattr__(self, "_observation_snapshot", observation_snapshot)

    def _validated(self) -> SubjectObservationAttachment:
        if type(self) is not SubjectObservationAttachment:
            raise MultiTimeframeObservationTransportError(
                "Attachments must have the exact reviewed type."
            )
        try:
            snapshot = object.__getattribute__(self, "_identity_snapshot")
            observation_snapshot = object.__getattribute__(
                self,
                "_observation_snapshot",
            )
        except AttributeError as error:
            raise MultiTimeframeObservationTransportError(
                "The subject observation attachment is malformed."
            ) from error
        current = (
            self.subject,
            self.observations,
            self.association_role,
            self.provenance_refs,
        )
        if any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ) or _observation_snapshot(self.observations) != observation_snapshot:
            raise MultiTimeframeObservationTransportError(
                "The subject observation attachment changed after construction."
            )
        return self

    def __copy__(self) -> SubjectObservationAttachment:
        return self._validated()

    def __deepcopy__(
        self,
        memo: dict[int, object],
    ) -> SubjectObservationAttachment:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Subject observation attachments cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class ObservationTransportDiagnostic(metaclass=_SealedTransportType):
    state: ObservationTransportDiagnosticState
    subject: AnalyzedWaveSubject
    observation_sets: tuple[NormalizedMarketObservations, ...]
    reason: str
    _identity_snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("Observation transport diagnostics cannot be subclassed.")

    def __post_init__(self) -> None:
        if type(self.state) is not ObservationTransportDiagnosticState:
            raise MultiTimeframeObservationTransportError(
                "Diagnostic state has an unexpected type."
            )
        if type(self.subject) is not AnalyzedWaveSubject:
            raise MultiTimeframeObservationTransportError(
                "Diagnostic subject has an unexpected type."
            )
        if type(self.observation_sets) is not tuple or any(
            type(item) is not NormalizedMarketObservations
            for item in self.observation_sets
        ):
            raise MultiTimeframeObservationTransportError(
                "Diagnostic observations must be one exact tuple."
            )
        _require_text(self.reason, "diagnostic reason")
        object.__setattr__(
            self,
            "_identity_snapshot",
            (self.state, self.subject, self.observation_sets, self.reason),
        )

    def _validated(self) -> ObservationTransportDiagnostic:
        try:
            snapshot = object.__getattribute__(self, "_identity_snapshot")
        except AttributeError as error:
            raise MultiTimeframeObservationTransportError(
                "The transport diagnostic is malformed."
            ) from error
        current = (self.state, self.subject, self.observation_sets, self.reason)
        if any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            raise MultiTimeframeObservationTransportError(
                "The transport diagnostic changed after construction."
            )
        self.__post_init__()
        return self

    def __copy__(self) -> ObservationTransportDiagnostic:
        return self._validated()

    def __deepcopy__(
        self,
        memo: dict[int, object],
    ) -> ObservationTransportDiagnostic:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Observation transport diagnostics cannot be pickled.")


def _subject_inventory(
    recursive_result: RecursiveCandidateCompositionResult,
) -> tuple[AnalyzedWaveSubject, ...]:
    try:
        recursive_result._validated()
    except Exception as error:
        raise MultiTimeframeObservationTransportError(
            "The recursive candidate result is malformed or changed."
        ) from error
    inventory: list[AnalyzedWaveSubject] = []
    active_nodes: set[int] = set()

    def visit(node: object) -> None:
        node_id = id(node)
        if node_id in active_nodes:
            raise MultiTimeframeObservationTransportError(
                "The recursive candidate tree contains a cycle."
            )
        active_nodes.add(node_id)
        try:
            subject = node.subject
            if any(existing is subject for existing in inventory):
                raise MultiTimeframeObservationTransportError(
                    "The recursive candidate tree repeats one exact subject."
                )
            inventory.append(subject)
            for child in node.children:
                visit(child)
        finally:
            active_nodes.remove(node_id)

    visit(recursive_result.parent_node)
    return tuple(inventory)


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class MultiTimeframeObservationTransportRequest(metaclass=_SealedTransportType):
    request_id: str
    recursive_candidate_result: RecursiveCandidateCompositionResult
    observation_bundle: MultiTimeframeObservationBundle
    subject_attachments: tuple[SubjectObservationAttachment, ...]
    provenance_refs: tuple[str, ...] = ()
    _identity_snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("Multi-timeframe transport requests cannot be subclassed.")

    def __post_init__(self) -> None:
        _require_text(self.request_id, "request_id")
        _require_provenance(self.provenance_refs)
        if type(self.recursive_candidate_result) is not RecursiveCandidateCompositionResult:
            raise MultiTimeframeObservationTransportError(
                "recursive_candidate_result must have its exact live result type."
            )
        inventory = _subject_inventory(self.recursive_candidate_result)
        if type(self.observation_bundle) is not MultiTimeframeObservationBundle:
            raise MultiTimeframeObservationTransportError(
                "observation_bundle must have its exact reviewed type."
            )
        bundle = self.observation_bundle._validated()
        if type(self.subject_attachments) is not tuple:
            raise MultiTimeframeObservationTransportError(
                "subject_attachments must be one exact tuple."
            )
        seen_pairs: set[tuple[int, int]] = set()
        for attachment in self.subject_attachments:
            if type(attachment) is not SubjectObservationAttachment:
                raise MultiTimeframeObservationTransportError(
                    "Every attachment must have the exact reviewed type."
                )
            attachment._validated()
            if not any(attachment.subject is item for item in inventory):
                raise MultiTimeframeObservationTransportError(
                    "An attached subject is foreign to the recursive candidate tree."
                )
            if not any(
                attachment.observations is item for item in bundle.observation_sets
            ):
                raise MultiTimeframeObservationTransportError(
                    "An attachment observation is not an exact member of the bundle."
                )
            pair = (id(attachment.subject), id(attachment.observations))
            if pair in seen_pairs:
                raise MultiTimeframeObservationTransportError(
                    "The same exact subject and observation set cannot be attached twice."
                )
            seen_pairs.add(pair)
        object.__setattr__(
            self,
            "_identity_snapshot",
            (
                self.request_id,
                self.recursive_candidate_result,
                self.observation_bundle,
                self.subject_attachments,
                self.provenance_refs,
            ),
        )

    def _validated(self) -> MultiTimeframeObservationTransportRequest:
        if type(self) is not MultiTimeframeObservationTransportRequest:
            raise MultiTimeframeObservationTransportError(
                "Transport requests must have the exact reviewed type."
            )
        try:
            snapshot = object.__getattribute__(self, "_identity_snapshot")
        except AttributeError as error:
            raise MultiTimeframeObservationTransportError(
                "The transport request is malformed."
            ) from error
        current = (
            self.request_id,
            self.recursive_candidate_result,
            self.observation_bundle,
            self.subject_attachments,
            self.provenance_refs,
        )
        if any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            raise MultiTimeframeObservationTransportError(
                "The transport request changed after construction."
            )
        self.__post_init__()
        return self

    def __copy__(self) -> MultiTimeframeObservationTransportRequest:
        return self._validated()

    def __deepcopy__(
        self,
        memo: dict[int, object],
    ) -> MultiTimeframeObservationTransportRequest:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Multi-timeframe transport requests cannot be pickled.")


def _diagnostics(
    subjects: tuple[AnalyzedWaveSubject, ...],
    attachments: tuple[SubjectObservationAttachment, ...],
) -> tuple[ObservationTransportDiagnostic, ...]:
    diagnostics: list[ObservationTransportDiagnostic] = []
    for subject in subjects:
        observations = tuple(
            attachment.observations
            for attachment in attachments
            if attachment.subject is subject
        )
        if not observations:
            diagnostics.append(
                ObservationTransportDiagnostic(
                    ObservationTransportDiagnosticState.SUBJECT_NO_OBSERVATIONS,
                    subject,
                    (),
                    "NO_OBSERVATION_ASSOCIATION_SUPPLIED",
                )
            )
            continue
        diagnostics.append(
            ObservationTransportDiagnostic(
                ObservationTransportDiagnosticState.SUBJECT_ATTACHED,
                subject,
                observations,
                "Exact caller-supplied observation associations are retained.",
            )
        )
        if len(observations) > 1:
            diagnostics.extend(
                (
                    ObservationTransportDiagnostic(
                        ObservationTransportDiagnosticState.MULTIPLE_RESOLUTIONS_ATTACHED,
                        subject,
                        observations,
                        "Multiple distinct chart resolutions are explicitly attached.",
                    ),
                    ObservationTransportDiagnostic(
                        ObservationTransportDiagnosticState.FINER_RESOLUTION_AVAILABLE,
                        subject,
                        observations,
                        "An explicitly attached observation has a finer sampling resolution.",
                    ),
                    ObservationTransportDiagnostic(
                        ObservationTransportDiagnosticState.COARSER_RESOLUTION_AVAILABLE,
                        subject,
                        observations,
                        "An explicitly attached observation has a coarser sampling resolution.",
                    ),
                )
            )
    return tuple(diagnostics)


@dataclass(
    frozen=True,
    slots=True,
    eq=False,
    weakref_slot=True,
    init=False,
)
class MultiTimeframeObservationTransportResult(metaclass=_SealedTransportType):
    request_id: str
    recursive_candidate_result: RecursiveCandidateCompositionResult
    observation_bundle: MultiTimeframeObservationBundle
    subject_attachments: tuple[SubjectObservationAttachment, ...]
    subject_inventory: tuple[AnalyzedWaveSubject, ...]
    resolution_inventory: tuple[NormalizedMarketObservations, ...]
    transport_diagnostics: tuple[ObservationTransportDiagnostic, ...]
    provenance_refs: tuple[str, ...]
    _request: MultiTimeframeObservationTransportRequest
    _identity_snapshot: tuple[object, ...]

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("Transport results are created only by MethodologyKernel.")

    def _validated(self) -> MultiTimeframeObservationTransportResult:
        if type(self) is not MultiTimeframeObservationTransportResult:
            raise MultiTimeframeObservationTransportError(
                "Transport results must have the exact live result type."
            )
        try:
            request = object.__getattribute__(self, "_request")
            snapshot = object.__getattribute__(self, "_identity_snapshot")
        except AttributeError as error:
            raise MultiTimeframeObservationTransportError(
                "The transport result is malformed."
            ) from error
        current = (
            self.request_id,
            self.recursive_candidate_result,
            self.observation_bundle,
            self.subject_attachments,
            self.subject_inventory,
            self.resolution_inventory,
            self.transport_diagnostics,
            self.provenance_refs,
            request,
        )
        if any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            raise MultiTimeframeObservationTransportError(
                "The transport result changed after construction."
            )
        request._validated()
        if (
            self.request_id is not request.request_id
            or self.recursive_candidate_result is not request.recursive_candidate_result
            or self.observation_bundle is not request.observation_bundle
            or self.subject_attachments is not request.subject_attachments
            or self.provenance_refs is not request.provenance_refs
        ):
            raise MultiTimeframeObservationTransportError(
                "The result no longer retains its exact request identities."
            )
        expected_subjects = _subject_inventory(self.recursive_candidate_result)
        if len(self.subject_inventory) != len(expected_subjects) or any(
            observed is not expected
            for observed, expected in zip(
                self.subject_inventory,
                expected_subjects,
                strict=True,
            )
        ):
            raise MultiTimeframeObservationTransportError(
                "The subject inventory no longer matches the recursive tree."
            )
        expected_resolutions = self.observation_bundle.ordered_by_resolution()
        if len(self.resolution_inventory) != len(expected_resolutions) or any(
            observed is not expected
            for observed, expected in zip(
                self.resolution_inventory,
                expected_resolutions,
                strict=True,
            )
        ):
            raise MultiTimeframeObservationTransportError(
                "The resolution inventory no longer matches the exact bundle."
            )
        expected_diagnostics = _diagnostics(
            self.subject_inventory,
            self.subject_attachments,
        )
        if len(self.transport_diagnostics) != len(expected_diagnostics):
            raise MultiTimeframeObservationTransportError(
                "The diagnostic inventory has an unexpected cardinality."
            )
        for diagnostic in self.transport_diagnostics:
            if type(diagnostic) is not ObservationTransportDiagnostic:
                raise MultiTimeframeObservationTransportError(
                    "Transport diagnostics must retain their exact type."
                )
            diagnostic._validated()
        return self

    def __copy__(self) -> MultiTimeframeObservationTransportResult:
        return self._validated()

    def __deepcopy__(
        self,
        memo: dict[int, object],
    ) -> MultiTimeframeObservationTransportResult:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Multi-timeframe transport results cannot be pickled.")


def _attached_observations_for_subject(
    result: MultiTimeframeObservationTransportResult,
    subject: AnalyzedWaveSubject,
) -> tuple[NormalizedMarketObservations, ...]:
    if type(result) is not MultiTimeframeObservationTransportResult:
        raise MultiTimeframeObservationTransportError(
            "result must have the exact live transport result type."
        )
    result._validated()
    if type(subject) is not AnalyzedWaveSubject or not any(
        subject is item for item in result.subject_inventory
    ):
        raise MultiTimeframeObservationTransportError(
            "subject must be one exact member of the recursive tree."
        )
    return tuple(
        attachment.observations
        for attachment in result.subject_attachments
        if attachment.subject is subject
    )


def has_finer_observation_data(
    result: MultiTimeframeObservationTransportResult,
    subject: AnalyzedWaveSubject,
    relative_to_timeframe: Timeframe,
) -> bool:
    """Return only whether an explicitly attached finer sampling resolution exists."""
    timeframe = _validate_timeframe(relative_to_timeframe)
    return any(
        observation.timeframe.resolution_seconds < timeframe.resolution_seconds
        for observation in _attached_observations_for_subject(result, subject)
    )


def has_coarser_observation_data(
    result: MultiTimeframeObservationTransportResult,
    subject: AnalyzedWaveSubject,
    relative_to_timeframe: Timeframe,
) -> bool:
    """Return only whether an explicitly attached coarser sampling resolution exists."""
    timeframe = _validate_timeframe(relative_to_timeframe)
    return any(
        observation.timeframe.resolution_seconds > timeframe.resolution_seconds
        for observation in _attached_observations_for_subject(result, subject)
    )


def _attach_multi_timeframe_observations(
    request: object,
) -> MultiTimeframeObservationTransportResult:
    if type(request) is not MultiTimeframeObservationTransportRequest:
        raise MultiTimeframeObservationTransportError(
            "attach_multi_timeframe_observations requires one exact transport request."
        )
    request._validated()
    subjects = _subject_inventory(request.recursive_candidate_result)
    resolutions = request.observation_bundle.ordered_by_resolution()
    diagnostics = _diagnostics(subjects, request.subject_attachments)
    result = object.__new__(MultiTimeframeObservationTransportResult)
    values = {
        "request_id": request.request_id,
        "recursive_candidate_result": request.recursive_candidate_result,
        "observation_bundle": request.observation_bundle,
        "subject_attachments": request.subject_attachments,
        "subject_inventory": subjects,
        "resolution_inventory": resolutions,
        "transport_diagnostics": diagnostics,
        "provenance_refs": request.provenance_refs,
        "_request": request,
    }
    for name, value in values.items():
        object.__setattr__(result, name, value)
    object.__setattr__(result, "_identity_snapshot", tuple(values.values()))
    return result._validated()


__all__ = [
    "ARTIFACT_CLASSIFICATION",
    "ASSOCIATION_CLASSIFICATION",
    "TIMEFRAME_IS_NOT_DEGREE",
    "WORKFLOW_POLICY_CLASSIFICATION",
    "MultiTimeframeObservationBundle",
    "MultiTimeframeObservationTransportError",
    "MultiTimeframeObservationTransportRequest",
    "MultiTimeframeObservationTransportResult",
    "ObservationAssociationRole",
    "ObservationResolutionRelation",
    "ObservationTransportDiagnostic",
    "ObservationTransportDiagnosticState",
    "SubjectObservationAttachment",
    "compare_observation_resolutions",
    "has_coarser_observation_data",
    "has_finer_observation_data",
]
