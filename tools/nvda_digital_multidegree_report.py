"""Offline reporting only: reconcile frozen evidence, then emit canonical report data.

No inference, certification, capture or methodology evaluation occurs here.
"""
from collections import Counter
import argparse
from datetime import datetime, timezone
from fractions import Fraction
import json
import math
import sqlite3
from pathlib import Path

import nvda_digital_multidegree as run


def indicator_rows(raw, summary):
    """Check each saved summary against the original study at its exact timestamp."""
    mapping={'Volume':('Volume',1),'RSI':('Relative Strength Index',1),
             'Histogram':('MACD',1),'MACD':('MACD',2),'Signal':('MACD',3)}
    studies={s['name']:s for s in raw['studies']}
    checked=[]
    for row in summary['rows']:
        name,column=mapping[row['indicator']]
        timestamp=datetime.fromisoformat(row['bar_time']).timestamp()
        values=next(r['value'] for r in studies[name]['rows'] if r['value'][0]==timestamp)
        if values[column]!=row['value'] or row['capture']!=raw['captured_at_utc']:
            raise ValueError('Indicator snapshot/value mismatch')
        checked.append(dict(row,study=name,plot_column=column,
                            price_snapshot_comparable=False,interpretation='OBSERVATION_ONLY'))
    return checked


def canonical(doc,snapshots):
    """Reconcile duplicated display fields and prevent export-only authority changes."""
    run.audit_hierarchy(doc,snapshots)
    nodes={n['node_id']:n for n in doc['nodes']}
    for row in doc['hypotheses']:
        node=nodes[row['display_id']]
        if node['hypothesis_id']!=row['hypothesis_id'] or node['parent_id']!=row['parent_node_id']:
            raise ValueError('Hypothesis identity/link mismatch')
        if node['evaluations']!={'p004':row['p004'],'p005':row['p005']}:
            raise ValueError('Result/display mismatch')
        for i in range(5):
            child=nodes[row['display_id']+'.'+str(i+1)]
            if (child['start'],child['end'])!=tuple(row['endpoints'][2*i:2*i+2]):
                raise ValueError('Role/table endpoint mismatch')
            if child['parent_id']!=row['display_id'] or child['hypothesis_id']!=row['hypothesis_id']:
                raise ValueError('Foreign displayed role')
        if row['current_position']['engine']!='CURRENT_WAVE_POSITION_UNRESOLVED' or row['current_position']['completion_authority']:
            raise ValueError('False current/completion authority')
        if row['current_position']['developing_endpoint']!=(row['endpoints'][-1]['pivot_state']=='DEVELOPING'):
            raise ValueError('Forming state hidden')
    totals={k:dict(Counter(r[k]['status'] for r in doc['hypotheses'])) for k in ('p004','p005')}
    totals['p004_rejected_despite_p005']=sum(r['p004']['fatal'] and r['p005']['status']=='SUFFICIENT_CONDITION_ESTABLISHED' for r in doc['hypotheses'])
    if totals!=doc['totals'] or doc['inventories']!=[11,7,0,0] or doc['scenario_ranking'] is not None:
        raise ValueError('Totals/authority mismatch')
    return doc


def wave_table(doc):
    return [{'node_id':n['node_id'],'parent_id':n['parent_id'],'role':n['proposed_role'],
             'resolution':n['resolution'],'relative_degree':n['relative_degree'],'status':n['status'],
             'start':n['start']['timestamp_utc'],'start_field':n['start']['price_field'],'start_price':n['start']['price'],
             'end':n['end']['timestamp_utc'],'end_field':n['end']['price_field'],'end_price':n['end']['price'],
             'source_hash':n['start']['source_hash'],'unresolved':n['unresolved'],
             'source_refs':['P004','P005_POLICY','RECURSION']} for n in doc['nodes']]


def mdtable(headers, rows):
    def cell(v):return str(v).replace('|','/').replace('\n',' ')
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(cell(v) for v in r)+' |' for r in rows)


