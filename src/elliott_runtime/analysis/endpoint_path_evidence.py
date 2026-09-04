"""Hypothesis-bound endpoint and path evidence with no Elliott validity authority."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import NoReturn
import weakref

from elliott_methodology_kernel.contracts import Bar, NormalizedMarketObservations

from .family_hypotheses import ElliottFamilyEvaluationHypothesis, FamilyEvaluationKind
from ..market_data.geometric_pivots import (
    GeometricPivotKind,
    GeometricPivotObservation,
    GeometricPivotState,
)


ARTIFACT_CLASSIFICATION = "PROJECT_ANALYSIS_INFRASTRUCTURE"
ROLE_CLASSIFICATION = "HYPOTHESIS_ROLE_METADATA"
ENDPOINT_AUTHORITY_CLASS = "HYPOTHESIS_BOUND_COMPONENT_ENDPOINT"
ORTHODOX_ELLIOTT_ENDPOINT_AUTHORITY = False
FAMILY_VALIDITY_AUTHORITY = False
WAVE_VALIDITY_AUTHORITY = False
DEGREE_AUTHORITY = False
TIMEFRAME_IS_NOT_DEGREE = True
PATH_EXTREME_IS_NOT_ORTHODOX_ENDPOINT = True
_MAX_COMPONENTS = 5
_MAX_PATH_BARS = 100_000


class EndpointPathEvidenceError(ValueError):
    """Fail-closed evidence-contract error."""


class EndpointPathEvidenceLimitExceeded(EndpointPathEvidenceError):
    """Raised before returning a partial result."""


class ComponentEndpointState(StrEnum):
    CONFIRMED_BY_GEOMETRY_HYPOTHESIS_BOUND_ENDPOINT = (
        "CONFIRMED_BY_GEOMETRY_HYPOTHESIS_BOUND_ENDPOINT"
    )
    DEVELOPING_HYPOTHESIS_BOUND_ENDPOINT = "DEVELOPING_HYPOTHESIS_BOUND_ENDPOINT"


class ObservedComponentDirection(StrEnum):
    UP = "UP"
    DOWN = "DOWN"
    EQUAL = "EQUAL"


class _Sealed(type):
    def __new__(mcls, name, bases, namespace, **kwargs):
        if any(isinstance(base, mcls) for base in bases):
            raise TypeError("Endpoint/path evidence contracts cannot be subclassed.")
        return super().__new__(mcls, name, bases, namespace, **kwargs)


def _fail(message: str) -> NoReturn:
    raise EndpointPathEvidenceError(message)


def _text(value: object, name: str) -> str:
    if type(value) is not str or value.strip() == "":
        _fail(f"{name} must be one exact non-blank string.")
    return value


def _refs(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or any(type(item) is not str or not item.strip() for item in value):
        _fail("provenance_refs must be one exact tuple of non-blank strings.")
    return value


_ROLES = {
    FamilyEvaluationKind.SINGLE_ZIGZAG: ("A", "B", "C"),
    FamilyEvaluationKind.FLAT: ("A", "B", "C"),
    FamilyEvaluationKind.TRIANGLE: ("A", "B", "C", "D", "E"),
    FamilyEvaluationKind.ENDING_DIAGONAL: ("1", "2", "3", "4", "5"),
}


@dataclass(frozen=True, slots=True, eq=False)
class EndpointPathEvidenceRequest(metaclass=_Sealed):
    request_id: str
    family_hypothesis: ElliottFamilyEvaluationHypothesis
    source_observations: NormalizedMarketObservations
    max_path_bars: int
    provenance_refs: tuple[str, ...]
    _snapshot: tuple[object, ...] = field(init=False, repr=False)

    def __post_init__(self):
        _text(self.request_id, "request_id")
        if type(self.family_hypothesis) is not ElliottFamilyEvaluationHypothesis:
            _fail("family_hypothesis must have its exact reviewed type.")
        self.family_hypothesis._validated()
        if self.source_observations is not self.family_hypothesis.generated_candidate.source_observations:
            _fail("source_observations must retain exact candidate ancestry identity.")
        if type(self.max_path_bars) is not int or not 1 <= self.max_path_bars <= _MAX_PATH_BARS:
            _fail("max_path_bars must be one exact integer within the operational bound.")
        _refs(self.provenance_refs)
        current=(self.request_id,self.family_hypothesis,self.source_observations,self.max_path_bars,self.provenance_refs)
        if hasattr(self,"_snapshot") and any(a is not b for a,b in zip(current,self._snapshot,strict=True)):
            _fail("Endpoint/path request changed after construction.")
        object.__setattr__(self,"_snapshot",current)

    def _validated(self):
        if type(self) is not EndpointPathEvidenceRequest: _fail("Request has an unexpected type.")
        self.__post_init__(); return self

    def __copy__(self):
        return self._validated()

    def __deepcopy__(self, memo):
        memo[id(self)] = self
        return self._validated()

    def __reduce_ex__(self, protocol):
        raise TypeError("Endpoint/path requests cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False)
class FamilyComponentRoleBinding(metaclass=_Sealed):
    family_hypothesis: ElliottFamilyEvaluationHypothesis
    family_kind: FamilyEvaluationKind
    child_index: int
    component_role: str
    child_subject: object
    start_boundary: GeometricPivotObservation
    end_boundary: GeometricPivotObservation
    provenance_refs: tuple[str, ...]
    hypothesis_only: bool = True
    family_validity_authority: bool = False
    wave_validity_authority: bool = False
    degree_authority: bool = False

    def __post_init__(self):
        if type(self.family_hypothesis) is not ElliottFamilyEvaluationHypothesis: _fail("Role binding requires one exact hypothesis.")
        self.family_hypothesis._validated()
        if self.family_kind is not self.family_hypothesis.family_kind: _fail("Role family differs from hypothesis.")
        roles=_ROLES[self.family_kind]
        if type(self.child_index) is not int or not 0 <= self.child_index < len(roles): _fail("child_index is outside the exact family role scope.")
        if self.component_role != roles[self.child_index]: _fail("component_role differs from protected family order.")
        if self.child_subject is not self.family_hypothesis.ordered_child_subjects[self.child_index]: _fail("Role lost exact child identity.")
        pivots=self.family_hypothesis.generated_candidate.ordered_selected_pivots
        if self.start_boundary is not pivots[self.child_index] or self.end_boundary is not pivots[self.child_index+1]: _fail("Role boundaries lost exact candidate pivot identity.")
        _refs(self.provenance_refs)
        if self.hypothesis_only is not True or any((self.family_validity_authority,self.wave_validity_authority,self.degree_authority)):
            _fail("Role metadata cannot carry Elliott authority.")

    def __reduce_ex__(self, protocol): raise TypeError("Role bindings cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False)
class FamilyComponentEndpointEvidence(metaclass=_Sealed):
    role_binding: FamilyComponentRoleBinding
    boundary_pivot: GeometricPivotObservation
    observed_price: float
    geometric_pivot_kind: GeometricPivotKind
    geometric_state: GeometricPivotState
    endpoint_state: ComponentEndpointState
    endpoint_authority_class: str
    provenance_refs: tuple[str, ...]
    orthodox_elliott_endpoint_authority: bool = False

    def __post_init__(self):
        if type(self.role_binding) is not FamilyComponentRoleBinding: _fail("Endpoint requires one exact role binding.")
        self.role_binding.__post_init__()
        if self.boundary_pivot is not self.role_binding.end_boundary: _fail("Endpoint lost exact boundary pivot identity.")
        if self.observed_price is not self.boundary_pivot.observed_price: _fail("Endpoint price must retain exact candidate-boundary value.")
        if self.geometric_pivot_kind is not self.boundary_pivot.pivot_kind or self.geometric_state is not self.boundary_pivot.state: _fail("Endpoint geometry metadata differs from boundary.")
        expected=(ComponentEndpointState.DEVELOPING_HYPOTHESIS_BOUND_ENDPOINT if self.geometric_state is GeometricPivotState.DEVELOPING else ComponentEndpointState.CONFIRMED_BY_GEOMETRY_HYPOTHESIS_BOUND_ENDPOINT)
        if self.endpoint_state is not expected: _fail("Endpoint evidence state differs from geometric state.")
        if self.endpoint_authority_class != ENDPOINT_AUTHORITY_CLASS or self.orthodox_elliott_endpoint_authority: _fail("Endpoint authority was promoted.")
        _refs(self.provenance_refs)

    def __reduce_ex__(self, protocol): raise TypeError("Endpoint evidence cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False)
class FamilyComponentPathEvidence(metaclass=_Sealed):
    role_binding: FamilyComponentRoleBinding
    source_observations: NormalizedMarketObservations
    exact_bars: tuple[Bar, ...]
    observed_high_extreme: int | float
    observed_low_extreme: int | float
    observed_direction: ObservedComponentDirection
    provenance_refs: tuple[str, ...]
    wave_validity_authority: bool = False

    def __post_init__(self):
        if type(self.role_binding) is not FamilyComponentRoleBinding: _fail("Path requires one exact role binding.")
        self.role_binding.__post_init__()
        candidate=self.role_binding.family_hypothesis.generated_candidate
        if self.source_observations is not candidate.source_observations: _fail("Path observations lost exact candidate ancestry.")
        expected=tuple(bar for bar in self.source_observations.bars if self.role_binding.start_boundary.timestamp_utc <= bar.timestamp_utc <= self.role_binding.end_boundary.timestamp_utc)
        if not expected or type(self.exact_bars) is not tuple or len(expected)!=len(self.exact_bars) or any(a is not b for a,b in zip(self.exact_bars,expected,strict=True)): _fail("Path bars must be the exact inclusive candidate component interval.")
        if self.observed_high_extreme != max(bar.high for bar in expected) or self.observed_low_extreme != min(bar.low for bar in expected): _fail("Path extrema differ from exact observed bars.")
        start=self.role_binding.start_boundary.observed_price; end=self.role_binding.end_boundary.observed_price
        direction=ObservedComponentDirection.UP if end>start else ObservedComponentDirection.DOWN if end<start else ObservedComponentDirection.EQUAL
        if self.observed_direction is not direction: _fail("Observed direction differs from endpoint arithmetic.")
        if self.wave_validity_authority: _fail("Path evidence cannot carry wave validity authority.")
        _refs(self.provenance_refs)

    def __reduce_ex__(self, protocol): raise TypeError("Path evidence cannot be pickled.")


@dataclass(frozen=True, slots=True, eq=False, init=False, weakref_slot=True)
class EndpointPathEvidenceResult(metaclass=_Sealed):
    request: EndpointPathEvidenceRequest
    family_hypothesis: ElliottFamilyEvaluationHypothesis
    component_role_bindings: tuple[FamilyComponentRoleBinding, ...]
    component_endpoint_evidence: tuple[FamilyComponentEndpointEvidence, ...]
    component_path_evidence: tuple[FamilyComponentPathEvidence, ...]
    diagnostics: tuple[str, ...]
    provenance_refs: tuple[str, ...]
    family_validity_authority: bool
    wave_validity_authority: bool
    degree_authority: bool
    _snapshot: tuple[object, ...]

    def __init__(self,*args,**kwargs): raise TypeError("Evidence results are factory-only.")
    def _validated(self):
        if type(self) is not EndpointPathEvidenceResult or _ISSUED.get(self) is not self.component_role_bindings: _fail("Evidence result is unissued or malformed.")
        current=tuple(getattr(self,n) for n in self.__dataclass_fields__ if n!="_snapshot")
        if len(current)!=len(self._snapshot) or any(a is not b for a,b in zip(current,self._snapshot,strict=True)): _fail("Evidence result changed after issuance.")
        self.request._validated()
        for x in self.component_role_bindings: x.__post_init__()
        for x in self.component_endpoint_evidence: x.__post_init__()
        for x in self.component_path_evidence: x.__post_init__()
        if any((self.family_validity_authority,self.wave_validity_authority,self.degree_authority)): _fail("Evidence result cannot carry Elliott authority.")
        return self
    def __reduce_ex__(self,protocol): raise TypeError("Evidence results cannot be pickled.")


_ISSUED: weakref.WeakKeyDictionary[EndpointPathEvidenceResult, tuple[FamilyComponentRoleBinding,...]] = weakref.WeakKeyDictionary()


def build_endpoint_path_evidence(request: EndpointPathEvidenceRequest) -> EndpointPathEvidenceResult:
    if type(request) is not EndpointPathEvidenceRequest: _fail("Builder requires one exact request.")
    request._validated(); h=request.family_hypothesis; pivots=h.generated_candidate.ordered_selected_pivots; roles=_ROLES[h.family_kind]
    if len(roles)>_MAX_COMPONENTS or len(pivots)!=len(roles)+1: _fail("Family role count differs from exact candidate boundaries.")
    windows=tuple(tuple(bar for bar in request.source_observations.bars if pivots[i].timestamp_utc <= bar.timestamp_utc <= pivots[i+1].timestamp_utc) for i in range(len(roles)))
    if any(not w for w in windows): _fail("Every proposed component interval must contain exact source bars.")
    if sum(map(len,windows))>request.max_path_bars: raise EndpointPathEvidenceLimitExceeded("Path-bar preflight bound exceeded; no partial result was issued.")
    bindings=tuple(FamilyComponentRoleBinding(h,h.family_kind,i,role,h.ordered_child_subjects[i],pivots[i],pivots[i+1],request.provenance_refs+pivots[i].provenance_refs+pivots[i+1].provenance_refs+(f"hypothesis-role:{role}",)) for i,role in enumerate(roles))
    endpoints=tuple(FamilyComponentEndpointEvidence(b,b.end_boundary,b.end_boundary.observed_price,b.end_boundary.pivot_kind,b.end_boundary.state,ComponentEndpointState.DEVELOPING_HYPOTHESIS_BOUND_ENDPOINT if b.end_boundary.state is GeometricPivotState.DEVELOPING else ComponentEndpointState.CONFIRMED_BY_GEOMETRY_HYPOTHESIS_BOUND_ENDPOINT,ENDPOINT_AUTHORITY_CLASS,b.provenance_refs,False) for b in bindings)
    paths=tuple(FamilyComponentPathEvidence(b,request.source_observations,w,max(x.high for x in w),min(x.low for x in w),ObservedComponentDirection.UP if b.end_boundary.observed_price>b.start_boundary.observed_price else ObservedComponentDirection.DOWN if b.end_boundary.observed_price<b.start_boundary.observed_price else ObservedComponentDirection.EQUAL,b.provenance_refs,False) for b,w in zip(bindings,windows,strict=True))
    values={"request":request,"family_hypothesis":h,"component_role_bindings":bindings,"component_endpoint_evidence":endpoints,"component_path_evidence":paths,"diagnostics":("HYPOTHESIS_BOUND_ENDPOINT_IS_NOT_ORTHODOX_ENDPOINT","PATH_EXTREME_IS_MARKET_DATA_ONLY","NO_FAMILY_VALIDITY_OR_RULE_EXECUTION","TIMEFRAME_IS_NOT_DEGREE"),"provenance_refs":request.provenance_refs,"family_validity_authority":False,"wave_validity_authority":False,"degree_authority":False}
    result=object.__new__(EndpointPathEvidenceResult)
    for n,v in values.items(): object.__setattr__(result,n,v)
    object.__setattr__(result,"_snapshot",tuple(values.values())); _ISSUED[result]=bindings
    return result._validated()


def validate_endpoint_path_evidence_result(result: object) -> EndpointPathEvidenceResult:
    if type(result) is not EndpointPathEvidenceResult: _fail("Expected one exact evidence result.")
    return result._validated()


__all__=[name for name in globals() if name.isupper() or name.startswith(("Component","Endpoint","FamilyComponent","ObservedComponent","build_","validate_"))]
