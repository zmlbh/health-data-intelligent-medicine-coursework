"""Lesson 7 numerical evidence. Default Python; all products stay in this lesson."""
from pathlib import Path
import json, itertools, hashlib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import BernoulliNB
from sklearn.metrics import confusion_matrix, log_loss, brier_score_loss, roc_auc_score, average_precision_score, precision_recall_curve, roc_curve, auc

ROOT=Path(__file__).resolve().parents[1]
SLUG='pbl-machine-learning-basics-naive-bayes'
ASSET=ROOT/'assets'/SLUG
CN=['发热','恶心','腰痛','尿意频繁','排尿痛','尿道烧灼']
COLS=['temperature_c','nausea','lumbar_pain','urine_pushing','micturition_pains','burning_urethra','bladder_inflammation','nephritis']

def compute():
    raw=ROOT/'planning/source-data/acute-inflammations/diagnosis.data'
    df=pd.read_csv(raw,sep='\t',header=None,encoding='utf-16',decimal=',',names=COLS)
    assert df.shape==(120,8) and df.isna().sum().sum()==0
    X=np.column_stack([(df.iloc[:,0]>=38).astype(int),*(df[c].eq('yes').astype(int) for c in COLS[1:6])])
    y=df[COLS[6]].eq('yes').to_numpy(dtype=int)
    dev,te=train_test_split(np.arange(120),test_size=.2,random_state=7,stratify=y)
    tr,va=train_test_split(dev,test_size=.25,random_state=7,stratify=y[dev])
    model=BernoulliNB(alpha=1).fit(X[tr],y[tr]); p=model.predict_proba(X[va])[:,1]
    tables={}
    def tab(key,headers,rows,caption): tables[key]={'headers':headers,'rows':rows,'caption':caption}
    chosen=[0,20,40,60,80,100]
    tab('A1',['记录','体温℃','恶心','腰痛','尿意频繁','排尿痛','尿道烧灼','膀胱炎症','肾炎'],[[int(i+1),float(df.iloc[i,0]),*[int(df.iloc[i,j]=='yes') for j in range(1,8)]] for i in chosen], '表 A1  原始记录节选｜Q1 输入与标签。每行是一条专家设计的潜在病例描述；从120条中固定抽取6条。症状与标签中1表示有、0表示无；仅体温为℃。来源 UCI Acute Inflammations；不是新增患者。')
    audit=[['总记录与变量','120条；6项输入、2项疾病决策'],['主标签','膀胱炎症：有59条、无61条'],['另一个标签','肾炎：有50条、无70条'],['体温','非缺失120条；35.5至41.5℃'],['7个二元列','各列非缺失120条；均只有yes与no'],['缺失与异常标记','未发现空值、问号或第三种类别'],['完整8列的重复','重复余量21条；40条属于重复组'],['原始六项输入','99种不同组合；未静默删除重复'],['来源文字','医学专家为测试专家系统设计潜在病例记录；未提供患者标识或独立抽样说明'],['编码核对','说明写ASCII；实际文件为UTF-16且带BOM，小数用逗号']]
    tab('A2',['检查项','观察结果'],audit,'表 A2  来源与质量审计｜Q1 观察单位。每行是一项对全120条记录的检查；人数不详，记录数不等于独立患者数。来源为原始文件、配套说明与本课重算。')
    tab('A3',['集合','总记录','阳性','阴性'],[[n,len(ix),int(y[ix].sum()),int(len(ix)-y[ix].sum())] for n,ix in [('训练',tr),('验证',va),('测试',te)]],'表 A3  固定分层划分｜Q2 数据职责。每行一个集合；120条按72/24/24拆分，三集合行号无交集。两次分层拆分均固定随机种子7；此表不公布测试性能。')
    counts=np.array([X[tr][y[tr]==c].sum(axis=0) for c in [0,1]])
    tab('B1',['症状取值1的含义','阳性类计数 n=35','阴性类计数 n=37'],[[CN[j],int(counts[1,j]),int(counts[0,j])] for j in range(6)],'表 B1  训练集症状计数｜Q3 参数估计。每行一种二元症状，计数指该类内症状为1的记录数；共72条。发热预先定义为体温≥38℃，其他症状保持原0/1。所有参数仅来自训练集。')
    queries=np.array([[0,0,0,1,1,0],[1,1,1,1,1,1]])
    tab('B2',['查询','发热','恶心','腰痛','尿意频繁','排尿痛','尿道烧灼'],[[f'查询{i+1}',*map(int,row)] for i,row in enumerate(queries)],'表 B2  待预测症状｜Q3 后验计算。两行是指定的教学查询向量，不增加训练样本，也未给真标签。列顺序与表 B1 完全一致；1有、0无。只必算查询1；查询2供核对或选做。')
    # Two-symptom exercise, same original split; validation grouping retains true label.
    two=[3,4]
    grp=pd.DataFrame({'尿意频繁':X[va,3],'排尿痛':X[va,4],'真实标签':y[va]}).groupby(['尿意频繁','排尿痛','真实标签']).size().reset_index(name='记录数')
    tab('B3',['尿意频繁','排尿痛','真实标签','记录数'],grp.values.tolist(),'表 B3  课堂二症状验证记录｜翻转课堂训练（沿用Q3方法）。每行聚合相同二症状及相同真实膀胱炎症标签的记录，人数合计24；1有、0无。训练仍用表 B1 对应两行和35/37类计数；本表不能用于估计参数。')
    ly=[1,0,1,0]; pa=[.8,.2,.4,.1]; pb=[.99,.01,.01,.01]
    tab('B4',['教学记录','真实标签','模型甲的阳性概率','模型乙的阳性概率'],[[i+1,ly[i],pa[i],pb[i]] for i in range(4)],'表 B4  概率损失对照｜Q4 交叉熵。4条完全构造的教学记录；两组概率为人工指定，不是本数据NB结果。阈值均为0.50；自然对数，概率无单位。')
    tab('B5',['教学记录','真实次日体温℃','预测次日体温℃'],[[1,37,38],[2,39,37]],'表 B5  连续结局误差｜Q4 均方误差。2条构造的次日体温预测记录；真实与预测值全部列出。此处体温是预测目标，与本课分类模型中体温的输入角色不同。')
    threshold=[]
    for t in [.10,.50,.90]:
        tn,fp,fn,tp=confusion_matrix(y[va],p>=t,labels=[0,1]).ravel()
        threshold.append([f'{t:.2f}',int(tn),int(fp),int(fn),int(tp)])
    threshold.append(['先验基线，阈值0.50',12,0,12,0])
    tab('C1',['阈值或模型','真阴性TN','假阳性FP','假阴性FN','真阳性TP'],threshold,'表 C1  验证集错误计数｜Q5 分类评价。每行在同一24条验证记录上评价；实际阳性12条、实际阴性12条。前三行均为六症状NB，预测阳性规则p≥阈值。先验基线对每条均输出35/72；未使用症状。')
    def bins(prob):
        result=[]
        for lo,hi in [(0,.1),(.1,.5),(.5,.9),(.9,1)]:
            mask=(prob>=lo)&((prob<hi) if hi<1 else (prob<=hi))
            n=int(mask.sum())
            if n: result.append([f'[{lo:.1f}, {hi:.1f}'+(']' if hi==1 else ')'),n,int(y[va][mask].sum()),round(float(prob[mask].mean()),4),round(float(y[va][mask].mean()),4)])
        return result
    tab('C3',['概率区间','记录数','阳性数','平均预测概率','实际阳性比例'],bins(p),'表 C3  验证集校准分箱｜Q5 概率评价。每行一个预设非空概率箱，合计24条；方括号包含端点，小括号不含。概率及比例无单位；平均概率并非区间中点。只展示观察，不拟合校准器。')
    joint=[]
    for c in [1,0]:
        for a,b in itertools.product([0,1],repeat=2):
            joint.append([c,a,b,int(((y[tr]==c)&(X[tr,3]==a)&(X[tr,4]==b)).sum())])
    tab('D1',['真实类别','尿意频繁','排尿痛','训练记录数'],joint,'表 D1  类别内联合计数｜Q6 条件独立。每行是一种类别及两症状取值组合；阳性类合计35、阴性类37，共72条训练记录。用未平滑经验频率比较联合概率与边缘概率乘积；不作独立性显著性检验。')
    grid=np.array(list(itertools.product([0,1],repeat=6)))
    dup=BernoulliNB(alpha=1).fit(np.column_stack([X[tr],X[tr,1]]),y[tr])
    original=model.predict_proba(grid)[:,1]; copied=dup.predict_proba(np.column_stack([grid,grid[:,1]]))[:,1]
    largest=np.argsort(abs(original-copied))[-3:][::-1]
    tab('D2',['六症状向量','六列模型概率','复制恶心后概率'],[[' '.join(map(str,grid[i])),f'{original[i]:.4f}',f'{copied[i]:.4f}'] for i in largest],'表 D2  复制症状的干预｜Q6 重复信息。训练同为72条；七列模型额外加入完全相同的恶心列。穷举64种六位向量并展示概率差最大3种，不是64名患者。向量顺序同表 B2；无新增信息。')
    testp=model.predict_proba(X[te])[:,1]; train_patterns=set(map(tuple,X[tr]))
    rawx=df.iloc[:,:6].astype(str).to_numpy(); rawtrain=set(map(tuple,rawx[tr]))
    d3=[['阈值0.50测试计数','TN=12，FP=0，FN=0，TP=12'],['测试阳性与阴性','各12条，总24条'],['训练二值症状组合','9种'],['验证二值症状组合','9种；24/24条的组合在训练出现'],['测试二值症状组合','8种；24/24条的组合在训练出现'],['原始六输入与训练相同','验证2/24条；测试6/24条'],['测试集此前是否被查看过','是：本课材料编写者在早期探索中看过测试结果；本课把它作为固定教学测试，按“冻结后才发放”模拟流程']]
    assert sum(tuple(row) in train_patterns for row in X[te])==24
    assert sum(tuple(row) in rawtrain for row in rawx[te])==6
    tab('D3',['检查项','结果'],d3,'表 D3  固定测试与组合覆盖｜Q6 泛化范围。每行一个审计项目；三集合与表 A3 一致。原始输入含连续体温；二值输入以≥38℃代替体温。组合重复不自动等于泄漏，患者独立性信息未提供。')
    tab('D4',['假设输入','数值'],[['筛查人数',10000],['患病率','1%'],['敏感度','95%'],['特异度','95%']],'表 D4  低患病率迁移场景｜Q6 accuracy作业。全部数值是假设输入，不来自120条记录。假设这些性能在该人群成立；要求推算预期人数，可得到整数，不代表真实部署验证。')
    prec,rec,_=precision_recall_curve(y[va],p)
    transformed=.25+.5*p
    two_model=BernoulliNB(alpha=1).fit(X[tr][:,two],y[tr])
    two_results=[]
    for a,b,c,n in grp.values:
        pr=float(two_model.predict_proba([[a,b]])[0,1]); two_results.append([int(a),int(b),int(c),int(n),pr,int(pr>=.5)])
    metrics={'val_log_loss':float(log_loss(y[va],p)),'val_brier':float(brier_score_loss(y[va],p)),'roc_auc':float(roc_auc_score(y[va],p)), 'ap':float(average_precision_score(y[va],p)),'pr_trapezoid':float(auc(rec,prec)), 'transformed_log_loss':float(log_loss(y[va],transformed)), 'transformed_brier':float(brier_score_loss(y[va],transformed)), 'test_log_loss':float(log_loss(y[te],testp)), 'test_brier':float(brier_score_loss(y[te],testp)), 'duplicate_class_changes':int(((original>=.5)!=(copied>=.5)).sum()),'duplicate_max_change':float(abs(original-copied).max()),'query_probabilities':model.predict_proba(queries)[:,1].tolist(), 'loss_A':float(log_loss(ly,pa)), 'loss_B':float(log_loss(ly,pb)), 'two_results':two_results,'two_confusion':confusion_matrix(y[va],two_model.predict(X[va][:,two]),labels=[0,1]).tolist()}
    return dict(df=df,X=X,y=y,tr=tr,va=va,te=te,model=model,p=p,tables=tables,metrics=metrics,raw=raw,grid=grid,original=original,copied=copied,counts=counts)

