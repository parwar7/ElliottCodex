"""Factory-issued observation links, NEVER Kernel ancestry or family proof.

Interval containment is an operational relation among saved observations. A
boundary match is not an orthodox endpoint or a claim of complete coverage.
"""
from dataclasses import dataclass
from fractions import Fraction
from weakref import WeakKeyDictionary

from .normal_impulse_partial_evaluation import (
    NormalImpulsePartialEvaluationResult, validate_normal_impulse_partial_evaluation_result,
)
from elliott_runtime.market_data.aggregate_extremum import (
    ExtremumOccurrenceEvidence, occurrence_envelope, observation_identities, digest,
)

_issued = WeakKeyDictionary()
SUPPORTED = frozenset(('INTERIOR_OBSERVATION', 'BOUNDARY_SUPPORTED_PROPOSED_REFINEMENT'))


def _evaluation(result):
    if type(result) is not NormalImpulsePartialEvaluationResult or len(result.evaluations) != 1:
        raise ValueError('Exact single factory-issued evaluation required')
    validate_normal_impulse_partial_evaluation_result(result)
    return result.evaluations[0]


def _bar(snapshot, endpoint):
    field = endpoint.pivot_kind.value.lower()
    if field not in ('high', 'low'):
        raise ValueError('Unsupported endpoint field')
    bar = next((b for b in snapshot.observations.bars if b.timestamp_utc == endpoint.timestamp_utc), None)
    if bar is None or Fraction(getattr(bar, field)) != Fraction(endpoint.observed_price):
        raise ValueError('Endpoint is not its exact represented observation')
    return bar, field


def _inputs(parent, role_index, child, start, end):
    p, c = _evaluation(parent), _evaluation(child)
    if type(role_index) is not int or role_index not in range(5):
        raise ValueError('Exact proposed role index required')
    if parent is child or p.hypothesis.generated_candidate.subject is c.hypothesis.generated_candidate.subject:
        raise ValueError('Independent subjects required; self link forbidden')
    for evidence, side in ((start, 'start'), (end, 'end')):
        if type(evidence) is not ExtremumOccurrenceEvidence:
            raise ValueError('Exact occurrence evidence required')
        evidence.validated()
        if evidence.parent_result is not parent or evidence.role_index != role_index or evidence.edge != side:
            raise ValueError('Foreign parent, role or boundary evidence')
    if start.aggregate is not end.aggregate or start.finer is not end.finer:
        raise ValueError('Cross-snapshot boundary substitution')
    if c.hypothesis.generated_candidate.source_observations is not start.finer.observations:
        raise ValueError('Foreign finer hypothesis snapshot')
    if p.hypothesis.five_slot_view.binding is c.hypothesis.five_slot_view.binding:
        raise ValueError('Independent binding required')
    first = c.hypothesis.role_bindings[0].start_boundary
    last = c.hypothesis.role_bindings[-1].end_boundary
    cb0, cf0 = _bar(start.finer, first)
    cb1, cf1 = _bar(start.finer, last)
    return p, c, cb0, cf0, cb1, cf1


def _pair_state(a, b, first, last, same_start, same_end):
    """Half-open bar envelopes; no chosen instant or intrabar ordering."""
    if b[1] <= a[0]:
        return 'REJECTED_IMPOSSIBLE_ORDER'
    if a[1] > b[0] or first[1] > last[0]:
        return 'UNRESOLVED_OVERLAPPING_INTERVALS'
    left = same_start or a[1] <= first[0]
    right = same_end or last[1] <= b[0]
    if left and right:
        return 'BOUNDARY_SUPPORTED_PROPOSED_REFINEMENT' if same_start and same_end else 'INTERIOR_OBSERVATION'
    if last[1] <= a[0] or first[0] >= b[1]:
        return 'OUTSIDE_SUPPORTED_REGION'
    return 'UNRESOLVED_BOUNDARY_OVERLAP_OR_CROSSING'


def _derive(parent, role_index, child, start, end, max_pairings):
    p, c, cb0, cf0, cb1, cf1 = _inputs(parent, role_index, child, start, end)
    if type(max_pairings) is not int or not 1 <= max_pairings <= 4096:
        raise ValueError('Explicit bounded pairing budget required (1..4096)')
    if len(start.matches) * len(end.matches) > max_pairings:
        raise ValueError('Pairing budget exhausted; no partial link issued')
    limits = tuple(dict.fromkeys(start.limitations + end.limitations + (
        'OBSERVATIONAL_LINK_NOT_KERNEL_ANCESTRY', 'INDEPENDENT_P004_P005_ONLY',
        'UNOBSERVED_BOUNDARY_ALTERNATIVES_NOT_EXCLUDED', 'NO_TERMINAL_OR_FAMILY_PROOF',
    )))
    first, last = occurrence_envelope(start.finer, cb0), occurrence_envelope(start.finer, cb1)
    pairs = []
    if 'INCOMPATIBLE_METADATA' in (start.status, end.status):
        kind = 'INCOMPATIBLE_METADATA'
    elif first is None or last is None or start.interval_evidence is None or end.interval_evidence is None:
        kind = 'UNAVAILABLE_INTERVAL_EVIDENCE'
    elif not start.matches or not end.matches:
        kind = 'MISSING_BOUNDARY_EVIDENCE'
    else:
        for a in start.matches:
            for b in end.matches:
                same_start = a is cb0 and cf0 == start.price_field
                same_end = b is cb1 and cf1 == end.price_field
                state = _pair_state(occurrence_envelope(start.finer, a), occurrence_envelope(start.finer, b),
                                    first, last, same_start, same_end)
                pairs.append((a, b, state, same_start, same_end))
        states = {row[2] for row in pairs}
        kind = next(iter(states)) if len(states) == 1 else 'AMBIGUOUS_ALTERNATIVE_PAIRINGS'
    rejected = bool(p.p004_result.fatal_to_candidate or c.p004_result.fatal_to_candidate)
    return kind, tuple(pairs), limits, rejected, kind in SUPPORTED and not rejected


