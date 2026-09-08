"""Exact saved and explicitly synthetic TradingView fixtures; no network."""
import copy
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
import math
import pickle
import unittest
import support
import nvda_digital_multidegree as old
import nvda_aggregate_recent as runner
from elliott_runtime.market_data.tradingview import load_tradingview_snapshot
from elliott_runtime.market_data.aggregate_extremum import find_extremum_occurrences, interval, occurrence_envelope
from elliott_methodology_kernel import AnalyzedWaveSubject, OrderedChildBinding


def synthetic(res, dates, prices, **context):
    _,all_raw=old.tv.load_inputs();data=copy.deepcopy(all_raw[res])
    data['rows']=[{'index':i,'value':[int(datetime.fromisoformat(t).timestamp()),100,p,80,100,10]} for i,(t,p) in enumerate(zip(dates,prices))]
    data['context'].update(count=len(dates),last_bar_close_time=0,**context)
    data['captured_at_utc']='2026-09-08T14:00:00Z';data['revision_observation']={'rows_changed':[]}
    raw=json.dumps(data).encode()
    return load_tradingview_snapshot(raw,expected_sha256=hashlib.sha256(raw).hexdigest(),expected_resolution=res,source_identifier='SYNTHETIC_NOT_NVDA_ANALYSIS')


def pair(tie=False):
    a=synthetic('1M',['2026-05-01T13:30:00+00:00'],[236.54])
    f=synthetic('1D',['2026-05-14T13:30:00+00:00','2026-05-15T13:30:00+00:00'],[236.54,236.54 if tie else 235])
    return a,f


def bound_parent():
    s,_=old.tv.load_inputs();jobs,_,_=old.root_plan(s['1M'].observations,old.read(old.PACK/'search_plan.json'))
    _,discovery,points,_=next(j for j in jobs if j[0]=='M1')
    kernel=old.p.MethodologyKernel(support.PROTECTED_ROOT)
    parent=old.evaluate_scope('genuine-parent',AnalyzedWaveSubject('genuine-parent',s['1M'].observations.provenance.source_sha256),s['1M'].observations,discovery,points,s['1M'].observations.provenance.ingested_at_utc,kernel)
    bar=next(b for b in s['1M'].observations.bars if b.timestamp_utc==points[-1].timestamp_utc)
    return s,parent,bar,kernel


