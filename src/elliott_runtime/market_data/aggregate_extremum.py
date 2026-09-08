"""Exact observed aggregate extremum occurrences, without Elliott endpoint authority.

Calendar buckets/session envelopes establish membership only. No exchange
holiday calendar, early-close guarantee, completion or exhaustive coverage.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from zoneinfo import ZoneInfo
import hashlib
import json

from .tradingview import TradingViewSnapshot, INTERVALS
from elliott_runtime.analysis.normal_impulse_partial_evaluation import (
    NormalImpulsePartialEvaluationResult, validate_normal_impulse_partial_evaluation_result,
)


def digest(value):return hashlib.sha256(repr(value).encode('utf-8')).hexdigest()


def observation_identities(snapshot):
    """Pin nested immutable record identities as well as represented content."""
    o=snapshot.observations
    return (snapshot,o,o.symbol,o.timeframe,o.provenance,o.provenance.source_resolution,
            o.provenance.parent_source_hashes,o.quality,o.quality.duplicate_timestamps_utc,
            o.quality.missing_intervals,o.bars)+o.quality.missing_intervals+o.bars+tuple(b.provenance for b in o.bars)


def metadata(snapshot):
    if type(snapshot) is not TradingViewSnapshot:raise ValueError('Exact TradingView snapshot required')
    value=json.loads(snapshot.metadata_json)
    expected=INTERVALS.get(value['context']['resolution'])
    actual=snapshot.observations.timeframe
    if expected!=(actual.label,actual.resolution_seconds):raise ValueError('Metadata/observation resolution mismatch')
    return value


def interval(snapshot, bar):
    """Supported civil/session envelope. Never add nominal monthly seconds."""
    meta=metadata(snapshot);c=meta['context']
    if not any(b is bar for b in snapshot.observations.bars):raise ValueError('Foreign aggregate bar')
    required={'exchange_timezone':'America/New_York','session':'regular','resolved_session':'0930-1600'}
    if any(c.get(k)!=v for k,v in required.items()):return None
    tz=ZoneInfo(c['exchange_timezone']);local=bar.timestamp_utc.astimezone(tz)
    if local.hour!=9 or local.minute!=30:return None
    if c['resolution']=='1M':
        # Native 1M label identifies a civil month, not its exact first trade.
        if local.day>7:return None
        start=datetime(local.year,local.month,1,tzinfo=tz)
        end=datetime(local.year+int(local.month==12),1 if local.month==12 else local.month+1,1,tzinfo=tz)
        basis='NATIVE_CALENDAR_MONTH_ENVELOPE_NOT_TRADING_CALENDAR'
    elif c['resolution']=='1D':
        start=local.replace(second=0,microsecond=0)
        end=local.replace(hour=16,minute=0,second=0,microsecond=0)
        basis='DECLARED_REGULAR_SESSION_ENVELOPE_EARLY_CLOSE_UNVERIFIED'
    else:return None
    return (start.astimezone(timezone.utc),end.astimezone(timezone.utc),basis)


def occurrence_envelope(snapshot,bar):
    c=metadata(snapshot)['context'];tz=ZoneInfo(c['exchange_timezone'])
    local=bar.timestamp_utc.astimezone(tz)
    if c['resolution']=='1D':return interval(snapshot,bar)
    minutes={'240':240,'60':60,'15':15}.get(c['resolution'])
    if minutes is None or not (9*60+30<=local.hour*60+local.minute<16*60):return None
    end=min(local+timedelta(minutes=minutes),local.replace(hour=16,minute=0,second=0,microsecond=0))
    return (bar.timestamp_utc,end.astimezone(timezone.utc),'NATIVE_INTRADAY_SESSION_ENVELOPE_EARLY_CLOSE_UNVERIFIED')


@dataclass(frozen=True,slots=True,eq=False)
class ExtremumOccurrenceEvidence:
    aggregate: TradingViewSnapshot
    aggregate_bar: object
    price_field: str
    finer: TradingViewSnapshot
    interval_evidence: tuple | None
    examined: tuple
    matches: tuple
    status: str
    limitations: tuple
    parent_result: NormalImpulsePartialEvaluationResult | None = None
    role_index: int | None = None
    edge: str | None = None
    _identities: tuple=field(init=False,repr=False)
    _digest: str=field(init=False,repr=False)

    def _current(self):
        original=(self.aggregate,self.aggregate_bar,self.finer,self.aggregate.observations,
                  self.aggregate.observations.bars,self.finer.observations,self.finer.observations.bars,
                  self.examined,self.matches,self.interval_evidence,self.limitations,self.parent_result)
        original+=observation_identities(self.aggregate)+observation_identities(self.finer)
        if self.parent_result is not None:
            validate_normal_impulse_partial_evaluation_result(self.parent_result)
            h=self.parent_result.evaluations[0].hypothesis
            if type(self.role_index) is not int or self.role_index not in range(5) or self.edge not in ('start','end'):
                raise ValueError('Invalid exact parent role')
            role=h.role_bindings[self.role_index];endpoint=getattr(role,self.edge+'_boundary')
            if h.generated_candidate.source_observations is not self.aggregate.observations:
                raise ValueError('Foreign aggregate parent snapshot')
            if endpoint.timestamp_utc!=self.aggregate_bar.timestamp_utc or endpoint.observed_price!=getattr(self.aggregate_bar,self.price_field):
                raise ValueError('Parent endpoint not this aggregate observation')
            # Exact original bar field and pivot membership remain checked by parent validator.
            if endpoint.pivot_kind.value.lower()!=self.price_field:raise ValueError('Wrong endpoint price basis')
            original+=(h,role,h.five_slot_view,h.five_slot_view.binding,h.five_slot_view.binding.parent_subject,
                       h.five_slot_view.binding.ordered_children,role.child_subject,endpoint)
        elif self.role_index is not None or self.edge is not None:raise ValueError('Missing parent')
        return original

    def __post_init__(self):
        if type(self) is not ExtremumOccurrenceEvidence:raise ValueError('Exact occurrence evidence required')
        current=self._current();content=digest((self.aggregate,self.aggregate_bar,self.price_field,self.finer,
            self.interval_evidence,self.examined,self.matches,self.status,self.limitations,self.role_index,self.edge))
        if hasattr(self,'_identities'):
            if len(current)!=len(self._identities) or any(a is not b for a,b in zip(current,self._identities)) or content!=self._digest:
                raise ValueError('Occurrence evidence mutated; issuance cannot refresh')
        else:
            object.__setattr__(self,'_identities',current);object.__setattr__(self,'_digest',content)
        values=_derive(self.aggregate,self.aggregate_bar,self.price_field,self.finer)
        if self.interval_evidence!=values[0] or self.status!=values[3] or self.limitations!=values[4]:raise ValueError('Derived evidence differs')
        for actual,expected in ((self.examined,values[1]),(self.matches,values[2])):
            if type(actual) is not tuple or len(actual)!=len(expected) or any(a is not b for a,b in zip(actual,expected)):
                raise ValueError('Foreign/reordered occurrence evidence')

    def validated(self):self.__post_init__();return self
    def __reduce_ex__(self,protocol):raise TypeError('Serialized evidence cannot restore exact live ancestry')


def _derive(aggregate,bar,price_field,finer):
    if price_field not in ('high','low'):raise ValueError('High/high or low/low only')
    a=metadata(aggregate);f=metadata(finer)
    if aggregate.observations.timeframe.resolution_seconds<=finer.observations.timeframe.resolution_seconds:
        raise ValueError('Explicit finer resolution required; seconds compare resolution only, never membership')
    keys=('symbol','listing','feed','currency','session','resolved_session','exchange_timezone','dividend_adjustment','back_adjustment','split_adjustment')
    if aggregate.observations.symbol!=finer.observations.symbol or any(k not in a['context'] or k not in f['context'] or type(a['context'][k]) is not type(f['context'][k]) or a['context'][k]!=f['context'][k] for k in keys):
        return (interval(aggregate,bar),(),(),'INCOMPATIBLE_METADATA',('NO_PRICE_COMPARISON_PERFORMED',))
    bounds=interval(aggregate,bar)
    if bounds is None:return (None,(),(),'INTERVAL_UNAVAILABLE',('UNSUPPORTED_CALENDAR_SESSION_BASIS',))
    rows=tuple(b for b in finer.observations.bars if bounds[0]<=b.timestamp_utc<bounds[1])
    # Membership requires the finer bar envelope not to cross the aggregate envelope.
    eligible=tuple(b for b in rows if occurrence_envelope(finer,b) is not None and occurrence_envelope(finer,b)[1]<=bounds[1])
    limits=['COMPLETE_TRADING_COVERAGE_UNVERIFIED','EARLY_CLOSE_AND_HOLIDAY_CALENDAR_UNAVAILABLE','OCCURRENCE_IS_BAR_INTERVAL_NOT_INSTANT','NO_ORTHODOX_ENDPOINT_AUTHORITY']
    if a['context']['split_adjustment'] is None:limits.append('SPLIT_ADJUSTMENT_SEMANTICS_UNKNOWN')
    if a['captured_at_utc']!=f['captured_at_utc']:limits.append('NON_SYNCHRONOUS_CAPTURES')
    if len(eligible)!=len(rows):limits.append('FINER_BAR_INTERVAL_UNSUPPORTED_OR_CROSSING')
    if not rows:limits.append('NO_FINER_OBSERVATIONS_IN_ENVELOPE')
    # Calendar envelopes intentionally include closures; these are source extent flags, not counts of missing trades.
    if finer.observations.bars[0].timestamp_utc>bounds[0]:limits.append('FINER_HISTORY_START_INSIDE_OR_AFTER_ENVELOPE')
    if finer.observations.bars[-1].timestamp_utc<bounds[1]:limits.append('FINER_HISTORY_END_BEFORE_ENVELOPE_END')
    if aggregate.last_bar_forming is None:limits.append('AGGREGATE_FORMING_STATE_UNAVAILABLE')
    if bar is aggregate.observations.bars[-1] and aggregate.last_bar_forming:limits.append('AGGREGATE_BAR_FORMING')
    if any(b is finer.observations.bars[-1] for b in eligible) and finer.last_bar_forming is not False:limits.append('FINER_BAR_FORMING_OR_UNKNOWN')
    if a.get('revision_observation',{}).get('rows_changed') or f.get('revision_observation',{}).get('rows_changed'):
        limits.append('SNAPSHOT_REVISION_METADATA_PRESENT_NOT_APPLIED')
    matches=tuple(b for b in eligible if Fraction(getattr(b,price_field))==Fraction(getattr(bar,price_field)))
    state='MULTIPLE_OBSERVED_MATCHES' if len(matches)>1 else 'UNIQUE_OBSERVED_MATCH' if matches else 'NO_OBSERVED_MATCH_IN_AVAILABLE_ROWS'
    if not rows:state='NO_FINER_COVERAGE'
    return bounds,eligible,matches,state,tuple(limits)


def find_extremum_occurrences(aggregate,bar,price_field,finer,*,parent_result=None,role_index=None,edge=None,cache=None):
    if cache is not None and type(cache) is not dict:raise ValueError('Explicit local cache required')
    key=(id(aggregate),id(bar),price_field,id(finer),id(parent_result),role_index,edge)
    if cache is not None and key in cache:
        evidence=cache[key]
        if type(evidence) is not ExtremumOccurrenceEvidence or evidence.aggregate is not aggregate or evidence.aggregate_bar is not bar or evidence.finer is not finer or evidence.parent_result is not parent_result or (evidence.price_field,evidence.role_index,evidence.edge)!=(price_field,role_index,edge):
            raise ValueError('Foreign cached evidence')
        return evidence.validated()
    values=_derive(aggregate,bar,price_field,finer)
    evidence=ExtremumOccurrenceEvidence(aggregate,bar,price_field,finer,*values,parent_result,role_index,edge)
    if cache is not None:cache[key]=evidence
    return evidence
