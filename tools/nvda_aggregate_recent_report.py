"""Arabic report and independent raw-row reconciliation; no new analysis rules."""
from collections import Counter
from datetime import datetime,timezone
from fractions import Fraction
from pathlib import Path
import argparse
import sqlite3

import nvda_aggregate_recent as task
import nvda_digital_multidegree_report as display
old=task.old


def reconcile(doc,snapshots,raw):
    display.canonical(doc,snapshots)
    sources={s.observations.provenance.source_sha256:{r['value'][0]:r['value'] for r in raw[k]['rows']} for k,s in snapshots.items()}
    fields={'open':1,'high':2,'low':3,'close':4}
    def check(source,time,field,price):
        if sources[source][datetime.fromisoformat(time).timestamp()][fields[field]]!=price:raise ValueError('Raw source price/time mismatch')
    evidence={e['evidence_id']:e for e in doc['occurrence_evidence']};n=0
    for e in evidence.values():
        check(e['aggregate_source_hash'],e['original_bar_timestamp'],e['price_field'],e['original_price']);n+=1
        times=[]
        for o in e['occurrences']:
            check(o['source_hash'],o['bar_timestamp'],o['price_field'],o['price']);n+=1
            if o['price']!=e['original_price'] or o['price_field']!=e['price_field'] or o['exact_extremum_instant'] is not None or o['orthodox_endpoint']:
                raise ValueError('Occurrence match/authority altered')
            if not e['interval_evidence'][0]<=o['occurrence_envelope'][0]<o['occurrence_envelope'][1]<=e['interval_evidence'][1]:
                raise ValueError('Occurrence outside supported envelope')
            times.append(o['bar_timestamp'])
        if times!=sorted(set(times)):raise ValueError('Duplicated/reordered occurrence rows')
        # Independent raw-row census for this saved native-session experiment.
        # The capture has no interval-crossing rows in these supported windows.
        lo,hi=e['interval_evidence'][:2]
        expected=[datetime.fromtimestamp(t,timezone.utc).isoformat()
                  for t,v in sources[e['finer_source_hash']].items()
                  if lo<=datetime.fromtimestamp(t,timezone.utc).isoformat()<hi
                  and Fraction(v[fields[e['price_field']]])==Fraction(e['original_price'])]
        if times!=sorted(expected):raise ValueError('Saved matching occurrence omitted or invented')
        if e['wave_completion'] or e['family_authority']:raise ValueError('False occurrence authority')
        if e['status']=='UNIQUE_OBSERVED_MATCH' and len(times)!=1:raise ValueError('False uniqueness')
    for h in doc['hypotheses']:
        if h['parent_node_id'] is not None or h['old_parent_id'] is not None or h['attachment']!='OBSERVATIONAL_CONTEXT_ONLY_NO_VALIDATED_PARENT_CHILD_ATTACHMENT':
            raise ValueError('False attachment to old parent')
        for eid in h['context_evidence_ids']:
            if evidence[eid]['finer_source_hash']!=h['endpoints'][0]['source_hash']:raise ValueError('Foreign context snapshot')
        for e in h['endpoints']:check(e['source_hash'],e['timestamp_utc'],e['price_field'],e['price']);n+=1
    return {'result':'PASS','raw_fields_reconciled':n,'hypotheses':len(doc['hypotheses']),'occurrence_records':len(evidence),'old_parent_attachments':0,'family_certificates':0}


def source_plot(snapshot,start,end,field,matches):
    rows=[{'time':b.timestamp_utc.isoformat(),'price':getattr(b,field),'field':field,'label':('MATCH' if b.timestamp_utc.isoformat() in matches else ''),'source_hash':snapshot.observations.provenance.source_sha256} for b in snapshot.observations.bars if start<=b.timestamp_utc.date().isoformat()<end]
    db=sqlite3.connect(':memory:');db.row_factory=sqlite3.Row
    db.execute('CREATE TABLE observations(time TEXT,price REAL,field TEXT,label TEXT,source_hash TEXT)')
    db.executemany('INSERT INTO observations VALUES(:time,:price,:field,:label,:source_hash)',rows)
    sql='SELECT time,price,field,label,source_hash FROM observations ORDER BY time'
    rows=[dict(x) for x in db.execute(sql)];db.close()
    for row in rows:
        t=datetime.fromisoformat(row['time']);row['hour_utc']=t.hour+t.minute/60
    return rows,sql


