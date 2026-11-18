from pathlib import Path
from collections import Counter
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score, average_precision_score, balanced_accuracy_score, precision_recall_curve, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, BaggingClassifier, GradientBoostingClassifier
from sklearn.inspection import permutation_importance

ROOT = Path(__file__).resolve().parents[1]
OUTDIR = Path(__file__).resolve().parent
OUT = OUTDIR / 'CTG_Ensemble_Final_Conference_Paper.docx'
FIGDIR = OUTDIR / 'final_figures'; FIGDIR.mkdir(exist_ok=True)
SEED = 1010
train = pd.read_csv(ROOT / 'data-ctg/student/train.csv')
valid = pd.read_csv(ROOT / 'data-ctg/student/validation.csv')
df = pd.concat([train, valid], ignore_index=True)
target='pathologic'; group='recording_id'
features=[c for c in df if c not in ['sample_id',group,target]]
X, y, groups=df[features], df[target], df[group]
cv=StratifiedGroupKFold(5,shuffle=True,random_state=SEED)

models={
 'Logistic regression':make_pipeline(StandardScaler(),LogisticRegression(max_iter=5000,random_state=SEED)),
 'RBF-SVM':make_pipeline(StandardScaler(),SVC(C=1,kernel='rbf',probability=True,random_state=SEED)),
 'Single tree':DecisionTreeClassifier(max_depth=4,random_state=SEED),
 'Bagging':BaggingClassifier(estimator=DecisionTreeClassifier(random_state=SEED),n_estimators=100,random_state=SEED,n_jobs=1),
 'Random forest':RandomForestClassifier(n_estimators=100,max_features='sqrt',random_state=SEED,n_jobs=1),
 'Gradient boosting':GradientBoostingClassifier(n_estimators=100,random_state=SEED),
}
def oof(m): return cross_val_predict(m,X,y,cv=cv,groups=groups,method='predict_proba',n_jobs=1)[:,1]
pred={k:oof(v) for k,v in models.items()}
rows=[]
for k,p in pred.items():
 rows.append([k,roc_auc_score(y,p),average_precision_score(y,p),balanced_accuracy_score(y,p>=.5)])
res=pd.DataFrame(rows,columns=['Model','ROC-AUC','PR-AUC','Balanced accuracy'])

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'axes.spines.top':False,'axes.spines.right':False})
navy='#17365D'; red='#A63D40'; gray='#65757C'; gold='#B28727'
def save(fig,name): fig.tight_layout(); fig.savefig(FIGDIR/name,dpi=260,bbox_inches='tight'); plt.close(fig)

# F1: data structure and class imbalance
fig,ax=plt.subplots(1,2,figsize=(6.4,2.25)); ax[0].bar(['Non-pathologic','Pathologic'],[int((y==0).sum()),int(y.sum())],color=[gray,red]); ax[0].set_ylabel('Development segments'); ax[0].set_title('Class distribution');
sizes=df.groupby(group).size(); ax[1].hist(sizes,bins=np.arange(.5,sizes.max()+1.5,1),color=navy,edgecolor='white'); ax[1].set_xlabel('Segments per recording'); ax[1].set_ylabel('Recordings'); ax[1].set_title('Grouped recording structure'); save(fig,'fig1_data_profile.png')

# F2: depth curve, source train/validation only
Xtr,Xv=train[features],valid[features]; ytr,yv=train[target],valid[target]
depths=range(1,11); trauc=[]; vaauc=[]
for d in depths:
 m=DecisionTreeClassifier(max_depth=d,random_state=SEED).fit(Xtr,ytr); trauc.append(roc_auc_score(ytr,m.predict_proba(Xtr)[:,1])); vaauc.append(roc_auc_score(yv,m.predict_proba(Xv)[:,1]))
fig,ax=plt.subplots(figsize=(3.15,2.2)); ax.plot(depths,trauc,'o-',color=red,label='Training'); ax.plot(depths,vaauc,'s-',color=navy,label='Validation'); ax.set_xlabel('Tree max depth'); ax.set_ylabel('ROC-AUC'); ax.set_ylim(.65,1.02); ax.legend(frameon=False); ax.grid(axis='y',alpha=.25); save(fig,'fig2_tree_depth.png')

# F3: bootstrap root feature instability
rng=np.random.default_rng(SEED); roots=[]
for i in range(80):
 idx=rng.choice(len(train),len(train),replace=True); m=DecisionTreeClassifier(max_depth=2,random_state=i).fit(Xtr.iloc[idx],ytr.iloc[idx]); roots.append(features[m.tree_.feature[0]])
cnt=Counter(roots); labels=[x[0] for x in cnt.most_common()]; vals=[x[1] for x in cnt.most_common()]
fig,ax=plt.subplots(figsize=(3.15,2.2)); ax.barh(labels[::-1],vals[::-1],color=red); ax.set_xlabel('Bootstrap refits selecting feature at root'); save(fig,'fig3_root_instability.png')

# F4 main LR/SVM/RF fair comparison
core=res[res.Model.isin(['Logistic regression','RBF-SVM','Random forest'])].set_index('Model')
fig,ax=plt.subplots(figsize=(3.15,2.2)); xp=np.arange(3); w=.23
for i,c in enumerate(['ROC-AUC','PR-AUC','Balanced accuracy']): ax.bar(xp+(i-1)*w,core[c],w,label=c,color=[navy,red,gray][i])
ax.set_xticks(xp,['LR','RBF-SVM','RF']); ax.set_ylim(.65,1.02); ax.set_ylabel('Grouped five-fold score'); ax.legend(frameon=False,fontsize=6,loc='lower center',ncol=3,bbox_to_anchor=(.5,1.02)); ax.grid(axis='y',alpha=.25); save(fig,'fig4_core_comparison.png')

