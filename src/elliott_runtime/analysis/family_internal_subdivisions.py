"""Bounded source-derived internal requirements with operational child review.

Requirements describe what a family hypothesis asks to be evaluated.  They do
not prove a child family, create a terminal wave, or issue family authority.
Only exact caller-supplied recursive nodes are aggregated; no child candidates,
timeframes, degrees, endpoints, visibility, or Elliott labels are inferred.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import NoReturn
import weakref

from elliott_methodology_kernel import (
    AnalysisResolutionState,
    AnalyzedWaveSubject,
    BoundedRecursiveAnalysisNode,
    BoundedRecursiveAnalysisResolution,
    CertifiedStructuralInvalidity,
    OperationalAggregationState,
    aggregate_supplied_child_resolutions,
)

from .family_hypotheses import (
    ElliottFamilyEvaluationHypothesis,
    FamilyEvaluationKind,
    FamilyHypothesisBridgeResult,
    validate_family_hypothesis_bridge_result,
)
from .candidate_generation import GeneratedCandidateHypothesis


ARTIFACT_CLASSIFICATION = "PROJECT_ANALYSIS_INFRASTRUCTURE"
REQUIREMENT_AUTHORITY_CLASSIFICATION = "SOURCE_DERIVED_INTERNAL_SUBDIVISION_EXPECTATION"
CHILD_EVIDENCE_CLASSIFICATION = "CALLER_SUPPLIED_OPERATIONAL_CHILD_EVIDENCE"
SUMMARY_CLASSIFICATION = "PROJECT_OPERATIONAL_POLICY"
INTERNAL_REQUIREMENT_IS_NOT_INTERNAL_PROOF = True
REVIEWED_CHILD_IS_NOT_VALIDATED_FAMILY = True
RECURSIVE_REVIEW_IS_NOT_ELLIOTT_TERMINALITY = True
TIMEFRAME_IS_NOT_DEGREE = True
SOURCE_DERIVED_BASE_CASE_NOT_FOUND = "SOURCE_DERIVED_BASE_CASE_NOT_FOUND"
INTERNAL_FAMILY_PROOF_BLOCKED_BY_NO_SOURCE_DERIVED_BASE_CASE = (
    "INTERNAL_FAMILY_PROOF_BLOCKED_BY_NO_SOURCE_DERIVED_BASE_CASE"
)


class FamilyInternalSubdivisionError(ValueError):
    """Fail-closed family-internal subdivision contract error."""


class RequiredInternalShape(StrEnum):
    MOTIVE_FIVE_FAMILY_REQUIRED = "MOTIVE_FIVE_FAMILY_REQUIRED"
    CORRECTIVE_THREE_FAMILY_REQUIRED = "CORRECTIVE_THREE_FAMILY_REQUIRED"
    THREE_WAVE_STRUCTURE_REQUIRED = "THREE_WAVE_STRUCTURE_REQUIRED"
    CORRECTIVE_FAMILY_REQUIRED = "CORRECTIVE_FAMILY_REQUIRED"


class InternalRequirementStatus(StrEnum):
    NO_CHILD_EVIDENCE_SUPPLIED = "NO_CHILD_EVIDENCE_SUPPLIED"
    CHILD_EVIDENCE_STRUCTURALLY_INVALID = "CHILD_EVIDENCE_STRUCTURALLY_INVALID"
    CHILD_EVIDENCE_UNRESOLVED = "CHILD_EVIDENCE_UNRESOLVED"
    INTERNAL_FAMILY_PROOF_BLOCKED_BY_NO_SOURCE_DERIVED_BASE_CASE = (
        "INTERNAL_FAMILY_PROOF_BLOCKED_BY_NO_SOURCE_DERIVED_BASE_CASE"
    )
    CURRENT_INTERNAL_REQUIREMENT_REVIEWED = "CURRENT_INTERNAL_REQUIREMENT_REVIEWED"


class FamilyInternalOperationalSummary(StrEnum):
    BLOCKED_BY_STRUCTURAL_INVALIDITY = "BLOCKED_BY_STRUCTURAL_INVALIDITY"
    BLOCKED_BY_UNRESOLVED_INTERNAL_STRUCTURE = (
        "BLOCKED_BY_UNRESOLVED_INTERNAL_STRUCTURE"
    )
    CURRENT_INTERNAL_SCOPE_REVIEWED = "CURRENT_INTERNAL_SCOPE_REVIEWED"


class FamilyInternalDiagnosticCode(StrEnum):
    INTERNAL_REQUIREMENTS_CREATED = "INTERNAL_REQUIREMENTS_CREATED"
    CHILD_EVIDENCE_SUPPLIED = "CHILD_EVIDENCE_SUPPLIED"
    CHILD_EVIDENCE_MISSING = "CHILD_EVIDENCE_MISSING"
    STRUCTURAL_INVALIDITY_PRESENT = "STRUCTURAL_INVALIDITY_PRESENT"
    BASE_CASE_PROOF_BLOCKED = "BASE_CASE_PROOF_BLOCKED"
    CURRENT_INTERNAL_SCOPE_REVIEWED = "CURRENT_INTERNAL_SCOPE_REVIEWED"


class _SealedInternalType(type):
    def __new__(
        mcls: type,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
        **kwargs: object,
    ) -> type:
        if any(isinstance(base, mcls) for base in bases):
            raise TypeError("Family-internal subdivision infrastructure cannot be subclassed.")
        return super().__new__(mcls, name, bases, namespace, **kwargs)


def _fail(message: str) -> NoReturn:
    raise FamilyInternalSubdivisionError(message)


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


def _validate_node(value: object) -> BoundedRecursiveAnalysisNode:
    if type(value) is not BoundedRecursiveAnalysisNode:
        _fail("Child evidence must be one exact BoundedRecursiveAnalysisNode.")
    try:
        value.__post_init__()
        aggregate_supplied_child_resolutions((value,))
    except Exception as error:
        raise FamilyInternalSubdivisionError(
            "Child evidence node is malformed or changed."
        ) from error
    return value


@dataclass(frozen=True, slots=True, eq=False)
class FamilyChildCandidateEvidence(metaclass=_SealedInternalType):
    family_hypothesis: ElliottFamilyEvaluationHypothesis
    child_index: int
    child_subject: AnalyzedWaveSubject
    candidate_node: BoundedRecursiveAnalysisNode
    provenance_refs: tuple[str, ...]
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if type(self.family_hypothesis) is not ElliottFamilyEvaluationHypothesis:
            _fail("family_hypothesis must have its exact reviewed type.")
        self.family_hypothesis._validated()
        if type(self.child_index) is not int or not (
            0 <= self.child_index < len(self.family_hypothesis.ordered_child_subjects)
        ):
            _fail("child_index must identify one exact proposed child.")
        expected = self.family_hypothesis.ordered_child_subjects[self.child_index]
        if self.child_subject is not expected:
            _fail("Child evidence subject differs from the hypothesis child identity.")
        node = _validate_node(self.candidate_node)
        if node.subject is not self.child_subject:
            _fail("Child evidence node belongs to another subject identity.")
        _refs(self.provenance_refs)
        object.__setattr__(
            self,
            "_snapshot",
            (
                self.family_hypothesis,
                self.child_index,
                self.child_subject,
                self.candidate_node,
                self.provenance_refs,
            ),
        )

    def _validated(self) -> FamilyChildCandidateEvidence:
        if type(self) is not FamilyChildCandidateEvidence:
            _fail("Child evidence must have its exact reviewed type.")
        current = (
            self.family_hypothesis,
            self.child_index,
            self.child_subject,
            self.candidate_node,
            self.provenance_refs,
        )
        if len(current) != len(self._snapshot) or any(
            observed is not expected
            for observed, expected in zip(current, self._snapshot, strict=True)
        ):
            _fail("Child evidence changed after construction.")
        self.family_hypothesis._validated()
        _validate_node(self.candidate_node)
        _refs(self.provenance_refs)
        return self

    def __copy__(self) -> FamilyChildCandidateEvidence:
        return self._validated()

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> FamilyChildCandidateEvidence:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Family child evidence cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False)
class FamilyInternalSubdivisionEvaluationRequest(metaclass=_SealedInternalType):
    evaluation_id: str
    family_hypothesis_result: FamilyHypothesisBridgeResult
    child_evidence: tuple[FamilyChildCandidateEvidence, ...]
    provenance_refs: tuple[str, ...]
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        _text(self.evaluation_id, "evaluation_id")
        source = validate_family_hypothesis_bridge_result(
            self.family_hypothesis_result
        )
        if type(self.child_evidence) is not tuple or any(
            type(item) is not FamilyChildCandidateEvidence
            for item in self.child_evidence
        ):
            _fail("child_evidence must be one exact tuple of exact evidence objects.")
        available = {id(item): item for item in source.family_hypotheses}
        seen = set()
        for item in self.child_evidence:
            item._validated()
            if id(item.family_hypothesis) not in available:
                _fail("Child evidence references a foreign family hypothesis.")
            key = (id(item.family_hypothesis), item.child_index)
            if key in seen:
                _fail("At most one exact child-candidate path may be supplied per requirement in V1.")
            seen.add(key)
        _refs(self.provenance_refs)
        object.__setattr__(
            self,
            "_snapshot",
            (
                self.evaluation_id,
                self.family_hypothesis_result,
                self.child_evidence,
                self.provenance_refs,
            ),
        )

    def _validated(self) -> FamilyInternalSubdivisionEvaluationRequest:
        if type(self) is not FamilyInternalSubdivisionEvaluationRequest:
            _fail("Internal evaluation request must have its exact reviewed type.")
        current = (
            self.evaluation_id,
            self.family_hypothesis_result,
            self.child_evidence,
            self.provenance_refs,
        )
        if len(current) != len(self._snapshot) or any(
            observed is not expected
            for observed, expected in zip(current, self._snapshot, strict=True)
        ):
            _fail("Internal evaluation request changed after construction.")
        self.__post_init__()
        return self

    def __copy__(self) -> FamilyInternalSubdivisionEvaluationRequest:
        return self._validated()

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> FamilyInternalSubdivisionEvaluationRequest:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Family-internal evaluation requests cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False)
class FamilyInternalSubdivisionRequirement(metaclass=_SealedInternalType):
    requirement_id: str
    family_hypothesis: ElliottFamilyEvaluationHypothesis
    parent_candidate: GeneratedCandidateHypothesis
    child_index: int
    child_subject: AnalyzedWaveSubject
    required_internal_shape: RequiredInternalShape
    source_class: str
    source_principle_id: str | None
    protected_refs: tuple[str, ...]
    execution_status: InternalRequirementStatus
    supplied_child_evidence: FamilyChildCandidateEvidence | None
    provenance_refs: tuple[str, ...]
    validated_child_family_authority: bool = False
    terminality_authority: bool = False
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        _text(self.requirement_id, "requirement_id")
        if type(self.family_hypothesis) is not ElliottFamilyEvaluationHypothesis:
            _fail("Requirement family hypothesis has an unexpected type.")
        self.family_hypothesis._validated()
        if type(self.parent_candidate) is not GeneratedCandidateHypothesis:
            _fail("Requirement parent candidate has an unexpected type.")
        if self.parent_candidate is not self.family_hypothesis.generated_candidate:
            _fail("Requirement must retain exact parent candidate identity.")
        if type(self.child_index) is not int or not (
            0 <= self.child_index < len(self.family_hypothesis.ordered_child_subjects)
        ):
            _fail("Requirement child index is outside the exact hypothesis binding.")
        if self.child_subject is not self.family_hypothesis.ordered_child_subjects[self.child_index]:
            _fail("Requirement child subject differs from exact hypothesis order.")
        if type(self.required_internal_shape) is not RequiredInternalShape:
            _fail("Required internal shape has an unexpected type.")
        if self.source_class != "SOURCE_DEFINITION":
            _fail("Current internal requirements must retain SOURCE_DEFINITION provenance.")
        if self.source_principle_id is not None and (
            type(self.source_principle_id) is not str
            or self.source_principle_id not in {"P007", "P008", "P009"}
        ):
            _fail("Requirement source principle ID is unsupported.")
        _refs(self.protected_refs)
        if type(self.execution_status) is not InternalRequirementStatus:
            _fail("Requirement execution status has an unexpected type.")
        if self.supplied_child_evidence is not None:
            if type(self.supplied_child_evidence) is not FamilyChildCandidateEvidence:
                _fail("Supplied child evidence has an unexpected type.")
            self.supplied_child_evidence._validated()
            if (
                self.supplied_child_evidence.family_hypothesis is not self.family_hypothesis
                or self.supplied_child_evidence.child_index != self.child_index
                or self.supplied_child_evidence.child_subject is not self.child_subject
            ):
                _fail("Requirement evidence differs from exact hypothesis child identity.")
        if self.validated_child_family_authority is not False or self.terminality_authority is not False:
            _fail("Requirements cannot carry validated-family or terminality authority.")
        _refs(self.provenance_refs)
        names = tuple(
            name for name in self.__dataclass_fields__ if name != "_snapshot"
        )
        if hasattr(self, "_snapshot"):
            current = tuple(getattr(self, name) for name in names)
            if len(current) != len(self._snapshot) or any(
                observed is not expected
                for observed, expected in zip(current, self._snapshot, strict=True)
            ):
                _fail("Internal requirement changed after construction.")
        else:
            object.__setattr__(self, "_snapshot", tuple(getattr(self, name) for name in names))


@dataclass(frozen=True, slots=True, eq=False)
class FamilyInternalHypothesisEvaluation(metaclass=_SealedInternalType):
    family_hypothesis: ElliottFamilyEvaluationHypothesis
    internal_requirements: tuple[FamilyInternalSubdivisionRequirement, ...]
    operational_child_nodes: tuple[BoundedRecursiveAnalysisNode, ...]
    child_aggregation: OperationalAggregationState
    operational_summary: FamilyInternalOperationalSummary
    structural_invalidity_evidence: tuple[CertifiedStructuralInvalidity, ...]
    unresolved_reasons: tuple[str, ...]
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if type(self.family_hypothesis) is not ElliottFamilyEvaluationHypothesis:
            _fail("Internal hypothesis evaluation has an unexpected family type.")
        self.family_hypothesis._validated()
        if type(self.internal_requirements) is not tuple or any(
            type(item) is not FamilyInternalSubdivisionRequirement
            for item in self.internal_requirements
        ):
            _fail("Internal requirements have an unexpected type.")
        if type(self.operational_child_nodes) is not tuple:
            _fail("Operational child nodes must be one exact tuple.")
        if len(self.internal_requirements) != len(self.operational_child_nodes):
            _fail("Requirement and operational child-node counts differ.")
        for index, (requirement, node) in enumerate(
            zip(self.internal_requirements, self.operational_child_nodes, strict=True)
        ):
            requirement.__post_init__()
            _validate_node(node)
            if (
                requirement.family_hypothesis is not self.family_hypothesis
                or requirement.child_index != index
                or node.subject is not requirement.child_subject
            ):
                _fail("Internal evaluation requirement/node identity or order changed.")
        if aggregate_supplied_child_resolutions(self.operational_child_nodes) is not self.child_aggregation:
            _fail("Internal evaluation aggregation differs from existing recursive policy.")
        if type(self.operational_summary) is not FamilyInternalOperationalSummary:
            _fail("Internal evaluation summary has an unexpected type.")
        if type(self.structural_invalidity_evidence) is not tuple:
            _fail("Structural invalidity evidence must be one exact tuple.")
        expected_certificates = tuple(
            certificate
            for node in self.operational_child_nodes
            for certificate in _certificates(node)
        )
        if len(self.structural_invalidity_evidence) != len(expected_certificates) or any(
            observed is not expected
            for observed, expected in zip(
                self.structural_invalidity_evidence,
                expected_certificates,
                strict=True,
            )
        ):
            _fail("Structural invalidity evidence identity or membership changed.")
        for certificate in self.structural_invalidity_evidence:
            if type(certificate) is not CertifiedStructuralInvalidity:
                _fail("Structural invalidity evidence has an unexpected type.")
            certificate.origin
        if type(self.unresolved_reasons) is not tuple:
            _fail("Unresolved reasons must be one exact tuple.")
        for reason in self.unresolved_reasons:
            _text(reason, "unresolved reason")
        names = tuple(
            name for name in self.__dataclass_fields__ if name != "_snapshot"
        )
        if hasattr(self, "_snapshot"):
            current = tuple(getattr(self, name) for name in names)
            if len(current) != len(self._snapshot) or any(
                observed is not expected
                for observed, expected in zip(current, self._snapshot, strict=True)
            ):
                _fail("Internal hypothesis evaluation changed after construction.")
        else:
            object.__setattr__(self, "_snapshot", tuple(getattr(self, name) for name in names))


@dataclass(frozen=True, slots=True, eq=False)
class FamilyInternalDiagnostic(metaclass=_SealedInternalType):
    code: FamilyInternalDiagnosticCode
    count: int
    detail: str
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if type(self.code) is not FamilyInternalDiagnosticCode:
            _fail("Internal diagnostic code has an unexpected type.")
        if type(self.count) is not int or self.count < 0:
            _fail("Internal diagnostic count must be one non-negative exact integer.")
        _text(self.detail, "diagnostic detail")
        current = (self.code, self.count, self.detail)
        if hasattr(self, "_snapshot"):
            if len(current) != len(self._snapshot) or any(
                observed is not expected
                for observed, expected in zip(current, self._snapshot, strict=True)
            ):
                _fail("Internal diagnostic changed after construction.")
        else:
            object.__setattr__(self, "_snapshot", current)


@dataclass(frozen=True, slots=True, eq=False, init=False, weakref_slot=True)
class FamilyInternalSubdivisionEvaluationResult(metaclass=_SealedInternalType):
    evaluation_id: str
    family_hypothesis_result: FamilyHypothesisBridgeResult
    hypothesis_evaluations: tuple[FamilyInternalHypothesisEvaluation, ...]
    internal_requirements: tuple[FamilyInternalSubdivisionRequirement, ...]
    structurally_blocked_hypotheses: tuple[FamilyInternalHypothesisEvaluation, ...]
    internally_unresolved_hypotheses: tuple[FamilyInternalHypothesisEvaluation, ...]
    reviewed_internal_scope_hypotheses: tuple[FamilyInternalHypothesisEvaluation, ...]
    diagnostics: tuple[FamilyInternalDiagnostic, ...]
    provenance_refs: tuple[str, ...]
    _snapshot: tuple[object, ...]

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError("Family-internal results are created only by the evaluator.")

    def _validated(self) -> FamilyInternalSubdivisionEvaluationResult:
        if type(self) is not FamilyInternalSubdivisionEvaluationResult:
            _fail("Family-internal result must have its exact reviewed type.")
        try:
            issued = _ISSUED_RESULTS.get(self)
            snapshot = object.__getattribute__(self, "_snapshot")
        except Exception as error:
            raise FamilyInternalSubdivisionError("Family-internal result is malformed.") from error
        current = tuple(
            getattr(self, name)
            for name in self.__dataclass_fields__
            if name != "_snapshot"
        )
        if issued is None or len(current) != len(snapshot) or any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            _fail("Family-internal result is unissued or changed after creation.")
        validate_family_hypothesis_bridge_result(self.family_hypothesis_result)
        if len(issued) != len(self.hypothesis_evaluations) or any(
            observed is not expected
            for observed, expected in zip(self.hypothesis_evaluations, issued, strict=True)
        ):
            _fail("Family-internal evaluation membership differs from issuance.")
        if len(self.hypothesis_evaluations) != len(self.family_hypothesis_result.family_hypotheses):
            _fail("Every family hypothesis must retain one internal evaluation.")
        flattened = []
        for hypothesis, evaluation in zip(
            self.family_hypothesis_result.family_hypotheses,
            self.hypothesis_evaluations,
            strict=True,
        ):
            if type(evaluation) is not FamilyInternalHypothesisEvaluation:
                _fail("Family-internal hypothesis evaluation has an unexpected type.")
            evaluation.__post_init__()
            if evaluation.family_hypothesis is not hypothesis:
                _fail("Family-internal hypothesis order or identity changed.")
            flattened.extend(evaluation.internal_requirements)
        if len(flattened) != len(self.internal_requirements) or any(
            observed is not expected
            for observed, expected in zip(flattened, self.internal_requirements, strict=True)
        ):
            _fail("Flattened internal requirement identity or order changed.")
        views = {
            "structurally_blocked_hypotheses": FamilyInternalOperationalSummary.BLOCKED_BY_STRUCTURAL_INVALIDITY,
            "internally_unresolved_hypotheses": FamilyInternalOperationalSummary.BLOCKED_BY_UNRESOLVED_INTERNAL_STRUCTURE,
            "reviewed_internal_scope_hypotheses": FamilyInternalOperationalSummary.CURRENT_INTERNAL_SCOPE_REVIEWED,
        }
        for name, status in views.items():
            expected = tuple(
                item for item in self.hypothesis_evaluations
                if item.operational_summary is status
            )
            observed = getattr(self, name)
            if len(observed) != len(expected) or any(
                item is not reference
                for item, reference in zip(observed, expected, strict=True)
            ):
                _fail(f"Family-internal {name} view changed.")
        if type(self.diagnostics) is not tuple or any(
            type(item) is not FamilyInternalDiagnostic for item in self.diagnostics
        ):
            _fail("Family-internal diagnostics have an unexpected type.")
        for item in self.diagnostics:
            item.__post_init__()
        _refs(self.provenance_refs)
        return self

    def __copy__(self) -> FamilyInternalSubdivisionEvaluationResult:
        return self._validated()

    def __deepcopy__(
        self, memo: dict[int, object]
    ) -> FamilyInternalSubdivisionEvaluationResult:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Family-internal results cannot be pickled.")


_ISSUED_RESULTS: weakref.WeakKeyDictionary[
    FamilyInternalSubdivisionEvaluationResult,
    tuple[FamilyInternalHypothesisEvaluation, ...],
] = weakref.WeakKeyDictionary()


_MOTIVE_FIVE = RequiredInternalShape.MOTIVE_FIVE_FAMILY_REQUIRED
_CORRECTIVE_THREE = RequiredInternalShape.CORRECTIVE_THREE_FAMILY_REQUIRED
_THREE = RequiredInternalShape.THREE_WAVE_STRUCTURE_REQUIRED
_CORRECTIVE = RequiredInternalShape.CORRECTIVE_FAMILY_REQUIRED

_REQUIREMENT_MATRIX = MappingProxyType({
    FamilyEvaluationKind.SINGLE_ZIGZAG: (
        _MOTIVE_FIVE,
        _CORRECTIVE_THREE,
        _MOTIVE_FIVE,
    ),
    FamilyEvaluationKind.FLAT: (
        _CORRECTIVE_THREE,
        _CORRECTIVE_THREE,
        _MOTIVE_FIVE,
    ),
    FamilyEvaluationKind.TRIANGLE: (_CORRECTIVE,) * 5,
    FamilyEvaluationKind.ENDING_DIAGONAL: (_THREE,) * 5,
})

_SOURCE_META = MappingProxyType({
    FamilyEvaluationKind.SINGLE_ZIGZAG: (
        "P007",
        (
            "docs/elliott/SOURCE_EVIDENCE_MAP.json#P007",
            "docs/elliott/PATTERN_BRAIN.md#F-zigzag-family",
        ),
    ),
    FamilyEvaluationKind.FLAT: (
        "P008",
        (
            "docs/elliott/SOURCE_EVIDENCE_MAP.json#P008",
            "docs/elliott/PATTERN_BRAIN.md#G-flat-family",
        ),
    ),
    FamilyEvaluationKind.TRIANGLE: (
        "P009",
        (
            "docs/elliott/SOURCE_EVIDENCE_MAP.json#P009",
            "docs/elliott/PATTERN_BRAIN.md#H-triangle",
        ),
    ),
    FamilyEvaluationKind.ENDING_DIAGONAL: (
        None,
        (
            "docs/elliott/PATTERN_BRAIN.md#D-ending-diagonal",
            "Sources_LOCKED/volume_03/volume_03.srt@00:29:02.380-00:29:08.220",
        ),
    ),
})


def _missing_node(subject: AnalyzedWaveSubject) -> BoundedRecursiveAnalysisNode:
    return BoundedRecursiveAnalysisNode(
        subject,
        None,
        (),
        BoundedRecursiveAnalysisResolution(
            subject,
            AnalysisResolutionState.CURRENT_SUPPLIED_SCOPE_UNRESOLVED,
            "No exact child candidate evidence was supplied for this internal requirement.",
            provenance_refs=("family-internal:no-child-evidence",),
        ),
    )


def _status_for_node(node: BoundedRecursiveAnalysisNode) -> InternalRequirementStatus:
    aggregation = aggregate_supplied_child_resolutions((node,))
    if aggregation is OperationalAggregationState.BLOCKED_BY_INVALID_CHILD:
        return InternalRequirementStatus.CHILD_EVIDENCE_STRUCTURALLY_INVALID
    if aggregation is OperationalAggregationState.BLOCKED_BY_UNRESOLVED_CHILD:
        return InternalRequirementStatus.CHILD_EVIDENCE_UNRESOLVED
    if node.resolution.state is AnalysisResolutionState.VALIDATED_FAMILY:
        return InternalRequirementStatus.CURRENT_INTERNAL_REQUIREMENT_REVIEWED
    return InternalRequirementStatus.INTERNAL_FAMILY_PROOF_BLOCKED_BY_NO_SOURCE_DERIVED_BASE_CASE


def _certificates(node: BoundedRecursiveAnalysisNode) -> tuple[CertifiedStructuralInvalidity, ...]:
    own = node.resolution.supporting_structural_invalidity_certificate
    nested = tuple(
        certificate
        for child in node.children
        for certificate in _certificates(child)
    )
    return (() if own is None else (own,)) + nested


def _diagnostics(
    evaluations: tuple[FamilyInternalHypothesisEvaluation, ...],
    requirements: tuple[FamilyInternalSubdivisionRequirement, ...],
) -> tuple[FamilyInternalDiagnostic, ...]:
    supplied = sum(item.supplied_child_evidence is not None for item in requirements)
    missing = len(requirements) - supplied
    invalid = sum(
        item.operational_summary
        is FamilyInternalOperationalSummary.BLOCKED_BY_STRUCTURAL_INVALIDITY
        for item in evaluations
    )
    base_case = sum(
        item.execution_status
        is InternalRequirementStatus.INTERNAL_FAMILY_PROOF_BLOCKED_BY_NO_SOURCE_DERIVED_BASE_CASE
        for item in requirements
    )
    reviewed = sum(
        item.operational_summary
        is FamilyInternalOperationalSummary.CURRENT_INTERNAL_SCOPE_REVIEWED
        for item in evaluations
    )
    values = [FamilyInternalDiagnostic(
        FamilyInternalDiagnosticCode.INTERNAL_REQUIREMENTS_CREATED,
        len(requirements),
        "Source-derived expectations created without child-family proof.",
    )]
    for count, code, detail in (
        (supplied, FamilyInternalDiagnosticCode.CHILD_EVIDENCE_SUPPLIED, "Exact caller-supplied recursive child paths retained."),
        (missing, FamilyInternalDiagnosticCode.CHILD_EVIDENCE_MISSING, "No child evidence was supplied; no terminality is inferred."),
        (invalid, FamilyInternalDiagnosticCode.STRUCTURAL_INVALIDITY_PRESENT, "Genuine child invalidity blocks only its exact family evaluation path."),
        (base_case, FamilyInternalDiagnosticCode.BASE_CASE_PROOF_BLOCKED, SOURCE_DERIVED_BASE_CASE_NOT_FOUND),
        (reviewed, FamilyInternalDiagnosticCode.CURRENT_INTERNAL_SCOPE_REVIEWED, "All exact requirements carried genuine validated-family support."),
    ):
        if count:
            values.append(FamilyInternalDiagnostic(code, count, detail))
    return tuple(values)


def evaluate_family_internal_subdivisions(
    request: FamilyInternalSubdivisionEvaluationRequest,
) -> FamilyInternalSubdivisionEvaluationResult:
    """Construct exact requirements and aggregate only supplied recursive evidence."""

    if type(request) is not FamilyInternalSubdivisionEvaluationRequest:
        _fail("evaluate_family_internal_subdivisions requires one exact request.")
    request._validated()
    by_requirement = {
        (id(item.family_hypothesis), item.child_index): item
        for item in request.child_evidence
    }
    evaluations = []
    all_requirements = []
    for hypothesis in request.family_hypothesis_result.family_hypotheses:
        shapes = _REQUIREMENT_MATRIX[hypothesis.family_kind]
        principle_id, protected_refs = _SOURCE_META[hypothesis.family_kind]
        requirements = []
        nodes = []
        reasons = []
        for child_index, shape in enumerate(shapes):
            evidence = by_requirement.get((id(hypothesis), child_index))
            node = _missing_node(hypothesis.ordered_child_subjects[child_index]) if evidence is None else evidence.candidate_node
            status = (
                InternalRequirementStatus.NO_CHILD_EVIDENCE_SUPPLIED
                if evidence is None
                else _status_for_node(node)
            )
            if status is not InternalRequirementStatus.CURRENT_INTERNAL_REQUIREMENT_REVIEWED:
                reason = (
                    SOURCE_DERIVED_BASE_CASE_NOT_FOUND
                    if status
                    is InternalRequirementStatus.INTERNAL_FAMILY_PROOF_BLOCKED_BY_NO_SOURCE_DERIVED_BASE_CASE
                    else status.value
                )
                if reason not in reasons:
                    reasons.append(reason)
            requirement = FamilyInternalSubdivisionRequirement(
                requirement_id=f"{request.evaluation_id}:{hypothesis.hypothesis_id}:child:{child_index + 1}",
                family_hypothesis=hypothesis,
                parent_candidate=hypothesis.generated_candidate,
                child_index=child_index,
                child_subject=hypothesis.ordered_child_subjects[child_index],
                required_internal_shape=shape,
                source_class="SOURCE_DEFINITION",
                source_principle_id=principle_id,
                protected_refs=protected_refs,
                execution_status=status,
                supplied_child_evidence=evidence,
                provenance_refs=request.provenance_refs
                + hypothesis.provenance_refs
                + (f"internal-requirement:child-{child_index + 1}",),
            )
            requirements.append(requirement)
            nodes.append(node)
            all_requirements.append(requirement)
        nodes_tuple = tuple(nodes)
        aggregation = aggregate_supplied_child_resolutions(nodes_tuple)
        if aggregation is OperationalAggregationState.BLOCKED_BY_INVALID_CHILD:
            summary = FamilyInternalOperationalSummary.BLOCKED_BY_STRUCTURAL_INVALIDITY
        elif all(
            item.execution_status
            is InternalRequirementStatus.CURRENT_INTERNAL_REQUIREMENT_REVIEWED
            for item in requirements
        ):
            summary = FamilyInternalOperationalSummary.CURRENT_INTERNAL_SCOPE_REVIEWED
        else:
            summary = FamilyInternalOperationalSummary.BLOCKED_BY_UNRESOLVED_INTERNAL_STRUCTURE
        evaluations.append(FamilyInternalHypothesisEvaluation(
            hypothesis,
            tuple(requirements),
            nodes_tuple,
            aggregation,
            summary,
            tuple(certificate for node in nodes_tuple for certificate in _certificates(node)),
            tuple(reasons),
        ))
    evaluations_tuple = tuple(evaluations)
    requirements_tuple = tuple(all_requirements)
    values = {
        "evaluation_id": request.evaluation_id,
        "family_hypothesis_result": request.family_hypothesis_result,
        "hypothesis_evaluations": evaluations_tuple,
        "internal_requirements": requirements_tuple,
        "structurally_blocked_hypotheses": tuple(
            item for item in evaluations_tuple
            if item.operational_summary
            is FamilyInternalOperationalSummary.BLOCKED_BY_STRUCTURAL_INVALIDITY
        ),
        "internally_unresolved_hypotheses": tuple(
            item for item in evaluations_tuple
            if item.operational_summary
            is FamilyInternalOperationalSummary.BLOCKED_BY_UNRESOLVED_INTERNAL_STRUCTURE
        ),
        "reviewed_internal_scope_hypotheses": tuple(
            item for item in evaluations_tuple
            if item.operational_summary
            is FamilyInternalOperationalSummary.CURRENT_INTERNAL_SCOPE_REVIEWED
        ),
        "diagnostics": _diagnostics(evaluations_tuple, requirements_tuple),
        "provenance_refs": request.provenance_refs,
    }
    result = object.__new__(FamilyInternalSubdivisionEvaluationResult)
    for name, value in values.items():
        object.__setattr__(result, name, value)
    object.__setattr__(result, "_snapshot", tuple(values.values()))
    _ISSUED_RESULTS[result] = evaluations_tuple
    return result._validated()


def validate_family_internal_subdivision_evaluation_result(
    result: object,
) -> FamilyInternalSubdivisionEvaluationResult:
    """Return one exact live issued and unchanged internal-evaluation result."""

    if type(result) is not FamilyInternalSubdivisionEvaluationResult:
        _fail("Expected one exact FamilyInternalSubdivisionEvaluationResult.")
    return result._validated()


__all__ = [
    "ARTIFACT_CLASSIFICATION",
    "CHILD_EVIDENCE_CLASSIFICATION",
    "INTERNAL_FAMILY_PROOF_BLOCKED_BY_NO_SOURCE_DERIVED_BASE_CASE",
    "INTERNAL_REQUIREMENT_IS_NOT_INTERNAL_PROOF",
    "RECURSIVE_REVIEW_IS_NOT_ELLIOTT_TERMINALITY",
    "REQUIREMENT_AUTHORITY_CLASSIFICATION",
    "REVIEWED_CHILD_IS_NOT_VALIDATED_FAMILY",
    "SOURCE_DERIVED_BASE_CASE_NOT_FOUND",
    "SUMMARY_CLASSIFICATION",
    "TIMEFRAME_IS_NOT_DEGREE",
    "FamilyChildCandidateEvidence",
    "FamilyInternalDiagnostic",
    "FamilyInternalDiagnosticCode",
    "FamilyInternalHypothesisEvaluation",
    "FamilyInternalOperationalSummary",
    "FamilyInternalSubdivisionError",
    "FamilyInternalSubdivisionEvaluationRequest",
    "FamilyInternalSubdivisionEvaluationResult",
    "FamilyInternalSubdivisionRequirement",
    "InternalRequirementStatus",
    "RequiredInternalShape",
    "evaluate_family_internal_subdivisions",
    "validate_family_internal_subdivision_evaluation_result",
]
