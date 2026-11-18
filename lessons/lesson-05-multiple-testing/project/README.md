# 第 6 讲：多重检验校正

围绕“做了很多检验，哪些发现值得验证？”组织 PBL。沿用真实 Golub 白血病表达数据，比较 AML 与 ALL；按教学要求辅以明确标注的已知真值模拟，帮助区分发现数量、假发现与检出力。

## 材料入口

| 文件 | 用途 |
|---|---|
| [multiple-test.md](multiple-test.md) | 原课程教学要求 |
| [slides/multiple-test-pbl.pptx](slides/multiple-test-pbl.pptx) | 27 页课堂 PPT：核心名词、调研任务、实验数据与方法、待回答问题 |
| [data/README.md](data/README.md) | 数据背景、字段、来源、处理规则与边界 |
| [experiment-design.md](experiment-design.md) | 问题链、固定协议、45 分钟课堂与 60 分钟作业安排 |
| [student-worksheet.md](student-worksheet.md) | 学生预测、记录、判断与提交要求，不预填答案 |
| [teacher-reference.md](teacher-reference.md) | 计算结果、概念解释、追问、评分与误区；仅供教师 |
| [notebooks/multiple-test-lab.ipynb](notebooks/multiple-test-lab.ipynb) | 可直接运行的学生实验，计算函数内置，不依赖临时作者脚本 |

## 运行方式

从项目根目录安装环境：

```powershell
python -m pip install -r "class2026/materials/6. multiple-test/requirements.txt"
```

在 VS Code 的 Jupyter 界面打开 Notebook，选择该 Python 环境，按 A→B→C 顺序逐格运行。先填写工作单预测和协议，C3 锁定候选后才运行 C4。课堂以 A/B 的错误控制比较为主，教师分阶段展示 C；作业完成 C 的完整计算与结论。

Notebook 为正式教学实验工具，保留在课程目录。学生版没有执行输出；计算表、图、环境记录写入项目根目录 `.tmp/multiple-test/student-results/session-01/`。重复运行保留已有锁定名单，名单改变会停止；如需新独立运行，在设置单元格给 RUN_ID 换一个文件夹名，并先固定新运行协议。不要按验证结果换候选。

作者的生成/核验脚本、审核报告和教师计算中间结果均保留在根目录 `.tmp/multiple-test/`，不提交 Git。课程的正式数据、来源元数据、文字材料、依赖列表和学生实验 Notebook 保留在本目录。

## 解释边界

7,129 个探针不等于独立的 7,129 个基因；ALL/AML 比较不是疾病/健康比较。真实数据不知道单项真值，不能把发现数当作真阳性数。BH adjusted p 不自动等于 Storey q-value；留出样本不是外部独立队列。显著结果仍需质量控制、注释、机制证据及独立验证。
