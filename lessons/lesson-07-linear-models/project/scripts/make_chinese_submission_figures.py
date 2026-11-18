from __future__ import annotations

from pathlib import Path
import importlib.util
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from audit_panel_alignment import require_matplotlib_panel_alignment

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "research-upgrade" / "figures"
ANALYSIS = ROOT / "research-upgrade" / "analysis"

spec = importlib.util.spec_from_file_location("transport", SCRIPT_DIR / "multisite_transport_analysis.py")
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)

SITES = list(transport.FILES)
SHORT = ["Cleveland", "Hungary", "Switzerland", "VA"]
MODELS = ["Logistic regression", "Shrinkage LDA"]
MODEL_CN = {"Logistic regression": "逻辑回归", "Shrinkage LDA": "收缩 LDA"}
COLORS = {"Logistic regression": "#2F6B9A", "Shrinkage LDA": "#D17A22"}
SITE_COLORS = dict(zip(SITES, ["#3C6E91", "#D18B35", "#7A6AA6", "#4F8A70"]))


def configure() -> None:
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Microsoft YaHei", "Arial", "DejaVu Sans"],
        "font.size": 6.5,
        "axes.titlesize": 7.5,
        "axes.labelsize": 6.5,
        "axes.linewidth": 0.7,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
        "axes.unicode_minus": False,
    })


def save(fig: plt.Figure, stem: str) -> None:
    fig.savefig(FIG / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(FIG / f"{stem}.svg", bbox_inches="tight")
    fig.savefig(FIG / f"{stem}.png", dpi=600, bbox_inches="tight")
    fig.savefig(FIG / f"{stem}.tiff", dpi=600, bbox_inches="tight")
    plt.close(fig)


def label_panels(axes) -> None:
    for label, ax in zip("abcdef", np.asarray(axes).flat):
        if ax.get_visible():
            ax.text(-0.12, 1.08, label, transform=ax.transAxes, fontsize=8,
                    fontweight="bold", va="top", ha="right")


def design_figure() -> None:
    fig, ax = plt.subplots(figsize=(7.2, 2.25))
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis("off")
    boxes = [
        (0.02, 0.34, 0.16, 0.34, "四个中心\n920 条记录", "#E8EEF3"),
        (0.205, 0.34, 0.16, 0.34, "完整留出\n一个中心", "#DDEAF2"),
        (0.39, 0.34, 0.18, 0.34, "折内拟合\n预处理流程", "#E8EEF3"),
        (0.595, 0.34, 0.18, 0.34, "逻辑回归 + LDA\n交叉验证选阈值", "#F8E9D5"),
        (0.80, 0.34, 0.18, 0.34, "外部审计\n排序·概率·损失·认证", "#E7F1E8"),
    ]
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
    for x, y, w, h, text, color in boxes:
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.018",
                                    facecolor=color, edgecolor="#4A4A4A", linewidth=0.8))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=6.5, linespacing=1.3)
    for left, right in zip(boxes[:-1], boxes[1:]):
        ax.add_patch(FancyArrowPatch((left[0] + left[2] + 0.007, 0.51), (right[0] - 0.007, 0.51),
                                     arrowstyle="-|>", mutation_scale=9, color="#5A5A5A", linewidth=0.9))
    ax.text(0.28, 0.18, "重复四次；目标中心从不进入开发过程", ha="center", color="#3F5F75", fontsize=6.2)
    ax.text(0.88, 0.18, "5FN + FP；外部评价前冻结", ha="center", color="#6C542F", fontsize=6.2)
    require_matplotlib_panel_alignment(fig, json_out=FIG / "study-design-cn.alignment.json",
        overlay_svg=FIG / "study-design-cn.alignment.svg", tolerance_pt=1.5,
        gutter_tolerance_pt=1.5, require_panel_labels=False, strict=True)
    save(fig, "study-design-cn")


