"""Execute the predeclared teacher protocol; write only to project .tmp."""
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import json
import platform
import numpy as np
import pandas as pd
import sklearn
from sklearn.naive_bayes import BernoulliNB
from lab_utils import (FEATURES, fit_model, scores, threshold_table, choose_threshold,
                       reliability, dependence, hand_calculation, wilson, stress)

BASE = Path(__file__).resolve().parents[1]
OUT = BASE.parents[2]/'.tmp/naive-bayes/teacher-results'

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    train = pd.read_csv(BASE/'data/student/train.csv')
    val = pd.read_csv(BASE/'data/student/validation.csv')
    test = pd.read_csv(BASE/'data/student/locked-test-features.csv').merge(
        pd.read_csv(BASE/'data/teacher/locked-test-labels.csv'), on='sample_id',
        validate='one_to_one', sort=False)
    model = fit_model(train)
    p = model.predict_proba(val[FEATURES])[:, 1]
    thresholds = threshold_table(val.bladder_inflammation, p)
    threshold = choose_threshold(thresholds)
    thresholds.to_csv(OUT/'B-thresholds.csv', index=False)
    baseline = np.full(len(val), train.bladder_inflammation.mean())
    report = {'versions': {'python': platform.python_version(), 'numpy': np.__version__,
                           'pandas': pd.__version__, 'sklearn': sklearn.__version__},
              'class_counts': {name: frame.bladder_inflammation.value_counts().to_dict()
                               for name, frame in [('train',train),('validation',val),('test',test)]},
              'chosen_threshold': threshold,
              'validation': scores(val.bladder_inflammation, p, threshold),
              'baseline_validation': scores(val.bladder_inflammation, baseline)}
    reliability(val.bladder_inflammation, p).to_csv(OUT/'C-reliability.csv', index=False)
    dep = dependence(train).sort_values('difference', key=abs, ascending=False)
    dep.to_csv(OUT/'C-dependence.csv', index=False)
    # Six-bit illustrative symptom profile, fixed before looking at evaluation results.
    x = [0,0,0,1,1,1]
    hand, weights, posterior = hand_calculation(train, x)
    hand.to_csv(OUT/'A-hand-calculation.csv', index=False)
    predicted = model.predict_proba(pd.DataFrame([x], columns=FEATURES))[0,1]
    assert np.isclose(posterior, predicted, atol=1e-12)
    report['hand'] = dict(x=x, weights=weights.tolist(), posterior=posterior)
    duplicate_rows = []
    for copies in [0,1,5]:
        tr, va = train[FEATURES].copy(), val[FEATURES].copy()
        for i in range(copies):
            tr[f'lumbar_copy_{i}'] = tr.lumbar_pain
            va[f'lumbar_copy_{i}'] = va.lumbar_pain
        dup = BernoulliNB(alpha=1, binarize=None).fit(tr, train.bladder_inflammation)
        dp = dup.predict_proba(va)[:,1]
        duplicate_rows.append(dict(extra_copies=copies, **scores(val.bladder_inflammation,dp),
                                   mean_max_probability=float(np.maximum(dp,1-dp).mean()),
                                   max_probability_change=float(np.abs(dp-p).max())))
        pd.DataFrame({'sample_id':val.sample_id, 'y':val.bladder_inflammation,
                      'original_probability':p, 'duplicate_probability':dp}).to_csv(
                          OUT/f'C-duplicate-{copies}-probabilities.csv', index=False)
    pd.DataFrame(duplicate_rows).to_csv(OUT/'C-duplicate-summary.csv',index=False)
    tp = model.predict_proba(test[FEATURES])[:,1]
    final = scores(test.bladder_inflammation, tp, threshold)
    report['test'] = final
    report['wilson'] = dict(accuracy=wilson(final['tp']+final['tn'],len(test)),
                            sensitivity=wilson(final['tp'],final['tp']+final['fn']),
                            specificity=wilson(final['tn'],final['tn']+final['fp']))
    profiles_train = set(map(tuple, train[FEATURES].to_numpy()))
    report['test_profile_overlap'] = dict(
        unique_profiles=len(test[FEATURES].drop_duplicates()),
        rows_seen_in_train=sum(tuple(row) in profiles_train for row in test[FEATURES].to_numpy()))
    stress(model,test,test.bladder_inflammation,threshold).to_csv(OUT/'D-stress.csv',index=False)
    # Transfer uses EXACTLY the same row IDs as the primary task, no re-stratification.
    nm = fit_model(train,'nephritis')
    nv = nm.predict_proba(val[FEATURES])[:,1]
    nt = choose_threshold(threshold_table(val.nephritis,nv))
    report['nephritis'] = dict(threshold=nt, validation=scores(val.nephritis,nv,nt),
                              test=scores(test.nephritis,nm.predict_proba(test[FEATURES])[:,1],nt),
                              test_positive=int(test.nephritis.sum()))
    dependence(train,'nephritis').to_csv(OUT/'E-nephritis-dependence.csv',index=False)
    (OUT/'results.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__ == '__main__':
    main()
