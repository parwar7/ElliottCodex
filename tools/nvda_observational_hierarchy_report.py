"""Reconcile saved observations, then build canonical native offline report data."""
import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

import nvda_observational_hierarchy as task
import nvda_digital_multidegree_report as display
from elliott_runtime.analysis.observational_hierarchy import SUPPORTED, _acyclic
from elliott_runtime.market_data.aggregate_extremum import interval, occurrence_envelope, metadata

old = task.old


def reconcile(doc, snapshots, raw):
    old.audit_hierarchy(doc,snapshots)
    if doc['inventories'] != [11,7,0,0] or doc['validated_families'] or doc['kernel_ancestry_links_added'] or doc['scenario_ranking'] is not None:
        raise ValueError('False methodology/ancestry authority')
    by_hash = {s.observations.provenance.source_sha256:s for s in snapshots.values()}
    source = {s.observations.provenance.source_sha256:{r['value'][0]:r['value'] for r in raw[k]['rows']} for k,s in snapshots.items()}
    fields = {'open':1,'high':2,'low':3,'close':4}; checked = 0
    def price(sha, timestamp, field, value):
        nonlocal checked
        if Fraction(source[sha][datetime.fromisoformat(timestamp).timestamp()][fields[field]]) != Fraction(value):
            raise ValueError('Foreign raw observation value')
        checked += 1
    hyps = {h['display_id']:h for h in doc['hypotheses']}
    nodes = {n['node_id']:n for n in doc['nodes']}
    for h in hyps.values():
        if h['parent_node_id'] is not None:
            raise ValueError('Observation relation inserted into old hierarchy')
        if nodes[h['display_id']]['evaluations'] != {'p004':h['p004'],'p005':h['p005']}:
            raise ValueError('Outcome display changed')
        for i in range(5):
            n = nodes[h['display_id']+'.'+str(i+1)]
            if (n['start'],n['end']) != tuple(h['endpoints'][2*i:2*i+2]):
                raise ValueError('Role display mismatch')
        for e in h['endpoints']:
            price(e['source_hash'],e['timestamp_utc'],e['price_field'],e['price'])
    ev = {e['evidence_id']:e for e in doc['occurrence_evidence']}
    if len(ev) != len(doc['occurrence_evidence']):raise ValueError('Duplicate evidence ID')
    for e in ev.values():
        price(e['aggregate_source_hash'],e['original_bar_timestamp'],e['price_field'],e['original_price'])
        snapshot = by_hash[e['finer_source_hash']]
        aggregate=by_hash[e['aggregate_source_hash']]
        aggregate_bar=next(b for b in aggregate.observations.bars if b.timestamp_utc.isoformat()==e['original_bar_timestamp'])
        if e['interval_evidence']!=old.p.plain(interval(aggregate,aggregate_bar)):
            raise ValueError('Aggregate envelope altered')
        if e['capture_times']!=[metadata(aggregate)['captured_at_utc'],metadata(snapshot)['captured_at_utc']]:
            raise ValueError('Capture context altered')
        if e['wave_completion'] or e['family_authority']:raise ValueError('False occurrence authority')
        expected = []
        if e['interval_evidence'] and e['status'] != 'INCOMPATIBLE_METADATA':
            lo,hi = map(datetime.fromisoformat,e['interval_evidence'][:2])
            for b in snapshot.observations.bars:
                if not lo<=b.timestamp_utc<hi:continue
                envelope = occurrence_envelope(snapshot,b)
                if lo <= b.timestamp_utc < hi and envelope and envelope[1] <= hi and Fraction(getattr(b,e['price_field'])) == Fraction(e['original_price']):
                    expected.append(b.timestamp_utc.isoformat())
        if expected != [o['bar_timestamp'] for o in e['occurrences']]:raise ValueError('Occurrence census lost a tie or invented a match')
        for o in e['occurrences']:
            price(o['source_hash'],o['bar_timestamp'],o['price_field'],o['price'])
            bar = next(b for b in snapshot.observations.bars if b.timestamp_utc.isoformat()==o['bar_timestamp'])
            if old.p.plain(occurrence_envelope(snapshot,bar)) != o['occurrence_envelope'] or o['exact_extremum_instant'] is not None:
                raise ValueError('Occurrence interval became a false instant')
    edges=[]
    for l in doc['links']:
        p,c = hyps[l['parent_alias']],hyps[l['child_alias']]
        a,b = ev[l['start_evidence_id']],ev[l['end_evidence_id']]
        if (l['parent_hypothesis_id'],l['child_hypothesis_id']) != (p['hypothesis_id'],c['hypothesis_id']):raise ValueError('Foreign exported hypothesis')
        if (l['parent_binding_id'],l['child_binding_id'])!=(p['binding_id'],c['binding_id']):raise ValueError('Foreign exported binding')
        for e,ep,side in zip((a,b),p['endpoints'][2*(l['role_number']-1):2*l['role_number']],('start','end')):
            if e['original_parent_hypothesis_id'] != p['hypothesis_id'] or e['original_binding_id'] != l['parent_binding_id'] or e['role_index'] != l['role_number']-1 or e['edge'] != side:
                raise ValueError('Foreign role/binding export')
            if (e['aggregate_source_hash'],e['original_bar_timestamp'],e['price_field'],e['original_price']) != (ep['source_hash'],ep['timestamp_utc'],ep['price_field'],ep['price']):
                raise ValueError('Original aggregate endpoint replaced')
            if e['finer_source_hash'] != c['endpoints'][0]['source_hash']:raise ValueError('Cross-snapshot child leakage')
        if l['parent_subject'] == l['child_subject'] or l['parent_binding_id'] == l['child_binding_id']:
            raise ValueError('Independent subject/binding lost')
        expected_pairs = [(x['bar_timestamp'],y['bar_timestamp']) for x in a['occurrences'] for y in b['occurrences']]
        if expected_pairs != [(x['start_bar'],x['end_bar']) for x in l['pairings']]:raise ValueError('Pairing omitted/reordered')
        cs=by_hash[c['endpoints'][0]['source_hash']]
        ends=[c['endpoints'][0],c['endpoints'][-1]]
        own=[occurrence_envelope(cs,next(b for b in cs.observations.bars if b.timestamp_utc.isoformat()==ep['timestamp_utc'])) for ep in ends]
        for pair in l['pairings']:
            ao=next(o for o in a['occurrences'] if o['bar_timestamp']==pair['start_bar'])
            bo=next(o for o in b['occurrences'] if o['bar_timestamp']==pair['end_bar'])
            av,bv=[tuple(datetime.fromisoformat(v) for v in o['occurrence_envelope'][:2]) for o in (ao,bo)]
            same=[(ep['timestamp_utc'],ep['price_field'])==(o['bar_timestamp'],o['price_field']) for ep,o in zip(ends,(ao,bo))]
            if bv[1]<=av[0]:state='REJECTED_IMPOSSIBLE_ORDER'
            elif av[1]>bv[0] or own[0][1]>own[1][0]:state='UNRESOLVED_OVERLAPPING_INTERVALS'
            elif (same[0] or av[1]<=own[0][0]) and (same[1] or own[1][1]<=bv[0]):
                state='BOUNDARY_SUPPORTED_PROPOSED_REFINEMENT' if all(same) else 'INTERIOR_OBSERVATION'
            elif own[1][1]<=av[0] or own[0][0]>=bv[1]:state='OUTSIDE_SUPPORTED_REGION'
            else:state='UNRESOLVED_BOUNDARY_OVERLAP_OR_CROSSING'
            if (pair['state'],pair['child_start_corresponds'],pair['child_end_corresponds'])!=(state,*same):
                raise ValueError('Pairing state/coverage altered')
        states={p['state'] for p in l['pairings']}
        if states:
            relationship=next(iter(states)) if len(states)==1 else 'AMBIGUOUS_ALTERNATIVE_PAIRINGS'
        elif 'INCOMPATIBLE_METADATA' in (a['status'],b['status']):relationship='INCOMPATIBLE_METADATA'
        elif not a['interval_evidence'] or not b['interval_evidence'] or not all(own):relationship='UNAVAILABLE_INTERVAL_EVIDENCE'
        else:relationship='MISSING_BOUNDARY_EVIDENCE'
        if l['relationship']!=relationship:raise ValueError('Relationship state differs from raw interval evidence')
        rejected = bool(p['p004']['fatal'] or c['p004']['fatal'])
        if rejected != l['p004_rejected'] or l['surviving_observational_link'] != (l['relationship'] in SUPPORTED and not rejected):
            raise ValueError('P004 rejection hidden or P005 rescue')
        if l['complete_subdivision'] or l['kernel_ancestry']:raise ValueError('False link authority')
        expected_style = 'REJECTED' if rejected else 'OBSERVATIONAL' if l['surviving_observational_link'] else 'UNRESOLVED'
        if l['style']!=expected_style:raise ValueError('Link display conceals status')
        edges.append((l['parent_alias'],l['child_alias']))
    _acyclic(edges)
    for k,s in snapshots.items():
        v=doc['input_coverage'][k]
        if v['metadata']!=metadata(s) or v['last_bar_forming'] is not s.last_bar_forming or v['last_bar']!=s.observations.bars[-1].timestamp_utc.isoformat() or v['last_close']!=s.observations.bars[-1].close:
            raise ValueError('Latest/capture snapshot misrepresented')
    totals = {'links':len(doc['links']), 'pairings':sum(len(l['pairings']) for l in doc['links']),
        'relationships':dict(Counter(l['relationship'] for l in doc['links'])),
        'surviving_observational_links':sum(l['surviving_observational_link'] for l in doc['links']),
        'rejected_link_contexts':sum(l['p004_rejected'] for l in doc['links']), 'hypotheses':len(hyps)}
    if totals != doc['totals']:raise ValueError('Totals mismatch')
    return {'result':'PASS','raw_price_fields_checked':checked,'links_checked':len(edges),
            'all_occurrence_pairings_retained':True,'independent_subjects':True,'old_kernel_ancestry_unchanged':True}


