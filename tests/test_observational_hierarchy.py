"""Genuine public-factory synthetic fixtures (never analysis data)."""
import copy
from dataclasses import replace
from datetime import datetime
import hashlib
import json
import pickle
import unittest
from zoneinfo import ZoneInfo

import support
import nvda_digital_multidegree as old
from elliott_runtime.market_data.tradingview import load_tradingview_snapshot
from elliott_runtime.market_data.aggregate_extremum import find_extremum_occurrences
from elliott_runtime.analysis.observational_hierarchy import (
    link_observations, validate_observational_graph, ObservationalHierarchyLink, _pair_state, _acyclic,
)

RAW = None


def snapshot(res, dates, levels, *, ties=False, revision=False, forming=False, **context):
    global RAW
    if RAW is None:
        _, RAW = old.tv.load_inputs()
    raw = copy.deepcopy(RAW[res]); rows = []
    for i,(date,level) in enumerate(zip(dates,levels)):
        t = datetime.fromisoformat(date).replace(hour=9,minute=30,tzinfo=ZoneInfo('America/New_York'))
        rows.append({'index':i,'value':[int(t.timestamp()),level,level+1,level-1,level,10]})
    if ties:
        rows[0]['value'][3] = 119
        extra=copy.deepcopy(rows[-1]); extra['index']=len(rows)
        extra['value'][0]+=86400; extra['value'][2]=221; rows.append(extra)
    raw['rows'] = rows
    raw['context'].update(count=len(rows),last_bar_close_time=0 if forming else 1,**context)
    raw['captured_at_utc'] = '2026-09-08T14:00:00Z'
    raw['revision_observation'] = {'rows_changed':[{'synthetic':True}] if revision else []}
    data = json.dumps(raw).encode()
    s = load_tradingview_snapshot(data,expected_sha256=hashlib.sha256(data).hexdigest(),
        expected_resolution=res,source_identifier='SYNTHETIC_LINK_TEST_NOT_NVDA')
    return replace(s,last_bar_forming=forming)


def issue(s, alias):
    cfg = old.geometry(1)
    d = old.p.discover_geometric_pivots(old.p.GeometricPivotDiscoveryRequest(alias,s.observations,cfg,('SYNTHETIC',)))
    times = {b.timestamp_utc for b in s.observations.bars[1:7]}
    selected = tuple(p for p in d.pivots if p.timestamp_utc in times)
    if len(selected) != 6:
        raise AssertionError((len(selected),selected))
    return old.evaluate_scope(alias,old.p.AnalyzedWaveSubject(alias,s.observations.provenance.source_sha256),
        s.observations,d,selected,s.observations.provenance.ingested_at_utc,old.p.MethodologyKernel(support.PROTECTED_ROOT))


def fixture(*, ties=False, reject=False, revision=False, forming=False, **context):
    a = snapshot('1M',['2025-12-01','2026-01-02','2026-02-02','2026-03-02',
        '2026-04-01','2026-05-01','2026-06-01','2026-07-01'],[130,100,160,110,190,120,220,180])
    f = snapshot('1D',['2026-05-01','2026-05-04','2026-05-08','2026-05-12',
        '2026-05-20','2026-05-28','2026-06-05','2026-06-08'],
        [140,120,170,110 if reject else 140,200,160,220,190],ties=ties,revision=revision,forming=forming,**context)
    parent, child = issue(a,'synthetic-parent'), issue(f,'synthetic-child')
    start = find_extremum_occurrences(a,a.observations.bars[5],'low',f,parent_result=parent,role_index=4,edge='start')
    end = find_extremum_occurrences(a,a.observations.bars[6],'high',f,parent_result=parent,role_index=4,edge='end')
    return a,f,parent,child,start,end


def make(values,cache=None,budget=256):
    a,f,p,c,s,e = values
    return link_observations(p,4,c,s,e,max_pairings=budget,cache=cache)


