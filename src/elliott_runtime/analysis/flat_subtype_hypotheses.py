"""Source-locked, hypothesis-only Flat subtype evaluate-as infrastructure.

This module fans an exact generic Flat family hypothesis out into the three
protected, source-named shape hypotheses.  It does not classify a Flat,
execute endpoint rules, rank alternatives, or create Elliott validity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import NoReturn
import weakref

from .endpoint_path_evidence import (
    ENDPOINT_AUTHORITY_CLASS,
    EndpointPathEvidenceResult,
    ObservedComponentDirection,
    validate_endpoint_path_evidence_result,
)
from .family_hypotheses import (
    ElliottFamilyEvaluationHypothesis,
    FamilyEvaluationKind,
    FamilyHypothesisBridgeResult,
    validate_family_hypothesis_bridge_result,
)
from .recursive_child_family_evaluation import (
    RecursiveChildFamilyEvaluationResult,
    validate_recursive_child_family_evaluation_result,
)


ARTIFACT_CLASSIFICATION = "PROJECT_ANALYSIS_INFRASTRUCTURE"
EVALUATION_SCOPE_CLASSIFICATION = "SOURCE_DERIVED_EVALUATION_SCOPE"
SUBTYPE_HYPOTHESIS_IS_NOT_SUBTYPE_CLASSIFICATION = True
GENERIC_FLAT_IS_NOT_INVALIDATED_BY_SUBTYPE_RESULTS = True
HYPOTHESIS_BOUND_ENDPOINT_IS_NOT_ORTHODOX_ENDPOINT = True
TIMEFRAME_IS_NOT_DEGREE = True
TAXONOMY_COMPLETENESS = "KNOWN_SUBTYPES_NON_EXHAUSTIVE"
IRREGULAR_EXPANDED_ALIAS_DECISION = "IRREGULAR_IS_HISTORICAL_ALIAS_OF_EXPANDED"
_MAX_FLAT_HYPOTHESES = 100_000
_SUBTYPE_COUNT = 3


class FlatSubtypeHypothesisError(ValueError):
    """Fail-closed Flat subtype hypothesis contract error."""


class FlatSubtypeHypothesisLimitExceeded(FlatSubtypeHypothesisError):
    """Raised before any partial subtype result is issued."""


class FlatSubtypeEvaluationKind(StrEnum):
    REGULAR_FLAT = "REGULAR_FLAT"
    EXPANDED_FLAT = "EXPANDED_FLAT"
    RUNNING_FLAT = "RUNNING_FLAT"


class FlatSubtypeSourceKind(StrEnum):
    PARENT_FAMILY_HYPOTHESES = "PARENT_FAMILY_HYPOTHESES"
    RECURSIVE_CHILD_FAMILY_HYPOTHESES = "RECURSIVE_CHILD_FAMILY_HYPOTHESES"


class _Sealed(type):
    def __new__(mcls, name, bases, namespace, **kwargs):
        if any(isinstance(base, mcls) for base in bases):
            raise TypeError("Flat subtype hypothesis contracts cannot be subclassed.")
        return super().__new__(mcls, name, bases, namespace, **kwargs)


def _fail(message: str) -> NoReturn:
    raise FlatSubtypeHypothesisError(message)


def _text(value: object, name: str) -> str:
    if type(value) is not str or not value.strip():
        _fail(f"{name} must be one exact non-blank string.")
    return value


def _refs(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or any(
        type(item) is not str or not item.strip() for item in value
    ):
        _fail("provenance_refs must be one exact tuple of non-blank strings.")
    return value


_ALIASES = MappingProxyType(
    {
        FlatSubtypeEvaluationKind.REGULAR_FLAT: (),
        FlatSubtypeEvaluationKind.EXPANDED_FLAT: ("IRREGULAR_FLAT",),
        FlatSubtypeEvaluationKind.RUNNING_FLAT: (),
    }
)


def _source_hypotheses(
    source: FamilyHypothesisBridgeResult | RecursiveChildFamilyEvaluationResult,
) -> tuple[ElliottFamilyEvaluationHypothesis, ...]:
    if type(source) is FamilyHypothesisBridgeResult:
        validate_family_hypothesis_bridge_result(source)
    elif type(source) is RecursiveChildFamilyEvaluationResult:
        validate_recursive_child_family_evaluation_result(source)
    else:
        _fail("family_source must be one exact approved parent or child result.")
    hypotheses = source.family_hypotheses
    if type(hypotheses) is not tuple or any(
        type(item) is not ElliottFamilyEvaluationHypothesis for item in hypotheses
    ):
        _fail("family_source contains an unexpected family hypothesis type.")
    for item in hypotheses:
        item._validated()
    return hypotheses


@dataclass(frozen=True, slots=True, eq=False)
class FlatSubtypeHypothesisRequest(metaclass=_Sealed):
    request_id: str
    family_source: FamilyHypothesisBridgeResult | RecursiveChildFamilyEvaluationResult
    endpoint_evidence_results: tuple[EndpointPathEvidenceResult, ...]
    max_flat_hypotheses_processed: int
    max_subtypes_per_flat: int
    max_total_flat_subtype_hypotheses: int
    provenance_refs: tuple[str, ...]
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        _text(self.request_id, "request_id")
        flat_hypotheses = tuple(
            item
            for item in _source_hypotheses(self.family_source)
            if item.family_kind is FamilyEvaluationKind.FLAT
        )
        if type(self.endpoint_evidence_results) is not tuple or any(
            type(item) is not EndpointPathEvidenceResult
            for item in self.endpoint_evidence_results
        ):
            _fail("endpoint_evidence_results must be one exact tuple of issued results.")
        if len(self.endpoint_evidence_results) != len(flat_hypotheses):
            _fail("Every and only source Flat hypothesis requires endpoint evidence.")
        for hypothesis, evidence in zip(
            flat_hypotheses, self.endpoint_evidence_results, strict=True
        ):
            validate_endpoint_path_evidence_result(evidence)
            if evidence.family_hypothesis is not hypothesis:
                _fail("Endpoint evidence order or Flat-hypothesis identity differs.")
        for name, value, maximum in (
            ("max_flat_hypotheses_processed", self.max_flat_hypotheses_processed, _MAX_FLAT_HYPOTHESES),
            ("max_subtypes_per_flat", self.max_subtypes_per_flat, _SUBTYPE_COUNT),
            ("max_total_flat_subtype_hypotheses", self.max_total_flat_subtype_hypotheses, _MAX_FLAT_HYPOTHESES * _SUBTYPE_COUNT),
        ):
            if type(value) is not int or not 1 <= value <= maximum:
                _fail(f"{name} must be one exact integer within its operational bound.")
        _refs(self.provenance_refs)
        current = tuple(
            getattr(self, name)
            for name in self.__dataclass_fields__
            if name != "_snapshot"
        )
        if hasattr(self, "_snapshot"):
            if len(current) != len(self._snapshot) or any(
                observed is not expected
                for observed, expected in zip(current, self._snapshot, strict=True)
            ):
                _fail("Flat subtype request changed after construction.")
        else:
            object.__setattr__(self, "_snapshot", current)

    def _validated(self) -> FlatSubtypeHypothesisRequest:
        if type(self) is not FlatSubtypeHypothesisRequest:
            _fail("Flat subtype request has an unexpected type.")
        self.__post_init__()
        return self

    def __copy__(self):
        return self._validated()

    def __deepcopy__(self, memo):
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol):
        raise TypeError("Flat subtype requests cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False, init=False, weakref_slot=True)
class FlatSubtypeEvaluationHypothesis(metaclass=_Sealed):
    hypothesis_id: str
    source_kind: FlatSubtypeSourceKind
    family_source: FamilyHypothesisBridgeResult | RecursiveChildFamilyEvaluationResult
    flat_family_hypothesis: ElliottFamilyEvaluationHypothesis
    endpoint_evidence: EndpointPathEvidenceResult
    subtype_kind: FlatSubtypeEvaluationKind
    aliases: tuple[str, ...]
    a_start: object
    a_end: object
    b_end: object
    c_end: object
    a_direction: ObservedComponentDirection
    endpoint_authority_class: str
    provenance_refs: tuple[str, ...]
    hypothesis_only: bool
    subtype_classification_authority: bool
    family_validity_authority: bool
    wave_validity_authority: bool
    completion_authority: bool
    degree_authority: bool
    ranking_authority: bool
    _snapshot: tuple[object, ...]

    def __init__(self, *args, **kwargs):
        raise TypeError("Flat subtype hypotheses are created only by the builder.")

    def _validated(self) -> FlatSubtypeEvaluationHypothesis:
        if type(self) is not FlatSubtypeEvaluationHypothesis:
            _fail("Flat subtype hypothesis has an unexpected type.")
        if _ISSUED_HYPOTHESES.get(self) is not self.flat_family_hypothesis:
            _fail("Flat subtype hypothesis is unissued or malformed.")
        current = tuple(
            getattr(self, name)
            for name in self.__dataclass_fields__
            if name != "_snapshot"
        )
        if len(current) != len(self._snapshot) or any(
            observed is not expected
            for observed, expected in zip(current, self._snapshot, strict=True)
        ):
            _fail("Flat subtype hypothesis changed after issuance.")
        self.flat_family_hypothesis._validated()
        validate_endpoint_path_evidence_result(self.endpoint_evidence)
        if self.flat_family_hypothesis.family_kind is not FamilyEvaluationKind.FLAT:
            _fail("Subtype hypothesis lost exact generic Flat scope.")
        if self.endpoint_evidence.family_hypothesis is not self.flat_family_hypothesis:
            _fail("Subtype hypothesis lost exact endpoint-evidence ancestry.")
        bindings = self.endpoint_evidence.component_role_bindings
        endpoints = self.endpoint_evidence.component_endpoint_evidence
        if tuple(item.component_role for item in bindings) != ("A", "B", "C"):
            _fail("Subtype hypothesis lost exact A-B-C roles.")
        expected = (
            bindings[0].start_boundary,
            endpoints[0].boundary_pivot,
            endpoints[1].boundary_pivot,
            endpoints[2].boundary_pivot,
        )
        observed = (self.a_start, self.a_end, self.b_end, self.c_end)
        if any(item is not reference for item, reference in zip(observed, expected, strict=True)):
            _fail("Subtype endpoint identities differ from the exact role evidence.")
        if self.a_direction is not self.endpoint_evidence.component_path_evidence[0].observed_direction:
            _fail("A direction differs from exact endpoint arithmetic.")
        if self.aliases is not _ALIASES[self.subtype_kind]:
            _fail("Subtype canonical aliases differ from the protected taxonomy decision.")
        if self.endpoint_authority_class != ENDPOINT_AUTHORITY_CLASS:
            _fail("Subtype endpoint authority was promoted.")
        if self.hypothesis_only is not True or any(
            (
                self.subtype_classification_authority,
                self.family_validity_authority,
                self.wave_validity_authority,
                self.completion_authority,
                self.degree_authority,
                self.ranking_authority,
            )
        ):
            _fail("Subtype hypothesis cannot carry Elliott validity or ranking authority.")
        _refs(self.provenance_refs)
        return self

    def __copy__(self):
        return self._validated()

    def __deepcopy__(self, memo):
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol):
        raise TypeError("Flat subtype hypotheses cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False, init=False, weakref_slot=True)
class FlatSubtypeHypothesisResult(metaclass=_Sealed):
    request: FlatSubtypeHypothesisRequest
    source_kind: FlatSubtypeSourceKind
    flat_family_hypotheses: tuple[ElliottFamilyEvaluationHypothesis, ...]
    subtype_hypotheses: tuple[FlatSubtypeEvaluationHypothesis, ...]
    diagnostics: tuple[str, ...]
    provenance_refs: tuple[str, ...]
    exhaustive_taxonomy_authority: bool
    subtype_classification_authority: bool
    family_validity_authority: bool
    ranking_authority: bool
    _snapshot: tuple[object, ...]

    def __init__(self, *args, **kwargs):
        raise TypeError("Flat subtype results are created only by the builder.")

    def _validated(self) -> FlatSubtypeHypothesisResult:
        if type(self) is not FlatSubtypeHypothesisResult:
            _fail("Flat subtype result has an unexpected type.")
        if _ISSUED_RESULTS.get(self) is not self.subtype_hypotheses:
            _fail("Flat subtype result is unissued or malformed.")
        current = tuple(
            getattr(self, name)
            for name in self.__dataclass_fields__
            if name != "_snapshot"
        )
        if len(current) != len(self._snapshot) or any(
            observed is not expected
            for observed, expected in zip(current, self._snapshot, strict=True)
        ):
            _fail("Flat subtype result changed after issuance.")
        self.request._validated()
        for item in self.subtype_hypotheses:
            item._validated()
        expected = tuple(
            hypothesis
            for flat in self.flat_family_hypotheses
            for hypothesis in self.subtype_hypotheses
            if hypothesis.flat_family_hypothesis is flat
        )
        if len(expected) != len(self.subtype_hypotheses) or any(
            observed is not reference
            for observed, reference in zip(self.subtype_hypotheses, expected, strict=True)
        ):
            _fail("Flat subtype deterministic fanout order changed.")
        if any(
            (
                self.exhaustive_taxonomy_authority,
                self.subtype_classification_authority,
                self.family_validity_authority,
                self.ranking_authority,
            )
        ):
            _fail("Flat subtype result cannot carry closed-world or validity authority.")
        _refs(self.provenance_refs)
        return self

    def __copy__(self):
        return self._validated()

    def __deepcopy__(self, memo):
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol):
        raise TypeError("Flat subtype results cannot be pickled.")


_ISSUED_HYPOTHESES: weakref.WeakKeyDictionary[
    FlatSubtypeEvaluationHypothesis, ElliottFamilyEvaluationHypothesis
] = weakref.WeakKeyDictionary()
_ISSUED_RESULTS: weakref.WeakKeyDictionary[
    FlatSubtypeHypothesisResult, tuple[FlatSubtypeEvaluationHypothesis, ...]
] = weakref.WeakKeyDictionary()


def build_flat_subtype_hypotheses(
    request: FlatSubtypeHypothesisRequest,
) -> FlatSubtypeHypothesisResult:
    """Build all three known evaluate-as hypotheses without selecting among them."""
    if type(request) is not FlatSubtypeHypothesisRequest:
        _fail("Builder requires one exact Flat subtype request.")
    request._validated()
    source_hypotheses = _source_hypotheses(request.family_source)
    flats = tuple(
        item for item in source_hypotheses if item.family_kind is FamilyEvaluationKind.FLAT
    )
    demand = len(flats) * _SUBTYPE_COUNT
    if len(flats) > request.max_flat_hypotheses_processed:
        raise FlatSubtypeHypothesisLimitExceeded(
            "Flat-hypothesis preflight bound exceeded; no partial result was issued."
        )
    if _SUBTYPE_COUNT > request.max_subtypes_per_flat:
        raise FlatSubtypeHypothesisLimitExceeded(
            "Per-Flat subtype preflight bound exceeded; no partial result was issued."
        )
    if demand > request.max_total_flat_subtype_hypotheses:
        raise FlatSubtypeHypothesisLimitExceeded(
            "Total subtype preflight bound exceeded; no partial result was issued."
        )
    source_kind = (
        FlatSubtypeSourceKind.PARENT_FAMILY_HYPOTHESES
        if type(request.family_source) is FamilyHypothesisBridgeResult
        else FlatSubtypeSourceKind.RECURSIVE_CHILD_FAMILY_HYPOTHESES
    )
    created: list[FlatSubtypeEvaluationHypothesis] = []
    for flat, evidence in zip(flats, request.endpoint_evidence_results, strict=True):
        bindings = evidence.component_role_bindings
        endpoints = evidence.component_endpoint_evidence
        for subtype in FlatSubtypeEvaluationKind:
            values = {
                "hypothesis_id": f"{flat.hypothesis_id}:evaluate-as:{subtype.value}",
                "source_kind": source_kind,
                "family_source": request.family_source,
                "flat_family_hypothesis": flat,
                "endpoint_evidence": evidence,
                "subtype_kind": subtype,
                "aliases": _ALIASES[subtype],
                "a_start": bindings[0].start_boundary,
                "a_end": endpoints[0].boundary_pivot,
                "b_end": endpoints[1].boundary_pivot,
                "c_end": endpoints[2].boundary_pivot,
                "a_direction": evidence.component_path_evidence[0].observed_direction,
                "endpoint_authority_class": ENDPOINT_AUTHORITY_CLASS,
                "provenance_refs": request.provenance_refs
                + flat.provenance_refs
                + evidence.provenance_refs
                + (
                    "docs/elliott/PATTERN_BRAIN.md#G-flat-family",
                    "Sources_LOCKED/book_frost_prechter/Elliott_Wave_Principle_Frost_Prechter_20th_Anniversary_1998.pdf#pages-45-49",
                    f"evaluate-as:{subtype.value}",
                ),
                "hypothesis_only": True,
                "subtype_classification_authority": False,
                "family_validity_authority": False,
                "wave_validity_authority": False,
                "completion_authority": False,
                "degree_authority": False,
                "ranking_authority": False,
            }
            hypothesis = object.__new__(FlatSubtypeEvaluationHypothesis)
            for name, value in values.items():
                object.__setattr__(hypothesis, name, value)
            object.__setattr__(hypothesis, "_snapshot", tuple(values.values()))
            _ISSUED_HYPOTHESES[hypothesis] = flat
            created.append(hypothesis._validated())
    hypotheses = tuple(created)
    values = {
        "request": request,
        "source_kind": source_kind,
        "flat_family_hypotheses": flats,
        "subtype_hypotheses": hypotheses,
        "diagnostics": (
            IRREGULAR_EXPANDED_ALIAS_DECISION,
            TAXONOMY_COMPLETENESS,
            "EVALUATE_AS_IS_NOT_SUBTYPE_CLASSIFICATION",
            "NO_ENDPOINT_RULE_EXECUTION",
            "NO_RANKING_OR_CLOSED_WORLD_PROPAGATION",
        ),
        "provenance_refs": request.provenance_refs,
        "exhaustive_taxonomy_authority": False,
        "subtype_classification_authority": False,
        "family_validity_authority": False,
        "ranking_authority": False,
    }
    result = object.__new__(FlatSubtypeHypothesisResult)
    for name, value in values.items():
        object.__setattr__(result, name, value)
    object.__setattr__(result, "_snapshot", tuple(values.values()))
    _ISSUED_RESULTS[result] = hypotheses
    return result._validated()


def validate_flat_subtype_hypothesis_result(
    result: object,
) -> FlatSubtypeHypothesisResult:
    if type(result) is not FlatSubtypeHypothesisResult:
        _fail("Expected one exact Flat subtype result.")
    return result._validated()


__all__ = [
    "ARTIFACT_CLASSIFICATION",
    "EVALUATION_SCOPE_CLASSIFICATION",
    "GENERIC_FLAT_IS_NOT_INVALIDATED_BY_SUBTYPE_RESULTS",
    "HYPOTHESIS_BOUND_ENDPOINT_IS_NOT_ORTHODOX_ENDPOINT",
    "IRREGULAR_EXPANDED_ALIAS_DECISION",
    "SUBTYPE_HYPOTHESIS_IS_NOT_SUBTYPE_CLASSIFICATION",
    "TAXONOMY_COMPLETENESS",
    "TIMEFRAME_IS_NOT_DEGREE",
    "FlatSubtypeEvaluationHypothesis",
    "FlatSubtypeEvaluationKind",
    "FlatSubtypeHypothesisError",
    "FlatSubtypeHypothesisLimitExceeded",
    "FlatSubtypeHypothesisRequest",
    "FlatSubtypeHypothesisResult",
    "FlatSubtypeSourceKind",
    "build_flat_subtype_hypotheses",
    "validate_flat_subtype_hypothesis_result",
]
