"""Render shareable figures from recorded summary, never hand-enter scores."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parent
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'path','axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,'axes.edgecolor':'#d5dfe6','text.color':'#142d40','axes.labelcolor':'#425969','xtick.color':'#637786','ytick.color':'#142d40','savefig.facecolor':'#f7fafc'})
def main():
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
 for suffix in ['png','svg']:fig.savefig(ROOT/f'assets/scorecard.{suffix}',dpi=170,metadata={'Creator':'Chinese Workflow Decision Bench'})
 plt.close(fig)
 families=sorted(rows[0]['by_family']);matrix=np.array([[r['by_family'][f]['correct']/8 for r in rows] for f in families])
 fig,ax=plt.subplots(figsize=(12,8));fig.patch.set_facecolor('#f7fafc');fig.subplots_adjust(left=.23,right=.91,top=.83,bottom=.20)
 im=ax.imshow(matrix,vmin=0,vmax=1,cmap='Blues',aspect='auto');ax.set_xticks(range(4),['Jev\nchoice','Jev\nfour-noul','Laya multilingual\nchoice','Laya multilingual\nfour-noul']);ax.set_yticks(range(8),[f.replace('_',' ').title() for f in families]);ax.tick_params(length=0,pad=10)
 for i in range(8):
  for j in range(4):ax.text(j,i,f'{round(matrix[i,j]*8)}/8',ha='center',va='center',fontsize=15,fontweight='bold',color='white' if matrix[i,j]>.55 else '#142d40')
 fig.text(.04,.935,'Where do workflow decisions fail?',fontsize=25,fontweight='bold');fig.text(.04,.882,'Per-family exact label matches · first frozen repeat · 8 synthetic cases per family',fontsize=11,color='#637786')
 fig.text(.04,.075,'No statistical independence or generalization claim. Read the full methodology and every prediction in the repository.',fontsize=10,color='#637786')
 for suffix in ['png','svg']:fig.savefig(ROOT/f'assets/scenario-breakdown.{suffix}',dpi=170,metadata={'Creator':'Chinese Workflow Decision Bench'})
 plt.close(fig)
if __name__=='__main__':main()
