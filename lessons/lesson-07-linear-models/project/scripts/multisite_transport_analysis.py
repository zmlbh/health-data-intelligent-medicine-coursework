from __future__ import annotations

from pathlib import Path
import json
import math
import sys

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import pandas as pd
from scipy.stats import beta
from sklearn.calibration import calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score, roc_curve
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from audit_panel_alignment import require_matplotlib_panel_alignment


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw-uci"
OUT = ROOT / "research-upgrade" / "analysis"
FIG = ROOT / "research-upgrade" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

COLS = [
    "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
    "thalach", "exang", "oldpeak", "slope", "ca", "thal", "num",
]
FILES = {
    "Cleveland": "processed.cleveland.data",
    "Hungary": "processed.hungarian.data",
    "Switzerland": "processed.switzerland.data",
    "VA Long Beach": "processed.va.data",
}
NUMERIC = ["age", "trestbps", "chol", "thalach", "oldpeak"]
CATEGORICAL = ["sex", "cp", "fbs", "restecg", "exang", "slope", "ca", "thal"]
C_FN = 5.0
C_FP = 1.0
SEED = 2026


def load_data() -> pd.DataFrame:
    frames = []
    for site, filename in FILES.items():
        frame = pd.read_csv(RAW / filename, names=COLS, na_values="?")
        frame.insert(0, "site", site)
        frame["target"] = (pd.to_numeric(frame["num"], errors="coerce") > 0).astype(int)
        frames.append(frame.drop(columns="num"))
    return pd.concat(frames, ignore_index=True)


def pipeline(model: str) -> Pipeline:
    pre = ColumnTransformer(
        [
            (
                "num",
                Pipeline([
                    ("impute", SimpleImputer(strategy="median", add_indicator=True)),
                    ("scale", StandardScaler()),
                ]),
                NUMERIC,
            ),
            (
                "cat",
                Pipeline([
                    ("impute", SimpleImputer(strategy="most_frequent")),
                    ("encode", OneHotEncoder(handle_unknown="ignore", drop="if_binary", sparse_output=False)),
                ]),
                CATEGORICAL,
            ),
        ],
        verbose_feature_names_out=False,
    )
    if model == "Logistic regression":
        estimator = LogisticRegression(C=1.0, max_iter=5000, random_state=SEED)
    elif model == "Shrinkage LDA":
        estimator = LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")
    else:
        raise ValueError(model)
    return Pipeline([("preprocess", pre), ("model", estimator)])


def rates(y: np.ndarray, p: np.ndarray, threshold: float) -> tuple[float, float, int, int, int, int]:
    pred = p >= threshold
    tp = int(np.sum((pred == 1) & (y == 1)))
    fp = int(np.sum((pred == 1) & (y == 0)))
    fn = int(np.sum((pred == 0) & (y == 1)))
    tn = int(np.sum((pred == 0) & (y == 0)))
    tpr = tp / (tp + fn) if tp + fn else np.nan
    fpr = fp / (fp + tn) if fp + tn else np.nan
    return tpr, fpr, tp, fp, fn, tn


def loss(pi: float, tpr: float, fpr: float) -> float:
    return C_FN * pi * (1 - tpr) + C_FP * (1 - pi) * fpr


def select_threshold(y: np.ndarray, p: np.ndarray) -> float:
    candidates = np.unique(np.r_[0.01, np.linspace(0.02, 0.98, 193), 0.99, p])
    observed = []
    for threshold in candidates:
        _, _, _, fp, fn, _ = rates(y, p, threshold)
        observed.append((C_FN * fn + C_FP * fp, threshold))
    return float(min(observed, key=lambda x: (x[0], abs(x[1] - 1 / 6)))[1])


def cp_interval(k: int, n: int, alpha: float) -> tuple[float, float]:
    lo = 0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k))
    return lo, hi


