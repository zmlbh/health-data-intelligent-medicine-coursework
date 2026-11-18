from copy import deepcopy
from pathlib import Path
import shutil

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'CTG_Ensemble_Learning_Conference_Paper_7pages.docx'
BACKUP = ROOT / 'CTG_Ensemble_Learning_Conference_Paper_single_column_backup.docx'
shutil.copy2(BACKUP, SOURCE)
doc = Document(SOURCE)

def set_cols(section, n=2, space='360'):
    sect = section._sectPr
    cols = sect.find(qn('w:cols'))
    if cols is None:
        cols = OxmlElement('w:cols')
        sect.append(cols)
    cols.set(qn('w:num'), str(n))
    cols.set(qn('w:space'), space)

def insert_after(paragraph, text):
    new_p = OxmlElement('w:p')
    paragraph._p.addnext(new_p)
    result = Paragraph(new_p, paragraph._parent)
    result.paragraph_format.first_line_indent = Inches(.18)
    result.paragraph_format.line_spacing = 1.05
    result.paragraph_format.space_after = Pt(3)
    run = result.add_run(text)
    run.font.name = 'Times New Roman'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    run.font.size = Pt(9)
    return result

# Preserve the title/abstract front matter; make the article body a two-column conference layout.
set_cols(doc.sections[-1], 2)

# Drop the last two decorative diagrams and their captions as requested.
for para in list(doc.paragraphs):
    if para.text.startswith('图 7') or para.text.startswith('图 8'):
        previous = para._p.getprevious()
        if previous is not None:
            previous.getparent().remove(previous)
        para._element.getparent().remove(para._element)

# Add verified raw-data description immediately after the dataset paragraph.
for para in list(doc.paragraphs):
    if para.text.startswith('数据来自 UCI Cardiotocography'):
        added = insert_after(para,
            '数据结构进一步说明了为何必须按 recording_id 分组：训练集的 1,279 个片段来自 209 个录音，每个录音包含 1–26 个片段（中位数 4、四分位距 2–8）。训练集阳性为 108/1,279（8.4%），明显少于阴性 1,171 条，因此只报告 ROC-AUC 会掩盖少数类识别困难；本文同时报告 PR-AUC、balanced accuracy、敏感度和特异度。')
        insert_after(added,
            '原始变量为 21 个连续 CTG 自动分析特征，覆盖胎心率基线、加速/减速事件、短期与长期变异性和直方图统计量。例如训练集胎心率基线 LB 的均值为 133.25、标准差 9.33、范围 110–159。sample_id 和 recording_id 仅承担追踪与分组职责；若将它们输入模型，得到的高分将不再是可解释的生理信号证据。')
        break

# The main result table is retained; a wide method-comparison table is converted to prose below.
for para in list(doc.paragraphs):
    if para.text.startswith('4.3 Bagging 与 Boosting'):
        added = insert_after(para,
            '机制对照表明，Bagging 与随机森林均用相互独立、可并行的深树来降低方差；二者的差别在于随机森林还在每个节点随机抽取候选特征，以降低树间错误相关性。相对地，AdaBoost 和梯度提升按顺序更新，前者增加错分样本权重，后者在二分类 log-loss 下拟合负梯度 y−p，因此更依赖学习率、轮数与验证集早停。')
        insert_after(added,
            '这一区分回应了教师材料中“不能把 Boosting 简化为 Bagging”的要求：树数增多对随机森林通常只带来平台期后的计算代价，而 Boosting 轮数过多可能追随噪声。OOB 可作为 Bagging 类方法的内部估计，但在同一录音含多片段的 CTG 数据中仍可能乐观，故本文不以 OOB 代替 recording_id 分组的交叉验证。')
        break

for table in list(doc.tables[1:]):
    table._element.getparent().remove(table._element)

# Convert the main result to a two-column compact table so no metrics are lost in a narrow column.
main = doc.tables[0]
for row in main.rows:
    while len(row.cells) > 2:
        row._tr.remove(row.cells[-1]._tc)
grid = main._tbl.tblGrid
for col in list(grid)[2:]:
    grid.remove(col)
values = [
    ('模型', '分组 CV 指标  ROC-AUC / PR-AUC / BA'),
    ('单棵决策树', '0.866 / — / —'),
    ('逻辑回归', '0.990 / 0.923 / 0.872'),
    ('RBF-SVM', '0.980 / 0.875 / 0.797'),
    ('Bagging', '0.978 / 约 0.900 / 约 0.850'),
    ('随机森林', '0.994 / 0.944 / 0.925'),
]
for row, (name, metric) in zip(main.rows, values):
    row.cells[0].text = name
    row.cells[1].text = metric

# Fit the retained table inside one column, with white cells, black rules and centered values.
for table in doc.tables:
    table.alignment = WD_TABLE_ALIGNMENT.LEFT
    table.autofit = False
    widths = [1.10, 2.05]
    for row in table.rows:
        for i, cell in enumerate(row.cells):
            cell.width = Inches(widths[i])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            for p in cell.paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for r in p.runs:
                    r.font.size = Pt(6.2)

# Make every retained experiment figure column-width, retaining clear captions below each plot.
for shape in doc.inline_shapes:
    ratio = shape.height / shape.width
    shape.width = Inches(3.15)
    shape.height = int(shape.width * ratio)

doc.save(SOURCE)
print(SOURCE)