def build(output=task.PACK):
    output=Path(output);snapshots,raw=old.tv.load_inputs();doc=old.read(task.PACK/'canonical_analysis.json')
    audit=reconcile(doc,snapshots,raw);old.save(output/'independent_reconciliation.json',audit)
    # This narrative describes one frozen experiment, not arbitrary future data.
    if len(doc['hypotheses'])!=25 or doc['totals']['p004']!={'RULE_SATISFIED':11,'RULE_VIOLATED':14} or doc['totals']['p004_rejected_despite_p005']!=11:
        raise ValueError('Frozen narrative counts no longer describe this evidence')
    indicator_rows=display.indicator_rows(old.read(old.PREVIOUS/'indicators_1D_verified.json'),old.read(old.PREVIOUS/'indicator_summary.json'))
    old.save(output/'indicator_evidence.json',{'resolution':'1D','rows':indicator_rows,'source_sha256':old.hash_file(old.PREVIOUS/'indicators_1D_verified.json'),'interpretation':'OBSERVATIONS_ONLY; later indicator snapshot not merged with OHLCV'})
    old.save(output/'wave_table.json',display.wave_table(doc))
    by_id={h['display_id']:h for h in doc['hypotheses']};ev={e['evidence_id']:e for e in doc['occurrence_evidence']}
    now=datetime.now(timezone.utc).isoformat();title='NVDA — توقيت القمم والقيعان وحدود القراءة الحديثة'
    manifest={'version':1,'surface':'report','title':title,'description':'دليل وقوع أدق وفرضيات مستقلة؛ لا عدّ مؤكد ولا تداول','generatedAt':now,'cards':[],'charts':[],'tables':[],
              'sources':[{'id':'evidence','label':'Frozen BATS:NVDA / Cboe One observations and exact scoped evaluation','path':'canonical_analysis.json'}],'blocks':[]}
    datasets={};parts=[]
    def prose(id,body):manifest['blocks'].append({'id':id,'type':'markdown','body':body});parts.append('<a id="'+id+'"></a>\n\n'+body)
    def plot(id,rows,sql,title,subtitle,x,y,reference=None):
        datasets[id]=rows
        chart={'id':id,'title':title,'subtitle':subtitle,'type':'scatter','dataset':id,'layout':'full','unit':'USD','valueFormat':'number',
               'encodings':{'x':{'field':x,'type':'quantitative','label':'الساعة UTC' if x=='hour_utc' else 'السنة/الوقت'},'y':{'field':y,'type':'quantitative','label':'USD' if y=='price' else 'log10(USD) — عرض فقط'},'label':{'field':'label','type':'nominal','label':'الوقوع المرصود أو الدور المقترح'},'tooltip':[{'field':'time','label':'وقت البار UTC'},{'field':'price','label':'السعر الأصلي'},{'field':'field','label':'حقل السعر'}]},'labels':{'values':'all'},
               'source':{'id':id+'-sql','label':'Exact saved native observation rows; no resampling','path':'chart_rows.json','query':{'engine':'SQLite (in-memory)','language':'sql','sql':sql,'tables_used':['observations' if x=='hour_utc' else 'evidence'],'description':'Original snapshot rows; the plotting time coordinate is display-only. Full values, fields and snapshot hashes retained.'}}}
        if reference is not None:chart['referenceLines']=[{'axis':'y','value':reference,'label':'Daily low; not an intraday match'}]
        manifest['charts'].append(chart);manifest['blocks'].append({'id':id+'-block','type':'chart','chartId':id,'layout':'full'});parts.append('[الرسم: '+title+'](report.html#'+id+')')
    prose('title','# '+title)
    prose('summary','''## Executive Summary — الخلاصة

**أصبح توقيت قمة مايو أدق، لا معناها الموجي.** السعر 236.54 في البار الشهري الموسوم 1 مايو يطابق بار 14 مايو اليومي، ثم بار 15 دقيقة من **19:00 إلى 19:15 UTC**. هذه فترة وقوع مرصودة، لا ثانية التنفيذ ولا نهاية إليوت أرثوذكسية.

**قاع يوليو لم يُحسم لحظياً.** القيمة الشهرية/اليومية 190.01 في 29 يوليو لا تطابق أي low محفوظ في 4H أو 1H أو 15m. لا نستبدلها بـ190.02 ولا نختار «أقرب» سعر؛ سبب الاختلاف غير محسوم.

**أين قد نكون عند اللقطة الأخيرة؟** إذا انتهى الجزء الواسع المقترح في مايو، فالحركة الأخيرة تقع ضمن بنية لاحقة غير مصنفة. وإذا كان M2 مفتوحاً، فقد تظل ضمن استمرار الجزء الصاعد المقترح؛ تحديد قمة سبتمبر في بار 4 سبتمبر 14:15–14:30 لا يثبت اكتماله. آخر لقطة 15m في 8 سبتمبر 13:53:45 تسجل 229.29 داخل بار جارٍ؛ ليست سعراً حياً الآن.

أُعيد تقييم 25 فرضية محلية **بمدخلاتها الجديدة**: 14 مرفوضة بـP004، ومنها 11 تحقق كفاية P005 التي لا تنقذها. بقيت 11 غير مرفوضة بهذا الفحص فقط، وكلها بلا إثبات عائلة أو موضع موجي نشط. الروابط مع M1/M2 سياق أدلة فقط، وليست إلحاقاً معتمداً بأبنائهما.

[دليل التوقيت](#timing) · [قاع يوليو](#july) · [الفرضيات الحديثة](#recent) · [قبل/بعد](#comparison) · [كل النتائج](#all)

اقرأ MATCH كوقوع سعري مرصود داخل بار، و0–5 كأدوار فرضية مستقلة. لا تدمج بدائل الجدول أو تستنتج درجة إليوت من الإطار.''')
    prose('timing','''## قمة مايو انتقلت من شهر إلى فترة 15 دقيقة، دون تغيير الأب

تدرج الدليل محفوظ: الشهر [1 مايو، 1 يونيو) بتوقيت نيويورك → جلسة 14 مايو → بار 4H [17:30،20:00) UTC → بار 1H [18:30،19:30) → بار 15m [19:00،19:15). لم يتغير سعر القمة 236.54؛ لم تُحوّل 19:00 إلى توقيت مؤكد للقمة داخل ذلك الربع ساعة.

الفترة الشهرية مشتقة من التقويم المدني وهوية الإطار 1M، لا من إضافة 30 يوماً أو أخذ البار التالي دون فحص. الجلسة غلاف 09:30–16:00 المعلن، وليست شهادة باكتمال التداول في أيام العطلات أو الإغلاق المبكر. تطابق وحيد في الصفوف المحفوظة لا يستبعد تكراراً في بيانات غير متاحة.

حد M1 القديم ما زال تاريخ البار الشهري 1 مايو. لم نمدّه إلى 14 مايو أو نستبدل نهايته؛ بدلاً من ذلك جرى بحث نوافذ أحدث مستقلة ذات هويات وطلبات P004/P005 جديدة. فحص الشهر على اليومي/اللحظي أصبح ممكناً كدليل وقوع، لا كتعديل نسب موجي.''')
    may=ev['M1:15'];rows,sql=source_plot(snapshots['15'],'2026-05-14','2026-05-15','high',{o['bar_timestamp'] for o in may['occurrences']})
    plot('may-occurrence',rows,sql,'قمم بارات 15 دقيقة — 14 مايو 2026','High لكل بار محفوظ؛ MATCH عند البار المطابق 236.54. محور الوقت هو بداية البار لا اللحظة الدقيقة للقمة.','hour_utc','price')
    prose('evidence-table',display.mdtable(['الدليل','وقت البار الأصلي UTC','السعر/الحقل','الدقة الأدق','كل البارات المطابقة UTC','الحالة'],[[e['evidence_id'],e['original_bar_timestamp'],str(e['original_price'])+' '+e['price_field'],e['finer_resolution'],'; '.join(o['bar_timestamp'] for o in e['occurrences']) or 'لا مطابق محفوظ',e['status']] for e in doc['occurrence_evidence']]))
    prose('coverage-table',display.mdtable(['الدليل','غلاف الفترة UTC [بداية، نهاية)','أساس العضوية','صفوف مفحوصة','قيود التغطية واللقطة'],[[e['evidence_id'],' — '.join(e['interval_evidence'][:2]),e['interval_evidence'][2],e['examined_rows'],'; '.join(e['limitations'])] for e in doc['occurrence_evidence']]))
    prose('july','''## اختلاف يوليو يمنع اختلاق توقيت دقيق للقاع

تطابق low الشهري 190.01 مع low اليومي في 29 يوليو، لكن لا يوجد تطابق حرفي محفوظ على الأطر اللحظية الثلاثة. رسم القيعان التالية يعرض الأسعار الأصلية كما هي؛ الخط عند 190.01 هو مرجع يومي وليس سعراً لحظياً مرصوداً هنا. لا تقريب ولا هامش سماح ولا تحريك للنهاية إلى 190.02.

الهويات والجلسات وإعدادات التعديل المتاحة متوافقة، لكن دلالة تعديل الانقسامات غير متحققة، والالتقاطات ليست متزامنة. قد توجد فروق في بناء/مراجعة السلاسل؛ لا تتوافر سلطة كافية لتحديد السبب أو تصحيح أحد المصدرين من الآخر. لذلك يستمر البحث اللحظي مستقلاً، ولا يثبت أنه يبدأ من قاع يوليو الموجي.''')
    rows,sql=source_plot(snapshots['15'],'2026-07-29','2026-07-30','low',set())
    plot('july-observations',rows,sql,'قيعان بارات 15 دقيقة — 29 يوليو 2026','Low الأصلي؛ المرجع 190.01 من Daily. عدم التطابق لا يثبت غياب صفقة أو استحالة موجة.','hour_utc','price',190.01)
    prose('recent','''## القراءة الحديثة: مثالان غير مرفوضين، وليس عدّاً واحداً متصلاً

الفرضية الساعة **RECENT:60:S44** تقترح سلسلة محلية من 1 سبتمبر 13:30 عند 215.1 إلى 3 سبتمبر 13:30 عند 229.07. P004 لا يرفضها وP005 يثبت شرطه الكافي فقط. فرضية 15m **RECENT:15:S186** تبدأ 3 سبتمبر 19:45 عند 228.32 وتنتهي 4 سبتمبر 19:00 عند 230.71، بالحدود الداخلية المعروضة أدناه؛ لها التقييم الجزئي نفسه، لكنها **ليست ابناً مربوطاً بالفرضية الساعة** لمجرد قرب التوقيت.

إذا كانت هذه البنية الصغيرة قد انتهت، فمشاهدة 8 سبتمبر تأتي بعدها؛ إن لم تكن انتهت فترقيمها قد يتغير. لا تثبت قواعدنا الحالية اكتمالها أو تصحيحاً تابعاً أو بداية موجة جديدة. تظل **CURRENT_WAVE_POSITION_UNRESOLVED**. ولا يُرفض M1 أو M2 كله بسبب رفض فرضية محلية مستقلة.

الفرضيتان اليوميتان المختارتان في نافذة RECENT رُفضتا بـP004؛ هذا رفض لهذين الاختيارين تحديداً، لا لكل السلاسل اليومية أو البدائل غير المزارة. لم ننتقِ الناجين لإخفاء المرفوضين.''')
    h=by_id['RECENT:15:S186'];rows,sql=display.chart_data(snapshots['15'],h)
    plot('recent-proposal',rows,sql,'فرضية 15m مستقلة — 3–4 سبتمبر 2026','الأرقام أدوار 0–5 مقترحة؛ النقاط الأخرى إغلاقات. السعر log10 للعرض فقط، والأسعار الأصلية بالتفاصيل. لا درجة أو عائلة مثبتة.','year','display_log10_usd')
    prose('recent-table',display.mdtable(['الفرضية','الدور','البداية UTC','الحقل/السعر','النهاية UTC','الحقل/السعر'],[[h['display_id'],str(i+1),h['endpoints'][2*i]['timestamp_utc'],str(h['endpoints'][2*i]['price'])+' '+h['endpoints'][2*i]['price_field'],h['endpoints'][2*i+1]['timestamp_utc'],str(h['endpoints'][2*i+1]['price'])+' '+h['endpoints'][2*i+1]['price_field']] for h in (by_id['RECENT:60:S44'],by_id['RECENT:15:S186']) for i in range(5)]))
    prose('comparison','''## قبل/بعد: تحسن قابل للفحص، وحد نسب لم نتجاوزه

في المرحلة السابقة توقفت نوافذ الأب الصارمة عند تسمية البار الشهري، وبلغ الربط الفعلي مستويين في فرع 2025. هذه المرحلة لا تعيد كتابة ذلك التاريخ. الجديد هو 21 سجل دليل وقوع ومقارنة، ثم نوافذ مستقلة تركز على مايو ويوليو وسبتمبر، على Daily و4H و1H و15m.

| المسألة | قبل | بعد |
| --- | --- | --- |
| قمة مايو 236.54 | شهر/يوم معروفان بلا طبقة ربط زمنية | سلسلة وقوع محفوظة إلى [19:00،19:15) يوم 14 مايو |
| قمة سبتمبر 234.76 | بار شهري جارٍ موسوم 1 سبتمبر | وقوع في [14:15،14:30) يوم 4 سبتمبر؛ الشهر يظل جارياً |
| قاع يوليو 190.01 | منطقة يومية مرصودة | مطابق Daily، غير مطابق لحظياً؛ التوقيت الأدق محجوب |
| نافذة M1 الأصلية | نهاية بار 1 مايو | لم تتغير؛ البحث الأدق مستقل وليس ابناً معتمداً |
| بدائل أحدث | قد توقف مسارٌ عند ابن مختار مرفوض | جرى تقييم أول وآخر تسلسل مؤهل في كل نافذة بصورة مستقلة |

الخطة المسبقة: أربع نوافذ × أربعة أطر، عرض هندسي 2، حد 4000 بار لكل نافذة، 20,000 نافذة هندسية إجمالاً و32 فرضية. المنفذ 16 بحثاً، 25 فرضية؛ 575 تسلسلاً خارج المجال الهندسي غير مرفوض منهجياً، و438 مؤهلاً غير مزارة وفق الميزانية. لا تصنيف أهمية ولا ترتيب. لا عودية إضافية أو ادعاء بزيادة عمق الشجرة القديمة.

May على Daily لديه محاور غير كافية؛ May وRECENT على 4H لم ينتجا تسلسلاً في المجال المحدد. ليست هذه أحكام استحالة. كل التفاصيل والاستبعادات محفوظة في canonical_analysis.json.''')
    prose('capture','''## حدود الزمن والتغطية لا تختفي بالمطابقة

المصدر BATS:NVDA / Cboe One، ومعرّف الإدراج NASDAQ:NVDA فقط. البيانات اليومية منذ 1999، 4H منذ يناير 2022، 1H منذ مايو 2025، و15m منذ أبريل 2026. النوافذ الحديثة تقع ضمن التاريخ المحفوظ، لكن لا يوجد تقويم تداول يؤكد كل عطلة/إغلاق مبكر أو كل بار متوقع. جلسة regular فقط؛ USD؛ dividend-adjustment مغلق وback-adjustment مفعّل مع split semantics غير متحققة.

الالتقاطات في 8 سبتمبر 2026 بين 13:49 و13:54 UTC غير متزامنة. Daily يسجل 229.56 في لقطته، و15m يسجل 229.29 لاحقاً؛ لا نجمعهما في «سعر حالي» واحد. آخر البارات جزئية. كذلك قد يكون **المحور الهندسي DEVELOPING بسبب حافة نافذة البحث** حتى لو كان البار تاريخياً؛ هذا ليس ادعاء أن السوق التاريخي ما زال يتداول. P005 يبقى غير محسوم عند غياب أهلية النهاية المطلوبة.

المؤشرات التالية من لقطة Daily اللاحقة 14:01:42 UTC. هي قيم RSI وMACD وحجم أصلية، لا حساب جديد ولا إثبات داخليات أو تباعد أو تأكيد موجي. EWO غير مستخدم.''')
    prose('indicators',display.mdtable(['المؤشر','وقت البار UTC','القيمة','جارٍ'],[[x['indicator'],x['bar_time'],repr(x['value']),x['forming']] for x in indicator_rows]))
    prose('all','## جميع البدائل المقيمة — لا ترتيب أفضلية\n\n'+display.mdtable(['الفرضية','P004','P005','من UTC','إلى UTC'],[[f"[{h['display_id']}](#{h['display_id']})",h['p004']['status'],h['p005']['status'],h['endpoints'][0]['timestamp_utc'],h['endpoints'][-1]['timestamp_utc']] for h in doc['hypotheses']]))
    for h in doc['hypotheses']:
        prose(h['display_id'],'### '+h['display_id']+' — '+('مرفوضة بهذه الهوية' if h['p004']['fatal'] else 'غير مرفوضة بـP004؛ العائلة غير محسومة')+'\n\n[الفهرس](#all)\n\nP005: '+h['p005']['reason']+'؛ السياق: '+', '.join(h['context_evidence_ids'])+'؛ لا إلحاق معتمد بالأب القديم.\n\n'+display.mdtable(['الدور','البداية UTC','سعر/حقل','النهاية UTC','سعر/حقل'],[[str(i+1),h['endpoints'][2*i]['timestamp_utc'],str(h['endpoints'][2*i]['price'])+' '+h['endpoints'][2*i]['price_field'],h['endpoints'][2*i+1]['timestamp_utc'],str(h['endpoints'][2*i+1]['price'])+' '+h['endpoints'][2*i+1]['price_field']] for i in range(5)]))
    prose('limits','''## ما بقي مطلوباً لحسم القراءة؟

تحديد بار وقوع السعر لا يحوّله إلى نهاية موجة أرثوذكسية، ولا يسمح بتبديل حدود فرضية صادرة. الرابط الحالي بين دليل الشهر والفرضية الأدق هو **سياق ملاحظة**؛ تحويله إلى علاقة أصل/ابن معتمدة يحتاج عقداً مستقلاً يحدد سلطة فترة النهاية، ويظل غير مطبق هنا.

P004 قاعدة مصدرية تُرفض بها الفرضية الدقيقة؛ P005 كفاية نسبية فقط وفق SOURCE_POLICY واتفاق القياس المعتمد. المصدر: PATTERN_BRAIN قسم Normal impulse، SOURCE_POLICY قسم P005 المعتمد، DEGREE_RECURSION_BRAIN §§2 و5–6 لفصل الإطار عن الدرجة والداخليات غير المحسومة؛ ومراجع المصدر المعتمدة في الحزمة السابقة. لا تعديل لهذه القواعد أو لتجميد P006 وFlat/Triangle أو لغياب القاعدة النهائية.

المطلوب أولاً تفسير الفرق السعري في يوليو بدليل مصدر بيانات، لا بهامش سماح مخترع. وبعد ذلك يظل إثبات الداخل والعائلة والدرجة مسألة منفصلة. لا توصية تداول، لا ترتيب، لا ثقة رقمية، ولا ادعاء بموافقة مدير المشروع.''')
    artifact={'surface':'report','manifest':manifest,'snapshot':{'version':1,'generatedAt':now,'status':'ready','datasets':datasets},'sources':manifest['sources'],'package_info':{'delivery_mode':'html','audience':'product stakeholders','language':'ar'}}
    old.save(output/'artifact.json',artifact);old.save(output/'chart_rows.json',datasets)
    if not output.resolve().is_relative_to(old.ROOT):raise ValueError('Runtime output only')
    with (output/'report.md').open('x',encoding='utf-8',newline='\n') as f:f.write('\n\n'.join(parts)+'\n')
    old.save(output/'export_audit.json',{'raw_evidence':audit,'chart_rows':{k:len(v) for k,v in datasets.items()},'indicator_rows_checked':len(indicator_rows),'new_hypotheses':25,'old_parent_mutations':False,'no_new_family_or_degree_authority':True})
    print({'charts':len(datasets),'hypotheses':len(doc['hypotheses']),'raw_check':audit})


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=task.PACK)
    build(parser.parse_args().output)
