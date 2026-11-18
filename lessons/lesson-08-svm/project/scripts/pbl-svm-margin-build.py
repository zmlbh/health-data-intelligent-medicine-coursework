"""Lesson 9 only. Offline, deterministic analysis and four teaching documents.
Run from this lesson folder with Python containing numpy/pandas/sklearn/matplotlib/docx.
All outputs are confined to this course folder. Source data are bundled alongside.

Revision history
- v0 (2026-09-18, ChatGPT/Codex): first package; archived in planning/archive-v0-gpt-draft-20260918/.
- v1 (2026-09-18, takeover): completed the worksheet sections the skill requires (learning objectives,
  inquiry-question map, glossary, option-prediction table, directed reading guide, Packet A check,
  concept distinctions), added the real-data contrast table C3 and simulated validation counts in B2,
  replaced duplicated / generic prompts, and aligned the teacher plan. See review/takeover-gap-audit.md.
"""
from pathlib import Path
import json, sys, subprocess, hashlib, platform
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.datasets import make_moons
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.svm import SVC
from sklearn.metrics import confusion_matrix, balanced_accuracy_score
import sklearn
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT, WD_ROW_HEIGHT_RULE

ROOT=Path(__file__).resolve().parents[1]
AS=ROOT/'assets'/'pbl-svm-margin'
REVIEW=ROOT/'review'
SLUG='pbl-svm-margin'
SKILL=ROOT.parents[2]/'.codex'/'skills'/'pbl-ml-package'
FONT='Microsoft YaHei'
plt.rcParams.update({'font.sans-serif':[FONT,'DejaVu Sans'],'axes.unicode_minus':False,'font.size':10})
SOURCE='https://archive.ics.uci.edu/dataset/212/vertebral%2Bcolumn'
SVMREF='https://scikit-learn.org/stable/modules/svm.html'
RBFREF='https://scikit-learn.org/stable/auto_examples/svm/plot_rbf_parameters.html'
ISLR='https://www.statlearning.com/'
PHASE2_MINUTES=135
CN=['骨盆入射角','骨盆倾斜角','腰椎前凸角','骶骨倾角','骨盆半径','滑脱程度']
FEATURES=['pelvic_incidence','pelvic_tilt','lumbar_lordosis_angle','sacral_slope','pelvic_radius','degree_spondylolisthesis']
KN={'linear':'线性','poly':'二次多项式','rbf':'RBF'}
OPTIONS=[('L','采用线性核 SVM（边界是六维空间中的一个平面）：六项测量按训练集标准化，C 按“比较规则”中的选参规则选定后冻结。'),
         ('P','采用二次多项式核 SVM（边界可以是二次曲面；核设置固定为次数2、常数项1、gamma=1/6）：同样标准化，C 按选参规则选定后冻结。'),
         ('R','采用 RBF 核 SVM（边界可以随样本分布灵活弯曲）：同样标准化，C 与 gamma 按选参规则选定后冻结。'),
         ('D','暂缓：本轮不把 SVM 纳入比较，写明缺少哪一项证据或需要怎样修改方案。')]
PROBLEM='脊柱生物力学研究组要在下一轮离线算法比较中加入一个 SVM 基线，用六项测量预测已有的正常或异常标签，供研究人员比较方法。请在方案 L、P、R、D 中选择一个，用间隔几何、支持向量、软间隔、核选择和未见记录的证据说明选择；若验证表现不足或适用条件改变，指出应暂缓或修改的具体原因。'
RULES_TEXT=('比较规则（研究组预先写定）：①选参规则——每个核族只在验证集上选参数，取验证平衡准确率最高的一组，并列时取较小的 C、再取较小的 gamma；'
            '②合格条件——冻结的设置须满足验证平衡准确率不低于0.75，且异常、正常两类召回率都不低于0.65（召回率=该类记录中被判对的比例，平衡准确率=两类召回率的平均；这是本课离线比较的预设门槛，不是临床标准）；'
            '③冻结时点——看完 Packet C 后在总答案追踪表“T5 冻结方案”行冻结一个方案；Packet D 的测试结果只允许“保留 T5 方案”或“改为 D”，不能据测试结果换核或改参数。')
OBJECTIVES=[
('LO1','找到一个分类超平面；什么是 margin？','写出线性得分 f(x)=wᵀx+b，说明分类超平面 f(x)=0 的含义，并计算样本到超平面的几何距离。','几何与泛化'),
('LO2','为什么最大化 margin 有助于泛化？margin 越大，模型对扰动越稳健','用几何间隔解释“最大化间隔为什么可能有助于泛化”，并说明它只保护已有样本免受小扰动，不保证新样本的准确率。','几何与泛化'),
('LO3','Support vectors：决定分类边界的关键样本','从移除试验和边界图中识别支持向量，说明为什么只有支持向量决定边界。','支持向量'),
('LO4','Soft margin：允许少量分类错误；通过参数 C 控制误差和 margin 的权衡','计算合页损失，区分间隔违例与分类错误，用证据说明 C 怎样在间隔宽度与违例之间权衡。','软间隔'),
('LO5','kernel trick 是什么？linear kernel；polynomial kernel；RBF kernel','用内积与特征映射解释核技巧，比较线性、多项式和 RBF 核的边界，区分 gamma 与 C 的作用。','核方法'),
('LO6','参数敏感','在训练内标准化、验证选参、测试隔离的流程中说明参数敏感，并冻结一个可复现的方案。','参数选择'),
('LO7','适合中小样本；在高维数据中表现好；大数据上训练慢；可解释性有限','判断 SVM 在中小样本、高维和大样本研究中的适用性，并说明它的可解释性局限。','适用范围'),
('LO8','作业 用自己的话解释：为什么 SVM 不是简单地找一条“刚好分开两类”的线？','用自己的话解释“为什么 SVM 不是简单地找一条‘刚好分开两类’的线”（本讲作业原题）。','综合解释')]
CLUSTERS=[('几何与泛化',['分类超平面','决策得分','几何距离','间隔（margin）','最大间隔与扰动']),
          ('支持向量',['支持向量','边界只依赖支持向量']),
          ('软间隔',['软间隔','松弛量','合页损失','参数 C']),
          ('核方法',['内积与特征映射','核技巧','线性、多项式与 RBF 核','gamma']),
          ('参数选择',['训练内标准化','验证选参与测试隔离','平衡准确率与两类召回率','参数敏感']),
          ('适用范围',['中小样本与高维','大样本计算代价','可解释性局限','得分不是概率'])]
QS=[
dict(id='Q1',title='Q1 两条候选线的抗扰动差异',question='表 A2 的两条候选线都能分开六个样本：哪条更能容忍同样大小的扰动？表 A1 的脊柱变量能否直接套用这个结论？',learn='超平面、几何距离、最大间隔',objective_ids=['LO1','LO2'],concept_ids=['C1'],required_learning=['加权和、向量长度与垂直距离','规范化硬间隔与固定边界下的扰动保障'],student_action='计算两条候选线的最小几何距离并检验重缩放不变性；说明扰动保障为何不能直接搬到量纲不同的脊柱变量。',evidence_ids=['表 A1','表 A2'],release_after='A',minutes=16,tracker_row='T1 几何依据',student_output='Q1 距离计算表、Q1 几何与现实表及 T1',contribution_to_synthesis='说明偏好大间隔边界的几何依据及其泛化边界'),
dict(id='Q2',title='Q2 哪些样本约束边界',question='表 B1 中移除不同样本后，边界为什么有时不变、有时移动？',learn='支持向量',objective_ids=['LO3'],concept_ids=['C2'],required_learning=['支持向量是训练样本，不是特征','边界只由支持向量决定'],student_action='由边界位置和带宽推出间隔线，点名支持向量；比较两次移除；预测移除非支持向量的结果。',evidence_ids=['表 A2','表 B1'],release_after='B',minutes=10,tracker_row='T2 关键样本',student_output='Q2 支持向量表及 T2',contribution_to_synthesis='解释所选方案依赖哪些训练记录'),
dict(id='Q3',title='Q3 C 控制的究竟是哪一种代价',question='表 B2、图 B1 中改变 C，间隔宽度、违例与验证结果怎样变化？宽间隔能否直接支持“C 越小越好”？',learn='软间隔、合页损失、C',objective_ids=['LO4'],concept_ids=['C3'],required_learning=['软间隔目标与合页损失','间隔违例与分类错误的区别'],student_action='计算四个合页损失；比较 C 路径中的带宽、违例、支持向量与验证判对数，判断能否外推到脊柱数据。',evidence_ids=['图 S1','表 B2','图 B1'],release_after='B',minutes=15,tracker_row='T3 容错权衡',student_output='Q3 合页损失表、Q3 参数比较表及 T3',contribution_to_synthesis='给出选 C 原则及其需要的验证证据'),
dict(id='Q4',title='Q4 三种核怎样表示相似性',question='图 C1、表 C1 中三种核怎样改变二维边界？二次核为什么不必显式升维？',learn='核技巧、三种核、gamma',objective_ids=['LO5'],concept_ids=['C4'],required_learning=['内积、显式映射与核函数','RBF 相似度与 gamma'],student_action='核验二次核与三维映射内积一致；比较三核边界；计算两种 gamma 下的 RBF 相似度。',evidence_ids=['图 C1','表 C1'],release_after='C',minutes=20,tracker_row='T4 核的理由',student_output='Q4 二次核计算表、三核比较表、gamma 与 C 表及 T4',contribution_to_synthesis='用数学与图形说明何时值得选非线性核'),
dict(id='Q5',title='Q5 在脊柱数据上冻结方案',question='表 C2、表 C3、图 C2 的脊柱验证结果足以冻结 L、P、R 中的哪一个？缩放、C 与 gamma 怎样改变判断？',learn='标准化、验证选参、参数敏感',objective_ids=['LO4','LO6'],concept_ids=['C3','C5'],required_learning=['训练内标准化','验证选参、测试隔离与平衡准确率'],student_action='比较尺度对照、最宽带宽与大 gamma 的训练—验证差距，按合格条件逐核检查并冻结一个方案或暂缓。',evidence_ids=['表 S1','表 A1','表 C2','表 C3','图 C2'],release_after='C',minutes=18,tracker_row='T5 冻结方案',student_output='Q5 验证证据表及 T5',contribution_to_synthesis='指定可复现的冻结方案而非泛泛推荐 SVM'),
dict(id='Q6',title='Q6 是否保留冻结方案以及能迁移多远',question='表 D1、图 D1、表 D2：冻结方案能否保留？能迁移到哪些研究规模？',learn='泛化、优点与局限、作业原题',objective_ids=['LO2','LO7','LO8'],concept_ids=['C1','C6'],required_learning=['内部测试与几何稳健性不同','中小样本、高维、核计算代价和解释边界'],student_action='计算冻结方案的两类召回率，区分平均表现与预测翻转；判断两种迁移场景；回答作业原题。',evidence_ids=['表 D1','图 D1','表 D2'],release_after='D',minutes=22,tracker_row='T6 适用范围',student_output='Q6 测试复核表、迁移判断表、作业原题及 T6',contribution_to_synthesis='限制适用范围并整合所有核心概念')]
OTHER_MINUTES=dict(packet_a_check=6,evidence_card=8,concept_distinction=5,decision_matrix=5,memo=12)

