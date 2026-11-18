# 健康大数据与智能医学实践：课程作业仓库

本仓库按课程分节保存作业、公开数据、代码、结果和提交版本，供课程助教和同伴复查。

## 查看与复现

1. 从 `course-materials/` 查看 PBL 要求、评分标准和课程计划。
2. 从 `lessons/lesson-XX-*` 进入相应课程文件夹。
3. 每节课的 `assignment/` 保存最终提交版本；`project/` 保存相关代码、notebook、数据、说明和结果。
4. 若某项目包含 `requirements.txt`，请先创建独立 Python 环境，再执行 `pip install -r requirements.txt`。

## 课程结构

```text
course-materials/                         # PBL 要求、评分标准、课程计划
lessons/
  lesson-01-ai-and-git/                   # 课程介绍与 Git/GitHub
  lesson-02-data-types/                   # 变量类型与数据类型
  lesson-03-dimension-reduction/          # 高维数据、PCA 与 UMAP
  lesson-04-hypothesis-testing/           # 统计检验与假设设计
  lesson-05-multiple-testing/             # 多重检验校正
  lesson-06-naive-bayes/                  # 机器学习基础与朴素贝叶斯
  lesson-07-linear-models/                # 线性模型、LDA 与 Logistic Regression
  lesson-08-svm/                          # SVM 与 Margin
  lesson-09-ensemble-bootstrap/           # 集成学习与 Bootstrapping
AI_CONVERSATION_RECORDS.md                # 历史 AI 对话记录的补充说明
EXCLUDED_FROM_PUBLIC_REPOSITORY.txt       # 未公开的缓存、渲染文件和超大文件清单
```

## 公开范围与限制

本仓库仅包含课程作业中已经提供的公开或教学用途材料。为避免泄露不应公开的内容，未纳入虚拟环境、缓存、运行日志、临时渲染目录和超过 50 MB 的文件。数据使用条件、版本信息和字段说明以各项目内的 README 或数据说明为准。

历史 AI 对话原文未随本次材料一并提供，因此本仓库不会虚构或伪造对话记录。提交前请按照 `AI_CONVERSATION_RECORDS.md` 补入各课实际使用的 AI 对话导出或共享链接。
