"""Shared SVM experiments; no file writes or test-label reads on import."""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.metrics import confusion_matrix, balanced_accuracy_score, roc_auc_score

BASE = Path(__file__).resolve().parents[1]
REPO = BASE.parents[2]
FEATURES = ['pelvic_incidence', 'degree_spondylolisthesis']
C_GRID = [.01, .1, 1, 10, 100]
RBF_C = [.1, 1, 10, 100]
GAMMA_GRID = [.01, .1, 1, 10]

def load_development():
    return tuple(pd.read_csv(BASE/f'data/student/{name}.csv') for name in ['train', 'validation'])

def make_model(kernel='linear', C=1., gamma=.1, scaled=True):
    svc = SVC(kernel=kernel, C=C, gamma=gamma, degree=2, coef0=1.,
              probability=False, tol=1e-7, max_iter=200000)
    return make_pipeline(StandardScaler(), svc) if scaled else svc

def svc_of(model):
    return model.named_steps['svc'] if hasattr(model, 'named_steps') else model

def metrics(y, score):
    pred = (np.asarray(score) >= 0).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return dict(n=len(y), TN=int(tn), FP=int(fp), FN=int(fn), TP=int(tp),
                accuracy=float(np.mean(pred == np.asarray(y))),
                balanced_accuracy=float(balanced_accuracy_score(y, pred)),
                sensitivity=float(tp/(tp+fn)), specificity=float(tn/(tn+fp)),
                roc_auc=float(roc_auc_score(y, score)))

def assess(model, train, validation, **setting):
    train_score = model.decision_function(train[FEATURES])
    ym = 2*train.abnormal.to_numpy()-1
    hinge = np.maximum(0, 1-ym*train_score)
    svc = svc_of(model)
    row = dict(**setting, n_sv=len(svc.support_),
               train_errors=int(np.sum((train_score >= 0) != train.abnormal)),
               mean_hinge=float(hinge.mean()), margin_violations=int(np.sum(hinge > 1e-5)))
    row.update({'train_'+k: v for k, v in metrics(train.abnormal, train_score).items()})
    row.update({'val_'+k: v for k, v in metrics(validation.abnormal, model.decision_function(validation[FEATURES])).items()})
    if svc.kernel == 'linear':
        norm = np.linalg.norm(svc.coef_[0]); row['linear_width'] = float(2/norm)
        row['regularizer'] = float(.5*norm**2)
        row['objective'] = float(.5*norm**2 + svc.C*hinge.sum())
    return row