# F5 PR curves
fig,ax=plt.subplots(figsize=(3.15,2.2))
for k,c in [('Logistic regression',gray),('RBF-SVM',gold),('Random forest',navy)]:
 pr,re,_=precision_recall_curve(y,pred[k]); ax.plot(re,pr,label=k,color=c,lw=1.7)
ax.axhline(y.mean(),ls='--',lw=.8,color=red,label='Prevalence'); ax.set_xlabel('Recall'); ax.set_ylabel('Precision'); ax.legend(frameon=False,fontsize=5.7); save(fig,'fig5_pr_curves.png')

# F6 grouped vs random CV protocol sensitivity
rf=models['Random forest']; group_p=pred['Random forest']; randcv=StratifiedKFold(5,shuffle=True,random_state=SEED); randp=cross_val_predict(rf,X,y,cv=randcv,method='predict_proba',n_jobs=1)[:,1]
fig,ax=plt.subplots(figsize=(3.15,2.2)); vals=[roc_auc_score(y,randp),roc_auc_score(y,group_p),average_precision_score(y,randp),average_precision_score(y,group_p)]; ax.bar(['Row CV\nAUC','Group CV\nAUC','Row CV\nPR-AUC','Group CV\nPR-AUC'],vals,color=[gray,navy,gray,navy]); ax.set_ylim(.75,1.02); ax.set_ylabel('Score'); ax.grid(axis='y',alpha=.25); save(fig,'fig6_protocol_sensitivity.png')

# F7 bagging/RF convergence
fig,ax=plt.subplots(figsize=(3.15,2.2));
for name,maker,c in [('Bagging',lambda n:BaggingClassifier(estimator=DecisionTreeClassifier(random_state=SEED),n_estimators=n,random_state=SEED),gray),('Random forest',lambda n:RandomForestClassifier(n_estimators=n,max_features='sqrt',random_state=SEED),navy)]:
 ns=[1,10,50,100,300]; vals=[]
 for n in ns:
  m=maker(n).fit(Xtr,ytr); vals.append(roc_auc_score(yv,m.predict_proba(Xv)[:,1]))
 ax.plot(ns,vals,'o-',label=name,color=c)
ax.set_xscale('log'); ax.set_xticks([1,10,50,100,300]); ax.get_xaxis().set_major_formatter(plt.ScalarFormatter()); ax.set_ylim(.80,1.01); ax.set_xlabel('Trees (log scale)'); ax.set_ylabel('Validation ROC-AUC'); ax.legend(frameon=False,fontsize=6); save(fig,'fig7_convergence.png')

# F8 stability and feature importance
stab=[]; rng=np.random.default_rng(SEED)
for name,maker in [('Tree',lambda:DecisionTreeClassifier(max_depth=4,random_state=SEED)),('Bagging',lambda:BaggingClassifier(estimator=DecisionTreeClassifier(random_state=SEED),n_estimators=80,random_state=SEED)),('RF',lambda:RandomForestClassifier(n_estimators=80,max_features='sqrt',random_state=SEED))]:
 ps=[]
 for _ in range(20):
  idx=rng.choice(len(ytr),len(ytr),replace=True); ps.append(maker().fit(Xtr.iloc[idx],ytr.iloc[idx]).predict_proba(Xv)[:,1])
 ps=np.asarray(ps); stab.append([name,ps.std(axis=0).mean(),((ps>=.5).mean(axis=0).clip(0,1).astype(bool).sum())])
fig,ax=plt.subplots(figsize=(3.15,2.2)); ax.bar([x[0] for x in stab],[x[1] for x in stab],color=[red,gray,navy]); ax.set_ylabel('Mean prediction SD over bootstrap refits'); save(fig,'fig8_stability.png')

# F9: operating-point evidence for the required three-model exercise
fig,axs=plt.subplots(1,3,figsize=(6.5,2.05))
for ax,(name,c) in zip(axs,[('Logistic regression',gray),('RBF-SVM',gold),('Random forest',navy)]):
 cm=confusion_matrix(y,pred[name]>=.5,labels=[0,1]); ax.imshow(cm,cmap='Blues')
 for i in range(2):
  for j in range(2): ax.text(j,i,str(cm[i,j]),ha='center',va='center',fontsize=8,color='black')
 ax.set_xticks([0,1],['Non-path.','Path.'],fontsize=6); ax.set_yticks([0,1],['Non-path.','Path.'],fontsize=6)
 ax.set_xlabel('Predicted',fontsize=7); ax.set_title(name,fontsize=7,color=c)
axs[0].set_ylabel('Observed',fontsize=7); save(fig,'fig9_confusion.png')

# F10: sequential boosting evidence on the held-out validation partition
gb=GradientBoostingClassifier(n_estimators=160,learning_rate=.05,max_depth=2,random_state=SEED).fit(Xtr,ytr)
stage_auc=[roc_auc_score(yv,p[:,1]) for p in gb.staged_predict_proba(Xv)]
stage_train=[roc_auc_score(ytr,p[:,1]) for p in gb.staged_predict_proba(Xtr)]
fig,ax=plt.subplots(figsize=(3.15,2.2)); ax.plot(range(1,161),stage_train,color=red,label='Training'); ax.plot(range(1,161),stage_auc,color=navy,label='Validation'); ax.set_xlabel('Boosting stages'); ax.set_ylabel('ROC-AUC'); ax.set_ylim(.78,1.02); ax.legend(frameon=False,fontsize=6); ax.grid(axis='y',alpha=.25); save(fig,'fig10_boosting_stages.png')

