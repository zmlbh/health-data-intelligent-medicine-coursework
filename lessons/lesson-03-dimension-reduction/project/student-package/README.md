# 第四课 高维数据与降维 · 学生材料

本课讨论同一批120名神经母细胞瘤患者、23,146个基因的表达数据：
怎样理解并展示这批患者的高维数据，同时避免把漂亮的图和训练高分当作可靠发现。

## 先做什么

1. **上课前**：读 `pbl-high-dimension-reduction-student-worksheet.docx` 的「情境与任务」页，
   再按「背景阅读」页读完标为**先读**的 R1–R3（约45分钟）。这三份都在 `readings/` 里，不用联网。
2. **课堂**：跟着 `notebook/pbl-high-dimension-reduction-classroom.ipynb` 运行，
   把结果填进工作页的「课堂实验记录」。
3. **课后自学**：按 Q1→Q6 顺序做工作页第二阶段。每个模块开头写了它的**背景阅读编号**，
   做到哪一模块就读哪一份（R4–R9，三选一后约90分钟）。
   证据在 `pbl-high-dimension-reduction-evidence-pack.docx`，由老师按 Packet A→B→C→D 分阶段发放。
4. **翻转课堂**：每人都要准备被随机抽到上台讲，讲的是你自己的证据和推理，没有固定讲稿。

工作页的自学部分目标150分钟，另留30分钟读写缓冲；背景阅读时间不计在内。

## 目录说明

| 路径 | 内容 |
|---|---|
| `pbl-high-dimension-reduction-student-worksheet.docx` | 学生工作页，本课的主材料，全部作答都写在这里 |
| `pbl-high-dimension-reduction-evidence-pack.docx` | 分阶段证据包，与工作页的表号图号完全一致 |
| `readings/` | 背景阅读的 PDF，来源与范围见 `readings/README.md` |
| `notebook/` | 课堂实验 notebook |
| `data/` | 教学数据：`cohort120.npz` 是固定的120人×23,146基因矩阵，`patient-manifest.csv` 是患者名单与80/40划分 |
| `data/source/` | 原始来源的说明文件（README、SOFT 注释），Q1 的查证要用 `README.txt` 的 Genes x Samples 段 |
| `requirements.txt` | 运行 notebook 所需的依赖版本 |

原始表达文件（GEO 上的 `GSE49711_SEQC_NB_TUC_G_log2.txt.gz`，约78MB）没有放进来，
课堂实验不需要它；要自己核对原始数据的话从 GEO 下载：
https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE49711

## 运行环境

装好 `requirements.txt` 里的依赖后，在本目录或 `notebook/` 目录启动 Jupyter 都可以，
notebook 会自己找到 `data/`。第一次运行 UMAP 需要编译，会慢一两分钟，属正常。

## 允许和不允许

可以使用教材、网课、可靠参考资料和 AI 助手，但**必须核对 AI 给出的数字和来源，并保留你自己的判断**。
工作页的每一道题都要求引用具体的表号、图号和数字；照搬一段通用说明是不算数的。

本课用于研究方法训练。高危标签是研究中的临床风险分组，不是健康与患病的诊断分类；
本队列不能证明临床有效性、部署可行性或因果关系。UMAP 用于探索，不能由图形直接命名新亚型。
