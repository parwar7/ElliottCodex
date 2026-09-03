"""Same-process composition of exact, already-analyzed candidate results.

This module is PROJECT_ANALYSIS_INFRASTRUCTURE.  Its summaries are
PROJECT_OPERATIONAL_POLICY and its relationships are caller-supplied structure
declarations.  It performs no candidate discovery, methodology validation,
family proof, completion proof, degree inference, or certificate issuance.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import StrEnum

from ._structural_invalidity_certification import CertifiedStructuralInvalidity
from .bounded_manual_chart_analysis import (
    BoundedManualChartAnalysisResult,
    BoundedManualChartFinalSummary,
)
from .bounded_recursive_analysis import (
    AnalysisResolutionState,
    BoundedRecursiveAnalysisContractError,
    BoundedRecursiveAnalysisNode,
    BoundedRecursiveAnalysisResolution,
    OperationalAggregationState,
    aggregate_supplied_child_resolutions,
)
from .subject_binding import AnalyzedWaveSubject, OrderedChildBinding


ARTIFACT_CLASSIFICATION = "PROJECT_ANALYSIS_INFRASTRUCTURE"
WORKFLOW_POLICY_CLASSIFICATION = "PROJECT_OPERATIONAL_POLICY"
RELATIONSHIP_CLASSIFICATION = "CALLER_SUPPLIED_STRUCTURE_DECLARATION"


class RecursiveCandidateCompositionSummary(StrEnum):
    BLOCKED_BY_STRUCTURAL_INVALIDITY = "BLOCKED_BY_STRUCTURAL_INVALIDITY"
    BLOCKED_BY_UNRESOLVED_DESCENDANT = "BLOCKED_BY_UNRESOLVED_DESCENDANT"
    RECURSIVE_SCOPE_OPERATIONALLY_REVIEWED = "RECURSIVE_SCOPE_OPERATIONALLY_REVIEWED"


class RecursiveCandidateCompositionError(ValueError):
    """Raised when an exact recursive-composition contract fails closed."""


class _SealedCompositionType(type):
    def __new__(
        mcls: type,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
        **kwargs: object,
    ) -> type:
        if any(isinstance(base, mcls) for base in bases):
            raise TypeError("Recursive candidate-composition types cannot be subclassed.")
        return super().__new__(mcls, name, bases, namespace, **kwargs)


def _require_text(value: object, name: str) -> str:
    if type(value) is not str or value.strip() == "":
        raise RecursiveCandidateCompositionError(
            f"{name} must be an exact non-blank string."
        )
    return value


def _require_provenance(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or any(
        type(item) is not str or item.strip() == "" for item in value
    ):
        raise RecursiveCandidateCompositionError(
            "provenance_refs must be one exact tuple of non-blank strings."
        )
    return value


def _validate_bounded_result(
    value: object,
) -> BoundedManualChartAnalysisResult:
    if type(value) is not BoundedManualChartAnalysisResult:
        raise RecursiveCandidateCompositionError(
            "A bounded candidate must have the exact live result type."
        )
    try:
        return copy.copy(value)
    except Exception as error:
        raise RecursiveCandidateCompositionError(
            "A bounded candidate result is malformed or changed."
        ) from error


def _candidate_subject(value: object) -> AnalyzedWaveSubject:
    if type(value) is BoundedManualChartAnalysisResult:
        return _validate_bounded_result(value).subject
    if type(value) is RecursiveCandidateCompositionResult:
        return value._validated().parent_candidate_result.subject
    raise RecursiveCandidateCompositionError(
        "Child results must be exact bounded or recursive candidate results."
    )


def _validate_certificate(value: object) -> CertifiedStructuralInvalidity:
    if type(value) is not CertifiedStructuralInvalidity:
        raise RecursiveCandidateCompositionError(
            "Structural-invalidity evidence must retain the exact certificate type."
        )
    try:
        if value.fatal_to_candidate is not True:
            raise RecursiveCandidateCompositionError(
                "Structural-invalidity evidence must remain fatal."
            )
        value.origin
    except RecursiveCandidateCompositionError:
        raise
    except Exception as error:
        raise RecursiveCandidateCompositionError(
            "Structural-invalidity evidence is not genuine, live, and unchanged."
        ) from error
    return value


def _resolution_for_bounded_result(
    result: BoundedManualChartAnalysisResult,
) -> BoundedRecursiveAnalysisResolution:
    checked = _validate_bounded_result(result)
    supplied = checked.candidate_analysis_result.operational_resolution
    summary = checked.final_summary

    if summary is BoundedManualChartFinalSummary.STRUCTURALLY_INVALID:
        if not checked.structural_invalidity_certificates:
            raise RecursiveCandidateCompositionError(
                "A structurally blocked candidate retained no invalidity evidence."
            )
        certificate = _validate_certificate(
            checked.structural_invalidity_certificates[0]
        )
        if (
            type(supplied) is BoundedRecursiveAnalysisResolution
            and supplied.state is AnalysisResolutionState.STRUCTURALLY_INVALID
            and supplied.supporting_structural_invalidity_certificate is certificate
        ):
            return supplied
        return BoundedRecursiveAnalysisResolution(
            subject=checked.subject,
            state=AnalysisResolutionState.STRUCTURALLY_INVALID,
            reason="The exact bounded candidate retained genuine structural invalidity.",
            supporting_structural_invalidity_certificate=certificate,
            provenance_refs=checked.provenance_refs,
        )

    if summary is BoundedManualChartFinalSummary.UNRESOLVED:
        if (
            type(supplied) is BoundedRecursiveAnalysisResolution
            and supplied.state
            in (
                AnalysisResolutionState.UNRESOLVED_FINER_DATA_REQUIRED,
                AnalysisResolutionState.UNRESOLVED_METHODOLOGY_DEPENDENCY,
                AnalysisResolutionState.CURRENT_SUPPLIED_SCOPE_UNRESOLVED,
            )
        ):
            return supplied
        if not checked.unresolved_reasons:
            raise RecursiveCandidateCompositionError(
                "An unresolved bounded candidate retained no unresolved reason."
            )
        return BoundedRecursiveAnalysisResolution(
            subject=checked.subject,
            state=AnalysisResolutionState.CURRENT_SUPPLIED_SCOPE_UNRESOLVED,
            reason=checked.unresolved_reasons[0],
            provenance_refs=checked.provenance_refs,
        )

    if summary is BoundedManualChartFinalSummary.CURRENT_SUPPLIED_SCOPE_REVIEWED:
        if supplied is not None:
            if type(supplied) is not BoundedRecursiveAnalysisResolution:
                raise RecursiveCandidateCompositionError(
                    "The candidate operational resolution has an unexpected type."
                )
            try:
                supplied.__post_init__()
            except Exception as error:
                raise RecursiveCandidateCompositionError(
                    "The candidate operational resolution is malformed or changed."
                ) from error
            if supplied.subject is not checked.subject or supplied.state in (
                AnalysisResolutionState.STRUCTURALLY_INVALID,
                AnalysisResolutionState.UNRESOLVED_FINER_DATA_REQUIRED,
                AnalysisResolutionState.UNRESOLVED_METHODOLOGY_DEPENDENCY,
                AnalysisResolutionState.CURRENT_SUPPLIED_SCOPE_UNRESOLVED,
            ):
                raise RecursiveCandidateCompositionError(
                    "The candidate summary and operational resolution conflict."
                )
            return supplied
        return BoundedRecursiveAnalysisResolution(
            subject=checked.subject,
            state=AnalysisResolutionState.CURRENT_SUPPLIED_SCOPE_REVIEWED,
            reason="The exact bounded candidate's current supplied scope was reviewed.",
            provenance_refs=checked.provenance_refs,
        )

    raise RecursiveCandidateCompositionError(
        "The bounded candidate has an unsupported final summary."
    )


def _node_for_child_result(value: object) -> BoundedRecursiveAnalysisNode:
    if type(value) is BoundedManualChartAnalysisResult:
        checked = _validate_bounded_result(value)
        return BoundedRecursiveAnalysisNode(
            subject=checked.subject,
            child_binding=None,
            children=(),
            resolution=_resolution_for_bounded_result(checked),
        )
    if type(value) is RecursiveCandidateCompositionResult:
        return value._validated().parent_node
    raise RecursiveCandidateCompositionError(
        "Child results must be exact bounded or recursive candidate results."
    )


def _walk_node_tree(
    node: BoundedRecursiveAnalysisNode,
    *,
    active_nodes: set[int],
    seen_nodes: set[int],
    seen_subjects: set[int],
) -> None:
    if type(node) is not BoundedRecursiveAnalysisNode:
        raise RecursiveCandidateCompositionError(
            "Recursive trees must contain only exact bounded analysis nodes."
        )
    node_id = id(node)
    if node_id in active_nodes:
        raise RecursiveCandidateCompositionError("Recursive candidate cycle detected.")
    if node_id in seen_nodes:
        raise RecursiveCandidateCompositionError(
            "The same recursive node cannot be reused within one tree."
        )
    subject_id = id(node.subject)
    if subject_id in seen_subjects:
        raise RecursiveCandidateCompositionError(
            "The same exact subject cannot occupy two positions in one tree."
        )
    try:
        node.__post_init__()
    except Exception as error:
        raise RecursiveCandidateCompositionError(
            "A recursive analysis node is malformed or changed."
        ) from error
    active_nodes.add(node_id)
    seen_nodes.add(node_id)
    seen_subjects.add(subject_id)
    try:
        for child in node.children:
            _walk_node_tree(
                child,
                active_nodes=active_nodes,
                seen_nodes=seen_nodes,
                seen_subjects=seen_subjects,
            )
    finally:
        active_nodes.remove(node_id)


def _validate_request_values(
    request: RecursiveCandidateCompositionRequest,
    active_results: set[int] | None = None,
) -> None:
    _require_text(request.request_id, "request_id")
    _require_provenance(request.provenance_refs)
    parent = _validate_bounded_result(request.parent_candidate_result)
    if type(request.ordered_child_candidate_results) is not tuple:
        raise RecursiveCandidateCompositionError(
            "ordered_child_candidate_results must be one exact tuple."
        )
    if type(request.child_binding) is not OrderedChildBinding:
        raise RecursiveCandidateCompositionError(
            "child_binding must be one exact OrderedChildBinding."
        )
    try:
        request.child_binding.__post_init__()
    except Exception as error:
        raise RecursiveCandidateCompositionError(
            "The exact child binding is malformed or changed."
        ) from error
    if request.child_binding.parent_subject is not parent.subject:
        raise RecursiveCandidateCompositionError(
            "The binding parent must be the parent result's exact subject."
        )

    checked_child_subjects: list[AnalyzedWaveSubject] = []
    seen_child_results: set[int] = set()
    seen_child_subjects: set[int] = set()
    for child in request.ordered_child_candidate_results:
        if id(child) in seen_child_results:
            raise RecursiveCandidateCompositionError(
                "The same child result identity cannot be supplied twice."
            )
        seen_child_results.add(id(child))
        if type(child) is BoundedManualChartAnalysisResult:
            child_subject = _validate_bounded_result(child).subject
        elif type(child) is RecursiveCandidateCompositionResult:
            child_subject = child._validated(active_results).parent_candidate_result.subject
        else:
            raise RecursiveCandidateCompositionError(
                "Child results must be exact bounded or recursive candidate results."
            )
        if child_subject is parent.subject:
            raise RecursiveCandidateCompositionError(
                "A parent cannot appear as its own child."
            )
        if id(child_subject) in seen_child_subjects:
            raise RecursiveCandidateCompositionError(
                "The same exact child subject cannot be supplied twice."
            )
        seen_child_subjects.add(id(child_subject))
        checked_child_subjects.append(child_subject)

    expected = request.child_binding.ordered_children
    observed = tuple(checked_child_subjects)
    if len(expected) != len(observed) or any(
        bound is not supplied
        for bound, supplied in zip(expected, observed, strict=True)
    ):
        raise RecursiveCandidateCompositionError(
            "Binding children must exactly match result subjects and order."
        )


@dataclass(frozen=True, slots=True, eq=False, weakref_slot=True)
class RecursiveCandidateCompositionRequest(metaclass=_SealedCompositionType):
    request_id: str
    parent_candidate_result: BoundedManualChartAnalysisResult
    ordered_child_candidate_results: tuple[
        BoundedManualChartAnalysisResult | RecursiveCandidateCompositionResult,
        ...,
    ]
    child_binding: OrderedChildBinding
    provenance_refs: tuple[str, ...] = ()
    _identity_snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("Recursive candidate-composition requests cannot be subclassed.")

    def __post_init__(self) -> None:
        _validate_request_values(self)
        object.__setattr__(
            self,
            "_identity_snapshot",
            (
                self.request_id,
                self.parent_candidate_result,
                self.ordered_child_candidate_results,
                self.child_binding,
                self.provenance_refs,
            ),
        )

    def _validated(
        self,
        active_results: set[int] | None = None,
    ) -> RecursiveCandidateCompositionRequest:
        if type(self) is not RecursiveCandidateCompositionRequest:
            raise RecursiveCandidateCompositionError(
                "Composition requests must have the exact reviewed type."
            )
        try:
            snapshot = object.__getattribute__(self, "_identity_snapshot")
        except AttributeError as error:
            raise RecursiveCandidateCompositionError(
                "The recursive composition request is malformed."
            ) from error
        current = (
            self.request_id,
            self.parent_candidate_result,
            self.ordered_child_candidate_results,
            self.child_binding,
            self.provenance_refs,
        )
        if len(snapshot) != len(current) or any(
            observed is not expected
            for observed, expected in zip(current, snapshot, strict=True)
        ):
            raise RecursiveCandidateCompositionError(
                "The recursive composition request changed after construction."
            )
        _validate_request_values(self, active_results)
        return self

    def __copy__(self) -> RecursiveCandidateCompositionRequest:
        return self._validated()

    def __deepcopy__(
        self,
        memo: dict[int, object],
    ) -> RecursiveCandidateCompositionRequest:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Recursive candidate-composition requests cannot be pickled.")


def _result_unresolved_reasons(value: object) -> tuple[str, ...]:
    if type(value) is BoundedManualChartAnalysisResult:
        return _validate_bounded_result(value).unresolved_reasons
    if type(value) is RecursiveCandidateCompositionResult:
        return value._validated().unresolved_reasons
    raise RecursiveCandidateCompositionError("Unexpected child result type.")


def _result_certificates(
    value: object,
) -> tuple[CertifiedStructuralInvalidity, ...]:
    if type(value) is BoundedManualChartAnalysisResult:
        certificates = _validate_bounded_result(value).structural_invalidity_certificates
    elif type(value) is RecursiveCandidateCompositionResult:
        certificates = value._validated().structural_invalidity_evidence_refs
    else:
        raise RecursiveCandidateCompositionError("Unexpected child result type.")
    for certificate in certificates:
        _validate_certificate(certificate)
    return certificates


@dataclass(
    frozen=True,
    slots=True,
    eq=False,
    weakref_slot=True,
    init=False,
)
class RecursiveCandidateCompositionResult(metaclass=_SealedCompositionType):
    request_id: str
    parent_candidate_result: BoundedManualChartAnalysisResult
    ordered_child_candidate_results: tuple[
        BoundedManualChartAnalysisResult | RecursiveCandidateCompositionResult,
        ...,
    ]
    child_binding: OrderedChildBinding
    parent_node: BoundedRecursiveAnalysisNode
    child_nodes: tuple[BoundedRecursiveAnalysisNode, ...]
    child_aggregation: OperationalAggregationState
    composed_summary: RecursiveCandidateCompositionSummary
    unresolved_reasons: tuple[str, ...]
    structural_invalidity_evidence_refs: tuple[CertifiedStructuralInvalidity, ...]
    provenance_refs: tuple[str, ...]
    _request: RecursiveCandidateCompositionRequest
    _identity_snapshot: tuple[object, ...]

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise TypeError(
            "Recursive candidate-composition results are created only by MethodologyKernel."
        )

    def _validated(
        self,
        active_results: set[int] | None = None,
    ) -> RecursiveCandidateCompositionResult:
        if type(self) is not RecursiveCandidateCompositionResult:
            raise RecursiveCandidateCompositionError(
                "Composition results must have the exact live result type."
            )
        active = set() if active_results is None else active_results
        result_id = id(self)
        if result_id in active:
            raise RecursiveCandidateCompositionError("Recursive candidate cycle detected.")
        active.add(result_id)
        try:
            try:
                snapshot = object.__getattribute__(self, "_identity_snapshot")
                request = object.__getattribute__(self, "_request")
            except AttributeError as error:
                raise RecursiveCandidateCompositionError(
                    "The recursive composition result is malformed."
                ) from error
            current = (
                self.request_id,
                self.parent_candidate_result,
                self.ordered_child_candidate_results,
                self.child_binding,
                self.parent_node,
                self.child_nodes,
                self.child_aggregation,
                self.composed_summary,
                self.unresolved_reasons,
                self.structural_invalidity_evidence_refs,
                self.provenance_refs,
                request,
            )
            if len(snapshot) != len(current) or any(
                observed is not expected
                for observed, expected in zip(current, snapshot, strict=True)
            ):
                raise RecursiveCandidateCompositionError(
                    "The recursive composition result changed after construction."
                )
            request._validated(active)
            if (
                self.request_id is not request.request_id
                or self.parent_candidate_result is not request.parent_candidate_result
                or self.ordered_child_candidate_results
                is not request.ordered_child_candidate_results
                or self.child_binding is not request.child_binding
                or self.provenance_refs is not request.provenance_refs
            ):
                raise RecursiveCandidateCompositionError(
                    "The result no longer retains its exact request identities."
                )
            if type(self.child_nodes) is not tuple or len(self.child_nodes) != len(
                self.ordered_child_candidate_results
            ):
                raise RecursiveCandidateCompositionError(
                    "Child node cardinality differs from supplied child results."
                )
            for result, node in zip(
                self.ordered_child_candidate_results,
                self.child_nodes,
                strict=True,
            ):
                if type(result) is BoundedManualChartAnalysisResult:
                    if node.subject is not result.subject or node.children:
                        raise RecursiveCandidateCompositionError(
                            "A bounded child must retain one exact composition-leaf node."
                        )
                elif type(result) is RecursiveCandidateCompositionResult:
                    if node is not result._validated(active).parent_node:
                        raise RecursiveCandidateCompositionError(
                            "A nested child must retain its exact recursive root node."
                        )
                else:
                    raise RecursiveCandidateCompositionError(
                        "A child result has an unsupported exact type."
                    )
            if (
                self.parent_node.subject is not self.parent_candidate_result.subject
                or self.parent_node.child_binding is not self.child_binding
                or self.parent_node.children is not self.child_nodes
            ):
                raise RecursiveCandidateCompositionError(
                    "The parent node no longer retains the exact composition structure."
                )
            _walk_node_tree(
                self.parent_node,
                active_nodes=set(),
                seen_nodes=set(),
                seen_subjects=set(),
            )
            if aggregate_supplied_child_resolutions(self.child_nodes) is not self.child_aggregation:
                raise RecursiveCandidateCompositionError(
                    "The retained child aggregation no longer matches the exact tree."
                )
            for reason in self.unresolved_reasons:
                _require_text(reason, "unresolved reason")
            if type(self.unresolved_reasons) is not tuple:
                raise RecursiveCandidateCompositionError(
                    "unresolved_reasons must be one exact tuple."
                )
            if type(self.structural_invalidity_evidence_refs) is not tuple:
                raise RecursiveCandidateCompositionError(
                    "structural_invalidity_evidence_refs must be one exact tuple."
                )
            for certificate in self.structural_invalidity_evidence_refs:
                _validate_certificate(certificate)
            if type(self.composed_summary) is not RecursiveCandidateCompositionSummary:
                raise RecursiveCandidateCompositionError(
                    "The composed summary has an unexpected type."
                )
            if type(self.child_aggregation) is not OperationalAggregationState:
                raise RecursiveCandidateCompositionError(
                    "The child aggregation has an unexpected type."
                )
            return self
        finally:
            active.remove(result_id)

    def __copy__(self) -> RecursiveCandidateCompositionResult:
        return self._validated()

    def __deepcopy__(
        self,
        memo: dict[int, object],
    ) -> RecursiveCandidateCompositionResult:
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol: int) -> object:
        raise TypeError("Recursive candidate-composition results cannot be pickled.")


def _compose_recursive_candidate(
    request: object,
) -> RecursiveCandidateCompositionResult:
    if type(request) is not RecursiveCandidateCompositionRequest:
        raise RecursiveCandidateCompositionError(
            "compose_recursive_candidate requires one exact composition request."
        )
    request._validated()
    parent = request.parent_candidate_result
    child_nodes = tuple(
        _node_for_child_result(child)
        for child in request.ordered_child_candidate_results
    )
    parent_node = BoundedRecursiveAnalysisNode(
        subject=parent.subject,
        child_binding=request.child_binding,
        children=child_nodes,
        resolution=_resolution_for_bounded_result(parent),
    )
    _walk_node_tree(
        parent_node,
        active_nodes=set(),
        seen_nodes=set(),
        seen_subjects=set(),
    )
    aggregation = aggregate_supplied_child_resolutions(child_nodes)
    reasons = parent.unresolved_reasons + tuple(
        reason
        for child in request.ordered_child_candidate_results
        for reason in _result_unresolved_reasons(child)
    )
    certificates = parent.structural_invalidity_certificates + tuple(
        certificate
        for child in request.ordered_child_candidate_results
        for certificate in _result_certificates(child)
    )
    if (
        parent.final_summary is BoundedManualChartFinalSummary.STRUCTURALLY_INVALID
        or aggregation is OperationalAggregationState.BLOCKED_BY_INVALID_CHILD
    ):
        summary = RecursiveCandidateCompositionSummary.BLOCKED_BY_STRUCTURAL_INVALIDITY
    elif (
        parent.final_summary is BoundedManualChartFinalSummary.UNRESOLVED
        or aggregation is OperationalAggregationState.BLOCKED_BY_UNRESOLVED_CHILD
    ):
        summary = RecursiveCandidateCompositionSummary.BLOCKED_BY_UNRESOLVED_DESCENDANT
    elif (
        parent.final_summary
        is BoundedManualChartFinalSummary.CURRENT_SUPPLIED_SCOPE_REVIEWED
        and aggregation
        is OperationalAggregationState.CHILDREN_OPERATIONALLY_RESOLVED
    ):
        summary = RecursiveCandidateCompositionSummary.RECURSIVE_SCOPE_OPERATIONALLY_REVIEWED
    else:
        raise RecursiveCandidateCompositionError(
            "The exact parent and child states have no safe composition summary."
        )

    result = object.__new__(RecursiveCandidateCompositionResult)
    values = {
        "request_id": request.request_id,
        "parent_candidate_result": parent,
        "ordered_child_candidate_results": request.ordered_child_candidate_results,
        "child_binding": request.child_binding,
        "parent_node": parent_node,
        "child_nodes": child_nodes,
        "child_aggregation": aggregation,
        "composed_summary": summary,
        "unresolved_reasons": reasons,
        "structural_invalidity_evidence_refs": certificates,
        "provenance_refs": request.provenance_refs,
        "_request": request,
    }
    for name, value in values.items():
        object.__setattr__(result, name, value)
    object.__setattr__(result, "_identity_snapshot", tuple(values.values()))
    return result._validated()


__all__ = [
    "ARTIFACT_CLASSIFICATION",
    "RELATIONSHIP_CLASSIFICATION",
    "WORKFLOW_POLICY_CLASSIFICATION",
    "RecursiveCandidateCompositionError",
    "RecursiveCandidateCompositionRequest",
    "RecursiveCandidateCompositionResult",
    "RecursiveCandidateCompositionSummary",
]
