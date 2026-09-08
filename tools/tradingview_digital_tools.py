"""Narrow market-data tools over an already-authorized desktop CDP client.

No connection setup, credentials, permission changes, trading, Pine source, or
arbitrary-JavaScript MCP tool. Internal chart APIs are version-sensitive and
must be checked against actual chart/data-window observations per capture.
"""
from __future__ import annotations
import json
import time

RESOLUTIONS = ('1M', '1W', '1D', '240', '60', '15')
SESSIONS = ('regular', 'extended', '24h')
SAFE_INPUTS = r'^(in_[0-9]+|length|col_prev_close|pineId|pineVersion|fast length|slow length|source|signal smoothing|simple ma\(oscillator\)|simple ma\(signal line\))$'
STATE_JS = """(()=>{const c=TradingViewApi.activeChart(),s=c.chartModel().mainSeries(),i=s.symbolInfo();if(!i)throw Error('symbol unresolved');return {symbol:c.symbol(),resolution:String(c.resolution()),listing:i.pro_name,feed:i.exchange,exchange_timezone:i.timezone,currency:i.currency_code,session:s.sessionId(),session_proxy:s.sessionIdProxyProperty().value(),resolved_session:i.session,dividend_adjustment:s.dividendsAdjustmentProperty().value(),back_adjustment:s.properties().childs().backAdjustment.value(),split_adjustment:null,chart_timezone:c.getTimezone(),chart_type:c.chartType(),loading:s.isLoading(),failed:s.isFailed(),replay:s.isInReplay().value(),count:s.bars().size(),end_of_data:s.endOfData(),request_more_available:s.requestMoreDataAvailable(),last_bar_close_time:s.barCloseTime(),viewport:c.getVisibleRange()}})()"""

class TradingViewDigitalError(ValueError): pass

