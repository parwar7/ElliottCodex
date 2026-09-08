"""Replay adapter for audited, loaded TradingView chart OHLCV snapshots.

No network, chart control, inferred adjustments, resampling or Elliott logic.
Preserves the raw snapshot hash and native bar timestamps. Chart-model access
is version-sensitive; reconciliation is a separate required capture audit.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
import math

from elliott_methodology_kernel.contracts import NormalizedMarketObservations, SymbolIdentity, Timeframe
from elliott_methodology_kernel.contracts import MarketType
from .ingestion import MarketDataError, _normalize

INTERVALS = {'1M': ('1mo',2592000), '1W':('1wk',604800), '1D':('1d',86400),
             '240':('4h',14400), '60':('1h',3600), '15':('15m',900)}

@dataclass(frozen=True, slots=True)
class TradingViewSnapshot:
    observations: NormalizedMarketObservations
    metadata_json: str
    last_bar_forming: bool | None

def _object(pairs):
    result={}
    for k,v in pairs:
        if k in result: raise MarketDataError('Duplicate JSON key')
        result[k]=v
    return result

def load_tradingview_snapshot(raw: bytes, *, expected_sha256: str,
                              expected_resolution: str, source_identifier: str) -> TradingViewSnapshot:
    """Strict native NVDA regular-session replay; partial history is explicit.

    Existing normalizer elapsed-time gaps are NOT exchange-calendar missing-bar
    claims (monthly seconds are nominal). No rows are filled, dropped or revised.
    """
    if type(raw) is not bytes or hashlib.sha256(raw).hexdigest()!=expected_sha256:
        raise MarketDataError('Snapshot hash mismatch')
    if expected_resolution not in INTERVALS or not source_identifier.strip():
        raise MarketDataError('Unsupported interval or missing source identity')
    try:
        data=json.loads(raw, object_pairs_hook=_object, parse_constant=lambda x: (_ for _ in ()).throw(MarketDataError('Nonfinite JSON')))
        c=data['context']; rows=data['rows']
        required={'symbol':'BATS:NVDA','resolution':expected_resolution,'session':'regular',
                  'currency':'USD','loading':False,'failed':False,'replay':False,'chart_type':1}
        if data['schema']!='TRADINGVIEW_LOADED_OHLCV_V1' or data['columns']!=['time','open','high','low','close','volume']:
            raise MarketDataError('Unknown snapshot schema')
        if any(type(c.get(k)) is not type(v) or c[k]!=v for k,v in required.items()):
            raise MarketDataError('Wrong feed/session or stale chart state')
        if c.get('feed')!='Cboe One' or c.get('listing')!='NASDAQ:NVDA' or c.get('exchange_timezone')!='America/New_York':
            raise MarketDataError('Unverified feed/listing/timezone')
        if type(c.get('dividend_adjustment')) is not bool or type(c.get('back_adjustment')) is not bool or 'split_adjustment' not in c:
            raise MarketDataError('Missing adjustment metadata')
        captured=datetime.fromisoformat(data['captured_at_utc'].replace('Z','+00:00'))
        if captured.tzinfo is None: raise MarketDataError('Naive capture timestamp')
        if type(rows) is not list or not 1<=len(rows)<=20000 or type(c['count']) is not int or c['count']!=len(rows):
            raise MarketDataError('Missing rows/count mismatch/cap exceeded')
        records=[]; previous=-1; previous_index=None
        for row in rows:
            values=row['value']; index=row['index']
            if type(values) is not list or len(values)!=6 or type(index) is not int:
                raise MarketDataError('Malformed native row')
            t,*prices,volume=values
            if type(t) is not int or t<=previous or (previous_index is not None and index!=previous_index+1):
                raise MarketDataError('Duplicate/reordered timestamp or discontinuous source index')
            if t>captured.timestamp(): raise MarketDataError('Future bar start')
            for value in prices+[volume]:
                if value is None and value is volume: continue
                if type(value) not in (int,float) or not math.isfinite(value) or (type(value) is int and int(float(value))!=value):
                    raise MarketDataError('Non-numeric/nonfinite/lossy OHLCV')
            if any(p is None for p in prices): raise MarketDataError('Null OHLC')
            records.append(dict(zip(('timestamp','open','high','low','close','volume'),
                [datetime.fromtimestamp(t,timezone.utc).isoformat(),*prices,volume])))
            previous=t; previous_index=index
        tf=Timeframe(*INTERVALS[expected_resolution])
        obs=_normalize(records,raw,'tradingview_loaded_chart',source_identifier,
                       SymbolIdentity('NVDA',MarketType.STOCK,'BATS','BATS:NVDA'),tf)
        # Deterministic factual replay timestamp, not wall clock normalization time.
        obs=replace(obs,provenance=replace(obs.provenance,ingested_at_utc=captured.isoformat()))
        close=c.get('last_bar_close_time')
        forming=None if type(close) not in (int,float) or not math.isfinite(close) else captured.timestamp()<=close
        meta={k:v for k,v in data.items() if k!='rows'}
        meta['normalization']='Native unix seconds to aware UTC ISO; int/float OHLCV to existing float Bar; no row changes'
        meta['gap_semantics']='Elapsed-time intervals only; weekends, holidays, overnight closures and variable months are not distinguished'
        return TradingViewSnapshot(obs,json.dumps(meta,ensure_ascii=False,allow_nan=False),forming)
    except (KeyError,TypeError,ValueError,OverflowError) as exc:
        if isinstance(exc,MarketDataError): raise
        raise MarketDataError('Malformed TradingView snapshot: '+str(exc)) from exc
