"""Reproducible classroom demonstrations for ensemble learning.

Usage: python scripts/demo_ensemble.py --data wdbc   (default; data/)
       python scripts/demo_ensemble.py --data ctg    (alternative; data-ctg/, grouped by recording_id)
"""
from pathlib import Path
import argparse
import json
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import AdaBoostClassifier, BaggingClassifier, GradientBoostingClassifier, RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold, cross_validate
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

BASE = Path(__file__).resolve().parents[1]
SEED = 1010
# name -> (data folder, label column, group column or None)
DATASETS = {"wdbc": ("data", "malignant", None), "ctg": ("data-ctg", "pathologic", "recording_id")}

def load(name):
    folder, label, group = DATASETS[name]
    train = pd.read_csv(BASE / folder / "student/train.csv")
    valid = pd.read_csv(BASE / folder / "student/validation.csv")
    features = [c for c in train.columns if c not in {"sample_id", "recording_id", label}]
    return train, valid, features, label, group

def models():
    return {
        "single_tree": DecisionTreeClassifier(max_depth=4, random_state=SEED),
        "bagging": BaggingClassifier(estimator=DecisionTreeClassifier(max_depth=None, random_state=SEED), n_estimators=100, max_features=1.0, random_state=SEED, n_jobs=1),
        "random_forest": RandomForestClassifier(n_estimators=100, max_features="sqrt", random_state=SEED, n_jobs=1),
        "adaboost": AdaBoostClassifier(n_estimators=50, random_state=SEED),
        "gradient_boosting": GradientBoostingClassifier(n_estimators=100, random_state=SEED),
        "logistic": make_pipeline(StandardScaler(), LogisticRegression(max_iter=5000, random_state=SEED)),
        "rbf_svm": make_pipeline(StandardScaler(), SVC(C=1, kernel="rbf", random_state=SEED)),
    }

def score(model, X):
    return model.decision_function(X) if hasattr(model, "decision_function") else model.predict_proba(X)[:, 1]

def fit_table(X, y, Xv, yv):
    rows = []
    for name, model in models().items():
        model.fit(X, y)
        pred = model.predict(Xv)
        tn, fp, fn, tp = confusion_matrix(yv, pred, labels=[0, 1]).ravel()
        rows.append({"model": name, "roc_auc": roc_auc_score(yv, score(model, Xv)), "balanced_accuracy": balanced_accuracy_score(yv, pred),
                     "sensitivity": tp / (tp + fn), "specificity": tn / (tn + fp), "tn": tn, "fp": fp, "fn": fn, "tp": tp})
    return pd.DataFrame(rows)

def development_cv(Xd, yd, groups):
    # Five folds on train+validation; with recording groups, all segments of one recording stay in one fold.
    cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED) if groups is not None else StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    rows = []
    for name, model in models().items():
        result = cross_validate(model, Xd, yd, cv=cv, groups=groups, n_jobs=1,
                                scoring={"roc_auc": "roc_auc", "average_precision": "average_precision", "balanced_accuracy": "balanced_accuracy"})
        rows.append({"model": name, "roc_auc_mean": result["test_roc_auc"].mean(), "roc_auc_sd": result["test_roc_auc"].std(ddof=1),
                     "average_precision_mean": result["test_average_precision"].mean(), "balanced_accuracy_mean": result["test_balanced_accuracy"].mean()})
    return pd.DataFrame(rows)

def prediction_stability(X, y, Xv, n_refits=30):
    # The same bootstrap resamples of train are shared by every model; model seeds stay fixed,
    # so the spread reflects training-sample perturbation only.
    rng = np.random.default_rng(SEED)
    resamples = [rng.choice(len(y), size=len(y), replace=True) for _ in range(n_refits)]
    rows = []
    for name in ("single_tree", "bagging", "random_forest"):
        probs = np.asarray([clone(models()[name]).fit(X.iloc[idx], y.iloc[idx]).predict_proba(Xv)[:, 1] for idx in resamples])
        share = (probs >= .5).mean(axis=0)
        rows.append({"model": name, "prediction_sd_mean": probs.std(axis=0).mean(), "prediction_sd_max": probs.std(axis=0).max(),
                     "class_flip_rate": ((share > 0) & (share < 1)).mean()})
    return pd.DataFrame(rows)

def tree_count_curve(X, y, Xv, yv):
    rows = []
    for n in (1, 10, 50, 100, 300):
        for name, model in (("bagging", BaggingClassifier(estimator=DecisionTreeClassifier(random_state=SEED), n_estimators=n, oob_score=n >= 50, random_state=SEED)),
                            ("random_forest", RandomForestClassifier(n_estimators=n, max_features="sqrt", oob_score=n >= 50, random_state=SEED))):
            model.fit(X, y)
            rows.append({"model": name, "n_trees": n, "validation_roc_auc": roc_auc_score(yv, model.predict_proba(Xv)[:, 1]),
                         "oob_accuracy": model.oob_score_ if n >= 50 else np.nan})
    return pd.DataFrame(rows)

def feature_importance(X, y, Xv, yv):
    forest = RandomForestClassifier(n_estimators=300, random_state=SEED).fit(X, y)
    perm = permutation_importance(forest, Xv, yv, scoring="roc_auc", n_repeats=20, random_state=SEED)
    table = pd.DataFrame({"feature": X.columns, "impurity_importance": forest.feature_importances_,
                          "permutation_auc_drop_mean": perm.importances_mean, "permutation_auc_drop_sd": perm.importances_std})
    return table.sort_values("impurity_importance", ascending=False)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", choices=sorted(DATASETS), default="wdbc")
    args = parser.parse_args()
    out = Path(__file__).resolve().parents[4] / ".tmp" / "ensemble" / args.data
    out.mkdir(parents=True, exist_ok=True)
    train, valid, features, label, group = load(args.data)
    X, y, Xv, yv = train[features], train[label], valid[features], valid[label]
    table = fit_table(X, y, Xv, yv)
    table.to_csv(out / "model-comparison.csv", index=False)
    dev = pd.concat([train, valid], ignore_index=True)
    development_cv(dev[features], dev[label], dev[group] if group else None).to_csv(out / "cross-validation.csv", index=False)
    stability = prediction_stability(X, y, Xv)
    stability.to_csv(out / "prediction-stability.csv", index=False)
    tree_count_curve(X, y, Xv, yv).to_csv(out / "tree-count-curve.csv", index=False)
    feature_importance(X, y, Xv, yv).to_csv(out / "feature-importance.csv", index=False)
    (out / "run-info.json").write_text(json.dumps({"data": args.data, "label": label, "group": group, "seed": SEED,
                                                    "n_train": len(train), "n_validation": len(valid)}, indent=2), encoding="utf-8")
    print(table.round(4).to_string(index=False))
    print(stability.round(4).to_string(index=False))
    print("Wrote", out)

if __name__ == "__main__":
    main()
