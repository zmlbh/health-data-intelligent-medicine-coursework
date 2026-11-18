"""
Complete PBL analysis for homework6 / Lecture 6: ML basics & Naive Bayes.
Publication-quality figures in Nature Medicine / Lancet Digital Health style.
"""
import sys, os, json, warnings
from pathlib import Path
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from sklearn.naive_bayes import BernoulliNB
from sklearn.metrics import (confusion_matrix, roc_curve, precision_recall_curve,
                             roc_auc_score, average_precision_score, log_loss,
                             brier_score_loss)

# Nature Medicine / Lancet Digital Health style
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 9,
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.labelsize": 10,
    "axes.titlesize": 10.5,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "xtick.major.width": 0.8,
    "ytick.major.width": 0.8,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "figure.dpi": 150,
    "savefig.dpi": 600,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.15,
    "legend.frameon": False,
    "legend.fontsize": 8.5,
    "axes.grid": True,
    "grid.alpha": 0.2,
    "grid.linestyle": "-",
    "grid.linewidth": 0.5,
})

# Nature color palette (muted, colorblind-friendly)
C_BLUE = "#2166AC"
C_RED = "#B2182B"
C_GREEN = "#4DAF4A"
C_PURPLE = "#984EA3"
C_ORANGE = "#FF7F00"
C_GRAY = "#636363"
C_LBLUE = "#92C5DE"
C_LRED = "#F4A582"

BASE = Path(r"C:\Users\zml\Documents\Codex\2026-09-16\ctrl-cmd-shift-p-python-create-2\homework6\7. Naive-Bayes")
FIG = BASE / "review" / "render-student"
FIG.mkdir(parents=True, exist_ok=True)

FEATURES = ["fever_ge_38","nausea","lumbar_pain","urine_pushing","micturition_pain","burning_urethra"]
F_LABELS = ["Fever\n>=38C","Nausea","Lumbar\npain","Urinary\nurgency","Micturition\npain","Urethral\nburning"]
TARGET = "bladder_inflammation"

train = pd.read_csv(BASE/"data/student/train.csv")
valid = pd.read_csv(BASE/"data/student/validation.csv")
test_feat = pd.read_csv(BASE/"data/student/locked-test-features.csv")
test_lab = pd.read_csv(BASE/"data/teacher/locked-test-labels.csv")
test = test_feat.merge(test_lab[["sample_id", TARGET]], on="sample_id")

print(f"train={len(train)} valid={len(valid)} test={len(test)}")

model = BernoulliNB(alpha=1.0, binarize=None).fit(train[FEATURES], train[TARGET])
prior = model.class_log_prior_.copy()
theta = np.exp(model.feature_log_prob_)

x = np.array([0,0,0,1,1,1])
p_hand = model.predict_proba(x.reshape(1,-1))[0,1]

rows = []
for ci, label in enumerate([0,1]):
    part = train[train[TARGET]==label]
    for j, f in enumerate(FEATURES):
        cnt = int(part[f].sum())
        theta_val = (cnt+1)/(len(part)+2)
        term = theta_val if x[j]==1 else (1-theta_val)
        rows.append(dict(label=label, feature=f, xj=int(x[j]), count_one=cnt,
                         theta=theta_val, likelihood=term))
hand_df = pd.DataFrame(rows)

p_train = model.predict_proba(train[FEATURES])[:,1]
p_valid = model.predict_proba(valid[FEATURES])[:,1]
p_test  = model.predict_proba(test[FEATURES])[:,1]
base_p = train[TARGET].mean()
p_base_valid = np.full(len(valid), base_p)

def eval_metrics(y, p, th=0.5):
    y = np.asarray(y); pred = p >= th
    tn,fp,fn,tp = confusion_matrix(y, pred, labels=[0,1]).ravel()
    def r(a,b): return a/b if b else float("nan")
    sens = r(tp,tp+fn); spec = r(tn,tn+fp)
    ppv = r(tp,tp+fp)
    npv = r(tn,tn+fn)
    lr_pos = r(sens, 1-spec) if (1-spec) > 0 else float("inf")
    lr_neg = r(1-sens, spec) if spec > 0 else float("inf")
    return dict(tn=int(tn),fp=int(fp),fn=int(fn),tp=int(tp),
                accuracy=r(tp+tn,len(y)), sensitivity=sens,
                specificity=spec, precision=ppv, npv=npv,
                lr_pos=lr_pos, lr_neg=lr_neg,
                f1=r(2*tp,2*tp+fp+fn),
                roc_auc=roc_auc_score(y,p), log_loss=log_loss(y,p,labels=[0,1]),
                brier=brier_score_loss(y,p))

