"""Bounded, caller-declared subhypotheses over existing Normal Impulse roles.

This is operational orchestration, NOT family-requirement proof or a second
certification system. All methodology and recursive aggregation are delegated.
Partial temporal containment does not establish coincident Elliott endpoints.
"""
from dataclasses import dataclass, field
import copy
import hashlib

from elliott_methodology_kernel import (
    OrderedChildBinding,
    RecursiveCandidateCompositionRequest,
)
from elliott_methodology_kernel.contracts import NormalizedMarketObservations
from elliott_runtime.market_data.geometric_pivots import (
    GeometricPivotDiscoveryConfig, GeometricPivotDiscoveryRequest,
    GeometricPivotDiscoveryResult, discover_geometric_pivots,
)
from .candidate_generation import (
    CandidateGenerationRequest, CandidateGenerationConfig, CandidatePivotWindow,
    CandidateHypothesisShape, generate_candidate_hypotheses,
)
from .competing_candidates import CompetingCandidateSetRequest, build_competing_candidate_set
from .family_hypotheses import FamilyHypothesisBridgeRequest, FamilyEvaluationKind, build_family_evaluation_hypotheses
from .normal_impulse_partial_evaluation import (
    NormalImpulsePartialEvaluationResult, NormalImpulsePartialEvaluationRequest,
    validate_normal_impulse_partial_evaluation_result, evaluate_normal_impulse_partial_scope,
)
from .geometric_swing_search import movement_domain

CLASSIFICATION='CALLER_SUPPLIED_PARTIAL_COMPONENT_EXPLORATION'

def _digest(value):
    return hashlib.sha256(repr(value).encode('utf-8')).hexdigest()

def evaluate_scope(identifier, subject, observations, discovery, selected, at, kernel):
    """One five-segment hypothesis through unchanged public factories."""
    refs=(CLASSIFICATION, identifier, observations.provenance.source_sha256)
    request=CandidateGenerationRequest(identifier,at,subject,observations,discovery,
        CandidateGenerationConfig(6,6,0,1,(CandidateHypothesisShape.FIVE_SEGMENT_HYPOTHESIS,),CandidatePivotWindow.EARLIEST),(),refs,selected)
    generated=generate_candidate_hypotheses(request)
    competing=build_competing_candidate_set(CompetingCandidateSetRequest(identifier+':set',identifier,generated,refs))
    # Ending-diagonal cardinality supplies the existing five-slot bridge ONLY.
    # It is not evidence of diagonal position, internals, geometry or family.
    bridge=build_family_evaluation_hypotheses(FamilyHypothesisBridgeRequest(identifier+':bridge',at,competing,(FamilyEvaluationKind.ENDING_DIAGONAL,),refs),kernel)
    return evaluate_normal_impulse_partial_scope(NormalImpulsePartialEvaluationRequest(identifier+':partial',at,bridge,1,1,1,refs),kernel)