class TradingViewDigitalBridge:
    def __init__(self, client, require_authorized_unsaved):
        self.client=client; self.guard=require_authorized_unsaved
    def state(self):
        return self.client.eval(STATE_JS)
    def configure(self, resolution: str, session: str='regular', symbol: str='BATS:NVDA'):
        if resolution not in RESOLUTIONS or session not in SESSIONS or symbol!='BATS:NVDA':
            raise TradingViewDigitalError('Unsupported exact chart context')
        self.guard()
        self.client.eval('TradingViewApi.activeChart().setSymbol('+json.dumps(symbol)+');undefined')
        self.client.eval('TradingViewApi.activeChart().setResolution('+json.dumps(resolution)+');undefined')
        self.client.eval('TradingViewApi.activeChart().chartModel().mainSeries().properties().childs().sessionId.setValue('+json.dumps(session)+');undefined')
        for _ in range(24):
            time.sleep(.5); s=self.state()
            if s['symbol']==symbol and s['resolution']==resolution and s['session']==session and not s['loading'] and not s['failed'] and s['count']:
                return s
        raise TradingViewDigitalError('Chart transition did not settle in authorized context')
    def request_history(self, count:int):
        if type(count) is not int or not 1<=count<=2000: raise TradingViewDigitalError('History batch outside 1..2000')
        self.guard(); before=self.state()
        if before['loading'] or before['failed']: raise TradingViewDigitalError('Unready chart')
        if before['end_of_data'] or not before['request_more_available']: return {'before':before,'after':before,'requested':False}
        self.client.eval(f'TradingViewApi.activeChart().chartModel().mainSeries().requestMoreData({count});undefined')
        for _ in range(24):
            time.sleep(.5); after=self.state()
            if not after['loading']: break
        keys=('symbol','resolution','session','dividend_adjustment','back_adjustment')
        if after['loading'] or after['failed']:raise TradingViewDigitalError('Historical load did not settle')
        if any(before[k]!=after[k] for k in keys): raise TradingViewDigitalError('Context changed during historical load')
        return {'before':before,'after':after,'requested':True,'batch':count}
    def snapshot(self, resolution:str, session:str='regular', max_bars:int=20000):
        if resolution not in RESOLUTIONS or session not in SESSIONS or type(max_bars) is not int or not 1<=max_bars<=20000:
            raise TradingViewDigitalError('Unsupported snapshot bounds')
        self.guard()
        expr="""(()=>{const state=()=>STATE;const before=state();if(before.symbol!=='BATS:NVDA'||before.resolution!==RES||before.session!==SES||before.loading||before.failed||before.replay||before.chart_type!==1)throw Error('Wrong/stale chart context');const c=TradingViewApi.activeChart(),s=c.chartModel().mainSeries(),b=s.bars();if(b.size()>CAP)throw Error('Snapshot cap exceeded; no truncation');let rows=[];b.each((index,value)=>{if(!Array.isArray(value)||value.length!==6)throw Error('Unexpected OHLCV row layout');for(let j=0;j<6;j++)if(value[j]!==null&&!Number.isFinite(value[j]))throw Error('Nonfinite row');rows.push({index,value:[...value]});});const after=state();for(const k of ['symbol','resolution','session','dividend_adjustment','back_adjustment','count'])if(before[k]!==after[k])throw Error('Chart changed during snapshot');const studies=c.getAllStudies().map(x=>{let a=c.getStudyById(x.id);return {id:x.id,name:x.name,inputs:a.getInputValues().filter(p=>/^(in_[0-9]+|length|col_prev_close|pineId|pineVersion)$/.test(p.id))}});return {schema:'TRADINGVIEW_LOADED_OHLCV_V1',captured_at_utc:new Date().toISOString(),context:before,columns:['time','open','high','low','close','volume'],rows,studies,source_path:'TradingViewApi.activeChart().chartModel().mainSeries().bars().each',history_authority:'LOADED_ACCOUNT_ACCESSIBLE_BARS_ONLY',volume_semantics:'Returned series volume; units not independently verified',forming_bar_authority:'last_bar_close_time metadata; not Elliott completion'}})()"""
        expr=expr.replace('STATE',STATE_JS).replace('RES',json.dumps(resolution)).replace('SES',json.dumps(session)).replace('CAP',str(max_bars))
        return self.client.eval(expr)
    def data_window_samples(self, indices:list[int]):
        if type(indices) is not list or not 1<=len(indices)<=12 or any(type(x) is not int for x in indices):
            raise TradingViewDigitalError('Exact bounded bar indices required')
        self.guard()
        return self.client.eval("(()=>{const s=TradingViewApi.activeChart().chartModel().mainSeries(),b=s.bars();return "+json.dumps(indices)+".map(index=>{if(!b.contains(index))throw Error('Foreign index');return {index,row:b.valueAt(index),items:s.dataWindowValuesProvider().getValues(index).map(x=>({title:x.title,value:x.value,visible:x.visible}))}});})()")

    def reconcile_times(self, resolution:str, timestamps:list[int]):
        if resolution not in RESOLUTIONS or type(timestamps) is not list or not 1<=len(timestamps)<=12 or any(type(t) is not int or t<0 for t in timestamps):
            raise TradingViewDigitalError('Bounded exact timestamps required')
        self.guard()
        state=self.state()
        if state['symbol']!='BATS:NVDA' or state['resolution']!=resolution or state['session']!='regular' or state['loading'] or state['failed'] or state['replay']:
            raise TradingViewDigitalError('Wrong/stale reconciliation context')
        samples=self.client.eval("(()=>{const s=TradingViewApi.activeChart().chartModel().mainSeries(),wanted="+json.dumps(timestamps)+";let found=[];s.bars().each((i,v)=>{if(wanted.includes(v[0]))found.push({index:i,row:[...v],window:s.dataWindowValuesProvider().getValues(i).map(x=>({title:x.title,value:x.value,visible:x.visible}))});});return found})()")
        return {'context':state,'samples':samples,'requested_timestamps':timestamps,'captured_at_unix':time.time()}

    def indicator_snapshot(self):
        self.guard()
        return self.client.eval("""(()=>{const c=TradingViewApi.activeChart(),m=c.chartModel();const context=STATE;if(context.symbol!=='BATS:NVDA'||context.session!=='regular'||context.loading||context.failed||context.replay||context.count>20000)throw Error('Unready indicator context');return {context,captured_at_utc:new Date().toISOString(),studies:c.getAllStudies().filter(x=>['Volume','Relative Strength Index','MACD'].includes(x.name)).map(a=>{const api=c.getStudyById(a.id),s=m.dataSourceForId(a.id),meta=s.metaInfo();if(s.data().size()>20000)throw Error('Indicator cap');let rows=[];s.data().each((i,v)=>{rows.push({index:i,value:[...v]});});return {id:a.id,name:a.name,inputs:api.getInputValues().filter(x=>/SAFE/.test(x.id)),input_names:api.getInputsInfo().filter(x=>/SAFE/.test(x.id)).map(x=>({id:x.id,name:x.name,type:x.type})),plots:meta.plots,styles:meta.styles,rows,window:s.dataWindowValuesProvider?s.dataWindowValuesProvider().getValues(s.data().lastIndex()):s.valuesProvider().getValues(s.data().lastIndex())}})}})()""".replace('STATE',STATE_JS).replace('SAFE',SAFE_INPUTS))

    def add_macd(self):
        self.guard()
        return self.client.eval("""(async()=>{const c=TradingViewApi.activeChart();if(c.getAllStudies().some(s=>s.name==='MACD'))return {already_present:true};try{return {id:await c.createStudy('MACD',false,false)}}catch(e){return {blocked:String(e)}}})()""",await_promise=True)

    def show_sample(self, timestamp:int, resolution:str):
        if type(timestamp) is not int or resolution not in RESOLUTIONS: raise TradingViewDigitalError('Bad sample scope')
        self.guard(); state=self.state()
        if state['symbol']!='BATS:NVDA' or state['resolution']!=resolution or state['session']!='regular':raise TradingViewDigitalError('Wrong sample chart')
        # Ordinary chart navigation over 41 neighboring loaded bars; no new endpoint authority.
        return self.client.eval("""(()=>{const c=TradingViewApi.activeChart(),m=c.chartModel(),b=m.mainSeries().bars();let found=null;b.each((i,v)=>{if(v[0]===STAMP)found=i});if(found===null)throw Error('Sample not loaded');const lo=b.valueAt(Math.max(b.firstIndex(),found-20))[0],hi=b.valueAt(Math.min(b.lastIndex(),found+20))[0];m.gotoTimeRange(lo*1000,hi*1000);return {sample_index:found,timestamp:STAMP,requested_from:lo,requested_to:hi,crosshair_api:typeof c.setCrossHairPosition}})()""".replace('STAMP',str(timestamp)))

def register_digital_tools(mcp, client, guard):
    bridge=TradingViewDigitalBridge(client,guard)
    mcp.tool(name='tv_digital_state')(bridge.state)
    mcp.tool(name='tv_digital_configure')(bridge.configure)
    mcp.tool(name='tv_digital_request_history')(bridge.request_history)
    mcp.tool(name='tv_digital_snapshot')(bridge.snapshot)
    mcp.tool(name='tv_digital_data_window_samples')(bridge.data_window_samples)
    mcp.tool(name='tv_digital_reconcile_times')(bridge.reconcile_times)
    mcp.tool(name='tv_digital_indicator_snapshot')(bridge.indicator_snapshot)
    mcp.tool(name='tv_digital_add_macd')(bridge.add_macd)
    mcp.tool(name='tv_digital_show_sample')(bridge.show_sample)
    return bridge