def geometry_experiment(train):
    # Deliberately separable TRAIN subset, for geometry only. No population inference.
    normal = train[(train.abnormal == 0) & (train.degree_spondylolisthesis < 5)].sort_values('sample_id').head(4)
    abnormal = train[(train.abnormal == 1) & (train.degree_spondylolisthesis > 30)].sort_values('sample_id').head(4)
    subset = pd.concat([normal, abnormal]).reset_index(drop=True)
    assert len(subset) == 8
    scaler = StandardScaler().fit(train[FEATURES])
    z = scaler.transform(subset[FEATURES]); y = subset.abnormal.to_numpy(); ym = 2*y-1
    fit = SVC(kernel='linear', C=10000., tol=1e-9, max_iter=200000).fit(z, y)
    w, b = fit.coef_[0], fit.intercept_[0]; f = fit.decision_function(z)
    assert np.min(ym*f) > 1-1e-5  # large-C fit actually has no material violations here
    half_width = 1/np.linalg.norm(w)
    # Same normal vector, three offsets; all separate these selected records.
    candidates = []
    for offset in [-.6, 0., .6]:
        bb = b + offset
        signed = ym*(z@w+bb)/np.linalg.norm(w)
        candidates.append(dict(offset=offset, b=bb, training_errors=int(np.sum(signed < 0)),
                               min_signed_distance=float(signed.min())))
    # Select one SUPPORT vector and one distant NON-support vector by a stated rule.
    support = fit.support_.tolist()
    nonsupport = sorted(set(range(8))-set(support))
    non = max(nonsupport, key=lambda i: abs(f[i]))
    sv = min(support, key=lambda i: subset.iloc[i].sample_id)
    changes = []
    for label, index in [('delete_non_support', non), ('delete_support', sv)]:
        keep = np.arange(8) != index
        refit = SVC(kernel='linear', C=10000., tol=1e-9, max_iter=200000).fit(z[keep], y[keep])
        changes.append(dict(operation=label, sample_id=subset.iloc[index].sample_id,
                            coefficient_change=float(np.linalg.norm(refit.coef_[0]-w)),
                            intercept_change=float(abs(refit.intercept_[0]-b)),
                            score_change_max=float(np.max(np.abs(refit.decision_function(z)-f)))))
    # Counterfactual duplicate with opposite label proves hard-margin infeasibility.
    z_conflict = np.vstack([z, z[sv]])
    y_conflict = np.r_[y, 1-y[sv]]
    contradiction = []
    for C in [.01, 1., 100.]:
        m = SVC(kernel='linear', C=C, tol=1e-8, max_iter=200000).fit(z_conflict, y_conflict)
        ss = m.decision_function(z_conflict); ll = np.maximum(0, 1-(2*y_conflict-1)*ss)
        contradiction.append(dict(C=C, errors=int(np.sum((ss >= 0) != y_conflict)),
                                  sum_hinge=float(ll.sum()), n_sv=len(m.support_)))
    table = subset[['sample_id', *FEATURES, 'abnormal']].copy()
    table['z1'], table['z2'], table['score'] = z[:, 0], z[:, 1], f
    table['signed_margin'] = ym*f
    table['distance'] = abs(f)/np.linalg.norm(w)
    table['hinge'] = np.maximum(0, 1-ym*f)
    table['support'] = np.isin(np.arange(8), support)
    return dict(subset=subset, scaler=scaler, z=z, model=fit, table=table,
                candidates=pd.DataFrame(candidates), changes=pd.DataFrame(changes),
                contradiction=pd.DataFrame(contradiction), half_width=half_width)

def parameter_experiment(train, validation):
    rows, models = [], {}
    settings = [('linear', C, .1) for C in C_GRID]
    settings += [('rbf', C, g) for C in RBF_C for g in GAMMA_GRID]
    settings += [('poly', 1., .1)]
    for kernel, C, gamma in settings:
        model = make_model(kernel, C, gamma).fit(train[FEATURES], train.abnormal)
        assert svc_of(model).fit_status_ == 0
        key = (kernel, C, gamma); models[key] = model
        rows.append(assess(model, train, validation, kernel=kernel, C=C, gamma=gamma))
    return pd.DataFrame(rows), models

def scaling_experiment(train, validation):
    # Artificial unit change in x1: same information, different numeric coordinates.
    tr2, va2 = train.copy(), validation.copy()
    tr2[FEATURES[0]] *= 100; va2[FEATURES[0]] *= 100
    rows, scores = [], {}
    for scaled in [False, True]:
        for unit, tr, va in [('original', train, validation), ('x1_times_100', tr2, va2)]:
            model = make_model('rbf', 1., .1, scaled).fit(tr[FEATURES], tr.abnormal)
            scores[(scaled, unit)] = model.decision_function(va[FEATURES])
            rows.append(assess(model, tr, va, scaled=scaled, unit=unit, C=1., gamma=.1))
    return pd.DataFrame(rows), {str(scaled): float(np.max(np.abs(scores[(scaled, 'original')]-scores[(scaled, 'x1_times_100')]))) for scaled in [False, True]}

def select_validation_configs(grid):
    # Same fixed rule for each family, never applied to test scores.
    configs = {}
    for kernel in ['linear', 'rbf']:
        row = grid[grid.kernel == kernel].sort_values(
            ['val_balanced_accuracy', 'C', 'gamma'], ascending=[False, True, True]).iloc[0]
        configs[kernel] = (kernel, float(row.C), float(row.gamma))
    return configs

