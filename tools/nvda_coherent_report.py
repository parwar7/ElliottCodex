"""Evidence-only historical path inspection and Arabic synthesis; no evaluation."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

import nvda_targeted_recent as previous
import nvda_targeted_recent_report as display

old = previous.old
STAGE = 'NVDA-COHERENT-HISTORY-AND-CURRENT-POSITION-REPORT-V1'
PACK = old.ROOT / 'kernel_reviews' / STAGE
PRIOR_HASH = '505f9561943ab942884d0cc6ebbda8d6dfca5cfe8065da246766f66224126400'
BANDS = (('1999', '2002-10'), ('2002-10', '2009-12'),
         ('2009-12', '2022-11'), ('2022-11', '2026-10'))
ALIASES = ('M1', 'M2', 'D2026:1D:N6:S38', 'RECENT:60:N6:S43',
           'TAIL:15:N6:S10', 'H4CONTEXT:240:N4:S31:SINGLE_ZIGZAG',
           'H4CONTEXT:240:N4:S31:FLAT')


def integrity():
    path = previous.PACK / 'REVIEW_manifest.json'
    if old.hash_file(path) != PRIOR_HASH:
        raise ValueError('Prior review changed')
    m = old.read(path)
    for key, root in (('files', previous.PACK), ('implementation_files', old.ROOT)):
        for e in m[key]:
            p = root / e['path']
            if p.stat().st_size != e['bytes'] or old.hash_file(p) != e['sha256']:
                raise ValueError('Prior entry changed: ' + str(p))
    return previous.integrity()


def observed(bar, field, snapshot):
    value = getattr(bar, field)
    return {'bar_label_utc': bar.timestamp_utc.isoformat(), 'field': field,
            'value': value, 'represented_ratio': old.p.plain(Fraction(value)),
            'source_sha256': snapshot.observations.provenance.source_sha256,
            'precision': 'EXACT_REPRESENTED_OBSERVATION_NOT_EXTREMUM_INSTANT'}


def inspect_window(snapshot, start, end, *, inclusive_end=False):
    """Bar-label window extrema, not an Elliott endpoint or path validator."""
    if start >= end:
        raise ValueError('Ordered window required')
    rows = tuple(b for b in snapshot.observations.bars
                 if start <= b.timestamp_utc.isoformat() and
                 (b.timestamp_utc.isoformat() <= end if inclusive_end else
                  b.timestamp_utc.isoformat() < end))
    if not rows:
        return {'window': [start, end], 'bars': 0, 'status': 'NO_OBSERVATIONS',
                'low_occurrences': [], 'high_occurrences': []}
    low = min(b.low for b in rows)
    high = max(b.high for b in rows)
    return {'window': [start, end], 'inclusive_end_bar_label': inclusive_end,
            'bars': len(rows), 'status': 'OBSERVATION_ONLY',
            'first_bar': rows[0].timestamp_utc.isoformat(),
            'last_bar': rows[-1].timestamp_utc.isoformat(),
            'low_occurrences': [observed(b, 'low', snapshot) for b in rows if b.low == low],
            'high_occurrences': [observed(b, 'high', snapshot) for b in rows if b.high == high],
            'endpoint_authority': False, 'methodology_evaluation': None}


def inspect_roots(doc, snapshot):
    result = []
    for alias in ('M1', 'M2'):
        h = next(h for h in doc['hypotheses'] if h['display_id'] == alias)
        if h['source_response_sha256'] != snapshot.observations.provenance.source_sha256:
            raise ValueError('Foreign root snapshot')
        if h['p004']['fatal']:
            raise ValueError('Rejected root cannot support a surviving interpretation')
        # Existing raw reconciliation owns all exact exported binding/price checks.
        for index in range(5):
            a, b = h['endpoints'][2*index:2*index+2]
            window = inspect_window(snapshot, a['timestamp_utc'], b['timestamp_utc'], inclusive_end=True)
            result.append({'hypothesis': alias, 'hypothesis_id': h['hypothesis_id'],
                           'role': index+1, 'original_start': deepcopy(a),
                           'original_end': deepcopy(b), 'observed_window': window,
                           'interpretation': 'NO_RULE_OR_ORTHODOX_ENDPOINT_INFERENCE'})
    return result


def select_cases(doc):
    all_rows = {h['display_id']: h for h in doc['hypotheses'] + doc['corrective_hypotheses']}
    result = []
    for alias in ALIASES:
        h = all_rows[alias]
        if h.get('p004') and h['p004']['fatal']:
            raise ValueError('Rejected selected case')
        result.append(deepcopy(h))
    return result


def build(output=PACK):
    output = Path(output).resolve()
    if not output.is_relative_to(old.ROOT) or output == old.ROOT or (output/'REVIEW_manifest.json').exists():
        raise ValueError('New unsealed Runtime directory required')
    pre = integrity()
    old.save(output/'pre_integrity.json', pre)
    doc = old.read(previous.PACK/'canonical_hierarchy.json')
    snapshots, raw = old.tv.load_inputs()
    receipt = display.reconcile(doc, snapshots, raw)
    roots = inspect_roots(doc, snapshots['1M'])
    bands = [inspect_window(snapshots['1M'], a, b) for a, b in BANDS]
    if sum(x['bars'] for x in bands) != len(snapshots['1M'].observations.bars):
        raise ValueError('Historical bands do not cover the saved Monthly history exactly')
    cases = select_cases(doc)
    links = [deepcopy(l) for l in doc['links'] if l['surviving_observational_link']]
    synthesis = {'stage': STAGE, 'prior_manifest_sha256': PRIOR_HASH,
                 'new_candidate_evaluations': 0, 'historical_bands': bands,
                 'root_path_observations': roots, 'display_cases': cases,
                 'observational_links': links, 'input_coverage': doc['input_coverage'],
                 'current_wave_position': 'CURRENT_WAVE_POSITION_UNRESOLVED',
                 'rank': None, 'validated_count': False, 'inventories': [11, 7, 0, 0],
                 'omitted_survivors': 'All earlier survivors remain in the hashed prior canonical export; these are reader examples, not a ranking or new candidate selection.'}
    old.save(output/'synthesis.json', synthesis)
    # Guard the specific new narrative facts against silently changed inputs.
    by_role = {(r['hypothesis'], r['role']): r for r in roots}
    checks = [(('M1', 2), 'low_occurrences', 0.14375, '2008-11-03'),
              (('M1', 3), 'low_occurrences', 0.21625, '2010-08-02'),
              (('M2', 5), 'high_occurrences', 236.54, '2026-05-01')]
    for key, field, value, date in checks:
        found = by_role[key]['observed_window'][field]
        if not any(x['value'] == value and x['bar_label_utc'].startswith(date) for x in found):
            raise ValueError('Historical narrative fact requires review')
    prior_artifact = old.read(previous.PACK/'artifact.json')
    now = datetime.now(timezone.utc).isoformat()
    title = 'NVDA — التاريخ والسيناريوهات والموضع المشروط'
    manifest = {'version': 1, 'surface': 'report', 'title': title,
                'description': 'قراءة مترابطة من اللقطات المحفوظة؛ ليست عدّاً مثبتاً',
                'generatedAt': now, 'cards': [], 'charts': [], 'tables': [], 'blocks': [],
                'sources': [{'id': 'synthesis', 'label': 'Original BATS:NVDA captures and preserved exact hypotheses', 'path': 'synthesis.json'}]}
    datasets = {}
    parts = []
    def prose(key, body):
        manifest['blocks'].append({'id': key, 'type': 'markdown', 'body': body})
        parts.append(body)
    def table(key, title, headers, rows):
        prose(key, '### '+title+'\n\n'+display.display.mdtable(headers, rows))
    def roles(alias):
        h = next(x for x in cases if x['display_id'] == alias)
        rows = []
        for i in range(len(h['endpoints'])//2):
            a, b = h['endpoints'][2*i:2*i+2]
            rows.append([i+1, a['timestamp_utc'][:10], a['price_field']+' '+str(a['price']),
                         b['timestamp_utc'][:10], b['price_field']+' '+str(b['price'])])
        table('roles-'+alias, 'الأدوار المقترحة — '+alias,
              ['الدور', 'بار البداية UTC', 'الحقل والسعر', 'بار النهاية UTC', 'الحقل والسعر'], rows)
    def plot(key, res, alias, label):
        h = next(x for x in cases if x['display_id'] == alias) if alias else None
        rows = display.chart_rows(snapshots[res], h, start='1999' if res == '1M' else None)
        chart = deepcopy(prior_artifact['manifest']['charts'][0])
        chart.update(id=key, title=label, dataset=key)
        chart['source'].update(id=key+'-source', path='chart_rows.json')
        datasets[key] = rows
        manifest['charts'].append(chart)
        manifest['blocks'].append({'id': key+'-block', 'type': 'chart', 'chartId': key, 'layout': 'full'})
        parts.append('الرسم «'+label+'» متاح في HTML؛ جميع القيم الأصلية في جدول الرسم. المقياس log10 للعرض فقط.')
    prose('title', '# '+title)
    narrative = old.read(PACK/'narrative.json')
    for section in narrative:
        prose(section['id'], section['body'])
        key = section['id']
        if key == 'history':
            table('history-bands', 'التاريخ المرصود قبل تفسيره', ['فترة بارات UTC', 'عدد البارات الشهرية', 'أدنى low وبار وقوعه', 'أعلى high وبار وقوعه'],
                  [[x['first_bar'][:10]+' — '+x['last_bar'][:10], x['bars'],
                    str(x['low_occurrences'][0]['value'])+' / '+x['low_occurrences'][0]['bar_label_utc'][:10],
                    str(x['high_occurrences'][0]['value'])+' / '+x['high_occurrences'][0]['bar_label_utc'][:10]] for x in bands])
        if key == 'm1':
            roles('M1'); plot('monthly-m1', '1M', 'M1', 'السياق الشهري M1 — أدوار مقترحة')
        if key == 'm2':
            roles('M2'); plot('monthly-m2', '1M', 'M2', 'السياق الشهري M2 — طرف خامس جارٍ مقترح')
        if key == 'recent-linked':
            roles('D2026:1D:N6:S38'); plot('recent-daily', '1D', 'D2026:1D:N6:S38', 'الجزء اليومي المحتوى — يوليو وأغسطس')
        if key == 'local-corrective':
            roles('H4CONTEXT:240:N4:S31:SINGLE_ZIGZAG')
            plot('local-4h', '240', 'H4CONTEXT:240:N4:S31:SINGLE_ZIGZAG', 'الاختبار الثلاثي المحلي — 4H')
        if key == 'local-ni':
            roles('RECENT:60:N6:S43'); roles('TAIL:15:N6:S10')
        if key == 'coverage':
            table('captures', 'كل لقطة مستقلة', ['الدقة', 'أول بار', 'آخر بار', 'الالتقاط UTC', 'آخر إغلاق'],
                  [[k, v['first_bar'][:10], v['last_bar'][:10], v['metadata']['captured_at_utc'], v['last_close']]
                   for k, v in doc['input_coverage'].items()])
    artifact = {'surface': 'report', 'manifest': manifest,
                'snapshot': {'version': 1, 'generatedAt': now, 'status': 'ready', 'datasets': datasets},
                'sources': manifest['sources'], 'package_info': {'delivery_mode': 'html', 'audience': 'product stakeholders', 'language': 'ar'}}
    old.save(output/'artifact.json', artifact)
    old.save(output/'chart_rows.json', datasets)
    old.save(output/'audit.json', {'raw_reconciliation': receipt, 'historical_bars': sum(x['bars'] for x in bands),
                'root_role_windows': len(roots), 'selected_reader_cases': len(cases),
                'prior_survivors_preserved': True, 'new_evaluations': 0,
                'data_boundary_not_wave_origin': True, 'path_extrema_not_endpoint_replacements': True,
                'no_new_ancestry': True, 'current_position_unresolved': True,
                'chart_rows': {k: len(v) for k, v in datasets.items()}})
    report_path = (output/'report.md').resolve()
    if not report_path.is_relative_to(output):
        raise ValueError('Escaping report path')
    with report_path.open('x', encoding='utf-8', newline='\n') as f:
        f.write('\n\n'.join(parts)+'\n')
    print({'stage': STAGE, 'blocks': len(manifest['blocks']), 'charts': len(datasets), 'new_evaluations': 0})


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, default=PACK)
    build(p.parse_args().output)