def paths(doc):
    """Display traversal only, not recursive Kernel composition or degree."""
    by_id = {h['display_id']:h for h in doc['hypotheses']}
    active = [l for l in doc['links'] if l['surviving_observational_link']]
    result=[]
    def walk(alias, trail):
        for link in active:
            if link['parent_alias']!=alias:continue
            next_trail=trail+[link['link_id']]
            leaf=by_id[link['child_alias']]
            coverage=next(v for v in doc['input_coverage'].values() if v['source_hash']==leaf['endpoints'][-1]['source_hash'])
            result.append({'root':by_id[trail[0].split(':role')[0]]['display_id'] if trail else alias,
                'links':next_trail,'leaf':link['child_alias'],'last_evidenced_endpoint':leaf['endpoints'][-1],
                'latest_snapshot_bar':coverage['last_bar'],
                'reaches_latest_captured_bar':leaf['endpoints'][-1]['timestamp_utc']==coverage['last_bar'],
                'active_wave_authority':False,'type':'PROPOSED_OBSERVATIONAL_PATH_NOT_SUBDIVISION'})
            walk(link['child_alias'],next_trail)
    _acyclic([(l['parent_alias'],l['child_alias']) for l in active])
    for root in ('M1','M2'):walk(root,[])
    return result


def coverage_rows(doc,snapshots):
    hyps={h['display_id']:h for h in doc['hypotheses']}
    evidence={e['evidence_id']:e for e in doc['occurrence_evidence']}
    sources={s.observations.provenance.source_sha256:s for s in snapshots.values()}
    rows=[]
    for link in doc['links']:
        child=hyps[link['child_alias']]; start,end=child['endpoints'][0],child['endpoints'][-1]
        snapshot=sources[start['source_hash']]
        own=[occurrence_envelope(snapshot,next(b for b in snapshot.observations.bars if b.timestamp_utc.isoformat()==ep['timestamp_utc'])) for ep in (start,end)]
        a,b=evidence[link['start_evidence_id']],evidence[link['end_evidence_id']]
        pair_coverage=[]
        for pair in link['pairings']:
            av=next(o['occurrence_envelope'] for o in a['occurrences'] if o['bar_timestamp']==pair['start_bar'])
            bv=next(o['occurrence_envelope'] for o in b['occurrences'] if o['bar_timestamp']==pair['end_bar'])
            supported=pair['state'] in SUPPORTED
            pair_coverage.append({'start_occurrence_bar':pair['start_bar'],'end_occurrence_bar':pair['end_bar'],
                'state':pair['state'],
                'uncovered_before_child': [av[1],own[0][0].isoformat()] if supported and not pair['child_start_corresponds'] else None,
                'uncovered_after_child': [own[1][1].isoformat(),bv[0]] if supported and not pair['child_end_corresponds'] else None,
                'unexamined_internal_structure':True,'intrabar_order_claim':False})
        rows.append({'link_id':link['link_id'],'relationship':link['relationship'],
            'original_start':{k:a[k] for k in ('original_bar_timestamp','original_price','price_field','aggregate_source_hash')},
            'original_end':{k:b[k] for k in ('original_bar_timestamp','original_price','price_field','aggregate_source_hash')},
            'child_start':start,'child_end':end,'pair_coverage':pair_coverage,
            'limitation':'No whole-window subdivision claim; no invented uncovered interval for incompatible/missing/noncontained pairs',
            'missing_boundaries':[side for side,e in (('start',a),('end',b)) if not e['occurrences']]})
    return rows


