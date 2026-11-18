
"""Reproduce the classroom experiments from pbl-high-dimension-reduction-classroom.ipynb.
Writes all outputs into homework3/analysis/results/. Data is read from student-package.
"""
import os
for _k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMBA_NUM_THREADS']:
    os.environ[_k] = '1'
import json, sys, hashlib
from pathlib import Path
import numpy as np, pandas as pd
from scipy.spatial.distance import pdist, squareform
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.decomposition import PCA
from threadpoolctl import threadpool_limits
threadpool_limits(1)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE.parent
PKG = ANALYSIS.parent / 'student-package'
RES = ANALYSIS / 'results'; RES.mkdir(parents=True, exist_ok=True)
CACHE = ANALYSIS / 'cache'; CACHE.mkdir(parents=True, exist_ok=True)
os.environ['NUMBA_CACHE_DIR'] = str(CACHE)
SEED = 20260921
COUNTS = [20, 100, 500, 2000, 5000]

a = np.load(PKG / 'data' / 'cohort120.npz', allow_pickle=True)
a = {k: a[k] for k in a.files}
X, y, ids, genes = a['X'], a['y'], a['ids'], a['genes']
tr, te = a['development'], a['test']
Xd, yd = X[tr], y[tr]
print('X', X.shape, 'dev', Xd.shape, 'test', X[te].shape)
print('risk counts dev', np.bincount(yd), 'test', np.bincount(y[te]))

report = {}

# ---------- Q2 distance experiment (cell 4) ----------
order = np.random.default_rng(SEED + 100).permutation(X.shape[1])
fig, ax = plt.subplots(figsize=(9, 4))
dist_rows = []
for k in COUNTS + [X.shape[1]]:
    z = StandardScaler().fit_transform(Xd[:, order[:k]])
    dd = squareform(pdist(z)); np.fill_diagonal(dd, np.inf); near = dd.min(1)
    np.fill_diagonal(dd, 0); far = dd.max(1)
    row = dict(p=int(k), mean=float(pdist(z).mean()), near=float(near.mean()),
               far=float(far.mean()), contrast=float(np.mean((far - near) / near)))
    dist_rows.append(row)
    print(k, row)
    ax.hist(pdist(z) / pdist(z).mean(), bins=30, density=True, histtype='step', label=str(k))
ax.set(xlabel='distance / mean distance at same p', ylabel='density',
       title='same 80 patients, permutation 1, 20..23146 standardized genes')
ax.legend(title='genes')
fig.tight_layout(); fig.savefig(RES / 'classroom-distances.png', dpi=160); plt.close(fig)
report['distance'] = dist_rows
# nearest/farthest pair for the 20-gene set
z20 = StandardScaler().fit_transform(Xd[:, order[:20]])
d20 = squareform(pdist(z20)); np.fill_diagonal(d20, np.inf)
i, j = np.unravel_index(np.argmin(d20), d20.shape)
print('20-gene closest pair', ids[tr][i], ids[tr][j], d20[i, j])
report['closest_20'] = dict(a=str(ids[tr][i]), b=str(ids[tr][j]), d=float(d20[i, j]))

# ---------- Q3 fixed split demo (cell 6, quick=True) ----------
def fixed_demo(quick=True, reps=20):
    p = X.shape[1]; rows = []; predictions = []
    for rep in range(1 if quick else reps):
        o = np.random.default_rng(SEED + 100 + rep).permutation(p)
        for k in COUNTS + [p]:
            idx = o[:k]
            sc = StandardScaler().fit(X[tr][:, idx]); zt = sc.transform(X[tr][:, idx])
            model = LogisticRegression(C=1, solver='liblinear', dual=k > len(tr),
                                       max_iter=10000, random_state=SEED).fit(zt, y[tr])
            for group, ix in [('seen', tr), ('unseen', te)]:
                pred = model.predict(sc.transform(X[ix][:, idx])); correct = pred == y[ix]
                r = dict(repeat=rep + 1, p=int(k), group=group, n=int(len(ix)),
                         correct=int(correct.sum()), proportion=float(correct.mean()))
                for lab, name in [(1, 'high'), (0, 'nonhigh')]:
                    m = y[ix] == lab
                    r[name + '_n'] = int(m.sum()); r[name + '_correct'] = int(correct[m].sum())
                    r[name + '_proportion'] = float(correct[m].mean())
                rows.append(r)
        print('fixed gene ordering', rep + 1, 'done', flush=True)
    return pd.DataFrame(rows)

first = fixed_demo(quick=True)
print(first.to_string(index=False))
first.to_csv(RES / 'classroom-seen-unseen.csv', index=False, encoding='utf-8-sig')
report['fixed_split'] = first.to_dict('records')

# ---------- Q4/Q5 standardization, PCA, UMAP (cell 8) ----------
from umap import UMAP
sc = StandardScaler().fit(Xd); z = sc.transform(Xd)
print('whole-matrix mean (after scaling) %.3e' % z.mean())
print('median gene sd (after scaling)', np.median(z.std(0)))
print('raw per-gene sd median', np.median(Xd.std(0)))
pc = PCA(n_components=2, svd_solver='full').fit(z); xy = pc.transform(z)
print('PCA explained variance ratio', pc.explained_variance_ratio_)
um = UMAP(n_neighbors=15, min_dist=.1, random_state=SEED, n_jobs=1).fit(z)
fig, axs = plt.subplots(1, 2, figsize=(10, 4))
for ax_, label, coords in [(axs[0], 'PCA', xy), (axs[1], 'UMAP', um.embedding_)]:
    ax_.scatter(coords[:, 0], coords[:, 1], c=yd, cmap='coolwarm')
    ax_.set(xlabel=label + ' 1', ylabel=label + ' 2', title=label)
fig.suptitle('same 80 patients, all 23146 genes, colored by risk group')
fig.tight_layout(); fig.savefig(RES / 'classroom-pca-umap.png', dpi=160); plt.close(fig)
report['standardization'] = dict(median_gene_sd_scaled=float(np.median(z.std(0))),
                                 median_gene_sd_raw=float(np.median(Xd.std(0))),
                                 mean_scaled=float(z.mean()))
report['pca'] = dict(ratio=[float(v) for v in pc.explained_variance_ratio_])
json.dump(report, open(RES / 'classroom_results.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=2)
print('DONE ->', RES)

