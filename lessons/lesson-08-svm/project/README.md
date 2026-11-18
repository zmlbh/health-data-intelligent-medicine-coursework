# 第 9 讲：SVM 与 Margin

通过 UCI 脊柱生物力学数据，理解 SVM 怎样确定边界、容忍违例，以及通过核函数改变相似度。课堂解释围绕概念和受控实验展开。

## 上课材料

- [课堂导入 PPT](slides/svm-pbl-intro.pptx)：概念、数据、学习问题和实验理由，保留计算与结果解释给学生。
- [学生工作单](student-worksheet.md)：先预测，再运行，再解释。
- [实验 Notebook](svm-lab.ipynb)：按工作单顺序运行，默认关闭测试标签。
- [教师参考](teacher-reference.md)：实测结果、误区和教学提示，勿提前发放。
- [数据说明](data/README.md)：来源、字段、分组、文件与使用边界。
- [实验设计](experiment-design.md)及[工作计划](plan.md)。

## 运行

从本课文件夹打开终端，Python 3.11+：

```powershell
python -m pip install -r requirements.txt
jupyter lab svm-lab.ipynb
```

数据已随课程保存，不需要联网即可实验。重新整理固定数据：

```powershell
python -B scripts/prepare_data.py
```

仅在需要重新下载官方原档时加 `--download`。脚本不会修改原标签。教师复现实验：

```powershell
python -B scripts/teacher_analysis.py
```

教师结果、图和缓存输出到项目根目录 `.tmp/svm/`，不作为学生交付物。已用 Python 3.13.12、scikit-learn 1.8.0 完成实验检查；依赖实际版本保存在数据清单中。Notebook 保存为空输出版本。`scripts/build_notebook.py` 可重新生成它；`scripts/build_slides.mjs` 需本机 Artifact Tool 运行环境和 presentations 技能路径，可通过环境变量覆盖。

## 发放

发给学生：工作单、Notebook、`scripts/lab_utils.py`、`data/student/` 和数据说明。原始归档与 `data/teacher/` 由教师保留，测试阶段再提供测试标签。完整仓库本身不是访问控制系统；默认关闭测试是教学协议。教师已为可行性检查查看过测试结果，课程不宣称这是全新独立验证。

本课使用两个预先指定的特征，目的是观察二维几何机制。所得性能不是该数据集所有可用信息的性能上限，也不是诊断效用证明。