def dump(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')

def savefig(name):
    plt.savefig(AS/name,dpi=190,bbox_inches='tight',facecolor='white'); plt.close()

def score(model,X,y):
    pr=model.predict(X); tn,fp,fn,tp=confusion_matrix(y,pr,labels=[0,1]).ravel()
    return dict(errors=int((pr!=y).sum()),ba=float(balanced_accuracy_score(y,pr)),tn=int(tn),fp=int(fp),fn=int(fn),tp=int(tp),sensitivity=float(tp/(tp+fn)),specificity=float(tn/(tn+fp)))

def fit_svm(X,y,kernel,C,gamma=1/6,scaled=True):
    s=SVC(kernel=kernel,C=C,gamma=gamma,degree=2,coef0=1,tol=1e-7)
    model=make_pipeline(StandardScaler(),s) if scaled else make_pipeline(s)
    model.fit(X,y); return model

def model_row(model,Xt,yt,Xv,yv,kernel,C,gamma,scaled):
    s=model[-1]; a=score(model,Xt,yt); b=score(model,Xv,yv)
    return dict(kernel=kernel,C=C,gamma=gamma,scaled=scaled,train_errors=a['errors'],train_ba=a['ba'],validation_ba=b['ba'],validation_sensitivity=b['sensitivity'],validation_specificity=b['specificity'],validation_tp=b['tp'],validation_tn=b['tn'],sv=int(s.n_support_.sum()),width=float(2/np.linalg.norm(s.coef_)) if kernel=='linear' else None)

def analyze():
    AS.mkdir(parents=True,exist_ok=True); REVIEW.mkdir(exist_ok=True)
    raw=pd.read_csv(AS/'source-data'/'column_2C.dat',sep=r'\s+',header=None,names=FEATURES+['class'])
    raw3=pd.read_csv(AS/'source-data'/'column_3C.dat',sep=r'\s+',header=None,names=FEATURES+['class'])
    X=raw[FEATURES].to_numpy(); y=(raw['class']=='AB').to_numpy(dtype=int)
    assert raw.shape==(310,7) and raw.isna().sum().sum()==0
    assert np.array_equal(X,raw3[FEATURES].to_numpy())
    assert np.array_equal(y,(raw3['class']!='NO').to_numpy(dtype=int))
    ids=np.arange(310); dev,test=train_test_split(ids,test_size=.2,stratify=y,random_state=9)
    train,val=train_test_split(dev,test_size=.25,stratify=y[dev],random_state=9)
    pd.DataFrame({'row_id':ids+1,'split':np.select([np.isin(ids,train),np.isin(ids,val)],['train','validation'],default='test')}).to_csv(AS/'split.csv',index=False)
    raw.to_csv(AS/'vertebral-column.csv',index=False)
    audit=[]
    for j,n in enumerate(CN):
        audit.append(dict(feature=n,n=310,missing=int(raw[FEATURES[j]].isna().sum()),min=float(X[:,j].min()),max=float(X[:,j].max()),train_sd=float(X[train,j].std(ddof=0)),unit='源页未注明单位',zero_count=int((X[:,j]==0).sum())))
    audit=pd.DataFrame(audit);audit.to_csv(AS/'packet-a-audit.csv',index=False)
    summary=dict(samples=310,features=6,normal=100,abnormal=210,missing=0,exact_duplicate_rows=int(raw.duplicated().sum()),duplicate_feature_rows=int(raw[FEATURES].duplicated().sum()),patient_identifier_available=False,train=186,validation=62,test=62,source=SOURCE,license='CC BY 4.0',source_sha256=hashlib.sha256((AS/'source-data'/'column_2C.dat').read_bytes()).hexdigest(),documentation_notes=['源页单位栏为空，不擅自添加单位。','三分类与二分类文件为同一批记录，不合并为620条。','存在负值和极端值；来源未提供合理范围，不把负值当缺失，不自动删除。','未见重复整行不等于已证实患者独立；发布数据没有患者标识可进一步核查。'],pelvic_identity_max_abs_error=float(np.max(abs(X[:,0]-X[:,1]-X[:,3]))))
    pd.DataFrame([dict(samples=310,features=6,normal=100,abnormal=210,missing=0)]).to_csv(AS/'dataset-summary.csv',index=False)
    dump(AS/'data-audit.json',summary)
    # Six completely specified geometric teaching points, not clinical records.
    toy=np.array([[-3,0],[-1,-1],[-1,1],[1,0],[3,-1],[3,1]],float); ty=np.array([0,0,0,1,1,1])
    pd.DataFrame({'id':['N1','N2','N3','P1','P2','P3'],'u':toy[:,0],'v':toy[:,1],'label':ty}).to_csv(AS/'packet-a-six-points.csv',index=False)
    deletions=[]
    # The first three rows are shown as 表 B1; 移除 P2 answers the Q2 prediction and appears only in the notebook and teacher plan.
    for label,remove in [('全部保留',None),('移除 N1',0),('移除 P1',3),('移除 P2',4)]:
        keep=np.ones(6,dtype=bool)
        if remove is not None:keep[remove]=False
        m=SVC(kernel='linear',C=1e4,tol=1e-9).fit(toy[keep],ty[keep]); w=m.coef_[0]; b=m.intercept_[0]
        deletions.append(dict(operation=label,remaining=int(keep.sum()),boundary_u=round(float(-b/w[0]),6)+0.0,width=float(2/np.linalg.norm(w)),shown_in_worksheet=remove!=4,support_ids=','.join(np.array(['N1','N2','N3','P1','P2','P3'])[keep][m.support_])))
    pd.DataFrame(deletions).to_csv(AS/'packet-b-removal.csv',index=False)
    # Two-dimensional simulation for the mandated classroom experiment.
    mx,my=make_moons(n_samples=120,noise=.20,random_state=9)
    md,mt=train_test_split(np.arange(120),test_size=.2,stratify=my,random_state=9)
    mtr,mv=train_test_split(md,test_size=.25,stratify=my[md],random_state=9)
    sc=StandardScaler().fit(mx[mtr]); z=sc.transform(mx)
    pd.DataFrame({'id':np.arange(1,121),'marker_a':mx[:,0],'marker_b':mx[:,1],'label':my,'split':np.select([np.isin(np.arange(120),mtr),np.isin(np.arange(120),mv)],['train','validation'],default='test')}).to_csv(AS/'simulation.csv',index=False)
    smods={}; sr=[]
    for kernel,C,gamma in [('linear',.01,1),('linear',1,1),('linear',100,1),('poly',1,1),('rbf',1,1),('rbf',100,10)]:
        m=SVC(kernel=kernel,C=C,gamma=gamma,degree=2,coef0=1,tol=1e-8).fit(z[mtr],my[mtr]);name=f'{kernel}-{C}-{gamma}';smods[name]=m
        f=(2*my[mtr]-1)*m.decision_function(z[mtr]);pv=m.predict(z[mv])
        sr.append(dict(name=name,kernel=kernel,C=C,gamma=gamma,errors=int((m.predict(z[mtr])!=my[mtr]).sum()),violations=int((f<1-1e-5).sum()),sv=int(m.n_support_.sum()),width=float(2/np.linalg.norm(m.coef_)) if kernel=='linear' else None,validation_correct=int((pv==my[mv]).sum()),validation_n=int(len(mv)),validation_ba=float(balanced_accuracy_score(my[mv],pv))))
    sim=pd.DataFrame(sr);sim.to_csv(AS/'packet-b-simulation.csv',index=False)
    gx,gy=np.meshgrid(np.linspace(-2.4,2.4,150),np.linspace(-2.6,2.5,150));grid=np.c_[gx.ravel(),gy.ravel()]
    def panel(ax,m,title,sv=False):
        zz=m.decision_function(grid).reshape(gx.shape)
        ax.contourf(gx,gy,zz>0,levels=[-.5,.5,1.5],colors=['#e3edf8','#f9e7db'])
        ax.contour(gx,gy,zz,levels=[-1,0,1],colors=['#6f8195','#101820','#6f8195'],linestyles=['--','-','--'],linewidths=[1,1.6,1])
        for c,mark,col in [(0,'o','#245b8f'),(1,'^','#ac542b')]:
            ix=mtr[my[mtr]==c];ax.scatter(z[ix,0],z[ix,1],s=13,c=col,marker=mark,label=f'模拟类 {c}')
        if sv:ax.scatter(m.support_vectors_[:,0],m.support_vectors_[:,1],s=48,facecolors='none',edgecolors='black',linewidths=.6)
        ax.set(xlabel='模拟形态指标 u（标准化，无量纲）',ylabel='模拟形态指标 v（标准化，无量纲）',title=title,xlim=(-2.4,2.4),ylim=(-2.6,2.5));ax.legend(fontsize=7,loc='upper right');ax.set_aspect('equal')
    fig,axs=plt.subplots(1,3,figsize=(10.8,3.8),constrained_layout=True)
    for ax,key,title in zip(axs,['linear-0.01-1','linear-100-1','rbf-1-1'],['左：线性核 C=0.01','中：线性核 C=100','右：RBF C=1，gamma=1']):panel(ax,smods[key],title)
    savefig('figure-s1.png')
    fig,axs=plt.subplots(1,3,figsize=(10.8,3.8),constrained_layout=True)
    for ax,key,title in zip(axs,['linear-0.01-1','linear-1-1','linear-100-1'],['C=0.01','C=1','C=100']):panel(ax,smods[key],title,True)
    savefig('figure-b1.png')
    fig,axs=plt.subplots(1,3,figsize=(10.8,3.8),constrained_layout=True)
    for ax,key,title in zip(axs,['linear-1-1','poly-1-1','rbf-1-1'],['线性核 C=1','二次多项式 C=1','RBF C=1，gamma=1']):panel(ax,smods[key],title,True)
    savefig('figure-c1.png')
    real=[]; models={}
    for kernel in ['linear','poly','rbf']:
        for C in [.01,.1,1,10,100]:
            for gamma in ([.01,.1,1,10] if kernel=='rbf' else [1/6]):
                m=fit_svm(X[train],y[train],kernel,C,gamma);real.append(model_row(m,X[train],y[train],X[val],y[val],kernel,C,gamma,True));models[(kernel,C,gamma)]=m
    un=fit_svm(X[train],y[train],'rbf',1,.1,False);real.append(model_row(un,X[train],y[train],X[val],y[val],'rbf',1,.1,False))
    results=pd.DataFrame(real);results.to_csv(AS/'packet-c-real-grid.csv',index=False)
    best=[];selected={}
    for kernel in ['linear','poly','rbf']:
        row=results[(results.kernel==kernel)&results.scaled].sort_values(['validation_ba','C','gamma'],ascending=[False,True,True]).iloc[0]
        best.append(row.to_dict());selected[kernel]=models[(kernel,row.C,row.gamma)]
    pd.DataFrame(best).to_csv(AS/'packet-c-selected.csv',index=False)
    # 表 C3: fixed contrasts from the same grid (no new fitting), chosen before looking at test data.
    def pick(kernel,C,gamma,scaled=True):
        g=1/6 if kernel=='linear' else gamma
        return results[(results.kernel==kernel)&np.isclose(results.C,C)&np.isclose(results.gamma,g)&(results.scaled==scaled)].iloc[0].to_dict()
    contrast=[dict(setting='线性，C=0.01',**pick('linear',.01,None)),dict(setting='线性，C=0.1',**pick('linear',.1,None)),dict(setting='线性，C=10',**pick('linear',10,None)),
              dict(setting='RBF，C=1，gamma=0.1，未标准化',**pick('rbf',1,.1,False)),dict(setting='RBF，C=1，gamma=0.1，已标准化',**pick('rbf',1,.1)),dict(setting='RBF，C=1，gamma=10，已标准化',**pick('rbf',1,10))]
    contrast=pd.DataFrame(contrast);contrast.to_csv(AS/'packet-c-contrast.csv',index=False)
    piv=results[(results.kernel=='rbf')&results.scaled].pivot(index='gamma',columns='C',values='validation_ba')
    fig,ax=plt.subplots(figsize=(7,3.6),constrained_layout=True);im=ax.imshow(piv,vmin=.5,vmax=1,cmap='Blues',aspect='auto')
    ax.set(xticks=range(len(piv.columns)),xticklabels=[f'{v:g}' for v in piv.columns],yticks=range(len(piv.index)),yticklabels=[f'{v:g}' for v in piv.index],xlabel='C',ylabel='gamma',title='RBF 在 62 条验证记录上的平衡准确率')
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):ax.text(j,i,f'{piv.iloc[i,j]:.3f}',ha='center',va='center',color='black' if piv.iloc[i,j]<.8 else 'white')
    fig.colorbar(im,ax=ax,label='平衡准确率');savefig('figure-c2.png')
    # Test used once for a fixed, predeclared comparison; no re-fit or re-selection.
    tests=[]
    for kernel,m in selected.items():tests.append(dict(kernel=kernel,**score(m,X[test],y[test])))
    td=pd.DataFrame(tests);td.to_csv(AS/'packet-d-test.csv',index=False)
    # Change only pelvic radius; do not break PI = PT + SS by independent angular noise.
    stress=[];rng=np.random.default_rng(91);eps=rng.normal(size=(200,len(test)))
    sd=X[train,4].std(ddof=0)
    for kernel,m in selected.items():
        clean=m.predict(X[test])
        for size in [0,.1,.2]:
            vals=[]
            for e in eps:
                pert=X[test].copy();pert[:,4]+=size*sd*e;pr=m.predict(pert)
                vals.append([balanced_accuracy_score(y[test],pr),float(np.mean(pr!=clean))])
            a=np.array(vals);stress.append(dict(kernel=kernel,sd_fraction=size,mean_ba=float(a[:,0].mean()),sd_ba=float(a[:,0].std()),flip=float(a[:,1].mean()),repetitions=200))
    st=pd.DataFrame(stress);st.to_csv(AS/'packet-d-stress.csv',index=False)
    fig,axs=plt.subplots(1,2,figsize=(8,3.2),constrained_layout=True)
    for k,label,col in [('linear','线性','#245b8f'),('poly','二次多项式','#76518e'),('rbf','RBF','#ac542b')]:
        r=st[st.kernel==k];axs[0].plot(r.sd_fraction,r.mean_ba,'o-',label=label,color=col);axs[1].plot(r.sd_fraction,r.flip,'o-',label=label,color=col)
    for ax in axs:ax.set_xlabel('骨盆半径噪声标准差 / 训练标准差');ax.legend(fontsize=8);ax.grid(alpha=.2)
    axs[0].set(ylabel='平均平衡准确率',ylim=(.45,1),title='固定模型的分类表现');axs[1].set(ylabel='相对无扰动预测的翻转比例',ylim=(0,.3),title='固定模型的预测变化');savefig('figure-d1.png')
    pd.DataFrame([dict(scenario='脊柱主案例',n=310,p=6,full_gram_mb=310**2*8/1e6),dict(scenario='基因表达迁移',n=80,p=2000,full_gram_mb=80**2*8/1e6),dict(scenario='多中心大表迁移',n=100000,p=6,full_gram_mb=100000**2*8/1e6)]).to_csv(AS/'packet-d-scale.csv',index=False)
    dump(AS/'environment.json',dict(python=platform.python_version(),numpy=np.__version__,sklearn=sklearn.__version__,seed=9,measurement_seed=91))
    return dict(raw=raw,audit=audit,summary=summary,toy=toy,deletions=deletions,sim=sim,grid=results,best=best,contrast=contrast,test=td,stress=st)

EVIDENCE_ITEMS=[('表 S1','S1','dataset-summary.csv','主案例310条记录、六项特征、固定划分与比较计划；启动阶段只有规模和任务事实。'),
    ('图 S1','S1','figure-s1.png','模拟样本120个，图示72个训练点；三格分别为线性 C=0.01、线性 C=100、RBF。'),
    ('表 A1','A','packet-a-audit.csv','六个变量，每变量310个非缺失值，最小值与最大值；源页单位未注明。'),
    ('表 A2','A','packet-a-six-points.csv','六个完全指定的模拟点，无量纲，标签−1/+1。'),
    ('表 B1','B','packet-b-removal.csv','三次近似硬间隔重拟合（全部保留、移除 N1、移除 P1）。'),
    ('表 B2','B','packet-b-simulation.csv','同72个模拟训练点、24个验证点，三个 C 的误差、违例、支持向量、带宽与验证判对数。'),
    ('图 B1','B','figure-b1.png','三组线性 C 边界，圈标支持向量。'),
    ('图 C1','C','figure-c1.png','同72个训练点，三种核，C=1。'),
    ('表 C1','C','packet-b-simulation.csv','三核模型的训练错误、支持向量与24个模拟验证点判对数。'),
    ('表 C2','C','packet-c-selected.csv','186训练、62验证；各核族按选参规则选出的设置及两类召回率。'),
    ('表 C3','C','packet-c-contrast.csv','同一划分下六组固定对照：线性 C 路径三点、RBF 尺度对照两点、RBF 大 gamma 一点。'),
    ('图 C2','C','figure-c2.png','脊柱 RBF 验证网格，20格。'),
    ('表 D1','D','packet-d-test.csv','62条测试记录（异常42、正常20）；三核族冻结模型各评一次，从未用于选参。'),
    ('图 D1','D','figure-d1.png','只扰动骨盆半径，每强度200次，模型保持固定。'),
    ('表 D2','D','packet-d-scale.csv','真实规模与两项设定迁移情境，完整核矩阵大小为算术示例。')]

