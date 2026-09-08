"""Read-only evidence reconciliation and native report export for targeted search."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import math
import sqlite3
from pathlib import Path

import nvda_targeted_recent as task
import nvda_observational_hierarchy_report as links_report

old=task.old
display=links_report.display
CHART_SQL='SELECT time, price, field, label, kind, source_hash FROM saved_chart_evidence ORDER BY time, kind'


def reconcile(doc,snapshots,raw):
    # Reuse the approved independent raw/link reconciliation; its legacy totals
    # are a display adapter only, never a mutation of issued live evidence.
    check=dict(doc)
    check['links']=[dict(l,style='REJECTED' if l['p004_rejected'] else 'OBSERVATIONAL' if l['surviving_observational_link'] else 'UNRESOLVED') for l in doc['links']]
    check['totals']={'links':len(doc['links']),'pairings':sum(len(l['pairings']) for l in doc['links']),
        'relationships':dict(Counter(l['relationship'] for l in doc['links'])),
        'surviving_observational_links':sum(l['surviving_observational_link'] for l in doc['links']),
        'rejected_link_contexts':sum(l['p004_rejected'] for l in doc['links']),'hypotheses':len(doc['hypotheses'])}
    receipt=links_report.reconcile(check,snapshots,raw)
    source={s.observations.provenance.source_sha256:{r['value'][0]:r['value'] for r in raw[k]['rows']} for k,s in snapshots.items()}
    fields={'open':1,'high':2,'low':3,'close':4};checked=0
    all_rows=doc['hypotheses']+doc['corrective_hypotheses']
    if len({h['display_id'] for h in all_rows})!=len(all_rows):raise ValueError('Duplicate aliases')
    for h in doc['corrective_hypotheses']:
        if h['family'] not in ('SINGLE_ZIGZAG','FLAT') or h['family_validity'] or h['parent_node_id'] is not None or h['p004'] is not None or h['p005'] is not None:
            raise ValueError('Unsupported corrective claim or authority leakage')
        for e in h['endpoints']:
            value=source[e['source_hash']][datetime.fromisoformat(e['timestamp_utc']).timestamp()][fields[e['price_field']]]
            if Fraction(value)!=Fraction(e['price']) or old.p.plain(Fraction(value))!=e['represented_ratio']:
                raise ValueError('Corrective raw endpoint mismatch')
            checked+=1
        if h['authority']['family_validity']:raise ValueError('False family certificate')
        executed=[c for c in h['coverage'] if c['state']=='SUPPLIED_AND_EXECUTED']
        if len(executed)!=1 or 'CARDINALITY' not in executed[0]['behavior_id']:raise ValueError('Unexpected family behavior')
    for h,t in zip(all_rows,doc['open_tails'],strict=True):
        if t!=task.tail(h,snapshots[h['resolution']]):raise ValueError('Open tail altered or falsely completed')
    new=[h for h in doc['hypotheses'] if h['evaluation_origin']=='NEW']
    res_by_hash={s.observations.provenance.source_sha256:k for k,s in snapshots.items()}
    historical=[]
    for path in (old.PACK/'canonical_hierarchy.json',task.previous.PACK/'canonical_hierarchy.json'):
        historical+=old.read(path)['hypotheses']
    old_keys={task.exported_key(h,res_by_hash[h['source_response_sha256']]) for h in historical}
    overlaps=[h['display_id'] for h in new if task.exported_key(h,h['resolution']) in old_keys]
    if overlaps:raise ValueError('Previously evaluated coordinate sequence labelled new: '+str(overlaps))
    t=doc['totals']
    expected={'new_normal_hypotheses':len(new),'new_corrective_evaluate_as_hypotheses':len(doc['corrective_hypotheses']),
        'new_unique_normal_endpoint_sequences':len({task.exported_key(h,h['resolution']) for h in new}),
        'new_p004':dict(Counter(h['p004']['status'] for h in new)),
        'new_p005':dict(Counter(h['p005']['status'] for h in new)),
        'new_fatal_despite_p005':sum(h['p004']['fatal'] and h['p005']['status']=='SUFFICIENT_CONDITION_ESTABLISHED' for h in new)}
    if any(t[k]!=v for k,v in expected.items()):raise ValueError('New/old outcome totals altered')
    if sum(x['status']=='EVALUATED' for x in doc['execution_ledger'])!=len(new)+len(doc['corrective_hypotheses'])//2:raise ValueError('Execution ledger mismatch')
    return dict(receipt,corrective_raw_fields_checked=checked,new_totals_reconciled=True,open_tails_checked=len(all_rows),
                prior_full_digital_and_recent_contexts_compared=len(historical),old_coordinate_sequences_mislabelled_new=overlaps)


def chart_rows(snapshot,hypothesis=None,start=None):
    """Display full remaining captured tail, not a fabricated final wave."""
    if hypothesis and (hypothesis['source_response_sha256']!=snapshot.observations.provenance.source_sha256 or any(e['source_hash']!=snapshot.observations.provenance.source_sha256 for e in hypothesis['endpoints'])):
        raise ValueError('Foreign chart snapshot provenance')
    if hypothesis and start is None:start=hypothesis['endpoints'][0]['timestamp_utc']
    rows=[]
    for b in snapshot.observations.bars:
        if start and b.timestamp_utc.isoformat()<start:continue
        rows.append({'time':b.timestamp_utc.isoformat(),'price':b.close,'field':'close','label':'',
                     'kind':'captured close','source_hash':snapshot.observations.provenance.source_sha256})
    if hypothesis:
        for i,e in enumerate([hypothesis['endpoints'][0]]+hypothesis['endpoints'][1::2]):
            label=str(i) if hypothesis['family']=='NORMAL_IMPULSE_PARTIAL' else ('origin' if i==0 else 'child_'+str(i))
            rows.append({'time':e['timestamp_utc'],'price':e['price'],'field':e['price_field'],
                         'label':hypothesis['display_id']+' / '+label,'kind':'proposed endpoint','source_hash':e['source_hash']})
    db=sqlite3.connect(':memory:');db.row_factory=sqlite3.Row
    db.execute('CREATE TABLE saved_chart_evidence(time TEXT, price REAL, field TEXT, label TEXT, kind TEXT, source_hash TEXT)')
    db.executemany('INSERT INTO saved_chart_evidence VALUES(:time,:price,:field,:label,:kind,:source_hash)',rows)
    rows=[dict(r) for r in db.execute(CHART_SQL)];db.close()
    for row in rows:
        dt=datetime.fromisoformat(row['time']);a=datetime(dt.year,1,1,tzinfo=timezone.utc);b=datetime(dt.year+1,1,1,tzinfo=timezone.utc)
        row['year']=dt.year+(dt-a).total_seconds()/(b-a).total_seconds()
        row['display_log10_usd']=math.log10(row['price'])
    rows.sort(key=lambda r:(r['time'],r['kind']))
    # No plotted date/price can be synthesized from an endpoint estimate.
    lookup={b.timestamp_utc.isoformat():b for b in snapshot.observations.bars}
    for r in rows:
        if Fraction(getattr(lookup[r['time']],r['field']))!=Fraction(r['price']):raise ValueError('Chart raw mismatch')
    return rows


def summaries(doc):
    incoming={}
    for l in doc['links']:
        if l['surviving_observational_link']:incoming.setdefault(l['child_alias'],[]).append(l)
    result=[]
    for h in doc['hypotheses']:
        if h['evaluation_origin']!='NEW' or h['p004']['fatal']:continue
        result.append({'alias':h['display_id'],'start':h['endpoints'][0],'end':h['endpoints'][-1],
            'resolution':h['resolution'],'incoming_links':[l['link_id'] for l in incoming.get(h['display_id'],[])],
            'classification':'INTERIOR_OR_BOUNDARY_SUPPORTED_OBSERVATIONAL_PROPOSAL' if incoming.get(h['display_id']) else 'INDEPENDENT_LOCAL_HYPOTHESIS',
            'p005':h['p005'],'internal_status':'INTERNALS_UNRESOLVED'})
    return result


def wave_rows(doc):
    rows=display.wave_table(doc)
    for h in doc['corrective_hypotheses']:
        for i in range(3):
            a,b=h['endpoints'][2*i:2*i+2]
            rows.append({'node_id':h['display_id']+'.'+str(i+1),'parent_id':h['display_id'],'role':'child_'+str(i+1),
                'resolution':h['resolution'],'relative_degree':'DIRECT_CHILD_PROPOSAL_ONLY','status':'INTERNALS_UNRESOLVED',
                'start':a['timestamp_utc'],'start_field':a['price_field'],'start_price':a['price'],
                'end':b['timestamp_utc'],'end_field':b['price_field'],'end_price':b['price'],
                'source_hash':a['source_hash'],'unresolved':['CARDINALITY_ONLY','NO_CHILD_FAMILY_PROOF','SOURCE_DERIVED_BASE_CASE_NOT_FOUND'],
                'source_refs':['P007' if h['family']=='SINGLE_ZIGZAG' else 'P008']})
    return rows


def boundary_diagnostics(snapshots):
    """Factual date-window extrema, never substitute operands or new bindings."""
    rows=[]
    for date in ('2026-07-29','2026-08-11','2026-08-24'):
        for res in ('1D','240','60','15'):
            s=snapshots[res];bars=[b for b in s.observations.bars if b.timestamp_utc.date().isoformat()==date]
            price=min((b.low for b in bars),default=None)
            rows.append({'date':date,'resolution':res,'bar_count':len(bars),'minimum_observed_low':price,
                'occurrence_bar_labels':[b.timestamp_utc.isoformat() for b in bars if b.low==price],
                'source_hash':s.observations.provenance.source_sha256,'capture':task.previous.metadata(s)['captured_at_utc'],
                'usage':'DIAGNOSTIC_ONLY_NOT_REPLACEMENT_ENDPOINT_OR_RESAMPLING'})
    return rows


def build(output=task.PACK):
    output=Path(output);doc=old.read(output/'canonical_hierarchy.json');snapshots,raw=old.tv.load_inputs()
    if doc['stage']!=task.STAGE or (output/'REVIEW_manifest.json').exists() or not output.resolve().is_relative_to(old.ROOT):
        raise ValueError('Only this unsealed Runtime report may be regenerated')
    def save(name,value):
        # Generated report-only artifacts, never inputs or historical baselines.
        import json
        destination=(output/name).resolve()
        if not destination.is_relative_to(output.resolve()):raise ValueError('Escaping report output')
        with destination.open('w',encoding='utf-8',newline='\n') as f:
            json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
    audit=reconcile(doc,snapshots,raw)
    plan=old.read(task.PACK/'search_plan.json');selection=old.read(output/'selection_before_evaluation.json')
    indicators=display.indicator_rows(old.read(old.PREVIOUS/'indicators_1D_verified.json'),old.read(old.PREVIOUS/'indicator_summary.json'))
    save('indicator_evidence.json',{'rows':indicators,'source_sha256':old.hash_file(old.PREVIOUS/'indicators_1D_verified.json')})
    synthesis=summaries(doc);paths=links_report.paths(doc);coverage=links_report.coverage_rows(doc,snapshots)
    save('path_synthesis.json',{'survivors':synthesis,'paths':paths,'no_preference_order':True})
    save('link_coverage.json',coverage)
    diagnostics=boundary_diagnostics(snapshots);save('boundary_diagnostics.json',diagnostics)
    waves=wave_rows(doc);save('wave_table.json',waves)
    t=doc['totals'];by_id={h['display_id']:h for h in doc['hypotheses']+doc['corrective_hypotheses']}
    supported=[l for l in doc['links'] if l['surviving_observational_link']]
    now=datetime.now(timezone.utc).isoformat();title='NVDA — بحث حديث ومسارات مقترحة'
    manifest={'version':1,'surface':'report','title':title,'description':'لقطات 8 سبتمبر 2026؛ بحث محدود لا عدّ معتمد',
        'generatedAt':now,'cards':[],'charts':[],'tables':[],'blocks':[],
        'sources':[{'id':'evidence','label':'Saved BATS:NVDA / Cboe One targeted public evaluations','path':'canonical_hierarchy.json'}]}
    parts=[];datasets={}
    def prose(key,body):
        manifest['blocks'].append({'id':key,'type':'markdown','body':body});parts.append(body)
    def table(key,title,headers,rows):prose(key,'### '+title+'\n\n'+display.mdtable(headers,rows))
    def plot(key,res,h=None,start=None):
        rows=chart_rows(snapshots[res],h,start);datasets[key]=rows
        chart={'id':key,'title':(h['display_id'] if h else 'السياق الكامل')+' — '+res,'type':'scatter','dataset':key,'layout':'full',
            'encodings':{'x':{'field':'year','type':'quantitative','label':'وقت البار — عرض مستمر'},
            'y':{'field':'display_log10_usd','type':'quantitative','label':'log10(USD) للعرض فقط'},
            'label':{'field':'label','type':'nominal'},'tooltip':[{'field':'time','label':'بار UTC'},{'field':'price','label':'السعر الأصلي'},{'field':'field','label':'الحقل'}]},
            'labels':{'values':'all'},'source':{'id':key+'-source','label':'Captured closes plus original proposed endpoints including unlabelled captured tail','path':'chart_rows.json',
            'query':{'engine':'SQLite in-memory','language':'sql','sql':CHART_SQL,'tables_used':['saved_chart_evidence'],
                     'description':'Original saved close rows and separately labelled hypothesis endpoint rows; native report projection. Subsequent year/log10 transforms are display-only.'}}}
        manifest['charts'].append(chart);manifest['blocks'].append({'id':key+'-block','type':'chart','chartId':key,'layout':'full'})
        parts.append('الرسم '+key+' في report.html؛ الإغلاقات تمتد إلى آخر بار محفوظ ولا تُمَدّ تسميات الأدوار إليه.')
    prose('title','# '+title)
    latest=doc['input_coverage']['15'];maxreach=max((p['last_evidenced_endpoint']['timestamp_utc'] for p in paths),default='لا مسار')
    prose('summary',f'''## Executive Summary — الخلاصة

**البحث الجديد لا يحوّل الحركة الأخيرة إلى موجة نشطة مثبتة.** آخر لقطة 15m عند {latest['metadata']['captured_at_utc']} تسجل إغلاقاً {latest['last_close']} في بار جارٍ. نعرض البارات اللاحقة لآخر دور مقترح بدلاً من تمديد التسميات إليها.

**اختُبرت بدائل جديدة فعلاً:** {t['new_normal_hypotheses']} فرضية Normal Impulse جزئية و{t['new_corrective_evaluate_as_hypotheses']} اختبار عائلة تصحيحية. أُعيد بناء M1/M2 فقط من القديم. توجد {len(supported)} وصلات ملاحظة غير مرفوضة؛ آخر نهاية لمسار من السياق الشهري هي {maxreach}. الوصلات ليست تقسيماً كاملاً ولا تأكيدات مستقلة.

**التفسير العملي مشروط:** إذا كان M2 سياقاً مناسباً، فالأجزاء المحتواة الموضحة لاحقاً قد تقع داخله؛ أما الفروع بلا وصلة مدعومة فتبقى قراءات محلية مستقلة. بديل الحركة التصحيحية مفتوح كاختبار Zigzag/Flat، لكنه لا يُثبت بمجرد ثلاثة أجزاء. لا احتمال أو تفضيل أو هدف سعري.''')
    prose('new-paths','''## الوصلات الجديدة تعرض أجزاء محتواة، لا سلسلة تُلصق لمجرد قربها

↝ تعني حدوداً مرصودة واحتواءً مقترحاً؛ INTERIOR_OBSERVATION لا يغطي طرفي دور الأب. BOUNDARY_SUPPORTED_PROPOSED_REFINEMENT يعني مطابقة الطرفين فقط، لا اكتمال داخليات إليوت. × يستبعد فرضية Normal Impulse نفسها بسبب P004، ولا يستبعد المنطقة أو يثبت شقيقها. الفجوات غير المسماة تبقى غير محسومة. الأطر الزمنية دقات ملاحظة وليست درجات تلقائية.''')
    table('paths','مسارات السياق الشهري غير المرفوضة',['المسار','الفرضية الأخيرة','آخر نهاية UTC','السعر/الحقل','بارات بعدها'],
        [[' ↝ '.join(p['links']),p['leaf'],p['last_evidenced_endpoint']['timestamp_utc'],str(p['last_evidenced_endpoint']['price'])+' '+p['last_evidenced_endpoint']['price_field'],next(x['trailing_bars'] for x in doc['open_tails'] if x['hypothesis']==p['leaf'])] for p in paths])
    if 'D2026:1D:N6:S38' in by_id:
        h=by_id['D2026:1D:N6:S38'];p=[h['endpoints'][0]]+h['endpoints'][1::2]
        if [(e['timestamp_utc'][:10],e['price']) for e in p] != [('2026-07-29',190.01),('2026-08-07',224.76),('2026-08-11',216.2),('2026-08-17',227.92),('2026-08-24',207.25),('2026-08-27',230.47)]:
            raise ValueError('Specific recent narrative requires review against changed operands')
        prose('concrete-reading','''## وصلنا إلى 27 أغسطس، لكن هذا لا يجعل حركة سبتمبر امتداداً مؤكداً

القراءة اليومية D2026:1D:N6:S38 تقترح الأدوار: 190.01 في 29 يوليو → 224.76 في 7 أغسطس → 216.20 في 11 أغسطس → 227.92 في 17 أغسطس → 207.25 في 24 أغسطس → 230.47 في 27 أغسطس. لها احتواء مرصود داخل الدور الخامس المقترح لـM2. P004 غير مخالف، أما P005 فلا يثبت شرط الكفاية لهذا الترتيب؛ لا يعني ذلك رفضاً سلبياً. P006 والداخليات لم يُثبتا.

إذا كان هذا التقسيم المقترح مناسباً، فإن البارات اللاحقة لـ27 أغسطس تقع خارج نهايته المرسومة، ولا يجوز تسميتها «السادسة» أو موجة نشطة جديدة. هناك أيضاً اختبار ثلاثي مستقل يبدأ 24 أغسطس عند 207.25، ثم 230.47 في 27 أغسطس، ثم 215.10 في 1 سبتمبر، ثم 234.76 في 4 سبتمبر. يمكن طرحه لتقييم Zigzag أو Flat، لكن لا نُقرّه ABC ولا نوصله قسراً بالأدوار اليومية السابقة. البار الملتقط في 8 سبتمبر لاحق حتى لنهايته.

إذن تحسن الامتداد المرصود إلى أغسطس، لكن لا يوجد في نتائج هذا البحث مسار شهري–يومي–لحظي غير مرفوض ومكتمل الوصلات. القراءات اللحظية حتى 4 سبتمبر تبقى محلية مستقلة؛ لا يدعم هذا وحده اختيار عائلة أو موضع موجة نشطة.''')
    prose('new-boundary-gap','''## تعثّر الربط الحديث ليس محصوراً في اختلاف يوليو

الدوران حول 11 أغسطس يحتاجان low يومياً 216.20؛ أدنى low محفوظ في 4H/1H/15m لذلك التاريخ هو 216.18. والدوران حول 24 أغسطس يحتاجان 207.25 يومياً، مقابل 207.22 لحظياً. سجل وقوع الحدود نفسه لا يجد القيمة اليومية المطلوبة في الصفوف الأدق؛ لذلك لا يكفي احتواء التوقيت لإنشاء الوصلة.

هذه حدود مرصودة مختلفة في لقطات غير متزامنة، لا تقريب عددي مسموح ولا تشخيصاً مؤكداً لسبب اختلاف التغذية. جدول الحد الأدنى أدناه تشخيص لصفوف التاريخ فقط؛ لم يُعد تجميع سلسلة جديدة ولم تُستبدل به أية نهاية. حل مطابقة هذين الحدين أو دليل بديل مصرح به أضيق من طلب إطار برمجي عام جديد.''')
    table('boundary-table','قيم الحدود غير المتطابقة في الصفوف المحفوظة',['التاريخ','الدقة','الصفوف','أدنى low مرصود','بارات الوقوع UTC'],
        [[r['date'],r['resolution'],r['bar_count'],r['minimum_observed_low'],'; '.join(r['occurrence_bar_labels'])] for r in diagnostics])
    developing=[h for h in doc['corrective_hypotheses'] if h['endpoints'][-1]['pivot_state']=='DEVELOPING' and h['endpoints'][-1]['timestamp_utc']==doc['input_coverage'][h['resolution']]['last_bar']]
    prose('developing-tail','''## يوجد طرف مقترح جارٍ على 4H، لكنه ليس إثبات موضع موجة نشطة

احتفظ البحث باختبارات ثلاثية مستقلة على 4H تنتهي في البار الجاري الملتقط 8 سبتمبر 13:30 UTC، عند low=229.06؛ إغلاق لقطة 4H نفسها 230.0. نهاية child_3 هنا مقترحة ومرتبطة فعلاً بملاحظة هندسية DEVELOPING، وليست نهاية اخترعناها لإغلاق ست نقاط. لا تُستبدل بإغلاق 15m البالغ 229.29، لأن اللقطتين مختلفتان.

إذا صح هذا الاقتراح المحلي، فالحد الجاري يخص نهاية الدور الثالث المقترح في ذلك الاختبار الثلاثي فقط. لم تُثبت عائلته كـZigzag أو Flat، ولا صلته بالسياق الشهري أو اكتمال الدور؛ ولذلك لا نسميه C مؤكدة أو موجة نشطة مثبتة. تكراره في نافذتين مع اختبارَي عائلة ينتج أربعة سياقات، لا أربعة تأكيدات مستقلة. هذا يختلف عن الفرضيات الدافعة التي تنتهي قبل آخر بار وتترك ذيلاً لاحقاً غير مسمى.''')
    table('developing-contexts','الأطراف الجارية الأصلية في سياقاتها',['الفرضية','آخر بار UTC','حقل/سعر','حالة المحور','سلطة اكتمال'],
        [[h['display_id'],h['endpoints'][-1]['timestamp_utc'],h['endpoints'][-1]['price_field']+' '+str(h['endpoints'][-1]['price']),h['endpoints'][-1]['pivot_state'],'لا'] for h in developing])
    if developing:
        h=developing[0]
        prose('developing-plot-note','الرسم التالي يبقي child_1–3 كأدوار اختبار محلي مستقل على 4H، ويعرض النهاية الجارية دون ترقيتها إلى اكتمال أو عائلة مثبتة. السعر المعروض هو الحقل المرصود الأصلي، لا مستوى تداول.')
        plot('developing-4h','240',h)
    prose('history','''## التاريخ الكبير يظل سياقاً مقترحاً، لا تفسيراً مكتملاً منذ الإدراج

البيانات الشهرية المحفوظة تبدأ في 1999. حد البيانات ليس أصل موجة. لم نعد البحث التاريخي الشامل: احتفظنا بـM1/M2 كمقترحين سابقين، ولا نرفعهما إلى حقيقة. يمتد الدور الخامس المقترح من low=10.813 في بار أكتوبر 2022 إلى قمة مايو 236.54 في M1، أو قمة سبتمبر 234.76 في M2. تاريخ البار التجميعي ليس لحظة القمة داخله. الرسم الكامل التالي يبين الإغلاقات حتى آخر التقاط، لا كل الموجات الداخلية.''')
    plot('history','1M')
    prose('before','''## لماذا انتهى التقرير السابق في يوليو؟ ليس لأن بيانات ما بعده معدومة

التقرير السابق أعاد 25 اختياراً حديثاً سابقاً ولم يختبر البدائل المتروكة. وصلة M2 إلى JULY:1D:S0 انتهت 31 يوليو عند high=202.0. بدائل Daily الحديثة المختارة كانت مرفوضة بـP004؛ استمرار شرط P005 الكافي لم ينقذها. المطابقة 190.01 اليومية مقابل 190.02 اللحظية بقيت ناقصة، كما افتقدت الوصلات المباشرة من أكتوبر 2022 إلى اللقطات القصيرة حد البداية. هذه أسباب مختلفة عن غياب عائلة نهائية قابلة للإثبات.

هنا استُبعدت إحداثيات الاختيارات القديمة من التقييم الجديد، ثم اختير وسط كل شريحة عددية من البدائل المؤهلة زمنياً. لا اختيار بناء على نتيجة الفحص. النوافذ التي لا تحوي بدائل جديدة تسجل ذلك؛ لا يُصنع مرشح أخير بالقوة.''')
    table('compare','ما تغير فعلاً',['المقياس','القيمة'],[[k,v] for k,v in t.items() if k not in ('relationships','selection_dispositions','new_p004','new_p005')])
    table('scope','نوافذ البحث المعلنة وما فُحص فيها',['النافذة','الإطار','نقاط/مرشح','بارات النافذة','محاور','اختيارات','سقف'],
        [[s['id'],' — '.join(s['window']),s['point_count'],s['bars'],s['pivots'],len(s['selected']),s['cap']] for s in selection['searches']])
    prose('recent','''## القراءات المحلية التالية لا تتحد تلقائياً في سيناريو واحد

كل فرضية غير مرفوضة تحتفظ ببدايتها وأدوارها الخمسة ونتائجها ووصلة السياق إن وُجدت. قد يكون الجزء حركة داخل سياق أكبر، لكن علاقة «مع/ضد اتجاه الدرجة الأكبر» ليست مستنتجة من اتجاه الرسم وحده. P006 مجمّد؛ شرط P005 كافٍ جزئياً لا اختبار كامل. لا نثبت نهاية خامسة أو عائلة دافعة من عدد المحاور.

لتسهيل قراءة أحدث النوافذ، تعرض الرسوم التالية أحدث نهاية غير مرفوضة في كل دقة معنية (ترتيب عرض زمني فقط)، وتُظهر الذيل غير المسمّى بعدها. جميع البدائل، لا هذه العينة البصرية فقط، محفوظة في الجداول والتصدير.''')
    chosen=[]
    for res in ('1D','60','15'):
        options=[h for h in doc['hypotheses'] if h['evaluation_origin']=='NEW' and h['resolution']==res and not h['p004']['fatal']]
        if options:
            h=max(options,key=lambda x:(x['endpoints'][-1]['timestamp_utc'],x['display_id']));chosen.append(h['display_id'])
            a,b=h['endpoints'][0],h['endpoints'][-1];tail=task.tail(h,snapshots[res]);incoming=[l['link_id'] for l in supported if l['child_alias']==h['display_id']]
            prose('plot-note-'+res,f"### {h['display_id']} — نهاية مرصودة لا موجة حالية مؤكدة\n\nتبدأ عند {a['timestamp_utc']}، {a['price_field']}={a['price']} وتنتهي عند {b['timestamp_utc']}، {b['price_field']}={b['price']}. بعدها {tail['trailing_bars']} بارات محفوظة بلا تعيين موجي. P004: {h['p004']['status']}؛ P005: {h['p005']['status']}. " + ('لها وصلة ملاحظة: '+'؛ '.join(incoming) if incoming else 'لا وصلة نسب مدعومة؛ تبقى فرضية محلية مستقلة.')+' لا يثبت الرسم تقسيم الداخل أو اكتماله.')
            plot('recent-'+res,res,h)
    prose('corrective','''## Zigzag وFlat بديلان للفحص، لا تصنيفان تم إثباتهما

وفق PATTERN_BRAIN §F/§G وP007/P008 (SOURCE_DEFINITION)، المطلوب في Single Zigzag هو 5–3–5 وفي Flat هو 3–3–5. الأرقام متطلبات عائلة داخلية، لا شهادة تنتج عن ثلاثة أو خمسة محاور مرئية. فُحص العدد المباشر فقط عبر المسارين العامّين الموجودين؛ لا هندسة Flat المجمدة ولا تصنيف subtype ولا استنتاج ABC من الشكل.

لذلك يبقى تفسير أحدث ثلاثة أجزاء كتصحيح احتمالاً مشروطاً بتصنيف داخلي لم يُثبت، وليس بديلاً ناجحاً لأن فرضية دافعة فشلت. عقد الوصلة المرصودة الحالي يقبل تقييمات Normal Impulse المحددة فقط؛ لم نمرر إليه كائنات تصحيحية متنكرة، ولم ننشئ طبقة عقود أخرى. فجوة الربط هذه منفصلة عن فجوة الإثبات المصدري للعائلة.''')
    recent_c=[h for h in doc['corrective_hypotheses'] if h['resolution']=='1D' and h['family']=='SINGLE_ZIGZAG']
    if recent_c:
        h=max(recent_c,key=lambda x:(x['endpoints'][-1]['timestamp_utc'],x['display_id']))
        prose('corrective-chart-note',f"الرسم {h['display_id']} يعرض ثلاثة أدوار child_1–3 فقط كمدخل لتقييم Single Zigzag؛ نفس الهندسة لها اختبار Flat مستقل. نقاط النهاية ليست حروف ABC مؤكدة، والذيل بعد النهاية غير مصنّف.")
        plot('corrective-recent','1D',h)
    table('correctives','اختبارات التصحيح — كل سياق مستقل',['الفرضية','البداية UTC / سعر','النهاية UTC / سعر','فحص العدد','الداخل'],
        [[h['display_id'],h['endpoints'][0]['timestamp_utc']+' / '+str(h['endpoints'][0]['price']),h['endpoints'][-1]['timestamp_utc']+' / '+str(h['endpoints'][-1]['price']),h['state'],'UNRESOLVED — لا دليل عائلة طفل'] for h in doc['corrective_hypotheses']])
    prose('survivors','''## الأدوار غير المرفوضة محفوظة دون دمج الأشقاء

اقرأ كل عنوان كفرضية مستقلة. تسلسل الجدول هو ترتيب أدوارها فقط، لا ترتيب أفضلية بين الفرضيات. الوصلة الخارجية منفصلة عن parent_id الداخلي؛ لا ينتقل فشل طفل مستقل إلى أب آخر ولا تُثبت الشهادة المفقودة.''')
    for item in synthesis:
        h=by_id[item['alias']];a,b=item['start'],item['end']
        prose('survivor-'+h['display_id'],f"### {h['display_id']}\n\nمن {a['timestamp_utc']} ({a['price_field']}={a['price']}) إلى {b['timestamp_utc']} ({b['price_field']}={b['price']}). " + ('روابط الملاحظة: '+'؛ '.join(item['incoming_links']) if item['incoming_links'] else 'فرضية محلية مستقلة؛ لا اتصال أعلى مثبت.')+f" P005: {h['p005']['status']}؛ {h['p005']['reason']}. تبقى العائلة والداخليات وموضع الذيل غير محسومة.")
        table('roles-'+h['display_id'],'الأدوار المقترحة',['الدور','بداية UTC','حقل/سعر','نهاية UTC','حقل/سعر'],
            [[i+1,h['endpoints'][2*i]['timestamp_utc'],h['endpoints'][2*i]['price_field']+' '+str(h['endpoints'][2*i]['price']),h['endpoints'][2*i+1]['timestamp_utc'],h['endpoints'][2*i+1]['price_field']+' '+str(h['endpoints'][2*i+1]['price'])] for i in range(5)])
    prose('rejected','''## ملحق الرفض والحدود: فشل المرشح لا يثبت استحالة المنطقة

الجدول يحفظ الفرضيات المرفوضة بعينها. نتيجة P005، حتى حين تثبت الكفاية، لا تتجاوز P004. الاستبعاد من مجال الحركة المتناوبة أو نفاد الميزانية ليس رفضاً موجياً. البيانات المحمّلة ليست كلها مفحوصة، وغياب مرشح ضمن هذه العينات ليس إثبات غياب عائلة.''')
    table('rejected-table','بدائل مرفوضة بعينها',['الفرضية','بداية/نهاية UTC','P004','P005'],
        [[h['display_id'],h['endpoints'][0]['timestamp_utc']+' — '+h['endpoints'][-1]['timestamp_utc'],h['p004']['reason'],h['p005']['status']] for h in doc['hypotheses'] if h['evaluation_origin']=='NEW' and h['p004']['fatal']])
    table('bounds','الحدود الفعلية',['البند','القيمة'],[['اختيار',t['selection_dispositions']],['روابط',doc['link_budget']],['حد وقت البحث بالثواني',plan['wall_time_seconds']],['مجال هندسي', 'عرض 2، محاور أصلية متتالية، حركة غير صفرية متناوبة؛ لا أهمية موجية']])
    prose('quality','''## المؤشرات واللقطات لا تشكّل دليلاً متزامناً واحداً

جميع الأسعار BATS:NVDA / Cboe One؛ NASDAQ معرّف إدراج لا إثبات تغذية مباشرة. لا Yahoo ولا إعادة تجميع. الجلسة regular 09:30–16:00 نيويورك؛ حالة تعديل الانقسامات غير محسومة، والبارات الأخيرة جارية. القيم من لقطات مختلفة الأوقات؛ لا نُجبر نهايات الأطر على المساواة.

RSI/MACD/الحجم أدناه من الدراسة اليومية المحفوظة عند وقتها، لا من كل فرضية أو دقة. لا تفسير تباعد أو تأكيد أو تصنيف عائلة، وEWO غير مستخدم. اختلاف يوليو 190.01/190.02 باقٍ دون هامش سماح، لكنه لم يمنع اختبار أغسطس وسبتمبر.''')
    table('captures','التغطية المتاحة لا تساوي التغطية المحللة',['الدقة','أول بار','آخر بار','الالتقاط','آخر إغلاق'],[[k,v['first_bar'],v['last_bar'],v['metadata']['captured_at_utc'],v['last_close']] for k,v in doc['input_coverage'].items()])
    table('indicators','ملاحظات الدراسة اليومية فقط',['المؤشر','بار UTC','القيمة','الالتقاط','جارٍ'],[[r['indicator'],r['bar_time'],r['value'],r['capture'],r['forming']] for r in indicators])
    prose('blockers','''## ما الذي يمكن أن يغير القراءة الحالية؟

التمييز المطلوب ليس ترتيب عشرات المرشحين: يجب أن تُفسَّر داخليات الفروع بعائلات مصدرية مثبتة وأن يدعم الدليل حدود كل وصلة، لا مجرد قرب التواريخ. لا تعالج زيادة عدد المحاور وحدها P006 المجمد أو غياب قاعدة عائلة نهائية. وبالنسبة للذيل الملتقط، لا توجد هنا حجة تمنح آخر بار اسم موجة نشطة؛ القراءة الأكثر تحديداً هي الفترة المرصودة بعد آخر نهاية مقترحة في كل جدول.

الخطوة العملية إن استؤنف التحليل هي مراجعة الفروع الحديثة ذات الحدود المتطابقة المحددة في path_synthesis/link_coverage، ثم طلب الدليل الناقص لكل داخل بعينه. لا حاجة لإعادة بحث أكتوبر 2022 لكل مكوّن حديث، ولا لإعادة البحث نفسه على مصدر لم يتغير. تحسين الربط التشغيلي لا يمنح سلطة مصدرية مفقودة، ولا يجيز هذا التقرير تنفيذ P006 أو ترتيب سيناريوهات.

المنهجية 11 / منتجو الرفض 7 / منتجو وشهادات العائلة 0/0؛ تجميد Flat/Triangle وقاعدة SOURCE_DERIVED_BASE_CASE_NOT_FOUND وlegacy analyze غير المنفذ لم تتغير. هذا تقرير فرضيات جزئية، لا مخرَج عدّ مكتمل ولا موافقة مدير مشروع.''')
    artifact={'surface':'report','manifest':manifest,'snapshot':{'version':1,'generatedAt':now,'status':'ready','datasets':datasets},
              'sources':manifest['sources'],'package_info':{'delivery_mode':'html','audience':'product stakeholders','language':'ar'}}
    save('artifact.json',artifact);save('chart_rows.json',datasets)
    if not output.resolve().is_relative_to(old.ROOT):raise ValueError('Runtime only')
    report_path=(output/'report.md').resolve()
    if not report_path.is_relative_to(output.resolve()):raise ValueError('Escaping report output')
    with report_path.open('w',encoding='utf-8',newline='\n') as f:f.write('\n\n'.join(parts)+'\n')
    save('export_audit.json',{'reconciliation':audit,'paths':len(paths),'plotted_hypotheses':chosen,
        'chart_rows':{k:len(v) for k,v in datasets.items()},'indicator_values_checked':len(indicators),
        'chart_contract':'Native scatter with original closes and labels; each chart asks time/price with exact endpoint lookup. Log axis is display only, no measurement change. Each close series extends to saved last bar.',
        'report_structure':'Arabic user-requested title/summary; findings, evidence, questions and caveats; native chart semantic tables; Find aliases, no unsupported clickable tree.',
        'indicators':'Separate saved Daily study capture, no methodology interpretation'})
    print({'audit':audit,'paths':len(paths),'charts':len(datasets)},flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=task.PACK)
    build(parser.parse_args().output)