def landscape_figure(data: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.0))
    fig.subplots_adjust(left=0.08, right=0.95, bottom=0.20, top=0.84, wspace=0.85)
    counts = data.groupby(["site", "target"]).size().unstack(fill_value=0).loc[SITES]
    y = np.arange(4)
    ax = axes[0]
    ax.barh(y, counts[0], color="#B8C1C8", label="阴性", edgecolor="none")
    ax.barh(y, counts[1], left=counts[0], color="#C86B4A", label="阳性", edgecolor="none")
    for i, site in enumerate(SITES):
        n = int(counts.loc[site].sum()); p = counts.loc[site, 1] / n
        ax.text(n - 7, i, f"n={n}\np={p:.2f}", color="white", ha="right", va="center",
                fontsize=5, fontweight="semibold", linespacing=1.25)
    ax.set_yticks(y, SHORT, fontsize=6); ax.invert_yaxis(); ax.set_xlim(0, 370)
    ax.set_xlabel("记录数"); ax.set_title("结局构成")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.19), ncol=2, frameon=False, fontsize=5.3)

    miss = data.groupby("site")[transport.NUMERIC + transport.CATEGORICAL].apply(lambda x: x.isna().mean()).loc[SITES]
    feature_cn = ["年龄", "静息血压", "胆固醇", "最大心率", "ST 压低", "性别", "胸痛类型",
                  "空腹血糖", "静息心电图", "运动性心绞痛", "ST 斜率", "主要血管数", "地中海贫血"]
    ax = axes[1]
    im = ax.imshow(miss.to_numpy().T, aspect="auto", cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(4), ["Clev.", "Hung.", "Swiss", "VA"], fontsize=5.5)
    ax.set_yticks(range(13), feature_cn, fontsize=5.3); ax.set_title("各中心缺失比例")
    cax = ax.inset_axes([1.035, 0.24, 0.045, 0.56]); cb = fig.colorbar(im, cax=cax)
    cb.set_label("缺失比例", fontsize=5.8); cb.ax.tick_params(labelsize=5.2)

    numeric = data[transport.NUMERIC]
    z = (numeric - numeric.mean()) / numeric.std(ddof=0); z["site"] = data.site
    means = z.groupby("site")[transport.NUMERIC].mean().loc[SITES]
    vmax = max(abs(means.min().min()), abs(means.max().max()))
    ax = axes[2]
    im2 = ax.imshow(means.to_numpy().T, aspect="auto", cmap="RdBu_r", vmin=-vmax, vmax=vmax)
    ax.set_xticks(range(4), ["Clev.", "Hung.", "Swiss", "VA"], fontsize=5.5)
    ax.set_yticks(range(5), ["年龄", "静息血压", "胆固醇", "最大心率", "ST 压低"], fontsize=5.3)
    ax.set_title("数值变量标准化均值")
    cax2 = ax.inset_axes([1.035, 0.24, 0.045, 0.56]); cb2 = fig.colorbar(im2, cax=cax2)
    cb2.set_label("合并标准差", fontsize=5.8); cb2.ax.tick_params(labelsize=5.2)
    label_panels(axes)
    require_matplotlib_panel_alignment(fig, json_out=FIG / "data-landscape-cn.alignment.json",
        overlay_svg=FIG / "data-landscape-cn.alignment.svg", tolerance_pt=1.5,
        gutter_tolerance_pt=1.5, require_panel_labels=True, strict=True,
        exclude_axes=[cax, cax2])
    save(fig, "data-landscape-cn")


def feature_distribution_figure(data: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(7.2, 4.8))
    fig.subplots_adjust(left=0.08, right=0.97, bottom=0.10, top=0.91, wspace=0.34, hspace=0.48)
    specs = [("age", "年龄（岁）"), ("trestbps", "静息血压"), ("chol", "胆固醇"),
             ("thalach", "最大心率"), ("oldpeak", "ST 压低")]
    for ax, (col, title) in zip(axes.flat[:5], specs):
        vals = [data.loc[data.site == site, col].dropna().to_numpy() for site in SITES]
        bp = ax.boxplot(vals, patch_artist=True, widths=0.62, showfliers=False,
                        medianprops={"color": "#222222", "linewidth": 1})
        for patch, site in zip(bp["boxes"], SITES):
            patch.set_facecolor(SITE_COLORS[site]); patch.set_alpha(0.72); patch.set_edgecolor("none")
        ax.set_xticks(range(1, 5), ["Clev.", "Hung.", "Swiss", "VA"], fontsize=5.4)
        ax.set_title(title); ax.grid(axis="y", color="#E6E6E6", linewidth=0.5)
    ax = axes[1, 2]
    cat = []
    cat_labels = []
    for col, label in [("sex", "男性"), ("fbs", "高空腹血糖"), ("exang", "运动性心绞痛")]:
        cat.append([pd.to_numeric(data.loc[data.site == s, col], errors="coerce").mean() for s in SITES])
        cat_labels.append(label)
    cp_high = [pd.to_numeric(data.loc[data.site == s, "cp"], errors="coerce").isin([3, 4]).mean() for s in SITES]
    cat.append(cp_high); cat_labels.append("胸痛类型 3/4")
    im = ax.imshow(np.asarray(cat), aspect="auto", cmap="YlOrRd", vmin=0, vmax=1)
    ax.set_xticks(range(4), ["Clev.", "Hung.", "Swiss", "VA"], fontsize=5.4)
    ax.set_yticks(range(4), cat_labels, fontsize=5.2); ax.set_title("分类变量阳性比例")
    cax = ax.inset_axes([1.035, 0.18, 0.045, 0.64]); cb = fig.colorbar(im, cax=cax)
    cb.set_label("比例", fontsize=5.8); cb.ax.tick_params(labelsize=5.2)
    label_panels(axes)
    require_matplotlib_panel_alignment(fig, json_out=FIG / "feature-distributions-cn.alignment.json",
        overlay_svg=FIG / "feature-distributions-cn.alignment.svg", tolerance_pt=1.5,
        gutter_tolerance_pt=1.5, require_panel_labels=True, strict=True, exclude_axes=[cax])
    save(fig, "feature-distributions-cn")