res_train = eval_metrics(train[TARGET], p_train)
res_valid = eval_metrics(valid[TARGET], p_valid)
res_base  = eval_metrics(valid[TARGET], p_base_valid)
res_test  = eval_metrics(test[TARGET], p_test)

THS = [0.05,0.1,0.2,0.3,0.5,0.7,0.8,0.9,0.95]
th_rows = []
for t in THS:
    m = eval_metrics(valid[TARGET], p_valid, t)
    th_rows.append(dict(threshold=t, fp=m["fp"], fn=m["fn"],
                        sensitivity=m["sensitivity"], specificity=m["specificity"]))
th_df = pd.DataFrame(th_rows)
elig = th_df[th_df.sensitivity>=0.9]
chosen = elig.sort_values(["specificity","threshold"], ascending=[False,True]).iloc[0]
chosen_t = float(chosen.threshold)

# FIG 1: Study workflow (CONSORT-style, black/gray/white, as in Gadalla et al. 2019 Sci Rep)
fig, ax = plt.subplots(figsize=(6.5, 6.0))
ax.set_xlim(0,10); ax.set_ylim(0,12); ax.axis("off")

def draw_box(x, y, w, h, text, fc="white", ec="#333333", fs=8.5, bold=True):
    ax.add_patch(FancyBboxPatch((x,y),w,h, boxstyle="round,pad=0.05",
                                 facecolor=fc, edgecolor=ec, linewidth=1.0))
    ax.text(x+w/2, y+h/2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", color="#222222")

def draw_arrow(x1, y1, x2, y2):
    ax.annotate("", xy=(x2,y2), xytext=(x1,y1),
                arrowprops=dict(arrowstyle="->", lw=1.0, color="#444444"))

# Top: source data
draw_box(2.5, 10.5, 5, 1.0, "UCI Acute Inflammations\nn = 120 records", "#F0F0F0")
draw_arrow(5, 10.5, 5, 9.8)

# Feature engineering
draw_box(2.0, 8.5, 6, 1.0, "Feature engineering\n6 binary symptoms (fever, nausea, lumbar pain, urgency, dysuria, urethral burning)", "#F8F8F8", fs=7.5)
draw_arrow(5, 8.5, 5, 7.8)

# Data split header
draw_box(3.0, 6.8, 4, 0.7, "Data split (stratified 6:2:2)", "#E0E0E0", fs=9)
draw_arrow(5, 6.8, 1.7, 6.0)
draw_arrow(5, 6.8, 5, 6.0)
draw_arrow(5, 6.8, 8.3, 6.0)

# Three arms
draw_box(0.3, 4.8, 2.8, 1.2, "Training set\nn = 72\n(37 neg, 35 pos)", "#FFFFFF", fs=8)
draw_box(3.6, 4.8, 2.8, 1.2, "Validation set\nn = 24\n(12 neg, 12 pos)", "#FFFFFF", fs=8)
draw_box(6.9, 4.8, 2.8, 1.2, "Test set\nn = 24\n(12 neg, 12 pos)", "#FFFFFF", fs=8)

draw_arrow(1.7, 4.8, 1.7, 3.8)
draw_arrow(5, 4.8, 5, 3.8)
draw_arrow(8.3, 4.8, 8.3, 3.8)

# What each does
draw_box(0.3, 2.6, 2.8, 1.2, "Model training\nBernoulli NB\n(alpha = 1)", "#F5F5F5", fs=7.5)
draw_box(3.6, 2.6, 2.8, 1.2, "Threshold selection\nsensitivity >= 0.90\nmaximize specificity", "#F5F5F5", fs=7.5)
draw_box(6.9, 2.6, 2.8, 1.2, "Final evaluation\nno further tuning\nmetrics once", "#F5F5F5", fs=7.5)

# Side annotation
ax.text(0.1, 1.5, "Model: Bernoulli Naive Bayes\nOutcome: Bladder inflammation (binary)",
        fontsize=7.5, color="#555555", va="top", style="italic")

ax.text(5, 11.6, "Figure 1. Study workflow and data partitioning", ha="center", fontsize=10, fontweight="bold")
plt.savefig(FIG/"fig1_workflow.png", facecolor="white")
plt.close()

# FIG 2: Conditional probabilities (bar + heatmap difference)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.8), gridspec_kw={"width_ratios": [1.2, 1]})
xpos = np.arange(len(FEATURES))
w = 0.35
bars1 = ax1.bar(xpos-w/2, theta[0], w, label="Negative (Y=0)", color=C_LBLUE, edgecolor=C_BLUE, linewidth=0.8)
bars2 = ax1.bar(xpos+w/2, theta[1], w, label="Positive (Y=1)", color=C_LRED, edgecolor=C_RED, linewidth=0.8)
ax1.set_xticks(xpos); ax1.set_xticklabels(F_LABELS, fontsize=7.5)
ax1.set_ylabel("P(X_j = 1 | Y = c)", fontsize=9)
ax1.set_title("a  Class-conditional symptom probabilities", fontsize=9.5, fontweight="bold", loc="left")
ax1.legend(loc="upper right", fontsize=8)
ax1.set_ylim(0,1.1)
for bar in bars1:
    h = bar.get_height()
    ax1.text(bar.get_x()+bar.get_width()/2, h+0.02, f"{h:.2f}", ha="center", fontsize=6.5, color=C_BLUE)
for bar in bars2:
    h = bar.get_height()
    ax1.text(bar.get_x()+bar.get_width()/2, h+0.02, f"{h:.2f}", ha="center", fontsize=6.5, color=C_RED)

diff = theta[1] - theta[0]
im = ax2.imshow(diff.reshape(1,-1), cmap="RdBu_r", aspect="auto", vmin=-0.5, vmax=0.5)
ax2.set_xticks(range(len(FEATURES)))
ax2.set_xticklabels([f.split("\n")[0] for f in F_LABELS], rotation=45, ha="right", fontsize=7)
ax2.set_yticks([0]); ax2.set_yticklabels(["Delta P\n(pos - neg)"], fontsize=8)
ax2.set_title("b  Probability difference", fontsize=9.5, fontweight="bold", loc="left")
for j in range(len(FEATURES)):
    color = "white" if abs(diff[j]) > 0.25 else "black"
    ax2.text(j, 0, f"{diff[j]:+.2f}", ha="center", va="center", fontsize=7.5, fontweight="bold", color=color)
plt.colorbar(im, ax=ax2, fraction=0.046, pad=0.04)
plt.tight_layout()
plt.savefig(FIG/"fig2_theta.png", facecolor="white")
plt.close()

# FIG 3: ROC + PR curves
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.5, 3.8))
fpr, tpr, _ = roc_curve(valid[TARGET], p_valid)
prec, rec, _ = precision_recall_curve(valid[TARGET], p_valid)
ax1.plot(fpr, tpr, color=C_BLUE, lw=2, label=f"NB  (AUC = {roc_auc_score(valid[TARGET],p_valid):.3f})")
ax1.plot([0,1],[0,1],"--",color="#BDBDBD",lw=1,label="Chance")
ax1.fill_between(fpr, tpr, alpha=0.15, color=C_BLUE)
ax1.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=9)
ax1.set_ylabel("True Positive Rate (Sensitivity)", fontsize=9)
ax1.set_title("a  ROC curve (validation set)", fontsize=9.5, fontweight="bold", loc="left")
ax1.legend(fontsize=8, loc="lower right")
ax1.set_xlim(-0.02,1.02); ax1.set_ylim(-0.02,1.02)