def chart_data(snapshot, hypothesis=None):
    """A real SQLite projection; plot transform is display-only, operands unchanged."""
    obs=snapshot.observations
    bars=obs.bars
    if hypothesis:
        start=hypothesis['endpoints'][0]['timestamp_utc'];end=hypothesis['endpoints'][-1]['timestamp_utc']
        bars=tuple(b for b in bars if start<=b.timestamp_utc.isoformat()<=end)
    source=[]
    for b in bars:
        source.append({'time':b.timestamp_utc.isoformat(),'price':b.close,'label':'','kind':'close','field':'close'})
    if hypothesis:
        endpoints=[hypothesis['endpoints'][0]]+hypothesis['endpoints'][1::2]
        for i,e in enumerate(endpoints):
            source.append({'time':e['timestamp_utc'],'price':e['price'],'label':str(i),'kind':'proposed endpoint','field':e['price_field']})
    db=sqlite3.connect(':memory:');db.row_factory=sqlite3.Row
    db.execute('CREATE TABLE evidence(time TEXT, price REAL, label TEXT, kind TEXT, field TEXT)')
    db.executemany('INSERT INTO evidence VALUES(:time,:price,:label,:kind,:field)',source)
    sql="SELECT time, price, label, kind, field FROM evidence ORDER BY time, kind"
    rows=[dict(r) for r in db.execute(sql)];db.close()
    for row in rows:
        t=datetime.fromisoformat(row['time']);a=datetime(t.year,1,1,tzinfo=timezone.utc);b=datetime(t.year+1,1,1,tzinfo=timezone.utc)
        row['year']=t.year+(t-a).total_seconds()/(b-a).total_seconds()
        row['display_log10_usd']=math.log10(row['price'])
        row['source_hash']=obs.provenance.source_sha256
    return rows,sql