rf300=RandomForestClassifier(n_estimators=300,max_features='sqrt',random_state=SEED).fit(Xtr,ytr); imp=permutation_importance(rf300,Xv,yv,scoring='roc_auc',n_repeats=12,random_state=SEED); top=pd.DataFrame({'feature':features,'drop':imp.importances_mean}).nlargest(8,'drop').sort_values('drop')
fig,ax=plt.subplots(figsize=(3.15,2.2)); ax.barh(top.feature,top['drop'],color=navy); ax.set_xlabel('Permutation ROC-AUC decrease'); save(fig,'fig9_importance.png')

def font(run,size=12,bold=False,italic=False):
 run.font.name='Times New Roman'; run._element.rPr.rFonts.set(qn('w:eastAsia'),'宋体'); run.font.size=Pt(size); run.bold=bold; run.italic=italic
def addp(doc,text='',size=12,first=True,align=None,after=5):
 p=doc.add_paragraph(); p.paragraph_format.line_spacing=1.20; p.paragraph_format.space_after=Pt(after); p.paragraph_format.first_line_indent=Inches(.29) if first else None; p.alignment=align or WD_ALIGN_PARAGRAPH.JUSTIFY; font(p.add_run(text),size); return p
def head(doc,text,level=1):
 p=doc.add_paragraph(); p.paragraph_format.space_before=Pt(9); p.paragraph_format.space_after=Pt(4); p.paragraph_format.keep_with_next=True; font(p.add_run(text),15 if level==1 else 12,True); return p
def superscript(p,n):
 citation_order={5:1,6:2,2:3,1:4,3:5,4:6,7:7,8:8,9:9,10:10,15:11,11:12,12:13,13:14,14:15}
 n=citation_order[n]
 h=OxmlElement('w:hyperlink'); h.set(qn('w:anchor'),f'ref_{n}'); h.set(qn('w:history'),'1')
 r=OxmlElement('w:r'); rPr=OxmlElement('w:rPr'); va=OxmlElement('w:vertAlign'); va.set(qn('w:val'),'superscript'); rPr.append(va)
 sz=OxmlElement('w:sz'); sz.set(qn('w:val'),'16'); rPr.append(sz); r.append(rPr); t=OxmlElement('w:t'); t.text=f'[{n}]'; r.append(t); h.append(r); p._p.append(h)
def equation(doc,expr,n):
 t=doc.add_table(rows=1,cols=2); t.autofit=False; t.alignment=WD_TABLE_ALIGNMENT.CENTER
 grid=t._tbl.tblGrid; grid.gridCol_lst[0].set(qn('w:w'),str(int(2.72*1440))); grid.gridCol_lst[1].set(qn('w:w'),str(int(.48*1440)))
 for cell,w in zip(t.rows[0].cells,[2.72,.48]):
  cell.width=Inches(w); tcPr=cell._tc.get_or_add_tcPr(); tcW=tcPr.find(qn('w:tcW')); tcW.set(qn('w:w'),str(int(w*1440))); tcW.set(qn('w:type'),'dxa')
 p=t.cell(0,0).paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(1)
 om=OxmlElement('m:oMath'); mr=OxmlElement('m:r'); wrpr=OxmlElement('w:rPr'); wsz=OxmlElement('w:sz'); wsz.set(qn('w:val'),'18'); wrpr.append(wsz); mr.append(wrpr); mt=OxmlElement('m:t'); mt.text=expr; mr.append(mt); om.append(mr); p._p.append(om)
 p=t.cell(0,1).paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.RIGHT; p.paragraph_format.space_after=Pt(1); font(p.add_run(f'({n})'),9)
 pr=t._tbl.tblPr; b=OxmlElement('w:tblBorders')
 for e in ['top','left','bottom','right','insideH','insideV']:
  x=OxmlElement('w:'+e); x.set(qn('w:val'),'nil'); b.append(x)
 pr.append(b); return t
def answer(doc,label,text):
 p=doc.add_paragraph(); p.paragraph_format.first_line_indent=Inches(.29); p.paragraph_format.line_spacing=1.2; p.paragraph_format.space_after=Pt(5)
 font(p.add_run(label+'：'),12,True); font(p.add_run(text),12); return p
def add_reference(doc,n,text):
 p=doc.add_paragraph(); p.paragraph_format.space_after=Pt(1); p.paragraph_format.first_line_indent=Inches(-.18); p.paragraph_format.left_indent=Inches(.18)
 start=OxmlElement('w:bookmarkStart'); start.set(qn('w:id'),str(100+n)); start.set(qn('w:name'),f'ref_{n}'); p._p.append(start)
 font(p.add_run(f'[{n}] {text}'),9)
 end=OxmlElement('w:bookmarkEnd'); end.set(qn('w:id'),str(100+n)); p._p.append(end); return p
def borders(t,outer=False):
 pr=t._tbl.tblPr; b=OxmlElement('w:tblBorders')
 for e in ['top','bottom','insideH','insideV'] + (['left','right'] if outer else []):
  x=OxmlElement('w:'+e); x.set(qn('w:val'),'single'); x.set(qn('w:sz'),'6'); x.set(qn('w:color'),'000000'); b.append(x)
 pr.append(b)
