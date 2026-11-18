# 第 7 讲实验数据集筛选与建议

核验日期：2026-10-18。依据：本目录 `WORKPLAN.md`。已查询 UCI 官方元数据，并下载、检查两个首选数据集的原始文件。

## 一、选型结论

建议采用“**Acute Inflammations 主实验 + Early Stage Diabetes 选做数据练习**”。主实验用六项二元特征完成模型定义、训练与预测、数据划分、Bayes手算、损失及分类评价；24条留出记录的结果在方案固定后才查看，不作为开篇冲突。补充练习引入医院问卷来源、更多记录和数据质量问题。两者是不同疾病任务，后者不是前者的外部验证集。

若只选一个数据集，保留 **Acute Inflammations**。它与现有Notebook一致，适合六输入手算；validation和test均24/24正确是已有结果，不是选择数据时必须满足的教学目标。若改用Early Stage Diabetes，应先制定重复记录处理方案，并相应调整手算输入、数据划分及实验记录表。

| 候选 | 规模与变量 | 与本讲的匹配程度 | 限制与建议用途 |
|---|---|---|---|
| **UCI Acute Inflammations** | 120 行；体温 + 5 项二元症状；2 个标签；无缺失 | 最高：体温二元化后直接使用 BernoulliNB；可手算；完全对应现有计划 | 专家为专家系统测试创建的数据，不应称为真实临床队列；适合主实验 |
| **UCI Early Stage Diabetes Risk Prediction** | 520 行；14 项 Yes/No 症状 + 年龄、性别；无缺失；阳性 320 / 阴性 200 | 高：仅使用 14 项症状即可沿用 BernoulliNB；适合阈值、条件依赖、概率质量和数据审计 | 单医院问卷来源；269 条完全重复的额外记录，独立性不明；适合迁移与审计，不宜直接按行拆分 |
| UCI Breast Cancer Wisconsin (Diagnostic) | 569 行；30 项连续细胞核形态特征；无缺失 | 中：适合相关特征、概率质量和分类评价 | 更自然地使用 GaussianNB；若强制二元化会引入阈值选择和信息损失；作为扩展备用 |
| UCI Heart Disease（Cleveland 常用子集） | 303 行；13 项连续/分类特征；有缺失 | 中偏低：医学语义明确，可讨论不同错误代价 | 混合变量、缺失处理和多类别编码增加入门负担；不是直接套用 BernoulliNB 的首选 |
| UCI Breast Cancer（Ljubljana，非 Wisconsin） | 286 行；9 项特征，以分类变量为主；有缺失；标签为复发/未复发 | 中偏低：适合类别不平衡和后续 CategoricalNB | 不应与乳腺良恶性诊断数据混淆；需要澄清预测时点、缺失与类别编码；留作进阶 |

后三项已核对 UCI 元数据，未在本次下载和运行模型；表中缺失等信息来自官方说明。推荐并非基于模型分数排名。

## 二、主实验：Acute Inflammations

- 官方页面：<https://archive.ics.uci.edu/dataset/184/acute+inflammations>
- DOI：<https://doi.org/10.24432/C5V59S>
- 官方下载：<https://archive.ics.uci.edu/static/public/184/acute+inflammations.zip>
- 创建者：Jacek Czerniak；相关文献：J. Czerniak、H. Zarzycki，*Application of rough sets in the presumptive diagnosis of urinary system diseases*，2003。
- 许可：UCI 页面明确标注 CC BY 4.0；分发时保留来源、署名和改动说明。
- 本地原始包：[`data/raw/acute+inflammations.zip`](data/raw/acute+inflammations.zip)。

### 变量和读取约定

| 原始位置 | 建议列名 | 含义 | 实验处理 |
|---|---|---|---|
| 1 | `temperature_c` | 体温 | 按计划转换为 `fever_ge_38 = temperature_c >= 38` |
| 2 | `nausea` | 恶心 | yes/no → 1/0 |
| 3 | `lumbar_pain` | 腰痛 | yes/no → 1/0 |
| 4 | `urine_pushing` | 持续尿意 | yes/no → 1/0 |
| 5 | `micturition_pain` | 排尿疼痛 | yes/no → 1/0 |
| 6 | `burning_urethra` | 尿道灼痛、瘙痒等 | yes/no → 1/0 |
| 7 | `bladder_inflammation` | 膀胱炎症 | 主标签，yes = 阳性 |
| 8 | `nephritis` | 肾盂来源的肾炎 | 迁移标签，yes = 阳性 |

原始包包含 `diagnosis.data` 和 `diagnosis.names`。实测数据文件为 **UTF-16、TAB 分隔、逗号小数、无表头**；不要直接按 UTF-8 普通 CSV 读取，也不要依照网页中“ASCII”的描述猜编码。

### 实测数据审计与课程影响

- 原始矩阵 120 × 8，无缺失。膀胱炎症阳性 59、阴性 61；肾炎阳性 50、阴性 70。
- 按完整 8 列比较，有 21 条重复的额外行，即 99 种完整记录。
- 按计划把体温二元化后，六项输入总共只有 **9 种不同特征组合**。
- 主标签分层划分：先保留 20% test，再将剩余数据的 25% 分为 validation，两次均 `random_state=7`，得到 72/24/24。
- `BernoulliNB(alpha=1.0)` 在上述 validation 和 test 上均为 `[[12, 0], [0, 12]]`，矩阵顺序为 TN、FP / FN、TP。复现的是教师侧已有设计，并非学生可反复查看测试集的许可。
- 主任务 test 的不同二元特征组合有 8 种，均在 train 中出现。完美分数可能反映对既有有限模式的复现，不能据此证明对新症状组合或独立临床人群有效。