def make_design():
    items=EVIDENCE_ITEMS
    analyses=[]
    for q in QS:
        es=[i for i in items if i[0] in q['evidence_ids']]
        arts=sorted({i[2] for i in es})
        extra={'Q1':['dataset-summary.csv','data-audit.json','vertebral-column.csv','split.csv','simulation.csv'],'Q5':['packet-c-real-grid.csv','environment.json'],'Q6':['packet-d-stress.csv']}.get(q['id'],[])
        analyses.append(dict(id='A'+q['id'][1:],objective_ids=q['objective_ids'],inquiry_question_ids=[q['id']],question=q['question'],domain='similarity_distance' if q['id']=='Q1' else 'model_behavior' if q['id'] in ['Q2','Q3','Q4'] else 'validation_robustness',method=q['student_action'],applicability=q['contribution_to_synthesis'],artifacts=sorted(set(arts+extra)),packet=q['release_after'],interpretation_boundary='几何、模拟和历史内部比较不证明临床或因果结论。',notebook_ref=q['id']))
    coverage=[]
    for lo in OBJECTIVES:
        q=[q for q in QS if lo[0] in q['objective_ids']]
        coverage.append(dict(objective_id=lo[0],concept_cluster_ids=sorted({c for z in q for c in z['concept_ids']}),inquiry_question_ids=[z['id'] for z in q],analysis_ids=['A'+z['id'][1:] for z in q],required_learning=[s for z in q for s in z['required_learning']],student_output='；'.join(z['student_output'] for z in q),worksheet_location=' / '.join('Phase 2 '+z['id'] for z in q),synthesis_use='；'.join(z['contribution_to_synthesis'] for z in q)+('；研究备忘录引用 Q6 作业原题' if lo[0]=='LO8' else ''),assessment_evidence=lo[2]))
    clusters=[dict(id='C'+str(i+1),name=n,objective_ids=[l[0] for l in OBJECTIVES if l[3]==n],concepts=cs) for i,(n,cs) in enumerate(CLUSTERS)]
    clusters[-1]['objective_ids'].append('LO8')
    qs=[{k:v for k,v in q.items() if k not in ('title','learn')} for q in QS]
    d=dict(study_goal='理解并审慎选择SVM边界，完成总纲二维课堂练习及解释作业。',
        authorization='2026-09-17用户要求按最新版技能复核后直接生成课件；2026-09-18用户要求接手未完成的学习单，按技能补全、试填并修正。',
        learning_objectives=[dict(id=l[0],source_excerpt=l[1],observable_outcome=l[2]) for l in OBJECTIVES],concept_clusters=clusters,
        decision_problem=PROBLEM,driving_question=PROBLEM,entry_type='direct_problem',
        problem_architecture=dict(overarching_problem=PROBLEM,downstream_use='研究人员下一轮离线算法比较的SVM基线',decision_options=[a+' '+b for a,b in OPTIONS],inquiry_questions=qs),
        course_coverage=coverage,
        data_context=dict(dataset_name='UCI Vertebral Column',source=SOURCE,task='binary classification',observation_unit='发布表中一条受试者测量记录，缺少可核查重复受试者的标识',variable_roles=dict(features=FEATURES,metadata=[]),grouping_fields=[],target='AB=1, NO=0'),
        analyses=analyses,split_plan=dict(required=True,unit='row',rationale='研究泛化与验证选参；186/62/62，分层且固定seed9；无患者ID，独立性不可再核查。'),
        packets={p:dict(purpose=pur,reveals=rev,withholds=hid) for p,pur,rev,hid in [('A','几何与数据语义',['变量范围与记录核验','六点输入'],['移除试验','核参数验证','测试']),('B','支持向量与容错',['移除试验','模拟C路径及验证判对数'],['核比较','脊柱验证','测试']),('C','核选择和冻结',['三核图','脊柱验证选参','参数与尺度对照','RBF验证网格'],['测试和扰动']),('D','综合和边界',['测试','扰动','规模迁移'],[])]},
        boundaries=['教学研究，不用于临床诊断、部署或患者护理。','模拟形态坐标不是真实细胞测量。','测试不能用于事后重新选择核。'],
        evidence_items=[dict(id=i,packet=p,artifacts=[a],context=c) for i,p,a,c in items],
        syllabus_tasks=[dict(source_excerpt=t,worksheet_location=loc) for t,loc in [('课堂练习 用二维模拟数据展示：不同 C 对分类边界的影响','Phase 1 启动观察表第1行（图 S1 左、中图）；Phase 2 Q3 深化'),('linear kernel 与 RBF kernel 的区别','Phase 1 启动观察表第3行（图 S1 中、右图）；Phase 2 Q4 深化'),('margin 如何变化','Phase 1 启动观察表第2行；Phase 2 Q1、Q3'),('作业 用自己的话解释：为什么 SVM 不是简单地找一条“刚好分开两类”的线？','Phase 2 Q6 作业原题；研究备忘录只引用')]],
        time_budget=dict(phase1=45,phase2=PHASE2_MINUTES,phase3=45,module_minutes=sum(q['minutes'] for q in QS),other_minutes=OTHER_MINUTES))
    dump(AS/'analysis-design.json',d);return d

# ---------------------------------------------------------------- document helpers
def font(run,size=10.5,bold=False,color='000000'):
    run.font.name='Arial';run.font.size=Pt(size);run.font.bold=bold;run.font.color.rgb=RGBColor.from_string(color)
    run._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),FONT)

def newdoc(kind,header_kind):
    d=Document();s=d.sections[0];s.page_width=Inches(8.268);s.page_height=Inches(11.693)
    s.top_margin=s.bottom_margin=s.left_margin=s.right_margin=Inches(.65);s.header_distance=s.footer_distance=Inches(.28)
    for name,size in [('Normal',10.5),('Title',23),('Subtitle',11),('Heading 1',16),('Heading 2',12),('Heading 3',11),('Caption',9)]:
        st=d.styles[name];st.font.name='Arial';st.font.size=Pt(size);st.font.color.rgb=RGBColor(0,0,0)
        st.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),FONT)
        st.paragraph_format.space_after=Pt(5);st.paragraph_format.line_spacing=1.15
        if name.startswith('Heading'):st.paragraph_format.keep_with_next=True;st.paragraph_format.space_before=Pt(10)
        for border in list(st.element.iter(qn('w:pBdr'))):border.getparent().remove(border)
    d.styles['Normal'].paragraph_format.widow_control=True
    hp=s.header.paragraphs[0];font(hp.add_run('AI for Biomedical Data Science     第9讲     '+header_kind),8,color='555555')
    p=s.footer.paragraphs[0];p.alignment=2
    font(p.add_run('教学研究用途  •  '),9);f=OxmlElement('w:fldSimple');f.set(qn('w:instr'),'PAGE');p._p.append(f)
    p=d.add_paragraph('第9讲 SVM 与 Margin',style='Title');p.alignment=1
    p=d.add_paragraph(kind,style='Subtitle');p.alignment=1
    return d

def para(d,text,style=None):
    p=d.add_paragraph(text,style);p.paragraph_format.keep_together=True;return p

def prompt(d,text):
    # Prompt card: bold the short title before the first full-width colon so students can scan for tasks.
    head,sep,body=text.partition('：')
    p=d.add_paragraph()
    if sep and len(head)<=34:
        font(p.add_run(head+sep),10.5,True);font(p.add_run(body),10.5)
    else:font(p.add_run(text),10.5)
    p.paragraph_format.keep_with_next=True;p.paragraph_format.keep_together=True
    return p

SUCCESSORS=('w:tabs','w:suppressAutoHyphens','w:kinsoku','w:wordWrap','w:overflowPunct','w:topLinePunct','w:autoSpaceDE','w:autoSpaceDN','w:bidi','w:adjustRightInd','w:snapToGrid','w:spacing','w:ind','w:contextualSpacing','w:mirrorIndents','w:suppressOverlap','w:jc','w:textDirection','w:textAlignment','w:textboxTightWrap','w:outlineLvl','w:divId','w:cnfStyle','w:rPr','w:sectPr','w:pPrChange')

def shade(p,fill,rule=None):
    # w:pBdr and w:shd must sit before spacing/indent/justification children of w:pPr.
    pPr=p._p.get_or_add_pPr()
    if rule:
        bdr=OxmlElement('w:pBdr');left=OxmlElement('w:left')
        for k,v in [('val','single'),('sz','18'),('space','6'),('color',rule)]:left.set(qn('w:'+k),v)
        bdr.append(left);pPr.insert_element_before(bdr,'w:shd',*SUCCESSORS)
    sh=OxmlElement('w:shd');sh.set(qn('w:val'),'clear');sh.set(qn('w:fill'),fill);pPr.insert_element_before(sh,*SUCCESSORS)
    return p

def card(d,text):
    # Tracker-update card: no answer box of its own; shaded with a left rule so it is not mistaken for body text.
    p=prompt(d,text);p.paragraph_format.keep_with_next=False
    return shade(p,'F2F5F9','5B7FA6')

def info(d,text):
    p=para(d,text);p.paragraph_format.keep_with_next=True
    for r in p.runs:font(r,9,color='333333')
    return shade(p,'EEF3E8')

def heading(d,text,level=1,new=False):
    p=d.add_heading(text,level)
    if new:p.paragraph_format.page_break_before=True
    return p

def table(d,headers,rows,widths=None,answer=False,height=.36,size=None):
    t=d.add_table(rows=1,cols=len(headers));t.style='Table Grid';t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
    widths=widths or [6.968/len(headers)]*len(headers)
    for i,w in enumerate(widths):t.columns[i].width=Inches(w)
    for c,s in zip(t.rows[0].cells,headers):c.text=str(s)
    for row in rows:
        cells=t.add_row().cells
        for c,v in zip(cells,row):c.text='' if v is None else str(v)
    pr=t._tbl.tblPr;b=OxmlElement('w:tblBorders')
    for side in ['top','left','bottom','right','insideH','insideV']:
        x=OxmlElement('w:'+side);x.set(qn('w:val'),'single');x.set(qn('w:sz'),'4');x.set(qn('w:color'),'BFBFBF');b.append(x)
    pr.append(b)
    for ri,row in enumerate(t.rows):
        trpr=row._tr.get_or_add_trPr();trpr.append(OxmlElement('w:cantSplit'))
        if ri==0:trpr.append(OxmlElement('w:tblHeader'))
        if answer and ri>0:row.height=Inches(height);row.height_rule=WD_ROW_HEIGHT_RULE.AT_LEAST
        for ci,c in enumerate(row.cells):
            c.width=Inches(widths[ci]);c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cp=c._tc.get_or_add_tcPr();mar=OxmlElement('w:tcMar')
            for side in ['top','left','bottom','right']:
                el=OxmlElement('w:'+side);el.set(qn('w:w'),'70');el.set(qn('w:type'),'dxa');mar.append(el)
            cp.append(mar)
            if ri==0:
                sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'DCE8F2');cp.append(sh)
            for p in c.paragraphs:
                p.paragraph_format.space_after=Pt(1);p.paragraph_format.space_before=Pt(1);p.paragraph_format.keep_together=True;p.paragraph_format.line_spacing=1.05
                # keep short tables in one piece; long ones may break between rows (rows never split)
                if ri==0 or (len(rows)<=8 and ri<len(rows)):p.paragraph_format.keep_with_next=True
                for run in p.runs:font(run,size or (9 if len(headers)>5 else 9.5 if len(headers)>3 else 10),ri==0)
    return t

def answer(d,text,rows,headers=('填写项目','个人作答'),widths=(1.45,5.518),height=.55):
    prompt(d,text)
    return table(d,list(headers),rows,list(widths),True,height)

def _memo_tall(d):
    # evidence-and-reasoning is the long paragraph of the memo
    d.tables[-1].rows[2].height=Inches(2.2)

def caption(d,label,text):
    p=para(d,label+'  '+text,'Caption');p.paragraph_format.keep_with_next=True

def picture(d,name,label,text,width=6.8):
    caption(d,label,text);p=d.add_paragraph();p.paragraph_format.keep_together=True;p.add_run().add_picture(str(AS/name),width=Inches(width))

def eq(d,text):
    # Editable native Office math, linear notation for compact scalar formulas.
    p=d.add_paragraph();p.alignment=1;p.paragraph_format.keep_with_next=True
    om=OxmlElement('m:oMath');r=OxmlElement('m:r');t=OxmlElement('m:t');t.text=text;r.append(t);om.append(r);p._p.append(om)
    return p

def fmt(v):return f'{v:.3f}'
def frac(k,n):return f'{k}/{n}（{k/n:.3f}）'

# ---------------------------------------------------------------- evidence (single source for worksheet and evidence pack)
def ev_S1(d,a):
    caption(d,'表 S1','启动事实。每行是研究组告知的一项条件；数据来自 UCI Vertebral Column（脊柱数据集），一条记录是发布表中一名受试者的一组测量。服务 Q1、Q5。')
    table(d,['事实','数值或说明'],[['样本与变量','310条记录，每条6项连续测量（骨盆与腰椎的四个角度、骨盆半径、滑脱程度）；标签另列。'],['标签','正常100条、异常210条；异常由两种病理类别合并而成。'],['数据划分','已固定分层划分：训练186条、验证62条、测试62条；测试记录在 Packet D 之前不开放。'],['比较计划','下一轮还将比较第8讲学过的逻辑回归（logistic regression）等方法；研究组要求所选基线可复现，并能向合作者说明主要参数。']],[1.4,5.568])

def ev_S1fig(d,a):
    picture(d,'figure-s1.png','图 S1','总纲课堂练习。每点是人为模拟的二维样本（双月形模拟，固定种子9，噪声尺度0.20，共120点），u、v 无量纲，不代表真实细胞或脊柱指标；图中画出72个训练点（两类各36），全部按训练集均值与标准差标准化。背景色为判定区域，实线 f=0 是分类边界，虚线是 f=+1 与 f=−1。左图、中图只改变线性核的 C，右图为 RBF 核。服务 Q1、Q3、Q4。')

def ev_A1(d,a):
    caption(d,'表 A1','变量范围与记录核验。每行一个变量，各有310个非缺失值；数值来自 UCI 脊柱数据发布表的原始取值。源页未注明计量单位，表内保持原值，未删除负值或极端值。服务 Q1、Q5。')
    table(d,['变量','非缺失数','最小值','最大值','缺失数'],[[r.feature,310,f'{r.min:.2f}',f'{r.max:.2f}',0] for r in a['audit'].itertuples()],widths=[2.2,1.1,1.2,1.2,1.268])
    para(d,f"记录核验：官方称正常100条、异常210条，本地计数一致；异常由椎间盘突出60条与脊椎滑脱150条合并而成。完全相同的整行记录 {a['summary']['exact_duplicate_rows']} 条；发布数据没有受试者编号，无法进一步核查同一受试者是否出现多次。二分类文件与三分类文件的六项测量逐行相同，是同一批记录，不能合并成620条。")

def ev_A2(d,a):
    caption(d,'表 A2','六点几何练习。每行一个人为构造的样本，输入 u、v 无量纲；标签 y 取−1（负类）或+1（正类）。它们只用于精确计算边界几何，与真实脊柱记录无对应关系。服务 Q1、Q2。')
    table(d,['样本','u','v','标签 y'],[['N1',-3,0,-1],['N2',-1,-1,-1],['N3',-1,1,-1],['P1',1,0,1],['P2',3,-1,1],['P3',3,1,1]])
    para(d,'候选线 a：u=0，得分 fₐ(x)=u。候选线 b：u=0.8，得分 fᵦ(x)=u−0.8。两条线都把得分为正的样本判为正类，都能把表 A2 的六个样本全部分对。它们是给定的候选边界，系数没有按 SVM 的 ±1 约定重新缩放。')

def ev_B1(d,a):
    caption(d,'表 B1','移除试验。起点为表 A2 的6个样本；每行删去一个样本（或不删）后重新拟合线性 SVM（C=10000，近似硬间隔，不缩放）。三次拟合的边界都是竖直线“u=常数”（v 的系数为0），“边界位置 u”即该常数；带宽是两条间隔线之间的距离 2/‖w‖，以 u 坐标计。服务 Q2。')
    table(d,['操作','剩余样本数','边界位置 u','带宽'],[[r['operation'],r['remaining'],fmt(r['boundary_u']),fmt(r['width'])] for r in a['deletions'] if r['shown_in_worksheet']])

def ev_B2(d,a):
    caption(d,'表 B2','二维模拟的线性核 C 路径。每行一次拟合：同72个训练点（两类各36，已按训练集标准化）；另有24个验证点（两类各12）不参与拟合，只用于计分。训练错误=类别被判错的训练点；间隔违例=y·f(x)<1 的训练点（容差10⁻⁵），包含判对但落入虚线带的点；支持向量按求解器的非零系数统计；带宽=2/‖w‖，无量纲。服务 Q3。')
    t=a['sim'][a['sim'].kernel=='linear']
    table(d,['C','训练错误数（/72）','间隔违例数（/72）','支持向量数（/72）','带宽','验证判对数（/24）'],[[f'{r.C:g}',r.errors,r.violations,r.sv,fmt(r.width),r.validation_correct] for r in t.itertuples()],[.8,1.25,1.25,1.25,.968,1.45])

