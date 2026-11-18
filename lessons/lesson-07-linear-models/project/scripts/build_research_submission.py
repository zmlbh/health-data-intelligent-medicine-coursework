from pathlib import Path
import re

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research-upgrade" / "Nature-style-manuscript.md"
FIGURES = {
    "![Figure 1]": ROOT / "research-upgrade" / "figures" / "study-design.png",
    "![Figure 2]": ROOT / "research-upgrade" / "figures" / "data-landscape.png",
    "![Figure 3]": ROOT / "research-upgrade" / "figures" / "multisite-transport-main.png",
}
OUT = ROOT / "research-upgrade" / "submission"
OUT.mkdir(parents=True, exist_ok=True)
DOCX = OUT / "centre-transport-linear-prediction.docx"


def set_cell_shading(paragraph, fill="F2F2F2"):
    p_pr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    p_pr.append(shd)


def set_keep(paragraph, next_=False):
    p_pr = paragraph._p.get_or_add_pPr()
    keep = OxmlElement("w:keepLines")
    p_pr.append(keep)
    if next_:
        keep_next = OxmlElement("w:keepNext")
        p_pr.append(keep_next)


def add_inline(paragraph, text):
    text = (text.replace("\\(\\pi\\)", "π")
                .replace("\\(TPR\\)", "TPR")
                .replace("\\(FPR\\)", "FPR")
                .replace("\\(5\\pi\\)", "5π")
                .replace("\\(1-\\pi\\)", "1−π")
                .replace("\\(\\alpha=0.05/3\\)", "α = 0.05/3")
                .replace("\\((\\pi_s,TPR_s,FPR_s)\\)", "(πₛ, TPRₛ, FPRₛ)")
                .replace("\\((\\pi_t,TPR_t,FPR_t)\\)", "(πₜ, TPRₜ, FPRₜ)")
                .replace("alone1–7", "alone [1–7]")
                .replace("decisions8,9", "decisions [8,9]")
                .replace("half10", "half [10]")
                .replace("thresholds11", "thresholds [11]")
                .replace("benefit12–14", "benefit [12–14]")
                .replace("collection15", "collection [15]")
                .replace("questions16", "questions [16]")
                .replace("validation10,17", "validation [10,17]")
                .replace("discrimination8", "discrimination [8]")
                .replace("work12–14", "work [12–14]")
                .replace("(200)15", "(200) [15]"))
    token_re = re.compile(r"(\*\*.*?\*\*|\*[^*]+\*|`[^`]+`|\[[^\]]+\]\([^\)]+\))")
    for part in token_re.split(text):
        if not part:
            continue
        if part.startswith("**"):
            paragraph.add_run(part[2:-2]).bold = True
        elif part.startswith("*"):
            paragraph.add_run(part[1:-1]).italic = True
        elif part.startswith("`"):
            run = paragraph.add_run(part[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(8.5)
        elif part.startswith("[") and "](" in part:
            paragraph.add_run(part[1:part.index("](")])
        else:
            paragraph.add_run(part)


def configure(document):
    sec = document.sections[0]
    sec.page_height, sec.page_width = Cm(29.7), Cm(21)
    sec.top_margin, sec.bottom_margin = Cm(1.8), Cm(1.8)
    sec.left_margin, sec.right_margin = Cm(1.8), Cm(1.8)
    sec.header_distance, sec.footer_distance = Cm(0.7), Cm(0.8)

    styles = document.styles
    for name in ["Normal", "Title", "Subtitle", "Heading 1", "Heading 2", "Heading 3", "Caption"]:
        style = styles[name]
        style.font.name = "Arial"
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), "Arial")
        style.paragraph_format.widow_control = True
    styles["Normal"].font.size = Pt(10)
    styles["Normal"].paragraph_format.line_spacing = 1.16
    styles["Normal"].paragraph_format.space_after = Pt(5)
    styles["Title"].font.size = Pt(22)
    styles["Title"].font.bold = True
    styles["Title"].paragraph_format.space_after = Pt(10)
    styles["Subtitle"].font.size = Pt(9)
    styles["Subtitle"].paragraph_format.space_after = Pt(4)
    styles["Heading 1"].font.size = Pt(14)
    styles["Heading 1"].font.bold = True
    styles["Heading 1"].paragraph_format.space_before = Pt(14)
    styles["Heading 1"].paragraph_format.space_after = Pt(5)
    styles["Heading 2"].font.size = Pt(11)
    styles["Heading 2"].font.bold = True
    styles["Heading 2"].paragraph_format.space_before = Pt(10)
    styles["Heading 2"].paragraph_format.space_after = Pt(4)
    styles["Heading 3"].font.size = Pt(10)
    styles["Heading 3"].font.bold = True
    styles["Caption"].font.size = Pt(8)
    styles["Caption"].font.bold = False
    styles["Caption"].font.italic = False
    styles["Caption"].paragraph_format.line_spacing = 1.05
    styles["Caption"].paragraph_format.space_after = Pt(8)

    header = sec.header.paragraphs[0]
    header.text = "ARTICLE  |  EXPLORATORY METHODS CASE STUDY"
    header.style = styles["Caption"]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer = sec.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)


