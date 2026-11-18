# 第 10 讲：集成学习与 Bootstrapping

课程问题是：多个弱模型怎样组合成更稳定的模型？学生先学会一棵决策树怎样预测、为什么不稳定，再在同一份数据、同一验证协议下比较单树、bagging、随机森林和 boosting，并与逻辑回归、SVM 对照；用“平均降低方差”解释集成为什么有效，用 bootstrap 解释训练扰动与不确定性，最后落到超参数、特征重要性和选型等应用问题。

## 数据：两套方案，由授课教师二选一

| | 方案 A：WDBC | 方案 B：CTG |
|---|---|---|
| 文件夹 | `data/` | `data-ctg/` |
| 内容 | 乳腺肿块细胞核特征，569 条，30 个特征 | 胎心监护信号片段特征，2126 段 / 352 个录音，21 个特征 |
| 标签 | `malignant=1` | `pathologic=1` |
| 能看到的现象 | 集成大幅改善单树，但不胜过 LR / SVM | 集成胜过单树，也在 PR-AUC、balanced accuracy 上胜过 LR / SVM；RF 明显好于 bagging |

两套数据的对照、参考结果和选择建议见 `teacher-reference.md` 开头。选定后删除课件中另一张数据页（第 3 页或第 4 页）。

## 文件

- `slides/ensemble-pbl.pptx`：PBL 导入课件（19 页）：决策树、集成为什么有效、bagging / 随机森林 / boosting 机制、常用实现与超参数、特征重要性、选型、实验协议与证据边界。
- `student-worksheet.md`：学生工作单 A–H，先预测再分析，最后写证据边界；分析内容不限于工作单。
- `teacher-reference.md`：数据方案对照、教师答案、两套数据的参考结果、追问清单、课堂流程和评分建议。
- `workplan.md`：课程设计说明。
- `scripts/prepare_data.py`、`scripts/prepare_data_ctg.py`：生成两套数据的固定划分。
- `scripts/demo_ensemble.py`：课堂演示和主要比较，结果写入项目根目录 `.tmp/ensemble/<数据名>/`。
- `scripts/build_slides.mjs`：重建课件，需要本机 Artifact Tool 运行环境（环境变量 `CODEX_ARTIFACT_RUNTIME`）。
- `data/`、`data-ctg/`：`student/` 为学生数据，`teacher/` 为教师测试标签与完整数据；各自的 `README.md` 说明来源、字段与使用边界。

## 运行

```powershell
python -m pip install -r requirements.txt
python scripts/prepare_data.py
python scripts/prepare_data_ctg.py
python scripts/demo_ensemble.py --data wdbc
python scripts/demo_ensemble.py --data ctg
```

脚本使用固定随机种子和预设参数，避免把课程变成大规模调参竞赛。方案 B 的交叉验证按 `recording_id` 分组。测试标签不被演示脚本读取；学生只能在教师安排的最后一步评价锁定测试集。

方法参考：<https://scikit-learn.org/stable/modules/ensemble.html>；XGBoost 原理：<https://xgboost.readthedocs.io/en/stable/tutorials/model.html>。