def calibration_figure(pred: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 6.8))
    fig.subplots_adjust(left=0.09, right=0.97, bottom=0.09, top=0.91, wspace=0.28, hspace=0.38)
    for ax, site in zip(axes.flat, SITES):
        ax.plot([0, 1], [0, 1], ls="--", lw=0.8, color="#999999", label="理想校准")
        for model in MODELS:
            part = pred[(pred.held_out_site == site) & (pred.model == model)].copy()
            part["bin"] = pd.qcut(part.probability, q=5, duplicates="drop")
            grouped = part.groupby("bin", observed=True).agg(predicted=("probability", "mean"),
                                                              observed=("target", "mean"), n=("target", "size"))
            ax.plot(grouped.predicted, grouped.observed, marker="o", ms=3.5, lw=1.1,
                    color=COLORS[model], label=MODEL_CN[model])
        ax.set(xlim=(-0.02, 1.02), ylim=(-0.02, 1.02), xlabel="平均预测概率", ylabel="观察阳性比例",
               title=SHORT[SITES.index(site)])
        ax.grid(color="#ECECEC", linewidth=0.5)
    axes[0, 0].legend(loc="upper left", fontsize=5.5, frameon=False,
                      handlelength=0.8, handletextpad=1.5)
    label_panels(axes)
    require_matplotlib_panel_alignment(fig, json_out=FIG / "calibration-cn.alignment.json",
        overlay_svg=FIG / "calibration-cn.alignment.svg", tolerance_pt=1.5,
        gutter_tolerance_pt=1.5, require_panel_labels=True, strict=True)
    save(fig, "calibration-cn")