重复特征模式本身不证明“同一个患者被泄漏”，但本数据没有足够来源信息支持将这些行当作独立临床患者。建议把完整行重复、输入模式覆盖和数据构造方式作为 Packet A 的审计问题，而不是悄悄去重后仍沿用既定分数。

### 与 WORKPLAN 的衔接

1. **Packet A：**增加编码核验、重复记录数量、二元化前后模式数及数据来源调查。
2. **Bayes 手算：**使用六项输入，明确 absent symptom 的概率也要参与乘积；另一疾病标签不能作为输入。
3. **Packet B：**只开放 validation，计算混淆矩阵并选择阈值；分数高也继续审计。
4. **Packet C：**在类别内部检查依赖；重复一个症状后比较概率、Brier 和 log loss，区分准确分类与概率可信度。24 条验证记录的校准图仅作描述，避免把少数分箱当稳定结论。
5. **Packet D：**冻结方案后开放 test；报告 Wilson 区间和模式重叠，并区分模拟症状翻转与真实外部验证。
6. **迁移肾炎任务：**两个标签可同时为阳性，不是互斥多分类。若改按肾炎分层，要重新生成划分与评价；若保留主任务的行索引，应明确说明。两者不是同一方案，不能混用预设指标。

## 三、补充实验：Early Stage Diabetes Risk Prediction

- 官方页面：<https://archive.ics.uci.edu/dataset/529/early+stage+diabetes+risk+prediction+dataset>
- DOI：<https://doi.org/10.24432/C5VG8H>
- 官方下载：<https://archive.ics.uci.edu/static/public/529/early+stage+diabetes+risk+prediction+dataset.zip>
- 来源：UCI 说明为孟加拉国 Sylhet Diabetes Hospital 患者的直接问卷，并经医生审核。
- 相关文献：M. M. F. Islam 等，*Likelihood Prediction of Diabetes at Early Stage Using Data Mining Techniques*，2019，DOI：<https://doi.org/10.1007/978-981-13-8798-2_12>。
- 许可：UCI 页面明确标注 CC BY 4.0。
- 本地原始包：[`data/raw/early+stage+diabetes+risk+prediction+dataset.zip`](data/raw/early+stage+diabetes+risk+prediction+dataset.zip)，包含 `diabetes_data_upload.csv`。

### 建议任务

用问卷症状预测当前 `class`（Positive/Negative），不能仅凭数据集名称将它解释为“未来发生糖尿病的风险预测”，也不能假定存在独立前瞻性结局。

初学版使用以下 14 个症状，Yes/No 映射为 1/0：

`Polyuria`、`Polydipsia`、`sudden weight loss`、`weakness`、`Polyphagia`、`Genital thrush`、`visual blurring`、`Itching`、`Irritability`、`delayed healing`、`partial paresis`、`muscle stiffness`、`Alopecia`、`Obesity`。

主模型暂不加入 Age 和 Gender，便于专注 Bernoulli NB 和手算。可预先指定 Polyuria、Polydipsia 等少数症状进行手算，再由完整症状模型计算；不要根据测试成绩挑选症状。

### 使用前必须处理的问题

- **重复记录：**520 行中完整行去重后为 251 行，即有 269 条额外重复记录；去掉标签后同样有 269 条额外重复输入。不能据此断言都是错误复制，也不能默认它们代表不同独立患者。
- **分组策略：**保留原始包；以全部原始输入、排除标签的组合生成分组标识，使相同输入不会跨 train/validation/test。若最终仅使用 14 个症状，可再检查或按这 14 项组合分组，审计最简输入模式的重叠。按症状模式分组是更严格的模式泛化压力测试，不等于患者 ID 分组或真实外部验证。
- **去重敏感性分析：**另报告保留一次完整重复行后的结果。去重会改变样本权重及类别比例；不可将它直接视为恢复了真实患者队列。
- **划分规模：**若按行 60/20/20，名义上是 312/104/104；采用分组后不应强求精确数量或比例，应报告实际样本数、组数和类别数。所有方案先确定，再锁定 test。
- **文档与文件不一致：**UCI 变量说明中的年龄范围与实际文件不同；本次文件实测 Age 为 **16–90 岁**。应以实测报告差异，不按网页范围静默删行。
- **语义边界：**没有充分的患者标识、时间、诊断流程和外部队列信息；不能排除选择偏倚，也不能把样本阳性比例当社区患病率。

该数据适合“迁移建模方法 + 审计数据”，不建议把它包装成无需质疑的真实临床金标准。此处不提供可供挑选方案的测试成绩。

## 四、其他候选的官方入口

- Wisconsin Diagnostic：<https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic>；DOI `10.24432/C5DW2B`。
- Heart Disease：<https://archive.ics.uci.edu/dataset/45/heart+disease>；DOI `10.24432/C52P4X`。303 行指常用 Cleveland 表，不是四个中心合并后的总人数。
- Breast Cancer（Ljubljana）：<https://archive.ics.uci.edu/dataset/14/breast+cancer>；DOI `10.24432/C51P4M`。

## 五、复核与文件位置

- 原始下载包及读取示例：[`data/README.md`](data/README.md)。
- 本地审计脚本：[`scripts/audit_datasets.py`](scripts/audit_datasets.py)，不需要联网，不训练或选择模型，只检查原始文件和模式数。
- 运行产生的审计 JSON 写入项目 `.tmp/naive-bayes-dataset-search/`，不作为正式课程材料提交。
- 本次仅新增数据筛选说明、原始包和审计脚本，未修改 WORKPLAN 或生成学生版 Notebook。WORKPLAN 提及的 Notebook 和 assets 尚未出现在本讲目录，后续制作时需另行落实。
