"""Run any classifier through a small Python adapter on the frozen choice track."""
import argparse,copy,datetime,importlib,json,math,random,time
from pathlib import Path
from bench import ROOT,digest,requests_for,CRITERIA
from summarize import summarize

def normalize(value):
    if not isinstance(value,dict) or value.get('label') not in CRITERIA:
        raise ValueError('Adapter must return a valid label')
    out={'predicted':value['label']}
    if 'probabilities' in value:
        probs=value['probabilities']
        if not isinstance(probs,dict) or set(probs)!=set(CRITERIA):raise ValueError('Invalid probability labels')
        if any(not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=1 for v in probs.values()):raise ValueError('Invalid probability value')
        if abs(sum(probs.values())-1)>.001:raise ValueError('Probabilities must sum to one')
        out['probabilities']=probs
    return out

def run(predict,output,model_id,repeats=3,adapter_name='custom',kind='model'):
    if repeats<1:raise ValueError('repeats must be positive')
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    if (output/'raw.jsonl').exists():raise ValueError('Refusing to overwrite a prior run')
    cases=[json.loads(x) for x in (ROOT/'data/cases.jsonl').read_text().splitlines()]
    manifest=json.loads((ROOT/'data/manifest.json').read_text())
    if digest(cases)!=manifest['cases_sha256']:raise ValueError('Frozen dataset mismatch')
    if digest({c['id']:requests_for(c) for c in cases})!=manifest['requests_sha256']:raise ValueError('Frozen prompts mismatch')
    metadata={'model_id':model_id,'kind':kind,'adapter':adapter_name,'track':'choice','repeats':repeats,'cases_sha256':manifest['cases_sha256'],'requests_sha256':manifest['requests_sha256'],'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'timing':'Serial end-to-end adapter wall time; one excluded warmup. Adapter must synchronize asynchronous local accelerators before returning. No automatic retry.'}
    try:normalize(predict(copy.deepcopy(requests_for(cases[0])['choice'])));metadata['warmup']='ok'
    except Exception as e:metadata['warmup_error']=type(e).__name__
    jobs=[(i,c) for i in range(repeats) for c in cases];random.Random(20260921).shuffle(jobs);rows=[]
    with (output/'raw.jsonl').open('w') as stream:
        for rep,c in jobs:
            req=copy.deepcopy(requests_for(c)['choice']);request_sha=digest(req)
            row={'id':c['id'],'family':c['family'],'expected':c['expected'],'mode':'choice','repeat':rep,'request_sha256':request_sha}
            try:
                start=time.perf_counter();value=predict(req);elapsed=(time.perf_counter()-start)*1000
                if digest(req)!=request_sha:raise ValueError('Adapter mutated the frozen request')
                row.update(status='ok',elapsed_ms=elapsed,**normalize(value))
            except Exception as e:row.update(status='error',error_type=type(e).__name__)
            rows.append(row);stream.write(json.dumps(row,ensure_ascii=False)+'\n');stream.flush()
    metadata['finished_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    (output/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
    metrics=summarize(rows,expected_repeats=repeats)
    (output/'summary.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2)+'\n')
    return metrics

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--adapter',required=True,help='module:factory returning a request -> prediction callable');parser.add_argument('--model-id',required=True);parser.add_argument('--kind',choices=['model','baseline'],default='model');parser.add_argument('--output',required=True);parser.add_argument('--repeats',type=int,default=3);a=parser.parse_args()
    module,factory=a.adapter.split(':',1);predict=getattr(importlib.import_module(module),factory)()
    metrics=run(predict,a.output,a.model_id,a.repeats,a.adapter,a.kind)
    print(json.dumps({'correct':metrics['correct'],'n':metrics['n'],'macro_f1':metrics['macro_f1'],'errors':metrics['errors']}))
if __name__=='__main__':main()
