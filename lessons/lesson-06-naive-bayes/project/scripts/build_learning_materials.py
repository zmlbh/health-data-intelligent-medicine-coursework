"""Build the editable lesson text and clean student notebook (no computed outputs)."""
from pathlib import Path
import json

BASE = Path(__file__).resolve().parents[1]

# Student and design Markdown are authoritative sources; do not overwrite them.

def build_notebook():
    cells = []
    def md(s): cells.append(dict(cell_type='markdown',metadata={},source=s.splitlines(True)))
    def code(s): cells.append(dict(cell_type='code',metadata={},source=s.splitlines(True),outputs=[],execution_count=None))
    md('# 第7讲 从症状到预测 机器学习基础与朴素贝叶斯\n配合新版工作单七项任务。任务1与3运行A；任务4运行A2与C；任务5和6运行B；任务7固定方案后运行D。核心问题是怎样从数据学习模型并评价预测。测试默认关闭。')
    code('''from pathlib import Path
import sys, json
sys.dont_write_bytecode = True
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display
from sklearn.naive_bayes import BernoulliNB
from sklearn.metrics import RocCurveDisplay, PrecisionRecallDisplay
candidates = [Path.cwd(), Path.cwd().parent,
              Path.cwd()/'class2026/materials/7. Naive-Bayes']
BASE = next(p for p in candidates if (p/'scripts/lab_utils.py').exists())
sys.path.insert(0,str(BASE/'scripts'))
from lab_utils import *
REPO = next((p for p in [BASE,*BASE.parents] if (p/'.gitignore').exists()), BASE)
OUT = REPO/'.tmp/naive-bayes/student-results'
OUT.mkdir(parents=True,exist_ok=True)
FREEZE_CONFIRMED = False
OPEN_LOCKED_TEST = False
TRANSFER_FREEZE_CONFIRMED = False
OPEN_TRANSFER_TEST = False
train = pd.read_csv(BASE/'data/student/train.csv')
val = pd.read_csv(BASE/'data/student/validation.csv')
TARGET = 'bladder_inflammation'
print('模型输入:',FEATURES)
''')
    md('## A 数据审计\n对应任务1与3。观察训练表并记录数据划分；仅审计开发数据；完全重复比较去掉ID后的全部列，模式比较只取六输入。读取来源说明，并核对作者与构建目的。')
    code('''for name, frame in [('train',train),('validation',val)]:
    print(name, 'n=',len(frame),'labels=',frame[TARGET].value_counts().to_dict(),
          'missing=',int(frame.isna().sum().sum()),
          'illegal bits=',int((~frame[FEATURES].isin([0,1])).sum().sum()),
          'extra duplicates=',int(frame.drop(columns='sample_id').duplicated().sum()),
          'unique profiles=',len(frame[FEATURES].drop_duplicates()))
assert not set(train.sample_id)&set(val.sample_id)
profiles_train = set(map(tuple,train[FEATURES].to_numpy()))
print('validation rows with profiles seen in train:',
      sum(tuple(x) in profiles_train for x in val[FEATURES].to_numpy()))
display(train.head())
''')
    md('## A2 Bayes 手算核对\n先完成任务4的六项似然及归一化，再运行。无症状也有似然项。')
    code('''model = fit_model(train)
x = [0,0,0,1,1,1]
hand, weights, posterior = hand_calculation(train,x)
display(hand)
print('weights=',weights,'posterior=',posterior)
print('sklearn=',model.predict_proba(pd.DataFrame([x],columns=FEATURES))[0,1])
''')
    md('## B 验证集、baseline 与阈值\n对应任务5与6。先查看训练与验证损失，再比较0.5阈值，然后按预先声明的规则选择，禁止访问test。PR摘要为AP。')
    code('''vp = model.predict_proba(val[FEATURES])[:,1]
baseline_p = np.full(len(val),train[TARGET].mean())
train_p = model.predict_proba(train[FEATURES])[:,1]
display(pd.DataFrame({
    'NB_train': scores(train[TARGET],train_p),
    'NB_validation': scores(val[TARGET],vp),
    'Prior_only_validation': scores(val[TARGET],baseline_p)
}).T[['accuracy','log_loss']])
display(pd.DataFrame({'prior_only':scores(val[TARGET],baseline_p),
                      'NB_at_0.5':scores(val[TARGET],vp)}).T)
thresholds = threshold_table(val[TARGET],vp)
display(thresholds)
threshold = choose_threshold(thresholds)
assert threshold is not None, '预设规则无可行阈值：停止并报告，不得打开test。'
print('validation-selected threshold:',threshold)
thresholds.to_csv(OUT/'B-thresholds.csv',index=False)
fig,axes=plt.subplots(1,2,figsize=(10,4))
RocCurveDisplay.from_predictions(val[TARGET],vp,ax=axes[0])
PrecisionRecallDisplay.from_predictions(val[TARGET],vp,ax=axes[1])
fig.tight_layout(); fig.savefig(OUT/'B-ranking.png',dpi=150); plt.show()
''')
    md('## C 类内依赖、重复输入与概率\n对应任务4.4与7.2；类内依赖的详细统计为选做。比较0/1/5份额外腰痛副本，原主模型和阈值保持不变。不要预设一次复制必然使评分变差。')
    code('''vp = model.predict_proba(val[FEATURES])[:,1]
dep = dependence(train).sort_values('difference',key=abs,ascending=False)
display(dep.head(10))
duplicates=[]
for copies in [0,1,5]:
    tx,vx=train[FEATURES].copy(),val[FEATURES].copy()
    for i in range(copies):
        tx[f'copy_{i}']=tx.lumbar_pain
        vx[f'copy_{i}']=vx.lumbar_pain
    dm=BernoulliNB(alpha=1,binarize=None).fit(tx,train[TARGET])
    dp=dm.predict_proba(vx)[:,1]
    duplicates.append(dict(extra_copies=copies,**scores(val[TARGET],dp),
                           mean_max_probability=np.maximum(dp,1-dp).mean()))
    changed=pd.DataFrame({'sample_id':val.sample_id,'y':val[TARGET],
                          'original_p':vp,'duplicate_p':dp,'change':abs(dp-vp)})
    print('extra copies=',copies); display(changed.sort_values('change',ascending=False).head(3))
display(pd.DataFrame(duplicates))
rel = reliability(val[TARGET],vp)
display(rel)
fig,ax=plt.subplots(figsize=(5,4))
ax.plot([0,1],[0,1],'--',color='gray')
ax.plot(rel.mean_probability,rel.observed_fraction,'o-')
ax.set(xlim=(0,1),ylim=(0,1),xlabel='Mean predicted probability',ylabel='Observed fraction')
fig.tight_layout(); fig.savefig(OUT/'C-reliability.png',dpi=150); plt.show()
''')
    md('## 冻结记录\n先完成任务6的阈值选择，在任务7.3填写固定方案和日期，提交教师；获得释放后修改顶部两个开关并从头运行。原72条模型不重训。保存冻结文件的行为本身不能阻止事后修改；教师应保留首次提交。')
    code('''freeze = dict(target=TARGET,features=FEATURES,alpha=1,fever_cutoff=38,
              training_ids=train.sample_id.tolist(),threshold=threshold,
              refit_train_plus_validation=False)
if FREEZE_CONFIRMED:
    (OUT/'frozen-protocol.json').write_text(json.dumps(freeze,indent=2),encoding='utf-8')
else:
    print('尚未确认冻结；D不运行。请先完成并提交冻结记录。')
''')
    md('## D 锁定测试、区间与压力测试\n对应任务7.3。只有教师释放标签后运行；区间与压力测试属于选做输出。区间依赖二项独立抽样近似，原数据不支持直接推论临床总体。压力分位范围是给定模拟机制下的波动。')
    code('''if OPEN_LOCKED_TEST:
    assert FREEZE_CONFIRMED, '必须先冻结主方案'
    test = pd.read_csv(BASE/'data/student/locked-test-features.csv').merge(
        pd.read_csv(BASE/'data/teacher/locked-test-labels.csv'),
        on='sample_id',validate='one_to_one',sort=False)
    assert not set(test.sample_id)&(set(train.sample_id)|set(val.sample_id))
    test_p=model.predict_proba(test[FEATURES])[:,1]
    test_scores=scores(test[TARGET],test_p,threshold)
    display(pd.Series(test_scores))
    intervals={'accuracy':wilson(test_scores['tn']+test_scores['tp'],len(test)),
               'sensitivity':wilson(test_scores['tp'],test_scores['tp']+test_scores['fn']),
               'specificity':wilson(test_scores['tn'],test_scores['tn']+test_scores['fp'])}
    print('Wilson95%',intervals)
    print('test profiles seen in train:',sum(tuple(x) in profiles_train for x in test[FEATURES].to_numpy()))
    stress_results=stress(model,test,test[TARGET],threshold)
    display(stress_results)
    stress_results.to_csv(OUT/'D-stress.csv',index=False)
else:
    print('测试关闭。完成A–C与冻结记录后，等待教师释放。')
''')
    md('## E 选做 更换预测目标为 nephritis\n保持完全相同的行划分。先完成validation与依赖检查，再提交第二份冻结记录。换标签不等于外部验证。')
    code('''transfer_model=fit_model(train,'nephritis')
np_val=transfer_model.predict_proba(val[FEATURES])[:,1]
transfer_thresholds=threshold_table(val.nephritis,np_val)
display(transfer_thresholds)
transfer_threshold=choose_threshold(transfer_thresholds)
display(dependence(train,'nephritis').sort_values('difference',key=abs,ascending=False).head())
print('transfer validation threshold=',transfer_threshold)
if TRANSFER_FREEZE_CONFIRMED:
    assert transfer_threshold is not None
    (OUT/'transfer-frozen-protocol.json').write_text(json.dumps(
        dict(target='nephritis',features=FEATURES,alpha=1,threshold=transfer_threshold,
             training_ids=train.sample_id.tolist()),indent=2),encoding='utf-8')
if OPEN_TRANSFER_TEST:
    assert OPEN_LOCKED_TEST and FREEZE_CONFIRMED and TRANSFER_FREEZE_CONFIRMED
    transfer_scores=scores(test.nephritis,transfer_model.predict_proba(test[FEATURES])[:,1],transfer_threshold)
    display(pd.Series(transfer_scores))
    print('阳性分母=',int(test.nephritis.sum()),'阴性分母=',int((test.nephritis==0).sum()))
else:
    print('迁移测试关闭；先冻结并提交第二份方案。')
''')
    md('## 学习综合\n完成任务7.4的一页说明或流程图，用自己的计算解释七个核心知识点。引用输出时写明数据部分、阈值和分母。不要求审批结论或CERB。结果和图保存在项目根目录 `.tmp/naive-bayes/student-results/`，不要提交这些缓存。')
    nb=dict(cells=cells,metadata=dict(kernelspec=dict(display_name='Python 3',language='python',name='python3'),
            language_info=dict(name='python',version='3.13')),nbformat=4,nbformat_minor=5)
    for i,c in enumerate(cells): c['id']=f'nb7-{i:03d}'
    (BASE/'notebooks').mkdir(exist_ok=True)
    (BASE/'notebooks/naive-bayes-lab.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')

if __name__=='__main__':
    build_notebook()
