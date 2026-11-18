"""Small, readable analysis helpers for the lesson 7 PBL lab."""
from itertools import combinations
from math import sqrt
import numpy as np
import pandas as pd
from sklearn.metrics import (confusion_matrix, roc_auc_score, average_precision_score,
                             log_loss, brier_score_loss)
from sklearn.naive_bayes import BernoulliNB

FEATURES = ['fever_ge_38', 'nausea', 'lumbar_pain', 'urine_pushing',
            'micturition_pain', 'burning_urethra']
THRESHOLDS = [.05, .1, .2, .3, .5, .7, .8, .9, .95]

def fit_model(train, target='bladder_inflammation'):
    return BernoulliNB(alpha=1.0, binarize=None).fit(train[FEATURES], train[target])

def scores(y, probability, threshold=.5):
    y, probability = np.asarray(y), np.asarray(probability)
    tn, fp, fn, tp = confusion_matrix(y, probability >= threshold, labels=[0, 1]).ravel()
    ratio = lambda a, b: float(a / b) if b else float('nan')
    return dict(tn=int(tn), fp=int(fp), fn=int(fn), tp=int(tp),
                accuracy=ratio(tp+tn, len(y)), sensitivity=ratio(tp, tp+fn),
                specificity=ratio(tn, tn+fp), precision=ratio(tp, tp+fp),
                f1=ratio(2*tp, 2*tp+fp+fn),
                roc_auc=float(roc_auc_score(y, probability)),
                average_precision=float(average_precision_score(y, probability)),
                brier=float(brier_score_loss(y, probability)),
                log_loss=float(log_loss(y, probability, labels=[0, 1])))

def threshold_table(y, probability):
    return pd.DataFrame([dict(threshold=t, **scores(y, probability, t)) for t in THRESHOLDS])

def choose_threshold(table):
    """Predeclared classroom rule; only call on validation results."""
    eligible = table[table.sensitivity >= .9].copy()
    if eligible.empty:
        return None
    eligible['distance_to_half'] = (eligible.threshold - .5).abs()
    return float(eligible.sort_values(['specificity', 'distance_to_half', 'threshold'],
                                     ascending=[False, True, True]).iloc[0].threshold)

def reliability(y, probability):
    frame = pd.DataFrame({'observed': np.asarray(y), 'predicted': probability})
    frame['bin'] = pd.cut(frame.predicted, bins=[0, .2, .4, .6, .8, 1],
                          include_lowest=True)
    result = frame.groupby('bin', observed=False).agg(
        n=('observed', 'size'), mean_probability=('predicted', 'mean'),
        observed_fraction=('observed', 'mean')).reset_index()
    result['bin'] = result['bin'].astype(str)
    return result

def dependence(train, target='bladder_inflammation'):
    rows = []
    for label in [0, 1]:
        part = train[train[target] == label]
        for a, b in combinations(FEATURES, 2):
            pa, pb = part[a].mean(), part[b].mean()
            joint = (part[a] * part[b]).mean()
            rows.append(dict(label=label, feature_a=a, feature_b=b, n=len(part),
                             p_a=pa, p_b=pb, joint=joint, product=pa*pb,
                             difference=joint-pa*pb))
    return pd.DataFrame(rows)

def hand_calculation(train, x, target='bladder_inflammation'):
    rows, weights = [], []
    for label in [0, 1]:
        part = train[train[target] == label]
        theta = (part[FEATURES].sum().to_numpy() + 1) / (len(part) + 2)
        terms = np.where(np.asarray(x) == 1, theta, 1-theta)
        weight = len(part)/len(train) * np.prod(terms)
        weights.append(weight)
        for feature, value, count, prob, term in zip(
                FEATURES, x, part[FEATURES].sum(), theta, terms):
            rows.append(dict(label=label, n_class=len(part), feature=feature,
                             x=int(value), count_one=int(count), theta=prob,
                             likelihood_term=term))
    return pd.DataFrame(rows), np.asarray(weights), weights[1]/sum(weights)

def wilson(successes, total, z=1.959963984540054):
    p = successes/total
    center = (p+z*z/(2*total))/(1+z*z/total)
    half = z*sqrt(p*(1-p)/total+z*z/(4*total*total))/(1+z*z/total)
    return [max(0., center-half), min(1., center+half)]

def stress(model, features, y, threshold=.5, repeats=1000, seed=42):
    """Independent bit flips of the fixed held-out inputs; no retraining."""
    rng = np.random.default_rng(seed)
    x = features[FEATURES].to_numpy()
    draws = rng.random((repeats, *x.shape))
    rows = []
    for rate in [0, .05, .1, .2]:
        flipped = np.logical_xor(x[None, :, :], draws < rate).astype(int)
        matrix = pd.DataFrame(flipped.reshape(-1, len(FEATURES)), columns=FEATURES)
        probabilities = model.predict_proba(matrix)[:, 1].reshape(repeats, len(y))
        pred = probabilities >= threshold
        labels = np.asarray(y).astype(bool)
        arrays = dict(accuracy=(pred == labels).mean(axis=1),
                      sensitivity=pred[:, labels].mean(axis=1),
                      specificity=(~pred[:, ~labels]).mean(axis=1))
        for metric, values in arrays.items():
            rows.append(dict(flip_rate=rate, metric=metric, mean=values.mean(),
                             sd=values.std(ddof=1), q05=np.quantile(values, .05),
                             q95=np.quantile(values, .95), repeats=repeats, seed=seed))
    return pd.DataFrame(rows)