def _pin(link):
    p, c, cb0, _, cb1, _ = _inputs(link.parent, link.role_index, link.child, link.start, link.end)
    refs = (link.parent, link.child, link.start, link.end, link.pairings, link.limitations, cb0, cb1)
    for h in (p.hypothesis, c.hypothesis):
        b = h.five_slot_view.binding
        refs += (h, h.generated_candidate, h.generated_candidate.subject, h.five_slot_view,
                 b, b.parent_subject, b.ordered_children, h.role_bindings) + b.ordered_children + h.role_bindings
        refs += tuple(v for r in h.role_bindings for v in (r.child_subject, r.start_boundary, r.end_boundary))
    refs += observation_identities(link.start.aggregate) + observation_identities(link.start.finer)
    refs += tuple(row for row in link.pairings)
    # Public parent/child and occurrence validators above own their deep content
    # guards. Do not recursively repr the same large issued graph many times.
    content = digest((link.role_index,
                      link.max_pairings, link.relationship, link.pairings, link.limitations,
                      link.p004_rejected, link.surviving_observational_link))
    return refs, content


@dataclass(frozen=True, slots=True, weakref_slot=True, eq=False, init=False)
class ObservationalHierarchyLink:
    parent: object
    role_index: int
    child: object
    start: ExtremumOccurrenceEvidence
    end: ExtremumOccurrenceEvidence
    max_pairings: int
    relationship: str
    pairings: tuple
    limitations: tuple
    p004_rejected: bool
    surviving_observational_link: bool

    def validated(self):
        if type(self) is not ObservationalHierarchyLink or self not in _issued:
            raise ValueError('Factory-issued live observation link required')
        original, content = _issued[self]
        current, actual = _pin(self)
        if len(current) != len(original) or any(a is not b for a, b in zip(current, original)) or actual != content:
            raise ValueError('Observation link mutated; issuance cannot refresh')
        return self

    def __reduce_ex__(self, protocol):
        raise TypeError('Serialized observation links cannot restore live identity')


def link_observations(parent, role_index, child, start, end, *, max_pairings, cache=None):
    """No writes to input objects. Cache is optional and local, never authority by ID."""
    if cache is not None and type(cache) is not dict:
        raise ValueError('Exact local cache required')
    if type(role_index) is not int or role_index not in range(5) or type(max_pairings) is not int or not 1 <= max_pairings <= 4096:
        raise ValueError('Exact role and explicit integer pairing budget required')
    key = (id(parent), role_index, id(child), id(start), id(end), max_pairings)
    if cache is not None and key in cache:
        value = cache[key]
        if type(value) is not ObservationalHierarchyLink or value.parent is not parent or value.child is not child or value.start is not start or value.end is not end or value.role_index != role_index or value.max_pairings != max_pairings:
            raise ValueError('Foreign cached link')
        return value.validated()
    values = _derive(parent, role_index, child, start, end, max_pairings)
    link = object.__new__(ObservationalHierarchyLink)
    for name, value in zip(ObservationalHierarchyLink.__dataclass_fields__,
                           (parent, role_index, child, start, end, max_pairings) + values):
        object.__setattr__(link, name, value)
    _issued[link] = _pin(link)
    if cache is not None:
        cache[key] = link
    return link


def validate_observational_graph(links, *, max_links):
    if type(links) is not tuple or type(max_links) is not int or not 1 <= max_links <= 4096 or len(links) > max_links:
        raise ValueError('Explicit bounded tuple of links required')
    edges = []
    for link in links:
        if type(link) is not ObservationalHierarchyLink:
            raise ValueError('Exact observation link required')
        link.validated()
        edges.append((id(link.parent), id(link.child)))
    _acyclic(edges)
    return links


def _acyclic(edges):
    graph, degrees = {}, {}
    for parent, child in edges:
        degrees.setdefault(parent,0); degrees.setdefault(child,0)
        targets=graph.setdefault(parent,set())
        if child not in targets:
            targets.add(child); degrees[child]+=1
    ready=[node for node,degree in degrees.items() if degree==0]; visited=0
    while ready:
        node=ready.pop(); visited+=1
        for child in graph.get(node,()):
            degrees[child]-=1
            if degrees[child]==0:ready.append(child)
    if visited!=len(degrees):raise ValueError('Observational cycle rejected')
