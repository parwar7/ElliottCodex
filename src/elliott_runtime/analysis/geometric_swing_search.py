"""Outcome-independent geometric search domain, never Elliott validation.

No consolidation, importance score, cross-discovery splice or certificate.
Returned requests use the existing exact scoped-pivot candidate contract.
"""
from dataclasses import dataclass
from math import isfinite

from .candidate_generation import (
    CandidateGenerationConfig, CandidateGenerationRequest, CandidatePivotWindow,
    estimate_candidate_generation_demand,
)

CLASSIFICATION = 'PROJECT_OPERATIONAL_POLICY'


@dataclass(frozen=True, slots=True)
class GeometricSwingSearchConfig:
    regions: tuple[tuple[int, int], ...]
    sequences_per_region: int
    max_source_pivots: int
    max_source_bars: int


def movement_domain(prices):
    """Compare represented finite values directly; no subtraction/tolerance."""
    if type(prices) is not tuple or len(prices) < 2:
        raise ValueError('An exact tuple of at least two prices is required')
    if any(type(x) not in (int, float) or not isfinite(x) for x in prices):
        raise ValueError('Prices must be finite exact int/float values')
    signs = tuple('UP' if b > a else 'DOWN' if b < a else 'ZERO'
                  for a, b in zip(prices, prices[1:]))
    reasons = []
    if 'ZERO' in signs:
        reasons.append('ZERO_PRICE_MOVEMENT')
    if any(a == b and a != 'ZERO' for a, b in zip(signs, signs[1:])):
        reasons.append('CONSECUTIVE_SAME_DIRECTION')
    return {'eligible': not reasons, 'movements': list(signs),
            'search_exclusion_reasons': reasons,
            'classification': CLASSIFICATION, 'structural_invalidity': False}