def build(output=task.PACK):
    output=Path(output); doc=old.read(task.PACK/'canonical_hierarchy.json'); snapshots,raw=old.tv.load_inputs()
    audit=reconcile(doc,snapshots,raw); proposed_paths=paths(doc)
    old.save(output/'raw_reconciliation.json',audit); old.save(output/'proposed_paths.json',proposed_paths)
    coverage=coverage_rows(doc,snapshots);old.save(output/'link_coverage.json',coverage)
    old.save(output/'wave_table.json',display.wave_table(doc))
    indicators=display.indicator_rows(old.read(old.PREVIOUS/'indicators_1D_verified.json'),old.read(old.PREVIOUS/'indicator_summary.json'))
    old.save(output/'indicator_evidence.json',{'rows':indicators,'source_sha256':old.hash_file(old.PREVIOUS/'indicators_1D_verified.json'),'interpretation':'Original later Daily study snapshot only'})
    by_id={h['display_id']:h for h in doc['hypotheses']}; ev={e['evidence_id']:e for e in doc['occurrence_evidence']}
    supported=[l for l in doc['links'] if l['surviving_observational_link']]
    reached=sum(p['reaches_latest_captured_bar'] for p in proposed_paths)
    if reached:raise ValueError('Frozen narrative requires reconsideration: a path now reaches the last captured bar')
    now=datetime.now(timezone.utc).isoformat(); title='NVDA — روابط مقترحة وحدود المسار الحديث'
    manifest={'version':1,'surface':'report','title':title,'description':'روابط ملاحظة لا نسب موجي معتمد','generatedAt':now,
        'cards':[],'charts':[],'tables':[],'sources':[{'id':'hierarchy','label':'Saved BATS:NVDA / Cboe One observations and independent P004/P005 outcomes','path':'canonical_hierarchy.json'}],'blocks':[]}
    datasets={}; parts=[]
    def prose(key,body):
        manifest['blocks'].append({'id':key,'type':'markdown','body':body});parts.append(body)
    def table(key,title,headers,rows):
        prose(key,'### '+title+'\n\n'+display.mdtable(headers,rows))
    def plot(alias,res):
        rows,sql=display.chart_data(snapshots[res],by_id[alias]); key='chart-'+alias.replace(':','-')
        for r in rows:
            if r['label']:r['label']=alias+' / '+r['label']
        datasets[key]=rows
        chart={'id':key,'title':alias+' — أدوار مقترحة من اللقطة '+res,'type':'scatter','dataset':key,'layout':'full',
            'encodings':{'x':{'field':'year','type':'quantitative','label':'وقت البار — عرض مستمر'},
              'y':{'field':'display_log10_usd','type':'quantitative','label':'log10(USD) — عرض فقط'},
              'label':{'field':'label','type':'nominal'},'tooltip':[{'field':'time','label':'وقت البار UTC'}, {'field':'price','label':'السعر الأصلي'}, {'field':'field','label':'الحقل'}]},
            'labels':{'values':'all'},'source':{'id':key+'-source','label':'Original close observations and identity-bound proposed endpoints',
                'path':'chart_rows.json','query':{'engine':'SQLite in-memory','language':'sql','sql':sql,'tables_used':['evidence']}}}
        manifest['charts'].append(chart);manifest['blocks'].append({'id':key+'-block','type':'chart','chartId':key,'layout':'full'})
        parts.append('الرسم الرقمي '+alias+' متاح في report.html؛ بياناته الأصلية في chart_rows.json.')
    prose('title','# '+title)
    prose('summary',f'''## Executive Summary — الخلاصة

**لم نحصل على مسار متصل مدعوم حتى آخر مشاهدة ملتقطة.** أضيفت {len(supported)} روابط ملاحظة غير مرفوضة ضمن {len(doc['links'])} سياق فحص معلن، لكن أياً من المسارات المقترحة المتصلة لا يصل إلى آخر بار في لقطته الأدق. العدد يخص روابط سياقية، لا موجات مستقلة ولا تأكيدات متكررة.

**أصبح بالإمكان عرض أجزاء داخل الدور الخامس المقترح لـM2 دون تغيير نهاياته الأصلية.** الدليل يجمع هوية الدور الشهري ووقوع حدوده في الصفوف الأدق، ثم يحتفظ بكل فرضية أدق وتقييمها المستقل. لا تتحول هذه الوصلات إلى أبناء في عقد النسب الأصلي.

**موضع الموجة النشطة ما زال غير محسوم.** إذا كان الجزء الكبير المفتوح الذي يقترحه M2 هو السياق المناسب، فالفروع المعروضة قد تكون حركات داخله فقط؛ لا يثبت ذلك أنها تقسيمه الكامل أو أن الحركة الأخيرة استمرار له. أما M1 فحده المقترح مرتبط بقمة مايو، ولا نمدّه إلى سبتمبر. الحالة التنفيذية تبقى CURRENT_WAVE_POSITION_UNRESOLVED.

آخر لقطة 15m محفوظة بتاريخ **8 سبتمبر 2026، 13:53:45.992 UTC**، بإغلاق مرصود **229.29** في بار جارٍ؛ ليست سعراً حياً الآن. لم نجمع لقطات الأطر المختلفة في سعر واحد.''')
    prose('meaning','''## كيف تقرأ المسارات دون خلطها بعدّ معتمد؟

**↝ وصلة ملاحظة مدعومة**: تطابق حدود أصلية محفوظة مع بارات أدق، واحتواء مدعوم للفترة المقترحة. **⋯?⋯ وصلة غير محسومة**: حد مفقود أو تداخل توقيت أو بدائل وقوع؛ لا تُستعمل لادعاء مسار مكتمل. **× فرضية مرفوضة بـP004**: تبقى في سجل البدائل وتُستبعد من المسار غير المرفوض، حتى لو ثبت شرط P005 الكافي.

الأرقام 1–5 أدوار مقترحة فقط. اختلاف الإطار والدقة لا يثبت درجة إليوت. الزمن المعروض بجانب السعر هو تسمية البار؛ فترة وقوع القيمة داخله ليست ثانية التنفيذ. لا نجمع مسارين بديلين في تفسير واحد، ولا نعدّ تكرار الإحداثيات في سياقين تأكيدين مستقلين.

للتنقل ابحث عن الاسم القصير مثل JULY:1D:S0 في التقرير، ثم اقرأ جدول الوصلة وجدول الأدوار الخاص به. الروابط التقنية والتفاصيل الكاملة في التصدير؛ لا نعد بانتقال داخلي آلي لم يتحقق اختباره.''')
    table('supported','الوصلات المدعومة رصدياً — غير مثبتة كأبناء', ['المسار المقترح','العلاقة','بداية وقوع حد الأب UTC','نهاية وقوع حد الأب UTC'],
        [[l['parent_alias']+'.'+str(l['role_number'])+' ↝ '+l['child_alias'],l['relationship'],
          '; '.join(' — '.join(o['occurrence_envelope'][:2]) for o in ev[l['start_evidence_id']]['occurrences']),
          '; '.join(' — '.join(o['occurrence_envelope'][:2]) for o in ev[l['end_evidence_id']]['occurrences'])] for l in supported])
    prose('uncovered','''## وصلة الاحتواء الواحدة لا تغطي طرفي الدور الكبير

في M2 ↝ JULY:1D:S0، يقع low=10.813 داخل جلسة 13 أكتوبر 2022، وhigh=234.76 داخل جلسة 4 سبتمبر 2026. أما الفرضية اليومية نفسها فتبدأ 7 يوليو عند low=191.14 وتنتهي 31 يوليو عند high=202.0.

لذلك تترك الوصلة فجوة قبل الطفل من نهاية غلاف جلسة 13 أكتوبر 2022 إلى بداية غلاف جلسة 7 يوليو 2026، وفجوة بعده من نهاية غلاف جلسة 31 يوليو إلى بداية غلاف جلسة 4 سبتمبر. هذه فترات غير مغطاة بهذا الطفل، لا أسماء موجات أو دليل غياب حركة. حتى داخليات يوليو تبقى غير مثبتة. جدول link_coverage.json يحفظ الفترات الدقيقة والبدائل لكل وصلة دون اختلاق فترة تغطية عندما يكون الحد مفقوداً.''')
    prose('macro','''## السياق الشهري لا يزيل الفجوة إلى أحدث حركة

يمتد الدور الخامس المقترح في M1 وM2 من البار الشهري الموسوم 3 أكتوبر 2022، low=10.813. نهاية M1 هي high=236.54 في البار الموسوم 1 مايو 2026؛ نهاية M2 هي high=234.76 في البار الموسوم 1 سبتمبر. لا تعني بداية الشهر أن القمة حدثت في ذلك اليوم.

الرسم التالي يفصل نقاط الدور المقترح عن الإغلاقات الشهرية. نافذة الفرضية ليست كل تاريخ البيانات منذ 1999 ولا تقسيمه النهائي. السلم اللوغاريتمي للعرض فقط، ولا يغير أسعار P004/P005. لا توجد مقارنة أفضلية بين M1 وM2.''')
    plot('M2','1M')
    prose('daily','''## رابط الشهر إلى يوليو لا يحسم الفرع اللحظي

الفرضية اليومية JULY:1D:S0 غير مرفوضة بـP004، لكن داخلياتها غير مثبتة وP005 غير محسوم بسبب أهلية حدود مطلوبة. عرضها داخل المنطقة المدعومة من M2 لا يجعلها تقسيم الدور الخامس كاملاً.

الرسم اليومي التالي يعرض إغلاقات اللقطة اليومية وأدوارها المستقلة. يجب قراءة السعر 190.01 كـlow يومي في 29 يوليو، لا كقيمة تمت مطابقتها في الساعة أو 15 دقيقة. لا تُستبدل هذه النهاية بـ190.02.''')
    plot('JULY:1D:S0','1D')
    selected_missing=[l for l in doc['links'] if l['parent_alias']=='JULY:1D:S0' and l['role_number']==4 and l['child_alias'] in ('MAY_JULY:60:S75','JULY:60:S23')]
    table('missing','الفجوة المحددة في الدور اليومي الرابع',['المسار','الحالة','بداية الحد','نهاية الحد','P004 مستقل','P005 مستقل'],
        [[l['parent_alias']+'.4 ⋯?⋯ '+l['child_alias'],l['relationship'],ev[l['start_evidence_id']]['status'],ev[l['end_evidence_id']]['status'],by_id[l['child_alias']]['p004']['status'],by_id[l['child_alias']]['p005']['status']] for l in selected_missing])
    prose('hourly','''## بداية متطابقة لا تكفي لإكمال الوصلة

الفرضية MAY_JULY:60:S75 مستقلة وغير مرفوضة؛ تبدأ من high=214.39 في 22 يوليو 16:30 UTC وتنتهي عند low=208.74 في 27 يوليو 13:30. قد تمثل حركة داخل الفترة اليومية المقترحة، لكن ربطها المقيد بحدّي الدور غير مكتمل: نهاية الدور اليومي 190.01 بلا مطابق لحظي محفوظ. JULY:60:S23 يكرر الإحداثيات بسياق مستقل؛ نحتفظ به ولا نضاعف قوة الدليل.

الرسم يعرض فرضية الساعة وحدها. لم ننقل نتيجة P005 إليها من الأب، ولم نحول اجتياز الفحص الجزئي إلى شهادة عائلة أو توقيت موجة نشطة.''')
    plot('MAY_JULY:60:S75','60')
    prose('latest','''## المسافة بين آخر دور مرصود وآخر بار تظل فجوة تحليلية

فرضية الساعة RECENT:60:S44 تنتهي في 3 سبتمبر 13:30 عند 229.07. فرضية 15m RECENT:15:S186 تبدأ لاحقاً في 3 سبتمبر 19:45 عند 228.32 وتنتهي في 4 سبتمبر 19:00 عند 230.71. لا تحتوي إحداهما الأخرى زمنياً؛ لا نصنع بينهما وصلة لمجرد قربهما.

الفترة اللاحقة حتى بارات 8 سبتمبر موجودة في البيانات، لكنها ليست امتداداً مثبتاً لآخر دور مرسوم. لا يجوز تسمية البار الجاري «موجة جديدة» أو «تصحيح» بلا الدليل الناقص. كما أن أصل أكتوبر 2022 غير موجود في تاريخ الساعة أو 15m المحفوظ، لذلك تبقى وصلات M2 المباشرة إليها ناقصة الحد الأول، حتى مع وجود تطابق لقمة سبتمبر.''')
    table('reach','نهايات المسارات المتصلة بالفعل',['المسار','آخر فرضية','نهاية الدليل UTC','سعر/حقل','آخر بار في اللقطة الأدق UTC','وصل إليه؟'],
        [[' ↝ '.join(p['links']),p['leaf'],p['last_evidenced_endpoint']['timestamp_utc'],str(p['last_evidenced_endpoint']['price'])+' '+p['last_evidenced_endpoint']['price_field'],p['latest_snapshot_bar'],'نعم' if p['reaches_latest_captured_bar'] else 'لا'] for p in proposed_paths])
    prose('comparison',f'''## قبل/بعد: روابط محددة بدل سياق عام، دون زيادة سلطة المنهجية

في التقرير السابق بقيت الفرضيات الحديثة الـ25 مستقلة دون سجل وصلة محدد بالأب والدور. هنا أُعيد إصدارها بالاختيارات نفسها، مع M1 وM2، وطابقت أسعارها ونتائجها السجل المعتمد. الجديد {len(doc['links'])} سجل وصلة، منها {len(supported)} مدعومة رصدياً وغير مرفوضة. لا بحث جديد ولا التقاط جديد ولا اختيار بناءً على نتيجة P004/P005.

كل بديل وقوع وكل اقتران متاح محفوظ. الحد التشغيلي 160 وصلة و256 اقتراناً لكل وصلة و4096 إجمالاً؛ لا اقتطاع صامت. ما عدا الدور الخامس لـM1/M2 والأدوار الخمسة لـJULY:1D:S0 خارج فحص الربط الحالي. لم نزر بدائل البحث الـ438 المؤجلة في المرحلة السابقة ولم نغير الاستبعادات الهندسية الـ575.

الفرق هندسي/رَصدي فقط: المنهجية 11، منتجو الرفض البنيوي 7، منتجو وشهادات العائلة 0/0. تجميد P006 وFlat/Triangle، وغياب قاعدة نهائية مصدرية، وحالة analyze غير المنفذة لم تتغير.''')
    table('all-links','كل السياقات — لا تخفَ البدائل المرفوضة أو غير المدعومة',['الحالة','الأب/الدور','الفرضية الأدق','العلاقة','دليل البداية','دليل النهاية','اقترانات'],
        [[{'REJECTED':'×','OBSERVATIONAL':'↝','UNRESOLVED':'⋯?⋯'}[l['style']],l['parent_alias']+'.'+str(l['role_number']),l['child_alias'],l['relationship'],l['start_evidence_id'],l['end_evidence_id'],len(l['pairings'])] for l in doc['links']])
    table('boundaries','الحدود الأصلية وفترات وقوعها — لا لحظات مخترعة',['الدليل','بار الأصل UTC','الحقل/السعر','كل فترات الوقوع UTC','الحالة','القيود'],
        [[e['evidence_id'],e['original_bar_timestamp'],str(e['original_price'])+' '+e['price_field'],'; '.join(' — '.join(o['occurrence_envelope'][:2]) for o in e['occurrences']) or 'لا مطابق محفوظ',e['status'],'; '.join(e['limitations'])] for e in doc['occurrence_evidence']])
    for h in doc['hypotheses']:
        table('roles-'+h['display_id'],h['display_id']+' — '+('× مرفوضة بـP004' if h['p004']['fatal'] else 'فرضية غير مرفوضة؛ العائلة غير محسومة'),
            ['الدور','بداية UTC','سعر/حقل','نهاية UTC','سعر/حقل'],[[i+1,h['endpoints'][2*i]['timestamp_utc'],str(h['endpoints'][2*i]['price'])+' '+h['endpoints'][2*i]['price_field'],h['endpoints'][2*i+1]['timestamp_utc'],str(h['endpoints'][2*i+1]['price'])+' '+h['endpoints'][2*i+1]['price_field']] for i in range(5)])
        prose('outcome-'+h['display_id'],'P004: '+h['p004']['status']+'؛ P005: '+h['p005']['status']+' — '+h['p005']['reason'])
    prose('coverage','''## البيانات متاحة بدقات مختلفة، وليست لقطات متزامنة

جميع الأسعار من BATS:NVDA / Cboe One، مع NASDAQ:NVDA كمعرّف إدراج فقط؛ لا Yahoo. جلسة regular 09:30–16:00 نيويورك؛ إطفاء dividend-adjustment وتفعيل back-adjustment لا يحسمان دلالة تعديل الانقسامات. راجع حدود كل لقطة أدناه. بارات النهاية جارية، والتغطية الكاملة للعطل/الإغلاق المبكر غير مثبتة.

قيم المؤشرات أدناه محفوظة من لقطة Daily اللاحقة عند 14:01:42.576 UTC، لا من لقطة الأسعار نفسها. هي ملاحظات RSI/MACD/حجم فقط، بلا تفسير تباعد أو تأكيد موجي أو ترتيب. لا EWO.''')
    table('capture-table','نطاق كل لقطة محفوظة',['الإطار','أول بار UTC','آخر بار UTC','الالتقاط UTC','آخر إغلاق','جارٍ'],
        [[k,v['first_bar'],v['last_bar'],v['metadata']['captured_at_utc'],v['last_close'],v['last_bar_forming']] for k,v in doc['input_coverage'].items()])
    table('indicators','قيم المؤشرات بسياقها الأصلي',['المؤشر','بار UTC','القيمة','الالتقاط UTC','جارٍ'],[[i['indicator'],i['bar_time'],i['value'],i['capture'],i['forming']] for i in indicators])
    prose('limits','''## ما الدليل الناقص تحديداً؟

1. تفسير مصدرِي/بياني لاختلاف 190.01 اليومي و190.02 اللحظي، أو بيانات متوافقة تثبت المطابقة المطلوبة؛ لا هامش سماح.
2. حد بداية مدعوم من أكتوبر 2022 لوصلة مباشرة إلى اللقطات القصيرة، أو مسار وسطي مستقل مدعوم الحدّين؛ لا استبدال تاريخ الأصل.
3. دليل يربط البنية الحديثة بالبارات اللاحقة حتى آخر التقاط، ثم داخليات المصدر اللازمة. وجود البيانات لا يثبت تلك الوصلة.

تحسين نقل الملاحظات عمل هندسي؛ إثبات العائلة والقاعدة النهائية والتجميدات يتطلب سلطة مصدرية منفصلة. لا يقترح هذا التقرير إعادة فتح P006 أو بدء مرحلة جديدة تلقائياً. لا ادعاء بعدّ صحيح أو موافقة مدير المشروع أو إشارة تداول.''')
    artifact={'surface':'report','manifest':manifest,'snapshot':{'version':1,'generatedAt':now,'status':'ready','datasets':datasets},
        'sources':manifest['sources'],'package_info':{'delivery_mode':'html','audience':'product stakeholders','language':'ar'}}
    old.save(output/'artifact.json',artifact); old.save(output/'chart_rows.json',datasets)
    if not output.resolve().is_relative_to(old.ROOT):raise ValueError('Runtime output only')
    with (output/'report.md').open('x',encoding='utf-8',newline='\n') as f:f.write('\n\n'.join(parts)+'\n')
    old.save(output/'export_audit.json',{'raw':audit,'supported_paths':len(proposed_paths),'latest_bar_reached':reached,
        'chart_rows':{k:len(v) for k,v in datasets.items()},'indicator_values_checked':len(indicators),
        'navigation':'Sequential native report and exact alias Find; no unsupported anchor-link claims',
        'visual_styles':{'observational':'↝','unresolved':'⋯?⋯','rejected':'×'}})
    print({'paths':len(proposed_paths),'links':len(supported),'audit':audit})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=task.PACK)
    build(p.parse_args().output)