def decision_certificate(y: np.ndarray, p: np.ndarray, threshold: float) -> dict[str, float | bool]:
    """Conservative rectangular 95% confidence set for prevalence, TPR and FPR.

    Bonferroni alpha/3 intervals are used. The reported upper regret is the
    worst model loss minus the better default action over the confidence box.
    A negative value certifies improvement over both defaults within that box.
    """
    tpr, fpr, tp, fp, fn, tn = rates(y, p, threshold)
    alpha_each = 0.05 / 3
    pi_lo, pi_hi = cp_interval(tp + fn, len(y), alpha_each)
    tpr_lo, tpr_hi = cp_interval(tp, tp + fn, alpha_each)
    fpr_lo, fpr_hi = cp_interval(fp, fp + tn, alpha_each)
    pi_grid = np.linspace(pi_lo, pi_hi, 1001)
    regret = np.array([
        loss(pi, tpr_lo, fpr_hi) - min(C_FN * pi, C_FP * (1 - pi))
        for pi in pi_grid
    ])
    return {
        "pi_lo": pi_lo,
        "pi_hi": pi_hi,
        "tpr_lo": tpr_lo,
        "tpr_hi": tpr_hi,
        "fpr_lo": fpr_lo,
        "fpr_hi": fpr_hi,
        "upper_regret": float(regret.max()),
        "certified": bool(regret.max() < 0),
    }


def bootstrap_metrics(y: np.ndarray, p: np.ndarray, threshold: float, rng: np.random.Generator) -> dict[str, tuple[float, float]]:
    stats = {"auc": [], "brier": [], "loss": [], "advantage": []}
    pos = np.where(y == 1)[0]
    neg = np.where(y == 0)[0]
    for _ in range(1000):
        idx = np.r_[rng.choice(pos, len(pos), replace=True), rng.choice(neg, len(neg), replace=True)]
        yy, pp = y[idx], p[idx]
        tpr, fpr, *_ = rates(yy, pp, threshold)
        pi = yy.mean()
        model_loss = loss(pi, tpr, fpr)
        stats["auc"].append(roc_auc_score(yy, pp))
        stats["brier"].append(brier_score_loss(yy, pp))
        stats["loss"].append(model_loss)
        stats["advantage"].append(min(C_FN * pi, 1 - pi) - model_loss)
    return {key: tuple(np.quantile(value, [0.025, 0.975])) for key, value in stats.items()}


