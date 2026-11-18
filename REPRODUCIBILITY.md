# 复现说明

## 1 推荐环境

以下是为复现而建议的环境，不冒充原始作业生成时的唯一环境：

- Windows 10/11、macOS 或 Linux
- Git 2.x
- Python 3.11 或 3.12 64 位
- PowerShell 7 或 Bash
- 至少 8 GB 内存和约 3 GB 可用磁盘空间
- JupyterLab 4，用于运行 notebook

每个课次优先使用其 `project/requirements.txt`。不同课次依赖范围不同，最稳妥的方式是分别建立虚拟环境，避免包版本互相影响。

已实际验证的配置：2026-11-18 在 Windows 64 位、Python 3.12、NumPy 2.5.5、SciPy 1.18.1 下成功执行第 4 课 `analysis.py`，并重新生成 `analysis_results.txt`。其他课次的完整 notebook 尚未在同一台干净电脑上逐一重跑，不能把保存的输出当作跨环境复现证明。

## 2 下载并检查仓库

### 步骤 1 克隆仓库

作用：下载代码、数据说明、作业和已保存输出。

```bash
git clone https://github.com/zmlbh/health-data-intelligent-medicine-coursework.git
cd health-data-intelligent-medicine-coursework
```

预期结果：当前目录下能看到 `README.md`、`lessons/`、`tools/` 和 `course-materials/`。

### 步骤 2 检查 Python

作用：确认命令行调用的是 Python 3.11 或 3.12 的 64 位解释器。

```bash
python --version
python -c "import sys, platform; print(sys.executable); print(platform.architecture())"
```

预期结果：显示 Python 3.x、解释器绝对路径和 `64bit`。

### 步骤 3 建立仓库级虚拟环境

作用：隔离复现依赖。`.venv/` 已被 `.gitignore` 排除，不会误传到 GitHub。

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

macOS 或 Linux：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

预期结果：命令行前出现 `(.venv)`，`python -m pip --version` 指向当前仓库的 `.venv`。

### 步骤 4 执行仓库级验收

作用：统计每课是否具备作业、代码、数据、README 和结果，并检查缓存或密钥类文件名。

```bash
python tools/audit_repository.py
```

预期结果：终端列出 9 个课次并显示 `reviewable`，同时生成 `outputs/repository-audit.csv`。

## 3 各课复现顺序

以下每个课次均假设命令从仓库根目录开始执行。复现下一课前先返回仓库根目录，或另开一个终端。

### 第 1 课 课程介绍与 Git

1. 打开 `lessons/lesson-01-ai-and-git/slides/lesson01-vscode-codex-git.pptx`。
2. 本课没有数据分析脚本，不应为了形式生成虚假结果。
3. 预期结果：理解 Git 初始化、commit 和 AI 代码核查流程。

### 第 2 课 变量类型与数据类型

1. 进入项目：

   ```bash
   cd lessons/lesson-02-data-types/project
   ```
2. 安装环境：

   ```bash
   python -m pip install jupyterlab numpy pandas scipy scikit-learn matplotlib seaborn
   ```

3. 启动 notebook：

   ```bash
   jupyter lab notebook/pbl-understanding-data-lab.ipynb
   ```

4. 执行 `Run All Cells`。
5. 预期结果：得到变量类型、缺失模式、距离度量、PCA 和预处理表图，并与 `assets/pbl-understanding-data/` 对照。

### 第 3 课 高维数据与降维

1. 进入项目并安装锁定依赖：

   ```bash
   cd lessons/lesson-03-dimension-reduction/project
   python -m pip install -r student-package/requirements.txt
   ```

2. 执行分析：

   ```bash
   python analysis/scripts/run_classroom.py
   ```

3. 预期结果：生成或更新 `analysis/results/classroom-seen-unseen.csv`。
4. 结果边界：PCA/UMAP 图不能直接证明生物学类别真实存在。

### 第 4 课 统计检验与假设设计

1. 进入项目并安装依赖：

   ```bash
   cd lessons/lesson-04-hypothesis-testing/project
   python -m pip install numpy scipy
   ```

2. 执行分析：

   ```bash
   python analysis.py
   ```

