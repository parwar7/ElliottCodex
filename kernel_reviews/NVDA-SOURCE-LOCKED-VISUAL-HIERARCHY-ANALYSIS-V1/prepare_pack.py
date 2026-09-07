"""Render reviewed, manually authored visual hypotheses; never run Elliott logic.

All market pixels are original MCP captures. Coordinates locate approximate
turning REGIONS, not numerical operands. Outputs stay in this review directory.
"""
import base64
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PACK = Path(__file__).resolve().parent
ROOT = PACK.parents[1]
CAP = ROOT / 'artifacts/tradingview_nvda_capture_20260907'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name, value):
    (PACK/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')

def prepare():
    manifest = json.loads((CAP/'nvda_chart_pack_manifest.json').read_text(encoding='utf-8-sig'))
    assert digest(CAP/'nvda_chart_pack_manifest.json') == '689473b59f03446d15c0bbf901facae3710cee5ceed0d36e0f450fc4e690d9dd'
    provenance = {'actual_feed':'BATS:NVDA / Cboe One', 'listing_only':'NASDAQ:NVDA',
      'capture_date_utc':'2026-09-07', 'Yahoo_operands_used':False,
      'settings':manifest['settings_common_to_all_delivered_images'], 'images':{}}
    for name, item in zip(('monthly','weekly','daily'), manifest['images']):
        src=CAP/item['image']; assert digest(src)==item['sha256']
        target=PACK/'originals'/f'{name}.png'
        if target.exists(): assert digest(target)==item['sha256']
        else: target.write_bytes(src.read_bytes())
        provenance['images'][name]={**item, 'original_local_artifact':item['image'], 'image':f'originals/{name}.png',
          'original_local_metadata':item['metadata'],'metadata':f'originals/{name}.json',
          'metadata_sha256':digest(CAP/item['metadata'])}
        (PACK/f'originals/{name}.json').write_bytes((CAP/item['metadata']).read_bytes())
    for name in ('early_weekly','middle_weekly','recent_daily','latest_daily'):
        item=json.loads((PACK/'originals'/f'{name}.json').read_text())
        assert digest(PACK/'originals'/f'{name}.png')==item['sha256']
        provenance['images'][name]={**item,'image':f'originals/{name}.png',
          'date_precision':'viewport dates exact from chart API; turning-region dates approximate',
          'inspected':True}
    provenance['latest_observation']={'displayed_price':'230.36','price_precision':'exact displayed label, not exported operand',
      'bar_date':'early September 2026; exact daily bar timestamp NOT independently established',
      'capture_time_is_not_bar_time':True,'monthly_developing':True,
      'monthly_developing_evidence':'original monthly last-price label: 23d 6h',
      'bound_developing_wave_component':False,'current_price_claim':False}
    save('capture_provenance.json',provenance)

    # Stable local evidence keys. These are NOT protected principle or engine IDs.
    refs={
      'S1':{'path':'volume_01/Volume_01.srt','locator':'00:29:45.679–00:31:41.909',
        'class':'SOURCE_RULE','meaning':'Impulse rule discussion, including wave 2 origin and wave 3 comparison. P006 interpretation remains frozen.'},
      'S2':{'path':'volume_08/volume_08.srt','locator':'00:04:47.070–00:06:37.050',
        'class':'SOURCE_GUIDELINE','meaning':'Begin with larger picture and inspect simultaneous nested structures; no timeframe-degree identity.'},
      'S3':{'path':'volume_08/volume_08.srt','locator':'00:08:10.130–00:09:23.600',
        'class':'SOURCE_GUIDELINE','meaning':'Nested first/second structures and extending third; possibility, not proof of the NVDA interpretation.'},
      'S4':{'path':'volume_10/volume_10.txt','locator':'00:02:18.480–00:03:35.760',
        'class':'SOURCE_OBSERVATION','meaning':'Aggregated bars can conceal lower-resolution structures; no invented subdivision from absence of visible bars.'},
      'S5':{'path':'book_frost_prechter/Elliott_Wave_Principle_Frost_Prechter_20th_Anniversary_1998.pdf',
        'locator':'PDF/printed page 31, Motive Waves and Impulse','class':'SOURCE_DEFINITION',
        'excerpt':'Motive waves subdivide into five waves',
        'meaning':'Five-position motive/impulse structural description is an expectation, not certification by five visible turns.'},
      'S6':{'path':'book_frost_prechter/Elliott_Wave_Principle_Frost_Prechter_20th_Anniversary_1998.pdf',
        'locator':'PDF/printed pages 32–33, Extension, Figures 1-5 and 1-8','class':'SOURCE_GUIDELINE',
        'meaning':'Extensions and nested first/second alternatives illustrated; frequent third extension is not a hard selection rule.',
        'figure_limit':'Illustrations establish possible organization, not NVDA endpoints or a universal count-selection rule.'},
      'S7':{'path':'docs/elliott/SOURCE_POLICY.md','root':'Brain_LOCKED',
        'locator':'P005 policy adoption and USER_APPROVED_PROJECT_CONVENTIONS subsection',
        'class':'SOURCE_RULE','qualification':'P005 underlying rule class preserved; percentage sufficient-condition selection and arithmetic conventions are USER_APPROVED_PROJECT_CONVENTIONS, not new source rules.',
        'meaning':'No sufficiency computation from approximate screenshot operands; no rescue of P004; no negative P005 inference.'},
      'S8':{'path':'docs/elliott/DEGREE_RECURSION_BRAIN.md','root':'Brain_LOCKED',
        'locator':'degree and recursive internal validation sections','class':'SOURCE_DEFINITION',
        'meaning':'Children belong to one parent; timeframe is observation resolution, not established degree; unresolved internals remain unresolved.'},
      'S9':{'path':'docs/elliott/SOURCE_EVIDENCE_MAP.json','root':'Brain_LOCKED','locator':'P023',
        'class':'SOURCE_RULE','meaning':'No invention of internals hidden by chart resolution.'}}
    save('source_references.json', {'default_root':'Sources_LOCKED','references':refs,
      'source_manifest_sha256':'ad774642080c9112796510c01697fd70f2499c828aede547de0b3d39429ad089',
      'analyst_boundary':'Scenario choices and pixel regions below are analyst hypotheses, not statements found in the sources.',
      'reviewed_existing_research':[
        'NORMAL-IMPULSE-PARTIAL-FAMILY-HYPOTHESIS-AND-EXECUTABLE-SCOPE-V1/protected_source_findings.json',
        'P006-AND-TERMINAL-BASE-CASE-DECISION-PACK-V1/decision.json'],
      'not_reopened':['P006 CONFLICT','Flat/Triangle freezes','SOURCE_DERIVED_BASE_CASE_NOT_FOUND']})
    # Ordering is chronological visual-region ordering, NOT an exact bar date.
    raw=[
      ('d0',0,'1999 data boundary','~0.03–0.05','monthly',False),
      ('e02',1,'2002 autumn low region','~0.065–0.080','early_weekly',False),
      ('e03',2,'2003 mid-year high region','~0.21–0.23','early_weekly',False),
      ('e04',3,'2004 summer low region','~0.075–0.09','early_weekly',False),
      ('e06h',4,'2006 spring high region','~0.50–0.55','early_weekly',False),
      ('e06l',5,'2006 summer low region','~0.28–0.32','early_weekly',False),
      ('e07',6,'2007 second-half high region','~0.90–1.00','early_weekly',False),
      ('e09',7,'late 2008 / early 2009 low cluster','~0.14–0.18','middle_weekly',False),
      ('e11',8,'2011 early-year high region','~0.60–0.70','middle_weekly',False),
      ('e12',9,'2012 second-half low region','~0.28–0.32','middle_weekly',False),
      ('e18',10,'2018 second-half high region','~7–8','middle_weekly',False),
      ('e19',11,'late 2018 / early 2019 low region','~3–3.5','middle_weekly',False),
      ('e21',12,'2021 late-year high region','~33–35','middle_weekly',False),
      ('e22',13,'2022 autumn low region','~10–12','recent_daily',False),
      ('e23h',14,'2023 summer high cluster','~48–51','recent_daily',False),
      ('e23l',15,'2023 autumn low region','~38–41','recent_daily',False),
      ('e24h',16,'2024 March high region','~95–100','recent_daily',False),
      ('e24l',17,'2024 April low region','~74–80','recent_daily',False),
      ('e25h',18,'late 2024 / early 2025 high cluster','~149–158','recent_daily',False),
      ('e25l',19,'2025 April low region','~85–95','recent_daily',False),
      ('e26h',20,'2026 May high region','~236–237','latest_daily',False),
      ('e26l',21,'2026 late-July low region','~189–194','latest_daily',False),
      ('e26a',22,'2026 late-August low region','~207–212','latest_daily',False),
      ('last',23,'early September 2026 last visible observation','230.36 displayed','latest_daily',True)]
    endpoints={k:{'order':o,'date_region':d,'price_display_or_estimate_USD':v,'primary_image':im,
      'precision':'EXACT_DISPLAYED_PRICE_DATE_UNVERIFIED' if exact else 'APPROXIMATE_VISUAL_REGION',
      'orthodox_endpoint_authority':False,'executable_operand_authority':False} for k,o,d,v,im,exact in raw}
    nodes=[]
    def node(s,id,parent,role,start,end,tf,reason,open_end=False):
        nodes.append({'scenario':s,'node_id':id,'parent_id':parent,'proposed_role':role,
          'timeframe':tf,'start_evidence':start,'end_evidence':end,
          'end_kind':'OPEN_OBSERVATION_BOUNDARY_NOT_WAVE_END' if open_end else 'PROPOSED_TURNING_REGION',
          'state':'PROVISIONAL_VISUAL_HYPOTHESIS','source_refs':['S1','S2','S5','S6','S8','S9'],
          'basis':reason,'unresolved_checks':['exact endpoint/bar identity','internal family proof','P006 frozen','degree unestablished'],
          'engine_evaluated':False,'validity_authority':False})
    for s in ('A','B'):
        node(s,s,None,'proposed larger upward structure','e02','last','1M','Selected visible 2002 turning region, not first available/IPO bar.',True)
        node(s,s+'.1',s,'1?','e02','e07','1M','Weekly expansion shown separately; five broad proposed child legs, not certified family.')
        node(s,s+'.2',s,'2?','e07','e09','1M','Deep retreat; exact low belongs to a late-2008/early-2009 cluster. Corrective family unassigned.')
        for i,(a,b) in enumerate(zip(('e02','e03','e04','e06h','e06l'),('e03','e04','e06h','e06l','e07')),1):
            node(s,f'{s}.1.{i}',s+'.1',f'{i}?',a,b,'1W','Visible weekly reversal regions inside this exact parent. Daily internals not inspected.')
    node('A','A.3','A','3?','e09','e21','1M','Interpret the 2021 high as proposed end of the larger third.')
    node('A','A.4','A','4?','e21','e22','1M','Treat the 2021–2022 retreat as the following larger correction, without a corrective family claim.')
    node('A','A.5','A','5? ongoing','e22','last','1M','Continuation hypothesis only; latest bar is not a certified fifth endpoint.',True)
    for i,(a,b) in enumerate(zip(('e09','e11','e12','e18','e19'),('e11','e12','e18','e19','e21')),1):
        node('A',f'A.3.{i}','A.3',f'{i}?',a,b,'1W','Five broad weekly legs; the long 2012–2018 leg needs finer nested evidence.')
    node('B','B.3','B','3? extended/ongoing','e09','last','1M','Alternative extension: do not assume that the 2021 high closed the larger third.',True)
    node('B','B.3.1','B.3','1?','e09','e18','1W','Possible first within the larger third. Complete internal five NOT demonstrated.')
    node('B','B.3.2','B.3','2?','e18','e19','1W','2018–2019 retreat assigned only within this alternative parent.')
    node('B','B.3.3','B.3','3? ongoing','e19','last','1W','Nested extension permitted as a hypothesis by S3/S6, not inferred from steepness.',True)
    node('B','B.3.3.1','B.3.3','1?','e19','e21','1W','Alternative role for the rise into 2021; internals not fully resolved.')
    node('B','B.3.3.2','B.3.3','2?','e21','e22','1W','Same observed retreat as A.4, but a different exact parent and proposed role.')
    node('B','B.3.3.3','B.3.3','3? ongoing','e22','last','1W','Shared recent price interval does not confirm either ancestry.',True)
    for s,parent in [('A','A.5'),('B','B.3.3.3')]:
        node(s,parent+'.1',parent,'1?','e22','e25h','1W','Proposed first up-leg ends somewhere in the late-2024/early-2025 high cluster; exact selection unresolved.')
        node(s,parent+'.2',parent,'2?','e25h','e25l','1W','Retreat to the April 2025 region; no ABC/zigzag/flat subtype assigned.')
        node(s,parent+'.3',parent,'3? continuation conditional','e25l','last','1W','Only if the advance from April 2025 remains within an unfinished actionary component.',True)
        for i,(a,b) in enumerate(zip(('e22','e23h','e23l','e24h','e24l'),('e23h','e23l','e24h','e24l','e25h')),1):
            node(s,parent+f'.1.{i}',parent+'.1',f'{i}?',a,b,'1D','Broad daily slot hypothesis; especially the last high cluster contains unresolved smaller subdivisions.')
    save('hierarchy.json',{'schema':'VISUAL_REVIEW_ONLY_NOT_ANALYSIS_OUTPUT_SCHEMA','rank':None,
      'precision_policy':'Regions are not exact dates/prices; no interpolation, ratios, equality tests or engine certificates.',
      'degree':'UNESTABLISHED; dotted IDs show parenthood only, not degree or confidence.',
      'protected_principle_ids_invented':False,'endpoints':endpoints,'nodes':nodes,
      'current_position':{
        'A':{'conditional_component':'A.5, possibly A.5.3','condition':'Only under the continuing-fifth interpretation; April-2025 advance not assumed completed.',
          'competing_local_explanation':'May-2026 may delimit a completed advance; latest rebound may instead be inside an unresolved subsequent correction. No local 1–5 or ABC imposed.'},
        'B':{'conditional_component':'B.3, possibly B.3.3.3.3','condition':'Only under the larger-third extension interpretation; all nested ancestry remains proposed.',
          'competing_local_explanation':'The same May–July–September interval may contain an unfinished correction rather than an identified actionary subwave.'},
        'engine_status':'CURRENT_WAVE_POSITION_UNRESOLVED','new_engine_call':False,
        'missing':'Exact bound endpoint eligibility, complete child structures, local May/July/August subdivisions, and frozen/base-case authority.'}})

    # Screen coordinates below use a 2048x1155 reference canvas, NOT price data.
    # Each callout names one node and exactly its end evidence (or contextual region).
    views=[]
    def view(name,scenario,image,title,marks,footer):
        views.append({'name':name,'scenario':scenario,'image':image,'title':title,'marks':marks,'footer':footer})
    def mark(node,e,x,y,dx,dy,label=None): return {'node':node,'evidence':e,'xy':[x,y],'offset':[dx,dy],'label':label or node+'?'}
    view('A_monthly','A','monthly','A | Larger fifth continuation? | Monthly 1999–2026',[
      mark('A','e02',324,905,5,-100,'2002 origin REGION?'),mark('A.1','e07',636,667,-35,-75),
      mark('A.2','e09',703,827,15,35),mark('A.3','e21',1511,343,-65,-85),
      mark('A.4','e22',1563,437,15,65),mark('A.5','last',1807,168,-190,-40,'A.5? OPEN')],
      '1999 is only the data boundary. A.5 may contain the last bar only conditionally; completion is not established.')
    view('B_monthly','B','monthly','B | Larger third still extending? | Monthly 1999–2026',[
      mark('B','e02',324,905,5,-100,'2002 origin REGION?'),mark('B.1','e07',636,667,-35,-75),
      mark('B.2','e09',703,827,15,35),mark('B.3.1','e18',1316,480,-95,-80),
      mark('B.3.2','e19',1329,556,15,55),mark('B.3','last',1807,168,-230,-40,'B.3? OPEN')],
      'Same market history, different parenthood. Extension is a hypothesis, not a preferred count or proof from slope.')
    for s in ('A','B'):
        view(s+'_early_weekly',s,'early_weekly',s+' | Proposed children of '+s+'.1 | Weekly 2001–2009',[
          mark(s+'.1','e02',463,929,-110,-60,'origin REGION?'),
          mark(s+'.1.1','e03',600,589,-60,-65),mark(s+'.1.2','e04',849,891,10,20),
          mark(s+'.1.3','e06h',1218,348,-85,-65),mark(s+'.1.4','e06l',1257,514,15,30),
          mark(s+'.1.5','e07',1523,168,10,45)],
          'Parent interval: 2002 autumn to 2007 high cluster. Weekly legs are proposed; pre-2022 Daily internals are uninspected.')
    view('A_middle_weekly','A','middle_weekly','A | Proposed children of A.3 | Weekly 2008–2022',[
      mark('A.3','e09',190,962,15,-80,'origin REGION?'),mark('A.3.1','e11',456,747,-25,-70),
      mark('A.3.2','e12',655,860,0,35),mark('A.3.3','e18',1360,395,-110,-80),
      mark('A.3.4','e19',1390,516,10,45),mark('A.3.5','e21',1735,168,-140,-35)],
      'A.3 spans the 2008/09 low cluster to the 2021 high. Long interior legs remain incomplete; P006 is not adjudicated.')
    view('B_middle_weekly','B','middle_weekly','B | Nested extension alternative | Weekly 2008–2022',[
      mark('B.3','e09',190,962,15,-80,'origin REGION?'),mark('B.3.1','e18',1360,395,-120,-80),
      mark('B.3.2','e19',1390,516,10,45),mark('B.3.3.1','e21',1735,168,-180,-35),
      mark('B.3.3.2','e22',1842,335,-210,50)],
      'B.3.3 remains OPEN beyond this window. The 2008/09–2018 first-child family is unresolved, not assumed proved.')
    for s,parent in [('A','A.5'),('B','B.3.3.3')]:
        view(s+'_recent_daily',s,'recent_daily',s+' | Proposed children of '+parent+'.1 | Daily 2022–2025',[
          mark(parent+'.1','e22',164,973,25,-90,'origin REGION?'),
          mark(parent+'.1.1','e23h',727,505,-140,-60),mark(parent+'.1.2','e23l',835,575,0,50),
          mark(parent+'.1.3','e24h',1100,303,-165,-55),mark(parent+'.1.4','e24l',1147,377,20,35),
          mark(parent+'.1.5','e25h',1569,171,-165,-50),mark(parent+'.2','e25l',1764,338,-140,60)],
          'High cluster late-2024/early-2025 is unresolved at bar level; callout is representative, not an exact chosen orthodox end.')
        view(s+'_latest_daily',s,'latest_daily',s+' | Latest observation inside '+parent+'? | Daily April–September 2026',[
          mark(parent+'.3','e26h',581,166,-170,-30,'May REGION ~236–237'),
          mark(parent+'.3','e26l',1403,710,-210,55,'July REGION ~189–194'),
          mark(parent+'.3','e26a',1693,494,-230,50,'August REGION ~207–212'),
          mark(parent+'.3','last',1838,224,-260,-100,'230.36 DISPLAYED')],
          'Context regions, NOT additional wave labels. Continuing rise versus unresolved correction: CURRENT_WAVE_POSITION_UNRESOLVED.')
    byid={n['node_id']:n for n in nodes}
    for v in views:
        v['coordinate_basis']=[2048,1155]
        v['source_image']=f"originals/{v['image']}.png"
        v['output']=f"annotated/{v['name']}.png"
        for m in v['marks']:
            assert byid[m['node']]['scenario']==v['scenario']
            m['relationship']='context_region' if v['image']=='latest_daily' and m['evidence']!='last' else ('start' if m['evidence']==byid[m['node']]['start_evidence'] else 'end')
            if m['relationship']!='context_region': assert m['evidence']==byid[m['node']][m['relationship']+'_evidence']
    save('annotations.json',views)
    render(views)
    artifact(provenance)
    return nodes, endpoints, refs, views

def render(views):
    out=PACK/'annotated'; out.mkdir(exist_ok=True)
    font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',27)
    titlefont=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',34)
    small=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',25)
    for v in views:
        src=Image.open(PACK/v['source_image']).convert('RGB')
        w,h=src.size; sx=w/2048; sy=h/1155; top=108
        canvas=Image.new('RGB',(w,h+228),'#101c2b'); canvas.paste(src,(0,top)); d=ImageDraw.Draw(canvas)
        color='#155e8b' if v['scenario']=='A' else '#70419a'
        d.text((30,15),v['title'],font=titlefont,fill='white')
        d.text((30,61),'BATS:NVDA / Cboe One | USD LOG | Captured 2026-09-07 | ALL ROLE LABELS PROVISIONAL',font=small,fill='#c9d8e7')
        for m in v['marks']:
            x,y=m['xy']; dx,dy=m['offset']; px,py=round(x*sx),round(y*sy)+top
            bx,by=round((x+dx)*sx),round((y+dy)*sy)+top
            tw=d.textbbox((0,0),m['label'],font=font)[2]; bw=tw+22; bh=40
            bx=max(8,min(w-bw-8,bx)); by=max(top+4,min(h+top-bh-4,by))
            d.line((px,py,bx+bw//2,by+bh//2),fill=color,width=3)
            d.ellipse((px-8,py-8,px+8,py+8),outline=color,width=3)
            d.rounded_rectangle((bx,by,bx+bw,by+bh),radius=6,fill='white',outline=color,width=3)
            d.text((bx+11,by+4),m['label'],font=font,fill=color)
        # No synthetic line joins endpoints. Actual original candlesticks retained.
        d.text((30,h+top+14),v['footer'],font=small,fill='white')
        d.text((30,h+top+59),'Approximate regions only; no exact rule operands, established degree, ranking, forecast or family certification.',font=small,fill='#c9d8e7')
        canvas.save(PACK/v['output'])

def artifact(provenance):
    import sqlite3
    from datetime import datetime, timezone
    query="SELECT timeframe, COUNT(*) AS windows FROM inspected_capture GROUP BY timeframe ORDER BY CASE timeframe WHEN 'Monthly' THEN 1 WHEN 'Weekly' THEN 2 ELSE 3 END"
    with sqlite3.connect(':memory:') as conn:
        conn.execute('CREATE TABLE inspected_capture (image TEXT, timeframe TEXT)')
        for name,item in provenance['images'].items():
            tf=item.get('timeframe') or item['metadata']['chart']['resolution']
            conn.execute('INSERT INTO inspected_capture VALUES (?,?)',(name,{'1M':'Monthly','1W':'Weekly','1D':'Daily'}[tf]))
        coverage=[{'timeframe':tf,'windows':n} for tf,n in conn.execute(query)]
    report=(PACK/'report_ar.md').read_text(encoding='utf-8')
    # Canonical shared report builder owns HTML layout. Markdown is its authoring source.
    blocks=[]
    import re
    for i,section in enumerate(re.split(r'(?m)(?=^## )',report)):
        blocks.append({'id':f'section_{i}','type':'markdown','body':section.strip()})
    for name in ('A_monthly','B_monthly','A_latest_daily','B_latest_daily'):
        data=base64.b64encode((PACK/'annotated'/f'{name}.png').read_bytes()).decode()
        blocks.append({'id':name,'type':'html','body':f'<figure><img alt="{name}: provisional visual hypothesis" src="data:image/png;base64,{data}"/><figcaption>{name} — proposed roles only; see linked hierarchy in review pack.</figcaption></figure>'})
    blocks.append({'id':'coverage','type':'chart','chartId':'inspected_windows'})
    save('artifact.json',{'surface':'report','manifest':{'version':1,'surface':'report',
      'title':'NVDA: سيناريوهان بصريان مشروطان، لا عدّ مؤكد','generatedAt':'2026-09-07T15:23:25Z',
      'blocks':blocks,'charts':[{'id':'inspected_windows','title':'النوافذ المفحوصة حسب الإطار — لا تعني اكتمال الداخليات',
      'type':'bar','dataset':'coverage','sourceId':'captures','encodings':{
      'x':{'field':'timeframe','type':'nominal','label':'الإطار'},'y':{'field':'windows','type':'quantitative','label':'نوافذ مفحوصة'}}}],
      'sources':[{'id':'captures','label':'BATS:NVDA / Cboe One — captured charts, 7 September 2026','path':'capture_provenance.json',
      'query':{'sql':query,'engine':'SQLite in-memory','language':'sql','tables_used':['inspected_capture'],
      'executed_at':datetime.now(timezone.utc).isoformat(),
      'description':'Count the seven inspected image receipts by their actual metadata resolution; prepare_pack.py loads the in-memory table from capture_provenance.json. Counts are coverage windows, not bars or validated subwaves.',
      'filters':['Only seven saved, inspected screenshots in this review'] }},
      {'id':'methodology','label':'Protected source references and adopted policy','path':'source_references.json'}]},
      'snapshot':{'version':1,'generatedAt':'2026-09-07T15:23:25Z','status':'partial','datasets':{'coverage':coverage},
      'accessIssues':[{'message':'Internal family proof, exact historic endpoints and current wave position remain unresolved.'}]},'sources':[]})

if __name__=='__main__':
    n,e,r,v=prepare()
    print(json.dumps({'nodes':len(n),'endpoint_regions':len(e),'source_refs':len(r),'annotated_views':len(v)}))