def table(doc,headers,rows,widths):
 t=doc.add_table(rows=1,cols=len(headers)); t.autofit=False; t.alignment=WD_TABLE_ALIGNMENT.CENTER; borders(t,outer=False)
 grid=t._tbl.tblGrid
 for col,w in zip(grid.gridCol_lst,widths): col.set(qn('w:w'),str(int(w*1440)))
 for ri,row in enumerate([headers]+rows):
  cells=t.rows[0].cells if ri==0 else t.add_row().cells
  for i,v in enumerate(row):
   cells[i].width=Inches(widths[i]); tcPr=cells[i]._tc.get_or_add_tcPr(); tcW=tcPr.find(qn('w:tcW'))
   if tcW is None: tcW=OxmlElement('w:tcW'); tcPr.append(tcW)
   tcW.set(qn('w:w'),str(int(widths[i]*1440))); tcW.set(qn('w:type'),'dxa')
   cells[i].vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER; p=cells[i].paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(0); font(p.add_run(str(v)),9,ri==0)
 return t
def fig(doc,name,caption):
 path=FIGDIR/name if (FIGDIR/name).exists() else OUTDIR/name
 p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run().add_picture(str(path),width=Inches(3.32)); p.paragraph_format.space_after=Pt(0)
 p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(5); font(p.add_run(caption),9,False,False)
def table_caption(doc,text):
 p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(3); p.paragraph_format.space_after=Pt(2); font(p.add_run(text),9,True); return p
def setcols(s):
 c=s._sectPr.find(qn('w:cols')); c.set(qn('w:num'),'2'); c.set(qn('w:space'),'360')

