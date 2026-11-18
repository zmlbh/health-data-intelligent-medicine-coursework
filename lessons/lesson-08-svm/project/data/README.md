# 实验数据：Vertebral Column

## 来源与授权

- 数据集：UCI Machine Learning Repository，**Vertebral Column**。
- 官方页面：<https://archive.ics.uci.edu/dataset/212/vertebral+column>
- DOI：<https://doi.org/10.24432/C5K89B>
- 下载地址：<https://archive.ics.uci.edu/static/public/212/vertebral+column.zip>
- UCI 署名：Guilherme Barreto、Ajalmar Neto。按 UCI 的 CC BY 4.0 授权使用，课程整理涉及字段命名、标签编码、教学特征选取和数据划分。
- UCI 说明：Henrique da Mota 医生在法国里昂 Centre Médico-Chirurgical de Réadaptation des Massues 的 GARO 团队工作期间建立此生物医学数据集。它描述骨盆、腰椎形态和方向相关的六个生物力学测量。
- 原档 SHA256：`899ed1d137ceb4c36d59fa35f3cbab39ec3b78fd3ca1fdaf2fae155459c1372f`。

校验值以 [`teacher/split-manifest.json`](teacher/split-manifest.json) 中完整的 `archive_sha256` 为准。下载时间、软件版本、固定划分 ID 均在同一清单中。原始归档保留不变，离线运行无需重新下载。

## 一行数据是什么？

一行是原数据集的一条患者测量记录。共 **310** 条，六个数值字段，无缺失。二分类源文件为 `column_2C.dat`。NO=Normal（100 条）；AB=Abnormal（210 条），AB 合并了椎间盘突出（60）与脊椎滑脱（150）。本课不把它改写成一般人群筛查、病情严重程度或未来患病风险标签。

UCI 未提供本课所需的外部验证队列、采样代表性保证、重复测量标识或完整测量误差资料。课堂沿用每行独立记录的划分方法，并说明该前提的资料限制。

## 字段

| 字段 | 含义与课堂用途 |
|---|---|
| `sample_id` | 按原文件行号编为 V001–V310，仅用于追踪和合并，不进入模型，也不是原始患者 ID |
| `pelvic_incidence` | 骨盆入射角，主实验输入 x₁ |
| `degree_spondylolisthesis` | 脊椎滑脱程度，主实验输入 x₂；degree 在此不应直接译成角度单位 |
| `pelvic_tilt` | 骨盆倾斜测量，仅保留在教师全字段文件 |
| `lumbar_lordosis_angle` | 腰椎前凸角，仅保留在教师文件 |
| `sacral_slope` | 骶骨倾斜测量，仅保留在教师文件 |
| `pelvic_radius` | 骨盆半径测量，仅保留在教师文件 |
| `class_code` | 原始 NO/AB，仅保留在教师全字段文件 |
| `abnormal` | 教学目标：NO→0、AB→1；公式使用 y=2×abnormal−1，即 −1/+1 |

源 ARFF 与当前 UCI 字段元数据没有逐字段单位说明。保留原数值，图中标为 **source scale**，不自行把滑脱程度解释为角度或百分比。标准化后 z₁、z₂ 为无量纲坐标。

两个输入在实验方案中预先固定，原因是能够直接画出二维边界并观察重叠；没有用测试结果筛选特征。它们不是“最佳两项指标”。模型不使用 sample_id、其余四个特征或原始标签字符串。

## 固定划分与预处理

使用两次分层 `train_test_split`，`random_state=9`：先留 62 条测试，再从其余 248 条留 62 条验证。划分 ID 保存在清单中，不重新随机分组。

| 集合 | NO=0 | AB=1 | 合计 | 用途 |
|---|---:|---:|---:|---|
| 训练 | 60 | 126 | 186 | 拟合 scaler 和 SVM |
| 验证 | 20 | 42 | 62 | 参数对照、选择和解释 |
| 锁定测试 | 20 | 42 | 62 | 配置记录后一次评价 |

StandardScaler 仅在训练集拟合。几何实验使用同一训练 scaler 变换八条教学记录；删除点时冻结 scaler。正式模型将 scaler 与 SVC 放进 Pipeline。

八条几何记录是**有意挑选的可分教学子集**：训练集中滑脱程度 <5 的 NO，和 >30 的 AB，各按 ID 取前四条。它们不用于估计整体分类性能。矛盾标签实验额外复制其中一点并赋相反标签，这是一项明确标识的人工反事实干预，不修改原始标签，也不进入正式拟合与评价。噪声扩展同样是人为特征扰动，不是实际仪器误差测量。

## 文件与复现

| 路径 | 内容 |
|---|---|
| `raw/vertebral-column.zip` | 官方原始归档，含二分类和三分类 DAT/ARFF |
| `raw/field-definitions.txt` | 从原始二分类 ARFF 提取的字段头 |
| `student/train.csv` | ID、两个输入、目标，186 行 |
| `student/validation.csv` | 同上，62 行 |
| `student/locked-test-features.csv` | ID、两个输入，无标签，62 行 |
| `teacher/locked-test-labels.csv` | 测试 ID 与标签，按 ID 合并 |
| `teacher/all-measurements.csv` | 310 条全字段教学整理表 |
| `teacher/split-manifest.json` | 来源、哈希、版本、下载时间、划分 ID |

运行 `python -B scripts/prepare_data.py` 可从保留的原档重建。实验图、指标表和审核文件只输出到项目 `.tmp/svm/`。请勿把完整原始归档或教师全表提前发给学生，然后声称测试标签仍然不可见。