def ev_B1fig(d,a):
    picture(d,'figure-b1.png','图 B1','与表 B2 相同的72个训练点、尺度与参数（从左到右 C=0.01、1、100）。实线 f=0，虚线 f=±1，空心黑圈为支持向量；三格坐标尺度相同。服务 Q3。')

def ev_C1fig(d,a):
    picture(d,'figure-c1.png','图 C1','三种核在同72个模拟训练点上的拟合，均取 C=1。二次多项式核：次数2、gamma=1、常数项1；RBF：gamma=1。实线 f=0，虚线 f=±1，空心黑圈为支持向量。核 SVM 的虚线是得分等高线，不是原始平面上的等距离线。服务 Q4。')

def ev_C1(d,a):
    caption(d,'表 C1','三种核在同一模拟数据上的结果。每行一种核，参数同图 C1；训练72点、验证24点（两类各12，不参与拟合）。模拟坐标不是脊柱或临床指标。服务 Q4。')
    s=a['sim'][(a['sim'].C==1)&(a['sim'].gamma==1)]
    table(d,['核','训练错误数（/72）','支持向量数（/72）','验证判对数（/24）'],[[KN[r.kernel],r.errors,r.sv,r.validation_correct] for r in s.itertuples()])

def ev_C2(d,a):
    caption(d,'表 C2','各核族按选参规则选出的设置（脊柱数据）。每行一个核族在预定参数组合中验证平衡准确率最高的一组（并列时取较小 C、再取较小 gamma）。训练186条（异常126、正常60），验证62条（异常42、正常20）；六项测量按训练集均值与标准差标准化。预定参数组合：C 取0.01、0.1、1、10、100；二次多项式核固定次数2、gamma=1/6、常数项1；RBF 的 gamma 取0.01、0.1、1、10。召回率写成“判对数/该类总数（比值）”。服务 Q5。')
    rows=[[KN[r['kernel']],f"{r['C']:g}",'不适用' if r['kernel']=='linear' else ('1/6' if r['kernel']=='poly' else f"{r['gamma']:g}"),int(r['sv']),fmt(r['train_ba']),fmt(r['validation_ba']),frac(int(r['validation_tp']),42),frac(int(r['validation_tn']),20)] for r in a['best']]
    table(d,['核族','C','gamma','支持向量数（/186）','训练平衡准确率','验证平衡准确率','验证异常召回','验证正常召回'],rows,[.95,.45,.6,.85,.85,.85,1.2,1.218])

def ev_C3(d,a):
    caption(d,'表 C3','参数与尺度对照（脊柱数据）。每行一次拟合，训练186条、验证62条同表 C2；除注明“未标准化”的一行外，六项测量均按训练集标准化。这些设置在查看任何测试记录之前固定。线性带宽=2/‖w‖，只对线性核有定义，在标准化后的六维空间中计算，其余行记为“—”。服务 Q5。')
    rows=[[r.setting,fmt(r.width) if r.kernel=='linear' else '—',int(r.sv),fmt(r.train_ba),fmt(r.validation_ba),frac(int(r.validation_tn),20)] for r in a['contrast'].itertuples()]
    table(d,['设置','线性带宽','支持向量数（/186）','训练平衡准确率','验证平衡准确率','验证正常召回'],rows,[2.05,.75,.95,.95,.95,1.318])

def ev_C2fig(d,a):
    picture(d,'figure-c2.png','图 C2','脊柱数据的 RBF 验证结果热图。每格是一组（C, gamma）在同62条验证记录上的平衡准确率；186条训练记录与标准化方式固定。服务 Q5。',5.8)

def ev_D1(d,a):
    caption(d,'表 D1','冻结模型的测试结果。每行一个核族按选参规则冻结的模型（参数同表 C2），只在186条训练记录上拟合；测试62条（异常42、正常20），此前从未用于选参。TP、FN 指异常记录被判对、判错的条数，TN、FP 指正常记录被判对、判错的条数。三行是研究组预先安排的并列报告，不能据此再次挑核。服务 Q6。')
    table(d,['模型','TP','FN','TN','FP','平衡准确率'],[[KN[r.kernel],r.tp,r.fn,r.tn,r.fp,fmt(r.ba)] for r in a['test'].itertuples()],[1.8,.7,.7,.7,.7,2.368])

def ev_D1fig(d,a):
    st=a['stress'];r20='；'.join(f"{KN[k]} {r.mean_ba:.3f}/{r.flip:.3f}" for k in ['linear','poly','rbf'] for r in [st[(st.kernel==k)&(st.sd_fraction==.2)].iloc[0]])
    picture(d,'figure-d1.png','图 D1','固定模型的扰动压力试验。同62条测试记录，三模型参数同表 D1；只给骨盆半径加零均值高斯噪声，标准差为该变量训练标准差的0、10%、20%，每个强度重复200次，三模型共用同一批噪声。左图为平均平衡准确率，右图为预测相对无噪声时发生翻转的记录比例；噪声为20%时的读数（平均平衡准确率/翻转比例）：'+r20+'。这是人为压力设定，不是仪器误差估计。服务 Q6。',6.4)

def ev_D2(d,a):
    caption(d,'表 D2','研究规模对照。每行一个研究任务：第一行是本案例，后两行是设定情境。n 为样本数，p 为特征数；“完整核矩阵”按 n×n 个双精度数（8n² 字节）估算存储，1 GB=10⁹字节，只作算术示例，不是软件的实际内存或耗时。服务 Q6。')
    table(d,['研究任务','n','p','完整核矩阵','研究组需要'],[['脊柱方法比较',310,6,'0.769 MB','比较预测方法'],['基因表达小样本',80,2000,'0.051 MB','提出候选标志物'],['多中心大表',100000,6,'80 GB','快速训练和复现']],[1.65,.8,.7,1.4,2.418])

PACKET_EVIDENCE={'A':[ev_A1,ev_A2],'B':[ev_B1,ev_B2,ev_B1fig],'C':[ev_C1fig,ev_C1,ev_C2,ev_C3,ev_C2fig],'D':[ev_D1,ev_D1fig,ev_D2]}

def tracker_card(d,q,text):
    card(d,f"{q['id']} 追踪更新卡（写在总答案追踪表“{q['tracker_row']}”行，更新阶段写 {q['id']}）：{text}")

def module_info(d,q):
    info(d,f"对应目标：{'、'.join(q['objective_ids'])}    证据：{'、'.join(q['evidence_ids'])}    约{q['minutes']}分钟    完成后更新：总答案追踪表“{q['tracker_row']}”行")

