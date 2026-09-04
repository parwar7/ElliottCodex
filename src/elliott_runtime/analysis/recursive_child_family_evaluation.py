"""One bounded child-family hypothesis layer over neutral generated evidence.

This infrastructure selects only source-supported *evaluation scopes* and
delegates them to the existing family bridge.  It cannot satisfy an internal
requirement, validate a family, infer degree, rank alternatives, or recurse.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import NoReturn
import weakref

from elliott_methodology_kernel import MethodologyKernel

from .family_hypotheses import (
    FamilyEvaluationKind,
    FamilyHypothesisBridgeRequest,
    FamilyHypothesisBridgeResult,
    build_family_evaluation_hypotheses,
    estimate_family_hypothesis_demand,
    validate_family_hypothesis_bridge_result,
)
from .family_internal_subdivisions import (
    FamilyInternalSubdivisionRequirement,
    RequiredInternalShape,
)
from .recursive_child_candidate_generation import (
    GeneratedChildCandidateEvidence,
    RecursiveChildCandidateGenerationResult,
)


ARTIFACT_CLASSIFICATION = "PROJECT_ANALYSIS_INFRASTRUCTURE"
SCOPE_CLASSIFICATION = "SOURCE_DERIVED_EVALUATION_SCOPE"
BOUND_CLASSIFICATION = "CALLER_SUPPLIED_OPERATIONAL_BOUND"
EXACT_CHILD_FAMILY_EVALUATION_LEVELS = 1
FAMILY_HYPOTHESIS_IS_NOT_FAMILY_CLASSIFICATION = True
INTERNAL_REQUIREMENT_IS_NOT_SATISFIED = True
ALL_EXECUTABLE_HYPOTHESES_INVALID_IS_NOT_CLOSED_WORLD_PROOF = True
TIMEFRAME_IS_NOT_DEGREE = True


class RecursiveChildFamilyEvaluationError(ValueError):
    """Fail-closed child-family evaluation contract error."""


class RecursiveChildFamilyEvaluationLimitExceeded(RecursiveChildFamilyEvaluationError):
    """Raised before family hypotheses are materialized when a bound is exceeded."""


class ChildFamilyCoverageState(StrEnum):
    EXECUTABLE_SCOPE_AVAILABLE = "EXECUTABLE_SCOPE_AVAILABLE"
    PARTIAL_EXECUTABLE_FAMILY_COVERAGE = "PARTIAL_EXECUTABLE_FAMILY_COVERAGE"
    NO_EXECUTABLE_FAMILY_COVERAGE = "NO_EXECUTABLE_FAMILY_COVERAGE"
    UNRESOLVED_COMPATIBILITY = "UNRESOLVED_COMPATIBILITY"


class ChildCandidateFamilyEvaluationState(StrEnum):
    EXECUTABLE_CHILD_FAMILY_HYPOTHESES_RETAINED = "EXECUTABLE_CHILD_FAMILY_HYPOTHESES_RETAINED"
    EXECUTABLE_CHILD_FAMILY_HYPOTHESES_EXHAUSTED = "EXECUTABLE_CHILD_FAMILY_HYPOTHESES_EXHAUSTED"
    NO_EXECUTABLE_COMPATIBLE_CHILD_FAMILY_HYPOTHESIS = "NO_EXECUTABLE_COMPATIBLE_CHILD_FAMILY_HYPOTHESIS"


class _SealedType(type):
    def __new__(mcls, name, bases, namespace, **kwargs):
        if any(isinstance(base, mcls) for base in bases):
            raise TypeError("Recursive child-family infrastructure cannot be subclassed.")
        return super().__new__(mcls, name, bases, namespace, **kwargs)


def _fail(message: str) -> NoReturn:
    raise RecursiveChildFamilyEvaluationError(message)


def _text(value: object, name: str) -> str:
    if type(value) is not str or not value.strip():
        _fail(f"{name} must be one exact non-blank string.")
    return value


def _refs(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or any(type(x) is not str or not x.strip() for x in value):
        _fail("provenance_refs must be one exact tuple of non-blank strings.")
    return value


def _positive(value: object, name: str) -> int:
    if type(value) is not int or value < 1:
        _fail(f"{name} must be one positive exact integer.")
    return value


@dataclass(frozen=True, slots=True, eq=False)
class ChildFamilyEvaluationConfig(metaclass=_SealedType):
    allowed_family_kinds: tuple[FamilyEvaluationKind, ...]
    max_requirements_processed: int
    max_child_candidate_sets_processed: int
    max_child_candidates_processed: int
    max_family_hypotheses_per_child_candidate: int
    max_total_child_family_hypotheses: int
    max_total_methodology_evaluations: int
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self):
        if type(self.allowed_family_kinds) is not tuple or any(type(x) is not FamilyEvaluationKind for x in self.allowed_family_kinds):
            _fail("allowed_family_kinds must contain only exact family kinds.")
        if len(set(self.allowed_family_kinds)) != len(self.allowed_family_kinds):
            _fail("allowed_family_kinds cannot contain duplicates.")
        for name in self.__dataclass_fields__:
            if name not in ("allowed_family_kinds", "_snapshot"):
                _positive(getattr(self, name), name)
        object.__setattr__(self, "_snapshot", tuple(getattr(self, n) for n in self.__dataclass_fields__ if n != "_snapshot"))

    def _validated(self):
        current = tuple(getattr(self, n) for n in self.__dataclass_fields__ if n != "_snapshot")
        if type(self) is not ChildFamilyEvaluationConfig or len(current) != len(self._snapshot) or any(a is not b for a, b in zip(current, self._snapshot, strict=True)):
            _fail("Child-family config changed or has an unexpected type.")
        return self


@dataclass(frozen=True, slots=True, eq=False)
class ChildRequirementFamilyScope(metaclass=_SealedType):
    internal_requirement: FamilyInternalSubdivisionRequirement
    coverage_state: ChildFamilyCoverageState
    compatible_executable_family_kinds: tuple[FamilyEvaluationKind, ...]
    unavailable_source_families: tuple[str, ...]
    blockers: tuple[str, ...]
    source_class: str
    protected_refs: tuple[str, ...]
    family_validity_authority: bool = False
    requirement_satisfaction_authority: bool = False
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self):
        if type(self.internal_requirement) is not FamilyInternalSubdivisionRequirement:
            _fail("Scope requires one exact internal requirement.")
        self.internal_requirement.__post_init__()
        if type(self.coverage_state) is not ChildFamilyCoverageState:
            _fail("Scope coverage state has an unexpected type.")
        if type(self.compatible_executable_family_kinds) is not tuple or any(type(x) is not FamilyEvaluationKind for x in self.compatible_executable_family_kinds):
            _fail("Compatible family scope has an unexpected type.")
        if type(self.unavailable_source_families) is not tuple or any(type(x) is not str or not x for x in self.unavailable_source_families):
            _fail("Unavailable families must be exact non-blank strings.")
        if type(self.blockers) is not tuple or any(type(x) is not str or not x for x in self.blockers):
            _fail("Blockers must be exact non-blank strings.")
        if self.source_class not in ("SOURCE_DEFINITION", "UNRESOLVED"):
            _fail("Scope source classification is unsupported.")
        _refs(self.protected_refs)
        if self.family_validity_authority or self.requirement_satisfaction_authority:
            _fail("Evaluation scope cannot carry family or satisfaction authority.")
        names = tuple(name for name in self.__dataclass_fields__ if name != "_snapshot")
        current = tuple(getattr(self, name) for name in names)
        if hasattr(self, "_snapshot"):
            if len(current) != len(self._snapshot) or any(a is not b for a, b in zip(current, self._snapshot, strict=True)):
                _fail("Child requirement family scope changed after construction.")
        else:
            object.__setattr__(self, "_snapshot", current)

    def _validated(self):
        if type(self) is not ChildRequirementFamilyScope:
            _fail("Child requirement family scope has an unexpected type.")
        self.__post_init__()
        return self


_SCOPE = MappingProxyType({
    RequiredInternalShape.MOTIVE_FIVE_FAMILY_REQUIRED: (
        ChildFamilyCoverageState.NO_EXECUTABLE_FAMILY_COVERAGE, (),
        ("NORMAL_IMPULSE", "LEADING_DIAGONAL"),
        ("MOTIVE_FIVE_EXECUTABLE_FAMILY_COVERAGE_UNAVAILABLE",), "SOURCE_DEFINITION",
    ),
    RequiredInternalShape.CORRECTIVE_THREE_FAMILY_REQUIRED: (
        ChildFamilyCoverageState.PARTIAL_EXECUTABLE_FAMILY_COVERAGE,
        (FamilyEvaluationKind.SINGLE_ZIGZAG, FamilyEvaluationKind.FLAT),
        ("DOUBLE_ZIGZAG", "TRIPLE_ZIGZAG", "WXY", "WXYXZ"),
        ("CORRECTIVE_THREE_COVERAGE_IS_NOT_EXHAUSTIVE",), "SOURCE_DEFINITION",
    ),
    RequiredInternalShape.CORRECTIVE_FAMILY_REQUIRED: (
        ChildFamilyCoverageState.PARTIAL_EXECUTABLE_FAMILY_COVERAGE,
        (FamilyEvaluationKind.SINGLE_ZIGZAG, FamilyEvaluationKind.FLAT, FamilyEvaluationKind.TRIANGLE),
        ("DOUBLE_ZIGZAG", "TRIPLE_ZIGZAG", "WXY", "WXYXZ"),
        ("CORRECTIVE_FAMILY_COVERAGE_IS_NOT_EXHAUSTIVE",), "SOURCE_DEFINITION",
    ),
    RequiredInternalShape.THREE_WAVE_STRUCTURE_REQUIRED: (
        ChildFamilyCoverageState.UNRESOLVED_COMPATIBILITY, (), (),
        ("THREE_WAVE_STRUCTURE_FAMILY_COMPATIBILITY_UNRESOLVED",), "UNRESOLVED",
    ),
})


def _scope(requirement, allowed):
    state, compatible, unavailable, blockers, source_class = _SCOPE[requirement.required_internal_shape]
    selected = tuple(kind for kind in compatible if kind in allowed)
    if compatible and not selected:
        state = ChildFamilyCoverageState.NO_EXECUTABLE_FAMILY_COVERAGE
        blockers = blockers + ("CALLER_SCOPE_EXCLUDES_COMPATIBLE_EXECUTABLE_FAMILIES",)
    return ChildRequirementFamilyScope(
        requirement, state, selected, unavailable, blockers, source_class,
        requirement.protected_refs,
    )


@dataclass(frozen=True, slots=True, eq=False)
class ChildCandidateFamilyEvaluation(metaclass=_SealedType):
    generated_child_evidence: GeneratedChildCandidateEvidence
    requirement_scope: ChildRequirementFamilyScope
    family_hypothesis_result: FamilyHypothesisBridgeResult | None
    evaluation_state: ChildCandidateFamilyEvaluationState
    family_validity_authority: bool = False
    requirement_satisfied: bool = False
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self):
        self.generated_child_evidence._validated()
        self.requirement_scope.__post_init__()
        if self.requirement_scope.internal_requirement is not self.generated_child_evidence.internal_requirement:
            _fail("Child evaluation lost exact requirement identity.")
        if self.family_hypothesis_result is not None:
            result = validate_family_hypothesis_bridge_result(self.family_hypothesis_result)
            if result.competing_candidate_set is not self.generated_child_evidence.competing_candidate_set:
                _fail("Child evaluation lost exact competing-set identity.")
        if type(self.evaluation_state) is not ChildCandidateFamilyEvaluationState:
            _fail("Child candidate family evaluation state has an unexpected type.")
        expected_state = ChildCandidateFamilyEvaluationState.NO_EXECUTABLE_COMPATIBLE_CHILD_FAMILY_HYPOTHESIS
        if self.family_hypothesis_result is not None and self.family_hypothesis_result.family_hypotheses:
            expected_state = (
                ChildCandidateFamilyEvaluationState.EXECUTABLE_CHILD_FAMILY_HYPOTHESES_EXHAUSTED
                if len(self.family_hypothesis_result.structurally_invalid_hypotheses)
                == len(self.family_hypothesis_result.family_hypotheses)
                else ChildCandidateFamilyEvaluationState.EXECUTABLE_CHILD_FAMILY_HYPOTHESES_RETAINED
            )
        if self.evaluation_state is not expected_state:
            _fail("Child candidate family evaluation state differs from exact bridge output.")
        if self.family_validity_authority or self.requirement_satisfied:
            _fail("Child family evaluation cannot validate or satisfy.")
        names = tuple(name for name in self.__dataclass_fields__ if name != "_snapshot")
        current = tuple(getattr(self, name) for name in names)
        if hasattr(self, "_snapshot"):
            if len(current) != len(self._snapshot) or any(a is not b for a, b in zip(current, self._snapshot, strict=True)):
                _fail("Child family evaluation changed after construction.")
        else:
            object.__setattr__(self, "_snapshot", current)

    def _validated(self):
        if type(self) is not ChildCandidateFamilyEvaluation:
            _fail("Child candidate family evaluation has an unexpected type.")
        self.__post_init__()
        return self


@dataclass(frozen=True, slots=True, eq=False)
class RecursiveChildFamilyEvaluationRequest(metaclass=_SealedType):
    request_id: str
    requested_at_utc: str
    child_candidate_generation_result: RecursiveChildCandidateGenerationResult
    config: ChildFamilyEvaluationConfig
    provenance_refs: tuple[str, ...]
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self):
        _text(self.request_id, "request_id"); _text(self.requested_at_utc, "requested_at_utc")
        if type(self.child_candidate_generation_result) is not RecursiveChildCandidateGenerationResult:
            _fail("Request requires one exact child-generation result.")
        self.child_candidate_generation_result._validated()
        if type(self.config) is not ChildFamilyEvaluationConfig: _fail("Request config has an unexpected type.")
        self.config._validated(); _refs(self.provenance_refs)
        names = tuple(name for name in self.__dataclass_fields__ if name != "_snapshot")
        current = tuple(getattr(self, name) for name in names)
        if hasattr(self, "_snapshot"):
            if len(current) != len(self._snapshot) or any(a is not b for a, b in zip(current, self._snapshot, strict=True)):
                _fail("Recursive child-family request changed after construction.")
        else:
            object.__setattr__(self, "_snapshot", current)

    def _validated(self):
        if type(self) is not RecursiveChildFamilyEvaluationRequest:
            _fail("Recursive child-family request has an unexpected type.")
        self.__post_init__()
        return self


@dataclass(frozen=True, slots=True, eq=False, init=False, weakref_slot=True)
class RecursiveChildFamilyEvaluationResult(metaclass=_SealedType):
    request: RecursiveChildFamilyEvaluationRequest
    requirement_scopes: tuple[ChildRequirementFamilyScope, ...]
    child_evaluations: tuple[ChildCandidateFamilyEvaluation, ...]
    family_hypotheses: tuple[object, ...]
    structurally_invalid_hypotheses: tuple[object, ...]
    unresolved_hypotheses: tuple[object, ...]
    reviewed_scope_hypotheses: tuple[object, ...]
    blockers: tuple[str, ...]
    provenance_refs: tuple[str, ...]
    _snapshot: tuple[object, ...]

    def __init__(self, *args, **kwargs):
        raise TypeError("Recursive child-family results are factory-only.")

    def _validated(self):
        if type(self) is not RecursiveChildFamilyEvaluationResult or _ISSUED.get(self) is not self.child_evaluations:
            _fail("Recursive child-family result is unissued or malformed.")
        current = tuple(getattr(self, n) for n in self.__dataclass_fields__ if n != "_snapshot")
        if len(current) != len(self._snapshot) or any(a is not b for a, b in zip(current, self._snapshot, strict=True)): _fail("Recursive child-family result changed after issuance.")
        self.request._validated()
        for item in self.child_evaluations: item._validated()
        return self


_ISSUED: weakref.WeakKeyDictionary[RecursiveChildFamilyEvaluationResult, tuple[ChildCandidateFamilyEvaluation, ...]] = weakref.WeakKeyDictionary()


def evaluate_recursive_child_family_hypotheses(request, methodology_kernel):
    """Preflight all bounds, then perform exactly one existing-bridge layer."""
    if type(request) is not RecursiveChildFamilyEvaluationRequest: _fail("Evaluation requires one exact request.")
    request._validated()
    if type(methodology_kernel) is not MethodologyKernel: _fail("Evaluation requires one exact MethodologyKernel.")
    evidence = request.child_candidate_generation_result.generated_child_evidence
    config = request.config
    if len(evidence) > config.max_requirements_processed or len(evidence) > config.max_child_candidate_sets_processed:
        raise RecursiveChildFamilyEvaluationLimitExceeded("Requirement or child-set preflight bound exceeded.")
    candidate_count = sum(len(item.competing_candidate_set.ordered_candidates) for item in evidence)
    if candidate_count > config.max_child_candidates_processed:
        raise RecursiveChildFamilyEvaluationLimitExceeded("Child-candidate preflight bound exceeded.")
    scopes = tuple(_scope(item.internal_requirement, set(config.allowed_family_kinds)) for item in evidence)
    demands = tuple(estimate_family_hypothesis_demand(item.competing_candidate_set, scope.compatible_executable_family_kinds) for item, scope in zip(evidence, scopes, strict=True))
    if any(per > config.max_family_hypotheses_per_child_candidate for _, per in demands):
        raise RecursiveChildFamilyEvaluationLimitExceeded("Per-child family-hypothesis preflight bound exceeded.")
    total = sum(count for count, _ in demands)
    if total > config.max_total_child_family_hypotheses or total > config.max_total_methodology_evaluations:
        raise RecursiveChildFamilyEvaluationLimitExceeded("Total family/methodology preflight bound exceeded.")
    evaluations = []
    for index, (item, scope) in enumerate(zip(evidence, scopes, strict=True), 1):
        result = None
        if scope.compatible_executable_family_kinds:
            result = build_family_evaluation_hypotheses(FamilyHypothesisBridgeRequest(
                f"{request.request_id}:child:{index}", request.requested_at_utc,
                item.competing_candidate_set, scope.compatible_executable_family_kinds,
                request.provenance_refs + item.provenance_refs + scope.protected_refs,
            ), methodology_kernel)
        state = ChildCandidateFamilyEvaluationState.NO_EXECUTABLE_COMPATIBLE_CHILD_FAMILY_HYPOTHESIS
        if result is not None and result.family_hypotheses:
            state = (
                ChildCandidateFamilyEvaluationState.EXECUTABLE_CHILD_FAMILY_HYPOTHESES_EXHAUSTED
                if len(result.structurally_invalid_hypotheses) == len(result.family_hypotheses)
                else ChildCandidateFamilyEvaluationState.EXECUTABLE_CHILD_FAMILY_HYPOTHESES_RETAINED
            )
        evaluations.append(ChildCandidateFamilyEvaluation(item, scope, result, state))
    evaluations_t = tuple(evaluations)
    results = tuple(item.family_hypothesis_result for item in evaluations_t if item.family_hypothesis_result is not None)
    hypotheses = tuple(h for result in results for h in result.family_hypotheses)
    values = {
        "request": request, "requirement_scopes": scopes, "child_evaluations": evaluations_t,
        "family_hypotheses": hypotheses,
        "structurally_invalid_hypotheses": tuple(h for result in results for h in result.structurally_invalid_hypotheses),
        "unresolved_hypotheses": tuple(h for result in results for h in result.unresolved_hypotheses),
        "reviewed_scope_hypotheses": tuple(h for result in results for h in result.reviewed_scope_hypotheses),
        "blockers": tuple(dict.fromkeys(b for scope in scopes for b in scope.blockers)),
        "provenance_refs": request.provenance_refs,
    }
    result = object.__new__(RecursiveChildFamilyEvaluationResult)
    for name, value in values.items(): object.__setattr__(result, name, value)
    object.__setattr__(result, "_snapshot", tuple(values.values()))
    _ISSUED[result] = evaluations_t
    return result._validated()


def validate_recursive_child_family_evaluation_result(result):
    if type(result) is not RecursiveChildFamilyEvaluationResult: _fail("Expected one exact recursive child-family result.")
    return result._validated()


__all__ = [name for name in globals() if name.isupper() or name.startswith("Child") or name.startswith("Recursive") or name.startswith("evaluate_") or name.startswith("validate_")]