def main_results_figure(summary: pd.DataFrame, pred: pd.DataFrame, decomp: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.5))
    fig.subplots_adjust(left=0.10, right=0.97, bottom=0.09, top=0.92, wspace=0.30, hspace=0.40)
    ax = axes[0, 0]
    for model in MODELS:
        part = pred[pred.model == model]; fpr, tpr, _ = roc_curve(part.target, part.probability)
        ax.plot(fpr, tpr, lw=1.4, color=COLORS[model], label=MODEL_CN[model])
    ax.plot([0, 1], [0, 1], "--", color="#999999", lw=0.8)
    ax.set(xlabel="假阳性率", ylabel="真阳性率", title="合并留出预测的区分能力")
    ax.legend(loc="lower right", frameon=False, fontsize=5.5)
    x = np.arange(4); offsets = {MODELS[0]: -0.11, MODELS[1]: 0.11}
    ax = axes[0, 1]
    for model in MODELS:
        part = summary.set_index(["held_out_site", "model"]).loc[[(s, model) for s in SITES]].reset_index()
        y = part.auc.to_numpy(); err = np.vstack([y - part.auc_lo, part.auc_hi - y])
        ax.errorbar(x + offsets[model], y, yerr=err, fmt="o", ms=4, capsize=2, lw=1, color=COLORS[model])
    ax.axhline(0.5, ls="--", lw=0.8, color="#999999"); ax.set_ylim(0.35, 1.02)
    ax.set_xticks(x, SHORT, fontsize=5.5); ax.set(ylabel="ROC-AUC（95% 区间）", title="区分能力随中心变化")
    ax = axes[1, 0]
    part = decomp[decomp.model == MODELS[0]].set_index("held_out_site").loc[SITES]
    base = part.source_loss_per_100.to_numpy(); prev = base + part.prevalence_component_per_100.to_numpy()
    target = part.target_loss_per_100.to_numpy()
    for i in range(4): ax.plot([i - .18, i, i + .18], [base[i], prev[i], target[i]], color="#777", lw=.9)
    ax.scatter(x - .18, base, s=20, color="#999", label="开发集折外")
    ax.scatter(x, prev, s=20, color="#4C91BF", label="仅替换患病率")
    ax.scatter(x + .18, target, s=20, color="#D96B4C", label="目标中心观察值")
    ax.set_xticks(x, SHORT, fontsize=5.5); ax.set(ylabel="每 100 条加权错误", title="逻辑回归决策损失分解")
    ax.legend(loc="upper left", fontsize=5.2, frameon=False)
    ax = axes[1, 1]
    for model in MODELS:
        part = summary.set_index(["held_out_site", "model"]).loc[[(s, model) for s in SITES]].reset_index()
        y = part.default_advantage_per_100.to_numpy(); err = np.vstack([y - part.advantage_lo, part.advantage_hi - y])
        ax.errorbar(x + offsets[model], y, yerr=err, fmt="o", ms=4, capsize=2, lw=1, color=COLORS[model])
    ax.axhline(0, color="#333", lw=.8); ax.set_xticks(x, SHORT, fontsize=5.5)
    ax.set(ylabel="相对较优默认策略的收益/100", title="决策效用具有中心特异性")
    label_panels(axes)
    require_matplotlib_panel_alignment(fig, json_out=FIG / "multisite-transport-main-cn.alignment.json",
        overlay_svg=FIG / "multisite-transport-main-cn.alignment.svg", tolerance_pt=1.5,
        gutter_tolerance_pt=1.5, require_panel_labels=True, strict=True)
    save(fig, "multisite-transport-main-cn")


def operating_figure(summary: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.4))
    fig.subplots_adjust(left=0.08, right=0.98, bottom=0.22, top=0.86, wspace=0.46)
    x = np.arange(4); offsets = {MODELS[0]: -0.11, MODELS[1]: 0.11}
    ax = axes[0]
    for model in MODELS:
        part = summary.set_index(["held_out_site", "model"]).loc[[(s, model) for s in SITES]].reset_index()
        ax.plot(x + offsets[model], part.threshold, "o", ms=4, color=COLORS[model], label=MODEL_CN[model])
    ax.axhline(1 / 6, color="#777", ls="--", lw=.8, label="理论阈值 1/6")
    ax.set_xticks(x, ["Clev.", "Hung.", "Swiss", "VA"], fontsize=5.4)
    ax.set(ylabel="冻结阈值", title="开发集选择的行动阈值"); ax.legend(fontsize=5.1, frameon=False)
    ax = axes[1]
    for site in SITES:
        for model, marker in zip(MODELS, ["o", "s"]):
            row = summary[(summary.held_out_site == site) & (summary.model == model)].iloc[0]
            ax.scatter(row.specificity, row.sensitivity, s=28, marker=marker,
                       color=SITE_COLORS[site], edgecolor="white", linewidth=.4)
    ax.set(xlim=(0, 1.03), ylim=(0, 1.03), xlabel="特异度", ylabel="灵敏度", title="外部操作点")
    for site in SITES:
        ax.plot([], [], "o", color=SITE_COLORS[site], label=SHORT[SITES.index(site)])
    ax.legend(fontsize=5.1, frameon=False, loc="lower left")
    ax = axes[2]
    rows = []
    labels = []
    for site in SITES:
        for model in MODELS:
            row = summary[(summary.held_out_site == site) & (summary.model == model)].iloc[0]
            rows.append(np.array([row.tn, row.fp, row.fn, row.tp]) / row.n)
            labels.append(f"{SHORT[SITES.index(site)]}·{'LR' if model == MODELS[0] else 'LDA'}")
    arr = np.asarray(rows); left = np.zeros(len(rows)); colors = ["#B8C1C8", "#E3A15E", "#A95A56", "#4F8A70"]
    for j, name in enumerate(["TN", "FP", "FN", "TP"]):
        ax.barh(np.arange(8), arr[:, j], left=left, color=colors[j], edgecolor="none", label=name)
        left += arr[:, j]
    ax.set_yticks(np.arange(8), labels, fontsize=5.1); ax.invert_yaxis(); ax.set_xlim(0, 1)
    ax.set(xlabel="占中心样本比例", title="混淆构成")
    ax.legend(ncol=4, fontsize=5.1, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.16))
    label_panels(axes)
    require_matplotlib_panel_alignment(fig, json_out=FIG / "operating-profile-cn.alignment.json",
        overlay_svg=FIG / "operating-profile-cn.alignment.svg", tolerance_pt=1.5,
        gutter_tolerance_pt=1.5, require_panel_labels=True, strict=True)
    save(fig, "operating-profile-cn")