def noise_experiment(model, train, validation, repeats=100):
    rng = np.random.default_rng(9); X = validation[FEATURES].copy()
    sd = train[FEATURES].std(ddof=0).to_numpy()
    original = model.predict(X); rows = []
    for level in [0., .05, .1, .2]:
        acc, flips = [], []
        for _ in range(1 if level == 0 else repeats):
            xx = X + rng.normal(size=X.shape)*sd*level
            p = model.predict(xx)
            acc.append(balanced_accuracy_score(validation.abnormal, p))
            flips.append(np.mean(p != original))
        rows.append(dict(noise_sd_fraction=level, repeats=len(acc),
                         mean_balanced_accuracy=float(np.mean(acc)),
                         sd_balanced_accuracy=float(np.std(acc)), mean_flip_rate=float(np.mean(flips))))
    return pd.DataFrame(rows)

def evaluate_locked(configs, freeze_confirmed=False, open_test=False):
    if not (freeze_confirmed and open_test):
        return 'Test locked: first record inputs, parameters and interpretation questions.'
    train, _ = load_development()
    features = pd.read_csv(BASE/'data/student/locked-test-features.csv')
    labels = pd.read_csv(BASE/'data/teacher/locked-test-labels.csv')
    test = features.merge(labels, on='sample_id', validate='one_to_one')
    rows = []
    for family, (kernel, C, gamma) in configs.items():
        model = make_model(kernel, C, gamma).fit(train[FEATURES], train.abnormal)
        row = dict(family=family, C=C, gamma=gamma)
        row.update(metrics(test.abnormal, model.decision_function(test[FEATURES])))
        rows.append(row)
    return pd.DataFrame(rows)

def draw_boundary(model, train, title='', standardized=False, scaler=None, subset=None):
    """Scientific plot from measured records and fitted scores; no file writing."""
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 5))
    data = train if subset is None else subset
    X = data[FEATURES].to_numpy()
    if standardized:
        X = scaler.transform(data[FEATURES])
    # Clip display only to show central observations; report off-screen count.
    low, high = np.percentile(X, [0, 98], axis=0) if len(X) > 20 else (X.min(0), X.max(0))
    pad = .12*np.maximum(high-low, 1e-3); low -= pad; high += pad
    xx, yy = np.meshgrid(np.linspace(low[0], high[0], 160), np.linspace(low[1], high[1], 160))
    points = np.c_[xx.ravel(), yy.ravel()]
    score = model.decision_function(points if standardized else pd.DataFrame(points, columns=FEATURES)).reshape(xx.shape)
    ax.contourf(xx, yy, score >= 0, levels=[-.5,.5,1.5], colors=['#e3efee','#f9e9dc'], alpha=.7)
    ax.contour(xx, yy, score, levels=[-1,0,1], colors=['#52686a','#193638','#52686a'], linestyles=['--','-','--'])
    for cls, col, marker in [(0,'#087c77','o'),(1,'#b75d24','^')]:
        mask = data.abnormal.to_numpy() == cls
        ax.scatter(X[mask,0],X[mask,1],color=col,marker=marker,s=30,label=['NO','AB'][cls],alpha=.8)
    sv = svc_of(model).support_
    ax.scatter(X[sv,0],X[sv,1],s=85,facecolors='none',edgecolors='#193638',linewidths=.8,label='Support vectors')
    outside = int(np.any((X < low)|(X > high), axis=1).sum())
    ax.set(xlim=(low[0],high[0]),ylim=(low[1],high[1]),
           xlabel='z1: pelvic incidence' if standardized else 'Pelvic incidence (source scale)',
           ylabel='z2: spondylolisthesis score' if standardized else 'Degree of spondylolisthesis (source scale)',
           title=title+f'\n{len(X)} training records; {outside} outside display')
    ax.legend(fontsize=8); fig.tight_layout()
    return fig
