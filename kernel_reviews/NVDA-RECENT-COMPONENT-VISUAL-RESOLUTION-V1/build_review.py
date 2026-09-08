"""Deterministic report serialization/callouts, adapted from the approved pack.
No market retrieval, wave discovery, evaluator imports, or authority issuance.
Analyst-authored regions below are not executable price operands.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PACK = Path(__file__).resolve().parent
PRIOR = PACK.parent / 'NVDA-SOURCE-LOCKED-VISUAL-HIERARCHY-ANALYSIS-V1'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name, obj):
    (PACK/name).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')

def build():
    old=read(PRIOR/'hierarchy.json')
    refs=read(PRIOR/'source_references.json')
    refs['review_scope']='Reconsulted relevant protected Volumes 1, 8, 10 passages and book pages 31-33; no exhaustive new corpus research.'
    refs['references']['S8']['locator']='Sections 2, 5-8 and 10; parent-child order, unresolved internals, completion changes degree'
    refs['references']['S6']['locator']='PDF/printed pages 32-33, Extension; Figures 1-5 and 1-8 visually inspected'
    refs['source_authority_note']='Local L1/L2 choices are analyst hypotheses. S3/S6 are possibility/guideline support, not confirmation. S7 project conventions remain separate from source rule. No trading practices applied.'
    save('source_references.json',refs)
    # Dates/prices are readable regions, not exact selected turning bars.
    raw=[
      ('origin',1,'April 2025 low region','~86-90','summer_2025'),
      ('may25',2,'mid-May 2025 high region','~135-137','summer_2025'),
      ('may25low',3,'late-May 2025 pullback region','~129-132','summer_2025'),
      ('aug25',4,'late July-August 2025 high plateau','~182-184','summer_2025'),
      ('sep25',5,'early September 2025 low region','~165-169','summer_2025'),
      ('oct25',6,'late October-early November 2025 high cluster','~210-212','advance_2026'),
      ('mar26',7,'late March 2026 low region','~164-168','advance_2026'),
      ('may26',8,'mid-May 2026 Daily peak region','~236-237','advance_2026'),
      ('jul26',9,'late July 2026 Daily low region','~189-194','overview'),
      ('last',10,'2026-09-04 rightmost Daily bar','C 230.36 displayed','last_bar_reading')]
    e={k:{'order':o,'date_region':d,'price_description_USD':p,'image':'originals/'+im+'.png',
       'precision':'APPROXIMATE_VISUAL_REGION','timeframe':'1D',
       'orthodox_endpoint_authority':False,'executable_operand_authority':False} for k,o,d,p,im in raw}
    e['context_2022']={**old['endpoints']['e22'],'order':0,'price_description_USD':old['endpoints']['e22']['price_display_or_estimate_USD'],
       'image':'../'+PRIOR.name+'/originals/recent_daily.png','timeframe':'1D','inherited_context_only':True}
    e['last'].update(precision='EXACT_DISPLAYED_BAR_DATE_AND_OHLC_NOT_EXPORTED_OPERAND',
       displayed_date='Fri 04 Sep 26',displayed_OHLC={'O':'231.09','H':'234.76','L':'229.63','C':'230.36'},
       exact_intraday_timestamp=None,bar_developing='Not independently verified; historical displayed bar, no completion certificate',
       crosshair_price_not_used='230.43 is pointer-axis level, NOT the bar close')
    nodes=[]; mappings=[]
    def n(lineage,suffix,parent,role,a,b,note,open_=False,prior=None):
        nodes.append({'node_id':lineage+suffix,'lineage':lineage,'local_interpretation':lineage[-2:],
          'parent_id':lineage+parent if parent is not None else None,'proposed_role':role,
          'start_evidence':a,'end_evidence':b,'timeframe':'1D; 4H context only where cited',
          'end_kind':'OPEN_OBSERVATION_BOUNDARY_NOT_WAVE_END' if open_ else 'PROPOSED_REGION_NOT_CERTIFIED_END',
          'prior_node_ref':prior,'note':note,'source_refs':['S2','S3','S5','S6','S8','S9'],
          'engine_evaluated':False,'validity_authority':False,'degree':'UNESTABLISHED'})
    for s,parent in [('A','A.5'),('B','B.3.3.3')]:
        for local in ('L1','L2'):
            lin=s+'.'+local
            n(lin,'',None,'Prior open ancestor: context only','context_2022','last',
              'Minimal snapshot continuation of prior ancestor; older children not reanalyzed or copied.',True,parent)
            nodes[-1]['external_parent_ref']='prior:'+next(x['parent_id'] for x in old['nodes'] if x['node_id']==parent)
            nodes[-1]['retained_prior_children_refs']=[parent+'.1',parent+'.2']
            mappings.append({'lineage':lin,'prior_ancestor':parent,'prior_open_component':parent+'.3',
              'new_component':lin+'.advance','policy':'EXPLICIT_ALTERNATIVE_CLOSURE' if local=='L1' else 'COMPATIBLE_OPEN_CONTINUATION',
              'subsequent_component':lin+'.correction' if local=='L1' else None,
              'historical_ancestry_reopened':False,'prior_snapshot':'2026-09-07','new_daily_boundary':'2026-09-04 bar inspected 2026-09-08'})
            if local=='L1':
                n(lin,'.advance','','3? proposed ended at May region','origin','may26',
                  'Conditional closure of former open component; not evidence of completed impulse.',prior=parent+'.3')
                for i,(a,b) in enumerate(zip(['origin','may25','may25low','oct25','mar26'],['may25','may25low','oct25','mar26','may26']),1):
                    n(lin,'.advance.'+str(i),'.advance',str(i)+'? hypothesis slot',a,b,
                      'Broad daily leg; complete lower family unresolved. Long third includes summer plateau and September pullback.')
                n(lin,'.correction','','4? unresolved subsequent correction','may26','last',
                  'Sibling of closed advance, NOT inside it. No ABC/Flat/Triangle or completion assigned.',True)
                n(lin,'.correction.decline','.correction','Unclassified observed decline','may26','jul26',
                  '4H shows interrupted decline, late-June/early-July lows, July bounce, late-July low; no universal three/five inferred.')
                n(lin,'.correction.rebound','.correction','Unclassified rebound; conditional latest container','jul26','last',
                  'If correction remains open, July-to-latest rebound belongs here. An already-ended correction is not disproved.',True)
            else:
                n(lin,'.advance','','3? remains open','origin','last',
                  'Preserve prior open relationship, add local nested alternative without claiming extension proof.',True,parent+'.3')
                n(lin,'.advance.1','.advance','1?','origin','oct25','Possible first; summer subdivisions below remain provisional.')
                n(lin,'.advance.2','.advance','2? unclassified correction','oct25','mar26','Prolonged retreat/range, not forced ABC.')
                n(lin,'.advance.3','.advance','3? open','mar26','last','Possible renewed actionary component.',True)
                for i,(a,b) in enumerate(zip(['origin','may25','may25low','aug25','sep25'],['may25','may25low','aug25','sep25','oct25']),1):
                    n(lin,'.advance.1.'+str(i),'.advance.1',str(i)+'? hypothesis slot',a,b,'Summer Daily region inspected; five slots are not a family certificate.')
                for i,a,b in [(1,'mar26','may26'),(2,'may26','jul26'),(3,'jul26','last')]:
                    n(lin,'.advance.3.'+str(i),'.advance.3',str(i)+'?'+(' open' if i==3 else ''),a,b,
                      'Nested local hypothesis; 4H context does not supply same-session exact endpoints.',i==3)
    hierarchy={'schema':'VISUAL_REVIEW_ONLY_NOT_ANALYSIS_OUTPUT_SCHEMA','rank':None,'endpoints':e,'nodes':nodes,'mappings':mappings,
      'interpretations':['L1','L2'],'duplicate_policy':'Separate A/B contextual instances retained; not independent confirmations.',
      'current_position':{'engine_status':'CURRENT_WAVE_POSITION_UNRESOLVED','new_engine_call':False,
        'L1':'Conditional rebound inside subsequent unresolved correction, A.L1.correction.rebound or B.L1.correction.rebound.',
        'L2':'Conditional nested third from late July, A.L2.advance.3.3 or B.L2.advance.3.3.',
        'latest_4H':'Live pre-market extension of observation only; exact 4H bar timestamp UNKNOWN; no wave binding.'}}
    hierarchy['context_observations']={
      'c4_jul':{'date_region':'late July 2026 low region','price_description_USD':'~190-192','precision':'APPROXIMATE_VISUAL_REGION'},
      'c4_aug_high':{'date_region':'mid-August 2026 rebound high region','price_description_USD':'~227-228','precision':'APPROXIMATE_VISUAL_REGION'},
      'c4_aug_low':{'date_region':'late August 2026 retreat region before Aug27 rise','price_description_USD':'~207-211; other extended-session wick lower, not substituted','precision':'APPROXIMATE_VISUAL_REGION'},
      'c4_live':{'date_region':'latest visible 4H bar; exact start timestamp UNKNOWN','price_description_USD':'232.51 displayed at capture 2026-09-08T13:14:14Z','precision':'EXACT_DISPLAYED_VALUE_NOT_EXPORTED_OPERAND'}}
    for item in hierarchy['context_observations'].values():
        item.update(image='originals/rebound_4h.png',timeframe='240',session='24H',role_endpoint_authority=False)
    save('hierarchy.json',hierarchy)
    table=['# Node / parent / endpoint ledger','',
      'All roles provisional; regions approximate except explicitly displayed last-bar values. A/B rows are alternative context, not confirmations.','',
      '| Node | Parent | Proposed role | Start evidence | End evidence |','|---|---|---|---|---|']
    for row in nodes: table.append('| '+' | '.join(str(row[k] or row.get('external_parent_ref')) for k in ['node_id','parent_id','proposed_role','start_evidence','end_evidence'])+' |')
    table+=['','## Evidence regions','','| Evidence | Date | USD / precision | Source |','|---|---|---|---|']
    for k,v in e.items(): table.append(f"| {k} | {v['date_region']} | {v['price_description_USD']} / {v['precision']} | {v['image']} |")
    table+=['','## 4H context only - not substituted Daily endpoints','','| Evidence | Date | USD / precision | Source |','|---|---|---|---|']
    for k,v in hierarchy['context_observations'].items(): table.append(f"| {k} | {v['date_region']} | {v['price_description_USD']} / {v['precision']} | {v['image']} |")
    (PACK/'node_table.md').write_text('\n'.join(table)+'\n',encoding='utf-8',newline='\n')
    captures={}
    for path in sorted((PACK/'originals').glob('*.json')):
        r=read(path); assert sha(path.with_suffix('.png'))==r['sha256']
        r['image']='originals/'+path.stem+'.png'; r['receipt']='originals/'+path.name
        r['viewport_utc']={k:datetime.fromtimestamp(v,timezone.utc).isoformat() for k,v in r['metadata']['chart']['range'].items()}
        r['range_authority']='Chart viewport, NOT proof of every underlying bar or wave; future blank space may occur.'
        r['inspected']=True; captures[path.stem]=r
    save('capture_provenance.json',{'actual_feed':'BATS:NVDA / Cboe One','listing_identifier_only':'NASDAQ:NVDA','Yahoo_used':False,
      'snapshot_kind':'Seven separately timed captures 2026-09-08; no atomic market snapshot asserted','images':captures,
      'settings':{'scale':'USD logarithmic; auto scale active','dividend_adjustment':'off (pressed=false)',
       'split_adjustment':'UNKNOWN','timezone':'Etc/UTC','Daily_session_configuration':'UNKNOWN; separate Pre quote visible',
       'four_hour_session':'24H visibly selected; may contain extended-session extremes absent in Daily',
       'visible_indicators':'Volume 20 with line; no volume interpretation. RSI listed by API but not visibly inspected or used.',
       'OHLCV_export':'NOT_VERIFIED','autosave':'OFF, checked before each capture'},
      'last_daily_bar':e['last'],
      'current_readings':{'overview_pre_quote':'232.28 at 13:07:30Z','rebound_4H_label':'232.51 at 13:14:14Z',
        'rebound_4H_countdown':'02:45:49, developing bar; exact bar-start timestamp UNKNOWN',
        'last_bar_reading_pre_quote':'232.72 at 13:15:30Z','not_comparable_atomic_operands':True},
      'failed_reading':'latest_daily crosshair showed Sep9 in EMPTY future space, not last-bar date. Last_bar_reading corrects it with Sep4 crosshair on actual bar.',
      'coverage':{'overview':1,'targeted':6,'targeted_limit':6,'missing_intraday_history':'Not encountered in displayed May-Sep windows; exact bar inventory not exported',
        'uninspected':['pre-May2026 intraday internals','below 4H internals','same-session extreme reconciliation','exact historic turning-bar OHLC'],
        'stop_reason':'Question-specific windows inspected and six-target capture budget reached; classification/completion remains unresolved.'}})
    views=[]
    def mark(node,evidence,xy,offset,label): return dict(node=node,evidence=evidence,xy=xy,offset=offset,label=label)
    for local in ('L1','L2'):
        # One local interpretation per image, instantiated separately for A and B in the ledger.
        marks=[mark('advance','origin',[112,927],[35,-85],'April 2025 origin REGION?')]
        if local=='L1':
            marks += [mark('advance.'+str(i),ev,xy,off,lab) for i,ev,xy,off,lab in [
              (1,'may25',[249,583],[-110,-90],'1? mid-May 2025'),(2,'may25low',[274,615],[45,25],'2? late May'),
              (3,'oct25',[810,247],[-115,-100],'3? Oct/Nov 2025'),(4,'mar26',[1314,428],[-190,45],'4? late March'),
              (5,'may26',[1472,164],[-175,-65],'5? May 2026 END?')]]
            marks += [mark('correction.rebound','last',[1853,181],[-340,105],'Subsequent correction? OPEN')]
            title='L1 | April advance may end in May; subsequent correction stays unresolved'
        else:
            marks += [mark('advance.1','oct25',[810,247],[-140,-95],'1? Oct/Nov 2025'),
              mark('advance.2','mar26',[1314,428],[-230,45],'2? late March'),
              mark('advance.3.1','may26',[1472,164],[-185,-65],'3.1? May region'),
              mark('advance.3.2','jul26',[1723,326],[-225,65],'3.2? late July'),
              mark('advance.3.3','last',[1853,181],[-300,100],'3.3? OPEN, not confirmed')]
            title='L2 | April advance remains open; nested March / July components?'
        views.append(dict(name=local+'_daily',local=local,source_image='originals/overview.png',title=title,marks=marks,
          footer='A and B mappings are separate ledger instances. A question mark marks every proposed role; no historical ancestry is rewritten.'))
        role='correction.rebound' if local=='L1' else 'advance.3.3'
        # 4H callouts are contextual observations, NOT replacements for Daily role endpoints.
        cm=[mark(role,'jul26',[811,895],[-265,-75],'Late-July REGION: 4H context'),
          mark(role,None,[1275,266],[-230,-80],'Mid-August rebound high'),
          mark(role,None,[1465,584],[-230,65],'Late-August retreat'),
          mark(role,None,[1818,200],[-345,-65],'232.51 displayed; bar developing')]
        for m,key in zip(cm,('c4_jul','c4_aug_high','c4_aug_low','c4_live')):
            m['context_only']=True; m['context_evidence']=key
        views.append(dict(name=local+'_rebound',local=local,source_image='originals/rebound_4h.png',
          title=local+(' | Rebound inside unresolved subsequent correction?' if local=='L1' else ' | Rebound inside proposed nested third?'),marks=cm,
          footer='4H is visibly 24H session. These contextual regions do not supply exact Daily endpoints or prove a corrective / motive family.'))
    for v in views:
        v['coordinate_basis']=[2048,1112]; v['output']='annotated/'+v['name']+'.png'
        for m in v['marks']:
            m['node_instances']=[s+'.'+v['local']+'.'+m['node'] for s in ('A','B')]
    save('annotations.json',views); render(views)

def render(views):
    (PACK/'annotated').mkdir(exist_ok=True)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',27)
    titlefont=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',33)
    small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',25)
    for v in views:
        src=Image.open(PACK/v['source_image']).convert('RGB'); w,h=src.size; top=108
        canvas=Image.new('RGB',(w,h+228),'#101c2b'); canvas.paste(src,(0,top)); d=ImageDraw.Draw(canvas)
        color='#155e8b' if v['local']=='L1' else '#70419a'
        d.text((30,15),v['title'],font=titlefont,fill='white')
        d.text((30,61),'BATS:NVDA / Cboe One | USD LOG | Captured 2026-09-08 | PROVISIONAL VISUAL INTERPRETATION ONLY',font=small,fill='#c9d8e7')
        for m in v['marks']:
            x,y=m['xy']; dx,dy=m['offset']; px,py=round(x*w/2048),round(y*h/1112)+top
            bx,by=round((x+dx)*w/2048),round((y+dy)*h/1112)+top
            bw=d.textbbox((0,0),m['label'],font=font)[2]+22; bh=40
            bx=max(8,min(w-bw-8,bx)); by=max(top+4,min(h+top-bh-4,by))
            d.line((px,py,bx+bw//2,by+bh//2),fill=color,width=3)
            d.ellipse((px-8,py-8,px+8,py+8),outline=color,width=3)
            d.rounded_rectangle((bx,by,bx+bw,by+bh),radius=6,fill='white',outline=color,width=3)
            d.text((bx+11,by+4),m['label'],font=font,fill=color)
        d.text((30,h+top+14),v['footer'],font=small,fill='white')
        d.text((30,h+top+59),'No synthetic price lines, exact pixel-derived operands, established degrees, ranking, forecast, or wave certification.',font=small,fill='#c9d8e7')
        canvas.save(PACK/v['output'])

if __name__=='__main__': build()
