# 第 10 讲数据说明：方案 B（CTG 胎心监护）

本文件夹是第 10 讲的备选数据，与 `data/`（方案 A，WDBC）并列，由授课教师二选一。

本数据来自 UCI Cardiotocography：2126 段胎心监护（CTG）信号经 SisPorto 软件自动提取 21 个特征，并由三位产科专家给出共识判读。每一行是一个**信号片段**，不是一位孕妇：2126 段来自 352 个录音文件，同一录音常被切成多个片段，片段之间可能在时间上重叠。

## 标签

原始专家判读 NSP：1=正常（1655 段）、2=可疑（295 段）、3=病理（176 段）。课程使用二分类 `pathologic=1`（NSP=3，8.3%），正常与可疑合为 0。三分类标签 `nsp_3class` 只保留在 `teacher/` 中，可作为课后扩展。本课不把标签解释为胎儿结局、个体风险或因果效应。

## 特征（21 个，连续，无缺失）

| 列名 | 含义 |
|---|---|
| LB | 胎心率基线（次/分） |
| AC | 每秒加速次数 |
| FM | 每秒胎动次数 |
| UC | 每秒宫缩次数 |
| DL | 每秒轻度减速次数 |
| DS | 每秒重度减速次数 |
| DP | 每秒延长减速次数 |
| ASTV | 短时变异异常的时间百分比 |
| MSTV | 短时变异均值 |
| ALTV | 长时变异异常的时间百分比 |
| MLTV | 长时变异均值 |
| Width、Min、Max | 胎心率直方图的宽度、最小值、最大值 |
| Nmax、Nzeros | 直方图峰的个数、零值个数 |
| Mode、Mean、Median、Variance、Tendency | 直方图的众数、均值、中位数、方差、偏态趋势 |

AC、FM、UC、DL、DS、DP 由原始计数除以片段时长（秒）得到，与 UCI “Data” 工作表一致。原表中的 DR（重复减速）全部为 0，LBE 与 LB 相同，形态分类 A–SUSP 与 CLASS 是由专家判读派生的类别，都不作为输入。

## 划分

`scripts/prepare_data_ctg.py` 固定 `random_state=1010`，用 `StratifiedGroupKFold` 按 `recording_id` 分组、按标签分层：

| 集合 | 片段数 | 录音数 | pathologic=1 |
|---|---:|---:|---:|
| train | 1279 | 209 | 108 |
| validation | 424 | 73 | 34 |
| test | 423 | 70 | 34 |

同一录音的片段只出现在一个集合中。学生获得 train、validation 和不含标签的 locked-test-features；教师保留 test 标签、三分类标签和完整测量表（含原始文件名、日期、片段起止时间）。在开发集内做交叉验证时也必须按 `recording_id` 分组；按行随机划分会让同一录音的相似片段同时出现在训练和验证中，结果偏乐观。随机森林的 OOB 也按行抽样，因此在本数据上同样偏乐观。

## 来源与许可

- 数据页：<https://archive.ics.uci.edu/dataset/193/cardiotocography>，DOI `10.24432/C51S4N`，许可 CC BY 4.0（2026-11-08 核对）。
- 引用：Campos, D. & Bernardes, J. (2000). Cardiotocography [Dataset]. UCI Machine Learning Repository. 原始研究：Ayres-de-Campos D. et al. SisPorto 2.0: a program for automated analysis of cardiotocograms. *J Matern Fetal Med*, 2000.
- `raw/cardiotocography.zip` 是 UCI 下载的原始压缩包（SHA-256 记录在 `teacher/split-manifest.json`）。重新生成需要 `xlrd` 读取其中的 `CTG.xls`：`python scripts/prepare_data_ctg.py`。

## 使用边界

数据是 1980–1998 年的历史录音，来源机构信息有限；录音文件不一定等于孕妇个体；缺少外部队列。结论只限于本数据和本划分下的方法比较，不支持临床部署、跨医院泛化或因果解释。