def analyse(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(SEED)
    rows = []
    predictions = []
    decompositions = []
    X_cols = NUMERIC + CATEGORICAL
    for held_out in FILES:
        train = data[data.site != held_out].reset_index(drop=True)
        test = data[data.site == held_out].reset_index(drop=True)
        X_train, y_train = train[X_cols], train.target.to_numpy()
        X_test, y_test = test[X_cols], test.target.to_numpy()
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
        for model_name in ["Logistic regression", "Shrinkage LDA"]:
            model = pipeline(model_name)
            oof = cross_val_predict(model, X_train, y_train, cv=cv, method="predict_proba", n_jobs=-1)[:, 1]
            threshold = select_threshold(y_train, oof)
            model.fit(X_train, y_train)
            p_test = model.predict_proba(X_test)[:, 1]
            src_tpr, src_fpr, *_ = rates(y_train, oof, threshold)
            tgt_tpr, tgt_fpr, tp, fp, fn, tn = rates(y_test, p_test, threshold)
            pi_src, pi_tgt = y_train.mean(), y_test.mean()
            l_src = loss(pi_src, src_tpr, src_fpr)
            l_prev = loss(pi_tgt, src_tpr, src_fpr)
            l_tgt = loss(pi_tgt, tgt_tpr, tgt_fpr)
            ci = bootstrap_metrics(y_test, p_test, threshold, rng)
            cert = decision_certificate(y_test, p_test, threshold)
            advantage = min(C_FN * pi_tgt, 1 - pi_tgt) - l_tgt
            rows.append({
                "held_out_site": held_out,
                "model": model_name,
                "n": len(test),
                "events": int(y_test.sum()),
                "prevalence": pi_tgt,
                "threshold": threshold,
                "auc": roc_auc_score(y_test, p_test),
                "auc_lo": ci["auc"][0],
                "auc_hi": ci["auc"][1],
                "brier": brier_score_loss(y_test, p_test),
                "brier_lo": ci["brier"][0],
                "brier_hi": ci["brier"][1],
                "sensitivity": tgt_tpr,
                "specificity": 1 - tgt_fpr,
                "tp": tp, "fp": fp, "fn": fn, "tn": tn,
                "weighted_loss_per_100": 100 * l_tgt,
                "loss_lo": 100 * ci["loss"][0],
                "loss_hi": 100 * ci["loss"][1],
                "default_advantage_per_100": 100 * advantage,
                "advantage_lo": 100 * ci["advantage"][0],
                "advantage_hi": 100 * ci["advantage"][1],
                **cert,
            })
            decompositions.append({
                "held_out_site": held_out,
                "model": model_name,
                "source_loss_per_100": 100 * l_src,
                "prevalence_component_per_100": 100 * (l_prev - l_src),
                "conditional_component_per_100": 100 * (l_tgt - l_prev),
                "target_loss_per_100": 100 * l_tgt,
            })
            for i, (yy, pp) in enumerate(zip(y_test, p_test)):
                predictions.append({
                    "held_out_site": held_out,
                    "model": model_name,
                    "row_in_site": i,
                    "target": int(yy),
                    "probability": float(pp),
                    "threshold": threshold,
                })
    return pd.DataFrame(rows), pd.DataFrame(predictions), pd.DataFrame(decompositions)


def make_figure(summary: pd.DataFrame, pred: pd.DataFrame, decomp: pd.DataFrame) -> None:
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "DejaVu Sans", "sans-serif"],
        "font.size": 7,
        "axes.titlesize": 8,
        "axes.labelsize": 7,
        "axes.linewidth": 0.7,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
    })
    sites = list(FILES)
    models = ["Logistic regression", "Shrinkage LDA"]
    colors = {"Logistic regression": "#2F6B9A", "Shrinkage LDA": "#D17A22"}
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.5), constrained_layout=True)

    ax = axes[0, 0]
    for model in models:
        part = pred[pred.model == model]
        fpr_all, tpr_all, _ = roc_curve(part.target, part.probability)
        ax.plot(fpr_all, tpr_all, lw=1.5, color=colors[model], label=model)
    ax.plot([0, 1], [0, 1], color="#9A9A9A", lw=0.8, ls="--")
    ax.set(xlabel="False-positive rate", ylabel="True-positive rate", title="Pooled held-out discrimination")
    ax.legend(loc="lower right")

    ax = axes[0, 1]
    offsets = {models[0]: -0.11, models[1]: 0.11}
    x = np.arange(len(sites))
    for model in models:
        part = summary.set_index(["held_out_site", "model"]).loc[[(s, model) for s in sites]].reset_index()
        y = part.auc.to_numpy()
        err = np.vstack([y - part.auc_lo.to_numpy(), part.auc_hi.to_numpy() - y])
        ax.errorbar(x + offsets[model], y, yerr=err, fmt="o", ms=4, capsize=2, lw=1,
                    color=colors[model], label=model)
    ax.set_xticks(x, ["Cleveland", "Hungary", "Switzerland", "VA"])
    ax.set_ylim(0.35, 1.02)
    ax.axhline(0.5, color="#9A9A9A", lw=0.8, ls="--")
    ax.set(ylabel="ROC-AUC (95% bootstrap CI)", title="Transportability varies by centre")

    ax = axes[1, 0]
    logistic = decomp[decomp.model == "Logistic regression"].set_index("held_out_site").loc[sites]
    base = logistic.source_loss_per_100.to_numpy()
    after_prev = base + logistic.prevalence_component_per_100.to_numpy()
    target = logistic.target_loss_per_100.to_numpy()
    for i in range(len(sites)):
        ax.plot([i - 0.18, i, i + 0.18], [base[i], after_prev[i], target[i]],
                color="#777777", lw=0.9, zorder=1)
    ax.scatter(x - 0.18, base, color="#9A9A9A", s=20, label="Source validation", zorder=2)
    ax.scatter(x, after_prev, color="#4C91BF", s=20, label="After prevalence shift", zorder=2)
    ax.scatter(x + 0.18, target, color="#D96B4C", s=20, label="Observed target", zorder=2)
    ax.set_xticks(x, ["Cleveland", "Hungary", "Switzerland", "VA"])
    ax.set(ylabel="Weighted errors per 100", title="Decision-loss decomposition (logistic)")
    ax.legend(fontsize=6, ncol=1, loc="upper left")

    ax = axes[1, 1]
    for model in models:
        part = summary.set_index(["held_out_site", "model"]).loc[[(s, model) for s in sites]].reset_index()
        y = part.default_advantage_per_100.to_numpy()
        err = np.vstack([y - part.advantage_lo.to_numpy(), part.advantage_hi.to_numpy() - y])
        ax.errorbar(x + offsets[model], y, yerr=err, fmt="o", ms=4, capsize=2, lw=1,
                    color=colors[model], label=model)
    ax.axhline(0, color="#333333", lw=0.8)
    ax.set_xticks(x, ["Cleveland", "Hungary", "Switzerland", "VA"])
    ax.set(ylabel="Gain vs better default per 100", title="Decision utility is centre-specific")

    for label, ax in zip("abcd", axes.flat):
        ax.text(-0.13, 1.06, label, transform=ax.transAxes, fontsize=9, fontweight="bold", va="top")
    require_matplotlib_panel_alignment(
        fig,
        json_out=FIG / "multisite-transport-main.alignment.json",
        overlay_svg=FIG / "multisite-transport-main.alignment.svg",
        tolerance_pt=1.5,
        gutter_tolerance_pt=1.5,
        require_panel_labels=True,
        strict=True,
    )
    fig.savefig(FIG / "multisite-transport-main.pdf", bbox_inches="tight")
    fig.savefig(FIG / "multisite-transport-main.svg", bbox_inches="tight")
    fig.savefig(FIG / "multisite-transport-main.png", dpi=600, bbox_inches="tight")
    fig.savefig(FIG / "multisite-transport-main.tiff", dpi=600, bbox_inches="tight")
    plt.close(fig)


