"""Deterministic adapter and guarded transport regressions; no live requests."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

from elliott_runtime.market_data.tradingview import load_tradingview_snapshot, MarketDataError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from tradingview_digital_tools import TradingViewDigitalBridge, TradingViewDigitalError, SAFE_INPUTS

def fixture():
    return {'schema':'TRADINGVIEW_LOADED_OHLCV_V1','columns':['time','open','high','low','close','volume'],
      'captured_at_utc':'2026-09-08T14:00:00Z','context':{
      'symbol':'BATS:NVDA','listing':'NASDAQ:NVDA','feed':'Cboe One','exchange_timezone':'America/New_York',
      'currency':'USD','session':'regular','resolution':'1D','loading':False,'failed':False,'replay':False,'chart_type':1,
      'count':2,'dividend_adjustment':False,'back_adjustment':True,'split_adjustment':None,'last_bar_close_time':1788897599},
      'capture_request':{'stop_reason':'NO_ADDITIONAL_BARS_RETURNED'},
      'rows':[{'index':0,'value':[1788528600,231.09,234.76,229.63,230.36,None]},
              {'index':1,'value':[1788874200,233.14,233.71,229.06,230,100]}]}

def load(d,**kw):
    raw=json.dumps(d,allow_nan=True).encode()
    return load_tradingview_snapshot(raw,expected_sha256=hashlib.sha256(raw).hexdigest(),expected_resolution='1D',source_identifier='fixture',**kw)

class TradingViewAdapterTests(unittest.TestCase):
    def test_exact_values_feed_and_provenance(self):
        d=fixture(); got=load(d);o=got.observations
        self.assertEqual(o.symbol.provider_symbol,'BATS:NVDA');self.assertEqual(o.symbol.exchange,'BATS')
        self.assertEqual(o.bars[0].high,234.76);self.assertIsNone(o.bars[0].volume)
        self.assertEqual(o.provenance.source_type,'tradingview_loaded_chart');self.assertFalse(o.provenance.resampled)
        self.assertEqual(o.bars[0].timestamp_utc.isoformat(),'2026-09-04T13:30:00+00:00')
        self.assertTrue(got.last_bar_forming)
    def test_replay_is_equal_not_authority_deserialization(self):
        a,b=load(fixture()),load(fixture());self.assertEqual(a,b);self.assertIsNot(a.observations,b.observations)
    def test_partial_history_retained(self):
        got=load(fixture());self.assertIn('NO_ADDITIONAL_BARS',got.metadata_json);self.assertEqual(len(got.observations.bars),2)
    def test_wrong_context_rejected(self):
        for k,v in [('symbol','NASDAQ:NVDA'),('feed','NASDAQ'),('session','24h'),('resolution','240'),('loading',True),('failed',True),('replay',True),('chart_type',True),('count',3)]:
            with self.subTest(k=k):
                d=fixture();d['context'][k]=v
                with self.assertRaises(MarketDataError):load(d)
    def test_bad_prices_rejected(self):
        for value in [None,True,'100',float('nan'),float('inf'),2**55+1]:
            with self.subTest(value=value):
                d=fixture();d['rows'][0]['value'][1]=value
                with self.assertRaises(MarketDataError):load(d)
    def test_ohlc_and_volume_validity(self):
        for col,v in [(2,1),(3,1000),(5,-1)]:
            d=fixture();d['rows'][0]['value'][col]=v
            with self.assertRaises(MarketDataError):load(d)
    def test_duplicate_reordered_and_foreign_index(self):
        for mode in ('duplicate','reverse','index'):
            d=fixture()
            if mode=='duplicate':d['rows'][1]['value'][0]=d['rows'][0]['value'][0]
            elif mode=='reverse':d['rows'].reverse()
            else:d['rows'][1]['index']=7
            with self.assertRaises(MarketDataError):load(d)
    def test_hash_and_unsupported_interval(self):
        raw=json.dumps(fixture()).encode()
        for h,r in [('0'*64,'1D'),(hashlib.sha256(raw).hexdigest(),'4H')]:
            with self.assertRaises(MarketDataError):load_tradingview_snapshot(raw,expected_sha256=h,expected_resolution=r,source_identifier='test')
    def test_duplicate_json_key(self):
        raw=b'{"schema":1,"schema":2}'
        with self.assertRaises(MarketDataError):load_tradingview_snapshot(raw,expected_sha256=hashlib.sha256(raw).hexdigest(),expected_resolution='1D',source_identifier='test')
    def test_forming_revision_not_silently_applied(self):
        d=fixture();a=load(d);d['revision_observation']={'rows_changed':[{'after':[1788874200,233,234,229,232,200]}]};b=load(d)
        self.assertEqual(a.observations.bars,b.observations.bars);self.assertNotEqual(a.observations.provenance.source_sha256,b.observations.provenance.source_sha256)
    def test_missing_eligibility_remains_unknown(self):
        d=fixture();d['context']['last_bar_close_time']=None;self.assertIsNone(load(d).last_bar_forming)
    def test_future_and_naive_capture_rejected(self):
        for at in ('2026-09-08T14:00:00','2025-09-08T14:00:00Z'):
            d=fixture();d['captured_at_utc']=at
            with self.assertRaises(MarketDataError):load(d)

class TradingViewGuardTests(unittest.TestCase):
    def setUp(self):
        self.client=Mock();self.guard=Mock();self.bridge=TradingViewDigitalBridge(self.client,self.guard)
    def test_bounds_fail_before_chart_access(self):
        for cap in (True,0,20001):
            with self.assertRaises(TradingViewDigitalError):self.bridge.snapshot('1D',max_bars=cap)
        for n in (0,2001,True):
            with self.assertRaises(TradingViewDigitalError):self.bridge.request_history(n)
        self.client.eval.assert_not_called()
    def test_autosave_guard_blocks_extraction(self):
        self.guard.side_effect=TradingViewDigitalError('Autosave on')
        with self.assertRaises(TradingViewDigitalError):self.bridge.snapshot('1D')
        self.client.eval.assert_not_called()
    def test_stale_reconciliation_rejected(self):
        self.client.eval.return_value={'symbol':'BATS:NVDA','resolution':'1W','session':'regular'}
        with self.assertRaises(TradingViewDigitalError):self.bridge.reconcile_times('1D',[1])
    def test_failed_transition_is_not_success(self):
        self.client.eval.return_value={'symbol':'BATS:NVDA','resolution':'1D','session':'24h','loading':False,'failed':False,'count':4}
        with patch('tradingview_digital_tools.time.sleep'):
            with self.assertRaises(TradingViewDigitalError):self.bridge.configure('1D')
    def test_no_sensitive_indicator_input(self):
        import re
        self.assertIsNone(re.match(SAFE_INPUTS,'text'));self.assertIsNone(re.match(SAFE_INPUTS,'token'))
        self.assertIsNotNone(re.match(SAFE_INPUTS,'fast length'))
    def test_no_trading_or_arbitrary_js_tool(self):
        names=[]
        class MCP:
            def tool(self,*,name):
                names.append(name);return lambda fn:fn
        from tradingview_digital_tools import register_digital_tools
        register_digital_tools(MCP(),self.client,self.guard)
        self.assertNotIn('eval',names);self.assertFalse(any('trade' in n or 'order' in n for n in names))

class TradingViewReplayTests(unittest.TestCase):
    def test_display_precision_is_not_rule_tolerance(self):
        from nvda_tradingview_replay import display_matches
        self.assertTrue(display_matches(195.845,'195.85'))
        self.assertFalse(display_matches(195.84,'195.85'))
        self.assertTrue(display_matches(147680809,'147.68\u202fM'))
    def test_all_native_intervals_supported_without_resampling(self):
        from elliott_runtime.market_data.tradingview import INTERVALS
        for res,(label,seconds) in INTERVALS.items():
            d=fixture();d['context']['resolution']=res;raw=json.dumps(d).encode()
            got=load_tradingview_snapshot(raw,expected_sha256=hashlib.sha256(raw).hexdigest(),expected_resolution=res,source_identifier='fixture')
            self.assertEqual(got.observations.timeframe.label,label);self.assertEqual(got.observations.timeframe.resolution_seconds,seconds)
            self.assertFalse(got.observations.provenance.resampled)
    def test_frozen_capture_replays_and_all_samples_reconcile(self):
        from nvda_tradingview_replay import quality
        result=quality()
        self.assertEqual(len(result['datasets']),6)
        self.assertTrue(all(x['input_usable'] for x in result['datasets'].values()))
        self.assertTrue(all(len(x['reconciliation'])>=3 for x in result['datasets'].values()))
    def test_region_extrema_have_no_methodology_authority(self):
        from nvda_tradingview_replay import quality
        result=quality()
        self.assertEqual(len(result['regions']),9)
        self.assertTrue(all(x['methodology_evaluation']=='NOT_EXECUTED_FROM_VISUAL_REGIONS' for x in result['regions']))

if __name__=='__main__':unittest.main()
