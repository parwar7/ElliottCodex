"""Hypothesis-only Normal Impulse fanout with existing P004 delegation.

The module interprets an exact neutral five-segment candidate only as an
``evaluate-as NORMAL_IMPULSE`` scope.  It binds five hypothesis-local roles,
delegates the already-approved P004 fact through ``MethodologyKernel``, and
delegates bounded P005 percentage sufficiency separately, and keeps full P005,
P006, complete-family proof, degree, rank, and terminality absent.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import StrEnum
from typing import NoReturn
import weakref

from elliott_methodology_kernel import (
    AnalyzedWaveSubject,
    BoundedManualChartAnalysisRequest,
    BoundedManualChartAnalysisResult,
    CandidateScope,
    CertifiedStructuralInvalidity,
    ImpulseDirection,
    ManualP004Wave2OriginFact,
    MethodologyKernel,
    NormalImpulseFiveSlotCandidateView,
    OrderedChildBinding,
    P004Result,
    P005PercentageSufficiencyInput,
    P005PercentageSufficiencyResult,
    SubjectBoundObservedPriceObservation,
    SubjectBoundObservedPriceEndpointPair,
    RuleCheckStatus,
    certify_structural_invalidity,
)

from .candidate_generation import (
    CandidateHypothesisShape,
    GeneratedCandidateHypothesis,
)
from ..market_data.geometric_pivots import GeometricPivotState
from .competing_candidates import (
    CompetingCandidateSetResult,
    validate_competing_candidate_set_result,
)
from .family_hypotheses import (
    FamilyHypothesisBridgeResult,
    validate_family_hypothesis_bridge_result,
)
from .family_internal_subdivisions import RequiredInternalShape
from .recursive_child_candidate_generation import (
    GeneratedChildCandidateEvidence,
    RecursiveChildCandidateGenerationResult,
)


ARTIFACT_CLASSIFICATION = "PROJECT_ANALYSIS_INFRASTRUCTURE"
EVALUATION_SCOPE_CLASSIFICATION = "SOURCE_DERIVED_EVALUATION_SCOPE"
ROLE_CLASSIFICATION = "HYPOTHESIS_ROLE_METADATA"
EXECUTION_CLASSIFICATION = "HYPOTHESIS_CONDITIONAL_STRUCTURAL_TEST"
FIVE_SEGMENTS_IS_NOT_NORMAL_IMPULSE = True
P004_PASS_IS_NOT_FAMILY_VALIDITY = True
P004_FAILURE_IS_HYPOTHESIS_LOCAL = True
TIMEFRAME_IS_NOT_DEGREE = True
SOURCE_DERIVED_BASE_CASE_NOT_FOUND = "SOURCE_DERIVED_BASE_CASE_NOT_FOUND"
_MAX_EVALUATIONS = 100_000
_ROLES = ("1", "2", "3", "4", "5")
_P004_BEHAVIOR_ID = "P004_NORMAL_IMPULSE_WAVE2_ORIGIN"


class NormalImpulsePartialEvaluationError(ValueError):
    """Fail-closed Normal Impulse partial-evaluation contract error."""


class NormalImpulsePartialEvaluationLimitExceeded(NormalImpulsePartialEvaluationError):
    """Raised before any partial result is issued when a cap is exceeded."""


class NormalImpulseFamilyScope(StrEnum):
    NORMAL_IMPULSE = "NORMAL_IMPULSE"


class NormalImpulseEvaluationSourceKind(StrEnum):
    PARENT_FAMILY_BRIDGE = "PARENT_FAMILY_BRIDGE"
    RECURSIVE_CHILD_CANDIDATE_GENERATION = "RECURSIVE_CHILD_CANDIDATE_GENERATION"


class NormalImpulseMethodologyDependency(StrEnum):
    P005_UNRESOLVED_METHODOLOGY_DEPENDENCY = "P005_UNRESOLVED_METHODOLOGY_DEPENDENCY"
    P006_UNRESOLVED_METHODOLOGY_DEPENDENCY_CONFLICT = (
        "P006_UNRESOLVED_METHODOLOGY_DEPENDENCY_CONFLICT"
    )
    COMPLETE_FAMILY_VALIDATION_UNAVAILABLE = "COMPLETE_FAMILY_VALIDATION_UNAVAILABLE"


class NormalImpulsePartialEvaluationState(StrEnum):
    P004_SATISFIED_WITH_UNRESOLVED_METHODOLOGY_DEPENDENCIES = (
        "P004_SATISFIED_WITH_UNRESOLVED_METHODOLOGY_DEPENDENCIES"
    )
    P004_VIOLATED_STRUCTURALLY_INVALID_HYPOTHESIS = (
        "P004_VIOLATED_STRUCTURALLY_INVALID_HYPOTHESIS"
    )
    P004_UNRESOLVED_WITH_UNRESOLVED_METHODOLOGY_DEPENDENCIES = (
        "P004_UNRESOLVED_WITH_UNRESOLVED_METHODOLOGY_DEPENDENCIES"
    )


class _Sealed(type):
    def __new__(mcls, name, bases, namespace, **kwargs):
        if any(isinstance(base, mcls) for base in bases):
            raise TypeError("Normal Impulse partial-evaluation contracts cannot be subclassed.")
        return super().__new__(mcls, name, bases, namespace, **kwargs)


def _fail(message: str) -> NoReturn:
    raise NormalImpulsePartialEvaluationError(message)


def _text(value: object, name: str) -> str:
    if type(value) is not str or not value.strip():
        _fail(f"{name} must be one exact non-blank string.")
    return value


def _refs(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or any(type(item) is not str or not item.strip() for item in value):
        _fail("provenance_refs must be one exact tuple of non-blank strings.")
    return value


def _cap(value: object, name: str) -> int:
    if type(value) is not int or not 1 <= value <= _MAX_EVALUATIONS:
        _fail(f"{name} must be one exact positive integer within its operational bound.")
    return value


def _validate_source(source: object):
    if type(source) is FamilyHypothesisBridgeResult:
        return validate_family_hypothesis_bridge_result(source)
    if type(source) is RecursiveChildCandidateGenerationResult:
        return source._validated()
    _fail("source must be one exact approved parent bridge or recursive child-generation result.")


@dataclass(frozen=True, slots=True, eq=False)
class NormalImpulsePartialEvaluationRequest(metaclass=_Sealed):
    request_id: str
    requested_at_utc: str
    source: FamilyHypothesisBridgeResult | RecursiveChildCandidateGenerationResult
    max_normal_impulse_hypotheses: int
    max_p004_evaluations: int
    max_total_partial_family_evaluations: int
    provenance_refs: tuple[str, ...]
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self):
        _text(self.request_id, "request_id")
        _text(self.requested_at_utc, "requested_at_utc")
        _validate_source(self.source)
        _cap(self.max_normal_impulse_hypotheses, "max_normal_impulse_hypotheses")
        _cap(self.max_p004_evaluations, "max_p004_evaluations")
        _cap(self.max_total_partial_family_evaluations, "max_total_partial_family_evaluations")
        _refs(self.provenance_refs)
        current = tuple(getattr(self, name) for name in self.__dataclass_fields__ if name != "_snapshot")
        if hasattr(self, "_snapshot"):
            if len(current) != len(self._snapshot) or any(
                observed is not expected
                for observed, expected in zip(current, self._snapshot, strict=True)
            ):
                _fail("Normal Impulse partial-evaluation request changed after construction.")
        else:
            object.__setattr__(self, "_snapshot", current)

    def _validated(self):
        if type(self) is not NormalImpulsePartialEvaluationRequest:
            _fail("Normal Impulse request has an unexpected type.")
        self.__post_init__()
        return self

    def __copy__(self):
        return self._validated()

    def __deepcopy__(self, memo):
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol):
        raise TypeError("Normal Impulse requests cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False, init=False, weakref_slot=True)
class NormalImpulseRoleBinding(metaclass=_Sealed):
    hypothesis_id: str
    generated_candidate: GeneratedCandidateHypothesis
    five_slot_view: NormalImpulseFiveSlotCandidateView
    child_index: int
    component_role: str
    child_subject: AnalyzedWaveSubject
    start_boundary: object
    end_boundary: object
    provenance_refs: tuple[str, ...]
    hypothesis_role_metadata: bool
    wave_validity_authority: bool
    degree_authority: bool
    _snapshot: tuple[object, ...]

    def __init__(self, *args, **kwargs):
        raise TypeError("Normal Impulse role bindings are created only by the evaluator.")

    def _validated(self):
        if type(self) is not NormalImpulseRoleBinding or _ISSUED_ROLES.get(self) is not self.generated_candidate:
            _fail("Normal Impulse role binding is unissued or malformed.")
        current = tuple(getattr(self, name) for name in self.__dataclass_fields__ if name != "_snapshot")
        if len(current) != len(self._snapshot) or any(a is not b for a, b in zip(current, self._snapshot, strict=True)):
            _fail("Normal Impulse role binding changed after issuance.")
        if type(self.generated_candidate) is not GeneratedCandidateHypothesis:
            _fail("Role binding lost its exact generated candidate.")
        self.generated_candidate._validated()
        _validate_issued_view(self.five_slot_view, self.generated_candidate)
        if type(self.child_index) is not int or not 0 <= self.child_index < 5:
            _fail("Role index is outside the five-slot scope.")
        if self.component_role != _ROLES[self.child_index]:
            _fail("Role order differs from the protected five-position sequence.")
        if self.child_subject is not self.five_slot_view.binding.ordered_children[self.child_index]:
            _fail("Role child identity differs from the five-slot view.")
        pivots = self.generated_candidate.ordered_selected_pivots
        if self.start_boundary is not pivots[self.child_index] or self.end_boundary is not pivots[self.child_index + 1]:
            _fail("Role boundary identity differs from the exact neutral candidate.")
        if self.hypothesis_role_metadata is not True or self.wave_validity_authority or self.degree_authority:
            _fail("Normal Impulse roles cannot carry wave or degree authority.")
        _refs(self.provenance_refs)
        return self

    def __reduce_ex__(self, protocol):
        raise TypeError("Normal Impulse role bindings cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False, init=False, weakref_slot=True)
class NormalImpulseEvaluationHypothesis(metaclass=_Sealed):
    hypothesis_id: str
    source_kind: NormalImpulseEvaluationSourceKind
    source: FamilyHypothesisBridgeResult | RecursiveChildCandidateGenerationResult
    generated_child_evidence: GeneratedChildCandidateEvidence | None
    competing_candidate_set: CompetingCandidateSetResult
    generated_candidate: GeneratedCandidateHypothesis
    five_slot_view: NormalImpulseFiveSlotCandidateView
    role_bindings: tuple[NormalImpulseRoleBinding, ...]
    family_scope: NormalImpulseFamilyScope
    provenance_refs: tuple[str, ...]
    hypothesis_only: bool
    family_validity_authority: bool
    wave_validity_authority: bool
    completion_authority: bool
    terminality_authority: bool
    degree_authority: bool
    ranking_authority: bool
    _snapshot: tuple[object, ...]

    def __init__(self, *args, **kwargs):
        raise TypeError("Normal Impulse hypotheses are created only by the evaluator.")

    def _validated(self):
        if type(self) is not NormalImpulseEvaluationHypothesis or _ISSUED_HYPOTHESES.get(self) is not self.generated_candidate:
            _fail("Normal Impulse hypothesis is unissued or malformed.")
        current = tuple(getattr(self, name) for name in self.__dataclass_fields__ if name != "_snapshot")
        if len(current) != len(self._snapshot) or any(a is not b for a, b in zip(current, self._snapshot, strict=True)):
            _fail("Normal Impulse hypothesis changed after issuance.")
        original_binding = _validate_issued_view(self.five_slot_view, self.generated_candidate)
        _validate_source(self.source)
        validate_competing_candidate_set_result(self.competing_candidate_set)
        if type(self.generated_candidate) is not GeneratedCandidateHypothesis:
            _fail("Hypothesis candidate has an unexpected type.")
        self.generated_candidate._validated()
        if self.generated_candidate.candidate_shape is not CandidateHypothesisShape.FIVE_SEGMENT_HYPOTHESIS:
            _fail("Only an exact five-segment neutral candidate may form this hypothesis.")
        if not any(self.generated_candidate is item for item in self.competing_candidate_set.ordered_candidates):
            _fail("Hypothesis candidate is foreign to its exact competing set.")
        if type(self.source) is FamilyHypothesisBridgeResult:
            if self.competing_candidate_set is not self.source.competing_candidate_set or not any(
                item.generated_candidate is self.generated_candidate and item.child_binding is original_binding
                for item in self.source.candidate_evaluations
            ):
                _fail("Normal Impulse parent binding ancestry changed.")
        elif not any(
            item is self.generated_child_evidence and item.competing_candidate_set is self.competing_candidate_set
            for item in self.source.generated_child_evidence
        ):
            _fail("Normal Impulse recursive-child ancestry changed.")
        if type(self.role_bindings) is not tuple or len(self.role_bindings) != 5:
            _fail("Normal Impulse hypothesis requires five exact role bindings.")
        for index, binding in enumerate(self.role_bindings):
            binding._validated()
            if (
                binding.generated_candidate is not self.generated_candidate
                or binding.child_index != index
                or binding.five_slot_view is not self.five_slot_view
                or binding.hypothesis_id is not self.hypothesis_id
            ):
                _fail("Normal Impulse role membership or order changed.")
        if self.family_scope is not NormalImpulseFamilyScope.NORMAL_IMPULSE:
            _fail("Normal Impulse family scope changed.")
        if self.hypothesis_only is not True or any((self.family_validity_authority, self.wave_validity_authority, self.completion_authority, self.terminality_authority, self.degree_authority, self.ranking_authority)):
            _fail("Normal Impulse hypothesis cannot carry validity, completion, terminality, degree, or rank authority.")
        _refs(self.provenance_refs)
        return self

    def __reduce_ex__(self, protocol):
        raise TypeError("Normal Impulse hypotheses cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False, init=False, weakref_slot=True)
class NormalImpulsePartialEvaluation(metaclass=_Sealed):
    hypothesis: NormalImpulseEvaluationHypothesis
    p004_fact: ManualP004Wave2OriginFact
    bounded_request: BoundedManualChartAnalysisRequest
    bounded_result: BoundedManualChartAnalysisResult
    p004_result: P004Result
    p005_input: P005PercentageSufficiencyInput
    p005_result: P005PercentageSufficiencyResult
    state: NormalImpulsePartialEvaluationState
    unresolved_dependencies: tuple[NormalImpulseMethodologyDependency, ...]
    structural_invalidity_certificate: CertifiedStructuralInvalidity | None
    provenance_refs: tuple[str, ...]
    family_validity_authority: bool
    complete_methodology_review_authority: bool
    requirement_satisfaction_authority: bool
    _snapshot: tuple[object, ...]

    def __init__(self, *args, **kwargs):
        raise TypeError("Normal Impulse evaluations are created only by the evaluator.")

    def _validated(self):
        if type(self) is not NormalImpulsePartialEvaluation or _ISSUED_EVALUATIONS.get(self) is not self.p004_result:
            _fail("Normal Impulse evaluation is unissued or malformed.")
        current = tuple(getattr(self, name) for name in self.__dataclass_fields__ if name != "_snapshot")
        if len(current) != len(self._snapshot) or any(a is not b for a, b in zip(current, self._snapshot, strict=True)):
            _fail("Normal Impulse evaluation changed after issuance.")
        self.hypothesis._validated()
        if type(self.p005_input) is not P005PercentageSufficiencyInput or type(self.p005_result) is not P005PercentageSufficiencyResult:
            _fail("Exact P005 sufficiency snapshot and result required.")
        self.p005_result.validated()
        if (
            self.p005_result.input_snapshot is not self.p005_input
            or self.p005_input.five_slot_view is not self.hypothesis.five_slot_view
            or self.p005_input.observation_snapshot is not self.hypothesis.generated_candidate.source_observations
            or self.p005_input.direction is not self.p004_fact.direction
        ):
            _fail("P005 snapshot lost its exact hypothesis ancestry.")
        for index, role in enumerate(self.hypothesis.role_bindings[::2]):
            pair = self.p005_input.endpoint_pairs[index]
            if (
                pair.subject is not role.child_subject
                or pair.proposed_start.price is not role.start_boundary.observed_price
                or pair.proposed_end.price is not role.end_boundary.observed_price
                or self.p005_input.endpoint_identity_refs[2 * index] is not role.start_boundary
                or self.p005_input.endpoint_identity_refs[2 * index + 1] is not role.end_boundary
            ):
                _fail("P005 exact role endpoint binding changed.")
        if type(self.p004_fact) is not ManualP004Wave2OriginFact:
            _fail("Evaluation requires the exact existing P004 fact type.")
        if type(self.bounded_request) is not BoundedManualChartAnalysisRequest or type(self.bounded_result) is not BoundedManualChartAnalysisResult:
            _fail("Evaluation requires exact existing bounded methodology objects.")
        if (
            self.bounded_request.child_binding is not self.hypothesis.five_slot_view.binding
            or self.bounded_request.subject is not self.hypothesis.generated_candidate.subject
        ):
            _fail("P004 request lost the exact hypothesis binding or candidate subject.")
        copy.copy(self.bounded_request)
        copy.copy(self.bounded_result)
        if self.bounded_request.manual_behavior_facts != (self.p004_fact,):
            _fail("Only the exact existing P004 fact may be delegated.")
        if type(self.p004_result) is not P004Result or self.p004_result.behavior_id != _P004_BEHAVIOR_ID:
            _fail("Evaluation lost the exact existing P004 result.")
        if self.p004_result.status is RuleCheckStatus.RULE_VIOLATED:
            if (
                type(self.structural_invalidity_certificate)
                is not CertifiedStructuralInvalidity
                or self.structural_invalidity_certificate.origin is not self.p004_result
            ):
                _fail("P004 violation must retain one genuine certificate for its exact origin.")
        elif self.structural_invalidity_certificate is not None:
            _fail("Only an exact P004 violation may carry structural invalidity.")
        expected_state = _state(self.p004_result.status)
        if self.state is not expected_state:
            _fail("Partial execution state differs from the exact P004 result.")
        expected_dependencies = tuple(NormalImpulseMethodologyDependency)
        if self.unresolved_dependencies != expected_dependencies:
            _fail("P005/P006/complete-family blockers changed or were hidden.")
        if any((self.family_validity_authority, self.complete_methodology_review_authority, self.requirement_satisfaction_authority)):
            _fail("Partial P004 execution cannot validate a family or satisfy a requirement.")
        _refs(self.provenance_refs)
        return self

    def __reduce_ex__(self, protocol):
        raise TypeError("Normal Impulse evaluations cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False, init=False, weakref_slot=True)
class NormalImpulsePartialEvaluationResult(metaclass=_Sealed):
    request: NormalImpulsePartialEvaluationRequest
    hypotheses: tuple[NormalImpulseEvaluationHypothesis, ...]
    evaluations: tuple[NormalImpulsePartialEvaluation, ...]
    structurally_invalid_hypotheses: tuple[NormalImpulseEvaluationHypothesis, ...]
    unresolved_hypotheses: tuple[NormalImpulseEvaluationHypothesis, ...]
    p004_certificates: tuple[CertifiedStructuralInvalidity, ...]
    diagnostics: tuple[str, ...]
    provenance_refs: tuple[str, ...]
    validated_normal_impulses: int
    validated_motive_families: int
    ranking_authority: bool
    _snapshot: tuple[object, ...]

    def __init__(self, *args, **kwargs):
        raise TypeError("Normal Impulse results are created only by the evaluator.")

    def _validated(self):
        if type(self) is not NormalImpulsePartialEvaluationResult or _ISSUED_RESULTS.get(self) is not self.evaluations:
            _fail("Normal Impulse result is unissued or malformed.")
        current = tuple(getattr(self, name) for name in self.__dataclass_fields__ if name != "_snapshot")
        if len(current) != len(self._snapshot) or any(a is not b for a, b in zip(current, self._snapshot, strict=True)):
            _fail("Normal Impulse result changed after issuance.")
        self.request._validated()
        if len(self.hypotheses) != len(self.evaluations):
            _fail("Normal Impulse hypothesis/evaluation counts differ.")
        for hypothesis, evaluation in zip(self.hypotheses, self.evaluations, strict=True):
            hypothesis._validated()
            evaluation._validated()
            if evaluation.hypothesis is not hypothesis:
                _fail("Normal Impulse hypothesis/evaluation order changed.")
        invalid = tuple(item.hypothesis for item in self.evaluations if item.state is NormalImpulsePartialEvaluationState.P004_VIOLATED_STRUCTURALLY_INVALID_HYPOTHESIS)
        unresolved = tuple(item.hypothesis for item in self.evaluations if item.state is not NormalImpulsePartialEvaluationState.P004_VIOLATED_STRUCTURALLY_INVALID_HYPOTHESIS)
        certificates = tuple(item.structural_invalidity_certificate for item in self.evaluations if item.structural_invalidity_certificate is not None)
        for observed, expected, name in ((self.structurally_invalid_hypotheses, invalid, "invalid"), (self.unresolved_hypotheses, unresolved, "unresolved"), (self.p004_certificates, certificates, "certificate")):
            if len(observed) != len(expected) or any(a is not b for a, b in zip(observed, expected, strict=True)):
                _fail(f"Normal Impulse {name} view changed.")
        if self.validated_normal_impulses != 0 or self.validated_motive_families != 0 or self.ranking_authority:
            _fail("Partial Normal Impulse evaluation cannot validate or rank.")
        _refs(self.provenance_refs)
        return self

    def __reduce_ex__(self, protocol):
        raise TypeError("Normal Impulse results cannot be pickled.")


_ISSUED_ROLES: weakref.WeakKeyDictionary[NormalImpulseRoleBinding, GeneratedCandidateHypothesis] = weakref.WeakKeyDictionary()
_ISSUED_HYPOTHESES: weakref.WeakKeyDictionary[NormalImpulseEvaluationHypothesis, GeneratedCandidateHypothesis] = weakref.WeakKeyDictionary()
_ISSUED_EVALUATIONS: weakref.WeakKeyDictionary[NormalImpulsePartialEvaluation, P004Result] = weakref.WeakKeyDictionary()
_ISSUED_RESULTS: weakref.WeakKeyDictionary[NormalImpulsePartialEvaluationResult, tuple[NormalImpulsePartialEvaluation, ...]] = weakref.WeakKeyDictionary()
# Values contain no view reference, so the weak key can expire with its hypothesis.
# Capture once in the factory; validation never writes or refreshes this evidence.
_ISSUED_VIEWS: weakref.WeakKeyDictionary[NormalImpulseFiveSlotCandidateView, tuple[object, ...]] = weakref.WeakKeyDictionary()


def _validate_issued_view(view, candidate) -> OrderedChildBinding:
    if type(view) is not NormalImpulseFiveSlotCandidateView or type(candidate) is not GeneratedCandidateHypothesis:
        _fail("Normal Impulse ancestry requires an exact issued view and candidate.")
    evidence = _ISSUED_VIEWS.get(view)
    if evidence is None:
        _fail("Normal Impulse view has no issuance-time binding evidence.")
    binding, binding_id, parent, children, subject_fields = evidence
    if (
        view.binding is not binding
        or binding.binding_id is not binding_id
        or binding.parent_subject is not parent
        or candidate.subject is not parent
        or binding.ordered_children is not children
    ):
        _fail("Normal Impulse view binding, parent, or ordered children changed after issuance.")
    for subject, subject_id, provenance in subject_fields:
        if subject.subject_id is not subject_id or subject.observation_provenance_ref is not provenance:
            _fail("Normal Impulse subject identity metadata changed after issuance.")
    return binding


def _source_entries(request: NormalImpulsePartialEvaluationRequest):
    if type(request.source) is FamilyHypothesisBridgeResult:
        return tuple(
            (request.source.competing_candidate_set, item.generated_candidate, item.child_binding, None)
            for item in request.source.candidate_evaluations
            if item.generated_candidate.candidate_shape is CandidateHypothesisShape.FIVE_SEGMENT_HYPOTHESIS
        )
    entries = []
    for evidence in request.source.generated_child_evidence:
        if evidence.internal_requirement.required_internal_shape is not RequiredInternalShape.MOTIVE_FIVE_FAMILY_REQUIRED:
            continue
        for candidate in evidence.competing_candidate_set.ordered_candidates:
            if candidate.candidate_shape is CandidateHypothesisShape.FIVE_SEGMENT_HYPOTHESIS:
                children = tuple(AnalyzedWaveSubject(
                    f"{candidate.candidate_id}:normal-impulse-proposed-child:{index + 1}",
                    f"candidate-segment:{candidate.candidate_id}:{index + 1}",
                ) for index in range(5))
                binding = OrderedChildBinding(
                    f"{candidate.candidate_id}:normal-impulse-proposed-direct-children",
                    candidate.subject,
                    children,
                )
                entries.append((evidence.competing_candidate_set, candidate, binding, evidence))
    return tuple(entries)


def _state(status: RuleCheckStatus) -> NormalImpulsePartialEvaluationState:
    if status is RuleCheckStatus.RULE_VIOLATED:
        return NormalImpulsePartialEvaluationState.P004_VIOLATED_STRUCTURALLY_INVALID_HYPOTHESIS
    if status is RuleCheckStatus.RULE_SATISFIED:
        return NormalImpulsePartialEvaluationState.P004_SATISFIED_WITH_UNRESOLVED_METHODOLOGY_DEPENDENCIES
    return NormalImpulsePartialEvaluationState.P004_UNRESOLVED_WITH_UNRESOLVED_METHODOLOGY_DEPENDENCIES


def evaluate_normal_impulse_partial_scope(
    request: NormalImpulsePartialEvaluationRequest,
    methodology_kernel: MethodologyKernel,
) -> NormalImpulsePartialEvaluationResult:
    """Delegate P004 and separately bounded nonfatal P005 sufficiency."""
    if type(request) is not NormalImpulsePartialEvaluationRequest:
        _fail("Evaluator requires one exact Normal Impulse request.")
    request._validated()
    if type(methodology_kernel) is not MethodologyKernel:
        _fail("Evaluator requires one exact MethodologyKernel.")
    entries = _source_entries(request)
    demand = len(entries)
    if demand > request.max_normal_impulse_hypotheses:
        raise NormalImpulsePartialEvaluationLimitExceeded("Normal Impulse hypothesis preflight bound exceeded; no partial result was issued.")
    if demand > request.max_p004_evaluations:
        raise NormalImpulsePartialEvaluationLimitExceeded("P004 evaluation preflight bound exceeded; no partial result was issued.")
    if demand > request.max_total_partial_family_evaluations:
        raise NormalImpulsePartialEvaluationLimitExceeded("Partial-family evaluation preflight bound exceeded; no partial result was issued.")
    hypotheses = []
    evaluations = []
    source_kind = (
        NormalImpulseEvaluationSourceKind.PARENT_FAMILY_BRIDGE
        if type(request.source) is FamilyHypothesisBridgeResult
        else NormalImpulseEvaluationSourceKind.RECURSIVE_CHILD_CANDIDATE_GENERATION
    )
    for index, (candidate_set, candidate, binding, child_evidence) in enumerate(entries, 1):
        view = NormalImpulseFiveSlotCandidateView(binding)
        _ISSUED_VIEWS[view] = (
            binding, binding.binding_id, binding.parent_subject, binding.ordered_children,
            tuple((subject, subject.subject_id, subject.observation_provenance_ref)
                  for subject in (binding.parent_subject, *binding.ordered_children)),
        )
        _validate_issued_view(view, candidate)
        hypothesis_id = f"{request.request_id}:{candidate.candidate_id}:evaluate-as:NORMAL_IMPULSE"
        role_items = []
        for child_index, role in enumerate(_ROLES):
            values = {
                "hypothesis_id": hypothesis_id,
                "generated_candidate": candidate,
                "five_slot_view": view,
                "child_index": child_index,
                "component_role": role,
                "child_subject": binding.ordered_children[child_index],
                "start_boundary": candidate.ordered_selected_pivots[child_index],
                "end_boundary": candidate.ordered_selected_pivots[child_index + 1],
                "provenance_refs": request.provenance_refs + candidate.provenance_refs + (f"normal-impulse-hypothesis-role:{role}",),
                "hypothesis_role_metadata": True,
                "wave_validity_authority": False,
                "degree_authority": False,
            }
            item = object.__new__(NormalImpulseRoleBinding)
            for name, value in values.items():
                object.__setattr__(item, name, value)
            object.__setattr__(item, "_snapshot", tuple(values.values()))
            _ISSUED_ROLES[item] = candidate
            role_items.append(item._validated())
        roles = tuple(role_items)
        hypothesis_values = {
            "hypothesis_id": hypothesis_id,
            "source_kind": source_kind,
            "source": request.source,
            "generated_child_evidence": child_evidence,
            "competing_candidate_set": candidate_set,
            "generated_candidate": candidate,
            "five_slot_view": view,
            "role_bindings": roles,
            "family_scope": NormalImpulseFamilyScope.NORMAL_IMPULSE,
            "provenance_refs": request.provenance_refs + candidate.provenance_refs + (
                "docs/elliott/PATTERN_BRAIN.md#A-normal-impulse",
                "Sources_LOCKED/volume_01/Volume_01.srt@00:29:45.679-00:31:41.909",
                "evaluate-as:NORMAL_IMPULSE",
            ),
            "hypothesis_only": True,
            "family_validity_authority": False,
            "wave_validity_authority": False,
            "completion_authority": False,
            "terminality_authority": False,
            "degree_authority": False,
            "ranking_authority": False,
        }
        hypothesis = object.__new__(NormalImpulseEvaluationHypothesis)
        for name, value in hypothesis_values.items():
            object.__setattr__(hypothesis, name, value)
        object.__setattr__(hypothesis, "_snapshot", tuple(hypothesis_values.values()))
        _ISSUED_HYPOTHESES[hypothesis] = candidate
        hypothesis._validated()
        p0, p1, p2 = candidate.ordered_selected_pivots[:3]
        direction = ImpulseDirection.UP if p1.observed_price > p0.observed_price else ImpulseDirection.DOWN if p1.observed_price < p0.observed_price else ImpulseDirection.UNKNOWN
        fact = ManualP004Wave2OriginFact(
            CandidateScope.NORMAL_IMPULSE,
            direction,
            p0.observed_price,
            p2.observed_price,
        )
        bounded_request = BoundedManualChartAnalysisRequest(
            hypothesis_id,
            request.requested_at_utc,
            candidate.subject,
            candidate.candidate_id,
            (fact,),
            child_binding=binding,
            provenance_refs=hypothesis.provenance_refs + (
                "docs/elliott/SOURCE_EVIDENCE_MAP.json#P004",
                "hypothesis-conditional:P004",
            ),
        )
        bounded_result = methodology_kernel.analyze_bounded_manual_chart(bounded_request)
        trace = tuple(item for item in bounded_result.traceability if item.behavior_id == _P004_BEHAVIOR_ID)
        if len(trace) != 1 or type(trace[0].result_object) is not P004Result:
            _fail("Existing bounded methodology did not return one exact P004 result.")
        p004_result = trace[0].result_object
        endpoint_pairs = tuple(SubjectBoundObservedPriceEndpointPair(
            SubjectBoundObservedPriceObservation(role.child_subject, role.start_boundary.observed_price,
                                                 f"{role.start_boundary.pivot_id}:proposed-start"),
            SubjectBoundObservedPriceObservation(role.child_subject, role.end_boundary.observed_price,
                                                 f"{role.end_boundary.pivot_id}:proposed-end"),
        ) for role in roles[::2])
        endpoints = tuple(pivot for role in roles[::2] for pivot in (role.start_boundary, role.end_boundary))
        eligibility = tuple(
            True if pivot.state is GeometricPivotState.CONFIRMED_BY_GEOMETRY
            else False if pivot.state is GeometricPivotState.DEVELOPING else None
            for pivot in endpoints
        )
        p005_input = P005PercentageSufficiencyInput(
            view, direction, endpoint_pairs, candidate.source_observations,
            eligibility, hypothesis.provenance_refs, endpoints,
        )
        p005_result = methodology_kernel.evaluate_p005_percentage_sufficiency(p005_input)
        certificate = (
            certify_structural_invalidity(p004_result)
            if p004_result.status is RuleCheckStatus.RULE_VIOLATED
            else None
        )
        evaluation_values = {
            "hypothesis": hypothesis,
            "p004_fact": fact,
            "bounded_request": bounded_request,
            "bounded_result": bounded_result,
            "p004_result": p004_result,
            "p005_input": p005_input,
            "p005_result": p005_result,
            "state": _state(p004_result.status),
            "unresolved_dependencies": tuple(NormalImpulseMethodologyDependency),
            "structural_invalidity_certificate": certificate,
            "provenance_refs": hypothesis.provenance_refs + p004_result.protected_sources + (
                "P005:PERCENTAGE_SUFFICIENCY_ONLY_FULL_VALIDATION_UNRESOLVED",
                "P006:UNCHANGED_FROZEN_UNRESOLVED_CONFLICT",
                SOURCE_DERIVED_BASE_CASE_NOT_FOUND,
            ),
            "family_validity_authority": False,
            "complete_methodology_review_authority": False,
            "requirement_satisfaction_authority": False,
        }
        evaluation = object.__new__(NormalImpulsePartialEvaluation)
        for name, value in evaluation_values.items():
            object.__setattr__(evaluation, name, value)
        object.__setattr__(evaluation, "_snapshot", tuple(evaluation_values.values()))
        _ISSUED_EVALUATIONS[evaluation] = p004_result
        hypotheses.append(hypothesis)
        evaluations.append(evaluation._validated())
    hypotheses_t = tuple(hypotheses)
    evaluations_t = tuple(evaluations)
    values = {
        "request": request,
        "hypotheses": hypotheses_t,
        "evaluations": evaluations_t,
        "structurally_invalid_hypotheses": tuple(item.hypothesis for item in evaluations_t if item.state is NormalImpulsePartialEvaluationState.P004_VIOLATED_STRUCTURALLY_INVALID_HYPOTHESIS),
        "unresolved_hypotheses": tuple(item.hypothesis for item in evaluations_t if item.state is not NormalImpulsePartialEvaluationState.P004_VIOLATED_STRUCTURALLY_INVALID_HYPOTHESIS),
        "p004_certificates": tuple(item.structural_invalidity_certificate for item in evaluations_t if item.structural_invalidity_certificate is not None),
        "diagnostics": (
            "FIVE_SEGMENTS_IS_NOT_NORMAL_IMPULSE",
            "P004_AND_P005_PERCENTAGE_SUFFICIENCY_PARTIAL_EXECUTABLE_SCOPE",
            "P005_UNRESOLVED_METHODOLOGY_DEPENDENCY",
            "P006_UNRESOLVED_METHODOLOGY_DEPENDENCY_CONFLICT",
            "MOTIVE_FIVE_REQUIREMENT_NOT_SATISFIED",
            SOURCE_DERIVED_BASE_CASE_NOT_FOUND,
            "NO_DEGREE_RANKING_OR_FAMILY_CERTIFICATE",
        ),
        "provenance_refs": request.provenance_refs,
        "validated_normal_impulses": 0,
        "validated_motive_families": 0,
        "ranking_authority": False,
    }
    result = object.__new__(NormalImpulsePartialEvaluationResult)
    for name, value in values.items():
        object.__setattr__(result, name, value)
    object.__setattr__(result, "_snapshot", tuple(values.values()))
    _ISSUED_RESULTS[result] = evaluations_t
    return result._validated()


def validate_normal_impulse_partial_evaluation_result(result: object) -> NormalImpulsePartialEvaluationResult:
    if type(result) is not NormalImpulsePartialEvaluationResult:
        _fail("Expected one exact Normal Impulse partial-evaluation result.")
    return result._validated()


__all__ = [
    "ARTIFACT_CLASSIFICATION",
    "EVALUATION_SCOPE_CLASSIFICATION",
    "EXECUTION_CLASSIFICATION",
    "FIVE_SEGMENTS_IS_NOT_NORMAL_IMPULSE",
    "P004_FAILURE_IS_HYPOTHESIS_LOCAL",
    "P004_PASS_IS_NOT_FAMILY_VALIDITY",
    "ROLE_CLASSIFICATION",
    "SOURCE_DERIVED_BASE_CASE_NOT_FOUND",
    "TIMEFRAME_IS_NOT_DEGREE",
    "NormalImpulseEvaluationHypothesis",
    "NormalImpulseEvaluationSourceKind",
    "NormalImpulseFamilyScope",
    "NormalImpulseMethodologyDependency",
    "NormalImpulsePartialEvaluation",
    "NormalImpulsePartialEvaluationError",
    "NormalImpulsePartialEvaluationLimitExceeded",
    "NormalImpulsePartialEvaluationRequest",
    "NormalImpulsePartialEvaluationResult",
    "NormalImpulsePartialEvaluationState",
    "NormalImpulseRoleBinding",
    "evaluate_normal_impulse_partial_scope",
    "validate_normal_impulse_partial_evaluation_result",
]