ap = average_precision_score(valid[TARGET], p_valid)
ax2.plot(rec, prec, color=C_GREEN, lw=2, label=f"NB  (AP = {ap:.3f})")
ax2.axhline(base_p, color="#BDBDBD", ls="--", lw=1, label=f"Baseline = {base_p:.3f}")
ax2.fill_between(rec, prec, alpha=0.15, color=C_GREEN)
ax2.set_xlabel("Recall (Sensitivity)", fontsize=9)
ax2.set_ylabel("Precision", fontsize=9)
ax2.set_title("b  Precision-Recall curve", fontsize=9.5, fontweight="bold", loc="left")
ax2.legend(fontsize=8, loc="lower left")
ax2.set_xlim(-0.02,1.02); ax2.set_ylim(-0.02,1.02)
plt.tight_layout()
plt.savefig(FIG/"fig3_roc_pr.png", facecolor="white")
plt.close()

# FIG 4: Confusion matrix
pred_test = p_test >= chosen_t
cm = confusion_matrix(test[TARGET], pred_test, labels=[0,1])
fig, ax = plt.subplots(figsize=(4.2, 3.8))
colors = [["#E8F5E9", "#FFF3E0"], ["#FFEBEE", "#E8F5E9"]]
for i in range(2):
    for j in range(2):
        ax.add_patch(plt.Rectangle((j,1-i),1,1, facecolor=colors[i][j], edgecolor="white", linewidth=3))
        ax.text(j+0.5, 1-i+0.5, str(cm[i][j]), ha="center", va="center",
                fontsize=24, fontweight="bold", color="#263238")
