# Codex 使用记录摘要

以下内容来自截至 2026-11-18 可访问的 Codex 历史，已删除私人绝对路径和逐字聊天内容。

## 整理集成学习顶刊风格论文

- 任务：阅读课件、PBL 要求、计划、数据和代码，形成双栏可编辑课程论文。
- Codex 协助：在两个候选数据集中选择 CTG；按原始监护记录分组，避免记录片段泄漏；将树的不稳定性、Bootstrap/OOB、Bagging、Random Forest、Boosting 和特征重要性边界写入论文。
- 对应产出：`project/submission_materials/CTG_Ensemble_Learning_Conference_Paper_7pages.docx` 及构建代码。

## 优化 Ensemble 投稿材料与图表

- 任务：改进双栏版式、表格、图形数量、公式、引用顺序和论文结构。
- Codex 协助：建立 LR、SVM、单树、Bagging、Random Forest、Gradient Boosting 的同协议比较；补充树深度、Bootstrap 根节点、树数收敛、预测稳定性和特征重要性实验；修正强制分页和宽表裁切。
- 用户核查：指出标题、章节、页脚、表格边框、图表数量和参考文献顺序等问题，并要求多轮修改。

## 数据量核查

- 历史记录核对出实际建模使用 `train.csv` 1,279 条和 `validation.csv` 424 条，共 1,703 条。
- `locked-test-features.csv` 有 423 条，不参与当前开发实验。
- 完整数据量 2,126 不能被误写为当前模型训练与交叉验证样本量。

记录类型：脱敏任务摘要，不是完整聊天导出。
