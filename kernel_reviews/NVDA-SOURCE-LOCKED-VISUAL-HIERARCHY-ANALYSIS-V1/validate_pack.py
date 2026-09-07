"""Narrow artifact checks only; no pipeline, methodology calls or network."""
import ast
import hashlib
import json
import subprocess
import unittest
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image

PACK=Path(__file__).resolve().parent
ROOT=PACK.parents[1]
def read(name): return json.loads((PACK/name).read_text(encoding='utf-8-sig'))
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(4*1024*1024),b''): h.update(block)
    return h.hexdigest()

class ArtifactChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.h=read('hierarchy.json'); cls.e=cls.h['endpoints']; cls.nodes=cls.h['nodes']
        cls.byid={n['node_id']:n for n in cls.nodes}; cls.views=read('annotations.json')
        cls.prov=read('capture_provenance.json'); cls.sources=read('source_references.json')['references']
    def test_unique_unranked_scenarios_and_nodes(self):
        self.assertEqual(len(self.byid),len(self.nodes)); self.assertEqual({n['scenario'] for n in self.nodes},{'A','B'})
        self.assertIsNone(self.h['rank'])
    def test_single_parent_same_scenario_containment(self):
        for n in self.nodes:
            a,b=[self.e[n[k]]['order'] for k in ('start_evidence','end_evidence')]
            self.assertLess(a,b)
            if n['parent_id']:
                p=self.byid[n['parent_id']]; self.assertEqual(n['scenario'],p['scenario'])
                self.assertGreaterEqual(a,self.e[p['start_evidence']]['order'])
                self.assertLessEqual(b,self.e[p['end_evidence']]['order'])
    def test_no_ipo_origin(self):
        self.assertFalse(any(n['start_evidence']=='d0' for n in self.nodes))
    def test_precision_never_becomes_operand_authority(self):
        for e in self.e.values():
            self.assertFalse(e['orthodox_endpoint_authority']); self.assertFalse(e['executable_operand_authority'])
        self.assertEqual(self.e['last']['price_display_or_estimate_USD'],'230.36 displayed')
    def test_current_position_conditional_and_open(self):
        self.assertEqual(self.h['current_position']['engine_status'],'CURRENT_WAVE_POSITION_UNRESOLVED')
        for n in self.nodes:
            if n['end_evidence']=='last': self.assertEqual(n['end_kind'],'OPEN_OBSERVATION_BOUNDARY_NOT_WAVE_END')
        for s in ('A','B'): self.assertTrue(self.h['current_position'][s]['condition'])
    def test_annotation_node_endpoint_and_scenario_links(self):
        for v in self.views:
            for m in v['marks']:
                n=self.byid[m['node']]; self.assertEqual(n['scenario'],v['scenario'])
                self.assertIn(m['evidence'],self.e)
                if m['relationship']!='context_region': self.assertEqual(n[m['relationship']+'_evidence'],m['evidence'])
    def test_image_coordinates_and_dimensions(self):
        for v in self.views:
            with Image.open(PACK/v['source_image']) as original, Image.open(PACK/v['output']) as image:
                self.assertEqual(original.size,(2546,1436)); self.assertEqual(image.size,(2546,1664))
            for m in v['marks']:
                self.assertTrue(0<=m['xy'][0]<2048 and 0<=m['xy'][1]<1155)
    def test_original_image_hashes(self):
        for item in self.prov['images'].values():
            self.assertEqual(sha(PACK/item['image']),item['sha256'])
            if 'metadata_sha256' in item: self.assertEqual(sha(PACK/item['metadata']),item['metadata_sha256'])
    def test_actual_feed_and_no_yahoo(self):
        self.assertEqual(self.prov['actual_feed'],'BATS:NVDA / Cboe One'); self.assertFalse(self.prov['Yahoo_operands_used'])
        for name in ('early_weekly','middle_weekly','recent_daily','latest_daily'):
            self.assertEqual(self.prov['images'][name]['metadata']['chart']['symbol'],'BATS:NVDA')
    def test_source_paths_protected_and_nodes_referenced(self):
        for r in self.sources.values():
            root=Path('C:/ElliottCodex')/r.get('root','Sources_LOCKED')
            self.assertTrue((root/r['path']).is_file(),r)
            self.assertTrue(r['locator'])
        for n in self.nodes:
            for r in n['source_refs']: self.assertIn(r,self.sources)
    def test_repeated_context_not_deduplicated(self):
        a=self.byid['A.5.1']; b=self.byid['B.3.3.3.1']
        self.assertEqual(a['start_evidence'],b['start_evidence']); self.assertEqual(a['end_evidence'],b['end_evidence'])
        self.assertNotEqual(a['parent_id'],b['parent_id']); self.assertNotEqual(a['node_id'],b['node_id'])
    def test_no_certification_or_methodology_execution(self):
        for n in self.nodes: self.assertFalse(n['engine_evaluated']); self.assertFalse(n['validity_authority'])
        tree=ast.parse((PACK/'prepare_pack.py').read_text(encoding='utf-8'))
        imports=[n.module or '' for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
        imports += [a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]
        self.assertFalse(any(x.startswith(('elliott','requests','socket')) for x in imports))
    def test_canonical_report_and_coverage_totals(self):
        a=read('artifact.json'); self.assertEqual(a['snapshot']['status'],'partial')
        rows=a['snapshot']['datasets']['coverage']
        self.assertEqual(sum(r['windows'] for r in rows),len(self.prov['images']))
        self.assertEqual([r['windows'] for r in rows],[1,3,3])
        self.assertEqual(len([b for b in a['manifest']['blocks'] if b['type']=='html']),4)
    def test_approved_tracked_files_unchanged(self):
        diff=subprocess.check_output(['git','diff','--diff-filter=DMRT','--name-only','0ac632d5162095bc9a9e5f16cf7d57b705f11d96','--'],cwd=ROOT,text=True)
        self.assertFalse(diff.strip(),diff)

def final_integrity():
    pre=read('pre_integrity.json'); result={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'packages':[]}
    for old,filename in zip(pre['packages'],('PACKAGE_MANIFEST.json','SOURCE_MANIFEST.json')):
        root=Path(old['root']); manifest=root/filename
        actual=sha(manifest); assert actual==old['manifest_sha256']
        files=json.loads(manifest.read_text(encoding='utf-8-sig'))['files']; assert len(files)==old['count']
        entries=[]
        for entry in files:
            rel=entry.get('path',entry.get('relative_path')); p=root/rel
            size=p.stat().st_size; hashed=sha(p)
            match=size==entry.get('size_bytes',entry.get('bytes')) and hashed==entry['sha256']
            assert match,rel
            entries.append({'path':rel,'bytes':size,'sha256':hashed,'match':match})
        result['packages'].append({'root':str(root),'manifest_sha256':actual,'count':len(files),'mismatches':0,'entries':entries})
    result['version']=(Path(pre['packages'][0]['root'])/'VERSION').read_text().strip()
    result['policy_sha256']=sha(Path(pre['packages'][0]['root'])/'docs/elliott/SOURCE_POLICY.md')
    assert result['version']==pre['version']=='0.1.0'; assert result['policy_sha256']==pre['policy_sha256']
    (PACK/'final_integrity.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    return {'brain_entries':30,'source_entries':21,'mismatches':0,'policy_sha256':result['policy_sha256']}

if __name__=='__main__':
    import sys
    if '--manifest' in sys.argv:
        entries=[{'path':p.relative_to(PACK).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
          for p in sorted(PACK.rglob('*')) if p.is_file() and p.name!='REVIEW_manifest.json']
        assert not any('__pycache__' in e['path'] or '.tmp-' in e['path'] for e in entries)
        manifest={'identifier':PACK.name,'kind':'ADDITIVE_VISUAL_REVIEW_NOT_METHODOLOGY_BASELINE',
          'approved_base':'0ac632d5162095bc9a9e5f16cf7d57b705f11d96','historical_files_superseded':[],
          'entry_count':len(entries),'files':entries,'self_hash':'reported externally; manifest excludes itself'}
        (PACK/'REVIEW_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8',newline='\n')
        print(json.dumps({'entries':len(entries),'manifest_sha256':sha(PACK/'REVIEW_manifest.json')}))
        raise SystemExit(0)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ArtifactChecks)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    receipt={'kind':'artifact-only checks, not methodology tests','tests':result.testsRun,
      'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful(),
      'full_regression':'NOT_RUN: user-authorized artifact-only scope','integrity':final_integrity()}
    (PACK/'validation_receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(receipt)); raise SystemExit(0 if result.wasSuccessful() else 1)
