# -*- coding: utf-8 -*-
"""Chapter 5 hypothesis-testing analysis on heart-disease-hypothesis.csv.

Computes every number needed to fill the student worksheet:
  * descriptive statistics of thalach by disease group (missing handling)
  * Welch t-test: mean difference, 95% CI, t, df, p-value
  * Mann-Whitney U as a robustness check
  * sex vs disease chi-square
  * age vs thalach correlation
  * logistic regression of disease on age, sex, thalach (+ site)
  * multiple-comparison family-wise error rate
"""
import csv
import math
from pathlib import Path

import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "package" / "data" / "heart-disease-hypothesis.csv"
OUT = HERE / "analysis_results.txt"

lines = []


def w(*a):
    s = " ".join(str(x) for x in a)
    lines.append(s)
    print(s)


# ---------------- load ----------------
with open(DATA, encoding="utf-8") as f:
    rows = list(csv.DictReader(f))


def fl(v):
    return float(v) if v not in ("", None) else None


n_total = len(rows)
age = np.array([fl(r["age"]) for r in rows], dtype=float)
sex = np.array([fl(r["sex"]) for r in rows], dtype=float)
thal = np.array([fl(r["thalach"]) for r in rows], dtype=float)
dis = np.array([fl(r["disease"]) for r in rows], dtype=float)

w("# RAW")
w("records:", n_total)
w("disease=1:", int(np.sum(dis == 1)), " disease=0:", int(np.sum(dis == 0)))
w("thalach missing:", int(np.sum(np.isnan(thal))))
miss = np.isnan(thal)
w("missing by group: disease=1 ->", int(np.sum(miss & (dis == 1))),
  " disease=0 ->", int(np.sum(miss & (dis == 0))))

# analysis sample: complete disease + thalach
keep = (~np.isnan(thal)) & (~np.isnan(dis))
t = thal[keep]
d = dis[keep]
g1 = t[d == 1]
g0 = t[d == 0]


def desc(x):
    return dict(n=len(x), mean=float(np.mean(x)), sd=float(np.std(x, ddof=1)),
                median=float(np.median(x)), q1=float(np.percentile(x, 25)),
                q3=float(np.percentile(x, 75)))


d1 = desc(g1)
d0 = desc(g0)
w("\n# THALACH BY GROUP (analysis sample n=%d)" % len(t))
for name, dd in (("disease=1", d1), ("disease=0", d0)):
    w(f"{name}: n={dd['n']} mean={dd['mean']:.2f} sd={dd['sd']:.2f} "
      f"median={dd['median']:.1f} IQR=[{dd['q1']:.1f},{dd['q3']:.1f}]")

# ---------------- Welch t-test ----------------
res = stats.ttest_ind(g1, g0, equal_var=False)
tstat = float(res.statistic)
pval = float(res.pvalue)


def welch_df(a, b):
    va, vb = np.var(a, ddof=1), np.var(b, ddof=1)
    na, nb = len(a), len(b)
    return (va / na + vb / nb) ** 2 / (
        (va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1))


df = welch_df(g1, g0)
diff = d1["mean"] - d0["mean"]
se = math.sqrt(np.var(g1, ddof=1) / len(g1) + np.var(g0, ddof=1) / len(g0))
tcrit = stats.t.ppf(0.975, df)
ci_lo, ci_hi = diff - tcrit * se, diff + tcrit * se
w("\n# WELCH T-TEST (two-sided)")
w(f"mean diff (disease1 - disease0) = {diff:.2f}")
w(f"SE = {se:.3f}")
w(f"t = {tstat:.3f}  df = {df:.2f}  p = {pval:.3e}")
w(f"95%% CI = [{ci_lo:.2f}, {ci_hi:.2f}]")
pooled_sd = math.sqrt(((len(g1)-1)*np.var(g1, ddof=1) + (len(g0)-1)*np.var(g0, ddof=1)) / (len(g1)+len(g0)-2))
w(f"Cohen's d = {diff/pooled_sd:.3f}")

