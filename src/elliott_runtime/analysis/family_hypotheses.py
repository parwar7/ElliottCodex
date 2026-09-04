"""Bounded evaluate-as bridge for source-supported family cardinalities.

The bridge creates proposed direct-child inputs and delegates them through the
existing bounded methodology API.  A family hypothesis is never a family
classification, and a reviewed cardinality is never complete family validity.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import NoReturn
import weakref

from elliott_methodology_kernel import (
    AnalyzedWaveSubject,
    BoundedManualChartAnalysisRequest,
    BoundedManualChartAnalysisResult,
    BoundedManualChartFinalSummary,
    ManualCardinalityBehavior,
    ManualDirectChildCardinalityFact,
    MethodologyKernel,
    OrderedChildBinding,
)

from .candidate_generation import (
    CandidateHypothesisShape,
    GeneratedCandidateHypothesis,
)
from .competing_candidates import (
    CompetingCandidateSetResult,
    validate_competing_candidate_set_result,
)


ARTIFACT_CLASSIFICATION = "PROJECT_ANALYSIS_INFRASTRUCTURE"
EVALUATION_SCOPE_CLASSIFICATION = "SOURCE_DERIVED_EVALUATION_SCOPE"
CHILD_HYPOTHESIS_CLASSIFICATION = "CALLER_OR_GENERATOR_SUPPLIED_CHILD_HYPOTHESIS"
FAN_OUT_ORDER_CLASSIFICATION = "PROJECT_OPERATIONAL_POLICY"
FAMILY_HYPOTHESIS_IS_NOT_CLASSIFICATION = True
EVALUATE_AS_IS_NOT_THIS_IS = True
CARDINALITY_MATCH_IS_NOT_FULL_FAMILY_VALIDITY = True
GEOMETRIC_PIVOT_IS_NOT_WAVE_ENDPOINT = True
TIMEFRAME_IS_NOT_DEGREE = True


class FamilyHypothesisBridgeError(ValueError):
    """Fail-closed family-hypothesis bridge contract error."""


class FamilyEvaluationKind(StrEnum):
    SINGLE_ZIGZAG = "SINGLE_ZIGZAG"
    FLAT = "FLAT"
    TRIANGLE = "TRIANGLE"
    ENDING_DIAGONAL = "ENDING_DIAGONAL"


class FamilyHypothesisDiagnosticCode(StrEnum):
    FAMILY_HYPOTHESES_CREATED = "FAMILY_HYPOTHESES_CREATED"
    MULTIPLE_FAMILIES_COEXIST = "MULTIPLE_FAMILIES_COEXIST"
    NO_COMPATIBLE_FAMILY_REQUESTED = "NO_COMPATIBLE_FAMILY_REQUESTED"
    CARDINALITY_SCOPE_REVIEWED = "CARDINALITY_SCOPE_REVIEWED"
    FAMILY_HYPOTHESES_STRUCTURALLY_INVALID = "FAMILY_HYPOTHESES_STRUCTURALLY_INVALID"
    FAMILY_HYPOTHESES_UNRESOLVED = "FAMILY_HYPOTHESES_UNRESOLVED"


class _SealedFamilyType(type):
    def __new__(
        mcls: type,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
        **kwargs: object,
    ) -> type:
        if any(isinstance(base, mcls) for base in bases):
            raise TypeError("Family-hypothesis infrastructure cannot be subclassed.")
        return super().__new__(mcls, name, bases, namespace, **kwargs)


def _fail(message: str) -> NoReturn:
    raise FamilyHypothesisBridgeError(message)


def _text(value: object, name: str) -> str:
    if type(value) is not str or value.strip() == "":
        _fail(f"{name} must be one exact non-blank string.")
    return value


def _refs(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or any(
        type(item) is not str or item.strip() == "" for item in value
    ):
        _fail("provenance_refs must be one exact tuple of non-blank strings.")
    return value


def _validate_kinds(value: object) -> tuple[FamilyEvaluationKind, ...]:
    if type(value) is not tuple or any(
        type(item) is not FamilyEvaluationKind for item in value
    ):
        _fail("allowed_family_kinds must be one exact tuple of exact family kinds.")
    if len(set(value)) != len(value):
        _fail("allowed_family_kinds cannot contain duplicates.")
    return value


@dataclass(frozen=True, slots=True, eq=False)
class FamilyHypothesisBridgeRequest(metaclass=_SealedFamilyType):
    bridge_id: str
    requested_at_utc: str
    competing_candidate_set: CompetingCandidateSetResult
    allowed_family_kinds: tuple[FamilyEvaluationKind, ...]
    provenance_refs: tuple[str, ...]
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        _text(self.bridge_id, "bridge_id")
        _text(self.requested_at_utc, "requested_at_utc")
        validate_competing_candidate_set_result(self.competing_candidate_set)
        _validate_kinds(self.allowed_family_kinds)
        _refs(self.provenance_refs)
        object.__setattr__(
            self,
            "_snapshot",
            (
                self.bridge_id,
                self.requested_at_utc,
                self.competing_candidate_set,
                self.allowed_family_kinds,
                self.provenance_refs,
            ),
        )

    def _validated(self) -> FamilyHypothesisBridgeRequest:
        if type(self) is not FamilyHypothesisBridgeRequest:
            _fail("Family bridge request must have its exact reviewed type.")
        current = (
            self.bridge_id,
            self.requested_at_utc,
            self.competing_candidate_set,
            self.allowed_family_kinds,
            self.provenance_refs,
        )
        if len(current) != len(self._snapshot) or any(
            observed is not expected
            for observed, expected in zip(current, self._snapshot, strict=True)
        ):
            _fail("Family bridge request changed after construction.")
        validate_competing_candidate_set_result(self.competing_candidate_set)
        _validate_kinds(self.allowed_family_kinds)
        _refs(self.provenance_refs)
        return self

    def __copy__(self) -> FamilyHypothesisBridgeRequest:
        return self._validated()

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> FamilyHypothesisBridgeRequest:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Family bridge requests cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False)
class FamilyHypothesisDiagnostic(metaclass=_SealedFamilyType):
    code: FamilyHypothesisDiagnosticCode
    count: int
    detail: str

    def __post_init__(self) -> None:
        if type(self.code) is not FamilyHypothesisDiagnosticCode:
            _fail("Family diagnostic code must have its exact reviewed type.")
        if type(self.count) is not int or self.count < 0:
            _fail("Family diagnostic count must be one non-negative exact integer.")
        _text(self.detail, "diagnostic detail")


@dataclass(frozen=True, slots=True, eq=False)
class ElliottFamilyEvaluationHypothesis(metaclass=_SealedFamilyType):
    hypothesis_id: str
    generated_candidate: GeneratedCandidateHypothesis
    family_kind: FamilyEvaluationKind
    parent_subject: AnalyzedWaveSubject
    ordered_child_subjects: tuple[AnalyzedWaveSubject, ...]
    child_binding: OrderedChildBinding
    manual_fact: ManualDirectChildCardinalityFact
    bounded_request: BoundedManualChartAnalysisRequest
    bounded_result: BoundedManualChartAnalysisResult
    provenance_refs: tuple[str, ...]
    hypothesis_only: bool = True
    family_validity_authority: bool = False
    completion_authority: bool = False
    degree_authority: bool = False
    ranking_authority: bool = False
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if (
            self.hypothesis_only is not True
            or self.family_validity_authority is not False
            or self.completion_authority is not False
            or self.degree_authority is not False
            or self.ranking_authority is not False
        ):
            _fail("Family hypotheses cannot carry validity, completion, degree, or rank authority.")
        _text(self.hypothesis_id, "hypothesis_id")
        if type(self.generated_candidate) is not GeneratedCandidateHypothesis:
            _fail("generated_candidate must have its exact reviewed type.")
        self.generated_candidate._validated()
        if type(self.family_kind) is not FamilyEvaluationKind:
            _fail("family_kind must have its exact reviewed type.")
        if self.parent_subject is not self.generated_candidate.subject:
            _fail("Family hypothesis parent must retain exact candidate subject identity.")
        if type(self.ordered_child_subjects) is not tuple or any(
            type(item) is not AnalyzedWaveSubject for item in self.ordered_child_subjects
        ):
            _fail("ordered_child_subjects must be one exact tuple of exact subjects.")
        if type(self.child_binding) is not OrderedChildBinding:
            _fail("child_binding must have its exact reviewed type.")
        if (
            self.child_binding.parent_subject is not self.parent_subject
            or len(self.child_binding.ordered_children) != len(self.ordered_child_subjects)
            or any(
                observed is not expected
                for observed, expected in zip(
                    self.child_binding.ordered_children,
                    self.ordered_child_subjects,
                    strict=True,
                )
            )
        ):
            _fail("Proposed child binding differs from exact child identities or order.")
        if type(self.manual_fact) is not ManualDirectChildCardinalityFact:
            _fail("manual_fact must be the exact existing cardinality fact type.")
        expected_behavior = _FAMILY_FACTS.get(self.family_kind)
        if self.manual_fact.behavior is not expected_behavior:
            _fail("Family hypothesis and exact cardinality selector differ.")
        if self.family_kind not in _SHAPE_FAMILIES[self.generated_candidate.candidate_shape]:
            _fail("Family hypothesis is incompatible with the neutral segment count.")
        if type(self.bounded_request) is not BoundedManualChartAnalysisRequest:
            _fail("bounded_request must have its exact existing type.")
        if type(self.bounded_result) is not BoundedManualChartAnalysisResult:
            _fail("bounded_result must have its exact existing type.")
        if (
            self.bounded_request.subject is not self.parent_subject
            or self.bounded_request.candidate_id != self.generated_candidate.candidate_id
            or self.bounded_request.child_binding is not self.child_binding
            or self.bounded_request.manual_behavior_facts != (self.manual_fact,)
            or self.bounded_result.subject is not self.parent_subject
            or self.bounded_result.candidate_id != self.generated_candidate.candidate_id
            or self.bounded_result.request_id != self.bounded_request.request_id
        ):
            _fail("Existing bounded methodology identities differ from the hypothesis.")
        try:
            copy.copy(self.bounded_request)
            copy.copy(self.bounded_result)
        except Exception as error:
            raise FamilyHypothesisBridgeError(
                "Existing bounded methodology request or result changed."
            ) from error
        _refs(self.provenance_refs)
        object.__setattr__(
            self,
            "_snapshot",
            tuple(
                getattr(self, name)
                for name in self.__dataclass_fields__
                if name != "_snapshot"
            ),
        )

    def _validated(self) -> ElliottFamilyEvaluationHypothesis:
        if type(self) is not ElliottFamilyEvaluationHypothesis:
            _fail("Family hypothesis must have its exact reviewed type.")
        current = tuple(
            getattr(self, name)
            for name in self.__dataclass_fields__
            if name != "_snapshot"
        )
        if len(current) != len(self._snapshot) or any(
            observed is not expected
            for observed, expected in zip(current, self._snapshot, strict=True)
        ):
            _fail("Family hypothesis changed after construction.")
        self.__post_init__()
        return self

    def __copy__(self) -> ElliottFamilyEvaluationHypothesis:
        return self._validated()

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> ElliottFamilyEvaluationHypothesis:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Family hypotheses cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False)
class CandidateFamilyEvaluation(metaclass=_SealedFamilyType):
    generated_candidate: GeneratedCandidateHypothesis
    ordered_child_subjects: tuple[AnalyzedWaveSubject, ...]
    child_binding: OrderedChildBinding
    family_hypotheses: tuple[ElliottFamilyEvaluationHypothesis, ...]

    def __post_init__(self) -> None:
        if type(self.generated_candidate) is not GeneratedCandidateHypothesis:
            _fail("Candidate evaluation must retain one exact generated candidate.")
        self.generated_candidate._validated()
        if type(self.ordered_child_subjects) is not tuple or any(
            type(item) is not AnalyzedWaveSubject for item in self.ordered_child_subjects
        ):
            _fail("Candidate evaluation children have an unexpected type.")
        if type(self.child_binding) is not OrderedChildBinding:
            _fail("Candidate evaluation binding has an unexpected type.")
        if type(self.family_hypotheses) is not tuple or any(
            type(item) is not ElliottFamilyEvaluationHypothesis
            for item in self.family_hypotheses
        ):
            _fail("Candidate family hypotheses have an unexpected type.")
        for item in self.family_hypotheses:
            item._validated()
            if (
                item.generated_candidate is not self.generated_candidate
                or item.ordered_child_subjects is not self.ordered_child_subjects
                or item.child_binding is not self.child_binding
            ):
                _fail("Candidate evaluation lost exact shared hypothesis identities.")


@dataclass(frozen=True, slots=True, eq=False, init=False, weakref_slot=True)
class FamilyHypothesisBridgeResult(metaclass=_SealedFamilyType):
    bridge_id: str
    competing_candidate_set: CompetingCandidateSetResult
    candidate_evaluations: tuple[CandidateFamilyEvaluation, ...]
    family_hypotheses: tuple[ElliottFamilyEvaluationHypothesis, ...]
    structurally_invalid_hypotheses: tuple[ElliottFamilyEvaluationHypothesis, ...]
    unresolved_hypotheses: tuple[ElliottFamilyEvaluationHypothesis, ...]
    reviewed_scope_hypotheses: tuple[ElliottFamilyEvaluationHypothesis, ...]
    diagnostics: tuple[FamilyHypothesisDiagnostic, ...]
    provenance_refs: tuple[str, ...]
    _snapshot: tuple[object, ...]

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("Family bridge results are created only by the bridge.")

    def _validated(self) -> FamilyHypothesisBridgeResult:
        if type(self) is not FamilyHypothesisBridgeResult:
            _fail("Family bridge result must have its exact reviewed type.")
        try:
            issued = _ISSUED_RESULTS.get(self)
            snapshot = object.__getattribute__(self, "_snapshot")
        except Exception as error:
            raise FamilyHypothesisBridgeError("Family bridge result is malformed.") from error
        current = tuple(
            getattr(self, name)
            for name in self.__dataclass_fields__
            if name != "_snapshot"
        )
        if issued is None or len(current) != len(snapshot) or any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            _fail("Family bridge result is unissued or changed after creation.")
        validate_competing_candidate_set_result(self.competing_candidate_set)
        if len(issued) != len(self.family_hypotheses) or any(
            observed is not expected
            for observed, expected in zip(self.family_hypotheses, issued, strict=True)
        ):
            _fail("Family hypothesis membership differs from issuance.")
        if len(self.candidate_evaluations) != len(self.competing_candidate_set.ordered_candidates):
            _fail("Every neutral candidate must retain one candidate-evaluation entry.")
        flattened = []
        for expected_candidate, evaluation in zip(
            self.competing_candidate_set.ordered_candidates,
            self.candidate_evaluations,
            strict=True,
        ):
            if type(evaluation) is not CandidateFamilyEvaluation:
                _fail("Candidate evaluation has an unexpected type.")
            evaluation.__post_init__()
            if evaluation.generated_candidate is not expected_candidate:
                _fail("Candidate evaluation order or identity changed.")
            flattened.extend(evaluation.family_hypotheses)
        if len(flattened) != len(self.family_hypotheses) or any(
            observed is not expected
            for observed, expected in zip(flattened, self.family_hypotheses, strict=True)
        ):
            _fail("Flattened family hypothesis order changed.")
        expected_views = {
            "structurally_invalid_hypotheses": BoundedManualChartFinalSummary.STRUCTURALLY_INVALID,
            "unresolved_hypotheses": BoundedManualChartFinalSummary.UNRESOLVED,
            "reviewed_scope_hypotheses": BoundedManualChartFinalSummary.CURRENT_SUPPLIED_SCOPE_REVIEWED,
        }
        for name, state in expected_views.items():
            expected = tuple(
                item for item in self.family_hypotheses
                if item.bounded_result.final_summary is state
            )
            observed = getattr(self, name)
            if len(observed) != len(expected) or any(
                item is not reference
                for item, reference in zip(observed, expected, strict=True)
            ):
                _fail(f"Family bridge {name} view changed.")
        if type(self.diagnostics) is not tuple or any(
            type(item) is not FamilyHypothesisDiagnostic for item in self.diagnostics
        ):
            _fail("Family bridge diagnostics have an unexpected type.")
        for item in self.diagnostics:
            item.__post_init__()
        _refs(self.provenance_refs)
        return self

    def __copy__(self) -> FamilyHypothesisBridgeResult:
        return self._validated()

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> FamilyHypothesisBridgeResult:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Family bridge results cannot be pickled.")


_ISSUED_RESULTS: weakref.WeakKeyDictionary[
    FamilyHypothesisBridgeResult,
    tuple[ElliottFamilyEvaluationHypothesis, ...],
] = weakref.WeakKeyDictionary()


_FAMILY_FACTS = MappingProxyType({
    FamilyEvaluationKind.SINGLE_ZIGZAG: ManualCardinalityBehavior.SINGLE_ZIGZAG,
    FamilyEvaluationKind.FLAT: ManualCardinalityBehavior.FLAT,
    FamilyEvaluationKind.TRIANGLE: ManualCardinalityBehavior.TRIANGLE,
    FamilyEvaluationKind.ENDING_DIAGONAL: ManualCardinalityBehavior.ENDING_DIAGONAL,
})


_SHAPE_FAMILIES = MappingProxyType({
    CandidateHypothesisShape.THREE_SEGMENT_HYPOTHESIS: (
        FamilyEvaluationKind.SINGLE_ZIGZAG,
        FamilyEvaluationKind.FLAT,
    ),
    CandidateHypothesisShape.FIVE_SEGMENT_HYPOTHESIS: (
        FamilyEvaluationKind.TRIANGLE,
        FamilyEvaluationKind.ENDING_DIAGONAL,
    ),
})


def _candidate_children(
    candidate: GeneratedCandidateHypothesis,
) -> tuple[tuple[AnalyzedWaveSubject, ...], OrderedChildBinding]:
    count = len(candidate.ordered_selected_pivots) - 1
    children = tuple(
        AnalyzedWaveSubject(
            f"{candidate.candidate_id}:proposed-child:{index + 1}",
            f"candidate-segment:{candidate.candidate_id}:{index + 1}",
        )
        for index in range(count)
    )
    binding = OrderedChildBinding(
        f"{candidate.candidate_id}:proposed-direct-children",
        candidate.subject,
        children,
    )
    return children, binding


def _diagnostics(
    evaluations: tuple[CandidateFamilyEvaluation, ...],
    hypotheses: tuple[ElliottFamilyEvaluationHypothesis, ...],
) -> tuple[FamilyHypothesisDiagnostic, ...]:
    invalid = sum(
        item.bounded_result.final_summary is BoundedManualChartFinalSummary.STRUCTURALLY_INVALID
        for item in hypotheses
    )
    unresolved = sum(
        item.bounded_result.final_summary is BoundedManualChartFinalSummary.UNRESOLVED
        for item in hypotheses
    )
    reviewed = sum(
        item.bounded_result.final_summary
        is BoundedManualChartFinalSummary.CURRENT_SUPPLIED_SCOPE_REVIEWED
        for item in hypotheses
    )
    coexist = sum(len(item.family_hypotheses) > 1 for item in evaluations)
    none = sum(not item.family_hypotheses for item in evaluations)
    items = [FamilyHypothesisDiagnostic(
        FamilyHypothesisDiagnosticCode.FAMILY_HYPOTHESES_CREATED,
        len(hypotheses),
        "Evaluate-as requests created without family classification or rank.",
    )]
    for count, code, detail in (
        (coexist, FamilyHypothesisDiagnosticCode.MULTIPLE_FAMILIES_COEXIST, "Candidates retaining more than one independent family evaluation hypothesis."),
        (none, FamilyHypothesisDiagnosticCode.NO_COMPATIBLE_FAMILY_REQUESTED, "Candidates with no compatible caller-allowed family evaluation scope."),
        (reviewed, FamilyHypothesisDiagnosticCode.CARDINALITY_SCOPE_REVIEWED, "Only supplied direct-child cardinality scope was reviewed."),
        (invalid, FamilyHypothesisDiagnosticCode.FAMILY_HYPOTHESES_STRUCTURALLY_INVALID, "Family hypotheses invalid only under their exact executed cardinality behavior."),
        (unresolved, FamilyHypothesisDiagnosticCode.FAMILY_HYPOTHESES_UNRESOLVED, "Family hypotheses unresolved under current supplied executable scope."),
    ):
        if count:
            items.append(FamilyHypothesisDiagnostic(code, count, detail))
    return tuple(items)


def build_family_evaluation_hypotheses(
    request: FamilyHypothesisBridgeRequest,
    methodology_kernel: MethodologyKernel,
) -> FamilyHypothesisBridgeResult:
    """Fan out neutral candidates and delegate exact cardinality-only requests."""

    if type(request) is not FamilyHypothesisBridgeRequest:
        _fail("build_family_evaluation_hypotheses requires one exact request.")
    request._validated()
    if type(methodology_kernel) is not MethodologyKernel:
        _fail("Family evaluation requires one exact MethodologyKernel.")
    allowed = set(request.allowed_family_kinds)
    evaluations = []
    flattened = []
    for candidate in request.competing_candidate_set.ordered_candidates:
        candidate._validated()
        children, binding = _candidate_children(candidate)
        compatible = _SHAPE_FAMILIES[candidate.candidate_shape]
        selected = tuple(item for item in compatible if item in allowed)
        hypotheses = []
        for family_kind in selected:
            hypothesis_id = f"{request.bridge_id}:{candidate.candidate_id}:evaluate-as:{family_kind.value}"
            fact = ManualDirectChildCardinalityFact(_FAMILY_FACTS[family_kind])
            bounded_request = BoundedManualChartAnalysisRequest(
                request_id=hypothesis_id,
                requested_at_utc=request.requested_at_utc,
                subject=candidate.subject,
                candidate_id=candidate.candidate_id,
                manual_behavior_facts=(fact,),
                child_binding=binding,
                provenance_refs=request.provenance_refs
                + candidate.provenance_refs
                + (f"family-evaluation-scope:{family_kind.value}",),
            )
            bounded_result = methodology_kernel.analyze_bounded_manual_chart(
                bounded_request
            )
            if type(bounded_result) is not BoundedManualChartAnalysisResult:
                _fail("Existing bounded methodology returned an unexpected result type.")
            hypothesis = ElliottFamilyEvaluationHypothesis(
                hypothesis_id=hypothesis_id,
                generated_candidate=candidate,
                family_kind=family_kind,
                parent_subject=candidate.subject,
                ordered_child_subjects=children,
                child_binding=binding,
                manual_fact=fact,
                bounded_request=bounded_request,
                bounded_result=bounded_result,
                provenance_refs=bounded_request.provenance_refs,
            )
            hypotheses.append(hypothesis)
            flattened.append(hypothesis)
        evaluations.append(CandidateFamilyEvaluation(
            candidate,
            children,
            binding,
            tuple(hypotheses),
        ))
    evaluations_tuple = tuple(evaluations)
    hypotheses_tuple = tuple(flattened)
    values = {
        "bridge_id": request.bridge_id,
        "competing_candidate_set": request.competing_candidate_set,
        "candidate_evaluations": evaluations_tuple,
        "family_hypotheses": hypotheses_tuple,
        "structurally_invalid_hypotheses": tuple(
            item for item in hypotheses_tuple
            if item.bounded_result.final_summary
            is BoundedManualChartFinalSummary.STRUCTURALLY_INVALID
        ),
        "unresolved_hypotheses": tuple(
            item for item in hypotheses_tuple
            if item.bounded_result.final_summary
            is BoundedManualChartFinalSummary.UNRESOLVED
        ),
        "reviewed_scope_hypotheses": tuple(
            item for item in hypotheses_tuple
            if item.bounded_result.final_summary
            is BoundedManualChartFinalSummary.CURRENT_SUPPLIED_SCOPE_REVIEWED
        ),
        "diagnostics": _diagnostics(evaluations_tuple, hypotheses_tuple),
        "provenance_refs": request.provenance_refs,
    }
    result = object.__new__(FamilyHypothesisBridgeResult)
    for name, value in values.items():
        object.__setattr__(result, name, value)
    object.__setattr__(result, "_snapshot", tuple(values.values()))
    _ISSUED_RESULTS[result] = hypotheses_tuple
    return result._validated()


def validate_family_hypothesis_bridge_result(
    result: object,
) -> FamilyHypothesisBridgeResult:
    """Return one exact live issued and unchanged family-bridge result."""

    if type(result) is not FamilyHypothesisBridgeResult:
        _fail("Expected one exact FamilyHypothesisBridgeResult.")
    return result._validated()


__all__ = [
    "ARTIFACT_CLASSIFICATION",
    "CARDINALITY_MATCH_IS_NOT_FULL_FAMILY_VALIDITY",
    "CHILD_HYPOTHESIS_CLASSIFICATION",
    "EVALUATE_AS_IS_NOT_THIS_IS",
    "EVALUATION_SCOPE_CLASSIFICATION",
    "FAMILY_HYPOTHESIS_IS_NOT_CLASSIFICATION",
    "FAN_OUT_ORDER_CLASSIFICATION",
    "GEOMETRIC_PIVOT_IS_NOT_WAVE_ENDPOINT",
    "TIMEFRAME_IS_NOT_DEGREE",
    "CandidateFamilyEvaluation",
    "ElliottFamilyEvaluationHypothesis",
    "FamilyEvaluationKind",
    "FamilyHypothesisBridgeError",
    "FamilyHypothesisBridgeRequest",
    "FamilyHypothesisBridgeResult",
    "FamilyHypothesisDiagnostic",
    "FamilyHypothesisDiagnosticCode",
    "build_family_evaluation_hypotheses",
    "validate_family_hypothesis_bridge_result",
]
