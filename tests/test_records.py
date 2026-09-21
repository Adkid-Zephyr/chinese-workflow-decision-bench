import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bench import digest,requests_for
ROOT=Path(__file__).resolve().parents[1]
class RecordsTests(unittest.TestCase):
 def test_frozen_inputs_and_no_label_leakage(self):
  cases=[json.loads(x) for x in (ROOT/'data/cases.jsonl').read_text().splitlines()];manifest=json.loads((ROOT/'data/manifest.json').read_text())
  self.assertEqual(digest(cases),manifest['cases_sha256']);self.assertEqual(digest({c['id']:requests_for(c) for c in cases}),manifest['requests_sha256'])
  for c in cases:
   for req in requests_for(c).values():self.assertEqual(set(req['state']),{'viewer','target_message_id','messages'})
 def test_complete_paired_records(self):
  expected={c['id']:c for c in map(json.loads,(ROOT/'data/cases.jsonl').read_text().splitlines())};pairs=[]
  for backend in ['jev','laya']:
   path=ROOT/'results/v1'/backend/'raw.jsonl'
   if not path.exists():self.skipTest('Recorded results are not present yet')
   rows=[json.loads(x) for x in path.read_text().splitlines()];self.assertEqual(len(rows),384)
   seen={}
   for r in rows:
    key=(r['id'],r['mode'],r['repeat']);self.assertNotIn(key,seen);seen[key]=r['request_sha256']
    self.assertEqual(r['expected'],expected[r['id']]['expected']);self.assertEqual(r['request_sha256'],digest(requests_for(expected[r['id']])[r['mode']]))
   pairs.append(seen)
  self.assertEqual(pairs[0],pairs[1])
if __name__=='__main__':unittest.main()