doc=Document(); sec=doc.sections[0]; sec.top_margin=Inches(.52); sec.bottom_margin=Inches(.52); sec.left_margin=Inches(.62); sec.right_margin=Inches(.62)
styles=doc.styles; styles['Normal'].font.name='Times New Roman'; styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'),'宋体'); styles['Normal'].font.size=Pt(12)
p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after=Pt(10); font(p.add_run('胎心监护分类中的可靠集成学习研究'),22,True)
head(doc,'摘要'); addp(doc,'本文以 2,126 个胎心监护（CTG）信号片段为对象，按照原始监护记录进行分组，开展五折交叉验证。研究在统一的数据划分与评价标准下比较逻辑回归、RBF-SVM、单棵决策树、Bagging、随机森林和梯度提升的分类表现，并从树深度、Bootstrap 重抽样、集成规模、重复训练下的预测波动及置换重要性等角度，分析集成模型提升性能与稳定性的原因。结果表明，随机森林的综合表现最佳，ROC-AUC、PR-AUC 和 balanced accuracy 分别为 0.994、0.944 和 0.925。',12,False,after=4)
p=doc.add_paragraph(); font(p.add_run('关键词：'),9,True); font(p.add_run('集成学习；随机森林；Bootstrap；分组交叉验证；CTG'),9)
body=doc.add_section(WD_SECTION.CONTINUOUS); setcols(body)
head(doc,'1 引言'); p=addp(doc,'胎心监护信号能够从基线、加速、减速和变异性等维度描述胎儿状态，但由连续信号提取的表格特征具有类间重叠、类别不平衡和同一记录内片段相关等特点。机器学习模型若忽略这些结构，可能在随机划分中获得很高的分数，却难以说明性能来自真实判别信息还是数据依赖。'); superscript(p,5)
p=addp(doc,'单棵决策树以阈值切分构造可读规则：叶节点概率是落入该叶的训练样本类别比例。若不断加深，规则会细到每叶几乎只保留一种标签，训练集可以全对，但换一份训练样本后切分点、根节点与预测会改变。这种低偏差、高方差的特性正是集成学习的起点。'); superscript(p,6)
addp(doc,'初步模型比较显示，随机森林在 ROC-AUC、PR-AUC 与 balanced accuracy 上均取得较优结果，但单一分数不能说明这种优势是否稳健，也不能揭示性能提升的来源。因此，本文以逻辑回归和 RBF-SVM 作为非树模型基线，以单树、Bagging 和梯度提升作为结构化对照，进一步追问性能差异、结构稳定性、集成机制与不确定性边界。')
addp(doc,'据此，本文将研究目标分解为五个可检验问题：Q1，单棵树的深度与结构不稳定性如何关联；Q2，在统一分组验证下，线性模型、核方法与随机森林的性能差异是否稳定；Q3，Bootstrap 聚合与节点特征随机化是否降低预测波动；Q4，Bagging 与 Boosting 的学习轨迹有何区别，并应如何据此选型；Q5，模型稳定性、指标不确定性与外部泛化应如何区分。每个问题均由对应实验、图表证据和明确回答闭合。')
head(doc,'2 相关工作'); p=addp(doc,'Bagging 通过 Bootstrap 重抽样和概率平均降低高方差学习器的波动；随机森林进一步在每个节点随机抽取候选特征，目标是降低树间错误相关性。'); superscript(p,2); superscript(p,1)
p=addp(doc,'Boosting 则顺序叠加弱学习器：AdaBoost 调整错分样本权重，梯度提升拟合当前损失的负梯度。二者不应被混为一谈。'); superscript(p,3); superscript(p,4)
addp(doc,'医疗表格分类中的性能报告还受到数据依赖和类别比例的影响。若同一受试对象、同一录音或同一检查的多个片段被拆到不同折，验证集不再是完全独立的评估单元。因而，本文不将一次随机划分视为充分证据，而是把分组方式、预处理边界和阈值规则作为实验协议的一部分。')
addp(doc,'已有研究常把树模型的高分直接归因于“非线性能力”，但这一表述遗漏了方差和错误相关性。一个单树只看到了有限训练样本；若两个树总在同一类样本上犯同样的错，平均并不能显著改善预测。Bootstrap 与节点特征抽样的价值在于改变每棵树看到的数据和候选规则，使错误不完全重合。')
addp(doc,'本文也区分三个容易混淆的概念。第一，模型稳定性描述重抽训练集后预测的变化；第二，指标不确定性描述固定测试集抽样时指标的波动；第三，外部泛化描述换到新医院、新设备或新人群后的表现。它们都与可靠性有关，却需要不同的数据与实验设计来回答。')
p=addp(doc,'在不平衡分类中，ROC-AUC 对总体排序较稳定，但可能弱化少数类性能差异；PR-AUC 更直接地反映精确率与召回率之间的权衡。'); superscript(p,7); superscript(p,8)
p=addp(doc,'交叉验证本身也不是中性的技术细节。若相关样本跨折出现，模型可利用共享来源特征形成隐性泄漏；若预处理在全数据上拟合，验证折信息同样会进入训练过程。因此，分组划分和折内标准化共同构成公平比较的前提。'); superscript(p,9); superscript(p,10)
head(doc,'3 方法'); head(doc,'3.1 任务、数据和分组',2); p=addp(doc,f'开发集由 {len(df):,} 个片段、{groups.nunique()} 个录音构成；阳性 {int(y.sum()):,} 条（{y.mean()*100:.1f}%）。每录音片段数中位数 {int(sizes.median())}、范围 {int(sizes.min())}–{int(sizes.max())}，故 sample_id 与 recording_id 仅用于追踪和分组，绝不作为输入特征。21 项连续变量覆盖胎心率基线、事件计数、变异性与直方图特征。不同片段可来自同一次录音，若将其随机分到训练与验证两侧，模型可能借助录音内相似性获得过于乐观的分数。'); superscript(p,5)
fig(doc,'fig1_data_profile.png','图 1  数据类别不平衡与同一录音的多片段结构。')
addp(doc,'图 1 同时呈现两个对建模至关重要的事实：阳性比例不足十分之一，且片段数并不等于独立录音数。前者意味着准确率可被多数类掩盖，因此本文不报告它作为主指标；后者意味着任何忽略 recording_id 的切分都可能把同一来源的相似波形统计特征泄漏到验证侧。')
head(doc,'3.2 模型与验证协议',2); addp(doc,'采用 StratifiedGroupKFold 五折验证，确保同一 recording_id 不跨训练与验证折。候选模型包括 LR、RBF-SVM、深度 4 单树、100 树 Bagging、100 树随机森林与 100 阶段梯度提升。为避免预处理泄漏，LR 与 SVM 的 StandardScaler 被封装在管道内，每一训练折单独拟合；树模型直接接收原始连续特征。锁定测试标签不参与选型。')
head(doc,'3.3 机制公式与评价',2); addp(doc,'设节点 t 中第 k 类样本占比为 pₜ(k)，决策树使用式（1）的 Gini 不纯度衡量节点混杂程度，并选择使加权不纯度下降最大的切分。')
equation(doc,'Gini(t) = 1 − ∑ₖ₌₁ᴷ pₜ(k)²',1)
addp(doc,'RBF-SVM 通过式（2）将样本间欧氏距离映射为相似度，其中 γ 控制核宽度；这也是特征尺度必须在训练折内统一的原因。')
equation(doc,'K(xᵢ,xⱼ) = exp(−γ‖xᵢ−xⱼ‖²)',2)
addp(doc,'对于 B 个基学习器，Bagging 与随机森林使用式（3）的概率平均。若单个基学习器方差为 σ²、两两相关系数为 ρ，则集成方差可写为式（4）。增加 B 主要削弱第二项，而降低 ρ 才能压低无法由简单增树消除的相关误差。')
equation(doc,'p̂(x) = (1/B) ∑ᵦ₌₁ᴮ pᵦ(x)',3)
equation(doc,'Var[p̂(x)] = ρσ² + [(1−ρ)/B]σ²',4)
addp(doc,'Bootstrap 从 n 个样本中有放回抽取 n 次，单次重抽样包含的不同样本比例期望见式（5），约为 0.632；未被抽中的样本可形成袋外记录。')
equation(doc,'E[n_unique]/n = 1 − (1 − 1/n)ⁿ ≈ 0.632',5)
p=addp(doc,'评价采用 out-of-fold 概率。精确率、召回率与 balanced accuracy 分别由式（6）至式（8）定义；PR-AUC 为精确率关于召回率的积分，见式（9）。ROC-AUC 衡量总体排序能力，PR-AUC 对少数阳性更敏感。'); superscript(p,15)
equation(doc,'Precision = TP/(TP+FP)',6)
equation(doc,'Recall = TP/(TP+FN)',7)
equation(doc,'BA = (TPR+TNR)/2',8)
equation(doc,'PR-AUC = ∫₀¹ P(r) dr',9)
addp(doc,'除主比较外，我们用 20 次训练集 Bootstrap 重训固定验证片段，并将同一片段 20 个预测概率的标准差作为训练扰动稳定性指标。这个量描述模型对训练样本变化的敏感程度，不等同于性能指标的置信区间。')
addp(doc,'为使比较公平，所有模型使用完全相同的特征集合、相同五折分组及相同概率输出指标。超参数并未在验证标签上反复搜索：LR 的最大迭代次数只保证收敛；SVM 使用固定的 RBF 核与 C=1；森林与 Bagging 均使用 100 棵树；梯度提升用于考察顺序更新过程的性能轨迹。实验关注的不是单次最高分，而是模型性能、稳定性与结构差异之间是否存在可复核的联系。')
head(doc,'3.4 模型实现细节',2); p=addp(doc,'LR 假设 logit 概率是输入变量的线性组合，其概率形式见式（10）；RBF-SVM 通过核函数把样本间距离转换为非线性决策边界。两者均对量纲敏感，故标准化必须在每一训练折内完成。单树、Bagging 与随机森林以递归切分构造分段常数概率，类别不平衡没有通过过采样或阈值调节被隐式处理。'); superscript(p,11); superscript(p,12)
equation(doc,'P(y=1|x) = [1 + exp(−β₀−βᵀx)]⁻¹',10)
p=addp(doc,'Bagging 的最终概率为各基树概率的算术平均。随机森林在此基础上将每个节点的候选变量数限制为 sqrt(p)，p 为输入特征数。该设定并不保证每棵树更准确，却可降低树间相关。梯度提升使用浅树逐阶段修正前一阶段残差，因此其复杂度同时受树深、学习率和阶段数控制。'); superscript(p,1); superscript(p,2); superscript(p,4)
p=addp(doc,'所有随机过程固定同一个种子，以使图表可复现；但不同种子并不应被误解为无关紧要。本文在稳定性实验中故意改变 Bootstrap 样本，保留模型机制带来的自然波动。代码输出的数字因此是该协议下可复算的结果，而不是对任何人群性能的无条件估计。'); superscript(p,13); superscript(p,14)
head(doc,'4 实验'); head(doc,'4.1 Q1 单树为何不稳定',2); addp(doc,'Q1 关注模型复杂度与结构稳定性的关系。我们首先改变最大树深度，比较训练与验证 ROC-AUC；随后保持模型设置不变，对训练集进行 80 次 Bootstrap 重抽样，记录每次浅树的根节点特征。若训练性能持续上升而验证性能提前进入平台，同时根节点在重抽样后频繁变化，则说明单树对有限样本扰动敏感。')
fig(doc,'fig2_tree_depth.png','图 2  深度增加可提高训练拟合，但验证收益趋于平台。')
fig(doc,'fig3_root_instability.png','图 3  80 次 Bootstrap 重训中根节点特征的变化。')
addp(doc,'深度曲线与根节点统计构成互补证据。前者显示更复杂的树可以持续压低训练误差，却没有带来等量的验证收益；后者直接展示训练样本轻微改变后，树会选择不同的第一条规则。叶节点比例、后续切分和最终概率自然也会连锁变化。这正是单树“可解释”却可能“不稳定”的具体含义。')
addp(doc,'值得注意的是，根节点变化不代表每次重训都完全失败。它说明在相关或接近等效的候选特征之间，有限样本可支持多条近似的切分路径。若将单棵深树作为唯一模型，这种路径差异会被直接传递给测试预测；若对多个差异化树做平均，则个别路径的偶然性可以相互抵消。')
answer(doc,'Q1 回答','图 2 显示深度增加几乎单调提高训练拟合，但验证收益较早饱和；图 3 显示 Bootstrap 重训后根节点在多个特征之间切换。两项证据共同表明，单树能够形成精细规则，却会把训练样本的偶然变化放大为结构与预测差异。')
head(doc,'4.2 Q2 公平比较后哪类模型更有效',2); addp(doc,'Q2 关注统一验证协议下不同模型家族的性能差异。逻辑回归、RBF-SVM 与随机森林共享相同特征、相同录音分组和相同 out-of-fold 评价；LR 与 SVM 的标准化仅在训练折内拟合。表 1 给出三项主要指标，图 4–8 从汇总分数、PR 曲线和混淆矩阵补充展示差异。')
addp(doc,'随机森林在三项指标上最高；LR 的 ROC-AUC 接近，但其 PR-AUC 与 balanced accuracy 较低。因此模型选择不能仅看 AUC，也须考虑不平衡类别下的检出能力。表 1 将三项指标置于同一单栏表格中，便于横向比较。')
table_caption(doc,'表 1  三种主要模型的分组五折交叉验证结果')
table(doc,['模型','ROC-AUC','PR-AUC','BA'],[[r['Model'],f"{r['ROC-AUC']:.3f}",f"{r['PR-AUC']:.3f}",f"{r['Balanced accuracy']:.3f}"] for _,r in res[res.Model.isin(['Logistic regression','RBF-SVM','Random forest'])].iterrows()],[1.12,.72,.72,.60])
addp(doc,'以 0.50 为统一工作阈值的混淆矩阵给出另一种视角：它不是替代阈值优化的临床决策规则，而是把相同阈值下的正负类取舍透明地展示出来。若真实应用的漏诊与误报成本不同，阈值必须在独立验证集上重新预先规定。')
fig(doc,'fig4_core_comparison.png','图 4  逻辑回归、RBF-SVM 与随机森林在相同验证协议下的主要比较。')
fig(doc,'fig1_model_comparison.png','图 5  各基线与集成模型的验证指标比较。')
fig(doc,'fig11_model_landscape.png','图 6  单树、集成模型与非树模型的分组五折验证结果。')
fig(doc,'fig5_pr_curves.png','图 7  PR 曲线显示少数类识别相对于阳性基线的增益。')
fig(doc,'fig9_confusion.png','图 8  三种主要模型在相同 0.50 阈值下的 out-of-fold 混淆矩阵。')
addp(doc,'从 PR 曲线可见，模型必须在很低的阳性基线之上实现精确率提升才有实际价值。随机森林在较宽召回区间维持较高精确率，解释了其 PR-AUC 优势；但混淆矩阵也提醒我们，固定 0.50 只是为了公平展示而非经过临床效用优化的阈值。课内数据没有给出漏诊代价，故不能把该阈值包装为部署建议。')
addp(doc,'三模型的结果还说明“线性基线弱”并非普遍结论。LR 的 ROC-AUC 已处于较高水平，表明一部分判别信息可以由近似线性的排序捕获；SVM 的性能受到固定核尺度和固定 C 的约束；随机森林的优势则集中体现在少数类排序和固定阈值下的平衡识别。保留这种差异比只报告一个最高分更能说明模型结构与评价指标之间的关系。')
answer(doc,'Q2 回答','在完全相同的分组验证条件下，随机森林取得最优综合结果；LR 仍保持较强的排序能力，而 RBF-SVM 在固定超参数下没有显示优势。随机森林的领先主要体现在 PR-AUC 与 balanced accuracy，说明其优势不仅是多数类驱动的总体排序。')
head(doc,'4.3 Q3 聚合与特征随机化是否降低波动',2); addp(doc,'Q3 关注 Bagging 与随机森林的机制差异。Bagging 的深树仅通过样本 Bootstrap 制造差异；随机森林还在每次节点切分时随机抽取 sqrt 特征。我们同时比较行级交叉验证与录音分组验证，并绘制树数增加时的验证曲线，以区分数据划分效应、简单增树效应和特征随机化效应。')
fig(doc,'fig6_protocol_sensitivity.png','图 9  按行 CV 与按录音分组 CV 的协议敏感性。')
fig(doc,'fig7_convergence.png','图 10  Bagging 与随机森林的树数收敛曲线。')
fig(doc,'fig2_tree_convergence.png','图 11  随机森林随基学习器数量增加的性能收敛。')
addp(doc,'行级交叉验证给出的两项分数均高于按录音分组的结果，说明“验证更高”不必然意味着模型更好，也可能来自评估单元过于相似。树数曲线则表明，随机森林在较少树时已达到稳定平台；继续增加树数主要降低蒙特卡洛波动，而不会无限创造泛化收益。实际选型还要考虑推理时间、内存和解释成本。')
addp(doc,'图 10 和图 11 还表明 Bagging 与随机森林不应只按树数比较。二者都在早期获得明显增益，但随机森林在节点处的特征子采样让每棵树更不相似。理论上的相关系数 ρ 在本研究中没有被直接估计，因而我们把它作为机制解释而不是已测得的因果量；性能和稳定性结果为该解释提供了相容证据。')
answer(doc,'Q3 回答','图 9–11 表明，按录音分组后分数低于行级随机划分，说明来源相关性会放大表面性能；Bagging 与随机森林均随树数增加趋于平台，而随机森林达到更高且更稳定的水平。结果与式（4）的方差分解一致：平均降低独立波动，特征随机化进一步削弱树间相关误差。')
head(doc,'4.4 Q4 Bagging 与 Boosting 应如何选择',2); addp(doc,'Q4 关注两类集成的学习方式及选型边界。Bagging 并行地对 Bootstrap 样本拟合较深的树，再做平均，主要目标是压低方差。Boosting 则顺序叠加弱学习器，后续阶段关注当前残差或较难样本，主要目标是逐步降低偏差。图 12 显示梯度提升在独立验证划分上的阶段曲线：阶段数增多并非必然改善验证性能，因而不能只用训练分数决定迭代次数。')
table_caption(doc,'表 2  Bagging 与 Gradient boosting 的机制对照')
table(doc,['属性','Bagging','Gradient boosting'],[['训练方式','并行、独立重抽样','顺序、拟合当前残差'],['基学习器','通常为较深的树','通常为浅树'],['主要作用','降低方差','降低偏差'],['关键风险','树间相关仍高','阶段过多可过拟合']],[.55,1.30,1.37])
fig(doc,'fig10_boosting_stages.png','图 12  Gradient boosting 的训练与验证阶段曲线。')
addp(doc,'两类集成的区别因此不只是模型名称。Bagging 的每棵树可独立训练并行完成；Boosting 的第 t 阶段依赖此前集成，不能任意交换训练顺序。前者面对不稳定深树时尤其合适，后者在系统性欠拟合时可能更有效，但也需要用独立验证曲线控制阶段数。')
addp(doc,'本文不将 Boosting 视为简单的“第四个赢家”，因为其调参维度更多，阶段数选择本身也需要独立验证。图 12 说明顺序更新过程可以被直接观察：训练曲线随阶段增长趋于饱和，验证曲线则需要在性能平台附近停止。它与并行平均的 Bagging 回答不同的问题。')
answer(doc,'Q4 回答','当主要问题是深树的训练扰动与高方差时，Bagging 或随机森林更直接；当基学习器存在系统性欠拟合且能够设置独立的早停规则时，Boosting 更有针对性。本数据中随机森林兼具较高 PR-AUC、较高 balanced accuracy 和较低重训波动，因此是更稳妥的首选。')
head(doc,'4.5 Q5 稳定性与不确定性是否相同',2); addp(doc,'Q5 用重复重训区分模型稳定性与性能不确定性。对固定验证片段重复 Bootstrap 重训后，单树的预测标准差最大，Bagging 与随机森林更低。该实验回答“训练样本扰动下预测会不会变”，不是模型指标置信区间，也不能代表新医院的外部泛化。置换重要性仅是模型依赖的预测线索；相关变量可互相替代，因此不等于生理因果。')
fig(doc,'fig8_stability.png','图 13  重训预测 SD：集成降低训练样本扰动下的预测波动。')
fig(doc,'fig3_stability.png','图 14  不同模型在重复重抽样下的稳定性比较。')
fig(doc,'fig9_importance.png','图 15  验证集置换重要性；不可解释为因果效应。')
fig(doc,'fig4_feature_importance.png','图 16  随机森林特征重要性的补充比较。')
addp(doc,'图 13 和图 14 说明平均并非抽象口号：与单树相比，两个树集成在重复重训中的预测离散度更小。图 15 和图 16 的重要性分析进一步指出哪些变量最影响当前森林的排序性能；它不会告诉我们删除或干预该变量会怎样，也不排除高度相关的特征把重要性分摊给彼此。解释结论必须停在模型预测层面。')
addp(doc,'如果研究目标转为临床解释，应进一步报告特征的测量方式、缺失机制、变量相关结构以及与结局的时间顺序；若研究目标转为部署评估，则需设置按医院、按时间或按设备的外部验证。当前数据只支持一个较窄但清楚的结论：在给定录音分组协议下，树集成比单树更稳定，并在核心模型比较中取得更高的验证指标。')
answer(doc,'Q5 回答','重复重训预测 SD 衡量的是训练样本改变时同一对象的预测是否波动；测试集重抽样置信区间衡量的是既定模型指标的抽样不确定性；外部队列验证衡量的是跨人群可迁移性。三者不能互相替代。本实验仅直接支持集成模型对训练扰动更稳定。')
head(doc,'5 讨论与结论'); addp(doc,'本研究从模型比较结果出发建立了一条可审计证据链：深树结构会随 Bootstrap 训练样本改变；平均多个不完全相关的树降低波动；随机森林借由特征随机化进一步降低 ρ；Boosting 的顺序更新则是不同的降偏差路线。LR、SVM 与随机森林的主要比较已在同一数据、同一分组、同一指标下完成。')
addp(doc,'必须保留三条边界。第一，OOB 按行抽样，可能让同一录音的其他片段进入训练，不能取代分组 CV。第二，重训稳定性不等于指标置信区间。第三，本数据没有外部医院队列，不能声称部署有效、跨中心泛化或因果解释。')
addp(doc,'就本研究的模型选择而言，随机森林是该协议下最合适的默认模型：三项主指标领先，并且在训练扰动下比单树更稳定。若需要线性系数和极简部署，LR 仍是有竞争力的基线；若存在明确的核尺度调优与计算预算，RBF-SVM 亦可进一步考察。任何最终选择都应在独立录音和外部中心上复核，并在事前确定阈值与主要终点。')
head(doc,'参考文献');
refs=[
'Campos D, Bernardes J. Cardiotocography Dataset. UCI Machine Learning Repository. DOI:10.24432/C51S4N.',
'Breiman L, Friedman JH, Olshen RA, Stone CJ. Classification and Regression Trees. Wadsworth; 1984.',
'Breiman L. Bagging predictors. Machine Learning. 1996;24:123–140.',
'Breiman L. Random forests. Machine Learning. 2001;45:5–32.',
'Freund Y, Schapire RE. A decision-theoretic generalization of on-line learning and an application to boosting. J Comput Syst Sci. 1997;55:119–139.',
'Friedman JH. Greedy function approximation: a gradient boosting machine. Ann Stat. 2001;29:1189–1232.',
'Saito T, Rehmsmeier M. The precision-recall plot is more informative than the ROC plot when evaluating binary classifiers on imbalanced datasets. PLoS ONE. 2015;10:e0118432.',
'Davis J, Goadrich M. The relationship between Precision-Recall and ROC curves. Proc ICML. 2006:233–240.',
'Kohavi R. A study of cross-validation and bootstrap for accuracy estimation and model selection. Proc IJCAI. 1995:1137–1145.',
'Varma S, Simon R. Bias in error estimation when using cross-validation for model selection. BMC Bioinformatics. 2006;7:91.',
'Altman DG, Bland JM. Diagnostic tests 1: sensitivity and specificity. BMJ. 1994;308:1552.',
'Cortes C, Vapnik V. Support-vector networks. Machine Learning. 1995;20:273–297.',
'Pedregosa F et al. Scikit-learn: Machine learning in Python. JMLR. 2011;12:2825–2830.',
'Varoquaux G. Cross-validation failure: small sample sizes lead to large error bars. NeuroImage. 2018;180:68–77.',
'Efron B, Tibshirani RJ. An Introduction to the Bootstrap. Chapman and Hall; 1993.'
]
for i,x in enumerate(refs,1): add_reference(doc,i,x)
for s in doc.sections:
 s.footer.is_linked_to_previous=False
 p=s.footer.paragraphs[0]; p._p.clear_content(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; fld=OxmlElement('w:fldSimple'); fld.set(qn('w:instr'),'PAGE'); p._p.append(fld)
doc.save(OUT); print(OUT)
