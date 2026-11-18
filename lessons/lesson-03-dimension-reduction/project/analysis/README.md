# homework3 分析工作区（第三讲 高维数据与维度灾难 / 降维、PCA 与 UMAP）

本文件夹集中存放我为 homework3 产生的**全部**文件；原始资料包 `homework3/student-package/` 未作任何改动。

## 交付物

- `deliverable/pbl-high-dimension-reduction-student-worksheet-completed.docx`
  —— 已作答的学生工作页。做法：把答案写进作答格的**本段（第一个段落）**，
  并删掉该格内仅供书写的空行占位符（空 <w:br/>），因此每个作答格只保留答案本身、上方不再有多余空行；
  表格底色、图片、以及正文/证据表里的横线全部保留，交付物与原文件的正文段落数/表格数一致（153 段 / 50 表）。
- `deliverable/answers.md` —— 同样的作答内容，便于快速阅读或复制。

## 本轮修订明细（补答 + 排版）

### 1) 补答
- `TABLE #6`（3W 表）原先「降维」行 3 格为空，且「距离 / 预测观察 / 降维」三行的
  已知/未知/下一步内容被错位重复。现按表格本意重写：**每行一个主题，三列分别是 已知 / 未知 / 下一步**。
- 复核结果：所有作答表（非证据表）均无空格、无重复、无空答（见 `inspection/audit_completed.py`、`inspection/audit_table6_dups.py`）。

### 2) 表格排版（全部用 Word 属性，未用空格凑版式）
- 垂直居中：所有单元格 `w:tcPr/w:vAlign = center`（上下居中）。
- 水平居中：短标签 / 表头（去空格后 ≤ 24 字）`w:jc = center`（左右居中）。
- 长答案段落：`w:jc = left` + 首行缩进 2 字符（`firstLineChars=200`）。
- 整表在页面上居中：`w:tblPr/w:jc = center`。

### 3) 正文排版
- `Normal` 正文：两端对齐（`jc=both`）+ 首行缩进 2 字符；标题、图表题（Title/Heading/Caption）保持原样。

### 4) 原横线保留（第 3 轮修订后的口径）
- 第 3 轮要求「去掉多余的空格」：经查，之前每一格是在原有空行占位符之后另起一段写答案，于是答案上方留着一整块空行，看起来就是“多余的空格”。现已改为直接写入该格原有段落，并删除这些空 <w:br/>。
- 空行占位符（`<w:br/>`）总量 198 → 30：其中作答格内 168 个已清零（不会再出现多余空行），剩下 30 个均在非作答位置（正文里的自学提示换行 + 表 #2/#3 的阅读登记表），按“横线保留”要求原样保留。
- 证据/数据表（#0–3、#11–13、#16–18、#22–23、#26–30、#33–36、#39）文字 0 处改动。
- 全文作答格经校验：不含连续空格（2 个以上）、不含全角空格（U+3000），段首无空白——版式全部靠 Word 属性，未用空格凑。

## 第 3 轮修订（去除表格内多余空格）

- 现象：作答表格虽已上下+左右居中，但每个填了答案的单元格里，答案上方仍有一块由原“书写横线”产生的空白行。
- 处理：所有 62 个作答格改为复用单元格自身第一个段落写答案，并移除该格内所有空 `<w:br/>`；首行缩进、对齐、居中属性保持不变。
- 复核：`inspection/verify_layout.py` 现会把“作答格内的 `<w:br/>`”与“作答格外的 `<w:br/>`”分开统计，结论 168 → 0 / 30 → 30，全部通过。

## 目录结构

| 路径 | 内容 |
| --- | --- |
| `scripts/run_classroom.py` | 复现课堂 notebook（距离 / 固定 80-40 划分 / 标准化 / PCA / UMAP），结果写入 `results/` |
| `scripts/verify_evidence.py` | 复算证据包表 C1/C1续/C2/C2续 |
| `scripts/fill_worksheet.py` | **唯一再生成入口**：把答案写入工作页并排版，输出 `deliverable/` |
| `results/` | 课堂运行结果：距离图、PCA/UMAP 图、见过-未见 CSV、两处 JSON |
| `inspection/` | 解析 docx/pptx/plan 的脚本与转储；校对脚本保留 `audit_completed.py`（查是否有漏答）与 `verify_layout.py`（查排版 + `<w:br/>` 口径） |
| `deliverable/` | 最终成品（docx + answers.md） |

## 复现方式（在仓库根目录，使用仓库内 .venv）

```powershell
.venv\Scripts\python.exe homework3\analysis\scripts\run_classroom.py
.venv\Scripts\python.exe homework3\analysis\scripts\verify_evidence.py
.venv\Scripts\python.exe homework3\analysis\scripts\fill_worksheet.py
```

再跑校对：

```powershell
.venv\Scripts\python.exe homework3\analysis\inspection\audit_completed.py
.venv\Scripts\python.exe homework3\analysis\inspection\verify_layout.py
```

## 关键设定

- 随机种子：20260921
- 固定划分：见过 80 人（高危 27 / 非高危 53），未见 40 人（高危 14 / 非高危 26）
- 表达单位：log2(1+FPKM)，基因层级 23146 列，不再取对数
- 作答中所有数字均可由 `results/` 与证据包表格复核