def build():
    document = Document()
    configure(document)
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    in_equation = False
    equation_lines = []
    in_references = False
    for raw in lines:
        line = raw.strip()
        if line == "\\[":
            in_equation = True
            equation_lines = []
            continue
        if line == "\\]":
            in_equation = False
            p = document.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            equation = " ".join(equation_lines)
            equation = (equation.replace("\\,", " ")
                         .replace("\\pi_s", "πₛ").replace("\\pi_t", "πₜ")
                         .replace("\\pi", "π")
                         .replace("TPR_s", "TPRₛ").replace("TPR_t", "TPRₜ")
                         .replace("FPR_s", "FPRₛ").replace("FPR_t", "FPRₜ")
                         .replace("\\alpha", "α"))
            run = p.add_run(equation)
            run.font.name = "Cambria Math"
            run.font.size = Pt(10)
            set_keep(p)
            continue
        if in_equation:
            equation_lines.append(line)
            continue
        if not line:
            continue
        if line.startswith("# "):
            p = document.add_paragraph(line[2:], "Title")
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            set_keep(p, True)
            continue
        if line.startswith("**Article type:**") or line.startswith("**Authors:**") or line.startswith("**Affiliations:**") or line.startswith("**Correspondence:**"):
            p = document.add_paragraph(style="Subtitle")
            add_inline(p, line)
            continue
        if line.startswith("## "):
            heading = line[3:]
            in_references = heading == "References"
            p = document.add_paragraph(heading, "Heading 1")
            set_keep(p, True)
            continue
        if line.startswith("### "):
            p = document.add_paragraph(line[4:], "Heading 2")
            set_keep(p, True)
            continue
        figure_path = next((path for marker, path in FIGURES.items() if line.startswith(marker)), None)
        if figure_path is not None:
            p = document.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run().add_picture(str(figure_path), width=Cm(17.2))
            set_keep(p, True)
            continue
        if re.match(r"\*\*Figure [123]", line):
            p = document.add_paragraph(style="Caption")
            add_inline(p, line)
            set_keep(p)
            continue
        if re.match(r"^\d+\. ", line) and in_references:
            p = document.add_paragraph(style="Caption")
            p.paragraph_format.left_indent = Cm(0.55)
            p.paragraph_format.first_line_indent = Cm(-0.55)
            p.paragraph_format.space_after = Pt(2.5)
            p.paragraph_format.line_spacing = 1.0
            add_inline(p, line)
            for run in p.runs:
                run.font.size = Pt(7.3)
            continue
        p = document.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        add_inline(p, line)
        set_keep(p)
        if document.paragraphs and any(h.text == "Summary" for h in document.paragraphs[-2:-1]):
            set_cell_shading(p, "F3F3F3")
            p.paragraph_format.left_indent = Cm(0.35)
            p.paragraph_format.right_indent = Cm(0.35)
            p.paragraph_format.space_before = Pt(5)
            p.paragraph_format.space_after = Pt(8)

    props = document.core_properties
    props.title = "Centre transport can preserve discrimination while reversing decision utility"
    props.subject = "Exploratory multicentre validation of linear clinical prediction"
    props.keywords = "external validation, transportability, logistic regression, LDA, decision utility"
    document.save(DOCX)
    print(DOCX)


if __name__ == "__main__":
    build()