def _save_figure_bundle(fig: plt.Figure, stem: str) -> None:
    fig.savefig(FIG / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(FIG / f"{stem}.svg", bbox_inches="tight")
    fig.savefig(FIG / f"{stem}.png", dpi=600, bbox_inches="tight")
    fig.savefig(FIG / f"{stem}.tiff", dpi=600, bbox_inches="tight")


def make_design_figure() -> None:
    fig, ax = plt.subplots(figsize=(7.2, 2.25), constrained_layout=True)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    boxes = [
        (0.02, 0.34, 0.14, 0.34, "Four centres\n920 records", "#E8EEF3"),
        (0.20, 0.34, 0.15, 0.34, "Hold out\none centre", "#DDEBF5"),
        (0.39, 0.34, 0.16, 0.34, "Fold-fitted\npreprocessing", "#E8EEF3"),
        (0.59, 0.34, 0.16, 0.34, "Logistic + LDA\nCV threshold", "#F7E8D5"),
        (0.79, 0.34, 0.19, 0.34, "External audit\nrank • probability\nloss • certificate", "#E7F1E8"),
    ]
    for x, y, w, h, label, color in boxes:
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.018",
                             facecolor=color, edgecolor="#4A4A4A", linewidth=0.8)
        ax.add_patch(box)
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=7, linespacing=1.25)
    for i in range(len(boxes) - 1):
        x1 = boxes[i][0] + boxes[i][2]
        x2 = boxes[i + 1][0]
        arrow = FancyArrowPatch((x1 + 0.007, 0.51), (x2 - 0.007, 0.51), arrowstyle="-|>",
                                mutation_scale=9, color="#5A5A5A", linewidth=0.9)
        ax.add_patch(arrow)
    ax.text(0.275, 0.19, "Repeat four times; the target centre never enters development",
            ha="center", va="center", fontsize=6.5, color="#3F5F75")
    ax.text(0.89, 0.19, "5FN + FP; frozen before target evaluation",
            ha="center", va="center", fontsize=6.5, color="#6C542F")
    require_matplotlib_panel_alignment(
        fig,
        json_out=FIG / "study-design.alignment.json",
        overlay_svg=FIG / "study-design.alignment.svg",
        tolerance_pt=1.5,
        gutter_tolerance_pt=1.5,
        require_panel_labels=False,
        strict=True,
    )
    _save_figure_bundle(fig, "study-design")
    plt.close(fig)