# ---------------------------------------------------------------- student worksheet
def worksheet(a):
    d=newdoc('Problem Based Learning Student Worksheet','学生学习与答题册')
    para(d,'姓名与学号写在本页右上角。本册由每位学生独立完成：可以讨论、查资料和使用 AI，但计算、证据核对与判断由本人负责，每个判断都要引用本册的表或图。除证据卡和定向阅读需要打开在线资料外，全部必做证据已印在本册中，不需要编写代码。本册仅用于教学研究，不构成临床诊断、部署或患者护理建议。')
    heading(d,'研究组的委托',2);para(d,PROBLEM)
    table(d,['方案','研究组实际采取的行动'],OPTIONS,[.8,6.168])
    para(d,RULES_TEXT)
    ev_S1(d,a)
    para(d,'最终产出——研究备忘录：写给脊柱研究组的200–350字说明，分“行动主张—证据与推理—边界”三段，依据总答案追踪表的 T1–T6 行写成（见“课外综合”）。')

    heading(d,'学习目标与探究路线')
    prompt(d,'本讲学习目标：下表的 LO 编号在各探究模块开头的“对应目标”中使用。')
    table(d,['编号','学完后你能做到','主要练习'],[[l[0],l[2],'、'.join(q['id'] for q in QS if l[0] in q['objective_ids'])+('、研究备忘录' if l[0]=='LO8' else '')] for l in OBJECTIVES],[.6,5.2,1.168])
    prompt(d,'三个阶段：')
    table(d,['阶段','时间','你要做什么'],[['Phase 1 课堂启动','45分钟','只用委托与表 S1 作初选；再用图 S1 完成二维课堂练习，并完成方案预测表、3W 表、个人学习计划与退出条。'],['Phase 2 课外自学',f'约{PHASE2_MINUTES}分钟','按 Packet A→B→C→D 顺序领取；完成 Packet A 核对、Q1–Q6、证据卡、概念辨析、决策检验矩阵与研究备忘录初稿。'],['Phase 3 翻转课堂','45分钟','随机抽1–2人白板讲解；同伴质询；个人修订研究备忘录并完成退出条。']],[1.45,1.0,4.518])
    prompt(d,'六个探究问题（Q1–Q6）：每题结束时更新总答案追踪表的一行；六行合起来就是研究备忘录的依据。')
    table(d,['问题','案例中的问题及证据','学习内容','Packet','分钟','更新追踪行'],[[q['id'],q['question'],q['learn'],q['release_after'],q['minutes'],q['tracker_row']] for q in QS],[.45,3.25,1.25,.55,.45,1.018])
    para(d,f"六个模块合计{sum(q['minutes'] for q in QS)}分钟；另有 Packet A 核对约{OTHER_MINUTES['packet_a_check']}分钟、证据卡约{OTHER_MINUTES['evidence_card']}分钟、课外综合约{OTHER_MINUTES['concept_distinction']+OTHER_MINUTES['decision_matrix']+OTHER_MINUTES['memo']}分钟。")
    heading(d,'本册过程用语',2)
    para(d,'Packet：按阶段领取的证据包（A–D）。总答案追踪表：保存你对总问题判断变化的唯一位置，T0 存初选，T1–T6 存各探究问题的结论。追踪更新卡：每个探究模块末尾带竖线底色的说明，告诉你该在追踪表哪一行、哪一列写什么；它本身没有答题框。冻结：在 T5 写定方案及参数后不再更改，只允许在 Packet D 后保留或改为 D。停止或修改条件：会让你改选或暂缓的具体发现。3W：我已经知道什么、还不知道什么、下一步做什么。方案预测表：在看到证据前，预测每个方案若合适或错选会出现什么结果。证据卡：用本册数据和原始资料核验一句具体说法。退出条：阶段结束时的简短回答。白板讲解：在翻转课堂上说明自己的学习与分析过程，不要求背稿。')
    heading(d,'中英术语对照（工作含义）',2)
    table(d,['术语','本册中的工作含义'],[['分类超平面（hyperplane）','满足 f(x)=wᵀx+b=0 的点；二维时是一条直线，六个变量时是六维空间中的一个五维“平面”。'],['决策得分（decision score）','f(x) 的数值；正负号给出类别，数值本身不是患病概率。'],['几何距离','样本到超平面的垂直距离 |f(x)|/‖w‖。'],['间隔（margin）','硬间隔时指分类边界到最近训练样本的距离；软间隔 SVM 中指两条虚线 f=±1 围成的带，允许样本进入带内。线性 SVM 中这条带的宽度为 2/‖w‖（本册称“带宽”）。'],['支持向量（support vector）','落在间隔线上、间隔内或被判错的训练样本；训练后的边界只由它们决定。'],['软间隔（soft margin）','允许部分样本进入间隔甚至被判错的 SVM。'],['合页损失（hinge loss）','max(0, 1−y·f(x))，用来计量一个样本的违例程度。'],['C','scikit-learn 中违例的惩罚权重（与 ISLR 教材中的“预算 C”方向相反）。'],['核函数（kernel）','直接算出映射后两个样本内积的函数 K(x,z)。'],['gamma','RBF 核中控制相似度随距离衰减快慢的参数；在多项式核中是内积前的缩放系数（本册固定）。'],['标准化（standardization）','每个变量减去训练集均值、除以训练集标准差。'],['召回率与平衡准确率','召回率：某类记录中被判对的比例；平衡准确率：两类召回率的平均。']],[2.1,4.868])
    heading(d,'分阶段发放',2)
    para(d,'课堂结束后领取 Packet A；在总答案追踪表写完“T1 几何依据”行后领取 Packet B；写完“T3 容错权衡”行后领取 Packet C；写完并提交“T5 冻结方案”行后领取 Packet D 与课外综合。使用整本印刷册时也按这个顺序，不提前翻看后续 Packet。')

    heading(d,'总答案追踪表',new=True)
    para(d,'总答案追踪表是你对总问题判断的唯一存放处。T0 在 Phase 1 填写，之后保留不改；T1–T6 各在对应探究问题结束时按该题的追踪更新卡填写一次。“当前判断”写该行的暂定结论（T0、T5、T6 必须写方案 L、P、R、D 之一）；“支持证据”写证据编号和数字；“反证或限制”写削弱该结论的证据或条件；“什么发现会改变判断”写一个具体、可检验的发现；“更新阶段”写 Phase 1 或 Q 编号。每处写一两句，不抄计算过程。')
    table(d,['追踪行','当前判断','支持证据','反证或限制','什么发现会改变判断','更新阶段'],[[label,None,None,None,None,None] for label in ['T0 初选']+[q['tracker_row'] for q in QS]],widths=[.8,1.65,1.15,1.15,1.55,.668],answer=True,height=1.0)

    heading(d,'Phase 1 课堂启动（45分钟）',new=True)
    para(d,'本阶段只使用“研究组的委托”（含方案表与比较规则）、表 S1、图 S1、启动概念读页和定向阅读指南；暂不阅读 Packet A–D。老师会安排短讨论，但每人独立作答。')
    table(d,['分钟','每人的动作','写在哪里'],[['0–6','读委托、方案表、比较规则与表 S1，作出初选','总答案追踪表“T0 初选”行'],['6–11','读启动概念读页与图 S1，用自己的话澄清两个术语','术语澄清表'],['11–24','总纲二维课堂练习：比较图 S1 的三幅图','启动观察表'],['24–30','预测每个方案合适或错选时会出现的证据','方案预测表'],['30–37','按三个概念簇整理知识缺口','3W 表'],['37–42','从定向阅读指南选资料，制订自学计划','个人学习计划表'],['42–45','写给研究组的一个问题','启动退出条']],[.75,3.9,2.318])
    card(d,'启动初选（写在总答案追踪表“T0 初选”行）：从“研究组的委托”方案表的 L、P、R、D 中选一个，只依据委托、比较规则和表 S1。“当前判断”写所选方案和一句理由；“支持证据”引用表 S1 的一项事实；“反证或限制”写你这个选择最依赖、但还没有证据支持的一个假设；“什么发现会改变判断”写一个会让你改选的具体结果（例如某个核族在验证集上的一项表现）；“更新阶段”写 Phase 1。')
    heading(d,'启动概念读页',2)
    para(d,'一个样本是一组测量值。二维时把它写成 x=(u,v)，线性得分 f(x)=w₁u+w₂v+b：w₁、w₂ 是两个坐标的权重，b 平移直线。f(x)=0 的点构成分类边界；f>0 判为一类，f<0 判为另一类。六个测量时 f(x)=w₁x₁+…+w₆x₆+b，f(x)=0 是六维空间中的一个“超平面”，二维时它就是一条直线。向量长度 ‖w‖=√(w₁²+w₂²)。')
    para(d,'间隔（margin）原意是边界离最近训练样本有多远（硬间隔）。图 S1 中实线是 f=0，两条虚线是 f=+1 和 f=−1；对线性 SVM，得分已按 SVM 的约定定好尺度，两条虚线之间的垂直宽度是 2/‖w‖（本册称“带宽”）。软间隔 SVM 允许一些样本进入虚线之间，甚至落到错误一侧，这时“间隔”指这条虚线带，而不是到最近样本的距离；C 是这种“违例”的惩罚权重。RBF 核能画出弯曲边界，gamma 控制它的相似度随距离衰减的快慢。课堂上先记录现象，课外再用证据解释原因。')
    ev_S1fig(d,a)
    answer(d,'术语澄清：为读懂方案 L 与 R 的差别，请结合启动概念读页和图 S1 左图，用自己的话各写一句：①“分类边界”在图中是哪条线，它怎样决定一个样本的类别；②“间隔”指图中的什么。不要照抄读页。',[['①分类边界',None],['②间隔',None]],height=.5)
    answer(d,'启动观察（总纲课堂练习）：图 S1 左图、中图只改变线性核的 C（0.01 与 100），右图是 RBF 核。每行写两句：第一句写你在图中看到的差异（指明比较哪两幅图、看的是实线还是虚线）；第二句写一个你想在课外核验的解释。暂不使用 Packet A–D 的任何数字。',[['C 与直线边界（左图对中图）',None],['间隔带宽如何变化（左图对中图）',None],['线性与 RBF 的边界形状（中图对右图）',None]],widths=(1.75,5.218),height=.72)
    answer(d,'方案预测：为了让 Packet C 的脊柱验证结果能检验你的初选，请对方案 L、P、R 各写一行，第二、三列各写一句。第二列写一个可观察的结果，例如与另两种核相比的验证平衡准确率、两类召回率或支持向量数；第三列写一个具体后果。此时是预测，没有标准答案。',[['L（线性核）',None,None],['P（二次多项式核）',None,None],['R（RBF 核）',None,None]],headers=('方案','若它是合适的基线，验证证据应显示什么？','若错选了它，研究组的比较会出什么问题？'),widths=(1.3,2.834,2.834),height=.62)
    answer(d,'3W 表：为补齐在方案 L、P、R、D 之间作选择所需的知识，按三个概念簇各写一行，第二至四列各写一句。第二列须引用表 S1、图 S1 或启动概念读页中的一项；第三列只写会影响方案选择的问题；第四列写定向阅读指南的编号（R1–R6）或探究问题编号，以及具体动作。第一行是另一门课的格式示例。',[['示例（另一门课）','已知两台仪器都以℃记录体温。','不知道两台仪器的读数是否一致。','查仪器说明，并用同一标准样本比较两台读数。'],['Q1–Q2 边界、间隔与支持向量',None,None,None],['Q3 软间隔与 C',None,None,None],['Q4–Q6 核、验证与适用范围',None,None,None]],headers=('概念簇','关于这个问题，我已经知道什么？','要正确回答问题，我还不知道什么？','下一步我要学习什么、查找什么或分析什么？'),widths=(1.3,1.85,1.85,1.968),height=.78)
    heading(d,'定向阅读指南',2)
    para(d,f'下列资料均可免费在线阅读，按探究问题选读，不必通读。ISLR 指 James 等著《An Introduction to Statistical Learning》第2版第9章（R 版与 Python 版均可），免费 PDF：{ISLR} 。scikit-learn SVM 用户指南：{SVMREF} 。')
    table(d,['编号','服务','读什么','读时找什么'],[['R1','Q1','ISLR 9.1.1–9.1.3（超平面、用分隔超平面分类、最大间隔分类器）','间隔的定义；为什么在所有能分开两类的超平面中选离训练样本最远的一个。'],['R2','Q2、Q3','ISLR 9.1.5 与 9.2.1–9.2.2（不可分情形、支持向量分类器）','哪些观测是支持向量，为什么只有它们影响超平面。注意：ISLR 的 C 是“违例预算”，C 越大越宽容、间隔越宽；scikit-learn 与本册的 C 是违例惩罚，方向相反。'],['R3','Q3','scikit-learn 指南 1.4.7.1 SVC','目标函数中的两项分别代表什么；C 乘在哪一项上。'],['R4','Q4',f'ISLR 9.3.1–9.3.2；scikit-learn 指南 1.4.6 与 1.4.6.1；示例页 RBF SVM parameters：{RBFREF}','核函数怎样代替显式升维；RBF 中 gamma 与 C 各自控制什么。'],['R5','Q5','scikit-learn 指南 1.4.5 Tips on Practical Use','关于缩放（scale）数据和设置 C 的建议；验证或测试数据应使用怎样的缩放。'],['R6','Q6','scikit-learn 指南 1.4 开头的优点与缺点列表、1.4.4 Complexity；ISLR 9.5（与逻辑回归的关系）','高维、样本量与训练代价；SVM 得分与逻辑回归概率的区别。']],[.5,.7,2.9,2.868])
    answer(d,'个人学习计划：从你的3W 表中选一项最影响方案选择的未知问题，写四行：要解决的问题；要读的资料（写定向阅读指南编号及小节）；读后要做的核验动作（对照本册哪张表或图）；完成标准（必须能用本册一张表或图检验，例如“能不看笔记，用某张图解释两种设置的差别”）。',[['要解决的问题',None],['资料（R 编号及小节）',None],['核验动作',None],['完成标准',None]],widths=(1.75,5.218),height=.4)
    answer(d,'启动退出条（最后3分钟）：写一个你想问研究组的问题（关于数据、标签或比较规则，而不是“哪个核最好”），并写出它的答案会影响 Q1–Q6 中的哪一题、为什么；共两句。',[['给研究组的问题',None]],height=.7)

    heading(d,'Phase 2 · Packet A：几何与数据',new=True)
    para(d,'课堂结束后领取 Packet A，完成 Packet A 核对与 Q1。只看到本 Packet 为止，不预读 Packet B–D。表 A1 给出启动阶段没有的变量范围与记录核验，表 A2 是 Q1 的计算材料。')
    ev_A1(d,a)
    answer(d,'Packet A 核对：研究组在选择方案前仍需要下表六项证据。逐行完成第二、三列：第二列判断表 S1 与表 A1 是否已经回答（写“已答”“部分”或“未答”，并引用一个数字或说明）；第三列写将由哪个探究问题、用哪项证据核查（依据“六个探究问题”表中的证据编号），若本册没有任何证据能回答，写“本册无法核查”并说明它会限制哪个结论。',[['六个变量的数值尺度能否直接放进同一个距离',None,None],['每条记录是否来自不同受试者',None,None],['边界由哪些训练记录决定',None,None],['各核族在验证记录上的两类召回率',None,None],['冻结方案在测试记录上的表现',None,None],['测量有小误差时预测是否稳定',None,None]],headers=('尚缺的证据','表 S1 或表 A1 已回答了吗？','将由哪个探究问题、用哪项证据核查？'),widths=(2.2,2.4,2.368),height=.42)
    ev_A2(d,a)
    q=QS[0];heading(d,q['title'],2);module_info(d,q)
    para(d,'学习重点：加权和决定边界所在的位置，但要比较“离边界多远”，必须把得分除以 ‖w‖ 变成几何距离。阅读：定向阅读指南 R1；scikit-learn 指南 1.4.7 开头的线性可分示意图（'+SVMREF+'#mathematical-formulation）。')
    para(d,'距离读页：记超平面 H 为 f(x)=0 的点。点 x 到 H 的垂直距离为下式；对带标签的样本，y·f(x)/‖w‖ 是带符号的间隔，为负表示判错。把 w 和 b 同时乘一个正数，分类线不变，原始得分却会变。对一条固定的线性边界，若一个点受到的扰动（位移向量）长度小于它到边界的距离，这个点就不会越过边界；这一保障只针对已有的点，不保证未来样本也离边界足够远。')
    eq(d,'d(x,H)=|wᵀx+b|/‖w‖')
    para(d,'在线性可分的硬间隔 SVM 中，可以把得分尺度约定为所有训练点满足 yᵢf(xᵢ)≥1、最近的点取等号。此时每侧的最小距离为 1/‖w‖，最小化 ½‖w‖² 就等价于最大化间隔。较大的间隔让已有的点能容忍更大的扰动，也限制了可选边界的范围；这是它可能有助于泛化的理由，但不是新样本准确率的保证——训练样本是否有代表性、特征尺度和噪声同样影响泛化。')
    answer(d,'Q1 距离计算：为比较候选线 a 与 b 离样本有多远，用表 A2 的六个样本逐行计算：最近样本（可能不止一个）、最小 |f|、‖w‖ 与最小几何距离（=最小 |f|/‖w‖）。第三行把线 a 的得分改写成 f=5u，检验同一条几何边界的最小距离是否改变。',[['a：f=u',None,None,None,None],['b：f=u−0.8',None,None,None,None],['a 重写：f=5u',None,None,None,None]],headers=('边界','最近样本','最小 |f|','‖w‖','最小几何距离'),widths=(1.5,1.4,1.4,1.268,1.4),height=.42)
    answer(d,'Q1 几何与现实：每行一到两句。①依据 Q1 距离计算表，说明任意长度小于0.3的扰动会不会让线 a、线 b 判错表 A2 中的某个样本，若会，点名该样本；②引用表 A1 中两个变量的取值范围，说明为什么在脊柱数据的原始数值上“长度0.3的扰动”对不同变量含义不同；再用一句话说明，即使尺度统一，①的保障为什么也不等于脊柱新记录的准确率。',[['①扰动小于0.3时',None],['②搬到脊柱数据时',None]],height=.72)
    tracker_card(d,q,'“当前判断”写：离最近样本更远的边界带来什么保障，以及这让你更倾向方案 L、P、R、D 中的哪一个，或暂不影响选择；“支持证据”写 Q1 距离计算表中线 a、线 b 的最小几何距离；“反证或限制”写 Q1 几何与现实表中限制这一保障的一点；“什么发现会改变判断”写一个可能在后续 Packet 中出现、会动摇“偏好更宽间隔”这一原则的结果。')

    heading(d,'Phase 2 · Packet B：支持向量与容错',new=True)
    para(d,'写完总答案追踪表“T1 几何依据”行后领取 Packet B，依次完成 Q2 与 Q3。不预读 Packet C、D。')
    q=QS[1];heading(d,q['title'],2);module_info(d,q)
    para(d,'学习重点：支持向量是参与决定边界的训练样本。在线性可分的硬间隔情形中，它们是恰好落在两条间隔线上的样本；在软间隔中，落在间隔内或被判错的样本也是支持向量。它们是样本（记录），不是被选中的特征，也不一定是“典型病例”。阅读：定向阅读指南 R2；scikit-learn 指南 1.4.1 Classification 中支持向量的示例（'+SVMREF+'#classification）。')
    ev_B1(d,a)
    answer(d,'Q2 支持向量：为判断研究组的边界依赖哪些训练记录，按行作答。①由表 B1 第一行的边界位置与带宽推出两条间隔线的位置，点名表 A2 中恰好落在间隔线上的样本；②各引用表 B1 的边界位置与带宽，说明为什么移除 N1 后边界不变、移除 P1 后边界改变；③预测：若只移除 P2，边界位置与带宽会怎样？用①的结论说明理由（可在辅助实验本 Q2 单元选做核对）。',[['①支持向量',None],['②移除 N1 与移除 P1',None],['③移除 P2 的预测',None]],height=.62)
    tracker_card(d,q,'“当前判断”写：SVM 的边界由哪一类训练记录决定，这对研究组理解“所选模型依赖哪些记录”有什么含义；“支持证据”写表 B1 中移除 P1 前后的边界位置或带宽；“反证或限制”写这个六点练习不能告诉你的、关于脊柱数据支持向量的一件事；“什么发现会改变判断”写一个关于脊柱模型支持向量数量的结果，若出现会让你担心模型只是在记住训练记录。')
    q=QS[2];heading(d,q['title'],2);module_info(d,q)
    para(d,'学习重点：软间隔（soft margin）允许间隔违例。本节标签 yᵢ 取−1 或+1（模拟图中的“类0”在公式里编码为−1，“类1”为+1）。令 mᵢ=yᵢf(xᵢ)，合页损失（hinge loss）为 max(0,1−mᵢ)：mᵢ≥1 时无损失；0<mᵢ<1 时已判对，但落在间隔内，仍有损失；mᵢ<0 才是判错。凡 mᵢ<1 的样本都算间隔违例（包括判错的样本）。样本的最低松弛量 ξᵢ 等于这个损失。')
    eq(d,'最小化 J = ½‖w‖² + C·Σᵢ max(0, 1−yᵢf(xᵢ))')
    para(d,'读目标函数时只需分辨两项：第一项偏好小的 ‖w‖（即宽的带宽 2/‖w‖），第二项累计违例。在特征表示、样本和核都固定时，C 越大，违例越“贵”，模型越倾向于减少违例、接受更窄的带宽；这不等于每个分类指标都会随 C 单调变好。软间隔的虚线带里可以有样本，所以它未必是“完全空白”的区域。阅读：定向阅读指南 R2（注意 ISLR 中 C 的方向相反）与 R3（'+SVMREF+'#svc）。')
    ev_B2(d,a);ev_B1fig(d,a)
    answer(d,'Q3 合页损失：为了区分研究组模型的“判错”与“间隔违例”，设四个教学样本的带标签得分 m 分别为1.4、0.4、−0.2、−1.0，逐行计算 max(0,1−m)，并判断该样本是否判对、是否属于间隔违例（写“是”或“否”）。这四个 m 是独立算例，不是表 B2 中的记录。',[['1.4',None,None,None],['0.4',None,None,None],['−0.2',None,None,None],['−1.0',None,None,None]],headers=('给定的 m','合页损失','是否判对','是否间隔违例'),widths=(1.5,1.8,1.8,1.868),height=.38)
    answer(d,'Q3 参数比较：①从表 B2 读出 C=0.01 与 C=100 各自的带宽、间隔违例数、支持向量数和验证判对数，并结合图 B1 用一句话说明 C 变小时虚线带和空心圈怎样变化，再与你在启动观察表“间隔带宽如何变化”一行的记录对照；②判断这些模拟结果能否支持“研究组在脊柱数据上应选尽可能小的 C”，写两句，其中一句说明两个设置的验证判对数相差几个、验证点只有24个意味着什么。',[['①C=0.01 与 C=100',None],['②能否外推到脊柱数据',None]],height=.85)
    tracker_card(d,q,'“当前判断”写你目前的选 C 原则（一句话的原则，不是具体数值）；“支持证据”写表 B2 的一组对照数字；“反证或限制”写这一原则只来自72个模拟训练点和24个验证点所带来的一个局限；“什么发现会改变判断”写一个若在脊柱验证数据上出现、就会推翻你选 C 原则的结果。')

    heading(d,'Phase 2 · Packet C：核选择与验证',new=True)
    para(d,'写完总答案追踪表“T3 容错权衡”行后领取 Packet C，依次完成 Q4、Q5 与证据卡。在“T5 冻结方案”行冻结方案并提交后，才能领取 Packet D。')
    q=QS[3];heading(d,q['title'],2);module_info(d,q)
    para(d,'核读页：内积 xᵀz 是对应坐标乘积之和。若先把输入映射成新坐标 φ(x)，就可以在新坐标中使用线性边界；核技巧（kernel trick）用 K(x,z)=φ(x)ᵀφ(z) 直接算出这个内积，不必逐项构造全部新坐标。核必须是某个映射下的内积，并非任意相似度都能直接作为 SVM 的核。')
    eq(d,'线性 K(x,z)=xᵀz');eq(d,'多项式 K(x,z)=(gamma·xᵀz+r)ᵈ');eq(d,'RBF K(x,z)=exp(−gamma·‖x−z‖²)')
    para(d,'多项式核的次数 d 控制可表达的交互阶数，r 是常数项。RBF 的 gamma 越大，相似度随距离衰减越快，每个训练样本的影响范围越小。核 SVM 仍然是在隐式的新坐标中找一个超平面，映射回原始坐标时可以呈现为曲线。训练后的预测只用到支持向量：')
    eq(d,'f(x)=Σ αᵢyᵢK(xᵢ,x)+b')
    para(d,'式中求和只对支持向量集合 SV 中的样本 i 进行，αᵢ 是训练求得的系数；这里只解释预测的结构，不要求推导对偶优化。核 SVM 图中的 f=±1 是得分等高线，不能按原始平面上的间距与线性带宽比较。阅读：定向阅读指南 R4（'+SVMREF+'#kernel-functions）。')
    ev_C1fig(d,a);ev_C1(d,a)
    answer(d,'Q4 二次核计算：为说明方案 P 的核在做什么，使用另一组给定输入 x=(1,2)、z=(2,0)，取 K(x,z)=(xᵀz)² 与映射 φ(x)=(x₁², √2·x₁x₂, x₂²)。逐行写出计算结果；最后一行用一句话说明为什么直接算 K 与先映射再求内积的结果相同，并指出本算例（常数项 r=0、gamma=1）与图 C1 中的二次多项式核（r=1）不是同一个核设置。',[['xᵀz 与 K(x,z)',None],['φ(x) 与 φ(z)',None],['φ(x)ᵀφ(z)',None],['为何相等；与图 C1 的差别',None]],widths=(1.75,5.218),height=.42)
    answer(d,'Q4 三核比较：为判断图 C1 能为方案 L、P、R 提供什么证据，第二、三列各写一句。“边界形状与表 C1 的一个数字”描述该核在图 C1 中的边界形状，并引用表 C1 的一个数字；“这组模拟证据不能推出什么”写一个看似合理、但这72个模拟训练点和24个验证点不能支持的推论。三行不要重复同一个推论。',[['线性（L）',None,None],['二次多项式（P）',None,None],['RBF（R）',None,None]],headers=('核族','边界形状与表 C1 的一个数字','这组模拟证据不能推出什么'),widths=(1.3,2.834,2.834),height=.6)
    answer(d,'Q4 gamma 与 C：设两个标准化后的样本相距 ‖x−z‖=1，用 RBF 核公式分别算 gamma=0.1 与 gamma=10 时的相似度 K（保留三位有效数字）；再用一句话说明 gamma 改变的对象与 C 改变的对象有什么不同。',[['gamma=0.1 时的 K',None],['gamma=10 时的 K',None],['gamma 与 C 各改变什么',None]],widths=(1.75,5.218),height=.42)
    tracker_card(d,q,'“当前判断”写：数据呈现什么形状时，你会选 P 或 R 而不选 L；“支持证据”写图 C1 或表 C1 的一个对照；“反证或限制”写把这组二维模拟证据推广到六维脊柱数据的一个限制；“什么发现会改变判断”写一个会让你放弃非线性核的脊柱验证结果。')
    q=QS[4];heading(d,q['title'],2);module_info(d,q)
    para(d,'学习重点：训练集用来估计标准化所需的均值、标准差和模型参数；验证集用来比较核与超参数；测试集只用来检查已冻结的方案。标准化（StandardScaler）用训练集均值和标准差变换每个变量。变量尺度改变时，样本间距离随之改变，同一个 gamma 或 C 的含义也随之改变。平衡准确率是两类召回率的平均，避免异常类（多数类）掩盖正常类的表现。SVM 得分的正负用于分类，数值不是患病概率。阅读：定向阅读指南 R5（'+SVMREF+'#tips-on-practical-use）。')
    ev_C2(d,a);ev_C3(d,a);ev_C2fig(d,a)
    answer(d,'Q5 验证证据：为在 T5 冻结一个方案，按行作答，每行一到两句并引用数字。①缩放：比较表 C3 中两行“RBF，C=1，gamma=0.1”（未标准化与已标准化）的支持向量数、训练与验证平衡准确率，说明未标准化时模型做了什么，并用表 A1 中一个变量的取值范围解释原因。②最宽带宽：比较表 C3 中“线性，C=0.01”与“线性，C=10”的带宽、验证平衡准确率和验证正常召回，说明这修正了你在 T3 写的选 C 原则的哪一点。③gamma 过大：用表 C3 最后一行和图 C2 中 gamma=10 的一行，说明训练与验证之间出现了什么差距。④合格条件：按“研究组的委托”中的合格条件逐一检查表 C2 的三个核族，写出每个核族通过与否及起决定作用的数字。',[['①缩放',None],['②最宽带宽',None],['③gamma 过大',None],['④合格条件（L、P、R）',None]],widths=(1.75,5.218),height=.62)
    card(d,'Q5 冻结卡（写在总答案追踪表“T5 冻结方案”行，更新阶段写 Q5；写完即提交，再领取 Packet D）：“当前判断”从方案表的 L、P、R、D 中选一个，写明核、C、gamma（若适用）与标准化方式；若不止一个核族合格，说明你怎样在它们之间取舍；“支持证据”引用表 C2 或表 C3 的数字；“反证或限制”写验证集只有62条（其中正常20条）带来的一个限制；“什么发现会改变判断”写一个会让你在 Packet D 改为 D 的测试结果，写成可检验的数值条件。冻结后不能用表 D1 换核。')
    answer(d,'证据卡：为核验 Q3–Q5 中一个选参理由，从 AI 回答、教材或官方文档中摘录一句关于 C、gamma 或缩放的具体说法（原文，不超过25个英文词或一句中文），再用本册表 B2、表 C2 或表 C3 中的一个数字，以及定向阅读指南 R2–R5 中的一处原文核验它。四行分别写：原句及出处；本册数据核验（写证据编号和数字）；原文核验（写 R 编号与小节）；结论——成立、需要限定或不成立，以及限定条件。',[['原句及出处',None],['本册数据核验',None],['原文核验',None],['结论与限定',None]],height=.45)

    heading(d,'Phase 2 · Packet D：新记录与适用范围',new=True)
    para(d,'只有总答案追踪表“T5 冻结方案”行已经写完并提交，才能阅读本 Packet。表 D1 的三行是研究组预先安排的并列报告；按比较规则，你只能保留 T5 冻结的方案或改为 D，不能据测试结果更换核、参数或阈值。')
    for f in PACKET_EVIDENCE['D']:f(d,a)
    q=QS[5];heading(d,q['title'],2);module_info(d,q)
    para(d,'学习重点：几何间隔描述固定模型对某类输入扰动的抵抗能力；泛化还取决于未来样本是否来自与训练数据可比的过程。中小样本时核 SVM 常是可行的候选；高维数据中间隔约束仍然有效，但无用特征、标签噪声和很小的 n 仍会伤害预测。非线性核不直接给出“每个原始变量的效应”。')
    para(d,'规模读页：核方法训练时要比较样本两两之间的相似度，代价随 n 增长明显上升；scikit-learn 指南 1.4.4 指出，其求解器的计算量大致在 n² 与 n³ 量级之间随样本数增长。表 D2 只是完整核矩阵的存储算术，实际软件有缓存等机制，不代表实际占用必为 8n²。大 n 时可考虑线性专用求解器；高 p 与大 n 是两种不同的困难。阅读：定向阅读指南 R6（'+SVMREF+'#complexity）。')
    answer(d,'Q6 测试复核：为决定是否保留 T5 冻结的方案，用表 D1 中该方案所在行的 TP、FN、TN、FP 计算两类召回率（若 T5 选了 D，就用表 D1 的“线性”一行计算），第三列写结果是否仍满足委托中的合格条件；最后一行从图 D1 读出该方案在噪声为训练标准差20%时的平均平衡准确率与预测翻转比例，并用一句话说明两个指标回答的问题有何不同。',[['异常召回率',None,None],['正常召回率',None,None],['图 D1 的两个指标（20%）',None,None]],headers=('项目','计算（分子/分母=比值）或读数','一句解释'),widths=(1.75,2.2,3.018),height=.5)
    answer(d,'Q6 迁移判断：依据表 D2，为“80个样本、2000个基因”和“100000个样本、6个特征”两个研究各写两句：第一句判断核 SVM 是否适合作为起点，并说明计算或统计上的限制；第二句说明在这个研究的“研究组需要”下，SVM 的支持向量或分类结果为什么不能直接当作病因或生物标志物的证据（或为什么这一点在该研究中不是主要问题）。',[['基因表达小样本（80×2000）',None],['多中心大表（100000×6）',None]],widths=(1.9,5.068),height=.72)
    answer(d,'Q6 作业原题：用自己的话回答“为什么 SVM 不是简单地找一条‘刚好分开两类’的线？”写120–180字，至少引用表 A2、表 B2、图 C1、表 C3、表 D1 中的两项证据，把间隔、支持向量、软间隔与 C、泛化连成一段解释。研究备忘录只引用本题，不重复作答。',[['作业原题',None]],height=1.9)
    tracker_card(d,q,'“当前判断”写保留 T5 冻结的方案还是改为 D（不重新选择核）；“支持证据”引用 Q6 测试复核表中的召回率或图 D1 的读数；“反证或限制”结合表 D2 或记录独立性写一项迁移限制；“什么发现会改变判断”写研究组还需要的一项独立证据，以及它出现什么结果时你会改变判断。')

    heading(d,'课外综合：概念辨析、决策检验矩阵与研究备忘录初稿',new=True)
    para(d,f"本节约{OTHER_MINUTES['concept_distinction']+OTHER_MINUTES['decision_matrix']+OTHER_MINUTES['memo']}分钟，随 Packet D 发放。研究备忘录按“主张—证据—推理—边界”（Claim–Evidence–Reasoning–Boundary，CERB）组织：主张是研究组应采取的行动，证据是本册的编号与数字，推理说明证据为何支持行动，边界说明结论不能用于什么。")
    answer(d,'概念辨析：研究组下一轮会把 SVM 与第8讲的逻辑回归并列报告，以下三对概念容易混用。第二、三列各写一句：第二列说明两者在本案例中的区别，并引用一个表、图或读页；第三列写混淆后研究组会作出的一个错误判断。',[['决策得分 f(x) 与逻辑回归的预测概率',None,None],['线性带宽 2/‖w‖ 与 RBF 图中的 f=±1 等高线',None,None],['验证集（表 C2、表 C3）与测试集（表 D1）的用途',None,None]],headers=('概念对','在本案例中的区别（引用编号或读页）','混淆会导致什么错误判断'),widths=(2.1,2.434,2.434),height=.62)
    answer(d,'决策检验矩阵：为写备忘录的“证据与推理”段，给方案 L、P、R 各填一行。第二、三列只写已经发放的证据中观察到的收益和代价，各附证据编号与数字；第四列对照你在 Phase 1 方案预测表中对该方案的预测，写“成立”“部分成立”或“不成立”，并给出依据的证据编号。未来可能改变判断的发现只写在总答案追踪表中，此处不写。',[['L',None,None,None],['P',None,None,None],['R',None,None,None]],headers=('方案','已观察到的收益（编号与数字）','已观察到的代价（编号与数字）','方案预测表中的预测是否成立'),widths=(.55,2.2,2.2,2.018),height=.62)
    answer(d,'研究备忘录初稿：写给脊柱研究组，200–350字，分三段。①行动主张：保留 T5 冻结的方案（写明参数）或改为 D；②证据与推理：从总答案追踪表的 T1–T6 行各取一项结论（注明行号），说明几何间隔、关键样本、C、核选择、验证与测试怎样共同支持你的主张，并说明为何不选另外两个核族（可引用决策检验矩阵）；③边界：写出这项结论不能用于什么，至少涉及临床用途、记录独立性、迁移规模中的两项。作业原题已在 Q6 作答，此处写“见 Q6 作业原题”即可。',[['①行动主张',None],['②证据与推理',None],['③边界',None]],height=.8);_memo_tall(d)

    heading(d,'Phase 3 翻转课堂与课堂修订（45分钟）',new=True)
    para(d,'本阶段45分钟：0–4分钟回看自己的研究备忘录初稿；4–20分钟教师随机抽一至两位同学白板讲解；20–30分钟同伴质询；30–38分钟教师追问与综合；38–43分钟个人修订；43–45分钟退出条。每人都要准备说明自己的完整学习与分析过程，讲解方式自定，没有固定汇报脚本或小组角色。')
    answer(d,'同伴质询记录：针对白板讲解中一个关于方案 L、P、R、D 的理由，引用本册一个表或图，写你提出或收到的一个问题以及对方（或你）的回应；如果当天没有被点名，写你自己对这个问题的回答。共两到三句。',[['问题与回应',None]],height=.8)
    answer(d,'课堂修订：比较你的研究备忘录初稿与课堂质询，写一段100–150字的替换或补充段落，指出一个发生改变的论证及对应证据编号；若维持原判断，回应课堂上最强的一个反对意见。修订后的行动仍只能是 T5 冻结的方案或 D，并写明总答案追踪表中受影响的行（T1–T6）。',[['备忘录修订段落',None]],height=1.2)
    answer(d,'结束退出条：每行一句。①从 T0 初选到课堂修订，你的方案有没有改变，是在哪一步改变的；②哪一项证据（写编号）最改变了你对间隔、支持向量、C 或核的理解；③关于 SVM 你仍想弄清的一个问题。',[['①方案变化',None],['②最关键的证据',None],['③仍想弄清的问题',None]],height=.45)

    heading(d,'数据获取与辅助实验资源',new=True)
    para(d,'必做题所需的数值和图片都已印在本册，不要求编写新代码。辅助实验本用于离线复现本册的表与图，不增加必做题。')
    para(d,'数据入口：'+SOURCE+'；DOI：10.24432/C5K89B；许可 CC BY 4.0；引用 Barreto 与 Neto 的数据记录。下载文件 column_2C.dat：每行6个连续值和一个 NO/AB 标签，空白分隔，无表头；源页称无缺失，本地核对未见“?”、NA 或空值。column_3C.dat 是同一批记录的三分类标签，不要与二分类文件合并。')
    para(d,'课程包内的文件：原始数据 assets/pbl-svm-margin/source-data/column_2C.dat；整理表 assets/pbl-svm-margin/vertebral-column.csv；辅助实验本 notebook/pbl-svm-margin-lab.ipynb（含 Q2“移除 P2”的核对单元）。整理表中的编号是课堂行号，不是患者标识。标准化、划分和模拟代码均随包提供。')
    para(d,'可选延伸（不计入课外时间）：交叉验证、bootstrap 区间、概率校准和外部验证将在第10至12讲学习；本讲不把这些技术当作完成 Q1–Q6 的先修要求。')
    d.save(ROOT/(SLUG+'-student-worksheet.docx'))
    return d

