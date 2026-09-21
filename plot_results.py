"""Render shareable figures from recorded summary, never hand-enter scores."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parent
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'path','axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,'axes.edgecolor':'#d5dfe6','text.color':'#142d40','axes.labelcolor':'#425969','xtick.color':'#637786','ytick.color':'#142d40','savefig.facecolor':'#f7fafc'})

ZH = {
 'CHINESE WORKFLOW DECISION BENCH':'中文工作流分类基准 · CWDB-64',
 'Can a classifier assign the right work?':'AI 能分清谁该做、该不该做、急不急吗？',
 'v1  /  64 frozen synthetic scenarios  /  8 workflow families  /  768 timed requests':'v1  /  64 个冻结合成场景  /  8 类工作情境  /  768 次计时请求',
 'Accuracy ↑':'分类准确率 ↑', 'False actions ↓':'误生成任务数 ↓', 'Request latency ↓':'请求耗时 ↓',
 'Jev 1.13 · choice':'Jev 1.13 · 单选择题', 'Jev 1.13 · four-noul':'Jev 1.13 · 四问组合',
 'Laya multilingual · choice':'Laya 多语言版 · 单选择题', 'Laya multilingual · four-noul':'Laya 多语言版 · 四问组合',
 'Percent · dashed line: 25% constant-class baseline':'百分比 · 虚线：始终猜同一类别的 25% 基线',
 'Non-action messages turned into tasks':'32 条无需行动的消息，被误判为待办或紧急',
 'Bar: p50 · whisker: p95 (not a confidence interval)':'柱长：中位数 p50 · 横线：p95（非置信区间）',
 'Quality uses the first frozen repeat (64 cases); all three repeats are published. Latency uses 192 requests per row after warmup.':'准确率采用预先固定的首次结果（64 例）；三次重复全部公开。每行耗时统计 192 次请求，不含预热。',
 'Laya: Apple M4 MPS, local. Jev: remote API including network. These are deployment paths, not a same-hardware comparison.':'Laya：苹果 M4 GPU 本地运行。Jev：云端 API，包含网络往返。此处比较实际调用方式，并非同硬件测试。',
 'Synthetic, AI-assisted diagnostic — not a general classifier or intelligence ranking.  •  github.com/Adkid-Zephyr/chinese-workflow-decision-bench':'AI 辅助编写的合成诊断集，不是通用能力排行榜。  ·  github.com/Adkid-Zephyr/chinese-workflow-decision-bench',
 'Where do workflow decisions fail?':'不同工作场景，模型分别答对多少？',
 'Per-family exact label matches · first frozen repeat · 8 synthetic cases per family':'逐类统计与预期标签一致的数量 · 首次冻结结果 · 每类 8 个合成案例',
 'No statistical independence or generalization claim. Read the full methodology and every prediction in the repository.':'小样本合成测试，不代表真实业务总体准确率；完整方法和逐条结果见仓库。',
 'Jev\nchoice':'Jev\n单选择题', 'Jev\nfour-noul':'Jev\n四问组合',
 'Laya multilingual\nchoice':'Laya 多语言版\n单选择题', 'Laya multilingual\nfour-noul':'Laya 多语言版\n四问组合',
 'Conditional':'条件是否成立', 'Cross Chat':'跨群干扰', 'Knowledge':'知识与资料', 'Lifecycle':'取消、完成与重启',
 'Ownership':'任务归属', 'Thread Context':'同群上下文', 'Untrusted Content':'引文与指令干扰', 'Urgency':'紧急程度',
}
def localize(fig, lang):
 if lang != 'zh': return
 from matplotlib import font_manager
 from matplotlib.text import Text
 candidates=[Path('/System/Library/Fonts/Hiragino Sans GB.ttc'),Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')]
 font_path=next((p for p in candidates if p.exists()),None)
 if font_path is None:raise RuntimeError('Chinese charts require Hiragino Sans GB or Noto Sans CJK.')
 for ax in fig.axes:
  for axis in ['x','y']:
   labels=getattr(ax,'get_'+axis+'ticklabels')(); translated=[ZH.get(t.get_text(),t.get_text()) for t in labels]
   if any(a!=b.get_text() for a,b in zip(translated,labels)):getattr(ax,'set_'+axis+'ticklabels')(translated)
 texts=fig.findobj(match=Text)
 for ax in fig.axes:
  for table in ax.tables:
   texts.extend(cell.get_text() for cell in table.get_celld().values())
 for text in texts:
  old=text.get_text();new=ZH.get(old,old)
  if old.endswith(' ms'):new=old[:-3]+' 毫秒'
  text.set_text(new);text.set_fontproperties(font_manager.FontProperties(fname=str(font_path),size=text.get_fontsize(),weight=text.get_fontweight()))

def chinese_table(rows):
 fig,ax=plt.subplots(figsize=(15,5.7));fig.patch.set_facecolor('#f7fafc');ax.axis('off')
 fig.text(.04,.89,'中文工作流分类测试：Jev 与 Laya',fontsize=24,fontweight='bold')
 fig.text(.04,.80,'64 个合成场景 · 准确率取首次冻结结果 · 耗时取预热后的请求中位数',fontsize=12,color='#637786')
 cells=[]
 for index,label in enumerate(['单选择题','四问组合']):
  jev,laya=rows[index],rows[index+2]
  cells.append([label,f"{jev['correct']}/64（{jev['accuracy']*100:.2f}%）",f"{laya['correct']}/64（{laya['accuracy']*100:.2f}%）",f"{jev['timing']['p50_ms']:.0f} 毫秒",f"{laya['timing']['p50_ms']:.0f} 毫秒"])
 table=ax.table(cellText=cells,colLabels=['测试方式','Jev 正确分类','Laya 正确分类','Jev 耗时','Laya 耗时'],cellLoc='center',bbox=[.0,.30,1,.42],colWidths=[.16,.26,.26,.16,.16])
 table.auto_set_font_size(False);table.set_fontsize(13)
 for (r,c),cell in table.get_celld().items():
  cell.set_edgecolor('#dbe5ec');cell.set_linewidth(.7)
  cell.set_facecolor('#142d40' if r==0 else ('#edf5fd' if c in [1,3] else '#eaf7f4' if c in [2,4] else '#ffffff'))
  cell.get_text().set_color('white' if r==0 else '#142d40')
  if r==0:cell.get_text().set_fontweight('bold')
 fig.text(.04,.19,'单选择题：直接四选一。四问组合：分别判断相关性、行动、紧急性、资料价值，再由固定规则分类。',fontsize=11)
 fig.text(.04,.12,'Laya 为苹果 M4 GPU 本地运行；Jev 为云端 API，包含网络往返。小样本合成测试，不代表总体准确率。',fontsize=10,color='#637786')
 localize(fig,'zh')
 for suffix in ['png','svg']:fig.savefig(ROOT/f'assets/comparison-table-zh.{suffix}',dpi=170,metadata={'Creator':'CWDB-64'})
 plt.close(fig)

def main(lang="en"):
 s=json.loads((ROOT/'results/v1/summary.json').read_text());(ROOT/'assets').mkdir(exist_ok=True)
 entries=[('jev','choice'),('jev','four_noul'),('laya','choice'),('laya','four_noul')]
 names=['Jev 1.13 · choice','Jev 1.13 · four-noul','Laya multilingual · choice','Laya multilingual · four-noul']
 rows=[s[b][m] for b,m in entries];colors=['#2874c8','#2874c8','#16998d','#16998d'];y=np.arange(4)
 fig,axes=plt.subplots(1,3,figsize=(18,8.3),gridspec_kw={'width_ratios':[1.4,1,1.15]});fig.patch.set_facecolor('#f7fafc')
 fig.subplots_adjust(left=.225,right=.955,top=.69,bottom=.25,wspace=.29)
 fig.text(.035,.92,'CHINESE WORKFLOW DECISION BENCH',fontsize=14,fontweight='bold',color='#2874c8')
 fig.text(.035,.845,'Can a classifier assign the right work?',fontsize=29,fontweight='bold')
 fig.text(.035,.787,'v1  /  64 frozen synthetic scenarios  /  8 workflow families  /  768 timed requests',fontsize=13,color='#637786')
 for ax in axes:
  ax.set_facecolor('#f7fafc');ax.set_ylim(3.7,-.7);ax.set_yticks(y);ax.tick_params(axis='y',length=0);ax.grid(axis='x',color='#e4ebf0',zorder=0);ax.set_axisbelow(True)
 axes[0].set_yticklabels(names,fontsize=12)
 for ax in axes[1:]:ax.set_yticklabels([])
 acc=[r['accuracy']*100 for r in rows];axes[0].barh(y,acc,color=colors,height=.47,zorder=3);axes[0].set_xlim(0,127);axes[0].set_xticks([0,25,50,75,100]);axes[0].axvline(25,color='#92a1ad',ls='--',lw=1);axes[0].set_title('Accuracy ↑',loc='left',fontsize=16,fontweight='bold',pad=18)
 for i,(v,r) in enumerate(zip(acc,rows)):axes[0].text(v+2,i,f"{v:.2f}%\n{r['correct']}/64",va='center',fontsize=11,fontweight='bold')
 axes[0].set_xlabel('Percent · dashed line: 25% constant-class baseline',fontsize=9,labelpad=14)
 bad=[r['false_action_count'] for r in rows];axes[1].barh(y,bad,color=colors,height=.47,zorder=3);axes[1].set_xlim(0,40);axes[1].set_xticks([0,8,16,24,32]);axes[1].set_title('False actions ↓',loc='left',fontsize=16,fontweight='bold',pad=18)
 for i,v in enumerate(bad):axes[1].text(v+1,i,f'{v}/32',va='center',fontsize=12,fontweight='bold')
 axes[1].set_xlabel('Non-action messages turned into tasks',fontsize=9,labelpad=14)
 latency=[r['timing']['p50_ms'] for r in rows];p95=[r['timing']['p95_ms'] for r in rows]
 axes[2].barh(y,latency,color=colors,height=.47,zorder=3);axes[2].set_xlim(0,620);axes[2].set_xticks([0,200,400,600]);axes[2].set_title('Request latency ↓',loc='left',fontsize=16,fontweight='bold',pad=18)
 for i,(v,hi) in enumerate(zip(latency,p95)):
  axes[2].plot([v,hi],[i,i],color='#263f51',lw=1.3);axes[2].plot([hi,hi],[i-.09,i+.09],color='#263f51',lw=1.3);axes[2].text(hi+10,i,f'{v:.0f} ms',va='center',fontsize=11,fontweight='bold')
 axes[2].set_xlabel('Bar: p50 · whisker: p95 (not a confidence interval)',fontsize=9,labelpad=14)
 fig.text(.035,.14,'Quality uses the first frozen repeat (64 cases); all three repeats are published. Latency uses 192 requests per row after warmup.',fontsize=11)
 fig.text(.035,.102,'Laya: Apple M4 MPS, local. Jev: remote API including network. These are deployment paths, not a same-hardware comparison.',fontsize=10,color='#637786')
 fig.text(.035,.063,'Synthetic, AI-assisted diagnostic — not a general classifier or intelligence ranking.  •  github.com/Adkid-Zephyr/chinese-workflow-decision-bench',fontsize=10,color='#637786')
 localize(fig,lang)
 for suffix in ['png','svg']:fig.savefig(ROOT/f"assets/scorecard{'-zh' if lang=='zh' else ''}.{suffix}",dpi=170,metadata={'Creator':'Chinese Workflow Decision Bench'})
 plt.close(fig)
 families=sorted(rows[0]['by_family']);matrix=np.array([[r['by_family'][f]['correct']/8 for r in rows] for f in families])
 fig,ax=plt.subplots(figsize=(12,8));fig.patch.set_facecolor('#f7fafc');fig.subplots_adjust(left=.23,right=.91,top=.83,bottom=.20)
 im=ax.imshow(matrix,vmin=0,vmax=1,cmap='Blues',aspect='auto');ax.set_xticks(range(4),['Jev\nchoice','Jev\nfour-noul','Laya multilingual\nchoice','Laya multilingual\nfour-noul']);ax.set_yticks(range(8),[f.replace('_',' ').title() for f in families]);ax.tick_params(length=0,pad=10)
 for i in range(8):
  for j in range(4):ax.text(j,i,f'{round(matrix[i,j]*8)}/8',ha='center',va='center',fontsize=15,fontweight='bold',color='white' if matrix[i,j]>.55 else '#142d40')
 fig.text(.04,.935,'Where do workflow decisions fail?',fontsize=25,fontweight='bold');fig.text(.04,.882,'Per-family exact label matches · first frozen repeat · 8 synthetic cases per family',fontsize=11,color='#637786')
 fig.text(.04,.075,'No statistical independence or generalization claim. Read the full methodology and every prediction in the repository.',fontsize=10,color='#637786')
 localize(fig,lang)
 for suffix in ['png','svg']:fig.savefig(ROOT/f"assets/scenario-breakdown{'-zh' if lang=='zh' else ''}.{suffix}",dpi=170,metadata={'Creator':'Chinese Workflow Decision Bench'})
 plt.close(fig)
 if lang=='zh':chinese_table(rows)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--lang',choices=['en','zh'],default='en');main(parser.parse_args().lang)