@dataclass(frozen=True, slots=True, eq=False)
class ComponentSearch:
    parent_result: NormalImpulsePartialEvaluationResult
    evaluation_index: int
    role_index: int
    observations: NormalizedMarketObservations
    discovery: GeometricPivotDiscoveryResult | None
    bars: tuple
    coverage: str
    _identities: tuple = field(init=False,repr=False)
    _content: str = field(init=False,repr=False)

    def __post_init__(self):
        self._check_values()
        current=self._current()
        content=_digest((self.observations,self.discovery,self.bars,self.coverage))
        if hasattr(self,'_identities'):
            if any(a is not b for a,b in zip(current,self._identities,strict=True)) or content!=self._content:
                raise ValueError('Component search changed; issuance evidence cannot be refreshed')
        else:
            object.__setattr__(self,'_identities',current)
            object.__setattr__(self,'_content',content)

    def _current(self):
        item=self.parent_result.evaluations[self.evaluation_index]
        role=item.hypothesis.role_bindings[self.role_index]
        binding=item.hypothesis.five_slot_view.binding
        return (self.parent_result,self.evaluation_index,self.role_index,self.observations,self.discovery,self.bars,self.coverage,
            item,role,binding,binding.parent_subject,binding.ordered_children,role.child_subject,role.start_boundary,role.end_boundary)

    def _check_values(self):
        if type(self) is not ComponentSearch or type(self.parent_result) is not NormalImpulsePartialEvaluationResult:
            raise ValueError('Exact component search and issued parent result required')
        validate_normal_impulse_partial_evaluation_result(self.parent_result)
        if type(self.evaluation_index) is not int or not 0<=self.evaluation_index<len(self.parent_result.evaluations):
            raise ValueError('Invalid parent index')
        if type(self.role_index) is not int or self.role_index not in (0,2,4):
            raise ValueError('Only caller-selected actionary slots 1/3/5; correction proof unavailable')
        if type(self.observations) is not NormalizedMarketObservations or type(self.bars) is not tuple:
            raise ValueError('Exact observation snapshot and tuple required')
        parent=self.parent_result.evaluations[self.evaluation_index]
        role=parent.hypothesis.role_bindings[self.role_index]
        old=parent.hypothesis.generated_candidate.source_observations
        if self.observations.symbol!=old.symbol or self.observations.timeframe.resolution_seconds>=old.timeframe.resolution_seconds:
            raise ValueError('Explicit compatible finer observation resolution required, not inferred degree')
        start,end=role.start_boundary.timestamp_utc,role.end_boundary.timestamp_utc
        expected=tuple(b for b in self.observations.bars if start<=b.timestamp_utc<=end)
        if len(expected)!=len(self.bars) or any(a is not b for a,b in zip(expected,self.bars,strict=True)):
            raise ValueError('Foreign/reordered/out-of-window observation bars')
        if self.discovery is not None:
            if type(self.discovery) is not GeometricPivotDiscoveryResult or self.discovery.input_observations is not self.observations or self.discovery.scoped_bars is not self.bars:
                raise ValueError('Foreign discovery snapshot/window')
        first,last=self.observations.bars[0].timestamp_utc,self.observations.bars[-1].timestamp_utc
        coverage='NO_FINER_COVERAGE' if not self.bars else 'PARTIAL_FINER_HISTORY' if first>start or last<end else 'AVAILABLE_WITHIN_TIMESTAMP_WINDOW'
        if self.coverage!=coverage:raise ValueError('Coverage changed')

    def validated(self):
        self.__post_init__()
        return self

    def __reduce_ex__(self, protocol):
        raise TypeError('Live component links cannot be restored from serialized reports')

def prepare_component_search(parent_result, evaluation_index, role_index, observations, geometry, cache=None):
    """Cache geometry only. Exact contextual subjects/results are never cached."""
    validate_normal_impulse_partial_evaluation_result(parent_result)
    if type(observations) is not NormalizedMarketObservations or type(geometry) is not GeometricPivotDiscoveryConfig:
        raise ValueError('Exact finer snapshot and geometry required')
    if type(evaluation_index) is not int or not 0<=evaluation_index<len(parent_result.evaluations) or type(role_index) is not int or role_index not in (0,2,4):
        raise ValueError('Invalid parent/role index')
    role=parent_result.evaluations[evaluation_index].hypothesis.role_bindings[role_index]
    start,end=role.start_boundary.timestamp_utc,role.end_boundary.timestamp_utc
    key=(id(observations),id(geometry),start,end)
    if cache is not None and key in cache:
        original,parameters,bars,discovery,digest=cache[key]
        if original is not observations or parameters is not geometry or digest!=_digest((observations,bars,discovery)):
            raise ValueError('Cached geometry mutated; no snapshot refresh')
    else:
        bars=tuple(b for b in observations.bars if start<=b.timestamp_utc<=end)
        if len(bars)>10000:raise ValueError('Component bar budget exceeded')
        discovery=None
        if bars:
            identifier='component-geometry:'+hashlib.sha256((observations.provenance.source_sha256+repr((start,end,geometry))).encode()).hexdigest()[:24]
            discovery=discover_geometric_pivots(GeometricPivotDiscoveryRequest(identifier,observations,geometry,(CLASSIFICATION,),bars))
        if cache is not None:cache[key]=(observations,geometry,bars,discovery,_digest((observations,bars,discovery)))
    coverage='NO_FINER_COVERAGE' if not bars else 'PARTIAL_FINER_HISTORY' if observations.bars[0].timestamp_utc>start or observations.bars[-1].timestamp_utc<end else 'AVAILABLE_WITHIN_TIMESTAMP_WINDOW'
    return ComponentSearch(parent_result,evaluation_index,role_index,observations,discovery,bars,coverage)