# ---------------------------------------------------------------- other documents
def evidence_doc(a):
    d=newdoc('Packet A–D Evidence Pack','证据汇编')
    para(d,'这是与学生学习单同编号的证据汇编，便于教师分阶段发放或学生检索。证据不附标准答案。先发启动材料，课后发 Packet A；学生写完总答案追踪表的 T1 行后发 Packet B，写完 T3 后发 Packet C，提交 T5 后发 Packet D。学习单内已含全部必做证据。')
    para(d,'源数据未注明单位与测量可靠性，无法声称真实仪器扰动分布；完整行未重复也不能证明受试者独立。所有结果只服务于教学和内部方法比较，不是临床诊断、部署或病因证据。公式与核设置依据：'+SVMREF+'。')
    heading(d,'启动材料',2);para(d,PROBLEM);table(d,['方案','行动'],OPTIONS,[.7,6.268]);para(d,RULES_TEXT);ev_S1(d,a);ev_S1fig(d,a)
    for q in QS:para(d,f"{q['id']}：{q['question']} 对应总答案追踪表“{q['tracker_row']}”行。")
    for packet in 'ABCD':
        heading(d,'Packet '+packet,new=True)
        for f in PACKET_EVIDENCE[packet]:f(d,a)
        for q in [q for q in QS if q['release_after']==packet]:para(d,f"证据复核 {q['id']}：使用{'、'.join(q['evidence_ids'])}完成学习单 {q['id']}，把依据与可改变判断的发现写在总答案追踪表“{q['tracker_row']}”行；不另交重复答案。")
    heading(d,'来源与适用边界',2)
    para(d,'真实数据：'+SOURCE+'，DOI 10.24432/C5K89B，CC BY 4.0，核查日期2026-09-17。模拟数据为固定种子9的教学构造，没有真实患者或真实细胞标签。')
    d.save(ROOT/(SLUG+'-evidence-pack.docx'))