class AggregateExtremumTests(unittest.TestCase):
    def test_calendar_month_not_nominal_seconds(self):
        a,f=pair();bounds=interval(a,a.observations.bars[0])
        self.assertEqual(bounds[0].isoformat(),'2026-05-01T04:00:00+00:00')
        self.assertEqual(bounds[1].isoformat(),'2026-06-01T04:00:00+00:00')
        self.assertNotEqual((bounds[1]-bounds[0]).total_seconds(),a.observations.timeframe.resolution_seconds)
    def test_month_dst_and_leap_year_boundaries(self):
        a=synthetic('1M',['2026-03-02T14:30:00+00:00'],[236.54])
        lo,hi,_=interval(a,a.observations.bars[0])
        self.assertEqual((hi-lo).total_seconds(),(31*24-1)*3600)
        a=synthetic('1M',['2024-02-01T14:30:00+00:00'],[236.54])
        lo,hi,_=interval(a,a.observations.bars[0]);self.assertEqual((hi-lo).days,29)
    def test_metadata_cannot_relabel_observation_resolution(self):
        a,f=pair();meta=json.loads(f.metadata_json);meta['context']['resolution']='15'
        with self.assertRaises(ValueError):find_extremum_occurrences(a,a.observations.bars[0],'high',replace(f,metadata_json=json.dumps(meta)))
    def test_boolean_adjustment_not_numeric_alias(self):
        a,f=pair();meta=json.loads(f.metadata_json);meta['context']['dividend_adjustment']=0
        e=find_extremum_occurrences(a,a.observations.bars[0],'high',replace(f,metadata_json=json.dumps(meta)))
        self.assertEqual(e.status,'INCOMPATIBLE_METADATA')
    def test_all_exact_ties_preserved(self):
        a,f=pair(True);e=find_extremum_occurrences(a,a.observations.bars[0],'high',f)
        self.assertEqual(e.status,'MULTIPLE_OBSERVED_MATCHES');self.assertEqual(len(e.matches),2)
        self.assertIs(e.matches[0],f.observations.bars[0]);self.assertIs(e.matches[1],f.observations.bars[1])
    def test_near_price_not_match(self):
        a,f=pair();object.__setattr__(f.observations.bars[0],'high',math.nextafter(236.54,math.inf))
        e=find_extremum_occurrences(a,a.observations.bars[0],'high',f)
        self.assertFalse(e.matches);self.assertEqual(e.status,'NO_OBSERVED_MATCH_IN_AVAILABLE_ROWS')
        self.assertIn('COMPLETE_TRADING_COVERAGE_UNVERIFIED',e.limitations)
    def test_only_same_field(self):
        a,f=pair();e=find_extremum_occurrences(a,a.observations.bars[0],'low',f)
        self.assertEqual(len(e.matches),2)
        with self.assertRaises(ValueError):find_extremum_occurrences(a,a.observations.bars[0],'close',f)
    def test_half_open_boundary_excludes_next_month(self):
        a,f=pair();f=synthetic('1D',['2026-06-01T13:30:00+00:00'],[236.54])
        e=find_extremum_occurrences(a,a.observations.bars[0],'high',f)
        self.assertEqual(e.status,'NO_FINER_COVERAGE');self.assertFalse(e.matches)
    def test_month_start_included_when_regular_session(self):
        a,f=pair();f=synthetic('1D',['2026-05-01T13:30:00+00:00'],[236.54])
        self.assertEqual(len(find_extremum_occurrences(a,a.observations.bars[0],'high',f).matches),1)
    def test_incompatible_session_no_comparison(self):
        a,f=pair();meta=json.loads(f.metadata_json);meta['context']['resolved_session']='0400-2000'
        f=replace(f,metadata_json=json.dumps(meta));e=find_extremum_occurrences(a,a.observations.bars[0],'high',f)
        self.assertEqual(e.status,'INCOMPATIBLE_METADATA');self.assertFalse(e.matches)
    def test_incompatible_adjustment_and_feed(self):
        for key,value in [('back_adjustment',False),('dividend_adjustment',True),('feed','foreign'),('currency','EUR')]:
            a,f=pair();meta=json.loads(f.metadata_json);meta['context'][key]=value
            e=find_extremum_occurrences(a,a.observations.bars[0],'high',replace(f,metadata_json=json.dumps(meta)))
            self.assertEqual(e.status,'INCOMPATIBLE_METADATA')
    def test_unknown_split_and_non_synchronous_preserved(self):
        a,f=pair();meta=json.loads(f.metadata_json);meta['captured_at_utc']='2026-09-08T13:49:00Z'
        e=find_extremum_occurrences(a,a.observations.bars[0],'high',replace(f,metadata_json=json.dumps(meta)))
        self.assertIn('SPLIT_ADJUSTMENT_SEMANTICS_UNKNOWN',e.limitations)
        self.assertIn('NON_SYNCHRONOUS_CAPTURES',e.limitations)
    def test_forming_is_not_no_match_or_completion(self):
        a,f=pair();a=replace(a,last_bar_forming=True)
        e=find_extremum_occurrences(a,a.observations.bars[0],'high',f)
        self.assertEqual(e.status,'UNIQUE_OBSERVED_MATCH');self.assertIn('AGGREGATE_BAR_FORMING',e.limitations)
    def test_revision_flag_not_silently_applied(self):
        a,f=pair();meta=json.loads(f.metadata_json);meta['revision_observation']={'rows_changed':[{'note':'synthetic revision'}]}
        e=find_extremum_occurrences(a,a.observations.bars[0],'high',replace(f,metadata_json=json.dumps(meta)))
        self.assertIn('SNAPSHOT_REVISION_METADATA_PRESENT_NOT_APPLIED',e.limitations)
    def test_exact_occurrence_is_interval_not_instant(self):
        a,f=pair();bounds=occurrence_envelope(f,f.observations.bars[0])
        self.assertEqual((bounds[1]-bounds[0]).total_seconds(),6.5*3600)
    def test_unknown_calendar_basis(self):
        a,f=pair();meta=json.loads(a.metadata_json);meta['context']['resolved_session']='unknown'
        a=replace(a,metadata_json=json.dumps(meta));f=replace(f,metadata_json=json.dumps(dict(json.loads(f.metadata_json),context=meta['context'])))
        self.assertIsNone(interval(a,a.observations.bars[0]))
    def test_foreign_equal_bar_rejected(self):
        a,f=pair()
        with self.assertRaises(ValueError):find_extremum_occurrences(a,replace(a.observations.bars[0]),'high',f)
    def test_nested_price_mutation_repeated_failure(self):
        a,f=pair();e=find_extremum_occurrences(a,a.observations.bars[0],'high',f)
        object.__setattr__(f.observations.bars[0],'high',237)
        for _ in range(2):
            with self.assertRaises(ValueError):e.validated()
    def test_equal_foreign_snapshot_and_tuple_substitution(self):
        for attribute in ('finer','matches'):
            a,f=pair();e=find_extremum_occurrences(a,a.observations.bars[0],'high',f)
            object.__setattr__(e,attribute,replace(f) if attribute=='finer' else tuple(list(e.matches)))
            with self.assertRaises(ValueError):e.validated()
    def test_equal_nested_observation_record_substitution(self):
        for target in ('provenance','timeframe','symbol','quality','bar_provenance','provenance_resolution'):
            a,f=pair();e=find_extremum_occurrences(a,a.observations.bars[0],'high',f)
            if target=='bar_provenance':
                b=f.observations.bars[0];object.__setattr__(b,'provenance',replace(b.provenance))
            elif target=='provenance_resolution':
                p=f.observations.provenance;object.__setattr__(p,'source_resolution',replace(p.source_resolution))
            else:object.__setattr__(f.observations,target,replace(getattr(f.observations,target)))
            for _ in range(2):
                with self.assertRaises(ValueError):e.validated()
    def test_cache_reuse_and_substitution(self):
        a,f=pair();cache={};e=find_extremum_occurrences(a,a.observations.bars[0],'high',f,cache=cache)
        self.assertIs(e,find_extremum_occurrences(a,a.observations.bars[0],'high',f,cache=cache))
        cache[next(iter(cache))]=find_extremum_occurrences(a,a.observations.bars[0],'low',f)
        with self.assertRaises(ValueError):find_extremum_occurrences(a,a.observations.bars[0],'high',f,cache=cache)
    def test_cache_mutation_not_refreshed(self):
        a,f=pair();cache={};find_extremum_occurrences(a,a.observations.bars[0],'high',f,cache=cache)
        object.__setattr__(f,'last_bar_forming',True)
        for _ in range(2):
            with self.assertRaises(ValueError):find_extremum_occurrences(a,a.observations.bars[0],'high',f,cache=cache)
    def test_no_pickle_authority(self):
        a,f=pair();e=find_extremum_occurrences(a,a.observations.bars[0],'high',f)
        with self.assertRaises(TypeError):pickle.dumps(e)
    def test_original_parent_pinned_and_unchanged(self):
        s,parent,bar,k=bound_parent();binding=parent.evaluations[0].hypothesis.five_slot_view.binding
        e=find_extremum_occurrences(s['1M'],bar,'high',s['1D'],parent_result=parent,role_index=4,edge='end')
        self.assertIs(e,e.validated());self.assertIs(binding,parent.evaluations[0].hypothesis.five_slot_view.binding)
        object.__setattr__(binding,'parent_subject',AnalyzedWaveSubject('foreign','foreign'))
        for _ in range(2):
            with self.assertRaises(ValueError):e.validated()
    def test_equivalent_parent_binding_substitution(self):
        s,parent,bar,k=bound_parent();h=parent.evaluations[0].hypothesis;b=h.five_slot_view.binding
        e=find_extremum_occurrences(s['1M'],bar,'high',s['1D'],parent_result=parent,role_index=4,edge='end')
        object.__setattr__(h.five_slot_view,'binding',OrderedChildBinding(b.binding_id,b.parent_subject,b.ordered_children))
        with self.assertRaises(ValueError):e.validated()
    def test_new_hypothesis_owns_operands_and_binding(self):
        s,parent,bar,k=bound_parent();e=find_extremum_occurrences(s['1M'],bar,'high',s['60'],parent_result=parent,role_index=4,edge='end')
        bars,discovery=runner.geometry_window(s['60'],'2026-05-01','2026-06-01',old.geometry(2),{})
        points=next(discovery.pivots[i:i+6] for i in range(len(discovery.pivots)-5) if old.movement_domain(tuple(p.observed_price for p in discovery.pivots[i:i+6]))['eligible'])
        result=runner.evaluate_independent('new-own-evidence',s['60'],discovery,points,(e,),k)
        h=result.evaluations[0].hypothesis
        self.assertIs(h.generated_candidate.source_observations,s['60'].observations)
        self.assertIsNot(h.five_slot_view.binding,parent.evaluations[0].hypothesis.five_slot_view.binding)
        self.assertIsNot(result.evaluations[0].p004_result,parent.evaluations[0].p004_result)
        self.assertIsNot(result.evaluations[0].p005_result,parent.evaluations[0].p005_result)
        self.assertFalse(result.evaluations[0].family_validity_authority)
    def test_geometry_cache_substitution_and_nested_mutation(self):
        s,_=old.tv.load_inputs();cache={};g=old.geometry(2)
        bars,d=runner.geometry_window(s['60'],'2026-05-01','2026-06-01',g,cache)
        self.assertIs(d,runner.geometry_window(s['60'],'2026-05-01','2026-06-01',g,cache)[1])
        object.__setattr__(bars[0],'high',bars[0].high+1)
        for _ in range(2):
            with self.assertRaises(ValueError):runner.geometry_window(s['60'],'2026-05-01','2026-06-01',g,cache)
    def test_geometry_cache_equal_result_substitution(self):
        s,_=old.tv.load_inputs();cache={};g=old.geometry(2)
        bars,d=runner.geometry_window(s['60'],'2026-05-01','2026-06-01',g,cache)
        key=next(iter(cache));original,parameters,bars,discovery,fingerprint,identities=cache[key]
        cache[key]=(original,parameters,bars,replace(discovery),fingerprint,identities)
        for _ in range(2):
            with self.assertRaises(ValueError):runner.geometry_window(s['60'],'2026-05-01','2026-06-01',g,cache)
    def test_geometry_cache_equal_nested_pivots_substitution(self):
        s,_=old.tv.load_inputs();cache={};g=old.geometry(2)
        bars,d=runner.geometry_window(s['60'],'2026-05-01','2026-06-01',g,cache)
        object.__setattr__(d,'pivots',tuple(list(d.pivots)))
        for _ in range(2):
            with self.assertRaises(ValueError):runner.geometry_window(s['60'],'2026-05-01','2026-06-01',g,cache)
    def test_geometry_cache_equal_nested_provenance_substitution(self):
        s,_=old.tv.load_inputs();cache={};g=old.geometry(2)
        runner.geometry_window(s['60'],'2026-05-01','2026-06-01',g,cache)
        object.__setattr__(s['60'].observations,'provenance',replace(s['60'].observations.provenance))
        for _ in range(2):
            with self.assertRaises(ValueError):runner.geometry_window(s['60'],'2026-05-01','2026-06-01',g,cache)
    def test_geometry_cache_equal_pivot_config_substitution(self):
        s,_=old.tv.load_inputs();cache={};g=old.geometry(2)
        bars,d=runner.geometry_window(s['60'],'2026-05-01','2026-06-01',g,cache)
        object.__setattr__(d.pivots[0],'discovery_parameters',replace(g))
        for _ in range(2):
            with self.assertRaises(ValueError):runner.geometry_window(s['60'],'2026-05-01','2026-06-01',g,cache)


if __name__=='__main__':unittest.main()
