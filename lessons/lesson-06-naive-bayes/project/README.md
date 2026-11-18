# 第 7 讲 机器学习基础与朴素贝叶斯

本课围绕“怎样用症状数据学到预测模型，并知道它预测得好不好”展开。新版工作单以七项核心知识为主线，让学生定义模型、区分训练与预测、安排三类数据、手算 Bayes、计算损失、评价分类并理解 accuracy 的局限。

**版本说明（2026-10-21）**：Markdown 工作单、教师参考、授课设计、配套 Notebook 及新版实验导入 PPT 已按七项核心任务组织。现有 student-worksheet.docx、teacher-reference.docx 和 naive-bayes-pbl.pptx 仍是旧版，不要与新版混用。需要打印时可从新版 Markdown 导出。

## 课程文件

| 文件 | 用途 |
|---|---|
| [experiment-design.md](experiment-design.md) | 两次45分钟课堂、课间实验及分阶段释放方案 |
| [student-worksheet.docx](student-worksheet.docx) / [Markdown](student-worksheet.md) | Markdown 为新版七项学习任务；DOCX 为待更新旧版 |
| [teacher-reference.docx](teacher-reference.docx) / [Markdown](teacher-reference.md) | Markdown 为新版逐题参考；DOCX 为待更新旧版 |
| [slides/naive-bayes-experiment-intro.pptx](slides/naive-bayes-experiment-intro.pptx) | 新版21页可编辑实验导入：概念解释、数据、问题及实验设计理由，计算和结果留给学生 |
| [slides/naive-bayes-pbl.pptx](slides/naive-bayes-pbl.pptx) | 旧版31页幻灯片，保留供历史参考，不配套新版工作单使用 |
| [notebooks/naive-bayes-lab.ipynb](notebooks/naive-bayes-lab.ipynb) | 干净学生Notebook，测试默认关闭 |
| [data/README.md](data/README.md) | 来源、许可、原始格式、编码和字段说明 |
| [DATASET-RECOMMENDATIONS.md](DATASET-RECOMMENDATIONS.md) | 主数据选择理由与糖尿病问卷选做数据 |
| [WORKPLAN.md](WORKPLAN.md) | PBL课程目标与原始授课框架 |

## 运行实验

在本目录创建Python环境（建议Python3.11–3.13），安装依赖，再启动Jupyter。Notebook可从本目录、notebooks目录或项目根目录运行。

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
jupyter lab notebooks/naive-bayes-lab.ipynb
```

原始数据和已划分CSV均已提供，实验运行不需要联网下载。CSV为UTF-8；原始ZIP内文件不是默认CSV格式。主模型只使用六项二元症状，不能把ID或另一疾病标签作为特征。

学生按工作单运行：任务1/3用A，任务4用A2和C，任务5/6用B；提交冻结协议后，教师释放测试标签到`data/teacher/locked-test-labels.csv`。将Notebook顶部`FREEZE_CONFIRMED`和`OPEN_LOCKED_TEST`设为True再从头运行D。迁移nephritis须另行冻结后打开另外两个开关。训练始终为原72条，不合并validation重训。

教师完整复现：

```powershell
python scripts/prepare_data.py
python scripts/audit_datasets.py
python scripts/teacher_analysis.py
```

以上分析输出统一写入项目根目录`.tmp/naive-bayes/`，不要提交运行缓存。`prepare_data.py`会按固定协议重新生成正式CSV；已有数据无需重复运行。Markdown 工作单和授课设计直接编辑，是正式文本来源；`build_learning_materials.py`只生成空白Notebook，不再用内嵌旧文本覆盖它们。`build_docx.py`为旧版转换脚本，重新导出后仍需检查版面。PPT作者脚本为`build_slides.mjs`，需要Codex artifact-tool运行环境，学生运行实验无需安装该工具。

## 教师分发与授课

发给学生：student-worksheet、notebooks、data/student、scripts/lab_utils.py及requirements.txt。教师保留data/raw、data/teacher、本README的教师说明和teacher-reference。Notebook不存在技术访问控制，原始ZIP也可还原标签；严格盲评时请教师在独立环境执行冻结方案。

新版课堂：第一次45分钟完成任务1–3；课间60–90分钟完成任务4–5及任务6实验记录；第二次45分钟讨论任务6–7。压力测试、区间、排序和换标签为选做，不计核心满分。详细安排见 experiment-design.md。新版实验导入 PPT 讲解概念与设计逻辑，不预先展示计算答案和测试结果。生成源为 scripts/build_intro_slides.mjs。旧幻灯片中的审批投票和CERB活动不再使用。

## 结论边界

主数据是专家创建用于专家系统测试的120条记录，不是真实独立临床队列。六输入全数据只有9种组合。固定内部测试能获得24/24，但全部测试输入模式都见于训练；这支持规则再现，不证明跨患者或跨医院泛化。Wilson区间和输入翻转模拟也不能替代独立临床验证。

数据：Jacek Czerniak，UCI Acute Inflammations，DOI [10.24432/C5V59S](https://doi.org/10.24432/C5V59S)，CC BY 4.0。本课进行了温度二元化、0/1编码与固定划分。选做糖尿病问卷为另一疾病任务，不充当主模型外部验证。数据详细署名和许可见data/README.md。
