"""Focused artifact checks, full protected read-only hashing, scoped manifest.
No methodology execution, live retrieval, or historical-artifact writes.
"""
import ast
import hashlib
import json
import re
import subprocess
import unittest
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image

PACK=Path(__file__).resolve().parent
ROOT=PACK.parents[1]
PRIOR=PACK.parent/'NVDA-SOURCE-LOCKED-VISUAL-HIERARCHY-ANALYSIS-V1'
BASE='25b56d9a8b0da62420546c1c9ad0baef7e64a755'
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def save(name,obj): (PACK/name).write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8',newline='\n')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(4*1024*1024),b''): h.update(b)
    return h.hexdigest()
def parents_valid(h):
    by={n['node_id']:n for n in h['nodes']}; e=h['endpoints']
    if len(by)!=len(h['nodes']): return False
    for n in h['nodes']:
        a,b=[e[n[k]]['order'] for k in ('start_evidence','end_evidence')]
        if not a<b: return False
        if n['parent_id']:
            p=by.get(n['parent_id'])
            if not p or p['lineage']!=n['lineage']: return False
            if a<e[p['start_evidence']]['order'] or b>e[p['end_evidence']]['order']: return False
    return True

class ReviewChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.h=read(PACK/'hierarchy.json'); cls.by={n['node_id']:n for n in cls.h['nodes']}
        cls.e=cls.h['endpoints']; cls.v=read(PACK/'annotations.json')
        cls.p=read(PACK/'capture_provenance.json'); cls.r=read(PACK/'source_references.json')['references']
    def test_two_interpretations_no_rank(self):
        self.assertEqual(self.h['interpretations'],['L1','L2']); self.assertIsNone(self.h['rank'])
        self.assertEqual({n['lineage'] for n in self.by.values()},{'A.L1','A.L2','B.L1','B.L2'})
    def test_parent_containment(self): self.assertTrue(parents_valid(self.h))
    def test_reject_correction_inside_closed_parent(self):
        h=json.loads(json.dumps(self.h))
        next(n for n in h['nodes'] if n['node_id']=='A.L1.correction')['parent_id']='A.L1.advance'
        self.assertFalse(parents_valid(h))
    def test_reject_cross_alternative_parent(self):
        h=json.loads(json.dumps(self.h))
        next(n for n in h['nodes'] if n['node_id']=='A.L2.advance.3.3')['parent_id']='B.L2.advance.3'
        self.assertFalse(parents_valid(h))
    def test_exact_prior_mappings(self):
        prior={n['node_id']:n for n in read(PRIOR/'hierarchy.json')['nodes']}
        for m in self.h['mappings']:
            self.assertIn(m['prior_ancestor'],prior); self.assertIn(m['prior_open_component'],prior)
            self.assertEqual(prior[m['prior_open_component']]['parent_id'],m['prior_ancestor'])
            a=self.by[m['new_component']]
            self.assertEqual(a['prior_node_ref'],m['prior_open_component'])
            if m['subsequent_component']:
                c=self.by[m['subsequent_component']]
                self.assertEqual(a['parent_id'],c['parent_id']); self.assertEqual(a['end_evidence'],c['start_evidence'])
    def test_open_boundaries_not_completion(self):
        for n in self.by.values():
            if n['end_evidence']=='last': self.assertEqual(n['end_kind'],'OPEN_OBSERVATION_BOUNDARY_NOT_WAVE_END')
        self.assertEqual(self.h['current_position']['engine_status'],'CURRENT_WAVE_POSITION_UNRESOLVED')
    def test_separate_context_instances_not_confirmation(self):
        for local in ('L1','L2'):
            a=self.by['A.'+local+'.advance']; b=self.by['B.'+local+'.advance']
            self.assertEqual(a['start_evidence'],b['start_evidence']); self.assertEqual(a['end_evidence'],b['end_evidence'])
            self.assertNotEqual(a['parent_id'],b['parent_id']); self.assertFalse(a['validity_authority'])
    def test_exact_last_reading_not_crosshair_axis(self):
        last=self.p['last_daily_bar']
        self.assertEqual(last['displayed_date'],'Fri 04 Sep 26'); self.assertEqual(last['displayed_OHLC']['C'],'230.36')
        self.assertIn('230.43',last['crosshair_price_not_used'])
        self.assertIn('EMPTY',self.p['failed_reading'])
    def test_session_and_price_separation(self):
        self.assertIn('24H',self.p['settings']['four_hour_session'])
        self.assertIn('UNKNOWN',self.p['settings']['Daily_session_configuration'])
        self.assertTrue(self.p['current_readings']['not_comparable_atomic_operands'])
        self.assertIn('developing',self.p['current_readings']['rebound_4H_countdown'])
    def test_actual_feed_and_timeframe(self):
        self.assertEqual(self.p['actual_feed'],'BATS:NVDA / Cboe One'); self.assertFalse(self.p['Yahoo_used'])
        for name,r in self.p['images'].items():
            self.assertEqual(r['metadata']['chart']['symbol'],'BATS:NVDA')
            self.assertEqual(r['metadata']['chart']['resolution'],'240' if name.endswith('_4h') else '1D')
            self.assertTrue(r['captured_at_utc'].startswith('2026-09-08'))
    def test_capture_limit_and_original_hashes(self):
        self.assertEqual(len(self.p['images']),7); self.assertEqual(self.p['coverage']['targeted'],6)
        for r in self.p['images'].values(): self.assertEqual(sha(PACK/r['image']),r['sha256'])
    def test_no_pixel_operand_authority(self):
        for e in self.e.values():
            self.assertFalse(e['orthodox_endpoint_authority']); self.assertFalse(e['executable_operand_authority'])
    def test_annotation_identity_and_endpoint(self):
        for v in self.v:
            for m in v['marks']:
                for node in m['node_instances']:
                    n=self.by[node]; self.assertEqual(n['local_interpretation'],v['local'])
                    if not m.get('context_only'):
                        self.assertIn(m['evidence'],[n['start_evidence'],n['end_evidence']])
    def test_images_and_context_not_endpoint_substitution(self):
        for v in self.v:
            with Image.open(PACK/v['source_image']) as a, Image.open(PACK/v['output']) as b:
                self.assertEqual(a.size,(2534,1376)); self.assertEqual(b.size,(2534,1604))
            for m in v['marks']:
                self.assertTrue(0<=m['xy'][0]<2048 and 0<=m['xy'][1]<1112)
                if 'rebound' in v['name']:
                    self.assertTrue(m['context_only'])
                    self.assertEqual(self.h['context_observations'][m['context_evidence']]['image'],v['source_image'])
                    self.assertFalse(self.h['context_observations'][m['context_evidence']]['role_endpoint_authority'])
    def test_source_references(self):
        for r in self.r.values():
            self.assertTrue((Path('C:/ElliottCodex')/r.get('root','Sources_LOCKED')/r['path']).is_file())
            self.assertTrue(r['locator'])
        for n in self.by.values(): self.assertTrue(all(x in self.r for x in n['source_refs']))
    def test_report_links_and_table(self):
        text=(PACK/'report_ar.md').read_text(encoding='utf-8')
        for link in re.findall(r'\]\(([^)]+)\)',text): self.assertTrue((PACK/link).is_file(),link)
        table=(PACK/'node_table.md').read_text(encoding='utf-8')
        for n in self.by.values(): self.assertIn('| '+n['node_id']+' |',table)
    def test_no_evaluator_or_network_in_renderer(self):
        tree=ast.parse((PACK/'build_review.py').read_text(encoding='utf-8'))
        imports=[n.module or '' for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        imports += [a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
        self.assertFalse(any(x.startswith(('elliott','requests','socket','subprocess')) for x in imports))
        self.assertTrue(all(not n['engine_evaluated'] and not n['validity_authority'] for n in self.by.values()))
    def test_prior_manifest_and_entries(self):
        self.assertEqual(sha(PRIOR/'REVIEW_manifest.json'),'1975bc826517b9783ee4d4f826358eca99bf68795b61829013eef680fdbacb5e')
        m=read(PRIOR/'REVIEW_manifest.json')
        for e in m['files']:
            self.assertEqual(sha(PRIOR/e['path']),e['sha256']); self.assertEqual((PRIOR/e['path']).stat().st_size,e['bytes'])
    def test_no_existing_tracked_modifications(self):
        diff=subprocess.check_output(['git','diff','--diff-filter=DMRT','--name-only',BASE,'--'],cwd=ROOT,text=True)
        self.assertFalse(diff.strip(),diff)
    def test_source_inventory_sealing_unchanged(self):
        tree=ast.parse((ROOT/'src/elliott_methodology_kernel/__init__.py').read_text())
        seals={n.func.id:n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id.startswith('_seal_')}
        self.assertEqual(len(seals['_seal_structural_validator_registry'].keywords[0].value.elts),7)
        self.assertEqual(len(seals['_seal_internal_family_validator_registry'].keywords[0].value.elts),0)
        self.assertEqual(read(PACK/'audit.json')['inventories'],{'methodology':11,'structural_producers':7,'family_producers':0,'family_issuances':0})

def integrity():
    pre=read(PACK/'pre_integrity.json'); result={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'packages':[]}
    for old,filename in zip(pre['packages'],('PACKAGE_MANIFEST.json','SOURCE_MANIFEST.json')):
        root=Path(old['root']); actual=sha(root/filename); assert actual==old['manifest_sha256']
        files=read(root/filename)['files']; assert len(files)==old['count']; entries=[]
        old_entries={e['path']:e for e in old['entries']}
        for ent in files:
            rel=ent.get('path',ent.get('relative_path')); p=root/rel
            size=p.stat().st_size; hashed=sha(p)
            assert size==ent.get('size_bytes',ent.get('bytes')) and hashed==ent['sha256'],rel
            assert hashed==old_entries[rel]['sha256'] and size==old_entries[rel]['bytes'],rel
            entries.append({'path':rel,'bytes':size,'sha256':hashed,'match':True})
        result['packages'].append({'root':str(root),'manifest_sha256':actual,'count':len(entries),'mismatches':0,'entries':entries})
    root=Path(pre['packages'][0]['root'])
    result['version']=(root/'VERSION').read_text().strip(); result['policy_sha256']=sha(root/'docs/elliott/SOURCE_POLICY.md')
    assert result['version']==pre['version']=='0.1.0'; assert result['policy_sha256']==pre['policy_sha256']
    book=Path(pre['packages'][1]['root'])/'book_frost_prechter/Elliott_Wave_Principle_Frost_Prechter_20th_Anniversary_1998.pdf'
    result['book_sha256']=sha(book)
    assert result['book_sha256']=='c78e1a29b717445e01de421370a627c440b127cf42c34646526a495b8c42ab9e'
    save('final_integrity.json',result)
    return {'Brain':30,'Sources':21,'mismatches':0,'book_sha256':result['book_sha256']}

if __name__=='__main__':
    import sys
    if '--manifest' in sys.argv:
        files=[{'path':p.relative_to(PACK).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
               for p in sorted(PACK.rglob('*')) if p.is_file() and p.name!='REVIEW_manifest.json']
        assert not any('__pycache__' in e['path'] for e in files)
        save('REVIEW_manifest.json',{'identifier':PACK.name,'kind':'ADDITIVE_PROVISIONAL_VISUAL_REVIEW',
             'approved_base':BASE,'historical_artifacts_modified':[],'entries':len(files),'files':files,'self_hash':'reported externally'})
        print(sha(PACK/'REVIEW_manifest.json'))
    else:
        result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ReviewChecks))
        receipt={'scope':'focused artifact checks only','tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),
                 'passed':result.wasSuccessful(),'full_regression':'NOT_RUN_ARTIFACT_ONLY','pipeline_runs':0,'integrity':integrity()}
        save('validation_receipt.json',receipt); print(json.dumps(receipt)); raise SystemExit(not result.wasSuccessful())