def build(output=None):
    pack=Path(output or run.PACK).resolve()
    if not pack.is_relative_to(run.ROOT):raise ValueError('Runtime output only')
    snapshots,_=run.tv.load_inputs()
    doc=canonical(run.read(run.PACK/'resolution_expanded/hierarchy.json'),snapshots)
    raw=run.read(run.PREVIOUS/'indicators_1D_verified.json')
    indicators=indicator_rows(raw,run.read(run.PREVIOUS/'indicator_summary.json'))
    indicator_receipt={'source_sha256':run.hash_file(run.PREVIOUS/'indicators_1D_verified.json'),'rows':indicators,'resolution':'1D','other_resolutions':'UNAVAILABLE','local_indicator_calculation':False}
    def unchanged_or_new(name,value):
        path=pack/name
        if path.exists():
            if run.read(path)!=value:raise ValueError('Existing export differs: '+name)
        else:run.save(path,value)
    unchanged_or_new('indicator_evidence.json',indicator_receipt)
    unchanged_or_new('canonical_hierarchy.json',doc)
    table=wave_table(doc);unchanged_or_new('wave_table.json',table)
    by_id={h['display_id']:h for h in doc['hypotheses']}
    stamp=datetime.now(timezone.utc).isoformat()
    manifest={'version':1,'surface':'report','title':'NVDA — أين يمكن أن نكون؟ فرضيات مترابطة وحدودها',
              'description':'قراءة عربية من بيانات TradingView المحفوظة؛ لا عدّ معتمد ولا توقع سعري',
              'generatedAt':stamp,'cards':[],'charts':[],'tables':[],'sources':[{'id':'evidence','label':'Frozen BATS:NVDA / Cboe One; native snapshots','path':'canonical_hierarchy.json'}],'blocks':[]}
    datasets={};texts=[]
    def prose(id,body):
        manifest['blocks'].append({'id':id,'type':'markdown','body':body});texts.append('<a id="'+id+'"></a>\n\n'+body)
    def chart(id,res,h=None):
        rows,sql=chart_data(snapshots[res],h);datasets[id]=rows
        label='الأسعار الشهرية المتاحة كاملة' if h is None else 'النقاط المقترحة — '+h['display_id']
        manifest['charts'].append({'id':id,'title':label,'subtitle':'النقاط الصغيرة إغلاقات فعلية؛ الأرقام 0–5 نهايات مقترحة وليست عدّاً مثبتاً. محور السعر log10(USD) للعرض فقط؛ الأسعار الأصلية في الجدول والتفاصيل.',
            'type':'scatter','dataset':id,'layout':'full','valueFormat':'number','unit':'display only',
            'encodings':{'x':{'field':'year','type':'quantitative','label':'السنة — موضع زمني دقيق'},'y':{'field':'display_log10_usd','type':'quantitative','label':'log10(USD) — للعرض فقط'},'label':{'field':'label','type':'nominal','label':'الدور المقترح'},'tooltip':[{'field':'time','label':'وقت البار'},{'field':'price','label':'USD الأصلي'},{'field':'field','label':'حقل السعر'},{'field':'kind','label':'نوع الملاحظة'}]},
            'labels':{'values':'all'},'settings':{'showPoints':'always'},
            'source':{'id':id+'-sql','label':'Frozen exact observations + genuine bound endpoints','path':'chart_rows.json','query':{'engine':'SQLite (in-memory)','language':'sql','sql':sql,'tables_used':['evidence'],'description':'Rows from exact canonical role endpoints and saved close observations. Python adds fractional UTC year and log10 for display only; no methodology arithmetic uses this display transform.'}}})
        manifest['blocks'].append({'id':id+'-block','type':'chart','chartId':id,'layout':'full'})
        texts.append('[الرسم التفاعلي '+id+'](report.html#'+id+')')
    prose('summary','''# NVDA — فرضيتان واسعتان، ولا موضع موجي نشط مثبت

## Executive Summary — الخلاصة

**أين قد نكون عند آخر لقطة؟** إذا كانت نهاية مايو 2026 هي نهاية الجزء الصاعد المقترح منذ أكتوبر 2022، فالسعر الأخير يقع في حركة لاحقة لذلك الجزء، لم تُحسم عائلتها. وإذا كان هذا الجزء لا يزال مفتوحاً، فقد تقع مشاهدات سبتمبر داخل امتداد الدور الخامس المقترح. هاتان قراءتان شرطيتان M1 وM2، بلا ترتيب؛ لا تثبت اللقطة أيّاً منهما ولا أن آخر قمة هي نهاية موجة.

آخر قيمة يومية محفوظة هي **229.56 دولار في بار 8 سبتمبر 2026، وقت التقاط 13:49:15 UTC**، لا إغلاق جلسة ولا سعر حيّ الآن. النتيجة الآلية في الحالتين **CURRENT_WAVE_POSITION_UNRESOLVED**. اختيار 234.76 كقمة البار الشهري الجاري في M2 لا يعني أن 229.56 ينتمي حتماً إلى موجة نشطة محددة.

فُحص كامل التاريخ الشهري المتاح هندسياً: 333 باراً منذ يناير 1999. نُفّذت 25 فرضية جزئية، منها 11 مرفوضة بـP004؛ 7 منها تحقق شرط P005 الكافي لكنه لا ينقذها. وصل الربط الفعلي إلى مستويين من الأبناء، لا إلى إثبات تقسيمات كل التاريخ. النهايات المرصودة دقيقة رقمياً؛ معانيها الموجية تبقى مقترحة.

[التغطية](#coverage) · [M1](#M1) · [M2](#M2) · [الفروع والرفض](#branches) · [السياق الحديث والمؤشرات](#recent) · [كل الفرضيات](#index)

استخدام: افتح أحد السيناريوهين، اقرأ جدول الأدوار، ثم اضغط رابط الابن تحت الدور المناسب. لا تجمع طفلين بديلين في مسار واحد. الأرقام أدوار فرضية وليست موجات مؤكدة؛ مستوى التنقل ليس درجة إليوت.''')
    prose('coverage','''## تاريخ الأسعار أوسع من تاريخ التقسيمات المفحوصة

التغذية الفعلية **BATS:NVDA / Cboe One**؛ NASDAQ:NVDA معرّف الإدراج فقط. الجلسة العادية 09:30–16:00 America/New_York، عرض الوقت UTC، العملة USD. اللقطات بين 13:49 و13:54 UTC يوم 8 سبتمبر 2026 وليست متزامنة. كل بار أخير جزئي. تعديل التوزيعات مغلق، back-adjustment مفعّل، ودلالة تعديل الانقسامات غير متحققة. لا Yahoo ولا إعادة تجميع.

تاريخ البار الشهري/الأسبوعي **تسمية للبار** وليس اليوم الذي حدثت فيه قمته أو قاعه. تاريخ يناير 1999 بداية بيانات، لا أصل موجة. لذلك لا نفرض مساواة نهاية شهرية مع يوم داخل الشهر، ولا نمد نافذة ابن عبر حدودها لمجرد تطابق السعر.''')
    coverage=doc['data_quality']['datasets']
    prose('coverage-table',mdtable(['الإطار','العدد','أول بار','آخر بار','التقاط'],[[key,r['bars'],r['first_bar_start'],r['last_bar_start'],r['capture_end']] for key,r in coverage.items()]))
    chart('full-history','1M')
    prose('search','''## كيف اختُبرت الصورة الكبيرة؟

قبل التقييم حُددت نافذتا هندسة بعرض 2 و8 بارات، وثلاث مناطق 1999–2007 و2008–2016 و2017–2026. فُحصت كل النوافذ المتتالية من ست نقاط: 66 نافذة في العرض 2 و15 في العرض 8؛ اختير أول وآخر تسلسل مؤهل في كل منطقة، لا أفضل نتيجة P004/P005. أضيف اقتراحان واسعان من مناطق معلنة مسبقاً. هذه سياسة بحث هندسية وليست قاعدة إليوت ولا بحثاً شاملاً في جميع المجموعات.

الحدود: 12 جذراً إقليمياً كحد أقصى، 64 فرضية، 24 بحث مكوّن، أول/آخر تسلسل مؤهل فقط لكل مكوّن، ومستوى أقصى مخطط 5. المنفّذ: 7 جذور إقليمية وM1/M2، و16 فرضية ابن؛ عمق فعلي 2. بقيت 38 نافذة شهرية مؤهلة غير مزارة في العرض 2. الست نقاط لا تثبت دافعاً خماسياً. لا أصل آلياً عند الاكتتاب ولا استدلال للدرجة من الإطار.

الفرضيات الإقليمية المقبولة في نطاق P004 ليست قطعاً نلصقها في عدّ مستمر. الفجوات، والنقاط المحذوفة ضمن اقتراح M1/M2، تبقى غير محسومة.''')
    for id in ('M1','M2'):
        h=by_id[id]
        text=('''## M1 — نهاية مقترحة في مايو، ثم حركة لاحقة غير مصنفة

البناء الواسع يقترح الأدوار 1 إلى قمة 2007، و2 إلى نقطة نوفمبر 2009، و3 إلى نوفمبر 2021، و4 إلى أكتوبر 2022، و5 إلى قمة البار الشهري مايو 2026 عند 236.54. اجتاز فقط P004 وحقق كفاية P005؛ لا يثبت ذلك الدافع أو اكتماله.

شرطياً، إذا صحّت نهاية الجزء في مايو، فحركة يوليو–سبتمبر تقع **خارج الجزء المغلق افتراضياً**، ضمن بنية لاحقة غير مصنفة. لا نسميها ABC أو موجة أولى جديدة. غياب إثبات عائلة الجزء السابق ونهايته قد يغيّر هذه القراءة.

قمة 236.54 مسجلة يومياً في 14 مايو، لكن وقت نهايتها الشهرية هو تسمية بار 1 مايو. هذا التعارض الزمني في دقة النهاية يمنع ربط ذلك اليوم كابن يتجاوز نافذة الأب الحالية؛ لم نمد النافذة أو نستبدلها سراً.'''
              if id=='M1' else '''## M2 — خامسة واسعة ما زالت مقترحة، لا «موجة نشطة» مؤكدة

يحتفظ M2 بالأدوار 1–4 نفسها ويترك نهاية الدور 5 عند القمة الهندسية للبار الشهري الجاري في سبتمبر: 234.76. لذلك P005 **غير محسوم بسبب أهلية النهاية المتكوّنة**؛ P004 لا يرفض الفرضية وحده.

شرطياً، قد تكون مشاهدات سبتمبر داخل استمرار الجزء المقترح منذ أكتوبر 2022؛ لكن القمة المختارة أدنى من قمة مايو 236.54، ولا نقرر من ذلك بتر الخامسة أو اكتمالها أو عائلة الحركة. السعر الأخير لا يكفي لتمييز استمرار هذا الدور عن حركة لاحقة كما في M1. البيانات اليومية تؤكد وجود قمم وقيعان داخل الفترة، لا معنى موجياً حاسماً لها.''')
        prose(id,text+'''

**حد مشترك مهم:** نقطة 2009 اختيرت من نافذة عام 2009 المحددة مسبقاً، وهي قاع هندسي محلي في نوفمبر عند 0.289، لا ادعاء بأنها أدنى سعر لأزمة 2008–2009. الأجزاء المحذوفة غير مثبتة؛ هذا يضعف شمول الاقتراح ولا نصلحه بإعادة اختيار لاحقة للنتائج. مرجعية اقتراح الأدوار: تعريف الدافع الخماسي في المصدر، مع بقاء P006 والداخليات مجمدة/غير مثبتة.''')
        chart('plot-'+id,'1M',h)
        roles=[r for r in table if r['parent_id']==id]
        prose(id+'-table',mdtable(['الدور','وقت البداية UTC','حقل/سعر','وقت النهاية UTC','حقل/سعر'],[[f"[{r['role']}](#{r['node_id']})",r['start'],f"{r['start_field']} {r['start_price']!r}",r['end'],f"{r['end_field']} {r['end_price']!r}"] for r in roles]))
    prose('branches','''## أبناء حقيقيون، لكنهم لا يغطون كل مكوّن الأب

توجد روابط شهرية → أسبوعية، ثم أسبوعية → 4 ساعات في فرع أواخر 2025. الإطار اليومي في نوافذ الأدوار الأخيرة المنتقاة أعطى 2 أو 5 أو 4 محاور فقط، دون ست نقاط مؤهلة؛ جُرّب نفس دور الأب على دقة أدق وفق خطة إعادة منفصلة، دون اختراع أب يومي أو درجة جديدة.

في الدور الخامس الأسبوعي من 24 نوفمبر إلى 15 ديسمبر 2025، يوجد اقتراح 4H من 25 نوفمبر إلى 8 ديسمبر: 169.555 → 182.91 → 173.68 → 185.65 → 179.12 → 188.0، غير مرفوض بـP004 وحقق كفاية P005. لا يغطي هذا الابن بداية الأب ونهايته بالكامل؛ لا يصح اعتباره تقسيمه الكامل.

الاقتراح الزمني التالي 26 نوفمبر–12 ديسمبر يُرفض بـP004 رغم كفاية P005؛ فتتوقف سلسلة ذلك الابن وحده. لا يؤدي رفضه إلى إثبات البديل السابق أو رفض الأب لمجرد نقص البحث. الروابط المتطابقة إحداثياً تحت M1 وM2 محفوظة كسياقين، لا كتأكيدين مستقلين.''')
    detail='M1.5:L1:O0:S2.5:L2:O2:S1'
    if detail in by_id:chart('linked-4h','240',by_id[detail])
    search_counts=dict(Counter(s['reason'] for s in doc['searches']))
    prose('stops',mdtable(['حالة سياق البحث','عدد السياقات'],list(search_counts.items()))+'''

هذه سياقات متكررة عبر البدائل، لا موجات فريدة. عشر نوافذ بلا تغطية أدق، وست بنقاط غير كافية، وسياقان لم يُزارا لنفاد حد 24 بحثاً. توجد 1H منذ مايو 2025 و15m منذ أبريل 2026 فقط؛ لا يمكنهما إثبات داخليات 2007 أو 2021. لا تعني هذه الحدود استحالة العائلة.''')
    prose('recent','''## الجزء الحديث: ما الذي يمكن قوله دون اختلاق نسب؟

البيانات اليومية تضبط مناطق الاهتمام: 7 أبريل 2025 low=86.62، 29 أكتوبر 2025 high=212.1899، 30 مارس 2026 low=164.27، 14 مايو high=236.54، و29 يوليو low=190.01. هذه نهايات مناطق مرصودة، لا نهايات أرثوذكسية معتمدة. السيناريوهان القديمان L1/L2، وكذلك A/B، لم يُستعملا كحقيقة أو كأب جاهز؛ لم يثبت البحث الحالي سلسلة نسبهما التفصيلية. تبقى قراءة «جزء انتهى في مايو» مقابل «جزء مستمر» مشروطة، وليست مجرد إعادة تسمية عدّ قديم.

ما يميز فعلياً الآن هو رفض P004 للفرضية الدقيقة وبعض كفاية P005؛ لا توجد عائلة نهائية مثبتة، ولا P006 تنفيذي، ولا حق في استنتاج صلاحية عائلة من فشل أخرى. لا نعين موجة نشطة من آخر رقم مرسوم.

المؤشرات المحفوظة التالية من **لقطة يومية لاحقة 14:01:42 UTC**، منفصلة عن لقطة الأسعار 13:49. لا نخلط قيمة البار الجاري بينهما. RSI وMACD والحجم هنا مشاهدات فقط؛ لا تأكيد موجي ولا تباعد مستنتج ولا هدف سعري. الأطر الأخرى بلا مؤشر محفوظ موثّق في هذه الحزمة؛ EWO محذوف.''')
    prose('indicators',mdtable(['المؤشر','وقت البار','القيمة الأصلية','جارٍ'],[[r['indicator'],r['bar_time'],repr(r['value']),r['forming']] for r in indicators]))
    prose('index','## فهرس الفرضيات — لا ترتيب أفضلية\n\n'+mdtable(['الفرضية','الأب','الدقة','P004','P005'],[[f"[{h['display_id']}](#{h['display_id']}-details)",h['parent_node_id'] or 'جذر مستقل',h['timeframe'],h['p004']['status'],h['p005']['status']] for h in doc['hypotheses']]))
    for h in doc['hypotheses']:
        id=h['display_id'];childlinks=[r for r in doc['hypotheses'] if r['parent_node_id'] and r['parent_node_id'].rsplit('.',1)[0]==id]
        prose(id+'-details','### '+id+' — '+('مرفوض؛ ليس سيناريو ناجياً' if h['p004']['fatal'] else 'فرضية جزئية؛ داخليات غير محسومة')+'\n\n'+
              ('[الأب](#'+h['parent_node_id']+') · ' if h['parent_node_id'] else '')+'[الفهرس](#index)\n\n'+
              'P004: '+h['p004']['status']+'؛ P005: '+h['p005']['status']+'. أسباب النقص الدقيقة: '+', '.join(h['unresolved_reasons'])+'\n\n'+
              mdtable(['الدور','بداية UTC','السعر/الحقل','نهاية UTC','السعر/الحقل','أبناء مرتبطون'],[[f"[{r['role']}](#{r['node_id']})",r['start'],str(r['start_price'])+' '+r['start_field'],r['end'],str(r['end_price'])+' '+r['end_field'],' · '.join(f"[{c['display_id']}](#{c['display_id']}-details)" for c in childlinks if c['parent_node_id']==r['node_id']) or 'لا ابن مفحوص'] for r in table if r['parent_id']==id]))
        for role in (r for r in table if r['parent_id']==id):
            prose(role['node_id'],'#### '+role['node_id']+'\n\n[الفرضية](#'+id+'-details) · '+' · '.join(f"[{c['display_id']}](#{c['display_id']}-details)" for c in childlinks if c['parent_node_id']==role['node_id'])+'\n\nالحالة: '+role['status']+'؛ لا تقييم مستقل لهذا الدور ولا درجة زمنية مستنتجة.')
    prose('sources','''## منهجية وحدود النتيجة

المصدر الحاكم: Brain_LOCKED وفق SOURCE_POLICY المعتمد. تعريف الدافع ذي خمسة أدوار لا يثبت داخليات أي اقتراح. P004 قاعدة مصدرية تخص أصل 1 وتراجع 2 للفرضية الدقيقة؛ P005 هو شرط كفاية نسبي فقط بموجب سياسة الكتاب واتفاق القياس المعتمد، لا حكم سلبي ولا إنقاذ لرفض P004. P006 ما زال مجمداً متعارضاً؛ تجميد Flat/Triangle وباقي حدود العائلة باقية.

مراجع دقيقة: Volume_01.srt 00:29:45.679–00:31:41.909 (P004/بنية الدافع، SOURCE_RULE/تعريف بنيوي منفصل)؛ كتاب Frost/Prechter، صفحات PDF المرجعية 31–33 وفق مراجعة المصدر السابقة (تعريف الدافع وسياق الامتداد، لا اختيار آلي للنهاية)؛ Volume_08.srt 00:04:47.070–00:06:37.050 (توجيه من الأعلى للأسفل، SOURCE_GUIDELINE)؛ MASTER_PROTOCOL وDEGREE_RECURSION_BRAIN (فصل الدرجة عن الإطار وتفكيك الداخليات)؛ SOURCE_POLICY لقواعد P005 ومقارنتها المعتمدة. تُحفظ المراجع ومساراتها وهاشاتها في source_refs.json.

لا منتج لعائلة معتمدة ولا إصدار: 0/0. الحد التشغيلي/النهاية المرئية ليس قاعدة نهائية لإليوت. لا ترتيب ولا ثقة رقمية ولا إشارة تداول. المطلوب لحسم القراءة أضيق من «مزيد من الصور»: سلطة نهاية/فترة البار التي تسمح بربط التطرف الشهري بيومه دون تغيير الأب، ثم داخليات داعمة؛ البحث الناقص لا يعوض تلك السلطة. لا يبدأ التقرير مرحلة جديدة ولا يفتح P006.''')
    artifact={'surface':'report','manifest':manifest,'snapshot':{'version':1,'generatedAt':stamp,'status':'ready','datasets':datasets},'sources':manifest['sources'],'package_info':{'audience':'product stakeholders','delivery_mode':'html','source_lock':True,'language':'ar'}}
    run.save(pack/'chart_rows.json',datasets);run.save(pack/'artifact.json',artifact)
    run.save(pack/'coverage.json',{'datasets':coverage,'search_counts':search_counts,'max_actual_child_depth':doc['audit']['max_executed_child_level'],'planned_child_depth':5,'exhaustive':False,'monthly_coverage':[{k:v for k,v in r.items() if k!='pivots'} for r in run.read(run.PACK/'resolution_expanded/planned_search.json')['coverage']]})
    with (pack/'report.md').open('x',encoding='utf-8',newline='\n') as f:f.write('\n\n'.join(texts)+'\n')
    run.save(pack/'export_audit.json',{'result':'PASS','canonical':doc['audit'],'indicator_values_reconciled':len(indicators),'chart_rows':{k:len(v) for k,v in datasets.items()},'total_hypotheses':len(doc['hypotheses']),'wave_rows':len(table),'source_snapshots_mixed':False,'rendering_authority':False})
    print(json.dumps({'hypotheses':len(doc['hypotheses']),'nodes':len(table),'charts':len(datasets),'indicator_rows':len(indicators)}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,help='New Runtime directory; approved artifacts are never overwritten')
    build(parser.parse_args().output)