def _feature_label(name: str) -> str:
    base_map = {
        "age": "年龄", "trestbps": "静息血压", "chol": "胆固醇", "thalach": "最大心率",
        "oldpeak": "ST 压低", "sex": "性别", "cp": "胸痛类型", "fbs": "空腹血糖",
        "restecg": "静息心电图", "exang": "运动性心绞痛", "slope": "ST 斜率",
        "ca": "主要血管数", "thal": "地中海贫血",
    }
    for base, cn in base_map.items():
        if name == base:
            return cn
        if name.startswith(base + "_"):
            return f"{cn}={name.split('_', 1)[1]}"
        if name.startswith("missingindicator_") and base in name:
            return f"{cn}缺失"
    return name


def coefficient_stability_figure(data: pd.DataFrame) -> None:
    rows = []
    for held_out in SITES:
        train = data[data.site != held_out]
        model = transport.pipeline("Logistic regression")
        model.fit(train[transport.NUMERIC + transport.CATEGORICAL], train.target)
        names = model.named_steps["preprocess"].get_feature_names_out()
        coefs = model.named_steps["model"].coef_[0]
        rows.append(pd.Series(coefs, index=names, name=held_out))
    coef = pd.DataFrame(rows).fillna(0)
    top = coef.abs().max(axis=0).nlargest(14).index
    shown = coef[top].T
    vmax = float(np.abs(shown.to_numpy()).max())
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    fig.subplots_adjust(left=0.25, right=0.92, bottom=0.13, top=0.89)
    im = ax.imshow(shown.to_numpy(), aspect="auto", cmap="RdBu_r", vmin=-vmax, vmax=vmax)
    ax.set_xticks(range(4), SHORT, fontsize=6)
    ax.set_yticks(range(len(shown)), [_feature_label(x) for x in shown.index], fontsize=5.6)
    ax.set_title("留一中心开发下的逻辑回归系数稳定性", fontsize=8, pad=7)
    for i in range(shown.shape[0]):
        for j in range(shown.shape[1]):
            value = shown.iat[i, j]
            color = "white" if abs(value) > 0.62 * vmax else "#222222"
            ax.text(j, i, f"{value:.2f}", ha="center", va="center", fontsize=5.1, color=color)
    cax = ax.inset_axes([1.025, 0.18, 0.035, 0.64]); cb = fig.colorbar(im, cax=cax)
    cb.set_label("回归系数", fontsize=6); cb.ax.tick_params(labelsize=5.2)
    require_matplotlib_panel_alignment(fig, json_out=FIG / "coefficient-stability-cn.alignment.json",
        overlay_svg=FIG / "coefficient-stability-cn.alignment.svg", tolerance_pt=1.5,
        gutter_tolerance_pt=1.5, require_panel_labels=False, strict=True, exclude_axes=[cax])
    save(fig, "coefficient-stability-cn")


def threshold_sensitivity_figure(pred: pd.DataFrame) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.8))
    fig.subplots_adjust(left=0.09, right=0.97, bottom=0.10, top=0.91, wspace=0.28, hspace=0.40)
    grid = np.linspace(0.01, 0.99, 199)
    for ax, site in zip(axes.flat, SITES):
        for model in MODELS:
            part = pred[(pred.held_out_site == site) & (pred.model == model)]
            y = part.target.to_numpy(); p = part.probability.to_numpy(); pi = y.mean()
            gains = []
            for threshold in grid:
                tpr, fpr, *_ = transport.rates(y, p, threshold)
                gains.append(100 * (min(transport.C_FN * pi, 1 - pi) - transport.loss(pi, tpr, fpr)))
            ax.plot(grid, gains, lw=1.2, color=COLORS[model], label=MODEL_CN[model])
            frozen = float(part.threshold.iloc[0])
            idx = int(np.argmin(abs(grid - frozen)))
            ax.scatter([frozen], [gains[idx]], s=20, color=COLORS[model], edgecolor="white", linewidth=.4, zorder=3)
        ax.axhline(0, color="#444444", lw=.8)
        ax.set(xlim=(0, 1), xlabel="候选阈值", ylabel="相对较优默认策略的收益/100", title=SHORT[SITES.index(site)])
        ax.grid(color="#ECECEC", linewidth=.5)
    axes[0, 0].legend(fontsize=5.5, frameon=False, loc="upper center",
                      bbox_to_anchor=(0.5, 1.16), ncol=2, handlelength=1.2,
                      handletextpad=0.7)
    label_panels(axes)
    require_matplotlib_panel_alignment(fig, json_out=FIG / "threshold-sensitivity-cn.alignment.json",
        overlay_svg=FIG / "threshold-sensitivity-cn.alignment.svg", tolerance_pt=1.5,
        gutter_tolerance_pt=1.5, require_panel_labels=True, strict=True)
    save(fig, "threshold-sensitivity-cn")