def plan_component(search):
    search.validated()
    pivots=() if search.discovery is None else search.discovery.pivots
    windows=[];eligible=[]
    for i in range(max(0,len(pivots)-5)):
        scope=pivots[i:i+6];domain=movement_domain(tuple(p.observed_price for p in scope))
        if domain['eligible']:eligible.append(i)
        windows.append({'start_index':i,'pivot_ids':[p.pivot_id for p in scope],'domain':domain,'disposition':'DOMAIN_EXCLUDED' if not domain['eligible'] else 'UNVISITED_BUDGET'})
    selected=list(dict.fromkeys([eligible[0],eligible[-1]])) if eligible else []
    for i in selected:windows[i]['disposition']='SELECTED'
    reason='SCOPES_SELECTED' if selected else 'NO_FINER_COVERAGE' if not search.bars else 'INSUFFICIENT_GEOMETRIC_PIVOTS' if len(pivots)<6 else 'NO_SEQUENCE_IN_SEARCH_DOMAIN'
    return {'coverage':search.coverage,'bars':len(search.bars),'pivot_count':len(pivots),'selected_starts':selected,'windows':windows,'reason':reason,'exhaustive':False,'authority':False}

@dataclass(frozen=True, slots=True, eq=False)
class ComponentEvaluation:
    search: ComponentSearch
    children: tuple
    compositions: tuple
    _identities: tuple=field(init=False,repr=False)

    def __post_init__(self):
        if type(self) is not ComponentEvaluation or type(self.search) is not ComponentSearch or type(self.children) is not tuple or type(self.compositions) is not tuple:
            raise ValueError('Exact component result transport required')
        current=(self.search,self.children,self.compositions)
        if hasattr(self,'_identities') and any(a is not b for a,b in zip(current,self._identities,strict=True)):
            raise ValueError('Component result substituted')
        self.search.validated()
        parent=self.search.parent_result.evaluations[self.search.evaluation_index]
        role=parent.hypothesis.role_bindings[self.search.role_index]
        if len(self.children)!=len(self.compositions):raise ValueError('Composition count differs')
        if parent.p004_result.fatal_to_candidate and self.children:raise ValueError('Rejected parent cannot present surviving descendants')
        for child,composition in zip(self.children,self.compositions,strict=True):
            validate_normal_impulse_partial_evaluation_result(child)
            if len(child.evaluations)!=1:raise ValueError('One exact child hypothesis per alternative required')
            item=child.evaluations[0];candidate=item.hypothesis.generated_candidate
            if candidate.subject is not role.child_subject or candidate.source_observations is not self.search.observations or candidate.source_geometric_pivots is not self.search.discovery:
                raise ValueError('Foreign child subject, snapshot or discovery')
            points=candidate.ordered_selected_pivots
            if not role.start_boundary.timestamp_utc<=points[0].timestamp_utc<points[-1].timestamp_utc<=role.end_boundary.timestamp_utc:
                raise ValueError('Child escaped exact parent interval')
            copy.copy(composition)
            if composition.parent_candidate_result is not parent.bounded_result or composition.ordered_child_candidate_results!=(item.bounded_result,):
                raise ValueError('Foreign recursive composition result')
            if composition.child_binding.parent_subject is not parent.bounded_result.subject or composition.child_binding.ordered_children!=(role.child_subject,):
                raise ValueError('Foreign composition ancestry')
        if not hasattr(self,'_identities'):object.__setattr__(self,'_identities',current)

    def validated(self):
        self.__post_init__();return self

    def __reduce_ex__(self,protocol):raise TypeError('Serialized hierarchy grants no live authority')

def evaluate_component(search, at, kernel, identifier):
    search.validated();parent=search.parent_result.evaluations[search.evaluation_index]
    if parent.p004_result.fatal_to_candidate:return ComponentEvaluation(search,(),())
    role=parent.hypothesis.role_bindings[search.role_index]
    children=[];compositions=[]
    for i in plan_component(search)['selected_starts']:
        child=evaluate_scope(identifier+':'+str(i),role.child_subject,search.observations,search.discovery,search.discovery.pivots[i:i+6],at,kernel)
        item=child.evaluations[0]
        binding=OrderedChildBinding(identifier+':partial-binding:'+str(i),parent.bounded_result.subject,(role.child_subject,))
        composition=kernel.compose_recursive_candidate(RecursiveCandidateCompositionRequest(identifier+':composition:'+str(i),parent.bounded_result,(item.bounded_result,),binding,(CLASSIFICATION,'Omitted sibling roles remain unresolved')))
        children.append(child);compositions.append(composition)
    return ComponentEvaluation(search,tuple(children),tuple(compositions))
