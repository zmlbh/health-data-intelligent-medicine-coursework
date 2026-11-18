from pathlib import Path
import re
import os

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "论文式作业.md"
FIG_DIR = ROOT / "research-upgrade" / "figures"
OUT = ROOT / "research-upgrade" / "submission"
OUT.mkdir(parents=True, exist_ok=True)
DOCX = Path(os.environ.get(
    "CENTRE_TRANSPORT_DOCX_OUT",
    OUT / "centre-transport-linear-prediction.docx",
))

FIGURES = {
    "图 1": FIG_DIR / "data-landscape-cn.png",
    "图 2": FIG_DIR / "feature-distributions-cn.png",
    "图 3": FIG_DIR / "calibration-cn.png",
    "图 4": FIG_DIR / "multisite-transport-main-cn.png",
    "图 5": FIG_DIR / "operating-profile-cn.png",
    "图 6": FIG_DIR / "coefficient-stability-cn.png",
    "图 7": FIG_DIR / "threshold-sensitivity-cn.png",
    "图 8": FIG_DIR / "discrimination-utility-plane-cn.png",
}

FIGURE_WIDTHS = {
    "图 1": 17.2, "图 2": 16.8, "图 3": 16.2, "图 4": 16.8,
    "图 5": 16.8, "图 6": 16.5, "图 7": 16.3, "图 8": 16.2,
}

EQUATIONS = [
    "p(x)=1/[1+exp{−(β₀+xᵀβ)}].",
    "δₖ(x)=xᵀΣ⁻¹μₖ−½μₖᵀΣ⁻¹μₖ+lnπₖ.",
    "L_class = 5FN + FP.",
    "L(π,TPR,FPR)=5π(1−TPR)+(1−π)FPR.",
    "ΔL_prev=L(πₜ,TPRₛ,FPRₛ)−L(πₛ,TPRₛ,FPRₛ).",
    "ΔL_cond=L(πₜ,TPRₜ,FPRₜ)−L(πₜ,TPRₛ,FPRₛ).",
]


def no_borders(table) -> None:
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.first_child_found_in("w:tblBorders")
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{edge}")
        element.set(qn("w:val"), "nil")
        borders.append(element)


def set_keep(paragraph, next_=False) -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    p_pr.append(OxmlElement("w:keepLines"))
    if next_:
        p_pr.append(OxmlElement("w:keepNext"))


def shade(paragraph, fill="F2F2F2") -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    p_pr.append(shd)