def select_geometric_swing_requests(template, config):
    """Enumerate all consecutive scopes, then budget by region, before outcomes.

The template's subject and observation are retained. Different origins remain
different requests even if their prices coincide. This returns no authority
token: downstream callers must execute the returned genuine public requests.
"""
    if type(template) is not CandidateGenerationRequest or type(config) is not GeometricSwingSearchConfig:
        raise ValueError('Exact candidate request and search config required')
    for name, limit, maximum in (
        ('sequences_per_region', config.sequences_per_region, 10),
        ('max_source_pivots', config.max_source_pivots, 10000),
        ('max_source_bars', config.max_source_bars, 10000),
    ):
        if type(limit) is not int or not 0 <= limit <= maximum or (name != 'sequences_per_region' and limit == 0):
            raise ValueError('Invalid operational bound: ' + name)
    if type(config.regions) is not tuple or not 1 <= len(config.regions) <= 20:
        raise ValueError('One to twenty exact chronological regions required')
    last = 0
    for region in config.regions:
        if type(region) is not tuple or len(region) != 2 or any(type(x) is not int for x in region):
            raise ValueError('Regions require exact integer year pairs')
        first, end = region
        if not last < first <= end <= 9999:
            raise ValueError('Regions must be nonoverlapping and chronological')
        last = end
    # Bound before expensive deterministic revalidation. The public request
    # constructor validates the exact geometry/observation relationship.
    from elliott_runtime.market_data.geometric_pivots import GeometricPivotDiscoveryResult
    if type(template.geometric_pivots) is not GeometricPivotDiscoveryResult:
        raise ValueError('Exact discovery result required')
    result = template.geometric_pivots
    if type(result.pivots) is not tuple or len(result.pivots) > config.max_source_pivots or len(template.observations.bars) > config.max_source_bars:
        raise ValueError('Source size exceeds caller operational bound')
    if template.scoped_pivots is not None or template.methodology_delegations:
        raise ValueError('Search template must be unscoped and without methodology delegation')
    c = template.config
    if (c.max_pivots_considered, c.max_candidate_span_pivots, c.max_skipped_pivots, c.pivot_window) != (6, 6, 0, CandidatePivotWindow.EARLIEST):
        raise ValueError('This search uses consecutive six-pivot scopes only')
    CandidateGenerationRequest(template.request_id, template.requested_at_utc,
        template.subject, template.observations, result, c, (), template.provenance_refs)
    estimate_candidate_generation_demand(len(result.pivots), c)
    if any(p.discovery_parameters is not result.config for p in result.pivots):
        raise ValueError('Pivot configuration identity substitution')
    pivots = result.pivots
    regions = [{'years': list(r), 'eligible_starts': [], 'selected_starts': [], 'unvisited_starts': []} for r in config.regions]
    windows = []
    for start in range(max(0, len(pivots) - 5)):
        scope = pivots[start:start + 6]
        domain = movement_domain(tuple(p.observed_price for p in scope))
        region = next((i for i, (a, b) in enumerate(config.regions) if a <= scope[0].timestamp_utc.year and scope[-1].timestamp_utc.year <= b), None)
        disposition = 'SEARCH_DOMAIN_EXCLUDED' if not domain['eligible'] else 'REGION_POLICY_EXCLUDED' if region is None else 'UNVISITED_BUDGET'
        if domain['eligible'] and region is not None:
            regions[region]['eligible_starts'].append(start)
        windows.append({'start_index': start, 'pivot_ids': [p.pivot_id for p in scope],
                        'first_timestamp': scope[0].timestamp_utc.isoformat(), 'last_timestamp': scope[-1].timestamp_utc.isoformat(),
                        'region': region, 'domain': domain, 'disposition': disposition})
    selected = []
    for region in regions:
        starts = region['eligible_starts']
        region['selected_starts'] = starts[:config.sequences_per_region]
        region['unvisited_starts'] = starts[config.sequences_per_region:]
        selected.extend(region['selected_starts'])
    requests = []
    for start in selected:
        windows[start]['disposition'] = 'SELECTED'
        requests.append(CandidateGenerationRequest(
            template.request_id + ':swing:' + str(start), template.requested_at_utc,
            template.subject, template.observations, result,
            CandidateGenerationConfig(6, 6, 0, c.max_candidates_generated, c.allowed_candidate_shapes, CandidatePivotWindow.EARLIEST),
            (), template.provenance_refs, pivots[start:start + 6]))
    bars = template.observations.bars if result.scoped_bars is None else result.scoped_bars
    ties = []
    for index in range(result.config.left_window_bars, len(bars)):
        full = index + result.config.right_window_bars < len(bars)
        if not full and not result.config.include_developing:
            continue
        window = bars[index-result.config.left_window_bars:index+result.config.right_window_bars+1]
        high = max(b.high for b in window); low = min(b.low for b in window)
        hc = sum(b.high == high for b in window); lc = sum(b.low == low for b in window)
        if hc > 1 or lc > 1:
            ties.append({'bar_index_in_scope': index, 'timestamp': bars[index].timestamp_utc.isoformat(), 'high_extreme_ties': hc, 'low_extreme_ties': lc})
    diagnostics = {'classification': CLASSIFICATION, 'geometry_diagnostics': list(result.diagnostics),
                   'equal_extreme_policy': result.config.equal_extreme_policy.value, 'tie_windows': ties,
                   'same_kind_adjacent_pairs': [[a.pivot_id, b.pivot_id] for a,b in zip(pivots,pivots[1:]) if a.pivot_kind is b.pivot_kind],
                   'equal_price_adjacent_pairs': [[a.pivot_id, b.pivot_id] for a,b in zip(pivots,pivots[1:]) if a.observed_price == b.observed_price],
                   'consolidation': 'NONE; retain original emitted pivots; ambiguous dual extrema remain excluded by discovery',
                   'regions': regions, 'windows': windows, 'selected_sequence_count': len(requests),
                   'family_authority': False, 'degree_authority': False, 'structural_invalidity': False}
    return tuple(requests), diagnostics
