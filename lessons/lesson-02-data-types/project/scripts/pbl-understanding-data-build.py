#!/usr/bin/env python
"""Build the approved Understanding Data PBL package.

This course-specific script creates objective-mapped evidence, four DOCX
teaching documents, a reproducible notebook, and the package manifest.  It
writes only inside ``class2026/materials/2. Data``.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor
from sklearn.datasets import load_breast_cancer
from sklearn.decomposition import PCA
from sklearn.feature_selection import mutual_info_classif
from sklearn.metrics import pairwise_distances
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
SLUG = "understanding-data"
ASSET_DIR = ROOT / "assets" / f"pbl-{SLUG}"
NOTEBOOK_DIR = ROOT / "notebook"
DATA_PATH = ASSET_DIR / "heart-disease-four-site.csv"


def ensure_dirs() -> None:
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)

NAVY = "17365D"
BLUE = "2F6B9A"
PALE_BLUE = "EAF2F8"
PALE_GRAY = "F5F6F7"
MID_GRAY = "D9D9D9"
BLACK = "000000"

LO = [
    ("LO1", "区分连续、离散、二分类、多分类、有序、时间和高维变量。", "根据变量语义和测量尺度完成变量分类，并说明判断依据。"),
    ("LO2", "用样本 × 特征的数据矩阵解释临床表格、组学矩阵和图像特征表。", "说明数据对象、行列含义、表示结构及其对分析的影响。"),
    ("LO3", "根据变量类型、研究问题和结局形式，提出合理的统计检验或模型候选。", "把研究问题、变量类型与可用方法连接起来，并指出适用条件。"),
    ("LO4", "识别缺失值、异常值、批次效应、类别不平衡和测量误差等数据质量问题。", "使用数据证据识别质量风险，区分观察事实与原因推断。"),
    ("LO5", "判断哪些变量需要标准化，并说明标准化应在数据划分后如何实施。", "设计只用训练数据拟合预处理参数的无泄漏流程。"),
    ("LO6", "对一个公开生物医学数据集完成基本的数据审查，并写出结论边界。", "提交可审计的数据准备建议，并明确临床、因果与部署边界。"),
    ("LO7", "根据数据语义选择 Euclidean/Manhattan、cosine、correlation 或 Jaccard 等度量。", "比较度量对尺度、平移、相关结构、稀疏性和共同为零的敏感性。"),
    ("LO8", "说明代表性抽样、分层抽样、聚合、离散化、二值化和数值变换的用途、风险与实施顺序。", "比较处理方案造成的代表性和信息变化，并给出实施顺序。"),
]

CONCEPTS = [
    {"id": "C1", "name": "数据对象与变量语义", "objective_ids": ["LO1", "LO2", "LO3"], "concepts": ["data object", "attribute", "variable role", "nominal", "ordinal", "interval", "ratio", "discrete", "continuous", "asymmetric binary"]},
    {"id": "C2", "name": "数据表示与数据特征", "objective_ids": ["LO2", "LO6"], "concepts": ["record", "matrix", "document", "transaction", "graph", "ordered data", "dimensionality", "sparsity", "resolution", "size"]},
    {"id": "C3", "name": "数据质量与来源", "objective_ids": ["LO4", "LO6"], "concepts": ["missingness", "noise", "outlier", "duplicate", "batch effect", "class imbalance", "measurement error", "provenance"]},
    {"id": "C4", "name": "相似性 距离与依赖", "objective_ids": ["LO7"], "concepts": ["Euclidean", "Manhattan", "Minkowski", "Mahalanobis", "SMC", "Jaccard", "cosine", "correlation", "entropy", "mutual information", "mixed-type proximity"]},
    {"id": "C5", "name": "抽样 聚合与属性变换", "objective_ids": ["LO5", "LO8"], "concepts": ["simple random sampling", "stratified sampling", "aggregation", "discretization", "binarization", "encoding", "log transform", "normalization", "data leakage"]},
    {"id": "C6", "name": "降维与数据准备综合", "objective_ids": ["LO2", "LO3", "LO5", "LO6", "LO8"], "concepts": ["curse of dimensionality", "PCA", "feature subset selection", "feature creation", "workflow", "stopping condition", "reporting boundary"]},
]

QUESTIONS = [
    {"id": "Q1", "question": "数据对象、属性值、变量角色和测量尺度分别是什么？", "objective_ids": ["LO1", "LO3"], "concept_ids": ["C1"], "required_learning": ["变量角色", "测量尺度", "类型与方法适配"], "student_action": "审查数据字典和尺度微型案例，纠正仅凭数字编码判断变量类型的做法。", "evidence_needed": ["packet-b-data-dictionary.csv", "packet-b-measurement-scale-cases.csv", "packet-b-method-map.csv"], "student_output": "变量审查表和方法选择理由", "contribution_to_synthesis": "确定哪些描述、变换、距离和方法在语义上允许。"},
    {"id": "Q2", "question": "数据属于记录、矩阵、文档、事务、图还是有序数据，表示方式如何影响分析？", "objective_ids": ["LO2"], "concept_ids": ["C1", "C2"], "required_learning": ["数据对象", "六类数据结构", "观察单位与独立性"], "student_action": "比较生物医学微型案例，说明每种表示保留和丢失的关系。", "evidence_needed": ["packet-b-structure-types.csv"], "student_output": "数据表示说明", "contribution_to_synthesis": "确定行列、关系、顺序和分析单位。"},
    {"id": "Q3", "question": "维度、稀疏性、分辨率和数据规模带来哪些限制？", "objective_ids": ["LO2", "LO8"], "concept_ids": ["C2", "C6"], "required_learning": ["维度", "稀疏性", "分辨率", "规模", "维度灾难"], "student_action": "比较两套数据的结构，并检查距离集中随维度变化。", "evidence_needed": ["packet-b-data-characteristics.csv", "packet-c-distance-concentration.csv"], "student_output": "计算与表示风险清单", "contribution_to_synthesis": "决定是否改变表示、选择特征或降维。"},
    {"id": "Q4", "question": "如何发现并处理缺失、异常、噪声、重复、批次效应、不平衡和测量误差？", "objective_ids": ["LO4", "LO6"], "concept_ids": ["C3"], "required_learning": ["数据质量诊断", "来源与批次", "事实和原因的区别"], "student_action": "计算缺失率、站点差异、异常值、重复、异常零值和类别分布，提出核查顺序。", "evidence_needed": ["packet-b-quality-audit.csv", "packet-b-quality-evidence-boundaries.csv", "packet-b-missingness-by-site.csv", "packet-b-missingness.png", "packet-b-target-by-site.csv"], "student_output": "质量问题 后果 核查 处理矩阵", "contribution_to_synthesis": "形成修复、分层、补充信息或停止分析的条件。"},
    {"id": "Q5", "question": "Euclidean、Manhattan、Minkowski、Mahalanobis、cosine、correlation和信息度量分别保留什么含义？", "objective_ids": ["LO7"], "concept_ids": ["C4"], "required_learning": ["距离与相似性", "尺度与平移敏感性", "协方差", "信息依赖"], "student_action": "比较缩放前后近邻、向量变换、Minkowski参数和Mahalanobis协方差调整。", "evidence_needed": ["packet-c-neighbor-ranking.csv", "packet-c-metric-comparison.csv", "packet-c-distance-sensitivity.png", "packet-c-vector-metrics.csv", "packet-c-information-measures.csv"], "student_output": "度量选择备忘录", "contribution_to_synthesis": "定义任务中有意义的相似。"},
    {"id": "Q6", "question": "面对混合类型变量和缺失值，如何构造可解释的综合相似性？", "objective_ids": ["LO7"], "concept_ids": ["C4"], "required_learning": ["SMC 与 Jaccard", "分类型度量", "缺失维度", "加权组合"], "student_action": "比较共同为零的处理，并设计 Gower 式分项距离。", "evidence_needed": ["packet-c-binary-similarity.csv", "packet-c-mixed-similarity.csv"], "student_output": "综合相似性规则及边界", "contribution_to_synthesis": "避免把任意编码后的混合变量直接投入统一距离。"},
    {"id": "Q7", "question": "抽样和聚合会改变什么，如何检查代表性和信息损失？", "objective_ids": ["LO6", "LO8"], "concept_ids": ["C5"], "required_learning": ["随机抽样", "分层抽样", "代表性", "聚合"], "student_action": "重复比较随机与分层抽样，并对比患者级与站点级结果。", "evidence_needed": ["packet-c-sampling-replicates.csv", "packet-c-sampling-sensitivity.png", "packet-c-aggregation.csv"], "student_output": "抽样与聚合建议", "contribution_to_synthesis": "明确数据代表谁以及哪些细节被聚合隐藏。"},
    {"id": "Q8", "question": "离散化、二值化、编码、变换和标准化应如何选择并防止泄漏？", "objective_ids": ["LO5", "LO8"], "concept_ids": ["C5"], "required_learning": ["离散化", "二值化", "one-hot", "数值变换", "标准化", "训练集拟合"], "student_action": "比较处理前后分布，审计两条预处理流程并修正顺序。", "evidence_needed": ["packet-c-transformation-summary.csv", "packet-c-transformations.png", "packet-d-preprocessing-audit.csv"], "student_output": "无泄漏预处理流程", "contribution_to_synthesis": "规定每个预处理参数的拟合数据和执行时点。"},
    {"id": "Q9", "question": "何时需要 PCA、特征选择或特征创建，如何检查信息和语义损失？", "objective_ids": ["LO2", "LO8"], "concept_ids": ["C6"], "required_learning": ["相关冗余", "PCA", "解释方差", "特征选择", "特征创建"], "student_action": "检查相关特征、累计解释方差和载荷，比较三类维度处理。", "evidence_needed": ["packet-c-pca-summary.csv", "packet-c-pca-loadings.csv", "packet-c-pca.png", "packet-c-feature-options.csv"], "student_output": "降维决策及信息损失说明", "contribution_to_synthesis": "在计算、预测信息和医学可解释性之间做有边界的选择。"},
    {"id": "Q10", "question": "如何综合证据形成可审计的数据准备工作流、方法候选和停止条件？", "objective_ids": ["LO3", "LO5", "LO6"], "concept_ids": ["C6"], "required_learning": ["工作流综合", "适用性", "不确定性", "结论边界"], "student_action": "把 Q1 至 Q9 的结果写成主张 证据 推理 边界，并标注停止条件。", "evidence_needed": ["packet-d-workflow-decision.csv", "packet-d-boundary-checklist.csv", "packet-d-preprocessing-workflow.png"], "student_output": "最终 Data readiness plan", "contribution_to_synthesis": "直接回答总问题并说明何时修改或停止流程。"},
]

MISCONCEPTIONS = [
    "变量存成数字就一定是连续变量。",
    "分类标签编码成 0 1 2 后就具有等距含义。",
    "标准化可以修复缺失 异常 批次效应和测量误差。",
    "所有特征都可直接放入 Euclidean 距离。",
    "稀疏二值向量共同为零越多就越相似。",
    "相关系数接近零表示不存在任何关系。",
    "可以先用全体数据确定插补 分箱和标准化参数再划分。",
    "样本量大就等于具有代表性。",
    "PCA 保留方差就等于保留医学含义。",
]


def rel_asset(name: str) -> str:
    return f"assets/pbl-{SLUG}/{name}"


def save_csv(df: pd.DataFrame, name: str) -> Path:
    path = ASSET_DIR / name
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=90, start=100, bottom=90, end=100) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for m, v in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{m}"))
        if node is None:
            node = OxmlElement(f"w:{m}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(v))
        node.set(qn("w:type"), "dxa")


def set_table_borders(table) -> None:
    tbl_pr = table._tbl.tblPr
    borders = tbl_pr.find(qn("w:tblBorders"))
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tbl_pr.append(borders)
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        tag = borders.find(qn(f"w:{edge}"))
        if tag is None:
            tag = OxmlElement(f"w:{edge}")
            borders.append(tag)
        tag.set(qn("w:val"), "single")
        tag.set(qn("w:sz"), "5")
        tag.set(qn("w:color"), MID_GRAY)


def set_cell_width(cell, inches: float) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_w = tc_pr.find(qn("w:tcW"))
    if tc_w is None:
        tc_w = OxmlElement("w:tcW")
        tc_pr.append(tc_w)
    tc_w.set(qn("w:w"), str(int(inches * 1440)))
    tc_w.set(qn("w:type"), "dxa")


def add_table(doc: Document, headers: list[str], rows: list[list[object]], widths: list[float] | None = None, font_size: float = 8.7, compact_after: bool = False):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_repeat_table_header(table.rows[0])
    for j, header in enumerate(headers):
        cell = table.rows[0].cells[j]
        cell.text = str(header)
        set_cell_shading(cell, NAVY)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        if widths:
            set_cell_width(cell, widths[j])
        for p in cell.paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in p.runs:
                run.font.bold = True
                run.font.color.rgb = RGBColor(255, 255, 255)
                run.font.size = Pt(font_size)
    for i, row in enumerate(rows):
        cells = table.add_row().cells
        for j, value in enumerate(row):
            cells[j].text = "" if value is None else str(value)
            cells[j].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cells[j])
            if widths:
                set_cell_width(cells[j], widths[j])
            if i % 2:
                set_cell_shading(cells[j], PALE_BLUE)
            for p in cells[j].paragraphs:
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.05
                if len(str(value)) < 18 and j == 0:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for run in p.runs:
                    run.font.size = Pt(font_size)
                    run.font.color.rgb = RGBColor(0, 0, 0)
    set_table_borders(table)
    tail = doc.add_paragraph()
    tail.paragraph_format.space_after = Pt(0 if compact_after else 1)
    if compact_after:
        tail.paragraph_format.space_before = Pt(0)
        tail.paragraph_format.line_spacing = Pt(1)
        tail.add_run(" ").font.size = Pt(1)
    return table


def setup_doc(title: str, subtitle: str, landscape: bool = False) -> Document:
    doc = Document()
    section = doc.sections[0]
    section.page_width = Inches(11 if landscape else 8.5)
    section.page_height = Inches(8.5 if landscape else 11)
    section.orientation = WD_ORIENT.LANDSCAPE if landscape else WD_ORIENT.PORTRAIT
    margin = 0.55 if landscape else 0.65
    section.top_margin = section.bottom_margin = Inches(margin)
    section.left_margin = section.right_margin = Inches(margin)
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Arial"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor(0, 0, 0)
    normal.paragraph_format.space_after = Pt(5)
    normal.paragraph_format.line_spacing = 1.12
    for style_name, size in (("Title", 24), ("Subtitle", 12), ("Heading 1", 17), ("Heading 2", 13), ("Heading 3", 11)):
        s = styles[style_name]
        s.font.name = "Arial"
        s._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
        s.font.size = Pt(size)
        s.font.color.rgb = RGBColor(0, 0, 0)
        s.font.bold = style_name != "Subtitle"
    title_ppr = styles["Title"]._element.get_or_add_pPr()
    title_border = title_ppr.find(qn("w:pBdr"))
    if title_border is not None:
        title_ppr.remove(title_border)
    title_p = doc.add_paragraph(style="Title")
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_p.add_run(title)
    title_p_pr = title_p._p.get_or_add_pPr()
    title_border = title_p_pr.find(qn("w:pBdr"))
    if title_border is not None:
        title_p_pr.remove(title_border)
    sub_p = doc.add_paragraph(style="Subtitle")
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_p.add_run(subtitle)
    doc.add_paragraph("本材料用于课程学习与方法训练，不构成临床、患者照护、因果推断或部署建议。")
    return doc


def add_heading(doc: Document, text: str, level: int = 1):
    p = doc.add_heading(text, level=level)
    p.paragraph_format.keep_with_next = True
    return p


def add_response_area(doc: Document, prompt: str, lines: int = 3) -> None:
    p = doc.add_paragraph()
    r = p.add_run(prompt)
    r.bold = True
    for _ in range(lines):
        p = doc.add_paragraph("________________________________________________________________________________")
        p.paragraph_format.space_after = Pt(3)


def add_picture(doc: Document, path: Path, width: float, caption: str) -> None:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(path), width=Inches(width))
    cap = doc.add_paragraph(caption)
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cap.paragraph_format.space_after = Pt(8)
    for run in cap.runs:
        run.italic = True
        run.font.size = Pt(9)


def add_page_number(paragraph) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = paragraph.add_run()
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.extend([fld_char1, instr, fld_char2])


def finalize_doc(doc: Document, path: Path) -> None:
    for section in doc.sections:
        add_page_number(section.footer.paragraphs[0])
    doc.core_properties.author = "AI4BiomedicalDS course team"
    doc.core_properties.subject = "Problem Based Learning"
    doc.save(path)


def entropy(values: pd.Series) -> float:
    p = values.value_counts(normalize=True).to_numpy()
    return float(-(p * np.log2(p)).sum())


def gower_like_distance(a: pd.Series, b: pd.Series, frame: pd.DataFrame) -> tuple[float, int, str]:
    specs = [
        ("age", "continuous", 1.0),
        ("trestbps", "continuous", 1.0),
        ("sex", "nominal", 1.0),
        ("cp", "nominal", 1.0),
        ("slope", "ordinal", 1.0),
        ("exang", "asymmetric_binary", 1.0),
    ]
    parts = []
    used = 0
    weighted = 0.0
    total_w = 0.0
    for col, kind, weight in specs:
        if pd.isna(a[col]) or pd.isna(b[col]):
            continue
        used += 1
        if kind == "continuous":
            rng = frame[col].max(skipna=True) - frame[col].min(skipna=True)
            d = 0.0 if rng == 0 else abs(float(a[col]) - float(b[col])) / float(rng)
        elif kind == "ordinal":
            d = abs(float(a[col]) - float(b[col])) / 2.0
        elif kind == "asymmetric_binary":
            if float(a[col]) == 0 and float(b[col]) == 0:
                continue
            d = 0.0 if float(a[col]) == float(b[col]) else 1.0
        else:
            d = 0.0 if float(a[col]) == float(b[col]) else 1.0
        weighted += weight * d
        total_w += weight
        parts.append(f"{col}:{d:.2f}")
    return (weighted / total_w if total_w else math.nan, used, "; ".join(parts))


def analyze_data() -> dict[str, object]:
    plt.style.use("seaborn-v0_8-whitegrid")
    heart = pd.read_csv(DATA_PATH)
    numeric_cols = [c for c in heart.columns if c not in ["record_id", "site"]]
    for col in numeric_cols:
        heart[col] = pd.to_numeric(heart[col], errors="coerce")
    heart["disease_binary"] = (heart["num"] > 0).astype(int)

    cancer_bunch = load_breast_cancer(as_frame=True)
    cancer = cancer_bunch.frame.copy()
    cancer = cancer.rename(columns={"target": "diagnosis_target"})
    cancer.insert(0, "sample_id", [f"WDBC-{i+1:03d}" for i in range(len(cancer))])
    cancer["diagnosis"] = cancer["diagnosis_target"].map({0: "malignant", 1: "benign"})

    dataset_summary = pd.DataFrame([
        {
            "dataset": "UCI Heart Disease four-site teaching table",
            "role": "primary",
            "observation_unit": "one historical patient record",
            "rows": len(heart),
            "feature_or_metadata_columns": 14,
            "target": "num 0-4; teaching binary view num>0",
            "target_distribution": "; ".join(f"{int(k)}:{int(v)}" for k, v in heart["num"].value_counts().sort_index().items()),
            "missing_cells": int(heart.drop(columns=["disease_binary"]).isna().sum().sum()),
            "source": "UCI Heart Disease DOI 10.24432/C52P4X",
            "license_note": "CC BY 4.0 recorded in course source metadata",
        },
        {
            "dataset": "Breast Cancer Wisconsin Diagnostic",
            "role": "supporting",
            "observation_unit": "one digitized FNA sample",
            "rows": len(cancer),
            "feature_or_metadata_columns": 30,
            "target": "diagnosis_target 0 malignant 1 benign",
            "target_distribution": f"malignant:{int((cancer['diagnosis_target']==0).sum())}; benign:{int((cancer['diagnosis_target']==1).sum())}",
            "missing_cells": int(cancer.isna().sum().sum()),
            "source": "UCI WDBC; bundled in scikit-learn",
            "license_note": "Attribution included; recheck current UCI terms before external redistribution",
        },
    ])
    save_csv(dataset_summary, "dataset-summary.csv")

    dictionary_rows = [
        ["record_id", "record identifier", "identifier", "nominal", "No", "do not treat as a numeric feature"],
        ["site", "data collection site", "provenance metadata", "nominal", "No", "stratify or audit site effects"],
        ["age", "age in years", "feature", "ratio continuous", "Usually", "median IQR correlation or model feature"],
        ["sex", "recorded sex code", "feature", "binary nominal", "No", "contingency table or encoded feature"],
        ["cp", "chest pain category", "feature", "nominal multiclass", "No", "counts chi-square or one-hot encoding"],
        ["trestbps", "resting blood pressure", "feature", "ratio continuous", "Usually", "distribution comparison or numeric feature"],
        ["chol", "serum cholesterol", "feature", "ratio continuous", "Usually", "distribution transform or numeric feature"],
        ["fbs", "fasting blood sugar threshold flag", "feature", "binary nominal", "No", "proportion or binary feature"],
        ["restecg", "resting ECG category", "feature", "nominal multiclass", "No", "counts or one-hot encoding"],
        ["thalach", "maximum heart rate", "feature", "ratio continuous", "Usually", "distribution comparison or numeric feature"],
        ["exang", "exercise-induced angina flag", "feature", "asymmetric binary", "No", "Jaccard may be meaningful for symptom presence"],
        ["oldpeak", "ST depression", "feature", "ratio continuous", "Usually", "robust summary transform or numeric feature"],
        ["slope", "slope category", "feature", "ordinal", "Not as raw category code", "ordered summary or explicit encoding"],
        ["ca", "number of major vessels", "feature", "discrete count", "With context", "count or categorical treatment"],
        ["thal", "thalassemia test category", "feature", "nominal", "No", "counts or one-hot encoding"],
        ["num", "angiographic disease status 0-4", "target", "ordinal outcome", "Not as ordinary continuous", "ordinal or binary task after justified definition"],
    ]
    data_dictionary = pd.DataFrame(dictionary_rows, columns=["variable", "working_meaning", "role", "measurement_scale", "standardize", "analysis_implication"])
    save_csv(data_dictionary, "packet-b-data-dictionary.csv")

    scale_cases = pd.DataFrame([
        ["collection_site", "A B C", "nominal", "different labels without order", "counts and stratification"],
        ["disease_stage", "I II III IV", "ordinal", "ordered but gaps are not assumed equal", "ordered summaries or ordinal model"],
        ["calendar_year", "2018 2019 2020", "interval", "differences are meaningful but year zero is arbitrary", "differences and trends not meaningful ratios"],
        ["age_years", "20 40 60", "ratio", "differences and a meaningful zero support ratios with context", "numeric summaries after distribution check"],
        ["mutation_count", "0 1 2 3", "discrete ratio", "counted integer events", "count distribution or justified transformation"],
        ["blood_pressure", "continuous measurement", "continuous ratio", "measured on a continuum within instrument resolution", "numeric summaries and scale-aware distance"],
    ], columns=["microcase_variable", "example_values", "measurement_scale", "reason", "analysis_consequence"])
    save_csv(scale_cases, "packet-b-measurement-scale-cases.csv")

    method_map = pd.DataFrame([
        ["continuous feature vs binary outcome", "distribution shape and independence", "median/IQR plus rank test; or logistic model", "association does not establish causation"],
        ["nominal feature vs categorical outcome", "expected cell counts and sampling design", "contingency table with chi-square or Fisher", "category codes have no distance"],
        ["ordinal outcome", "ordered meaning is defensible", "ordinal model or rank-based comparison", "spacing between levels is not assumed equal"],
        ["time-to-event outcome", "time origin censoring and follow-up are available", "survival analysis", "ordinary binary regression discards timing and censoring"],
        ["high-dimensional feature matrix", "sample size redundancy and validation design", "regularized model feature selection or PCA", "selection and tuning must remain inside training data"],
    ], columns=["question_and_variable_form", "check_before_choice", "candidate_method", "boundary"])
    save_csv(method_map, "packet-b-method-map.csv")

    structures = pd.DataFrame([
        ["record data", "patient × clinical variables", "one patient record", "row independence provenance and mixed scales"],
        ["matrix data", "sample × gene expression", "one biospecimen", "high dimension sparsity and batch structure"],
        ["document data", "clinical note × terms or embeddings", "one note", "tokenization frequency and note-to-patient linkage"],
        ["transaction data", "patient encounter × codes present", "one encounter set", "presence may matter more than joint absence"],
        ["graph data", "protein interaction network", "node or edge", "relationships violate an independent-row view"],
        ["ordered data", "longitudinal measurements or sequence", "time point within a subject", "order spacing and repeated-subject dependence"],
    ], columns=["structure", "biomedical_example", "object", "analysis_consequence"])
    save_csv(structures, "packet-b-structure-types.csv")

    cancer_features = cancer_bunch.data.copy()
    corr = cancer_features.corr().abs()
    upper = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool))
    correlated_pairs = int((upper > 0.9).sum().sum())
    characteristics = pd.DataFrame([
        ["Heart Disease", len(heart), 14, "mixed; moderately low-dimensional", "binary flags include many zeros", "patient-level; four historical sites", int(DATA_PATH.stat().st_size), "quality and mixed-type workflow"],
        ["WDBC", len(cancer), 30, "numeric; feature redundancy", f"exact zero fraction {float((cancer_features==0).mean().mean()):.3f}", "image-derived nucleus summaries", int(cancer_features.memory_usage(index=True, deep=True).sum()), f"PCA and feature selection; {correlated_pairs} pairs |r|>0.90"],
    ], columns=["dataset", "rows", "features", "dimensionality", "sparsity", "resolution", "approx_bytes", "implication"])
    save_csv(characteristics, "packet-b-data-characteristics.csv")

    missing = heart.drop(columns=["disease_binary"]).isna().sum().sort_values(ascending=False)
    quality_rows = []
    continuous = ["age", "trestbps", "chol", "thalach", "oldpeak"]
    for col in heart.drop(columns=["disease_binary"]).columns:
        miss = int(heart[col].isna().sum())
        outliers = "not assessed"
        if col in continuous:
            s = heart[col].dropna()
            q1, q3 = s.quantile([0.25, 0.75])
            iqr = q3 - q1
            outliers = int(((s < q1 - 1.5 * iqr) | (s > q3 + 1.5 * iqr)).sum())
        quality_rows.append([col, miss, round(100 * miss / len(heart), 1), outliers, "review by site and source semantics" if miss else "check range and coding"])
    quality_rows.append(["duplicate feature rows", 0, 0.0, int(heart.drop(columns=["record_id", "disease_binary"]).duplicated().sum()), "do not delete until record linkage is checked"])
    quality_audit = pd.DataFrame(quality_rows, columns=["item", "missing_n", "missing_pct", "iqr_outlier_or_duplicate_n", "interpretation_action"])
    for col in ["trestbps", "chol", "thalach"]:
        zero_n = int((heart[col] == 0).sum())
        if zero_n:
            quality_audit.loc[len(quality_audit)] = [f"{col} recorded as zero", 0, 0.0, zero_n, "verify whether zero is an impossible value or missing-value sentinel before transformation"]
    save_csv(quality_audit, "packet-b-quality-audit.csv")
    quality_boundaries = pd.DataFrame([
        ["explicit missing value", "NA counts and site pattern", "missing mechanism and collection reason", "obtain codebook and collection metadata before imputation"],
        ["implausible recorded zero", "chol trestbps or thalach equals zero", "whether zero means not measured device limit or entry error", "recode only after source verification"],
        ["outlier", "IQR or robust distribution flag", "error versus genuine extreme patient", "inspect source and sensitivity; do not delete automatically"],
        ["batch or site effect", "distribution or missingness differs by site", "biological population equipment or workflow cause", "retain provenance and analyze by source"],
        ["measurement noise", "unexpected spread or disagreement", "instrument and repeatability process", "request replicate calibration or QC information"],
        ["duplicate", "identical rows or identifiers", "repeated visit true duplicate or linked sample", "resolve observation unit and linkage before removal"],
        ["class imbalance", "target distribution", "decision prevalence and sampling frame", "choose sampling and evaluation consistent with the question"],
    ], columns=["quality_issue", "observable_signal", "not_identified_by_table_alone", "next_action"])
    save_csv(quality_boundaries, "packet-b-quality-evidence-boundaries.csv")
    miss_site = heart.groupby("site")[numeric_cols].apply(lambda x: x.isna().mean() * 100).round(1)
    miss_site.reset_index().to_csv(ASSET_DIR / "packet-b-missingness-by-site.csv", index=False, encoding="utf-8-sig")
    target_site = pd.crosstab(heart["site"], heart["num"], normalize="index").mul(100).round(1).reset_index()
    target_site.columns = ["site"] + [f"num_{int(c)}_pct" for c in target_site.columns[1:]]
    target_site["disease_binary_pct"] = heart.groupby("site")["disease_binary"].mean().reindex(target_site["site"]).to_numpy() * 100
    save_csv(target_site.round(1), "packet-b-target-by-site.csv")

    fig, ax = plt.subplots(figsize=(11, 5.4))
    plot_cols = [c for c in numeric_cols if heart[c].isna().any()]
    im = ax.imshow(miss_site[plot_cols].to_numpy(), aspect="auto", cmap="Blues", vmin=0, vmax=100)
    ax.set_xticks(range(len(plot_cols)), plot_cols, rotation=45, ha="right")
    ax.set_yticks(range(len(miss_site.index)), miss_site.index)
    ax.set_title("Missingness differs across collection sites")
    ax.set_xlabel("Variable")
    ax.set_ylabel("Site")
    for i in range(len(miss_site.index)):
        for j in range(len(plot_cols)):
            ax.text(j, i, f"{miss_site.iloc[i][plot_cols[j]]:.0f}%", ha="center", va="center", fontsize=8, color="black")
    fig.colorbar(im, ax=ax, label="Missing percent")
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "packet-b-missingness.png", dpi=180)
    plt.close(fig)

    dist_cols = ["age", "trestbps", "chol", "thalach", "oldpeak"]
    x = heart[dist_cols].copy()
    x = x.fillna(x.median())
    raw = x.to_numpy()
    scaled = StandardScaler().fit_transform(raw)
    d_raw_e = pairwise_distances(raw, metric="euclidean")
    d_scaled_e = pairwise_distances(scaled, metric="euclidean")
    d_scaled_m = pairwise_distances(scaled, metric="manhattan")
    d_scaled_p3 = pairwise_distances(scaled, metric="minkowski", p=3)
    covariance_inverse = np.linalg.pinv(np.cov(scaled, rowvar=False))
    d_scaled_mahal = pairwise_distances(scaled, metric="mahalanobis", VI=covariance_inverse)
    anchor = 0
    ranking_rows = []
    for label, matrix in (("Euclidean raw", d_raw_e), ("Euclidean standardized", d_scaled_e), ("Manhattan standardized", d_scaled_m)):
        order = np.argsort(matrix[anchor])[1:7]
        for rank, idx in enumerate(order, 1):
            ranking_rows.append([heart.loc[anchor, "record_id"], label, rank, heart.loc[idx, "record_id"], heart.loc[idx, "site"], round(float(matrix[anchor, idx]), 3)])
    neighbor_ranking = pd.DataFrame(ranking_rows, columns=["anchor", "metric_preprocessing", "rank", "neighbor", "neighbor_site", "distance"])
    save_csv(neighbor_ranking, "packet-c-neighbor-ranking.csv")

    metric_candidates = np.unique(np.concatenate([np.argsort(d_scaled_e[anchor])[1:5], np.argsort(d_scaled_m[anchor])[1:5], np.argsort(d_scaled_mahal[anchor])[1:5]]))
    metric_comparison = pd.DataFrame({
        "candidate": heart.loc[metric_candidates, "record_id"].to_numpy(),
        "Euclidean_standardized": d_scaled_e[anchor, metric_candidates].round(3),
        "Manhattan_standardized": d_scaled_m[anchor, metric_candidates].round(3),
        "Minkowski_p3_standardized": d_scaled_p3[anchor, metric_candidates].round(3),
        "Mahalanobis_covariance_adjusted": d_scaled_mahal[anchor, metric_candidates].round(3),
    })
    metric_comparison["interpretation_check"] = "rank may change; Mahalanobis also depends on covariance estimation"
    save_csv(metric_comparison, "packet-c-metric-comparison.csv")

    comparison_ids = np.unique(np.concatenate([np.argsort(d_raw_e[anchor])[1:6], np.argsort(d_scaled_e[anchor])[1:6]]))
    dist_plot = pd.DataFrame({
        "record_id": heart.loc[comparison_ids, "record_id"].to_numpy(),
        "raw_euclidean_relative": d_raw_e[anchor, comparison_ids] / d_raw_e[anchor, comparison_ids].max(),
        "standardized_euclidean_relative": d_scaled_e[anchor, comparison_ids] / d_scaled_e[anchor, comparison_ids].max(),
    }).sort_values("standardized_euclidean_relative")
    fig, ax = plt.subplots(figsize=(11, 5.2))
    y_pos = np.arange(len(dist_plot))
    ax.plot(dist_plot["raw_euclidean_relative"], y_pos, "o-", label="Raw scale")
    ax.plot(dist_plot["standardized_euclidean_relative"], y_pos, "s-", label="Standardized")
    ax.set_yticks(y_pos, dist_plot["record_id"])
    ax.set_xlabel("Relative distance within displayed candidates")
    ax.set_title("Scaling changes Euclidean distance and neighbor order")
    ax.legend()
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "packet-c-distance-sensitivity.png", dpi=180)
    plt.close(fig)

    base = StandardScaler().fit_transform(cancer_features.iloc[:80, :10])[0]
    vectors = {"same": base, "scaled_x2": base * 2, "shifted_plus2": base + 2, "reversed": base[::-1]}
    vector_rows = []
    for name, vec in vectors.items():
        eu = float(np.linalg.norm(base - vec))
        man = float(np.abs(base - vec).sum())
        cos = float(np.dot(base, vec) / (np.linalg.norm(base) * np.linalg.norm(vec))) if np.linalg.norm(vec) else math.nan
        cor = float(np.corrcoef(base, vec)[0, 1])
        vector_rows.append([name, round(eu, 3), round(man, 3), round(cos, 3), round(cor, 3), "correlation ignores positive scaling and translation" if name in ["scaled_x2", "shifted_plus2"] else "comparison"])
    vector_metrics = pd.DataFrame(vector_rows, columns=["transformation", "euclidean", "manhattan", "cosine_similarity", "correlation", "interpretation"])
    save_csv(vector_metrics, "packet-c-vector-metrics.csv")

    mi_frame = heart[["age", "chol", "cp", "exang", "disease_binary"]].copy()
    mi_frame["age_bin"] = pd.qcut(mi_frame["age"], q=5, duplicates="drop").cat.codes
    mi_frame["chol_bin"] = pd.qcut(mi_frame["chol"], q=5, duplicates="drop").cat.codes
    mi_x = mi_frame[["age_bin", "chol_bin", "cp", "exang"]].fillna(-1).astype(int)
    mi = mutual_info_classif(mi_x, mi_frame["disease_binary"], discrete_features=True, random_state=42)
    info_measures = pd.DataFrame({
        "measure": ["target_entropy_bits"] + [f"mutual_information_{c}" for c in mi_x.columns],
        "value": [round(entropy(mi_frame["disease_binary"]), 4)] + [round(float(v), 4) for v in mi],
        "meaning": ["uncertainty in the binary teaching outcome"] + ["observed dependence; not causal importance" for _ in mi],
    })
    save_csv(info_measures, "packet-c-information-measures.csv")

    binary = heart[["record_id", "sex", "fbs", "exang"]].dropna().head(120).reset_index(drop=True)
    binary_rows = []
    pairs = [(0, 1), (0, 5), (2, 12), (10, 40)]
    for i, j in pairs:
        av = binary.loc[i, ["sex", "fbs", "exang"]].astype(int).to_numpy()
        bv = binary.loc[j, ["sex", "fbs", "exang"]].astype(int).to_numpy()
        matches = int((av == bv).sum())
        union = int(((av == 1) | (bv == 1)).sum())
        intersection = int(((av == 1) & (bv == 1)).sum())
        joint_zero = int(((av == 0) & (bv == 0)).sum())
        smc = matches / len(av)
        jac = intersection / union if union else math.nan
        binary_rows.append([binary.loc[i, "record_id"], binary.loc[j, "record_id"], str(av.tolist()), str(bv.tolist()), joint_zero, round(smc, 3), None if math.isnan(jac) else round(jac, 3)])
    binary_similarity = pd.DataFrame(binary_rows, columns=["record_a", "record_b", "a_sex_fbs_exang", "b_sex_fbs_exang", "joint_zero_count", "SMC", "Jaccard"])
    save_csv(binary_similarity, "packet-c-binary-similarity.csv")

    anchors = []
    for site in heart["site"].unique():
        row = heart.loc[heart["site"] == site].sort_values("record_id").iloc[0]
        anchors.append(row)
    a = anchors[0]
    mixed_rows = []
    for b in anchors[1:] + [heart.iloc[100], heart.iloc[500]]:
        distance, used, parts = gower_like_distance(a, b, heart)
        mixed_rows.append([a["record_id"], b["record_id"], b["site"], round(distance, 3), used, parts, "missing dimensions excluded rather than treated as matches"])
    mixed_similarity = pd.DataFrame(mixed_rows, columns=["anchor", "candidate", "site", "mixed_distance", "dimensions_used", "component_distances", "missing_rule"])
    save_csv(mixed_similarity, "packet-c-mixed-similarity.csv")

    rng = np.random.default_rng(20260909)
    population_site = heart["site"].value_counts(normalize=True)
    population_prev = heart["disease_binary"].mean()
    sampling_rows = []
    n_sample = 120
    sites = population_site.index.tolist()
    allocations = {s: int(round(n_sample * population_site[s])) for s in sites}
    allocations[sites[0]] += n_sample - sum(allocations.values())
    for rep in range(250):
        idx_srs = rng.choice(heart.index.to_numpy(), size=n_sample, replace=False)
        idx_strat = []
        for site in sites:
            pool = heart.index[heart["site"] == site].to_numpy()
            idx_strat.extend(rng.choice(pool, size=allocations[site], replace=False).tolist())
        for method, idx in (("simple_random", idx_srs), ("site_stratified", np.array(idx_strat))):
            sample = heart.loc[idx]
            sample_site = sample["site"].value_counts(normalize=True).reindex(sites, fill_value=0)
            max_site_error = float((sample_site - population_site.reindex(sites)).abs().max())
            prev = float(sample["disease_binary"].mean())
            sampling_rows.append([rep + 1, method, round(max_site_error, 4), round(prev, 4), round(abs(prev - population_prev), 4)])
    sampling = pd.DataFrame(sampling_rows, columns=["replicate", "method", "max_site_proportion_error", "disease_prevalence", "disease_prevalence_abs_error"])
    save_csv(sampling, "packet-c-sampling-replicates.csv")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    for ax, col, title in zip(axes, ["max_site_proportion_error", "disease_prevalence_abs_error"], ["Site composition error", "Outcome prevalence error"]):
        groups = [sampling.loc[sampling["method"] == m, col] for m in ["simple_random", "site_stratified"]]
        ax.boxplot(groups, tick_labels=["Simple random", "Site-stratified"], patch_artist=True, boxprops={"facecolor": "#DCEAF5"})
        ax.set_title(title)
        ax.set_ylabel("Absolute error")
    fig.suptitle("Repeated sampling shows what stratification protects")
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "packet-c-sampling-sensitivity.png", dpi=180)
    plt.close(fig)

    aggregation = heart.groupby("site").agg(
        patient_n=("record_id", "count"),
        age_mean=("age", "mean"), age_sd=("age", "std"),
        chol_mean=("chol", "mean"), chol_sd=("chol", "std"),
        disease_prevalence=("disease_binary", "mean"),
    ).reset_index().round(3)
    aggregation["aggregation_consequence"] = "one site row hides patient variation and reduces 920 records to 4"
    save_csv(aggregation, "packet-c-aggregation.csv")

    transform_rows = []
    for col in ["chol", "oldpeak", "trestbps"]:
        s = heart[col].dropna()
        transformed = np.log1p(s - min(0, s.min()))
        transform_rows.append([col, len(s), round(float(s.mean()), 3), round(float(s.median()), 3), round(float(s.skew()), 3), round(float(transformed.skew()), 3), "log1p is a candidate, not an automatic requirement"])
    age_clean = heart["age"].dropna()
    transform_rows.append(["age equal-width bins", len(age_clean), "5 bins", str(pd.cut(age_clean, bins=5).value_counts().sort_index().tolist()), "NA", "NA", "fixed widths can create uneven counts"])
    transform_rows.append(["age equal-frequency bins", len(age_clean), "5 bins", str(pd.qcut(age_clean, q=5, duplicates="drop").value_counts().sort_index().tolist()), "NA", "NA", "quantile cut points must be fitted on training data"])
    transform_summary = pd.DataFrame(transform_rows, columns=["variable_or_operation", "n", "raw_mean_or_setting", "raw_median_or_counts", "raw_skew", "transformed_skew", "interpretation"])
    save_csv(transform_summary, "packet-c-transformation-summary.csv")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    chol = heart["chol"].dropna()
    axes[0].hist(chol, bins=30, color="#2F6B9A", alpha=0.85)
    axes[0].set_title("Cholesterol on recorded scale")
    axes[0].set_xlabel("chol")
    axes[0].set_ylabel("Records")
    axes[1].hist(np.log1p(chol.clip(lower=0)), bins=30, color="#66A182", alpha=0.85)
    axes[1].set_title("log1p transformation")
    axes[1].set_xlabel("log1p(chol)")
    axes[1].set_ylabel("Records")
    fig.suptitle("Transformation changes distribution shape but not data provenance")
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "packet-c-transformations.png", dpi=180)
    plt.close(fig)

    split_frame = heart[["age", "trestbps", "chol", "thalach", "oldpeak", "disease_binary"]].copy()
    train, test = train_test_split(split_frame, test_size=0.30, random_state=42, stratify=split_frame["disease_binary"])
    train_x = train.drop(columns=["disease_binary"])
    test_x = test.drop(columns=["disease_binary"])
    global_median = split_frame.drop(columns=["disease_binary"]).median()
    train_median = train_x.median()
    global_scaler = StandardScaler().fit(split_frame.drop(columns=["disease_binary"]).fillna(global_median))
    train_scaler = StandardScaler().fit(train_x.fillna(train_median))
    global_test = global_scaler.transform(test_x.fillna(global_median))
    trainfit_test = train_scaler.transform(test_x.fillna(train_median))
    preprocessing_audit = pd.DataFrame([
        ["A", "impute and scale on all 920 records, then split", "uses future test distribution", "leakage", "reject"],
        ["B", "split first; fit imputation and scaling on training records; apply fixed parameters to test", "test records do not set parameters", "valid teaching workflow", "retain"],
        ["test standardized mean check", "global-fit vs train-fit", f"global age mean {global_test[:,0].mean():.3f}; train-fit age mean {trainfit_test[:,0].mean():.3f}", "a near-zero global test mean can be partly engineered by leakage", "interpret with split provenance"],
    ], columns=["workflow", "operation", "information_used", "diagnosis", "decision"])
    save_csv(preprocessing_audit, "packet-d-preprocessing-audit.csv")

    z = StandardScaler().fit_transform(cancer_features)
    pca = PCA().fit(z)
    cumulative = np.cumsum(pca.explained_variance_ratio_)
    pca_summary = pd.DataFrame({
        "component": np.arange(1, len(cumulative) + 1),
        "explained_variance_ratio": pca.explained_variance_ratio_.round(5),
        "cumulative_explained_variance": cumulative.round(5),
    })
    save_csv(pca_summary, "packet-c-pca-summary.csv")
    loading_rows = []
    for comp in range(3):
        order = np.argsort(np.abs(pca.components_[comp]))[::-1][:6]
        for rank, idx in enumerate(order, 1):
            loading_rows.append([f"PC{comp+1}", rank, cancer_features.columns[idx], round(float(pca.components_[comp, idx]), 4)])
    pca_loadings = pd.DataFrame(loading_rows, columns=["component", "absolute_loading_rank", "feature", "loading"])
    save_csv(pca_loadings, "packet-c-pca-loadings.csv")
    fig, ax1 = plt.subplots(figsize=(11, 5.2))
    ax1.bar(pca_summary["component"].head(20), pca_summary["explained_variance_ratio"].head(20), color="#7FA8C9", label="Per component")
    ax1.set_xlabel("Principal component")
    ax1.set_ylabel("Explained variance ratio")
    ax2 = ax1.twinx()
    ax2.plot(pca_summary["component"], pca_summary["cumulative_explained_variance"], color="#A23B3B", marker="o", markersize=3, label="Cumulative")
    ax2.axhline(0.9, color="#555555", linestyle="--", linewidth=1)
    ax2.set_ylim(0, 1.03)
    ax2.set_ylabel("Cumulative explained variance")
    ax1.set_title("WDBC PCA reduces correlated numeric features with information loss")
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "packet-c-pca.png", dpi=180)
    plt.close(fig)

    concentration_rows = []
    z150 = z[:150]
    for dim in [2, 5, 10, 20, 30]:
        d = pairwise_distances(z150[:, :dim], metric="euclidean")
        vals = d[np.triu_indices_from(d, k=1)]
        nearest = np.partition(d + np.eye(len(d)) * 1e9, 0, axis=1)[:, 0]
        farthest = d.max(axis=1)
        concentration_rows.append([dim, round(float(vals.mean()), 4), round(float(vals.std()), 4), round(float(vals.std()/vals.mean()), 4), round(float(np.mean(nearest/farthest)), 4)])
    concentration = pd.DataFrame(concentration_rows, columns=["dimensions_used", "mean_pairwise_distance", "sd_pairwise_distance", "coefficient_of_variation", "mean_nearest_to_farthest_ratio"])
    save_csv(concentration, "packet-c-distance-concentration.csv")

    feature_options = pd.DataFrame([
        ["PCA", "compress correlated numeric features", "components mix original meanings", "fit inside training data; inspect explained variance and loadings"],
        ["feature subset selection", "retain named original variables", "selection instability and optimistic bias", "perform selection inside resampling and check stability"],
        ["feature creation", "encode domain-relevant ratios trends or interactions", "can import assumptions or leakage", "document formula timing and source variables"],
        ["retain all features", "avoid premature information loss", "distance concentration overfitting and computation", "use regularization and validation when modeling"],
    ], columns=["option", "possible_benefit", "risk", "required_check"])
    save_csv(feature_options, "packet-c-feature-options.csv")

    workflow_decision = pd.DataFrame([
        [1, "define object question target and grouping", "Q1 Q2", "data dictionary and structure audit", "stop if observation unit or target cannot be defined"],
        [2, "audit provenance structure and quality", "Q3 Q4", "characteristics missingness outliers duplicates site evidence", "change design if missingness or site is entangled with outcome"],
        [3, "choose representation and similarity semantics", "Q5 Q6", "metric sensitivity and mixed-type comparison", "reject a metric dominated by scale or arbitrary codes"],
        [4, "set sampling aggregation and transformation", "Q7 Q8", "sampling and transformation sensitivity", "change if key subgroups disappear or information loss changes the question"],
        [5, "choose dimensionality strategy", "Q9", "PCA loadings and feature option comparison", "stop reduction if retained variance loses required interpretation"],
        [6, "split when generalization or fitted preprocessing is involved", "Q8 Q10", "preprocessing audit", "reject any parameter fitted with validation or test information"],
        [7, "document evidence uncertainty and boundary", "Q10", "final readiness memo", "do not claim clinical causal or deployment validity"],
    ], columns=["step", "workflow_action", "inquiry_questions", "required_evidence", "change_or_stop_condition"])
    save_csv(workflow_decision, "packet-d-workflow-decision.csv")
    boundaries = pd.DataFrame([
        ["descriptive", "describe patterns in the supplied historical records", "population prevalence or representativeness"],
        ["association", "identify observed relationships for teaching", "causal effects of measurements or interventions"],
        ["prediction", "illustrate preparation effects", "clinical utility safety calibration or external validity"],
        ["missingness", "locate missing values", "identify mechanism without collection knowledge"],
        ["site difference", "show source distributions differ", "attribute causes without source metadata"],
        ["PCA", "describe retained variance", "preserve clinical meaning or predictive signal"],
    ], columns=["boundary_area", "evidence_can_support", "evidence_cannot_support"])
    save_csv(boundaries, "packet-d-boundary-checklist.csv")

    fig, ax = plt.subplots(figsize=(13, 3.7))
    ax.axis("off")
    labels = ["1 Define\nobject and question", "2 Audit\nstructure and quality", "3 Choose\nrepresentation", "4 Fit preprocessing\non training data", "5 Verify\nand report boundaries"]
    xs = np.linspace(0.1, 0.9, len(labels))
    for i, (xpos, label) in enumerate(zip(xs, labels)):
        ax.text(xpos, 0.58, label, ha="center", va="center", fontsize=11, color="white", bbox=dict(boxstyle="round,pad=0.5", fc="#17365D", ec="#17365D"))
        if i < len(labels) - 1:
            ax.annotate("", xy=(xs[i+1]-0.09, 0.58), xytext=(xpos+0.09, 0.58), arrowprops=dict(arrowstyle="->", lw=2, color="#2F6B9A"))
    ax.text(0.5, 0.18, "At every step: record evidence, uncertainty, change conditions, and what cannot be concluded", ha="center", fontsize=11)
    ax.set_title("Auditable data-readiness workflow", fontsize=16, pad=12)
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "packet-d-preprocessing-workflow.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    return {
        "heart": heart,
        "cancer": cancer,
        "dataset_summary": dataset_summary,
        "data_dictionary": data_dictionary,
        "method_map": method_map,
        "scale_cases": scale_cases,
        "structures": structures,
        "characteristics": characteristics,
        "quality_audit": quality_audit,
        "quality_boundaries": quality_boundaries,
        "missing_by_site": miss_site.reset_index(),
        "target_site": target_site,
        "neighbor_ranking": neighbor_ranking,
        "metric_comparison": metric_comparison,
        "vector_metrics": vector_metrics,
        "info_measures": info_measures,
        "binary_similarity": binary_similarity,
        "mixed_similarity": mixed_similarity,
        "sampling": sampling,
        "aggregation": aggregation,
        "transform_summary": transform_summary,
        "preprocessing_audit": preprocessing_audit,
        "pca_summary": pca_summary,
        "pca_loadings": pca_loadings,
        "concentration": concentration,
        "feature_options": feature_options,
        "workflow_decision": workflow_decision,
        "boundaries": boundaries,
        "correlated_pairs": correlated_pairs,
    }


def df_rows(df: pd.DataFrame, columns: list[str] | None = None, limit: int | None = None) -> list[list[object]]:
    view = df if columns is None else df[columns]
    if limit is not None:
        view = view.head(limit)
    rows = []
    for row in view.itertuples(index=False, name=None):
        cleaned = []
        for value in row:
            if pd.isna(value):
                cleaned.append("")
            elif isinstance(value, float):
                cleaned.append(f"{value:.3f}".rstrip("0").rstrip("."))
            else:
                cleaned.append(value)
        rows.append(cleaned)
    return rows


def add_inquiry_map(doc: Document, concise: bool = False) -> None:
    concise_questions = {
        "Q1": "对象、变量角色与测量尺度是什么？",
        "Q2": "数据表示如何影响分析？",
        "Q3": "维度、稀疏性与规模有何限制？",
        "Q4": "如何审查数据质量与来源差异？",
        "Q5": "不同距离和相似度保留什么含义？",
        "Q6": "如何定义混合数据的相似性？",
        "Q7": "抽样与聚合改变了什么？",
        "Q8": "如何变换数据并防止泄漏？",
        "Q9": "何时降维，如何检查信息损失？",
        "Q10": "如何形成可审计的数据准备流程？",
    }
    concise_contributions = {
        "Q1": "限定语义允许的处理",
        "Q2": "确定结构与分析单位",
        "Q3": "决定表示或降维",
        "Q4": "形成修复或停止条件",
        "Q5": "定义有意义的相似",
        "Q6": "避免任意统一距离",
        "Q7": "说明代表性与损失",
        "Q8": "规定拟合数据与时点",
        "Q9": "权衡信息与可解释性",
        "Q10": "回答总问题与边界",
    }
    rows = []
    for q in QUESTIONS:
        objectives = " ".join(q["objective_ids"])
        contribution = q["contribution_to_synthesis"]
        question = q["question"]
        if concise:
            question = concise_questions[q["id"]]
            contribution = concise_contributions[q["id"]]
        rows.append([q["id"], question, objectives, contribution])
    add_table(doc, ["问题", "你要解决的问题", "目标", "对总答案的作用"], rows, [0.5, 3.45, 0.75, 2.5], 8.4)


def add_objective_table(doc: Document) -> None:
    q_by_lo = {lo_id: [] for lo_id, _, _ in LO}
    for q in QUESTIONS:
        for lo_id in q["objective_ids"]:
            q_by_lo[lo_id].append(q["id"])
    rows = [[lo_id, source, outcome, " ".join(q_by_lo[lo_id])] for lo_id, source, outcome in LO]
    add_table(doc, ["目标", "课程要求", "可观察学习成果", "问题"], rows, [0.5, 2.55, 3.25, 0.7], 8.2)


def add_packet_a(doc: Document, data: dict[str, object], worksheet: bool = False) -> None:
    add_heading(doc, "Packet A 问题和初始事实", 1)
    doc.add_paragraph("使用时点：完成初步判断和3W以后再查看本页。Packet A只帮助你界定任务，不替代你的初始答案。")
    doc.add_paragraph("总问题：一个研究团队获得多源生物医学数据后，应如何理解数据对象和变量、选择数据表示、审查数据质量、定义相似性，并完成抽样、变换和降维，使数据能够合理用于机器学习？哪些发现会要求修改或停止这一流程？")
    summary = data["dataset_summary"]
    add_table(doc, ["数据", "作用", "观察单位", "规模", "目标与缺失"], [
        ["Heart Disease", "主数据", "历史患者记录", "920 × 16", f"num 0–4；缺失单元 {int(summary.iloc[0]['missing_cells'])}"],
        ["WDBC", "辅助数据", "FNA图像样本", "569 × 30", "恶性212 良性357；无缺失"],
    ], [1.15, 0.75, 1.55, 0.85, 3.0], 8.8)
    add_heading(doc, "尚缺证据清单", 2)
    checks = [
        "□ 每一行和每一列真正代表什么",
        "□ 变量类型和测量尺度是否支持计划中的分析",
        "□ 缺失 异常 站点和测量问题是否改变结论",
        "□ 相似性的定义是否符合任务语义",
        "□ 抽样 聚合和变换是否损失关键群体或信息",
        "□ 降维和特征处理是否保留所需解释",
        "□ 所有拟合型预处理是否只使用训练数据",
        "□ 结论边界和停止条件是否明确",
    ]
    for item in checks:
        doc.add_paragraph(item)
    if worksheet:
        add_response_area(doc, "查看 Packet A 后，我对总问题的第一次修订", 3)


def add_packet_b(doc: Document, data: dict[str, object], worksheet: bool = False) -> None:
    add_heading(doc, "Packet B 数据语义 结构和质量", 1)
    doc.add_paragraph("对应 Q1–Q4。先观察事实，再解释可能原因；不要把缺失模式或站点差异直接解释成生物学机制。")
    add_heading(doc, "B1 变量语义样例", 2)
    dd = data["data_dictionary"]
    add_table(doc, ["变量", "角色", "尺度", "分析含义"], df_rows(dd, ["variable", "role", "measurement_scale", "analysis_implication"], 16), [0.8, 1.2, 1.35, 3.95], 8.2)
    add_heading(doc, "B1a 四种测量尺度微型案例", 2)
    sc = data["scale_cases"]
    add_table(doc, ["变量", "例值", "尺度", "理由", "分析后果"], df_rows(sc), [1.15, 1.25, 0.9, 2.0, 2.0], 8.0)
    add_heading(doc, "B2 数据结构案例", 2)
    st = data["structures"]
    add_table(doc, ["结构", "生物医学例子", "对象", "分析后果"], df_rows(st), [1.0, 2.0, 1.35, 3.0], 8.3)
    add_heading(doc, "B3 数据特征", 2)
    ch = data["characteristics"]
    add_table(doc, ["数据", "行", "特征", "维度与稀疏", "用途"], [[r[0], r[1], r[2], f"{r[3]}; {r[4]}", r[7]] for r in df_rows(ch)], [1.15, 0.5, 0.55, 2.8, 2.35], 8.3)
    add_heading(doc, "B4 质量审查", 2)
    qa = data["quality_audit"].sort_values("missing_n", ascending=False)
    add_table(doc, ["项目", "缺失", "缺失率", "异常或重复", "下一步"], df_rows(qa, ["item", "missing_n", "missing_pct", "iqr_outlier_or_duplicate_n", "interpretation_action"], 12), [1.1, 0.65, 0.75, 0.95, 3.05], 8.2)
    qb = data["quality_boundaries"]
    add_table(doc, ["质量问题", "可观察信号", "表格不能单独识别", "下一步"], df_rows(qb), [1.2, 2.0, 2.15, 2.0], 8.0)
    add_picture(doc, ASSET_DIR / "packet-b-missingness.png", 6.8 if worksheet else 8.8, "图 B1 站点间缺失比例 对应 Q4 LO4 LO6")
    ts = data["target_site"]
    add_table(doc, list(ts.columns), df_rows(ts), [1.1] + [0.85] * (len(ts.columns)-1), 7.9)
    doc.add_paragraph("审查提示：哪些是直接观察到的事实？哪些只是关于仪器、临床流程或人群差异的假设？需要什么来源信息才能区分？")
    if worksheet:
        add_response_area(doc, "Packet B 使我如何修改 Q1–Q4 的答案和总工作流", 4)


def add_packet_c(doc: Document, data: dict[str, object], worksheet: bool = False) -> None:
    add_heading(doc, "Packet C 相似性 抽样 变换和降维", 1)
    doc.add_paragraph("对应 Q3、Q5–Q9。每项结果都用于比较方案；数值变化本身不等于方案更好。")
    add_heading(doc, "C1 尺度改变近邻", 2)
    nr = data["neighbor_ranking"]
    add_table(doc, ["预处理和度量", "名次", "邻居", "站点", "距离"], df_rows(nr, ["metric_preprocessing", "rank", "neighbor", "neighbor_site", "distance"], 18), [1.8, 0.55, 1.35, 1.25, 0.8], 8.3)
    add_picture(doc, ASSET_DIR / "packet-c-distance-sensitivity.png", 6.8 if worksheet else 8.8, "图 C1 缩放改变距离和近邻顺序 对应 Q5 LO7")
    add_heading(doc, "C2 Minkowski Mahalanobis 向量和信息度量", 2)
    mc = data["metric_comparison"]
    add_table(doc, ["候选", "Euclidean", "Manhattan", "Minkowski p3", "Mahalanobis", "检查"], df_rows(mc, ["candidate", "Euclidean_standardized", "Manhattan_standardized", "Minkowski_p3_standardized", "Mahalanobis_covariance_adjusted", "interpretation_check"]), [1.25, 0.75, 0.75, 0.8, 0.9, 2.6], 7.9)
    vm = data["vector_metrics"]
    add_table(doc, ["变换", "Euclidean", "Manhattan", "Cosine", "Correlation", "解释"], df_rows(vm), [1.25, 0.75, 0.75, 0.7, 0.85, 2.35], 8.1)
    im = data["info_measures"]
    add_table(doc, ["信息量", "值", "工作含义"], df_rows(im), [2.2, 0.8, 4.0], 8.5)
    add_heading(doc, "C3 二值和混合型相似性", 2)
    bs = data["binary_similarity"]
    add_table(doc, ["记录A", "记录B", "共同0", "SMC", "Jaccard"], df_rows(bs, ["record_a", "record_b", "joint_zero_count", "SMC", "Jaccard"]), [1.35, 1.35, 0.8, 0.8, 0.8], 8.5)
    ms = data["mixed_similarity"]
    add_table(doc, ["候选", "站点", "混合距离", "使用维度", "分项距离"], df_rows(ms, ["candidate", "site", "mixed_distance", "dimensions_used", "component_distances"]), [1.35, 1.2, 0.9, 0.8, 3.1], 8.1)
    add_heading(doc, "C4 抽样和聚合", 2)
    sampling = data["sampling"]
    samp_summary = sampling.groupby("method")[["max_site_proportion_error", "disease_prevalence_abs_error"]].agg(["mean", "std", "max"]).round(4)
    samp_summary.columns = ["_".join(c) for c in samp_summary.columns]
    add_table(doc, ["方法"] + list(samp_summary.columns), [[idx] + row.tolist() for idx, row in samp_summary.iterrows()], [1.25] + [0.95] * len(samp_summary.columns), 7.8)
    add_picture(doc, ASSET_DIR / "packet-c-sampling-sensitivity.png", 6.8 if worksheet else 8.8, "图 C2 分层抽样保护站点构成但不能保证所有统计量 对应 Q7 LO8")
    ag = data["aggregation"]
    add_table(doc, ["站点", "人数", "年龄均值", "年龄SD", "患病比例", "聚合后果"], df_rows(ag, ["site", "patient_n", "age_mean", "age_sd", "disease_prevalence", "aggregation_consequence"]), [1.15, 0.65, 0.8, 0.75, 0.85, 3.0], 8.1)
    add_heading(doc, "C5 变换和标准化", 2)
    doc.add_paragraph("注意：chol、trestbps或thalach中记录为0的值可能是异常值或缺失哨兵。必须先核对来源定义，不能用log变换把编码问题变成看似正常的数值。")
    tr = data["transform_summary"]
    add_table(doc, ["变量或操作", "样本", "原始设置", "原始偏度或计数", "变换后偏度", "解释"], df_rows(tr, ["variable_or_operation", "n", "raw_mean_or_setting", "raw_skew", "transformed_skew", "interpretation"]), [1.3, 0.55, 1.0, 1.1, 1.0, 2.35], 8.0)
    add_picture(doc, ASSET_DIR / "packet-c-transformations.png", 6.8 if worksheet else 8.8, "图 C3 变换改变分布形状但不会修复来源问题 对应 Q8 LO5 LO8")
    add_heading(doc, "C6 维度灾难 PCA和特征处理", 2)
    con = data["concentration"]
    add_table(doc, ["维度", "平均距离", "距离SD", "变异系数", "平均最近 最远比"], df_rows(con), [0.75, 1.0, 0.9, 0.9, 1.2], 8.5)
    pca_summary = data["pca_summary"]
    n90 = int(pca_summary.loc[pca_summary["cumulative_explained_variance"] >= 0.90, "component"].iloc[0])
    n95 = int(pca_summary.loc[pca_summary["cumulative_explained_variance"] >= 0.95, "component"].iloc[0])
    doc.add_paragraph(f"WDBC 的30个标准化特征中，累计解释方差达到90%需要 {n90} 个主成分，达到95%需要 {n95} 个。该数字只说明方差，不保证保留医学语义或任务信号。")
    add_picture(doc, ASSET_DIR / "packet-c-pca.png", 6.8 if worksheet else 8.8, "图 C4 PCA解释方差及累计信息 对应 Q9 LO2 LO8")
    fo = data["feature_options"]
    add_table(doc, ["方案", "可能收益", "风险", "必须检查"], df_rows(fo), [1.25, 1.8, 1.8, 2.45], 8.2)
    if worksheet:
        add_response_area(doc, "Packet C 使我如何修改 Q3 Q5–Q9 和总工作流", 5)


def add_packet_d(doc: Document, data: dict[str, object], worksheet: bool = False) -> None:
    add_heading(doc, "Packet D 综合工作流和边界", 1)
    doc.add_paragraph("对应 Q8 和 Q10。Packet D不是答案键；你需要判断这些步骤是否足以解决本案例，并用前面证据说明理由。")
    add_picture(doc, ASSET_DIR / "packet-d-preprocessing-workflow.png", 6.8 if worksheet else 8.55, "图 D1 可审计的数据准备路径 对应 Q10 LO3 LO5 LO6")
    wd = data["workflow_decision"]
    add_table(doc, ["步", "行动", "问题", "证据", "修改或停止条件"], df_rows(wd), [0.45, 1.65, 0.8, 2.0, 2.45], 8.0)
    pa = data["preprocessing_audit"]
    add_heading(doc, "预处理泄漏审查", 2)
    add_table(doc, ["流程", "操作", "使用的信息", "诊断", "决定"], df_rows(pa), [0.65, 2.2, 1.75, 1.85, 0.75], 8.0)
    bd = data["boundaries"]
    add_heading(doc, "结论边界", 2)
    add_table(doc, ["领域", "证据可以支持", "证据不能支持"], df_rows(bd), [1.05, 3.0, 3.25], 8.3 if worksheet else 8.0, compact_after=not worksheet)
    if worksheet:
        add_response_area(doc, "Packet D 后我的最终 Data readiness plan 还必须补充或修改什么", 4)


def build_student_worksheet(data: dict[str, object]) -> Path:
    path = ROOT / f"pbl-{SLUG}-student-worksheet.docx"
    doc = setup_doc("理解数据与机器学习准备", "Problem Based Learning Student Worksheet")
    doc.add_paragraph("你将从一个不完整的初步判断出发，通过自主学习和数据证据，形成一份能够说明如何处理数据、为何这样处理、何时必须修改或停止的 Data readiness plan。请独立完成全部记录，并准备在翻转课堂中被随机抽取进行白板说明。")

    add_heading(doc, "案例信息", 1)
    add_table(doc, ["项目", "内容"], [
        ["主数据", "UCI Heart Disease 四中心历史记录 920 × 16"],
        ["辅助数据", "WDBC 569 × 30 仅用于高维 PCA 和特征处理"],
        ["总问题", "多源生物医学数据需要如何理解 审查 表示 抽样 变换和降维 才能用于机器学习"],
        ["最终产出", "个人 Data readiness plan 包括主张 证据 推理 不确定性 边界和停止条件"],
    ], [1.2, 5.9], 9.0)
    add_heading(doc, "三阶段学习路线", 1)
    add_table(doc, ["阶段", "时间", "你要做什么", "留下的证据"], [
        ["第一阶段 课堂启动", "45分钟", "先判断 再澄清问题 完成3W和行动计划", "初步工作流 知识缺口 学习计划"],
        ["第二阶段 课外自学", "90至120分钟", "学习背景知识 分析Packet证据 完成Q1至Q10", "来源记录 分析结果 总答案的连续修订"],
        ["第三阶段 翻转课堂", "45分钟", "准备随机白板 talk 提问 修订", "最终工作流和反思"],
    ], [1.35, 0.9, 3.2, 2.0], 8.7)
    doc.add_page_break()
    add_heading(doc, "探究问题地图", 1)
    add_inquiry_map(doc, concise=False)

    doc.add_page_break()
    add_heading(doc, "第一阶段 课堂启动 45分钟", 1)
    add_table(doc, ["时间", "任务", "个人行动", "课堂证据"], [
        ["0至5", "问题触发", "阅读总问题和两套数据的初始事实 不查资料", "标记最不确定的三处"],
        ["5至11", "初步答案", "画出你目前认为合理的数据准备顺序", "初步工作流和理由"],
        ["11至18", "澄清定义", "圈出对象 属性 尺度 相似 代表性 降维等需要定义的词", "工作定义"],
        ["18至25", "阅读导航", "把Q1至Q10分配到课程材料的概念群", "阅读和检索路线"],
        ["25至35", "完成3W", "按概念群填写已知 未知 下一步", "3W表"],
        ["35至41", "学习计划", "选择资源 分析动作 完成标准", "个人学习合同"],
        ["41至45", "退出条", "写下当前判断 最大风险和下一步", "课堂退出条"],
    ], [0.7, 1.05, 3.55, 1.65], 8.5)
    add_heading(doc, "问题触发和初步判断", 2)
    doc.add_paragraph("研究团队希望把四个中心的心脏病历史记录用于机器学习，同时希望把同一套思路迁移到一个30维图像特征数据集。团队尚未确定变量尺度、缺失原因、站点差异、相似性定义、抽样方案、变换顺序和降维策略。你需要先提出方案，再用证据修订。")
    add_response_area(doc, "我的初步数据准备顺序和理由", 5)
    add_response_area(doc, "我认为可能迫使团队修改或停止的发现", 3)
    add_heading(doc, "需要澄清的术语和问题", 2)
    add_table(doc, ["术语或问题", "我的暂定含义", "需要向数据团队 教材或AI追问什么", "对应Q"], [["", "", "", ""] for _ in range(6)], [1.45, 1.8, 3.15, 0.55], 8.7)

    doc.add_page_break()
    add_heading(doc, "参考阅读导航", 1)
    reading_rows = [
        ["Q1 Q2", "对象 属性 变量角色 测量尺度 数据结构", "课程PPT属性与数据类型部分 教材数据表示章节"],
        ["Q3 Q9", "维度 稀疏 分辨率 维度灾难 PCA 特征处理", "课程PPT数据特征与降维部分 sklearn PCA文档"],
        ["Q4", "缺失 噪声 异常 重复 批次 测量误差", "课程PPT数据质量部分 数据来源说明"],
        ["Q5 Q6", "距离 相似 相关 信息度量 混合类型", "课程PPT相似性与距离部分 可靠统计教材"],
        ["Q7 Q8", "抽样 聚合 离散 编码 变换 标准化 泄漏", "课程PPT预处理部分 课程data.md"],
        ["Q10", "证据综合 方法边界 可复现流程", "本worksheet Packet D和教材报告规范"],
    ]
    add_table(doc, ["问题", "必学概念", "建议资源类型"], reading_rows, [0.9, 3.2, 3.05], 8.7)
    doc.add_paragraph("大模型使用规则：可以请大模型解释、生成比较例子或检查逻辑，但必须记录提示词和回答要点；至少用课程材料、教材、官方文档或数据证据核验一个关键说法。最终判断必须由你重写并负责。")
    add_heading(doc, "3W 知识缺口", 1)
    add_table(doc, ["概念群", "What do I know 已知", "What do I not know 未知", "What will I do next 下一步"], [[c["name"], "", "", ""] for c in CONCEPTS], [1.3, 1.9, 1.9, 2.1], 8.5)
    add_heading(doc, "个人学习计划和证据卡", 1)
    add_table(doc, ["要解决的问题", "资源和来源", "分析动作", "完成标准"], [["", "", "", ""] for _ in range(5)], [1.6, 2.0, 2.2, 1.4], 8.7)
    add_table(doc, ["证据卡字段", "个人记录"], [
        ["需要核验的教材 资料或AI说法", ""],
        ["对应Q和LO", ""],
        ["核验来源及可追溯信息", ""],
        ["数据或方法证据", ""],
        ["核验结论和仍有的不确定性", ""],
    ], [2.1, 5.1], 8.8)
    add_response_area(doc, "第一阶段退出条 当前判断 最大风险 下一步", 3)

    doc.add_page_break()
    add_heading(doc, "第二阶段 课外自主学习", 1)
    doc.add_paragraph("按Q1至Q10推进。每完成一个模块，都必须更新总答案；不要等到最后再拼接十份互不相关的答案。Packet A至D的实际证据位于后半部分，请按模块说明逐步查看。")
    for q in QUESTIONS:
        add_heading(doc, f"{q['id']} {q['question']}", 2)
        add_table(doc, ["本模块要学习", "使用的证据", "必须完成的分析", "个人产出"], [[
            "；".join(q["required_learning"]),
            "；".join(q["evidence_needed"]),
            q["student_action"],
            q["student_output"],
        ]], [1.75, 2.0, 2.35, 1.2], 8.2)
        doc.add_paragraph("建议资源：课程PPT与 data.md；相关教材；数据来源说明；必要时使用大模型解释，并按证据卡规则核验。")
        add_response_area(doc, "证据观察和分析结果", 2)
        add_response_area(doc, "暂定结论 仍不确定什么", 2)
        add_response_area(doc, "本模块如何修改总 Data readiness plan", 2)
        if q["id"] in ["Q2", "Q4", "Q6", "Q8"]:
            doc.add_page_break()

    doc.add_page_break()
    add_heading(doc, "学生证据页和分阶段使用说明", 1)
    doc.add_paragraph("本worksheet包含全部证据，便于课外独立完成。请遵守顺序：先提交课堂初步判断和3W，再查看A；完成Q1至Q4后查看B；完成初步度量和预处理方案后查看C；最后查看D。")
    add_packet_a(doc, data, worksheet=True)
    doc.add_page_break()
    add_packet_b(doc, data, worksheet=True)
    doc.add_page_break()
    add_packet_c(doc, data, worksheet=True)
    doc.add_page_break()
    add_packet_d(doc, data, worksheet=True)

    doc.add_page_break()
    add_heading(doc, "综合决策矩阵", 1)
    add_table(doc, ["选择或步骤", "理由或假设", "预期证据", "验证检查", "停止条件", "对应Q"], [["", "", "", "", "", ""] for _ in range(8)], [1.05, 1.45, 1.35, 1.35, 1.45, 0.55], 8.1)
    add_heading(doc, "初始与最终综合", 1)
    add_table(doc, ["要素", "课堂初始版本", "证据后的最终版本"], [
        ["Claim 建议的工作流", "", ""],
        ["Evidence 使用的关键证据", "", ""],
        ["Reasoning 为什么证据支持选择", "", ""],
        ["Uncertainty 仍未知什么", "", ""],
        ["Boundary 不能得出什么", "", ""],
        ["Stop conditions 何时修改或停止", "", ""],
    ], [1.6, 2.75, 2.75], 8.6)
    add_response_area(doc, "最终 Data readiness plan 必须明确引用 Q1至Q10", 7)

    add_heading(doc, "迁移任务", 1)
    doc.add_paragraph("选择一个新的小型公开生物医学数据情境，使用同一框架回答：对象和变量是什么；结构和质量允许什么；相似性如何定义；抽样、变换和降维如何选择；哪些结论不能支持。提交1至2页个人审查报告，并注明来源与许可。")
    add_heading(doc, "第三阶段 翻转课堂准备", 1)
    doc.add_paragraph("课堂将随机抽取一至两名学生进行白板 talk。你不需要背诵固定模板，但必须能说明：你最初怎样判断；通过哪些资源和分析学习；哪项证据改变了判断；最终工作流和停止条件是什么。所有学生都要独立完成worksheet并准备回答同伴和教师追问。")
    add_table(doc, ["自检", "完成"], [
        ["我能不用看答案解释 Q1至Q10 如何共同支持总答案", "□"],
        ["我保存了资料来源 分析依据和AI核验记录", "□"],
        ["我能指出至少两次答案修订及原因", "□"],
        ["我能解释一个有争议的度量或预处理选择", "□"],
        ["我能清楚说出证据不能支持的结论", "□"],
    ], [6.35, 0.75], 9.0)
    add_response_area(doc, "翻转课堂后修订和退出条 哪项证据改变了我的概念理解", 4)
    finalize_doc(doc, path)
    return path


def build_evidence_pack(data: dict[str, object]) -> Path:
    path = ROOT / f"pbl-{SLUG}-evidence-pack.docx"
    doc = setup_doc("理解数据与机器学习准备", "Packet A to D Evidence Pack", landscape=True)
    doc.add_paragraph("教师按A至D逐步发布。每个Packet之后，学生都要回答：现在可以得出什么、不能得出什么、如何修改当前工作流、什么证据会改变决定。")
    add_inquiry_map(doc, concise=True)
    add_packet_a(doc, data)
    add_packet_b(doc, data)
    add_packet_c(doc, data)
    add_packet_d(doc, data)
    finalize_doc(doc, path)
    return path


def build_teacher_plan(data: dict[str, object]) -> Path:
    path = ROOT / f"pbl-{SLUG}-teaching-plan-flipped-classroom.docx"
    doc = setup_doc("理解数据与机器学习准备", "PBL and Flipped Classroom Teacher Plan")
    doc.add_paragraph("本教学方案用一个开放的数据准备问题统领全章。教师提供问题、材料、证据和必要支架，不在学生形成初步判断和知识缺口之前直接给出答案。")
    add_heading(doc, "课程概览", 1)
    add_table(doc, ["项目", "安排"], [
        ["适用对象", "首次系统学习数据理解和预处理的生物医学AI学生"],
        ["三阶段", "45分钟课堂启动 90至120分钟课外自学 45分钟翻转课堂"],
        ["数据", "Heart Disease为主 WDBC为高维辅助"],
        ["总问题", "如何把多源生物医学数据转化为可审计且有边界的机器学习分析数据"],
        ["综合产出", "个人 Data readiness plan 和随机白板说明"],
    ], [1.35, 5.8], 9.0)
    add_heading(doc, "学习目标与问题映射", 1)
    add_objective_table(doc)
    add_heading(doc, "探究问题", 1)
    add_inquiry_map(doc, concise=True)

    add_heading(doc, "第一阶段 课堂启动 45分钟", 1)
    add_table(doc, ["时间", "教师行为", "学生行为", "阶段产出"], [
        ["0至5", "发放worksheet和问题数据 说明不得先看Packet B至D", "独立阅读并标记不确定处", "问题标记"],
        ["5至11", "提示先按已有知识作答 不纠正", "画初步工作流并写理由", "初步答案"],
        ["11至18", "追问对象 属性 尺度 相似和代表性", "形成工作定义和需要追问的问题", "澄清表"],
        ["18至25", "指向PPT和data.md相应章节", "建立Q1至Q10阅读导航", "学习路线"],
        ["25至35", "巡视并用问题支架推动知识缺口", "按概念群完成3W", "3W"],
        ["35至41", "检查计划是否含资源 分析和完成标准", "完成个人学习合同", "行动计划"],
        ["41至45", "收取退出条 决定课外支持重点", "提交当前判断 最大风险 下一步", "退出条"],
    ], [0.7, 2.55, 2.55, 1.25], 8.3)
    doc.add_paragraph("教师观察重点：学生是否把问题缩成某一个公式或模型；是否把数字编码误当作测量尺度；是否在没有定义观察单位和目标前就开始清洗或建模。")

    add_heading(doc, "第二阶段 课外自主学习", 1)
    add_table(doc, ["检查点", "学生任务", "发布材料", "教师反馈"], [
        ["A", "提交初步答案 3W和学习计划", "Packet A", "只反馈问题边界和缺失证据"],
        ["B", "完成Q1至Q4并更新总答案", "Packet B", "追问事实 原因和方法匹配"],
        ["C", "完成Q5至Q9的比较和敏感性解释", "Packet C", "追问度量语义 信息损失和泄漏"],
        ["D", "提交Q10及完整Data readiness plan", "Packet D", "检查Q1至Q9是否都进入综合答案"],
    ], [0.65, 2.55, 1.0, 3.1], 8.4)
    doc.add_paragraph("学生可用教材、网课、可靠资料和大模型。要求记录来源；对大模型或二手资料中的至少一个关键方法说法进行独立核验；保留自己的分析过程和答案修订。")
    add_heading(doc, "教师追问主题", 2)
    for prompt in [
        "如果删除站点变量，站点差异是否真的消失？",
        "为什么缩放改变Euclidean近邻却不一定改变correlation？",
        "共同为零在何种生物医学特征中应该或不应该算相似？",
        "分层抽样保护了什么，又没有保护什么？",
        "PCA保留90%方差为何仍可能损失任务含义？",
        "哪一步使用了全体数据的信息，为什么构成泄漏？",
    ]:
        doc.add_paragraph(prompt, style="List Bullet")

    add_heading(doc, "第三阶段 翻转课堂 45分钟", 1)
    add_table(doc, ["时间", "流程", "教师动作", "全体学生产出"], [
        ["0至4", "准备", "说明将随机抽取一至两名学生", "个人worksheet就绪"],
        ["4至16", "白板 talk", "随机抽取并追问分析证据与修订过程", "记录可借鉴和质疑点"],
        ["16至28", "同伴提问", "确保问题覆盖多个探究模块", "每人至少形成一个证据性问题"],
        ["28至37", "教师综合", "归纳共同难点 方法边界和停止条件", "修订概念连接"],
        ["37至43", "个人修订", "要求显式引用Q1至Q10", "最终答案"],
        ["43至45", "退出条", "收集仍未解决的问题", "反思"],
    ], [0.7, 1.15, 3.0, 2.3], 8.4)
    doc.add_paragraph("不使用固定演讲模板，也不预先指定学生角色。评价学生能否解释学习、分析和修订过程，而不是演讲形式。")

    add_heading(doc, "课堂练习", 1)
    doc.add_paragraph("给出两条患者记录和三种未经说明的距离结果。学生先指出变量尺度和缺失维度，再判断哪个结果最可能被量纲或共同为零主导，最后修改相似性规则。该练习直接服务Q1、Q5和Q6。")
    add_heading(doc, "作业要求", 1)
    doc.add_paragraph("完成全部worksheet、证据卡、Q1至Q10的阶段性答案、最终Data readiness plan和迁移任务。Notebook可用于复现证据，但评分对象是个人推理和证据使用。")
    add_heading(doc, "评价权重", 1)
    add_table(doc, ["评价维度", "权重", "可观察证据"], [
        ["课程覆盖与概念准确", "25%", "Q1至Q10均有合理回答且变量 方法 度量概念准确"],
        ["数据分析和证据使用", "25%", "能引用Packet结果并区分事实 推断和假设"],
        ["综合工作流", "25%", "步骤有依据 顺序防泄漏 含修改和停止条件"],
        ["推理 边界和不确定性", "15%", "使用Claim Evidence Reasoning Boundary"],
        ["自主学习和修订", "10%", "来源 AI核验记录和答案变化可追溯"],
    ], [2.0, 0.8, 4.45], 8.6)
    add_heading(doc, "教师综合锚点", 1)
    for item in [
        "先定义对象、问题和变量语义，再选择分析。",
        "质量处理、距离、抽样、变换和降维不是独立菜单，而是一条相互影响的工作流。",
        "所有从数据估计的预处理参数都必须尊重数据划分和独立单位。",
        "证据可以支持教学范围内的描述和方法判断，不能自动支持因果 临床或部署主张。",
    ]:
        doc.add_paragraph(item, style="List Bullet")
    add_heading(doc, "实施风险和应对", 1)
    add_table(doc, ["风险", "应对"], [
        ["学生提前阅读后续Packet", "允许完整worksheet发放 但用课堂提交和LMS检查点要求先留下不可回写的初始判断"],
        ["问题过多变成十份小作业", "每个模块必须写明如何修改总答案 最终评价检查Q1至Q10的综合"],
        ["学生只复述概念", "要求解释实际表格 图和方案比较"],
        ["学生依赖大模型代写", "要求证据卡 资料核验 分析记录和随机白板追问"],
        ["时间不足", "优先完成Q1 Q4 Q5 Q8 Q10 其余证据作为课外必做并在翻转课堂综合"],
    ], [2.0, 5.25], 8.7)
    finalize_doc(doc, path)
    return path


def build_design_rationale(data: dict[str, object]) -> Path:
    path = ROOT / f"pbl-{SLUG}-design-rationale.docx"
    doc = setup_doc("理解数据与机器学习准备", "Purpose Design Rationale Expected Outcomes")
    add_heading(doc, "教学问题", 1)
    doc.add_paragraph("传统章节教学容易把变量类型、数据质量、距离、抽样、变换和降维讲成彼此分离的概念。学生可能记得定义，却不能解释一套真实数据为何还不能直接用于机器学习，也不能判断某个处理步骤改变了什么。")
    add_heading(doc, "为什么适合PBL", 1)
    doc.add_paragraph("数据准备本质上是一个开放且有约束的决策问题。不存在脱离研究目的和数据语义的唯一处理方案。学生必须暴露初始判断、发现知识缺口、主动补充概念、解释数据证据并公开说明修订过程，这与三阶段PBL流程一致。")
    add_heading(doc, "问题架构如何覆盖全章", 1)
    doc.add_paragraph("总问题要求形成完整的数据准备工作流，而Q1至Q10分别承担语义、结构、质量、相似性、抽样、变换、降维和综合边界。任何一个核心问题被忽略，最终工作流都会留下可观察的缺口，因此总问题不能通过一个公式、一张图或一次模型运行回答。")
    add_inquiry_map(doc, concise=True)
    add_heading(doc, "目标覆盖", 1)
    add_objective_table(doc)
    add_heading(doc, "数据和证据设计", 1)
    doc.add_paragraph("Heart Disease保留四个来源中心、混合变量、缺失和不平衡，适合审查变量语义、来源差异、质量、相似性、抽样和预处理顺序。WDBC的30个连续图像特征包含明显相关冗余，作为小型辅助数据支持维度灾难、PCA和特征处理，而不把全章窄化为一个预测任务。")
    add_table(doc, ["证据群", "学生必须作出的判断", "为什么必要"], [
        ["数据字典 结构和方法映射", "对象 变量尺度和候选方法是否匹配", "阻止学生直接把数字列投入算法"],
        ["缺失 站点 异常和类别证据", "哪些是事实 哪些原因仍未知", "建立可审计的质量与停止条件"],
        ["多种距离和相似性比较", "哪种相似概念符合数据语义", "显示度量选择会改变近邻和解释"],
        ["抽样 聚合和变换敏感性", "处理保护或损失了什么", "连接代表性 信息量和实施顺序"],
        ["PCA 距离集中和特征方案", "何时降维以及如何检查损失", "覆盖高维数据而不承诺任务性能"],
        ["泄漏审查和综合工作流", "流程是否可复现 有边界 可停止", "把所有模块重新连接到总问题"],
    ], [2.1, 2.9, 2.25], 8.5)
    add_heading(doc, "渐进释放和完整worksheet", 1)
    doc.add_paragraph("学生worksheet内嵌全部Packet证据，便于课外独立完成。渐进性由任务顺序、课堂初始答案、3W、阶段检查点和明确的A至D使用说明实现。重点不是隐藏文件，而是要求学生在查看新证据前留下当前判断，并在查看后说明答案如何改变。")
    add_heading(doc, "预期学习成果", 1)
    for _, _, outcome in LO:
        doc.add_paragraph(outcome, style="List Bullet")
    add_heading(doc, "本材料不主张什么", 1)
    doc.add_paragraph("历史公开数据不能证明因果关系、目标人群代表性、临床效用、患者安全、校准充分性或部署准备度。缺失和站点差异只能被描述，不能在没有来源元数据时确定其机制。PCA解释方差不等于保留医学意义。")
    add_heading(doc, "迁移", 1)
    doc.add_paragraph("学生应把同一推理框架迁移到组学、医学影像特征、电子病历、临床文本或生物网络：先定义对象和问题，再审查结构和质量，随后选择相似性、抽样、变换和特征策略，最后明确验证需求与结论边界。")
    finalize_doc(doc, path)
    return path


def build_analysis_design() -> Path:
    analyses = [
        {"id": "A1", "objective_ids": ["LO1", "LO3"], "inquiry_question_ids": ["Q1"], "question": "变量语义和尺度允许哪些描述与方法？", "domain": "variable_semantics", "method": "人工审查数据字典和尺度微型案例并建立变量类型到方法的映射", "applicability": "直接检验变量语义和方法匹配", "artifacts": ["packet-b-data-dictionary.csv", "packet-b-measurement-scale-cases.csv", "packet-b-method-map.csv"], "packet": "B", "interpretation_boundary": "方法候选仍取决于研究设计和假设", "notebook_ref": "A1-variable-semantics"},
        {"id": "A2", "objective_ids": ["LO2"], "inquiry_question_ids": ["Q2"], "question": "不同数据结构保留哪些关系？", "domain": "data_structure", "method": "比较记录 矩阵 文档 事务 图和有序数据的观察单位与依赖", "applicability": "使学生在建立样本特征矩阵前明确结构", "artifacts": ["packet-b-structure-types.csv"], "packet": "B", "interpretation_boundary": "微型案例说明结构后果但不替代具体数据建模", "notebook_ref": "A2-data-structures"},
        {"id": "A3", "objective_ids": ["LO2", "LO8"], "inquiry_question_ids": ["Q3", "Q9"], "question": "维度 稀疏性和冗余如何影响距离与表示？", "domain": "data_structure", "method": "比较数据特征并计算距离集中随维度的变化", "applicability": "覆盖高维数据和维度灾难", "artifacts": ["packet-b-data-characteristics.csv", "packet-c-distance-concentration.csv"], "packet": "C", "interpretation_boundary": "距离集中不直接决定预测模型优劣", "notebook_ref": "A3-dimensionality"},
        {"id": "A4", "objective_ids": ["LO4", "LO6"], "inquiry_question_ids": ["Q4"], "question": "哪些质量问题由数据直接支持？", "domain": "data_quality", "method": "缺失率 站点缺失 差异 异常 重复 异常零值和目标分布审查", "applicability": "主数据包含真实的多站点缺失和分布差异", "artifacts": ["packet-b-quality-audit.csv", "packet-b-quality-evidence-boundaries.csv", "packet-b-missingness-by-site.csv", "packet-b-missingness.png", "packet-b-target-by-site.csv"], "packet": "B", "interpretation_boundary": "观察到的模式不能单独识别缺失或站点差异原因", "notebook_ref": "A4-quality-audit"},
        {"id": "A5", "objective_ids": ["LO7"], "inquiry_question_ids": ["Q5"], "question": "度量选择和缩放如何改变相似性判断？", "domain": "similarity_distance", "method": "比较Euclidean Manhattan Minkowski Mahalanobis cosine correlation 信息量和缩放前后近邻", "applicability": "显示度量保留的含义不同", "artifacts": ["packet-c-neighbor-ranking.csv", "packet-c-metric-comparison.csv", "packet-c-distance-sensitivity.png", "packet-c-vector-metrics.csv", "packet-c-information-measures.csv"], "packet": "C", "interpretation_boundary": "示例度量不保证任务相关性 Mahalanobis还依赖稳定的协方差估计", "notebook_ref": "A5-metric-sensitivity"},
        {"id": "A6", "objective_ids": ["LO7"], "inquiry_question_ids": ["Q6"], "question": "二值与混合变量如何组合相似性？", "domain": "similarity_distance", "method": "比较SMC Jaccard和按变量类型分项的Gower式距离", "applicability": "主数据同时含连续 名义 有序和非对称二值变量", "artifacts": ["packet-c-binary-similarity.csv", "packet-c-mixed-similarity.csv"], "packet": "C", "interpretation_boundary": "权重仍需由任务语义和领域知识确定", "notebook_ref": "A6-mixed-similarity"},
        {"id": "A7", "objective_ids": ["LO6", "LO8"], "inquiry_question_ids": ["Q7"], "question": "抽样和聚合保护或损失了什么？", "domain": "sampling_representativeness", "method": "250次随机与站点分层抽样比较 加上站点聚合", "applicability": "四中心结构可观察代表性变化", "artifacts": ["packet-c-sampling-replicates.csv", "packet-c-sampling-sensitivity.png", "packet-c-aggregation.csv"], "packet": "C", "interpretation_boundary": "分层只保护所用分层变量 不保证总体代表性", "notebook_ref": "A7-sampling-aggregation"},
        {"id": "A8", "objective_ids": ["LO5", "LO8"], "inquiry_question_ids": ["Q8"], "question": "变换 标准化和实施顺序如何影响数据？", "domain": "transformation_preprocessing", "method": "分布变换 分箱比较以及全数据拟合与训练集拟合审查", "applicability": "直接覆盖变换和防泄漏目标", "artifacts": ["packet-c-transformation-summary.csv", "packet-c-transformations.png", "packet-d-preprocessing-audit.csv"], "packet": "D", "interpretation_boundary": "变换不能修复来源 缺失机制或测量问题", "notebook_ref": "A8-transform-leakage"},
        {"id": "A9", "objective_ids": ["LO2", "LO8"], "inquiry_question_ids": ["Q9"], "question": "维度处理如何平衡压缩 信息和语义？", "domain": "transformation_preprocessing", "method": "标准化后PCA 解释方差 载荷和特征策略比较", "applicability": "WDBC提供小型相关高维数值特征", "artifacts": ["packet-c-pca-summary.csv", "packet-c-pca-loadings.csv", "packet-c-pca.png", "packet-c-feature-options.csv"], "packet": "C", "interpretation_boundary": "解释方差不等于临床意义或任务表现", "notebook_ref": "A9-pca-features"},
        {"id": "A10", "objective_ids": ["LO3", "LO5", "LO6"], "inquiry_question_ids": ["Q10"], "question": "完整数据准备流程如何被审查和停止？", "domain": "validation_robustness", "method": "综合Q1至Q9形成步骤 证据 修改停止条件和报告边界", "applicability": "把分散概念变为可审计决策", "artifacts": ["packet-d-workflow-decision.csv", "packet-d-boundary-checklist.csv", "packet-d-preprocessing-workflow.png"], "packet": "D", "interpretation_boundary": "工作流仅用于教学数据审查 不证明临床或部署有效", "notebook_ref": "A10-synthesis"},
    ]
    q_map = {q["id"]: q for q in QUESTIONS}
    course_coverage = []
    for lo_id, source, outcome in LO:
        qs = [q for q in QUESTIONS if lo_id in q["objective_ids"]]
        analysis_ids = [a["id"] for a in analyses if lo_id in a["objective_ids"]]
        course_coverage.append({
            "objective_id": lo_id,
            "source_excerpt": source,
            "observable_outcome": outcome,
            "concept_cluster_ids": [c["id"] for c in CONCEPTS if lo_id in c["objective_ids"]],
            "inquiry_question_ids": [q["id"] for q in qs],
            "analysis_ids": analysis_ids,
            "required_learning": sorted({item for q in qs for item in q["required_learning"]}),
            "student_action": "；".join(q["student_action"] for q in qs),
            "student_output": "；".join(q["student_output"] for q in qs),
            "worksheet_location": "Phase 2 " + " ".join(q["id"] for q in qs) + " and Packet evidence pages",
            "synthesis_use": "用于最终Data readiness plan中的主张 证据 推理 边界和停止条件",
            "assessment_evidence": outcome,
        })
    design = {
        "study_goal": "学生综合全章概念，把多源生物医学数据转化为可审计 有边界且防泄漏的机器学习分析数据。",
        "learning_objectives": [{"id": a, "source_excerpt": b, "observable_outcome": c} for a, b, c in LO],
        "concept_clusters": CONCEPTS,
        "misconceptions": MISCONCEPTIONS,
        "decision_problem": "为多源生物医学数据制定数据准备决策并说明修改或停止条件。",
        "driving_question": "这些数据需要如何处理 才能合理用于机器学习？",
        "entry_type": "direct_problem",
        "problem_architecture": {
            "overarching_problem": "研究团队获得四中心临床表格和高维图像特征数据，需要依据数据语义 结构 质量 相似性 抽样 变换和降维证据制定可审计的数据准备工作流，并在证据不足 泄漏或信息损失不可接受时修改或停止。",
            "inquiry_questions": QUESTIONS,
        },
        "course_coverage": course_coverage,
        "data_context": {
            "primary_dataset": {"dataset_name": "UCI Heart Disease four-site teaching table", "source": "UCI DOI 10.24432/C52P4X", "license_note": "CC BY 4.0 recorded in course metadata", "task": "data readiness audit", "observation_unit": "one historical patient record", "rows": 920, "columns": 16, "variable_roles": {"identifier": ["record_id"], "provenance": ["site"], "features": ["age", "sex", "cp", "trestbps", "chol", "fbs", "restecg", "thalach", "exang", "oldpeak", "slope", "ca", "thal"], "target": ["num"]}, "grouping_fields": ["site"], "target": "num 0-4; teaching binary view num>0"},
            "supporting_dataset": {"dataset_name": "Breast Cancer Wisconsin Diagnostic", "source": "UCI WDBC bundled in scikit-learn", "license_note": "Attribution included; recheck current UCI terms before external redistribution", "task": "dimensionality and PCA", "observation_unit": "one digitized FNA sample", "rows": 569, "features": 30, "target": "diagnosis 212 malignant 357 benign"},
        },
        "analyses": analyses,
        "split_plan": {"required": True, "unit": "patient record", "rationale": "仅用于演示拟合型插补和标准化参数必须在划分后从训练数据估计；本章不评价预测性能。"},
        "packets": {
            "A": {"purpose": "界定总问题并保存初始判断", "reveals": ["数据规模", "问题地图", "缺失证据清单"], "withholds": ["结构质量证据", "敏感性结果", "综合工作流"]},
            "B": {"purpose": "解释数据语义 结构和质量", "reveals": ["数据字典", "结构案例", "缺失和站点证据"], "withholds": ["度量 抽样 变换 降维和综合证据"]},
            "C": {"purpose": "比较相似性 抽样 变换和降维", "reveals": ["敏感性与信息损失证据"], "withholds": ["最终综合与边界"]},
            "D": {"purpose": "综合可审计工作流", "reveals": ["泄漏审查", "停止条件", "边界"], "withholds": []},
        },
        "boundaries": ["teaching only", "no causal inference", "no clinical utility claim", "no deployment readiness", "missingness mechanism not identified", "PCA variance is not clinical meaning"],
    }
    path = ASSET_DIR / "analysis-design.json"
    path.write_text(json.dumps(design, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def notebook_cell(cell_type: str, source: str) -> dict[str, object]:
    cell = {"cell_type": cell_type, "metadata": {}, "source": [line + "\n" for line in source.splitlines()]}
    if cell_type == "code":
        cell.update({"execution_count": None, "outputs": []})
    return cell


def build_notebook() -> Path:
    path = NOTEBOOK_DIR / f"pbl-{SLUG}-lab.ipynb"
    cells = [
        notebook_cell("markdown", "# 理解数据与机器学习准备\n\n本notebook离线复现Packet B至D的主要证据。它用于教学，不提供临床、因果或部署结论。每一节对应探究问题，并要求解释结果如何修改总Data readiness plan。"),
        notebook_cell("code", "from pathlib import Path\nimport numpy as np\nimport pandas as pd\nimport matplotlib.pyplot as plt\nfrom sklearn.datasets import load_breast_cancer\nfrom sklearn.decomposition import PCA\nfrom sklearn.feature_selection import mutual_info_classif\nfrom sklearn.metrics import pairwise_distances\nfrom sklearn.model_selection import train_test_split\nfrom sklearn.preprocessing import StandardScaler\nASSET_DIR = Path('../assets/pbl-understanding-data')\nheart = pd.read_csv(ASSET_DIR / 'heart-disease-four-site.csv')\nheart['disease_binary'] = (heart['num'] > 0).astype(int)\ncancer_bunch = load_breast_cancer(as_frame=True)\ncancer_x = cancer_bunch.data.copy()\nprint(heart.shape, cancer_x.shape)"),
        notebook_cell("markdown", "## Q1和Q2 数据对象 变量语义与结构\n\n检查数据字典中的角色和测量尺度。不要把数字编码自动解释为连续变量。"),
        notebook_cell("code", "dictionary = pd.read_csv(ASSET_DIR / 'packet-b-data-dictionary.csv')\nscale_cases = pd.read_csv(ASSET_DIR / 'packet-b-measurement-scale-cases.csv')\nstructures = pd.read_csv(ASSET_DIR / 'packet-b-structure-types.csv')\ndisplay(dictionary)\ndisplay(scale_cases)\ndisplay(structures)\nassert dictionary.loc[dictionary.variable.eq('cp'), 'measurement_scale'].iloc[0] == 'nominal multiclass'\nassert set(scale_cases.measurement_scale) >= {'nominal','ordinal','interval','ratio'}"),
        notebook_cell("markdown", "反思：如果把cp直接当作连续变量，距离和模型系数会隐含什么不存在的顺序？记录数据与有序数据的独立性假设有什么不同？"),
        notebook_cell("markdown", "## Q3和Q4 维度与数据质量 Packet B"),
        notebook_cell("code", "numeric = [c for c in heart.columns if c not in ['record_id','site','disease_binary']]\nmissing_overall = heart[numeric].isna().sum().sort_values(ascending=False)\nmissing_by_site = heart.groupby('site')[numeric].apply(lambda x: x.isna().mean()*100)\ndisplay(missing_overall.to_frame('missing_n'))\ndisplay(missing_by_site)\nprint('duplicate feature rows', heart.drop(columns=['record_id','disease_binary']).duplicated().sum())\nprint('recorded zeros', {c:int((heart[c]==0).sum()) for c in ['trestbps','chol','thalach']})\ndisplay(pd.read_csv(ASSET_DIR / 'packet-b-quality-evidence-boundaries.csv'))\nprint(pd.crosstab(heart.site, heart.num, normalize='index').round(3))"),
        notebook_cell("markdown", "反思：哪些模式是事实？哪些原因需要采集流程、仪器或中心信息才能判断？什么发现会迫使你停止合并四个中心？"),
        notebook_cell("markdown", "## Q5 距离 相似性和信息度量 Packet C"),
        notebook_cell("code", "cols = ['age','trestbps','chol','thalach','oldpeak']\nx = heart[cols].fillna(heart[cols].median())\nraw = x.to_numpy()\nz = StandardScaler().fit_transform(raw)\nd_raw = pairwise_distances(raw, metric='euclidean')\nd_z_e = pairwise_distances(z, metric='euclidean')\nd_z_m = pairwise_distances(z, metric='manhattan')\nd_z_p3 = pairwise_distances(z, metric='minkowski', p=3)\nVI = np.linalg.pinv(np.cov(z, rowvar=False))\nd_z_mahal = pairwise_distances(z, metric='mahalanobis', VI=VI)\nanchor = 0\nfor name, d in [('raw Euclidean', d_raw), ('standardized Euclidean', d_z_e), ('standardized Manhattan', d_z_m), ('Minkowski p3', d_z_p3), ('Mahalanobis', d_z_mahal)]:\n    order = np.argsort(d[anchor])[1:7]\n    print(name, heart.loc[order, 'record_id'].tolist())\n# Mahalanobis additionally depends on a stable covariance estimate.\nprint(pd.read_csv(ASSET_DIR / 'packet-c-metric-comparison.csv'))\n# cosine and correlation respond differently to scaling and translation\nv = z[0]\nfor label, w in [('scaled', 2*v), ('shifted', v+2), ('reversed', v[::-1])]:\n    cosine = np.dot(v,w)/(np.linalg.norm(v)*np.linalg.norm(w))\n    correlation = np.corrcoef(v,w)[0,1]\n    print(label, 'cosine', round(cosine,3), 'correlation', round(correlation,3))"),
        notebook_cell("code", "mi_frame = heart[['age','chol','cp','exang','disease_binary']].copy()\nmi_frame['age_bin'] = pd.qcut(mi_frame.age, 5, duplicates='drop').cat.codes\nmi_frame['chol_bin'] = pd.qcut(mi_frame.chol, 5, duplicates='drop').cat.codes\nmi_x = mi_frame[['age_bin','chol_bin','cp','exang']].fillna(-1).astype(int)\nmi = mutual_info_classif(mi_x, mi_frame.disease_binary, discrete_features=True, random_state=42)\npd.Series(mi, index=mi_x.columns, name='mutual_information')"),
        notebook_cell("markdown", "反思：哪个度量表达绝对数值差、向量方向、中心化后的共变趋势或信息依赖？任何一个较大数值是否足以证明临床相似或因果关系？"),
        notebook_cell("markdown", "## Q6 二值与混合变量相似性"),
        notebook_cell("code", "binary = pd.read_csv(ASSET_DIR / 'packet-c-binary-similarity.csv')\nmixed = pd.read_csv(ASSET_DIR / 'packet-c-mixed-similarity.csv')\ndisplay(binary)\ndisplay(mixed)\nprint('SMC counts joint zeros; Jaccard ignores them. Mixed distance excludes missing dimensions and rescales continuous variables.')"),
        notebook_cell("markdown", "反思：在症状或突变是否出现的特征中，共同未出现应否构成强相似证据？混合距离权重应由谁决定？"),
        notebook_cell("markdown", "## Q7 抽样与聚合"),
        notebook_cell("code", "sampling = pd.read_csv(ASSET_DIR / 'packet-c-sampling-replicates.csv')\ndisplay(sampling.groupby('method')[['max_site_proportion_error','disease_prevalence_abs_error']].agg(['mean','std','max']))\naggregation = heart.groupby('site').agg(n=('record_id','size'), age_mean=('age','mean'), age_sd=('age','std'), prevalence=('disease_binary','mean'))\ndisplay(aggregation)\nprint('Patient rows:', len(heart), 'Aggregated site rows:', len(aggregation))"),
        notebook_cell("markdown", "反思：站点分层保证了什么？它没有保证哪些人口或测量属性？站点均值隐藏了哪些患者级变异？"),
        notebook_cell("markdown", "## Q8 变换 标准化与泄漏 Packet C和D"),
        notebook_cell("code", "for col in ['chol','oldpeak','trestbps']:\n    s = heart[col].dropna()\n    print(col, 'raw skew', round(s.skew(),3), 'log1p skew', round(np.log1p(s-s.clip(upper=0).min()).skew(),3))\nprint(pd.cut(heart.age.dropna(), 5).value_counts().sort_index())\nprint(pd.qcut(heart.age.dropna(), 5, duplicates='drop').value_counts().sort_index())"),
        notebook_cell("code", "frame = heart[['age','trestbps','chol','thalach','oldpeak','disease_binary']]\ntrain, test = train_test_split(frame, test_size=.30, random_state=42, stratify=frame.disease_binary)\ntrain_x, test_x = train.drop(columns='disease_binary'), test.drop(columns='disease_binary')\ntrain_median = train_x.median()\nscaler = StandardScaler().fit(train_x.fillna(train_median))\ntest_z = scaler.transform(test_x.fillna(train_median))\nprint('Train-fitted test means', pd.Series(test_z.mean(axis=0), index=train_x.columns).round(3))\nprint('The test set did not determine medians or scaling parameters.')"),
        notebook_cell("markdown", "反思：为什么测试集标准化后均值不必等于0？哪些操作需要在训练折内重复拟合？"),
        notebook_cell("markdown", "## Q9 维度灾难 PCA和特征处理"),
        notebook_cell("code", "z_bc = StandardScaler().fit_transform(cancer_x)\npca = PCA().fit(z_bc)\ncum = np.cumsum(pca.explained_variance_ratio_)\nprint('components for 90%', np.argmax(cum>=.90)+1)\nprint('components for 95%', np.argmax(cum>=.95)+1)\nplt.plot(np.arange(1,31), cum, marker='o'); plt.axhline(.9, ls='--'); plt.xlabel('components'); plt.ylabel('cumulative variance'); plt.show()\nfor d in [2,5,10,20,30]:\n    distances = pairwise_distances(z_bc[:150,:d])\n    vals = distances[np.triu_indices_from(distances,k=1)]\n    print(d, 'CV of distances', round(vals.std()/vals.mean(),3))"),
        notebook_cell("code", "loadings = pd.DataFrame(PCA(n_components=3).fit(z_bc).components_.T, index=cancer_x.columns, columns=['PC1','PC2','PC3'])\nfor pc in loadings:\n    print(pc, loadings[pc].abs().nlargest(6).index.tolist())"),
        notebook_cell("markdown", "反思：90%解释方差回答了什么，没有回答什么？何时更愿意保留命名特征而不是使用主成分？"),
        notebook_cell("markdown", "## Q10 综合工作流 Packet D"),
        notebook_cell("code", "workflow = pd.read_csv(ASSET_DIR / 'packet-d-workflow-decision.csv')\nboundaries = pd.read_csv(ASSET_DIR / 'packet-d-boundary-checklist.csv')\ndisplay(workflow)\ndisplay(boundaries)\nassert set(workflow.inquiry_questions.str.cat(sep=' ').split()) >= {f'Q{i}' for i in range(1,11)}"),
        notebook_cell("markdown", "## 最终反思\n\n用Claim Evidence Reasoning Uncertainty Boundary Stop conditions重写你的Data readiness plan。明确引用Q1至Q10，并说明哪一项证据最可能改变当前决定。"),
    ]
    notebook = {
        "cells": cells,
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": f"{sys.version_info.major}.{sys.version_info.minor}"}},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.write_text(json.dumps(notebook, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def build_manifest(doc_paths: list[Path], notebook_path: Path, design_path: Path) -> Path:
    asset_names = sorted(p.name for p in ASSET_DIR.iterdir() if p.is_file())
    coverage = []
    design = json.loads(design_path.read_text(encoding="utf-8"))
    for item in design["course_coverage"]:
        coverage.append({
            "objective_id": item["objective_id"],
            "inquiry_question_ids": item["inquiry_question_ids"],
            "analysis_ids": item["analysis_ids"],
            "worksheet_output": item["student_output"],
            "synthesis": item["synthesis_use"],
        })
    manifest = {
        "topic": "理解数据与机器学习准备",
        "slug": SLUG,
        "mode": "data_preprocessing_workflow",
        "dataset": {
            "name": "UCI Heart Disease four-site teaching table with WDBC supporting evidence",
            "source": "UCI DOI 10.24432/C52P4X; UCI WDBC bundled in scikit-learn",
            "task": "data readiness audit",
            "target": "Heart Disease num; WDBC diagnosis used only as metadata for dimensionality evidence",
        },
        "outputs": {
            "student_worksheet": doc_paths[0].name,
            "evidence_pack": doc_paths[1].name,
            "teaching_plan": doc_paths[2].name,
            "design_rationale": doc_paths[3].name,
            "notebook": notebook_path.relative_to(ROOT).as_posix(),
        },
        "assets": [rel_asset(name) for name in asset_names],
        "boundary": "Teaching only; no clinical, patient-care, causal, or deployment claim.",
        "core_question": "这些多源生物医学数据需要如何处理 才能合理用于机器学习 哪些发现要求修改或停止流程",
        "problem_architecture": {"overarching_problem": design["problem_architecture"]["overarching_problem"], "inquiry_question_ids": [q["id"] for q in QUESTIONS]},
        "course_coverage": coverage,
        "customized": True,
        "course_brief": "data.md",
        "source_deck": "chap2_data.pptx",
        "analysis_design": design_path.relative_to(ROOT).as_posix(),
        "build_script": "scripts/pbl-understanding-data-build.py",
    }
    path = ROOT / "package-manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def validate_package(doc_paths: list[Path], notebook_path: Path, design_path: Path, manifest_path: Path) -> None:
    required = doc_paths + [notebook_path, design_path, manifest_path, DATA_PATH]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise RuntimeError(f"Missing required outputs: {missing}")
    design = json.loads(design_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    expected_los = {x[0] for x in LO}
    coverage_los = {x["objective_id"] for x in design["course_coverage"]}
    if expected_los != coverage_los:
        raise RuntimeError(f"Objective coverage mismatch: {expected_los ^ coverage_los}")
    expected_q = {q["id"] for q in QUESTIONS}
    for item in design["course_coverage"]:
        for field in ["inquiry_question_ids", "analysis_ids", "required_learning", "student_action", "student_output", "worksheet_location", "synthesis_use", "assessment_evidence"]:
            if not item.get(field):
                raise RuntimeError(f"Incomplete coverage {item['objective_id']} field {field}")
    analysis_q = {qid for a in design["analyses"] for qid in a["inquiry_question_ids"]}
    if analysis_q != expected_q:
        raise RuntimeError(f"Inquiry analysis coverage mismatch: {analysis_q ^ expected_q}")
    for analysis in design["analyses"]:
        if analysis["packet"] not in ["B", "C", "D"]:
            raise RuntimeError(f"Unexpected packet {analysis['packet']}")
        for artifact in analysis["artifacts"]:
            if not (ASSET_DIR / artifact).exists():
                raise RuntimeError(f"Missing analysis artifact {artifact}")
    if len([c for c in notebook["cells"] if c["cell_type"] == "code"]) < 10:
        raise RuntimeError("Notebook lacks substantive executable sections")
    notebook_text = "".join("".join(c["source"]) for c in notebook["cells"])
    for token in ["heart-disease-four-site.csv", "pairwise_distances", "train_test_split", "PCA", "packet-d-workflow-decision.csv"]:
        if token not in notebook_text:
            raise RuntimeError(f"Notebook missing reproducibility token {token}")
    for doc_path in doc_paths:
        doc = Document(doc_path)
        text_content = "\n".join(p.text for p in doc.paragraphs) + "\n" + "\n".join(cell.text for t in doc.tables for row in t.rows for cell in row.cells)
        if "�" in text_content:
            raise RuntimeError(f"Mangled Unicode in {doc_path.name}")
        if len(text_content) < 1500:
            raise RuntimeError(f"Document appears sparse: {doc_path.name}")
    worksheet_doc = Document(doc_paths[0])
    worksheet_text = "\n".join(p.text for p in worksheet_doc.paragraphs) + "\n" + "\n".join(cell.text for t in worksheet_doc.tables for row in t.rows for cell in row.cells)
    for token in ["What do I know", "What do I not know", "What will I do next", "随机抽取一至两名学生", "Q10", "Data readiness plan"]:
        if token not in worksheet_text:
            raise RuntimeError(f"Worksheet missing required text {token}")
    for asset in manifest["assets"]:
        if not (ROOT / asset).exists():
            raise RuntimeError(f"Manifest asset missing {asset}")
    pngs = list(ASSET_DIR.glob("*.png"))
    if not pngs:
        raise RuntimeError("No plot assets generated")
    for png in pngs:
        with Image.open(png) as im:
            if im.width < 900 or im.height < 450:
                raise RuntimeError(f"Plot too small {png.name}: {im.size}")
    print(f"Validated {len(doc_paths)} DOCX files, {len(manifest['assets'])} assets, and {len(notebook['cells'])} notebook cells")


def main() -> None:
    ensure_dirs()
    data = analyze_data()
    design_path = build_analysis_design()
    student = build_student_worksheet(data)
    evidence = build_evidence_pack(data)
    teacher = build_teacher_plan(data)
    rationale = build_design_rationale(data)
    notebook = build_notebook()
    docs = [student, evidence, teacher, rationale]
    manifest = build_manifest(docs, notebook, design_path)
    validate_package(docs, notebook, design_path, manifest)
    print("Package generated at", ROOT)


if __name__ == "__main__":
    main()
