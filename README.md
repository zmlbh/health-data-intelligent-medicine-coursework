# 健康大数据与智能医学实践：课程作业仓库

本仓库按课程分节保存作业、公开数据、代码、结果和提交版本，供课程助教和同伴复查。

## 查看与复现

1. 从 `course-materials/` 查看 PBL 要求、评分标准和课程计划。
2. 从 `lessons/lesson-XX-*` 进入相应课程文件夹。
3. 每节课的 `assignment/` 保存最终提交版本；`project/` 保存相关代码、notebook、数据、说明和结果。
4. 若某项目包含 `requirements.txt`，请先创建独立 Python 环境，再执行 `pip install -r requirements.txt`。

## 一条命令完成仓库验收

在仓库根目录运行：

```bash
python tools/audit_repository.py
```

该命令只使用 Python 标准库，检查每课的作业、代码、数据和输出，并重新生成 `outputs/repository-audit.csv`。详细复现入口见 `REPRODUCIBILITY.md`，结论与文件之间的对应关系见 `EVIDENCE_MAP.md`。

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

历史 AI 对话原文未随本次材料一并提供，因此本仓库不会虚构或伪造对话记录。提交前请按照 `AI_CONVERSATION_RECORDS.md` 补入各课实际使用的 AI 对话导出或共享链接。

## 验收状态

- 可复现：根目录命令可生成一张 CSV 验收表；各课已有运行入口在 `REPRODUCIBILITY.md` 中列出。
- 可追溯：`EVIDENCE_MAP.md` 将最终作业连接到数据、代码和输出。
- 可审阅：缓存、虚拟环境、密钥类文件和临时渲染目录已排除。
- 版本化：Git 历史按“初始整理、证据链说明、自动验收与边界”分阶段提交。
- 边界诚实：未完成课程、缺失的历史 AI 对话及未逐一重跑的分析均在 `LIMITATIONS.md` 中说明。