ax.set_xticks([0.5,1.5]); ax.set_xticklabels(["Predicted Negative","Predicted Positive"], fontsize=9)
ax.set_yticks([0.5,1.5]); ax.set_yticklabels(["True Negative","True Positive"], fontsize=9)
ax.set_xlim(0,2); ax.set_ylim(0,2)
ax.grid(False)
ax.set_title(f"Figure 4. Confusion matrix (test set, n=24, threshold={chosen_t:.2f})",
             fontsize=9.5, fontweight="bold", pad=12)
plt.tight_layout()
plt.savefig(FIG/"fig4_confusion.png", facecolor="white")
plt.close()

# FIG 5: Threshold sensitivity vs specificity
fig, ax = plt.subplots(figsize=(7, 3.8))
ax.plot(th_df.threshold, th_df.sensitivity, "o-", color=C_RED,
        lw=1.8, markersize=6, markeredgecolor="white", markeredgewidth=1.2, label="Sensitivity")
ax.plot(th_df.threshold, th_df.specificity, "s-", color=C_BLUE,
        lw=1.8, markersize=6, markeredgecolor="white", markeredgewidth=1.2, label="Specificity")
ax.axvline(chosen_t, color=C_ORANGE, ls="--", lw=1.5, alpha=0.8)
ax.annotate(f"Selected threshold\nt = {chosen_t:.2f}", xy=(chosen_t,0.5), fontsize=8,
            xytext=(chosen_t+0.12,0.3), color=C_ORANGE, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=C_ORANGE, lw=1))
ax.set_xlabel("Classification threshold", fontsize=9)
ax.set_ylabel("Score", fontsize=9)
ax.set_title("Figure 5. Sensitivity and specificity across thresholds (validation set)",
             fontsize=9.5, fontweight="bold", pad=10)
ax.legend(fontsize=8.5, loc="center left")
ax.set_ylim(0,1.05)
plt.tight_layout()
plt.savefig(FIG/"fig5_threshold.png", facecolor="white")
plt.close()

# FIG 6: Reliability diagram
bins = [0,0.2,0.4,0.6,0.8,1.0]
df_rel = pd.DataFrame({"y":valid[TARGET],"p":p_valid})
df_rel["bin"] = pd.cut(df_rel.p, bins=bins, include_lowest=True)
rel = df_rel.groupby("bin", observed=True).agg(
    n=("y","size"), mean_p=("p","mean"), obs=("y","mean")).reset_index()
fig, ax = plt.subplots(figsize=(4.8, 4.5))
ax.plot([0,1],[0,1],"--",color="#BDBDBD",lw=1.2,label="Perfect calibration")
ax.plot(rel.mean_p, rel.obs, "o-", color=C_PURPLE, lw=1.8,
        markersize=8, markeredgecolor="white", markeredgewidth=1.2, label="NB model")
for _,r in rel.iterrows():
    if r.n > 0:
        ax.annotate(f"n={int(r.n)}", (r.mean_p, r.obs), fontsize=7.5,
                    xytext=(8,8), textcoords="offset points", color=C_PURPLE)
ax.set_xlabel("Mean predicted probability", fontsize=9)
ax.set_ylabel("Observed positive fraction", fontsize=9)
ax.set_title("Figure 6. Reliability diagram (validation set)", fontsize=9.5, fontweight="bold", pad=10)
ax.legend(fontsize=8, loc="upper left")
ax.set_xlim(0,1); ax.set_ylim(0,1)
plt.tight_layout()
plt.savefig(FIG/"fig6_reliability.png", facecolor="white")
plt.close()