# ---------------- Mann-Whitney ----------------
u, pu = stats.mannwhitneyu(g1, g0, alternative="two-sided")
w("\n# MANN-WHITNEY U (robustness)")
w(f"U = {float(u):.1f}  p = {float(pu):.3e}")

# ---------------- sex vs disease chi-square ----------------
tab = np.zeros((2, 2))
for s in (0, 1):
    for dd_ in (0, 1):
        tab[s, dd_] = np.sum((sex == s) & (dis == dd_))
chi2, pchi, dof, exp = stats.chi2_contingency(tab)
w("\n# SEX x DISEASE (all records with disease; sex present)")
w("table [[female0,female1],[male0,male1]] =", tab.astype(int).tolist())
odds, pfish = stats.fisher_exact(tab)
if np.any(exp < 5):
    w(f"Fisher exact oddsratio={odds:.3f} p={pfish:.3e}")
w(f"chi2 = {chi2:.3f}  dof = {dof}  p = {pchi:.3e}")

# ---------------- age vs thalach correlation ----------------
am = ~np.isnan(age) & ~np.isnan(thal)
pear = stats.pearsonr(age[am], thal[am])
spear = stats.spearmanr(age[am], thal[am])
w("\n# AGE vs THALACH")
w(f"Pearson r = {pear.statistic:.3f}  p = {pear.pvalue:.3e}")
w(f"Spearman rho = {spear.statistic:.3f}  p = {spear.pvalue:.3e}")

# ---------------- logistic regression (numpy IRLS) ----------------
def logit_fit(X, y, iters=100):
    X = np.column_stack([np.ones(len(X)), X])
    beta = np.zeros(X.shape[1])
    for _ in range(iters):
        eta = X @ beta
        pr = 1 / (1 + np.exp(-eta))
        W = pr * (1 - pr)
        z = eta + (y - pr) / np.clip(W, 1e-9, None)
        XtW = X.T * W
        beta_new = np.linalg.solve(XtW @ X, XtW @ z)
        if np.allclose(beta_new, beta):
            beta = beta_new
            break
        beta = beta_new
    eta = X @ beta
    pr = 1 / (1 + np.exp(-eta))
    W = pr * (1 - pr)
    cov = np.linalg.inv((X.T * W) @ X)
    se = np.sqrt(np.diag(cov))
    return beta, se


cmp_ = (~np.isnan(thal)) & (~np.isnan(age)) & (~np.isnan(sex)) & (~np.isnan(dis))
yc = dis[cmp_]
Xc = np.column_stack([age[cmp_], sex[cmp_], thal[cmp_]])
b, se = logit_fit(Xc, yc)
names = ["intercept", "age", "sex(male)", "thalach"]
w("\n# LOGISTIC REGRESSION disease ~ age + sex + thalach")
for nm, bb, ss in zip(names, b, se):
    w(f"{nm}: beta={bb:.4f} SE={ss:.4f} OR={math.exp(bb):.4f} "
      f"95%CI=[{math.exp(bb-1.96*ss):.4f},{math.exp(bb+1.96*ss):.4f}] z={bb/ss:.3f} p={2*(1-stats.norm.cdf(abs(bb/ss))):.3e}")

# ---------------- multiple comparison FWER ----------------
w("\n# MULTIPLE COMPARISON")
w(f"1 - 0.95^20 = {1 - 0.95**20:.4f}")
w(f"Bonferroni alpha = 0.05/20 = {0.05/20:.4f}")

# ---------------- site distribution ----------------
sites = {}
for r in rows:
    sites.setdefault(r["site"], [0, 0])
    if fl(r["disease"]) == 1:
        sites[r["site"]][0] += 1
    elif fl(r["disease"]) == 0:
        sites[r["site"]][1] += 1
w("\n# SITE (disease, no-disease)")
for s, v in sites.items():
    w(f"{s}: {v[0]} / {v[1]}")

OUT.write_text("\n".join(lines), encoding="utf-8")
print("\nwritten", OUT)