class ObservationalHierarchyTests(unittest.TestCase):
    def test_exact_boundary_supported_link_and_independent_bindings(self):
        values=fixture(); a,f,p,c,s,e=values; b=p.evaluations[0].hypothesis.five_slot_view.binding
        link=make(values)
        self.assertEqual(link.relationship,'BOUNDARY_SUPPORTED_PROPOSED_REFINEMENT')
        self.assertTrue(link.surviving_observational_link)
        self.assertIs(link.start,s); self.assertIs(link.child,c)
        self.assertIs(b,p.evaluations[0].hypothesis.five_slot_view.binding)
        self.assertIsNot(b,c.evaluations[0].hypothesis.five_slot_view.binding)
        self.assertFalse(c.evaluations[0].family_validity_authority)
        self.assertIs(validate_observational_graph((link,),max_links=1)[0],link)

    def test_all_ties_all_pairings_retained(self):
        values=fixture(ties=True); link=make(values)
        self.assertEqual(len(link.pairings),4)
        self.assertEqual(link.relationship,'AMBIGUOUS_ALTERNATIVE_PAIRINGS')
        self.assertEqual({(id(a),id(b)) for a,b,*_ in link.pairings},
            {(id(a),id(b)) for a in values[4].matches for b in values[5].matches})

    def test_p004_rejection_not_rescued_by_p005(self):
        values=fixture(reject=True); link=make(values)
        self.assertTrue(values[3].evaluations[0].p004_result.fatal_to_candidate)
        self.assertFalse(values[2].evaluations[0].p004_result.fatal_to_candidate)
        self.assertTrue(link.p004_rejected); self.assertFalse(link.surviving_observational_link)
        self.assertEqual(link.relationship,'BOUNDARY_SUPPORTED_PROPOSED_REFINEMENT')

    def test_foreign_parent_and_role_rejected(self):
        v=fixture(); a,f,p,c,s,e=v
        with self.assertRaises(ValueError):link_observations(p,3,c,s,e,max_pairings=10)
        with self.assertRaises(ValueError):link_observations(issue(a,'foreign-parent'),4,c,s,e,max_pairings=10)

    def test_foreign_child_snapshot_equal_content_rejected(self):
        a,f,p,c,s,e=fixture()
        foreign=replace(f,observations=replace(f.observations))
        with self.assertRaises(ValueError):link_observations(p,4,issue(foreign,'foreign-child'),s,e,max_pairings=10)

    def test_cross_snapshot_evidence_rejected(self):
        a,f,p,c,s,e=fixture()
        foreign=find_extremum_occurrences(a,a.observations.bars[6],'high',replace(f),parent_result=p,role_index=4,edge='end')
        with self.assertRaises(ValueError):link_observations(p,4,c,s,foreign,max_pairings=10)

    def test_nested_child_binding_substitution_repeated_failure(self):
        v=fixture(); link=make(v); h=v[3].evaluations[0].hypothesis; b=h.five_slot_view.binding
        object.__setattr__(h.five_slot_view,'binding',old.p.OrderedChildBinding(b.binding_id,b.parent_subject,b.ordered_children))
        for _ in range(2):
            with self.assertRaises(ValueError):link.validated()

    def test_nested_parent_mutation_repeated_failure(self):
        v=fixture(); link=make(v); b=v[2].evaluations[0].hypothesis.five_slot_view.binding
        object.__setattr__(b,'parent_subject',old.p.AnalyzedWaveSubject('foreign','foreign'))
        for _ in range(2):
            with self.assertRaises(ValueError):link.validated()

    def test_nested_observation_mutation_rejected(self):
        v=fixture(); link=make(v)
        object.__setattr__(v[1].observations.bars[2],'high',172)
        for _ in range(2):
            with self.assertRaises(ValueError):link.validated()

    def test_equal_pairing_tuple_substitution(self):
        link=make(fixture()); object.__setattr__(link,'pairings',tuple(list(link.pairings)))
        with self.assertRaises(ValueError):link.validated()

    def test_cache_identity_and_stale_failure(self):
        v=fixture(); cache={}; link=make(v,cache)
        self.assertIs(make(v,cache),link)
        object.__setattr__(link,'relationship','INTERIOR_OBSERVATION')
        for _ in range(2):
            with self.assertRaises(ValueError):make(v,cache)

    def test_foreign_cache_value(self):
        v=fixture(); cache={}; make(v,cache); cache[next(iter(cache))]=make(fixture())
        with self.assertRaises(ValueError):make(v,cache)

    def test_mapping_duck_copy_and_pickle_have_no_live_authority(self):
        v=fixture(); link=make(v)
        for value in ({},object(),object.__new__(ObservationalHierarchyLink)):
            with self.assertRaises(ValueError):validate_observational_graph((value,),max_links=2)
        with self.assertRaises(TypeError):pickle.dumps(link)
        with self.assertRaises(TypeError):copy.copy(link)

    def test_pair_budget_preflight_no_truncation(self):
        with self.assertRaises(ValueError):make(fixture(ties=True),budget=3)

    def test_boolean_budget_cannot_alias_cached_integer(self):
        v=fixture(); cache={}; make(v,cache,budget=1)
        with self.assertRaises(ValueError):make(v,cache,budget=True)

    def test_graph_budget_and_distinct_context_retention(self):
        v=fixture(); first=make(v); second=make(v)
        self.assertIsNot(first,second)
        self.assertEqual(len(validate_observational_graph((first,second),max_links=2)),2)
        with self.assertRaises(ValueError):validate_observational_graph((first,second),max_links=1)

    def test_self_link_rejected(self):
        a,f,p,c,s,e=fixture()
        with self.assertRaises(ValueError):link_observations(p,4,p,s,e,max_pairings=10)

    def test_cycle_detection_and_shared_descendant(self):
        with self.assertRaises(ValueError):_acyclic([(1,2),(2,3),(3,1)])
        _acyclic([(1,2),(1,3),(2,4),(3,4)])
        _acyclic([(i,i+1) for i in range(4096)])

    def test_overlap_is_unresolved_not_chosen_instant(self):
        self.assertEqual(_pair_state((0,3),(2,4),(1,2),(3,4),False,False),'UNRESOLVED_OVERLAPPING_INTERVALS')

    def test_reverse_order_rejected(self):
        self.assertEqual(_pair_state((4,5),(1,2),(1,2),(4,5),False,False),'REJECTED_IMPOSSIBLE_ORDER')

    def test_interior_and_uncovered_boundaries(self):
        self.assertEqual(_pair_state((0,1),(9,10),(2,3),(6,7),False,False),'INTERIOR_OBSERVATION')

    def test_crossing_not_contained(self):
        self.assertEqual(_pair_state((0,2),(9,10),(1,3),(8,9),False,False),'UNRESOLVED_BOUNDARY_OVERLAP_OR_CROSSING')

    def test_incompatible_adjustment_remains_incompatible(self):
        link=make(fixture(back_adjustment=False))
        self.assertEqual(link.relationship,'INCOMPATIBLE_METADATA'); self.assertFalse(link.surviving_observational_link)

    def test_unverified_feed_rejected_by_existing_loader(self):
        with self.assertRaises(ValueError):fixture(feed='foreign')

    def test_revision_and_unknown_adjustments_visible(self):
        link=make(fixture(revision=True))
        self.assertIn('SNAPSHOT_REVISION_METADATA_PRESENT_NOT_APPLIED',link.limitations)
        self.assertIn('SPLIT_ADJUSTMENT_SEMANTICS_UNKNOWN',link.limitations)
        self.assertIn('COMPLETE_TRADING_COVERAGE_UNVERIFIED',link.limitations)

    def test_forming_content_substitution_not_refreshed(self):
        v=fixture(forming=True); link=make(v)
        self.assertIn('FINER_BAR_FORMING_OR_UNKNOWN',link.limitations)
        object.__setattr__(v[1],'last_bar_forming',False)
        for _ in range(2):
            with self.assertRaises(ValueError):link.validated()

    def test_no_family_or_degree_authority_fields(self):
        link=make(fixture())
        for name in ('certificate','degree','confidence','score','family_valid','preferred'):
            self.assertFalse(hasattr(link,name))


if __name__=='__main__':unittest.main()