def teacher_doc(a,design):
    b={r['kernel']:r for r in a['best']};t={r.kernel:r for r in a['test'].itertuples()};c={r.setting:r for r in a['contrast'].itertuples()}
    sim={r.name:r for r in a['sim'].itertuples()};st=a['stress']
    def stress(k,s):r=st[(st.kernel==k)&np.isclose(st.sd_fraction,s)].iloc[0];return f"{r.mean_ba:.3f}/{r.flip:.3f}"
    d=newdoc('PBL Flipped Classroom Teacher Plan','教师用书（不发给学生）')
    para(d,'面向生命科学学院大四直博生。目标是让学生通过证据理解 SVM 边界，并为脊柱研究组选择一个离线基线。学生已修微积分、数理统计和前八讲；向量、内积和长度在学习单中就地解释，不要求凸优化基础。')
    para(d,f'时间：课堂启动45分钟、课外自学约{PHASE2_MINUTES}分钟、翻转课堂45分钟。学习单是唯一必做载体；Notebook 为辅助复现；review/ 内的试填答案不得发给学生。')
    heading(d,'目标覆盖',2)
    for lo in OBJECTIVES:
        qids='、'.join(q['id'] for q in QS if lo[0] in q['objective_ids']);para(d,lo[0]+'（总纲：'+lo[1]+'）：'+lo[2]+' 对应 '+qids+'。')
    heading(d,'课堂启动的45分钟',2)
    table(d,['分钟','实施','检查个人产出'],[['0–6','呈现委托、互斥方案、比较规则与表 S1。','T0 初选；允许选 D，但要求写出理由与改选条件。'],['6–11','只澄清得分、超平面、间隔与术语，不讲 C 与核的结论。','术语澄清两句（用自己的话）。'],['11–24','用图 S1 完成总纲三项二维观察。','启动观察三行；第二句是待核验的解释而非结论。'],['24–30','要求对 L、P、R 分别写预测与错选后果。','方案预测表三行，可检验。'],['30–37','辨认影响选择的概念缺口。','3W 三行，第四列有 R 编号或 Q 编号。'],['37–42','检查学习计划的完成标准是否可检验。','资料、动作、标准。'],['42–45','收集给研究组的问题。','启动退出条；课后可汇总答复（如：单位、受试者独立性）。']],[.75,3.1,3.118])
    para(d,'首次讲解控制在4分钟以内，其余用短追问。图 S1 已包含 C 的改变、linear 与 RBF 的差别和间隔变化，不能把总纲课堂练习全部挪到课外。')
    heading(d,'课外发放与检查',2)
    para(d,'学习单是完整母版；印刷时分段发放，LMS 使用 student-release/ 中的阶段版：启动与追踪表、Packet A、Packet B、Packet C、Packet D 与综合、翻转课堂与入口。检查点：T1 写完发 B；T3 写完发 C；T5 提交后发 D。课前不要公开完整母版、完整证据包或已执行的 Notebook，否则阶段隔离只能靠自律。')
    table(d,['模块','分钟','开放与检查'],[['Packet A 核对',OTHER_MINUTES['packet_a_check'],'第三列须有 Q 编号或“本册无法核查”；“受试者独立”一行应识别为无法核查。']]+[[q['id'],q['minutes'],'Packet '+q['release_after']+'；检查“'+q['tracker_row']+'”行'] for q in QS]+[['证据卡',OTHER_MINUTES['evidence_card'],'Q5 后；原句、本册数字、原文小节须相符。'],['课外综合',OTHER_MINUTES['concept_distinction']+OTHER_MINUTES['decision_matrix']+OTHER_MINUTES['memo'],'Q6 后；备忘录须引用 T1–T6 各一行。']],[1.3,.7,4.968])
    para(d,'必读概念已在学习单就地提供；外部资料用于独立核验。AI 可以解释术语和公式，但学生答案必须引用本册的表图数值。模块没有额外总结框：暂定结论与未知因素只写入对应追踪行。')
    heading(d,'教师参考答案与追问',2)
    para(d,'方案预测表（Phase 1）：无标准答案。合理的预测形如“若 R 合适，验证平衡准确率应明显高于 L，且两类召回率都不低”“若错选 R，可能在验证集上表现不稳、支持向量很多”。到课外综合的决策检验矩阵时再对照。')
    para(d,'Packet A 核对：①尺度——部分（表 A1：滑脱程度约−11至419，骨盆倾斜角约−7至49），由 Q5 用表 C3 尺度对照核查；②受试者独立——未答，本册无法核查（无受试者编号），限制 Q6 的泛化结论；③关键训练记录——Q2，表 B1；④两类召回——Q5，表 C2；⑤测试表现——Q6，表 D1；⑥小误差稳定性——Q6，图 D1。')
    lw=sim['linear-0.01-1'];lh=sim['linear-100-1']
    para(d,f"Q1：线 a 的最近样本为 N2、N3、P1，最小 |f|=1、‖w‖=1、最小距离1；线 b 的最近样本为 P1，最小 |f|=0.2、最小距离0.2；5u 重写后最小 |f|=5、‖w‖=5，最小距离仍为1。长度小于0.3的扰动不会让线 a 判错任何样本，但可让线 b 判错 P1。脊柱变量原始范围差异很大且单位未注明，同一欧氏长度对不同变量含义不同；几何保障只针对已有点，不是新样本误差界。")
    p2=[r for r in a['deletions'] if r['operation']=='移除 P2'][0]
    para(d,f"Q2：①间隔线 u=−1 与 u=1，支持向量为 N2、N3、P1；②移除 N1（远点、非支持向量）边界仍为 u=0、带宽2；移除 P1 后边界移到 u=1、带宽4；③移除 P2 预测不变，核对结果边界 u={p2['boundary_u']:.3f}、带宽{p2['width']:.3f}。支持向量是样本不是特征，也不是“典型病例”。T2 的担忧信号：支持向量数接近训练集全部（表 C3 中有两行为186/186）。")
    para(d,f"Q3：合页损失依次为0、0.6、1.2、2.0；0.4 判对但违例，−0.2 与 −1.0 判错且违例。表 B2：C=0.01 带宽{lw.width:.3f}、违例{lw.violations}、支持向量{lw.sv}、验证判对{lw.validation_correct}/24；C=100 带宽{lh.width:.3f}、违例{lh.violations}、支持向量{lh.sv}、验证判对{lh.validation_correct}/24。C 变小时带宽变宽、带内点与支持向量增多。两者只差{lw.validation_correct-lh.validation_correct}个验证点，24点无法支撑“C 越小越好”，更不能外推到六维脊柱数据——这正是 Q5 表 C3 要检验的。允许学生在 T3 暂写“偏好较小 C”，Q5 应修正。")
    para(d,'Q4：xᵀz=2，K=4；φ(x)=(1, 2√2, 4)，φ(z)=(4, 0, 0)，φ(x)ᵀφ(z)=4。这是 r=0、gamma=1 的二次核算例，图 C1 使用 r=1，两者不能混算。距离1时 gamma=0.1 的相似度约0.905，gamma=10 约4.54×10⁻⁵。gamma 控制每个样本的影响范围（边界的弯曲程度），C 控制违例的代价。三核比较中“不能推出”的合格答案包括：不能推出脊柱数据也是弯曲结构；24个验证点上相差2个点不足以排名；RBF 训练错误少不等于泛化好。')
    cu=c['RBF，C=1，gamma=0.1，未标准化'];cs=c['RBF，C=1，gamma=0.1，已标准化'];c01=c['线性，C=0.01'];c10=c['线性，C=10'];cg=c['RBF，C=1，gamma=10，已标准化']
    para(d,f"Q5：①未标准化：支持向量{int(cu.sv)}/186、训练平衡准确率{cu.train_ba:.3f}、验证{cu.validation_ba:.3f}（全部判为异常）；已标准化：{int(cs.sv)}、{cs.train_ba:.3f}、{cs.validation_ba:.3f}。原因：滑脱程度的范围（约430）远大于其他变量，原始距离几乎只由它决定，gamma=0.1 时验证记录与所有训练记录都“不相似”，模型退化为记忆训练点。②线性 C=0.01 带宽{c01.width:.2f}最宽，但验证平衡准确率{c01.validation_ba:.3f}、正常召回0/20——全部判为异常；C=10 带宽{c10.width:.2f}、验证{c10.validation_ba:.3f}。宽带宽不是选择标准，C 必须由验证决定。③gamma=10：训练{cg.train_ba:.3f}、验证{cg.validation_ba:.3f}、支持向量{int(cg.sv)}/186，图 C2 中 gamma=10 一行验证在0.525–0.600。④合格条件：L 与 R 通过（L 的正常召回恰为13/20=0.650，处在门槛上）；P 的正常召回12/20=0.600 未通过。")
    table(d,['核族','C','gamma','验证平衡准确率','异常召回','正常召回'],[[KN[k],f"{r['C']:g}",'不适用' if k=='linear' else ('1/6' if k=='poly' else f"{r['gamma']:g}"),fmt(r['validation_ba']),frac(int(r['validation_tp']),42),frac(int(r['validation_tn']),20)] for k,r in b.items()])
    para(d,'T5 可接受的答案：L（C=10）——与 R 验证几乎相同（相差0.001），更简单、支持向量更少（56 对 94）、便于与逻辑回归并列说明；R（C=10、gamma=0.01）——正常召回14/20 比 L 多一条，离门槛更远；D——须指出具体的证据缺口（如验证正常类只有20条，L 恰在门槛上），不能只说“不是临床数据”。不接受 P 或“看测试再定”。')
    para(d,f"Q6：以 L 为例，异常召回 {t['linear'].tp}/42={t['linear'].tp/42:.3f}，正常召回 {t['linear'].tn}/20={t['linear'].tn/20:.3f}，满足合格条件；R 为 {t['rbf'].tp}/42、{t['rbf'].tn}/20。图 D1 在20%噪声时（平均平衡准确率/翻转比例）：线性 {stress('linear',.2)}，RBF {stress('rbf',.2)}，二次多项式 {stress('poly',.2)}。平均表现问“整体判对多少”，翻转比例问“多少记录的预测随小扰动改变”，前者可在翻转互相抵消时保持不变。正常只有20条，一条改变5个百分点，不宜把 L 与 R 的测试差距解释为普遍优势；测试后想换核，需要新的独立测试。80×2000：可以尝试线性核并严格验证，p≫n 时训练集往往可分但未必泛化，支持向量是样本而非基因，不能直接当生物标志物；100000×6：完整核矩阵约80 GB，核 SVM 训练代价大，宜用线性专用求解器，该任务关注复现与速度，可解释性不是首要问题。")
    para(d,'概念辨析参考：①SVM 得分只用符号分类，数值没有概率刻度，逻辑回归输出概率（仍需校准）；混淆会把得分当风险直接比较或设阈值。②线性带宽是标准化空间的几何宽度，RBF 的 f=±1 是隐式空间在原始平面上的等高线，不能用尺子比较；混淆会误判“RBF 间隔更窄/更宽”。③验证集用于选参与冻结，测试集只评估冻结方案；混淆会导致测试泄漏与过乐观报告。')
    para(d,'可用追问：为何要除以权重长度？判对为何仍有损失？支持向量能否当特征？改变单位时 gamma 是否仍是同一种设置？RBF 虚线为何不能用尺量出与线性相同含义的间隔？为什么线性 C=0.01 最宽却最差？高 p 与大 n 为什么是不同的问题？测试结束后若想换核，需要什么新的评估？')
    heading(d,'翻转课堂的45分钟',2)
    para(d,'0–4 回看；4–20 随机抽1–2人白板讲解；20–30 同伴质询；30–38 教师追问与综合；38–43 个人修订；43–45 退出条。所有学生都准备完整过程，教师不预设唯一的讲解顺序。')
    heading(d,'作业与评分',2)
    para(d,'个人提交完整学习单。Q6 保留总纲作业原题；研究备忘录须使用 T1–T6，不再次回答作业原题。迁移题在 Q6 的表 D2，不另加项目。')
    table(d,['维度','权重','判据'],[['几何与容错','30%','Q1 距离归一化与重缩放不变；Q2 点名支持向量并正确预测移除 P2；Q3 区分判对与违例，识别24点证据的局限。'],['核与参数','25%','Q4 内积恒等式与 gamma/C 区分；Q5 尺度、最宽带宽、大 gamma 与合格条件均引用数字。'],['适用与迁移','15%','Q6 召回率带分母；区分平均表现与翻转；区分高 p、大 n 与生物学解释。'],['综合与修订','25%','追踪表完整；决策矩阵与备忘录整合全部 Q；能回应反证。'],['来源核验','5%','证据卡的原句、本册数字、原文小节与限定相符。']],[1.2,.7,5.068])
    heading(d,'实施边界与风险响应',2)
    para(d,'若学生线性代数薄弱，先展开 w₁u+w₂v+b，使用向量长度定义；不删掉归一化距离。若学生读 ISLR，提醒其 C 与 scikit-learn 方向相反（学习单 R2 已提示）。若时间超出，删选修阅读，不删三种核、支持向量、C 或总纲课堂任务。')
    para(d,'数据与代码：186/62/62 固定分层划分；所有候选只用训练集拟合、验证集选择，查看测试后不重选。表 C3 的六组对照在查看测试前固定。正文不展开 CV、bootstrap 或校准；这些作为第10–12讲的可选延伸。主案例是历史脊柱标签识别，不证明因果或临床可用。')
    d.save(ROOT/(SLUG+'-teaching-plan-flipped-classroom.docx'))

