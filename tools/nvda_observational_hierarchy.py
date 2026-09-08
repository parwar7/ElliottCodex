"""Replay ONLY saved selections; add observation links, never Kernel ancestry."""
import argparse
from collections import Counter
from pathlib import Path

import nvda_aggregate_recent as prior
from elliott_runtime.market_data.aggregate_extremum import find_extremum_occurrences, digest, metadata
from elliott_runtime.analysis.observational_hierarchy import link_observations, validate_observational_graph

old = prior.old
STAGE = 'NVDA-OBSERVATIONAL-HIERARCHY-LINK-AND-REPORT-V1'
PACK = old.ROOT / 'kernel_reviews' / STAGE
PRIOR_HASH = '5d19c4d7530f56f2a319c16b9cbab3c21ffe8ffc1075aafe79a4a256aa19089a'


def integrity():
    assert old.hash_file(prior.PACK / 'REVIEW_manifest.json') == PRIOR_HASH
    manifest = old.read(prior.PACK / 'REVIEW_manifest.json')
    for key, root in (('files', prior.PACK), ('implementation_files', old.ROOT)):
        for entry in manifest[key]:
            path = root / entry['path']
            assert path.stat().st_size == entry['bytes'] and old.hash_file(path) == entry['sha256'], path
    return prior.integrity()


def rebuild(snapshots):
    """Original stable IDs and geometry; reconstruct live evaluations, not certificates."""
    kernel = old.p.MethodologyKernel(Path('C:/ElliottCodex/Brain_LOCKED'))
    jobs, _, _ = old.root_plan(snapshots['1M'].observations, old.read(old.PACK / 'search_plan.json'))
    live = {}
    for alias, discovery, points, _ in jobs:
        if alias not in ('M1', 'M2'):
            continue
        s = snapshots['1M']; identifier = old.STAGE + ':' + alias
        subject = old.p.AnalyzedWaveSubject(identifier, s.observations.provenance.source_sha256)
        live[alias] = old.evaluate_scope(identifier, subject, s.observations, discovery, points,
                                        s.observations.provenance.ingested_at_utc, kernel)
    saved = old.read(prior.PACK / 'canonical_analysis.json')
    expected = {h['display_id']: h for h in saved['hypotheses']}
    cache = {}; config = old.geometry(old.read(prior.PACK / 'search_plan.json')['geometry_width'])
    for search in old.read(prior.PACK / 'selection_before_evaluation.json')['searches']:
        if not search['selected']:
            continue
        snapshot = snapshots[search['resolution']]
        _, discovery = prior.geometry_window(snapshot, *search['window'], config, cache)
        for index in search['selected']:
            alias = search['id'] + ':S' + str(index)
            result = prior.evaluate_independent(prior.STAGE + ':' + alias, snapshot, discovery,
                                                 discovery.pivots[index:index+6], (), kernel)
            row, _ = old.export_hypothesis(result, alias, snapshot.observations)
            for key in ('hypothesis_id', 'endpoints', 'p004', 'p005'):
                if row[key] != expected[alias][key]:
                    raise ValueError('Replay differs from approved hypothesis: ' + alias + '/' + key)
            live[alias] = result
            print('Reconstructed ' + alias, flush=True)
    return live


