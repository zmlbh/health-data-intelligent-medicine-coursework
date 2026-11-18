# 第 7 讲实验数据与字段

下载并核验于 2026-10-18。两个 ZIP 均为 UCI 官方原始下载，内容未改动。选型理由与限制见 [`../DATASET-RECOMMENDATIONS.md`](../DATASET-RECOMMENDATIONS.md)。

| 本地文件 | 来源与署名 | 许可 |
|---|---|---|
| `raw/acute+inflammations.zip` | Jacek Czerniak，Acute Inflammations，UCI，DOI [10.24432/C5V59S](https://doi.org/10.24432/C5V59S) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| `raw/early+stage+diabetes+risk+prediction+dataset.zip` | Early Stage Diabetes Risk Prediction，UCI；相关研究 M. M. F. Islam 等（2019），见选型说明；DOI [10.24432/C5VG8H](https://doi.org/10.24432/C5VG8H) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |

两个数据集均应保留 UCI 数据引用与对应作者信息。转换编码、二元化、去重等处理属于改动，应在提交物中注明。

## 正式实验数据

主实验使用 Acute Inflammations。该数据由专家创建用于专家系统测试，不是临床抽样队列；记录不能自动解释为独立患者。全数据 120 条，无缺失，主标签 59 阳性、61 阴性；第二标签 50 阳性、70 阴性。去掉 ID 后有 21 条完全重复的额外记录，二元六输入仅 9 种组合。本课保留全部记录并审计其局限，不把内部评价作为临床有效性证据。

| 文件 | 行数 | 内容与释放阶段 |
|---|---:|---|
| [student/train.csv](student/train.csv) | 72 | 拟合模型；主标签阴性 37、阳性 35 |
| [student/validation.csv](student/validation.csv) | 24 | 选阈值及检查依赖、概率质量；主标签各 12 |
| [student/locked-test-features.csv](student/locked-test-features.csv) | 24 | ID、原始温度与六输入；不含疾病标签 |
| [teacher/locked-test-labels.csv](teacher/locked-test-labels.csv) | 24 | ID 与两个疾病标签，教师在方案冻结后释放；主标签各 12 |
| [teacher/split-manifest.json](teacher/split-manifest.json) | — | 划分 ID、随机种子及原始包校验信息 |

CSV 为 UTF-8，使用以下字段：

| 字段 | 含义与用途 |
|---|---|
| sample_id | 按原始行顺序生成 A001–A120，仅用于关联与审计 |
| temperature_c | 原始摄氏温度；保留用于审计，不进入六输入模型 |
| fever_ge_38 | 温度 ≥38°C 为 1，否则 0 |
| nausea | 恶心，yes→1、no→0 |
| lumbar_pain | 腰痛，yes→1、no→0 |
| urine_pushing | 尿急，yes→1、no→0 |
| micturition_pain | 排尿痛，yes→1、no→0 |
| burning_urethra | 尿道灼痛，yes→1、no→0 |
| bladder_inflammation | 主预测标签，膀胱炎，yes→1、no→0 |
| nephritis | 迁移任务标签，肾盂肾炎，yes→1、no→0 |

模型仅使用上述六个二元输入，不能加入 ID、原始连续温度或另一个疾病标签。模型为 BernoulliNB(alpha=1, binarize=None)。

划分按主标签分层：先留出 20% 测试，再从剩余记录留出 25% 验证，两步 random_state=7，形成 72/24/24。三个集合 ID 不重叠，但相同症状模式可跨集合出现；不能将 ID 分离等同于独立临床验证。迁移到 nephritis 保持全部 ID 不变，不重新分层，测试标签阴性 18、阳性 6。

在本讲目录运行 `python scripts/prepare_data.py` 可从保留的原始 ZIP 重建 CSV。转换仅包含编码、温度二元化、生成 ID 和固定划分，未去重或补造记录。模型始终在 72 条 train 上拟合，不合并 validation 重训。

学生先完成 A–C 并提交冻结方案，再释放教师标签；第二标签在同一释放文件中，迁移仍须另行冻结。此为教学流程约束，原始 ZIP 可还原标签，不提供技术保密。严格盲评由教师在独立环境执行冻结方案。可选 Diabetes 原始包供另设任务使用，不是本课主模型的外部验证数据。

## 无需解压的读取示例

依赖：Python、pandas。工作目录设为本讲目录；不要依赖当前打开文件的位置。

```python
from pathlib import Path
from zipfile import ZipFile
import pandas as pd

raw = Path("data/raw")
columns = [
    "temperature_c", "nausea", "lumbar_pain", "urine_pushing",
    "micturition_pain", "burning_urethra", "bladder_inflammation", "nephritis",
]
with ZipFile(raw / "acute+inflammations.zip") as z:
    with z.open("diagnosis.data") as f:
        acute = pd.read_csv(
            f, sep="\t", encoding="utf-16", decimal=",", header=None, names=columns
        )

X = acute[columns[1:6]].apply(lambda s: s.map({"yes": 1, "no": 0}))
X.insert(0, "fever_ge_38", (acute["temperature_c"] >= 38).astype(int))
y = acute["bladder_inflammation"].map({"yes": 1, "no": 0})
# nephritis 是第二个标签，不能混入上述六项输入。

with ZipFile(raw / "early+stage+diabetes+risk+prediction+dataset.zip") as z:
    with z.open("diabetes_data_upload.csv") as f:
        diabetes = pd.read_csv(f)
symptoms = diabetes.columns.difference(["Age", "Gender", "class"], sort=False)
X_diabetes = diabetes[symptoms].apply(lambda s: s.map({"Yes": 1, "No": 0}))
y_diabetes = diabetes["class"].map({"Positive": 1, "Negative": 0})

assert X.shape == (120, 6) and X_diabetes.shape == (520, 14)
assert not X.isna().any().any() and not X_diabetes.isna().any().any()
```

## 原始包 SHA-256

```text
066941c1a8352428f2d800f494581db9616dc4856e4109c98fa3bd1407e4a626  acute+inflammations.zip
67594c0f11257688b57493798e70737b7156ba37a2e6ac75507ae3a35221a388  early+stage+diabetes+risk+prediction+dataset.zip
```

注意：Acute 二元化后只有 9 种输入组合；Diabetes 有 269 条完全重复的额外行。划分训练、验证、测试之前先阅读选型说明中的重复与独立性讨论。两份数据分别涉及不同疾病，不能互作外部测试集。
