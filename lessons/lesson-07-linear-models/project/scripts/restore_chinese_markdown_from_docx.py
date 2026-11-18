from pathlib import Path

from docx import Document
from docx.document import Document as DocumentClass
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph


ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "research-upgrade" / "submission" / "centre-transport-linear-prediction.docx"
OUT = ROOT / "论文式作业.md"

FIGURES = [
    ("图 1｜留一中心外部验证与决策审计流程", "research-upgrade/figures/study-design-cn.png"),
    ("图 2｜四个中心的结局构成、缺失模式与数值特征分布", "research-upgrade/figures/data-landscape-cn.png"),
    ("图 3｜连续变量分布与分类变量构成", "research-upgrade/figures/feature-distributions-cn.png"),
    ("图 4｜四个外部中心的分组校准", "research-upgrade/figures/calibration-cn.png"),
    ("图 5｜跨中心迁移中的区分能力、损失来源与决策效用", "research-upgrade/figures/multisite-transport-main-cn.png"),
    ("图 6｜冻结阈值、外部操作点与混淆构成", "research-upgrade/figures/operating-profile-cn.png"),
]

EQUATIONS = [
    r"P(Y=1\mid\mathbf{x})=\frac{1}{1+\exp[-(\beta_0+\mathbf{x}^{\mathsf T}\boldsymbol{\beta})]}.",
    r"\delta_k(\mathbf{x})=\mathbf{x}^{\mathsf T}\Sigma^{-1}\boldsymbol{\mu}_k-\frac{1}{2}\boldsymbol{\mu}_k^{\mathsf T}\Sigma^{-1}\boldsymbol{\mu}_k+\log\pi_k.",
    r"L_{\mathrm{class}}=5FN+FP.",
    r"L(\pi,TPR,FPR)=5\pi(1-TPR)+(1-\pi)FPR.",
    r"L(\pi_t,TPR_s,FPR_s)-L(\pi_s,TPR_s,FPR_s).",
    r"L(\pi_t,TPR_t,FPR_t)-L(\pi_t,TPR_s,FPR_s).",
]

H1 = {
    "摘要": "摘要", "引言": "1 引言", "结果": "2 结果", "讨论": "3 讨论",
    "方法": "4 方法", "数据与代码可用性": "5 数据与代码可用性", "参考文献": "6 参考文献",
}


def iter_block_items(parent):
    parent_elm = parent.element.body if isinstance(parent, DocumentClass) else parent._tc
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def main() -> None:
    document = Document(DOCX)
    lines = []
    figure_no = 0
    equation_no = 0
    current_h1 = ""
    h2_count = 0
    for block in iter_block_items(document):
        if isinstance(block, Table):
            if equation_no < len(EQUATIONS):
                lines += [r"\[", EQUATIONS[equation_no], r"\]", ""]
                equation_no += 1
            continue
        text = block.text.strip()
        has_image = bool(block._p.xpath(".//w:drawing"))
        style = block.style.name
        if has_image:
            title, path = FIGURES[figure_no]
            lines += [f"![{title}]({path})", ""]
            figure_no += 1
            continue
        if not text:
            continue
        if style == "Title":
            lines += [f"# {text}", ""]
        elif style == "Subtitle":
            lines += [f"> {text}", ""]
        elif style == "Heading 1":
            current_h1 = H1.get(text, text)
            h2_count = 0
            lines += [f"## {current_h1}", ""]
        elif style == "Heading 2":
            h2_count += 1
            prefix = current_h1.split()[0] if current_h1 and current_h1[0].isdigit() else ""
            numbered = f"{prefix}.{h2_count} {text}" if prefix else text
            lines += [f"### {numbered}", ""]
        elif style == "Caption" and text.startswith("图 "):
            head, sep, tail = text.partition("。")
            lines += [f"**{head}。**{tail}" if sep else f"**{text}**", ""]
        else:
            lines += [text, ""]
    OUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
