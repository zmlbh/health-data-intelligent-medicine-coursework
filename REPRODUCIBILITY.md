# 复现说明

## 仓库级验收

以下命令不需要安装第三方包：

```bash
python tools/audit_repository.py
```

输出文件为 `outputs/repository-audit.csv`。它汇总每节课是否包含作业、代码、数据和结果，可用于检查仓库结构是否完整。

## 各课运行入口

不同课次使用了不同的 Python 依赖。运行课程分析前，建议在仓库外创建虚拟环境，并在对应 `project/` 目录安装其 `requirements.txt`。

| 课次 | 推荐入口 | 预期输出 |
| --- | --- | --- |
| 第 1 课 | 无分析代码，本课为 Git 与 AI 使用环境配置 | 课程课件 |
| 第 2 课 | `project/notebook/pbl-understanding-data-lab.ipynb` | 数据质量表、PCA 和预处理图表 |
| 第 3 课 | `project/analysis/scripts/run_classroom.py` | `project/analysis/results/classroom-seen-unseen.csv` |
| 第 4 课 | `project/analysis.py` | `project/analysis_results.txt` |
| 第 5 课 | `project/notebooks/multiple-test-lab.ipynb` | 多重检验结果与图表 |
| 第 6 课 | `project/scripts/full_analysis.py` | 朴素贝叶斯性能表和图表 |
| 第 7 课 | `project/notebook/pbl-linear-models-lda-logistic-regression-lab.ipynb` | 模型比较表、系数与校准图 |
| 第 8 课 | `project/notebook/pbl-svm-margin-lab.ipynb` | SVM margin、参数比较和测试结果 |
| 第 9 课 | `project/scripts/demo_ensemble.py` | 集成学习示例结果；课程论文结果见 `submission_materials/experiment_results/` |

这些入口来自现有项目文件。根目录验收脚本已经实际运行；各课分析没有在本次仓库整理过程中全部重新执行，因此环境差异仍可能影响结果。