def generate():
    z=compute(); ASSET.mkdir(parents=True,exist_ok=True)
    z['df'].to_csv(ASSET/'acute-inflammations.csv',index=False)
    for label,t in z['tables'].items():
        pd.DataFrame(t['rows'],columns=t['headers']).to_csv(ASSET/f'packet-{label.lower()}.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame([(int(i+1),name) for name in ['tr','va','te'] for i in z[name]],columns=['source_row','split']).to_csv(ASSET/'split-indices.csv',index=False)
    pd.DataFrame({'source_row':z['va']+1,'y':z['y'][z['va']],'probability':z['p']}).to_csv(ASSET/'validation-predictions.csv',index=False)
    pd.DataFrame(np.column_stack([z['grid'],z['original'],z['copied']]),columns=CN+['original_probability','duplicated_probability']).to_csv(ASSET/'redundancy-all64.csv',index=False)
    pd.DataFrame([{'records':120,'features':6,'targets':2,'positive':59,'negative':61,'missing_cells':0,'raw_unique_inputs':99,'binary_unique_inputs':9}]).to_csv(ASSET/'dataset-summary.csv',index=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.sans-serif':['Microsoft YaHei','SimHei','DejaVu Sans'],'axes.unicode_minus':False,'font.size':11})
    fig,axes=plt.subplots(1,2,figsize=(10.6,3.9),layout='constrained')
    fpr,tpr,_=roc_curve(z['y'][z['va']],z['p']); precision,recall,_=precision_recall_curve(z['y'][z['va']],z['p'])
    axes[0].plot(fpr,tpr,color='#234E70',lw=2,label='六症状NB'); axes[0].plot([0,1],[0,1],'--',color='#888888',label='随机排序参考')
    axes[1].plot(recall,precision,color='#234E70',lw=2,label='六症状NB'); axes[1].axhline(.5,ls='--',color='#888888',label='验证集阳性比例')
    for t,col,offset in [(.1,'#B34A38',(-45,-22)),(.5,'#2A785E',(12,-22)),(.9,'#785498',(-50,-36))]:
        tn,fp,fn,tp=confusion_matrix(z['y'][z['va']],z['p']>=t,labels=[0,1]).ravel()
        for ax,xy in [(axes[0],(fp/(fp+tn),tp/(tp+fn))),(axes[1],(tp/(tp+fn),tp/(tp+fp)))]:
            ax.scatter(*xy,s=40,color=col,zorder=5); ax.annotate(f'阈值{t:.2f}',xy,xytext=offset,textcoords='offset points',fontsize=9,color=col)
    axes[0].set(xlabel='假阳性率  FP/(FP+TN)',ylabel='真阳性率  TP/(TP+FN)',title='ROC  AUC=1.000')
    axes[1].set(xlabel='召回率 Recall',ylabel='精确率 Precision',title='PR  梯形面积=1.000；AP=1.000')
    for ax in axes: ax.set_xlim(-.03,1.03); ax.set_ylim(-.03,1.08); ax.legend(loc='lower right',fontsize=8); ax.grid(alpha=.15)
    fig.savefig(ASSET/'packet-c2-ranking.png',dpi=180); plt.close(fig)
    # Formula images use genuine mathematical typesetting, not exposed LaTeX text.
    formulas={
      'bayes':r'$P(Y=1\mid x)=\frac{S_1}{S_1+S_0},\quad S_c=P(Y=c)\prod_{j=1}^{6}P(X_j=x_j\mid Y=c)$',
      'bernoulli':r'$\theta_{jc}=\frac{n_{jc}+1}{n_c+2},\quad P(X_j=x_j\mid Y=c)=\theta_{jc}^{x_j}(1-\theta_{jc})^{1-x_j}$',
      'loss':r'$L_{\mathrm{CE}}=-\frac{1}{n}\sum_{i=1}^n[y_i\ln p_i+(1-y_i)\ln(1-p_i)]$',
      'mse':r'$L_{\mathrm{MSE}}=\frac{1}{n}\sum_{i=1}^n(y_i-\hat y_i)^2$',
    }
    for name,formula in formulas.items():
        fig=plt.figure(figsize=(10,.85)); fig.text(.5,.5,formula,ha='center',va='center',fontsize=20);fig.savefig(ASSET/f'equation-{name}.png',dpi=180,bbox_inches='tight',pad_inches=.1);plt.close(fig)
    out={'tables':z['tables'],'metrics':z['metrics'],'source_sha256':hashlib.sha256(z['raw'].read_bytes()).hexdigest(),'versions':{}}
    import sklearn,sys
    out['versions']={'python':sys.version.split()[0],'sklearn':sklearn.__version__,'numpy':np.__version__,'pandas':pd.__version__}
    (ASSET/'computed-evidence.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(z['metrics'],ensure_ascii=False,indent=2))

if __name__=='__main__': generate()
