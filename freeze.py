import json,collections
from pathlib import Path
from bench import digest,requests_for,POLICY,CRITERIA,ASKS,VIEWER
p=Path(__file__).parent; cases=[json.loads(x) for x in (p/'data/cases.jsonl').read_text().splitlines()]
assert len(cases)==64 and len({x['id'] for x in cases})==64
assert set(collections.Counter(x['expected'] for x in cases).values())=={16}
for c in cases:assert c['target_id'] in {m['id'] for m in c['messages']}
manifest={'version':'1.0','provenance':'AI-assisted, manually specified synthetic scenarios inspired by workplace workflows; no private chat logs. Not independently human-annotated.','cases':len(cases),'families':dict(collections.Counter(x['family'] for x in cases)),'labels':dict(collections.Counter(x['expected'] for x in cases)),'cases_sha256':digest(cases),'requests_sha256':digest({c['id']:requests_for(c) for c in cases}),'quality_repeat':0,'repetitions':3,'latency':'All successful timed requests across repetitions, excluding warmup; errors reported separately.','policy':POLICY,'criteria':CRITERIA,'asks':ASKS,'viewer':VIEWER}
(p/'data/manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(manifest['cases_sha256'],manifest['requests_sha256'])
