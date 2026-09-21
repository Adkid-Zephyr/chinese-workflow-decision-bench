"""Small, fixed stratified CPU check against the saved MPS results; no new weights/API calls."""
import argparse,hashlib,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from bench import requests_for,interpret

def main():
 p=argparse.ArgumentParser();p.add_argument('--checkpoint',required=True);a=p.parse_args()
 os.environ.update(HF_HUB_OFFLINE='1',USE_TF='0',USE_TORCH='1',TOKENIZERS_PARALLELISM='false')
 import torch,laya
 torch.set_num_threads(2)
 cases=[json.loads(x) for x in (ROOT/'data/cases.jsonl').read_text().splitlines()]
 # One case per family; rotate positions 0..7 => two examples per label.
 families=sorted({c['family'] for c in cases});selected=[sorted([c for c in cases if c['family']==family],key=lambda c:c['id'])[i] for i,family in enumerate(families)]
 reference={(r['id'],r['mode']):r for r in map(json.loads,(ROOT/'results/v1/laya/raw.jsonl').read_text().splitlines()) if r['repeat']==0}
 sha=hashlib.sha256()
 with (Path(a.checkpoint)/'model.safetensors').open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):sha.update(chunk)
 expected='9d628fd971b700382ac6f65920a86f149777b2e748e0c955fb3b19695aa8f204'
 assert sha.hexdigest()==expected,'Weight digest differs from the published Hub blob'
 agent=laya.load(a.checkpoint,device='cpu');rows=[]
 for c in selected:
  for mode,req in requests_for(c).items():
   start=time.perf_counter();res=agent.predict(req['state'],req['questions']);elapsed=(time.perf_counter()-start)*1000
   decoded=interpret(mode,res['answers']);ref=reference[(c['id'],mode)]
   key='probabilities' if mode=='choice' else 'signals';delta=max(abs(decoded[key][k]-ref[key][k]) for k in decoded[key])
   rows.append({'id':c['id'],'mode':mode,'expected':c['expected'],'cpu':decoded,'mps_predicted':ref['predicted'],'max_probability_delta':delta,'cpu_elapsed_ms':elapsed})
 out={'selection':'One case per sorted family; within-family indices 0..7, independent of observed errors. Two cases per expected label.','weight_sha256':sha.hexdigest(),'matches_hub_blob':True,'torch':torch.__version__,'cpu_dtype':str(next(agent.model.parameters()).dtype),'n':len(rows),'same_label_count':sum(r['cpu']['predicted']==r['mps_predicted'] for r in rows),'max_probability_delta':max(r['max_probability_delta'] for r in rows),'scope':'CPU and MPS share software and weights. Agreement reduces suspicion of an MPS-specific issue, not all shared implementation bugs. Not a performance benchmark.','rows':rows}
 (ROOT/'results/v1/environment_check.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in out.items() if k!='rows'}))
if __name__=='__main__':main()