def build(output=PACK):
    output = Path(output)
    pre = integrity(); old.save(output / 'pre_integrity.json', pre)
    plan = old.read(PACK / 'search_plan.json')
    snapshots, raw = old.tv.load_inputs(); live = rebuild(snapshots)
    if len(live) > plan['max_live_hypotheses']:
        raise ValueError('Hypothesis cap')
    original = {alias: (result.evaluations[0].hypothesis,
                       result.evaluations[0].hypothesis.five_slot_view.binding)
                for alias, result in live.items()}
    by_obs = {id(s.observations): s for s in snapshots.values()}
    doc = {'stage': STAGE, 'inventories': [11,7,0,0], 'scenario_ranking': None,
           'hypotheses': [], 'nodes': [], 'links': [], 'occurrence_evidence': [], 'searches': [],
           'kernel_ancestry_links_added': 0, 'validated_families': 0}
    for alias, result in live.items():
        obs = result.evaluations[0].hypothesis.generated_candidate.source_observations
        row, nodes = old.export_hypothesis(result, alias, obs)
        doc['hypotheses'].append(row); doc['nodes'] += nodes
    planned = []
    for parent_alias, roles in plan['parent_roles'].items():
        parent = live[parent_alias]
        ps = by_obs[id(parent.evaluations[0].hypothesis.generated_candidate.source_observations)]
        for number in roles:
            for child_alias, child in live.items():
                cs = by_obs[id(child.evaluations[0].hypothesis.generated_candidate.source_observations)]
                if cs.observations.timeframe.resolution_seconds < ps.observations.timeframe.resolution_seconds:
                    planned.append((parent_alias, number-1, child_alias, ps, cs))
    if len(planned) > plan['max_links']:
        raise ValueError('Link preflight cap; no partial graph')
    old.save(output / 'planned_links.json', {'links': [(a,r+1,c) for a,r,c,_,_ in planned], 'outcome_selection': False})
    cache = {}; evidence = {}; pending = []; total_pairings = 0
    for pa, index, ca, ps, cs in planned:
        parent = live[pa]; role = parent.evaluations[0].hypothesis.role_bindings[index]
        ev = []
        for side in ('start', 'end'):
            ep = getattr(role, side + '_boundary')
            bar = next(b for b in ps.observations.bars if b.timestamp_utc == ep.timestamp_utc)
            eid = pa + ':role' + str(index+1) + ':' + side + ':' + metadata(cs)['context']['resolution']
            e = evidence.get(eid)
            if e is None:
                e = find_extremum_occurrences(ps, bar, ep.pivot_kind.value.lower(), cs,
                                              parent_result=parent, role_index=index, edge=side, cache=cache)
            evidence[eid] = e; ev.append((eid,e))
        count = len(ev[0][1].matches) * len(ev[1][1].matches)
        if count > plan['max_pairings_per_link']:
            raise ValueError('Pairing preflight cap')
        total_pairings += count
        pending.append((pa,index,ca,ev))
    if total_pairings > plan['max_total_pairings']:
        raise ValueError('Total pairing preflight cap; no truncation')
    print('Boundary preflight complete: '+str(len(evidence))+' evidence records',flush=True)
    links = []
    for pa,index,ca,ev in pending:
        link = link_observations(live[pa], index, live[ca], ev[0][1], ev[1][1], max_pairings=plan['max_pairings_per_link'])
        links.append(link)
        p = live[pa].evaluations[0]; c = live[ca].evaluations[0]
        doc['links'].append({
            'link_id': pa + ':role' + str(index+1) + '=>' + ca,
            'parent_alias': pa, 'child_alias': ca, 'role_number': index+1,
            'parent_hypothesis_id': p.hypothesis.hypothesis_id,
            'parent_binding_id': p.hypothesis.five_slot_view.binding.binding_id,
            'parent_subject': old.p.plain(p.hypothesis.generated_candidate.subject),
            'child_hypothesis_id': c.hypothesis.hypothesis_id,
            'child_binding_id': c.hypothesis.five_slot_view.binding.binding_id,
            'child_subject': old.p.plain(c.hypothesis.generated_candidate.subject),
            'start_evidence_id': ev[0][0], 'end_evidence_id': ev[1][0],
            'relationship': link.relationship, 'limitations': list(link.limitations),
            'pairings': [{'start_bar': a.timestamp_utc.isoformat(), 'end_bar': b.timestamp_utc.isoformat(),
                          'state': state, 'child_start_corresponds': left, 'child_end_corresponds': right}
                         for a,b,state,left,right in link.pairings],
            'p004_rejected': link.p004_rejected, 'surviving_observational_link': link.surviving_observational_link,
            'style': 'REJECTED' if link.p004_rejected else 'OBSERVATIONAL' if link.surviving_observational_link else 'UNRESOLVED',
            'complete_subdivision': False, 'kernel_ancestry': False,
        })
        print('Linked ' + pa + '/' + str(index+1) + ' -> ' + ca + ': ' + link.relationship, flush=True)
    validate_observational_graph(tuple(links), max_links=plan['max_links'])
    doc['occurrence_evidence'] = [prior.evidence_row(k,v) for k,v in evidence.items()]
    doc['totals'] = {'links': len(links), 'pairings': total_pairings,
                     'relationships': dict(Counter(l.relationship for l in links)),
                     'surviving_observational_links': sum(l.surviving_observational_link for l in links),
                     'rejected_link_contexts': sum(l.p004_rejected for l in links),
                     'hypotheses': len(live)}
    doc['input_coverage'] = {k: {'source_hash': s.observations.provenance.source_sha256,
        'metadata': metadata(s), 'bars': len(s.observations.bars), 'last_bar_forming': s.last_bar_forming,
        'first_bar': s.observations.bars[0].timestamp_utc.isoformat(),
        'last_bar': s.observations.bars[-1].timestamp_utc.isoformat(), 'last_close': s.observations.bars[-1].close}
        for k,s in snapshots.items()}
    for alias, result in live.items():
        prior.validate_normal_impulse_partial_evaluation_result(result)
        h = result.evaluations[0].hypothesis
        if original[alias][0] is not h or original[alias][1] is not h.five_slot_view.binding:
            raise ValueError('Original hypothesis identity changed')
        row, _ = old.export_hypothesis(result,alias,h.generated_candidate.source_observations)
        if row != next(r for r in doc['hypotheses'] if r['display_id']==alias):
            raise ValueError('Original represented evidence changed')
    doc['original_results_unchanged'] = True
    # Old canonical hierarchy stays independent. Observation links are a separate collection.
    doc['audit'] = old.audit_hierarchy(doc, snapshots)
    old.save(output / 'canonical_hierarchy.json', doc)
    print(doc['totals'], flush=True)
    return doc


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=PACK)
    build(parser.parse_args().output)
