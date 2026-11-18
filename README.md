# 健康大数据与智能医学实践：课程作业仓库

本仓库按课程分节保存作业、公开数据、代码、结果和提交版本，供课程助教和同伴复查。

## 从零开始：仓库运行与结果复现

下面是推荐执行顺序。命令默认在终端中运行；Windows 可以使用 PowerShell，macOS/Linux 可以使用 Bash。

### 1. 安装基础软件

先安装：

- Git 2.x
- 64 位 Python 3.11 或 3.12
- 可选：JupyterLab 4（运行 notebook 课程时需要）

检查是否安装成功：

```bash
git --version
python --version
```

预期结果：分别显示 Git 版本以及 Python 3.11/3.12。

### 2. 克隆并进入仓库

作用：把代码、教学数据、作业和保存的结果下载到本地。

```bash
git clone https://github.com/zmlbh/health-data-intelligent-medicine-coursework.git
cd health-data-intelligent-medicine-coursework
```

预期结果：当前目录中能看到 `README.md`、`lessons/`、`course-materials/` 和 `tools/`。

### 3. 创建独立 Python 环境

作用：避免课程依赖与电脑中已有的 Python 包冲突。

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

macOS/Linux：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

预期结果：命令行前出现 `(.venv)`；运行 `python -m pip --version` 时，路径指向仓库中的 `.venv`。

### 4. 先检查仓库是否完整

作用：检查九课是否包含 README、作业、代码、数据、AI 记录和结果。

```bash
python tools/audit_repository.py
```

预期结果：九个课次均显示 `reviewable`，并生成 `outputs/repository-audit.csv`。

### 5. 复现第 4 课统计分析（已实际验证）

先安装依赖，再执行分析：

```bash
python -m pip install numpy scipy
python lessons/lesson-04-hypothesis-testing/project/analysis.py
```

预期结果：终端显示描述统计、Welch t 检验、Mann–Whitney U、卡方检验、相关和回归结果；完整文本写入：

```text
lessons/lesson-04-hypothesis-testing/project/analysis_results.txt
```

主要复核值包括 920 条记录、Welch t 检验 `p = 1.302e-33`、Mann–Whitney U `p = 9.026e-32`、卡方检验 `p = 2.485e-20`。不同依赖版本可能造成最后几位小数差异。

### 6. 复现第 6 课朴素贝叶斯分析（已实际验证）

安装该课依赖并运行主脚本：

```bash
python -m pip install -r lessons/lesson-06-naive-bayes/project/requirements.txt
python lessons/lesson-06-naive-bayes/project/scripts/full_analysis.py
```

预期结果：终端显示 `train=72 valid=24 test=24`，随后显示 `ALL FIGURES SAVED`；在以下本地目录生成 8 张分析图和结果文件：

```text
lessons/lesson-06-naive-bayes/project/review/render-student/
```

该 `review/` 目录属于可重新生成的本地结果，因此被 `.gitignore` 排除，不会污染版本历史。

### 7. 查看最终作业、代码和证据链

- 每课最终提交文件：`lessons/lesson-XX-*/assignment/`
- 每课分析代码和数据：`lessons/lesson-XX-*/project/`
- AI 使用记录：`lessons/lesson-XX-*/ai-records/`
- 作业—数据—代码—输出对应关系：`EVIDENCE_MAP.md`
- 公开限制和未验证项目：`LIMITATIONS.md`

### 8. 复现其他课程

第 2、3、5、7、8、9 课的具体命令、作用、运行顺序和预期结果均列在 `REPRODUCIBILITY.md`。这些入口已经完成路径和语法检查，但尚未全部在一台全新的电脑上逐课完整运行，因此遇到依赖差异时请按该文件最后的排查顺序处理。

复现结束后可以运行 `deactivate` 退出虚拟环境。完整复现原则是：先创建环境，再安装对应课程依赖，随后运行代码，最后把新输出与仓库保存的结果或作业结论进行比较。

## 课程结构

```text
course-materials/                         # PBL 要求、评分标准、课程计划
  pbl-instruction.pptx                    # PBL 总体说明
  PBL评分标准表.docx                      # 评分标准
  plan.docx                               # 课程计划
lessons/
  lesson-01-ai-and-git/                   # 课程介绍与 Git/GitHub
    README.md / slides/ / ai-records/
  lesson-02-data-types/                   # 变量类型与数据类型
    assignment/ / project/ / ai-records/
    project/{assets,notebook,scripts}
  lesson-03-dimension-reduction/          # 高维数据、PCA 与 UMAP
    project/ / ai-records/                # 无正式提交版
    project/{analysis,student-package}
  lesson-04-hypothesis-testing/           # 统计检验与假设设计
    assignment/ / project/ / ai-records/
    project/{data,analysis.py,analysis_results.txt}
  lesson-05-multiple-testing/             # 多重检验校正
    assignment/ / project/ / ai-records/
    project/{data,notebooks}
  lesson-06-naive-bayes/                  # 机器学习基础与朴素贝叶斯
    assignment/ / project/ / ai-records/
    project/{data,assets,notebook,notebooks,scripts}
  lesson-07-linear-models/                # 线性模型、LDA 与 Logistic Regression
    assignment/ / project/ / ai-records/
    project/{data,assets,notebook,notebooks,scripts,论文交付}
  lesson-08-svm/                          # SVM 与 Margin
    assignment/ / project/ / ai-records/
    project/{data,assets,notebook,scripts,slides,student-release}
  lesson-09-ensemble-bootstrap/           # 集成学习与 Bootstrapping
    assignment/ / project/ / ai-records/
    project/{data,data-ctg,scripts,slides,submission_materials}
tools/                                    # 仓库自动验收代码
outputs/                                  # 自动生成的验收表
AI_CONVERSATION_RECORDS.md                # 历史 AI 对话记录的补充说明
REPRODUCIBILITY.md                        # 环境与复现命令
EVIDENCE_MAP.md                           # 作业、数据、代码和输出的对应关系
LIMITATIONS.md                            # 已知限制与下一步
EXCLUDED_FROM_PUBLIC_REPOSITORY.txt       # 未公开的缓存、渲染文件和超大文件清单
```

## 公开范围与限制

本仓库仅包含课程作业中已经提供的公开或教学用途材料。为避免泄露不应公开的内容，未纳入虚拟环境、缓存、运行日志、临时渲染目录和超过 50 MB 的文件。数据使用条件、版本信息和字段说明以各项目内的 README 或数据说明为准。

仓库仅保存可核验历史任务的脱敏摘要，不公开完整聊天、私人路径或无关信息。未定位到原始会话的课次会明确标注“未核验到记录”，不会补写或伪造对话。

## 验收状态

- 可复现：根目录命令可生成 CSV 验收表；第 4、6 课主分析已实际重跑，其他课程入口在 `REPRODUCIBILITY.md` 中列出。
- 可追溯：`EVIDENCE_MAP.md` 将最终作业连接到数据、代码和输出。
- 可审阅：缓存、虚拟环境、密钥类文件和临时渲染目录已排除。
- 版本化：Git 历史按“初始整理、证据链说明、自动验收、AI 记录与复现增强”分阶段提交。
- 边界诚实：未完成课程、缺失的历史 AI 对话及未逐一重跑的分析均在 `LIMITATIONS.md` 中说明。