def clean_inline_math(text: str) -> str:
    replacements = {
        r"\boldsymbol{\beta}": "β", r"\mathbf{x}": "x",
        r"\pi": "π", r"\alpha": "α", r"\beta": "β", r"\Sigma": "Σ",
        r"\mathsf T": "T", r"\mid": "|", r"\mathrm": "",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    for old, new in {"_0": "₀", "_s": "ₛ", "_t": "ₜ", "_k": "ₖ"}.items():
        text = text.replace(old, new)
    text = text.replace("{", "").replace("}", "")
    return text


def add_inline(paragraph, text: str) -> None:
    text = re.sub(r"\\\((.*?)\\\)", lambda m: clean_inline_math(m.group(1)), text)
    token_re = re.compile(r"(\*\*.*?\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^\)]+\))")
    for part in token_re.split(text):
        if not part:
            continue
        if part.startswith("**"):
            paragraph.add_run(part[2:-2]).bold = True
        elif part.startswith("*"):
            paragraph.add_run(part[1:-1]).italic = True
        elif part.startswith("`"):
            run = paragraph.add_run(part[1:-1]); run.font.name = "Consolas"; run.font.size = Pt(8.5)
        elif part.startswith("[") and "](" in part:
            paragraph.add_run(part[1:part.index("](")])
        else:
            paragraph.add_run(part)


def configure(document: Document) -> None:
    sec = document.sections[0]
    sec.page_height, sec.page_width = Cm(29.7), Cm(21)
    sec.top_margin, sec.bottom_margin = Cm(1.75), Cm(1.75)
    sec.left_margin, sec.right_margin = Cm(1.8), Cm(1.8)
    sec.header_distance, sec.footer_distance = Cm(0.7), Cm(0.8)
    styles = document.styles
    for name in ["Normal", "Title", "Subtitle", "Heading 1", "Heading 2", "Heading 3", "Caption"]:
        style = styles[name]
        style.font.name = "Microsoft YaHei"
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
        style.paragraph_format.widow_control = True
    styles["Normal"].font.size = Pt(10)
    styles["Normal"].paragraph_format.line_spacing = 1.25
    styles["Normal"].paragraph_format.space_after = Pt(5)
    styles["Title"].font.size = Pt(20); styles["Title"].font.bold = True
    styles["Title"].paragraph_format.space_after = Pt(10)
    styles["Subtitle"].font.size = Pt(9); styles["Subtitle"].paragraph_format.space_after = Pt(5)
    styles["Heading 1"].font.size = Pt(14); styles["Heading 1"].font.bold = True
    styles["Heading 1"].paragraph_format.space_before = Pt(13); styles["Heading 1"].paragraph_format.space_after = Pt(5)
    styles["Heading 2"].font.size = Pt(11); styles["Heading 2"].font.bold = True
    styles["Heading 2"].paragraph_format.space_before = Pt(10); styles["Heading 2"].paragraph_format.space_after = Pt(4)
    styles["Heading 3"].font.size = Pt(10); styles["Heading 3"].font.bold = True
    styles["Caption"].font.size = Pt(8); styles["Caption"].font.bold = False; styles["Caption"].font.italic = False
    styles["Caption"].paragraph_format.line_spacing = 1.1
    styles["Caption"].paragraph_format.space_after = Pt(7)
    header = sec.header.paragraphs[0]
    header.text = ""
    footer = sec.footer.paragraphs[0]; footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    field = OxmlElement("w:fldSimple"); field.set(qn("w:instr"), "PAGE"); footer._p.append(field)


def add_equation(document: Document, number: int) -> None:
    table = document.add_table(rows=1, cols=3)
    table.autofit = False
    widths = [Cm(0.8), Cm(14.6), Cm(0.8)]
    for cell, width in zip(table.rows[0].cells, widths):
        cell.width = width; cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    no_borders(table)
    centre = table.cell(0, 1).paragraphs[0]
    centre.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = centre.add_run(EQUATIONS[number - 1]); run.font.name = "Cambria Math"; run.font.size = Pt(9.5)
    right = table.cell(0, 2).paragraphs[0]
    right.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    right.add_run(f"（{number}）").font.size = Pt(9.5)
    set_keep(centre); set_keep(right)


def build() -> None:
    document = Document(); configure(document)
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    in_equation = False; equation_number = 0; in_references = False
    for raw in lines:
        line = raw.strip()
        if line == r"\[":
            in_equation = True; continue
        if line == r"\]":
            in_equation = False; equation_number += 1; add_equation(document, equation_number); continue
        if in_equation:
            continue
        if not line:
            continue
        if line.startswith("# "):
            p = document.add_paragraph(line[2:], "Title"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; set_keep(p, True); continue
        if line.startswith("> "):
            p = document.add_paragraph(style="Subtitle"); add_inline(p, line[2:]); shade(p, "EEF3F7")
            p.paragraph_format.left_indent = Cm(0.25); p.paragraph_format.right_indent = Cm(0.25); continue
        if line.startswith("## "):
            heading = line[3:]; in_references = heading.endswith("参考文献")
            p = document.add_paragraph(heading, "Heading 1"); set_keep(p, True); continue
        if line.startswith("### "):
            p = document.add_paragraph(line[4:], "Heading 2"); set_keep(p, True); continue
        if line.startswith("![图 "):
            match = re.match(r"!\[(图 [1-9])", line)
            if match:
                p = document.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                key = match.group(1)
                p.add_run().add_picture(str(FIGURES[key]), width=Cm(FIGURE_WIDTHS[key])); set_keep(p, True)
            continue
        if re.match(r"\*\*图 [1-9]", line):
            p = document.add_paragraph(style="Caption"); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            add_inline(p, line); set_keep(p); continue
        if re.match(r"^\[\d+\] ", line) and in_references:
            p = document.add_paragraph(style="Caption")
            p.paragraph_format.left_indent = Cm(0.48); p.paragraph_format.first_line_indent = Cm(-0.48)
            p.paragraph_format.line_spacing = 1.0; p.paragraph_format.space_after = Pt(0.8)
            add_inline(p, line)
            for run in p.runs: run.font.size = Pt(6.2)
            continue
        p = document.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.first_line_indent = Cm(0.74)
        add_inline(p, line); set_keep(p)
        if len(document.paragraphs) >= 2 and document.paragraphs[-2].text == "摘要":
            shade(p, "F3F3F3"); p.paragraph_format.left_indent = Cm(0.35); p.paragraph_format.right_indent = Cm(0.35)
            p.paragraph_format.space_before = Pt(5); p.paragraph_format.space_after = Pt(8)
    if equation_number != len(EQUATIONS):
        raise RuntimeError(f"公式数量不一致：读取到 {equation_number}，预期 {len(EQUATIONS)}")
    props = document.core_properties
    props.title = "跨中心迁移可保留区分能力，却逆转线性临床预测的决策效用"
    props.subject = "线性模型课程研究论文式作业"
    props.keywords = "外部验证, 迁移性, 逻辑回归, LDA, 决策效用"
    document.save(DOCX); print(DOCX)


if __name__ == "__main__":
    build()
