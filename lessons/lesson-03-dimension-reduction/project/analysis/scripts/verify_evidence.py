
"""Independent verification of evidence tables C1, C1续, C2, C2续 (and B1 spot check)."""
import os, json
for _k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']:
    os.environ[_k] = '1'
from pathlib import Path
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from threadpoolctl import threadpool_limits
threadpool_limits(1)
HERE = Path(__file__).resolve().parent
PKG = HERE.parent.parent / 'student-package'
RES = HERE.parent / 'results'
a = np.load(PKG / 'data' / 'cohort120.npz', allow_pickle=True)
a = {k: a[k] for k in a.files}
X, y, ids, genes = a['X'], a['y'], a['ids'], a['genes']
tr = a['development']
Xd = X[tr].astype(float)
print('dev', Xd.shape)

def report(tag, centered, ncomp, dims):
    out = {}
    p = PCA(n_components=ncomp, svd_solver='full').fit(centered)
    cum = np.cumsum(p.explained_variance_ratio_)
    recon = p.inverse_transform(p.transform(centered))
    res_ss = ((centered - recon) ** 2).sum()
    tot_ss = (centered ** 2).sum()
    rel = res_ss / tot_ss
    for d in dims:
        q = PCA(n_components=d, svd_solver='full').fit(centered)
        r = q.inverse_transform(q.transform(centered))
        mse = ((centered - r) ** 2).mean()
        rr = ((centered - r) ** 2).sum() / tot_ss
        out[d] = dict(cum_var=float(np.cumsum(q.explained_variance_ratio_)[-1]), mse=float(mse), rel_mse=float(rr))
    print(tag, 'PC1 %.4f PC2 %.4f' % (p.explained_variance_ratio_[0], p.explained_variance_ratio_[1]),
          'dim90', int(np.searchsorted(cum, 0.9) + 1))
    for d in dims:
        print('   keep', d, 'cum %.4f mse %.4f rel %.4f' % (out[d]['cum_var'], out[d]['mse'], out[d]['rel_mse']))
    return p, out

mu = Xd.mean(0)
print('=== only centering ===')
p1, o1 = report('centered', Xd - mu, 79, [2, 5, 20, 47, 79])
print('=== per-gene standardization ===')
sc = StandardScaler().fit(Xd); z = sc.transform(Xd)
p2, o2 = report('standardized', z, 79, [2, 5, 20, 51, 79])

# C1: top-6 |PC1 loading| genes for standardized PCA, and query patient contributions
load = p2.components_[0]
i003 = list(ids).index('SEQC_NB003')
arg = np.argsort(-np.abs(load))[:6]
print('=== C1 standardized PC1 top6 |loading| ===')
tot6 = 0.0
for j in arg:
    val = z[i003, j]
    contrib = val * load[j]
    tot6 += contrib
    print('  %-10s raw_sd %.4f w %.4f z %.4f contrib %.4f' % (genes[j], sc.scale_[j], load[j], val, contrib))
score = float(z[i003] @ load)
print('C1续 standardized: top6 sum %.4f rest %.4f PC1 score %.4f' % (tot6, score - tot6, score))
# centered-only variant
mu_c = Xd - mu
loadc = p1.components_[0]
xc = mu_c[i003]
argc = np.argsort(-np.abs(loadc))[:6]
t6c = sum(xc[j] * loadc[j] for j in argc)
print('C1续 centered-only: top6 sum %.4f rest %.4f PC1 score %.4f' % (t6c, float(xc @ loadc) - t6c, float(xc @ loadc)))
json.dump(dict(centered=o1, standardized=o2), open(RES / 'verify_pca.json', 'w'), indent=2)