def rationale_doc(design):
    d=newdoc('Purpose · Design Rationale · Expected Outcomes','设计说明')
    para(d,'本版以学生能独立理解问题、查找证据并写出可检查答案为设计目标。课程总纲第9讲是 SVM 算法课，核心工作围绕几何间隔、关键样本、容错与核方法；评价指标只服务于选模，避免把整讲改写成通用的临床部署审计。')
    heading(d,'旧设计的复核与修订',2)
    para(d,'旧 plan.md 选脊柱数据，svm.md 另选模拟细胞数据；本版统一为真实脊柱主案例和明确标注的二维模拟辅助。首版（ChatGPT/Codex，已归档于 planning/）生成后中断；接手版按 pbl-ml-package 补齐学习目标、探究问题表、术语对照、方案预测表、定向阅读指南、Packet A 核对与概念辨析，增加表 C3 的真实数据对照与表 B2 的验证判对数，并去除重复提问。')
    para(d,'旧计划的 polynomial 只放概念卡，无法检验学生是否掌握；本版 Q4 加入具体内积恒等式与三核同数据比较。高维优势、大数据代价和解释局限由 Q6 场景题考核。必做自学约135分钟（旧计划为120–150分钟），CV、bootstrap、calibration 移为选修。')
    heading(d,'总问题与问题链覆盖',2)
    para(d,'研究人员要在下一轮离线比较中采用一个 SVM 基线，方案 L/P/R/D 互斥且可操作；参数由预先写定的选参规则决定，学生判断的是核族与是否暂缓。六个探究问题逐步建立选择理由；最终备忘录必须使用 T1–T6，不能凭一张性能表跳过几何、核和适用条件。')
    for q in QS:para(d,q['id']+'：'+q['contribution_to_synthesis']+'；通过'+q['student_output']+'留下个人证据。')
    heading(d,'数据与分析为何适合',2)
    para(d,'UCI 脊柱数据310条、6个连续特征，易于独立加载和短时间重复分析。来源说明两类由三类合并、单位字段为空；本地核对记录这些限制而不自行补齐。二维双月形模拟仅用于直观比较，六点算例用于精确计算；两者均不命名为真实生物标志物。')
    para(d,'有意保留的认知冲突来自真实结果而非人为制造：二维模拟中最小的 C 带宽最宽、验证也多对1点（表 B2），脊柱数据上最宽带宽的线性 C=0.01 却把全部验证记录判为异常（表 C3）。尺度对照固定核参数，解释时提醒同一 gamma 随尺度改变已代表不同相似度。压力测试只扰动骨盆半径，避免独立扰动相关角度破坏“骨盆入射角=骨盆倾斜角+骶骨倾角”的几何关系。')
    heading(d,'学生独立学习与可读性',2)
    para(d,'每个模块先给本地概念读页，再给精确的阅读小节、带编号的证据和有明确形式的作答任务。计算题预置行，判断题保留开放回答；证据标题和图注不写出待判断的结论。总答案追踪表保存结论和未知因素，模块不再另抄一遍。')
    para(d,'学生可以用 AI，但必须把一句具体说法与案例数字和原始资料相互核验；定向阅读指南提示 ISLR 与 scikit-learn 中 C 的方向相反，这是 AI 回答中常见的混淆点。教师随机选1–2人白板讲解，让每位学生准备全流程；不设固定分工。版式沿用第7讲 A4、0.65英寸边距、页眉页脚与题卡样式。')
    heading(d,'预期学习结果与不能声称的结果',2)
    para(d,'可观察结果：正确计算距离和合页损失，点名支持向量，区分 C 与 gamma，比较线性、多项式与 RBF，识别缩放与验证的作用，对高 p 和大 n 作不同判断。评分强调证据与推理。没有真实教学试验，不能声称本包已证明提升考试成绩或科研能力；模拟学生试填只用于发现题意、顺序和负担问题。')
    heading(d,'检验与迁移',2)
    para(d,'发布前检查目标覆盖、证据释放时点、DOCX 题目可读性、冷读指代审查与试填、图表一致性和页面排版。Q6 的小样本基因表达与大样本研究表要求迁移概念，不能把 SVM 的分类结果或支持向量直接解释成病因。')
    para(d,'数据与算法来源：'+SOURCE+'；'+SVMREF+'；'+RBFREF+'；'+ISLR+'。课程来源：全课程 plan.docx 第9讲与本目录两份旧计划。')
    d.save(ROOT/(SLUG+'-design-rationale.docx'))

def notebook():
    import nbformat as nb
    n=nb.v4.new_notebook();c=[]
    c.append(nb.v4.new_markdown_cell('# 第9讲 SVM 辅助复现\n所有必做证据已印在学习单中；本 Notebook 用于离线核查。数据不用于临床诊断或部署。运行后按 Q1–Q6 对照学习单的表与图。'))
    c.append(nb.v4.new_code_cell("from pathlib import Path\nimport importlib.util\nimport numpy as np, pandas as pd\nfrom IPython.display import Image, display\nROOT=Path.cwd().parent if Path.cwd().name=='notebook' else Path.cwd()\nspec=importlib.util.spec_from_file_location('lesson9',ROOT/'scripts'/'pbl-svm-margin-build.py')\nlesson=importlib.util.module_from_spec(spec); spec.loader.exec_module(lesson)\n# analyze() 加载本地数据、训练内缩放、固定拆分、重训所有候选、生成 B–D 表图。\na=lesson.analyze()\nprint(a['summary'])"))
    cells={'Q1':("display(pd.DataFrame(a['audit'])[['feature','min','max','train_sd']])\npoints=a['toy']\nrows=[]\nfor name,w,b in [('a',np.array([1.,0.]),0.),('b',np.array([1.,0.]),-.8),('5a',np.array([5.,0.]),0.)]:\n    distance=np.abs(points@w+b)/np.linalg.norm(w)\n    rows.append({'边界':name,'最小距离':distance.min(),'最近样本':[['N1','N2','N3','P1','P2','P3'][i] for i in np.flatnonzero(np.isclose(distance,distance.min()))]})\ndisplay(pd.DataFrame(rows))",['s1']),
           'Q2':("# 表 B1 的三行 + 学习单 Q2③ 的核对（移除 P2）\ndisplay(pd.DataFrame(a['deletions']))",[]),
           'Q3':("display(a['sim'][a['sim'].kernel=='linear'][['C','errors','violations','sv','width','validation_correct']])\nm=np.array([1.4,.4,-.2,-1.])\ndisplay(pd.DataFrame({'带标签得分':m,'合页损失':np.maximum(0,1-m),'判对':m>0,'间隔违例':m<1}))",['b1']),
           'Q4':("display(a['sim'][(a['sim'].C==1)&(a['sim'].gamma==1)][['kernel','errors','sv','validation_correct']])\nx=np.array([1.,2.]); z=np.array([2.,0.])\nphi=lambda t: np.array([t[0]**2,np.sqrt(2)*t[0]*t[1],t[1]**2])\nprint('K=',(x@z)**2,' phi(x)·phi(z)=',phi(x)@phi(z))\nprint('RBF 相似度（距离1）：gamma=0.1 ->',np.exp(-.1),'；gamma=10 ->',np.exp(-10))",['c1']),
           'Q5':("display(pd.DataFrame(a['best'])[['kernel','C','gamma','sv','train_ba','validation_ba','validation_tp','validation_tn']])\ndisplay(a['contrast'][['setting','width','sv','train_ba','validation_ba','validation_tn']])\ndisplay(a['grid'][a['grid'].kernel=='rbf'][['C','gamma','scaled','train_ba','validation_ba','sv']])",['c2']),
           'Q6':("display(a['test'])\ndisplay(a['stress'])\npd.testing.assert_frame_equal(pd.read_csv(lesson.AS/'packet-d-test.csv'),a['test'])",['d1'])}
    for q in QS:
        code,figs=cells[q['id']]
        c.append(nb.v4.new_markdown_cell('## '+q['id']+'\n'+q['question']+'\n\n核验本单元结果与学习单对应的表或图（'+'、'.join(q['evidence_ids'])+'）；写下一项你原先的判断需要的限定。'))
        c.append(nb.v4.new_code_cell(code))
        for name in figs:c.append(nb.v4.new_code_cell("display(Image(filename=str(lesson.AS/'figure-%s.png')))"%name))
    c.append(nb.v4.new_markdown_cell('## 反思\n1. 表 B2 与表 C3 中“最宽带宽”的表现为什么相反？这对选择 C 意味着什么？\n2. 如果把表 D1 用来重新选核，会破坏哪一项比较规则？\n3. 本数据没有受试者编号，这限制了哪一个结论？'))
    c.append(nb.v4.new_markdown_cell('## 可执行分析源码\n下一单元展示本课分析函数的完整源码，检查只用训练集拟合缩放、验证集选参以及扰动试验共用同一批噪声。无需联网。'))
    c.append(nb.v4.new_code_cell('import inspect\nprint(inspect.getsource(lesson.analyze))'))
    n.cells=c;n.metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3'))
    nb.write(n,ROOT/'notebook'/(SLUG+'-lab.ipynb'))

def release_copies():
    # Same content as the master worksheet, sliced at Heading 1 release boundaries.
    import copy
    src=Document(ROOT/(SLUG+'-student-worksheet.docx'))
    parts={};stage='启动与追踪表'
    for e in src.element.body:
        if e.tag==qn('w:sectPr'):continue
        texts=''.join(e.xpath('.//w:t/text()'))
        if e.tag==qn('w:p'):
            sty=e.find(qn('w:pPr'))
            sid=sty.find(qn('w:pStyle')).get(qn('w:val')) if sty is not None and sty.find(qn('w:pStyle')) is not None else ''
            if sid=='Heading1':
                for key,name in [('Packet A','Packet-A'),('Packet B','Packet-B'),('Packet C','Packet-C'),('Packet D','Packet-D与综合'),('Phase 3','翻转课堂与入口')]:
                    if key in texts:stage=name
        parts.setdefault(stage,[]).append(copy.deepcopy(e))
    dest=ROOT/'student-release';dest.mkdir(exist_ok=True)
    for old in dest.glob('*.docx'):old.unlink()
    for i,(stage,els) in enumerate(parts.items(),1):
        d=Document(ROOT/(SLUG+'-student-worksheet.docx'))
        for e in list(d.element.body):
            if e.tag!=qn('w:sectPr'):d.element.body.remove(e)
        for e in els:d.element.body.insert(len(d.element.body)-1,e)
        first=d.element.body[0];pb=first.find('.//'+qn('w:pageBreakBefore'))
        if pb is not None:pb.getparent().remove(pb)
        # Word requires a closing paragraph after a final table; keep it one point high so no blank page appears.
        if d.element.body[-2].tag==qn('w:tbl'):
            p=d.add_paragraph();p.paragraph_format.space_before=Pt(0);p.paragraph_format.space_after=Pt(0)
            p.paragraph_format.line_spacing=Pt(1);font(p.add_run(''),1)
            # hide the paragraph mark as well, so a table that ends exactly at the page foot adds no blank page
            rpr=OxmlElement('w:rPr');[rpr.append(OxmlElement(t)) for t in ('w:vanish',)];sz=OxmlElement('w:sz');sz.set(qn('w:val'),'2');rpr.append(sz);p._p.get_or_add_pPr().append(rpr)
        d.save(dest/f'{i:02d}-{stage}.docx')

def validate(design):
    for an in design['analyses']:
        for f in an['artifacts']:assert (AS/f).exists(),f
    for suffix in ['student-worksheet','evidence-pack','teaching-plan-flipped-classroom','design-rationale']:
        d=Document(ROOT/(SLUG+'-'+suffix+'.docx'));txt='\n'.join(p.text for p in d.paragraphs)+'\n'+'\n'.join(c.text for t in d.tables for r in t.rows for c in r.cells)
        assert '\ufffd' not in txt and 'SVM' in txt
        (REVIEW/(suffix+'-text.txt')).write_text(txt,encoding='utf-8')
    ws=(REVIEW/'student-worksheet-text.txt').read_text(encoding='utf-8')
    for label in [i[0] for i in EVIDENCE_ITEMS]:assert label in ws,label
    for teacher_only in ['参考答案','教师用书']:assert teacher_only not in ws,teacher_only
    from PIL import Image
    for p in AS.glob('figure-*.png'):assert Image.open(p).width>=900
    for q in QS:assert all(any(i['id']==e for i in design['evidence_items']) for e in q['evidence_ids'])
    reports=[]
    for mode,target,report in [('design',AS/'analysis-design.json',REVIEW/(SLUG+'-design-check.md')),('lint',ROOT/(SLUG+'-student-worksheet.docx'),REVIEW/(SLUG+'-lint.md'))]:
        cmd=[sys.executable,str(SKILL/'scripts'/'worksheet_check.py'),mode,str(target)]
        if mode=='design':cmd+=['--homework-minutes',str(PHASE2_MINUTES)]
        else:cmd+=['-o',str(report)]
        r=subprocess.run(cmd,text=True,encoding='utf-8',capture_output=True)
        if mode=='design':report.write_text(r.stdout,encoding='utf-8')
        print(mode,r.returncode,r.stdout.strip()[-300:],r.stderr.strip());reports.append(r.returncode)
    assert not any(reports),'Fix QA errors before release'

def manifest(design):
    o={k:f'{SLUG}-{s}.docx' for k,s in [('student_worksheet','student-worksheet'),('evidence_pack','evidence-pack'),('teaching_plan','teaching-plan-flipped-classroom'),('design_rationale','design-rationale')]};o['notebook']='notebook/'+SLUG+'-lab.ipynb'
    qa=dict(lint='review/'+SLUG+'-lint.md',design='review/'+SLUG+'-design-check.md',pilot_fields='review/pilot-fields.json',pilot_fill='review/'+SLUG+'-pilot-fill.docx',pilot_report='review/'+SLUG+'-pilot-report.md',takeover_audit='review/takeover-gap-audit.md',status='rebuilt-awaiting-pilot-and-render')
    d=dict(topic='第9讲 SVM与Margin',slug='svm-margin',mode='algorithm choice',dataset=dict(name='UCI Vertebral Column',source=SOURCE,task='binary classification',target='AB=1,NO=0'),outputs=o,assets=sorted(str(p.relative_to(ROOT)).replace('\\','/') for p in AS.rglob('*') if p.is_file()),boundary='教学研究；不构成临床、因果或部署结论。',core_question=PROBLEM,problem_architecture=design['problem_architecture'],course_coverage=design['course_coverage'],customized=True,course_brief=['plan.md','svm.md','../../../plan.docx'],analysis_design='assets/pbl-svm-margin/analysis-design.json',build_script='scripts/pbl-svm-margin-build.py',qa=qa,student_release=sorted(str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'student-release').glob('*.docx')),archive='planning/archive-v0-gpt-draft-20260918/')
    dump(ROOT/'package-manifest.json',d)

def main():
    a=analyze();design=make_design();worksheet(a);evidence_doc(a);teacher_doc(a,design);rationale_doc(design);notebook();release_copies();validate(design);manifest(design)
    print('Four documents and auxiliary assets generated; pilot and visual QA still required.')

if __name__=='__main__':main()