3. 预期结果：终端打印描述统计、Welch t 检验、Mann–Whitney U、卡方检验、相关和回归结果，并覆盖 `analysis_results.txt`。
4. 复核方式：与 `../assignment/pbl-hypothesis-student-worksheet.docx` 中的回答逐项比较。

### 第 5 课 多重检验校正

1. 进入项目并安装依赖：

   ```bash
   cd lessons/lesson-05-multiple-testing/project
   python -m pip install -r requirements.txt
   ```

2. 启动 notebook：

   ```bash
   jupyter lab notebooks/multiple-test-lab.ipynb
   ```

3. 执行全部单元格。
4. 预期结果：比较未校正 p 值、Bonferroni 和 Benjamini–Hochberg FDR；输入为 `data/leukemia.csv`。

### 第 6 课 朴素贝叶斯

1. 进入项目并安装依赖：

   ```bash
   cd lessons/lesson-06-naive-bayes/project
   python -m pip install -r requirements.txt
   ```

2. 执行主分析：

   ```bash
   python scripts/full_analysis.py
   ```

3. 预期结果：生成或更新性能、阈值、概率质量和锁定测试指标；主要复核表位于 `assets/pbl-machine-learning-basics-naive-bayes/`。
4. 结果解释不能只看 accuracy，还需检查 sensitivity、specificity、PR-AUC 和校准。

### 第 7 课 线性模型

1. 进入项目并安装依赖：

   ```bash
   cd lessons/lesson-07-linear-models/project
   python -m pip install -r requirements.txt
   python -m pip install jupyterlab
   ```

2. 启动主 notebook：

   ```bash
   jupyter lab notebook/pbl-linear-models-lda-logistic-regression-lab.ipynb
   ```

3. 执行全部单元格。
4. 预期结果：得到模型比较、系数、阈值和校准图表，并与 `assets/pbl-linear-models-lda-logistic-regression/` 对照。

### 第 8 课 SVM 与 Margin

1. 进入项目并安装依赖：

   ```bash
   cd lessons/lesson-08-svm/project
   python -m pip install -r requirements.txt
   ```

2. 启动主 notebook：

   ```bash
   jupyter lab notebook/pbl-svm-margin-lab.ipynb
   ```

3. 执行全部单元格。
4. 预期结果：得到 margin、支持向量删除、C/kernel/gamma 对照和锁定测试结果；主要表位于 `assets/pbl-svm-margin/`。
5. 结论边界：支持向量不等同于典型病例，单一保留集也不能证明跨医院泛化。

### 第 9 课 集成学习与 Bootstrapping

1. 进入项目并安装依赖：

   ```bash
   cd lessons/lesson-09-ensemble-bootstrap/project
   python -m pip install -r requirements.txt
   ```

2. 如果需要从原始 CTG 文件重新准备固定划分，先运行：

   ```bash
   python scripts/prepare_data_ctg.py
   ```

   作用：按 `recording_id` 分组生成 CTG 的训练、验证和锁定测试文件，避免同一录音片段跨集合泄漏。已有固定划分时可跳过。

3. 分别运行 WDBC 与 CTG 示例：

   ```bash
   python scripts/demo_ensemble.py --data wdbc
   python scripts/demo_ensemble.py --data ctg
   ```

   作用：在各自的数据与验证协议下比较单树、Bagging、Random Forest、Boosting 等模型。

4. 预期结果：终端输出两套数据的模型指标，并在项目根目录 `.tmp/ensemble/` 下生成临时结果；论文级结果位于 `submission_materials/experiment_results/`。
5. 复核边界：开发集包含 1,703 个样本，另有 423 个锁定测试特征；不得用锁定测试数据调参。

## 4 结果不一致时的排查顺序

1. 运行 `python --version`，确认没有误用系统中的另一个解释器。
2. 运行 `python -m pip list`，保存实际依赖版本。
3. 检查当前目录是否为对应课次的 `project/`。
4. 检查数据相对路径，不要改成仅在本机有效的绝对路径。
5. 检查随机种子、数据划分和是否错误使用锁定测试标签。
6. 保留错误日志，但不要公开用户名、密钥或私人路径。