def discrimination_utility_plane_figure(summary: pd.DataFrame) -> None:
    """Jointly display ranking performance and decision utility with uncertainty."""
    fig, ax = plt.subplots(figsize=(7.2, 4.35))
    fig.subplots_adjust(left=0.12, right=0.96, bottom=0.16, top=0.78)

    # The four regions make the evidence logic explicit without converting
    # either axis into an arbitrary composite score.
    ax.axhspan(0, 30, color="#E8F2EA", alpha=0.72, zorder=0)
    ax.axhspan(-110, 0, color="#F7E9E6", alpha=0.64, zorder=0)
    ax.axvline(0.5, color="#777777", lw=0.8, ls="--", zorder=1)
    ax.axhline(0, color="#303030", lw=1.0, zorder=1)

    markers = {"Logistic regression": "o", "Shrinkage LDA": "s"}

    for _, row in summary.iterrows():
        site, model = row.held_out_site, row.model
        x, y = float(row.auc), float(row.default_advantage_per_100)
        xerr = np.array([[x - float(row.auc_lo)], [float(row.auc_hi) - x]])
        yerr = np.array([[y - float(row.advantage_lo)], [float(row.advantage_hi) - y]])
        color = SITE_COLORS[site]
        ax.errorbar(x, y, xerr=xerr, yerr=yerr, fmt="none", ecolor=color,
                    elinewidth=0.9, capsize=2.2, alpha=0.72, zorder=2)
        size = 30 + 0.12 * float(row.n)
        ax.scatter(x, y, s=size, marker=markers[model], color=color,
                   edgecolor="white", linewidth=0.7, zorder=3)

    ax.set_xlim(0.47, 0.98); ax.set_ylim(-110, 30)
    ax.set_xlabel("外部 ROC–AUC（横向误差线：95% bootstrap 区间）")
    ax.set_ylabel("相对较优默认策略的收益/100\n（纵向误差线：95% bootstrap 区间）")
    ax.set_title("区分能力与决策效用的联合证据平面", fontsize=8.5, pad=8)
    ax.grid(False)

    legend_items = [
        (0.12, "● Cleveland", SITE_COLORS[SITES[0]]),
        (0.26, "● Hungary", SITE_COLORS[SITES[1]]),
        (0.38, "● Switzerland", SITE_COLORS[SITES[2]]),
        (0.54, "● VA", SITE_COLORS[SITES[3]]),
        (0.66, "● 逻辑回归", "#555555"),
        (0.80, "■ 收缩 LDA", "#555555"),
    ]
    for x, label, color in legend_items:
        fig.text(x, 0.875, label, color=color, fontsize=5.5, ha="left", va="center")

    require_matplotlib_panel_alignment(fig,
        json_out=FIG / "discrimination-utility-plane-cn.alignment.json",
        overlay_svg=FIG / "discrimination-utility-plane-cn.alignment.svg",
        tolerance_pt=1.5, gutter_tolerance_pt=1.5,
        require_panel_labels=False, strict=True)
    save(fig, "discrimination-utility-plane-cn")


def main() -> None:
    configure()
    data = transport.load_data()
    summary = pd.read_csv(ANALYSIS / "external-validation-summary.csv")
    pred = pd.read_csv(ANALYSIS / "held-out-predictions.csv")
    decomp = pd.read_csv(ANALYSIS / "decision-loss-decomposition.csv")
    design_figure()
    landscape_figure(data)
    feature_distribution_figure(data)
    calibration_figure(pred)
    main_results_figure(summary, pred, decomp)
    operating_figure(summary)
    coefficient_stability_figure(data)
    threshold_sensitivity_figure(pred)
    discrimination_utility_plane_figure(summary)


if __name__ == "__main__":
    main()
