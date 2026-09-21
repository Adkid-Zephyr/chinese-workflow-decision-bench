"""Render public tables from saved results without further model calls."""
import csv,json
from pathlib import Path
p=Path(__file__).parent;root=p/'results/v1';s=json.loads((root/'summary.json').read_text());cases={c['id']:c for c in map(json.loads,(p/'data/cases.jsonl').read_text().splitlines())}
allrows={name:[json.loads(x) for x in (root/name/'raw.jsonl').read_text().splitlines()] for name in s}
with (root/'comparison.csv').open('w',newline='') as stream:
 w=csv.writer(stream);w.writerow(['backend','mode','case_id','family','repeat','expected','predicted','status','elapsed_ms','review','request_sha256'])
 for name,rows in allrows.items():
  for r in sorted(rows,key=lambda r:(r['mode'],r['id'],r['repeat'])):w.writerow([name,r['mode'],r['id'],r['family'],r['repeat'],r['expected'],r.get('predicted','ERROR'),r['status'],r.get('elapsed_ms'),r.get('review'),r['request_sha256']])
lines=['# 测试结果 v1','', '![成绩图](assets/scorecard.png)', '', '[环境排查与原因分析](docs/ANALYSIS.md) · [接入新分类器](docs/ADDING_MODELS.md)', '', '## 结论及边界','本次64个合成工作场景中，Jev对任务归属、状态和上下文的判断更符合冻结标签；Laya单选择题的本地延迟较低，但误生成待办较多。这不是通用模型能力或同硬件速度排名。','', '所有质量数字取预先约定的第0次重复，每模式64例。延迟取3次重复的192个请求；每个后端384次计时请求加2次预热，合计772次调用。全部计时请求成功。','', '|后端 / 提示|匹配预期|Macro-F1|误生成行动 / 32|漏掉行动 / 32|紧急召回 / 16|p50 ms|p95 ms|','|---|---:|---:|---:|---:|---:|---:|---:|']
for name in ['jev','laya']:
 for mode,r in s[name].items():lines.append(f"|{name} / {mode}|{r['correct']}/64|{r['macro_f1']:.3f}|{r['false_action_count']}/32|{r['missed_action_count']}/32|{r['urgent_recalled']}/16|{r['timing']['p50_ms']:.1f}|{r['timing']['p95_ms']:.1f}|")
lines+=['','“误生成行动”指预期为valuable/noise却输出urgent/todo；“漏掉行动”指预期urgent/todo却输出非行动或请求失败。紧急召回必须输出urgent。此处优先衡量工作流影响，不仅看整体准确率。','', '## 重复运行','三次使用完全相同输入，打乱运行顺序。下面同时列出三次结果，避免首次得分掩盖波动。','', '|后端 / 提示|第0次|第1次|第2次|三次标签一致|','|---|---:|---:|---:|---:|']
for name in ['jev','laya']:
 for mode,r in s[name].items():
  counts=[sum(x.get('predicted')==x['expected'] for x in allrows[name] if x['mode']==mode and x['repeat']==rep) for rep in range(3)]
  lines.append(f"|{name} / {mode}|{counts[0]}/64|{counts[1]}/64|{counts[2]}/64|{r['repeat_consistency']['same_label_all_three']}/64|")
lines+=['','## 分场景结果','|场景（各8例）|Jev choice|Jev four_noul|Laya choice|Laya four_noul|','|---|---:|---:|---:|---:|']
for family in sorted({x['family'] for x in cases.values()}):lines.append('|'+family+'|'+'|'.join(f"{s[n][m]['by_family'][family]['correct']}/8" for n,m in [('jev','choice'),('jev','four_noul'),('laya','choice'),('laya','four_noul')])+'|')
lines+=['','## 失败案例','Jev第0次唯一分类不一致：cross_chat-03在four_noul下把普通待办判为noise，行动概率0.32，并触发review。目标群要求林工下周完成文档，其他群的紧急任务不应改变目标消息。choice首次64/64不代表所有运行完美，重复结果见上表。','', 'Laya每个场景类别在choice下按case id取首个失败，未人工筛选“最差案例”；完整失败和正确案例都在CSV及raw.jsonl。','', '|场景|同群上下文与目标文本|预期|输出|','|---|---|---|---|']
for family in sorted({x['family'] for x in cases.values()}):
 bad=sorted([r for r in allrows['laya'] if r['repeat']==0 and r['mode']=='choice' and r['family']==family and r.get('predicted')!=r['expected']],key=lambda r:r['id'])
 if bad:
  r=bad[0];c=cases[r['id']];text=' / '.join(f"[{m['chat_id']}] {m['text']}" for m in c['messages']);lines.append(f"|{family}|{text}|{r['expected']}|{r.get('predicted','ERROR')}|")
lines+=['','## 长度与资源','- Laya的64例在两种提示中均没有state或instructions截断；所有候选选项也低于48 token单选项上限，见option_token_audit.json。Jev服务端内部截断不可观测，summary中记为null而非0。','- Laya保持默认max_len=1024、head_max_len=256，并未通过增大预算追分。','- 两模型实际structured state/questions哈希逐项匹配；预期标签、场景family、评分结果都未发送到模型。','- 未测长群聊、图片、真实线上吞吐或故障恢复能力；本集不包含超长输入压力测试。']
meta=json.loads((root/'laya/metadata.json').read_text());lines.append(f"- Laya预加载约{meta['load_seconds']:.1f}秒（不含下载）；进程峰值RSS约{meta['peak_process_rss_bytes']/2**30:.2f}GiB。该RSS不是完整MPS显存统计。")
jmeta=json.loads((root/'jev/metadata.json').read_text());tokens=sum(r['response']['usage']['input_tokens'] for r in allrows['jev'])+sum(w['usage']['input_tokens'] for w in jmeta['warmups'])
lines.append(f'- Jev累计输入{tokens:,} tokens（含预热），按官方$0.042/百万输入tokens估算${tokens/1e6*.042:.5f}，非实际账单记录。')
lines+=['','## 概率诊断','以下只用于描述这64个合成标签，不是经过独立验证的校准结论。ECE取预测类别概率，不使用模型另行返回的熵置信分数。','', '|后端 choice|Multiclass Brier（各类平方误差之和）|ECE（10等宽bins）|','|---|---:|---:|']
for name in ['jev','laya']:
 c=s[name]['choice']['choice_probability_diagnostics'];lines.append(f"|{name}|{c['multiclass_brier_sum']:.4f}|{c['ece_10_equal_width_bins']:.4f}|")
lines+=['','## 审计与复现','- 输入及请求在模型调用前通过Git提交冻结：`0ce2d5f`。','- 完整数据哈希、标注政策见[data/manifest.json](data/manifest.json)。','- 运行元数据及所有原始响应见[results/v1](results/v1)。','- 由`python summarize.py`和`python render_report.py`生成；不需要API密钥即可重算结果。','- 测试设计参考此前少量探索，本轮并非盲测或独立人工标注。不要把64/64外推为真实工作中100%准确。']
(p/'RESULTS.md').write_text('\n'.join(lines)+'\n')