# FIG 7: Class imbalance + accuracy paradox
fig, axes = plt.subplots(1,2, figsize=(8.5, 3.5))
neg_count = (train[TARGET]==0).sum(); pos_count = (train[TARGET]==1).sum()
bars = axes[0].bar(["Negative","Positive"], [neg_count,pos_count],
                   color=[C_LBLUE, C_LRED], edgecolor=[C_BLUE,C_RED], linewidth=1.2, width=0.55)
axes[0].set_title("a  Training set class distribution", fontsize=9, fontweight="bold", loc="left")
for bar,v in zip(bars,[neg_count,pos_count]):
    axes[0].text(bar.get_x()+bar.get_width()/2, v+0.8, str(v), ha="center", fontweight="bold", fontsize=9)
axes[0].set_ylim(0,45); axes[0].set_ylabel("Number of samples", fontsize=8.5)

axes[1].bar(["All-negative\nclassifier"], [990], color=C_LBLUE, label="Correct (TN)", edgecolor=C_BLUE, linewidth=1.2)
axes[1].bar(["All-negative\nclassifier"], [10], bottom=990, color=C_RED, label="Missed cases (FN)", edgecolor=C_RED, linewidth=1.2)
axes[1].set_title("b  The accuracy paradox (n=1000, 10 cases)", fontsize=9, fontweight="bold", loc="left")
axes[1].set_ylabel("Number of samples", fontsize=8.5)
axes[1].legend(fontsize=7.5, loc="center right")
axes[1].text(0.5, 500, "Accuracy = 99.0%\nSensitivity = 0.0%\nPrecision = 0.0%",
             ha="center", fontsize=8, color="white", fontweight="bold")
plt.tight_layout()
plt.savefig(FIG/"fig7_imbalance.png", facecolor="white")
plt.close()

# FIG 8: Copy feature experiment
def extend(rep):
    Xtr = train[FEATURES].copy()
    Xva = valid[FEATURES].copy()
    for k in range(rep):
        Xtr[f"lumbar_pain_copy{k}"] = train["lumbar_pain"]
        Xva[f"lumbar_pain_copy{k}"] = valid["lumbar_pain"]
    m = BernoulliNB(alpha=1.0, binarize=None).fit(Xtr, train[TARGET])
    return m.predict_proba(Xva)[:,1]

p0 = extend(0); p1 = extend(1); p5 = extend(5)
fig, ax = plt.subplots(figsize=(5.5, 4.8))
ax.scatter(p0, p1, alpha=0.7, color=C_BLUE, label="1 copy", s=45, edgecolor="white", linewidth=0.8)
ax.scatter(p0, p5, alpha=0.7, color=C_RED, marker="^", label="5 copies", s=50, edgecolor="white", linewidth=0.8)
lims = [0,1]
ax.plot(lims,lims,"--",color="#BDBDBD",lw=1.2,label="No change")
ax.set_xlabel("Original P(Y = 1)", fontsize=9)
ax.set_ylabel("P(Y = 1) after copying lumbar_pain", fontsize=9)
ax.set_title("Figure 8. Effect of feature duplication on predicted probability", fontsize=9.5, fontweight="bold", pad=10)
ax.legend(fontsize=8)
plt.tight_layout()
plt.savefig(FIG/"fig8_copy.png", facecolor="white")
plt.close()

# save results
out = {
    "data": {"train":len(train),"valid":len(valid),"test":len(test),
             "train_pos":int((train[TARGET]==1).sum()),
             "valid_pos":int((valid[TARGET]==1).sum()),
             "test_pos":int((test[TARGET]==1).sum())},
    "priors": {"p0":float(np.exp(prior[0])),"p1":float(np.exp(prior[1]))},
    "theta_class0": theta[0].round(4).tolist(),
    "theta_class1": theta[1].round(4).tolist(),
    "hand_calc_p": float(p_hand),
    "hand_table": hand_df.to_dict(orient="records"),
    "train_metrics": res_train,
    "valid_metrics": res_valid,
    "baseline_metrics": res_base,
    "test_metrics": res_test,
    "threshold_table": th_df.to_dict(orient="records"),
    "chosen_threshold": chosen_t,
    "copy_p1_mean": float(p1.mean()),
    "copy_p5_mean": float(p5.mean()),
    "reliability": rel.assign(bin=rel.bin.astype(str)).to_dict(orient="records"),
}
with open(FIG/"results.json","w") as f:
    json.dump(out, f, indent=2, default=str)

print("\n=== ALL FIGURES SAVED ===")
for p in sorted(FIG.glob("*.png")):
    print(p.name, p.stat().st_size)
