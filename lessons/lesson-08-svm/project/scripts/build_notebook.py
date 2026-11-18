"""Build the student notebook with empty outputs. No data fitting at build time."""
from pathlib import Path
import hashlib
import json
import textwrap

BASE = Path(__file__).resolve().parents[1]
cells = []

def add(kind, source):
    source = textwrap.dedent(source).strip() + '\n'
    cell = {'cell_type': kind, 'id': hashlib.sha256((str(len(cells))+source).encode()).hexdigest()[:12],
            'metadata': {}, 'source': source.splitlines(keepends=True)}
    if kind == 'code': cell.update(execution_count=None, outputs=[])
    cells.append(cell)

def md(s): add('markdown', s)
def code(s): add('code', s)

md('''
# 第9讲：SVM怎样确定边界？

配合 `student-worksheet.md`，先写预测，再运行。数据是UCI Vertebral Column真实记录，
不是模拟患者。两个输入预先固定，八点子集仅用于几何，正式实验使用完整训练集。

本Notebook不自动保存图表和结果。需要导出时只写项目根目录 `.tmp/svm/`。
默认不读取测试标签。G为可选扩展，放在最后测试之前，避免根据测试追加解释或调参。
''')
code('''
import os, sys
from pathlib import Path
sys.dont_write_bytecode = True
here = Path.cwd().resolve()
lesson = next((q for p in [here, *here.parents]
               for q in [p, p/'class2026/materials/9. SVM']
               if (q/'scripts/lab_utils.py').is_file()), None)
if lesson is None:
    raise RuntimeError('请从项目根目录、本课文件夹或本课Notebook所在目录运行。')
repo = lesson.parents[2]
out = repo/'.tmp/svm/student'
out.mkdir(parents=True, exist_ok=True)
os.environ.setdefault('MPLCONFIGDIR', str(repo/'.tmp/svm/matplotlib'))
sys.path.insert(0, str(lesson/'scripts'))
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display
from lab_utils import *
pd.set_option('display.max_columns', 12)
''')
md('''
## A．记录、输入和目标

先完成工作单A。数据说明见 `data/README.md`。
图先显示全部训练范围，极端值也保留。后续边界图放大主要区域时会报告范围外点数，
范围外的点仍参与拟合。不要因为极值影响画图就删除记录。
''')
code('''
train, validation = load_development()
display(train.head())
display(pd.DataFrame({'train': train.abnormal.value_counts(),
                      'validation': validation.abnormal.value_counts()}).sort_index())
assert set(train.sample_id).isdisjoint(validation.sample_id)
fig, ax = plt.subplots(figsize=(8, 5))
for cls, color, marker in [(0, '#087c77', 'o'), (1, '#b75d24', '^')]:
    data = train[train.abnormal == cls]
    ax.scatter(data[FEATURES[0]], data[FEATURES[1]], color=color,
               marker=marker, alpha=.7, label=['NO', 'AB'][cls])
ax.set(xlabel='Pelvic incidence (source scale)', ylabel='Spondylolisthesis (source scale)',
       title='All 186 training records: full extent')
ax.legend(); plt.show()
''')
md('''
## B．三条候选线与距离

先观察图，不运行下一格数值核对。三条线的法向量相同，截距不同。
按工作单手算V061的分数与距离，解释同乘3后发生什么，再计算每条线最近的带标签距离。

`geometry_experiment`从训练集有意选择4个NO与4个AB；scaler拟合全训练集。
其大C拟合经核对近似展示可分数据的hard margin，不是专用hard-margin求解器。
''')
code('''
geo = geometry_experiment(train)
z, y = geo['z'], geo['subset'].abnormal.to_numpy()
w, b = geo['model'].coef_[0], geo['model'].intercept_[0]
fig, ax = plt.subplots(figsize=(7, 6))
for cls, color, marker in [(0, '#087c77', 'o'), (1, '#b75d24', '^')]:
    mask = y == cls
    ax.scatter(z[mask, 0], z[mask, 1], c=color, marker=marker, label=['NO', 'AB'][cls])
for i, name in enumerate(geo['subset'].sample_id):
    ax.annotate(name, z[i], xytext=(5, 5), textcoords='offset points')
xx = np.linspace(-2.1, 1.8, 100)
for offset, color in [(-.6, '#9c562b'), (0, '#193638'), (.6, '#5c7b9c')]:
    ax.plot(xx, -(w[0]*xx+b+offset)/w[1], color=color, label=f'b offset {offset:+.1f}')
ax.set(xlabel='z1', ylabel='z2', xlim=(-2.1, 1.8), ylim=(-1.3, 2.2), aspect='equal')
ax.legend(); plt.show()
display(geo['table'][['sample_id', 'z1', 'z2', 'abnormal']])
''')
md('先把你的预测与手算写在工作单B，之后运行下面的核对。')
code('''
print('w =', w, 'b =', b, '||w|| =', np.linalg.norm(w))
display(geo['candidates'])
display(geo['table'][['sample_id', 'score', 'signed_margin', 'distance', 'support']])
print('Full canonical band width:', 2/np.linalg.norm(w))
draw_boundary(geo['model'], train, 'Geometry subset: f = -1, 0, +1',
              True, geo['scaler'], geo['subset'])
plt.show()
''')
md('''
## C．支持向量与矛盾标签

先预测哪种删除会改变边界，以及重估scaler会混入什么因素。
本格比较删除非SV V072与SV V061，scaler冻结。

矛盾实验另外复制一点、给相反标签，只是人工反事实，不修改任何原始数据。
先写出hard-margin约束的矛盾，再看soft-margin拟合。不能把结果解释为原数据有错标。
''')
code('''
display(geo['changes'])
display(geo['contradiction'])
yf = np.array([-.5, .4, 1., 1.8])
display(pd.DataFrame({'y_times_f': yf, 'hinge': np.maximum(0, 1-yf), 'misclassified': yf < 0}))
''')
md('''
## D．只改变linear C

先用目标 `½||w||²+CΣhinge` 预测改变方向。下面统一拟合全部预定配置，后续重复使用。
先看linear切片，别先寻找最高分。mean_hinge乘186才是目标中的hinge总和。
线性宽度在训练标准化空间中，soft margin允许参考带内有点。
''')
code('''
grid, models = parameter_experiment(train, validation)
linear = grid[grid.kernel == 'linear']
display(linear[['C', 'linear_width', 'mean_hinge', 'regularizer', 'objective',
                'train_errors', 'n_sv', 'val_balanced_accuracy']])
fig, axes = plt.subplots(1, 3, figsize=(13, 3.5))
for ax, column in zip(axes, ['linear_width', 'mean_hinge', 'val_balanced_accuracy']):
    ax.semilogx(linear.C, linear[column], 'o-', color='#087c77')
    ax.set(xlabel='C', ylabel=column)
fig.tight_layout(); plt.show()
for C in [.01, 1., 100.]:
    draw_boundary(models[('linear', C, .1)], train, f'Linear C={C}')
    plt.show()
''')
md('''
## E．kernel与gamma的单因素切片

先手算距离1/2下两种gamma的RBF相似度。固定C=1看gamma，再固定gamma=10看C。
最后才读联合网格。原平面RBF的f=±1是分数轮廓，不能当等距margin线。
Polynomial仅展示一个配置，不展开搜索。
''')
code('''
for gamma in [.1, 1.]:
    print('gamma', gamma, 'K at distance 1, 2:', np.exp(-gamma*np.array([1., 2.])**2))
rbf = grid[grid.kernel == 'rbf']
columns = ['C', 'gamma', 'train_balanced_accuracy', 'val_balanced_accuracy', 'n_sv']
display(rbf[rbf.C == 1][columns])
display(rbf[rbf.gamma == 10][columns])
for gamma in [.01, 1., 10.]:
    draw_boundary(models[('rbf', 1., gamma)], train, f'RBF C=1, gamma={gamma}')
    plt.show()
display(rbf.pivot(index='C', columns='gamma', values='val_balanced_accuracy'))
for C in [10., 100.]:
    draw_boundary(models[('rbf', C, 10.)], train, f'RBF C={C}, gamma=10')
    plt.show()
for key in [('linear', 1., .1), ('poly', 1., .1), ('rbf', 1., .1)]:
    draw_boundary(models[key], train, f'Kernel comparison: {key}')
    plt.show()
''')
md('''
## F1．同信息、不同单位

先预测x₁乘100会怎样改变距离。这里固定C=1、gamma=.1，不重新选择参数。
两个因素：单位是否改变、是否使用训练标准化。
只比较分数不变性，不把此设置当作各流程的最佳性能。
''')
code('''
scaling, score_changes = scaling_experiment(train, validation)
display(scaling[['scaled', 'unit', 'val_balanced_accuracy', 'n_sv']])
print('max score change by scaled=False/True:', score_changes)
''')
md('''
## G．可选扩展：冻结模型的输入扰动

先冻结两个家族的验证配置。规则是验证balanced accuracy最高，平分取较小C再较小gamma。
这不是跨家族选冠军。扩展在测试之前进行，扰动假设为独立高斯噪声，不是真实测量误差。
默认跳过。即使不运行扩展，也会生成供F2记录的配置。
''')
code('''
configs = select_validation_configs(grid)
print('Validation-only configurations:', configs)
RUN_OPTIONAL_NOISE = False
if RUN_OPTIONAL_NOISE:
    for family, key in configs.items():
        print(family)
        display(noise_experiment(models[key], train, validation))
''')
md('''
## F2．记录后打开保留集

先完成工作单F的配置记录，并写出测试要检查什么。默认两个开关均为False。
函数在开关关闭时不读取测试标签。按教师安排发放标签后再开启。

训练仍为原186条，不把验证重新加入；不以测试继续搜索。
教师预跑已查看测试，此处只演示保留集流程，不宣称全新独立科研确认。
原生SVM分数不是概率，ROC-AUC用分数排序。
''')
code('''
FREEZE_CONFIRMED = False
OPEN_TEST = False
display(evaluate_locked(configs, freeze_confirmed=FREEZE_CONFIRMED, open_test=OPEN_TEST))
''')
md('''
## 解释与提交

完成工作单的一页概念解释：至少用两个受控实验说明机制、一个优势、一个局限和适用条件。
保留你在运行前的预测。不要提交整份自动输出，也不要用测试分数给模型排名。
''')

if __name__ == '__main__':
    notebook = {'cells': cells, 'metadata': {'kernelspec': {'display_name': 'Python 3',
                 'language': 'python', 'name': 'python3'}, 'language_info': {'name': 'python', 'version': '3.13'}},
                'nbformat': 4, 'nbformat_minor': 5}
    (BASE/'svm-lab.ipynb').write_text(json.dumps(notebook, ensure_ascii=False, indent=1)+'\n', encoding='utf-8')
    print(f'Wrote {len(cells)} empty-output cells')