def make_data_landscape_figure(data: pd.DataFrame) -> None:
    sites = list(FILES)
    short_sites = ["Cleveland", "Hungary", "Switzerland", "VA"]
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.0))
    fig.subplots_adjust(left=0.08, right=0.95, bottom=0.20, top=0.84, wspace=0.85)

    ax = axes[0]
    counts = data.groupby(["site", "target"]).size().unstack(fill_value=0).loc[sites]
    y = np.arange(len(sites))
    ax.barh(y, counts[0], color="#B8C1C8", label="Negative", edgecolor="none", linewidth=0)
    ax.barh(y, counts[1], left=counts[0], color="#C86B4A", label="Positive", edgecolor="none", linewidth=0)
    for i, site in enumerate(sites):
        n = int(counts.loc[site].sum())
        pi = counts.loc[site, 1] / n
        ax.text(n - 7, i, f"n={n}\np={pi:.2f}", va="center", ha="right",
                fontsize=5.0, linespacing=1.25, fontweight="semibold", color="white")
    ax.set_yticks(y, short_sites, fontsize=6)
    ax.invert_yaxis()
    ax.set_xlabel("Records", fontsize=6.5)
    ax.set_title("Outcome composition", fontsize=7.5, pad=5)
    ax.tick_params(axis="x", labelsize=5.5)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.19), ncol=2,
              fontsize=5.3, frameon=False, handlelength=1.2, columnspacing=0.8)
    ax.set_xlim(0, 370)

    ax = axes[1]
    miss = data.groupby("site")[NUMERIC + CATEGORICAL].apply(lambda frame: frame.isna().mean()).loc[sites]
    im = ax.imshow(miss.to_numpy().T, aspect="auto", cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(np.arange(4), ["Clev.", "Hung.", "Swiss", "VA"], fontsize=5.5)
    display_features = ["Age", "Resting BP", "Cholesterol", "Max heart rate", "ST depression",
                        "Sex", "Chest pain", "Fasting glucose", "Resting ECG", "Exercise angina",
                        "ST slope", "Major vessels", "Thal"]
    ax.set_yticks(np.arange(len(display_features)), display_features, fontsize=5.8)
    ax.set_title("Missing values by centre", fontsize=7.5, pad=5)
    cax = ax.inset_axes([1.035, 0.24, 0.045, 0.56])
    cbar = fig.colorbar(im, cax=cax)
    cbar.set_label("Missing fraction", fontsize=6)
    cbar.ax.tick_params(labelsize=5.5)

    ax = axes[2]
    numeric = data[NUMERIC].copy()
    standardized = (numeric - numeric.mean()) / numeric.std(ddof=0)
    standardized["site"] = data.site
    means = standardized.groupby("site")[NUMERIC].mean().loc[sites]
    vmax = max(abs(means.min().min()), abs(means.max().max()))
    im2 = ax.imshow(means.to_numpy().T, aspect="auto", cmap="RdBu_r", vmin=-vmax, vmax=vmax)
    ax.set_xticks(np.arange(4), ["Clev.", "Hung.", "Swiss", "VA"], fontsize=5.5)
    ax.set_yticks(np.arange(5), ["Age", "Resting BP", "Cholesterol", "Max heart rate", "ST depression"], fontsize=5.8)
    ax.set_title("Standardized numeric means", fontsize=7.5, pad=5)
    cax2 = ax.inset_axes([1.035, 0.24, 0.045, 0.56])
    cbar2 = fig.colorbar(im2, cax=cax2)
    cbar2.set_label("Pooled SD", fontsize=6)
    cbar2.ax.tick_params(labelsize=5.5)

    for label, ax in zip("abc", axes):
        ax.text(-0.08, 1.12, label, transform=ax.transAxes, fontsize=8,
                fontweight="bold", va="top", ha="right")
    require_matplotlib_panel_alignment(
        fig,
        json_out=FIG / "data-landscape.alignment.json",
        overlay_svg=FIG / "data-landscape.alignment.svg",
        tolerance_pt=1.5,
        gutter_tolerance_pt=1.5,
        require_panel_labels=True,
        strict=True,
        exclude_axes=[cbar.ax, cbar2.ax],
    )
    _save_figure_bundle(fig, "data-landscape")
    plt.close(fig)


def main() -> None:
    data = load_data()
    summary, predictions, decompositions = analyse(data)
    summary.to_csv(OUT / "external-validation-summary.csv", index=False)
    predictions.to_csv(OUT / "held-out-predictions.csv", index=False)
    decompositions.to_csv(OUT / "decision-loss-decomposition.csv", index=False)
    site_summary = data.groupby("site").agg(
        n=("target", "size"), events=("target", "sum"), prevalence=("target", "mean")
    ).reset_index()
    missing = data.groupby("site")[NUMERIC + CATEGORICAL].apply(lambda x: x.isna().mean()).reset_index()
    site_summary.to_csv(OUT / "site-summary.csv", index=False)
    missing.to_csv(OUT / "site-missingness.csv", index=False)
    make_design_figure()
    make_data_landscape_figure(data)
    make_figure(summary, predictions, decompositions)
    result = {
        "n_total": int(len(data)),
        "events": int(data.target.sum()),
        "sites": site_summary.to_dict(orient="records"),
        "certified_count": int(summary.certified.sum()),
        "evaluations": int(len(summary)),
    }
    (OUT / "analysis-summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(summary[["held_out_site", "model", "auc", "brier", "weighted_loss_per_100",
                   "default_advantage_per_100", "advantage_lo", "advantage_hi", "certified"]].to_string(index=False))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
