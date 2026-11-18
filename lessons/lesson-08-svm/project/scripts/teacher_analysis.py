"""Run feasibility checks before writing teaching results. Outputs under .tmp/svm."""
import os
from pathlib import Path
BASE = Path(__file__).resolve().parents[1]; REPO = BASE.parents[2]
OUT = REPO/'.tmp/svm/feasibility'; OUT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault('MPLCONFIGDIR', str(REPO/'.tmp/svm/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
import warnings
import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from lab_utils import *

def run():
    warnings.filterwarnings('error', category=ConvergenceWarning)
    train, val = load_development()
    assert len(train) == 186 and len(val) == 62
    assert set(train.sample_id).isdisjoint(val.sample_id)
    geo = geometry_experiment(train)
    grid, models = parameter_experiment(train, val)
    scaling, scale_check = scaling_experiment(train, val)
    configs = select_validation_configs(grid)
    for name, table in [('geometry',geo['table']),('candidates',geo['candidates']),
                        ('deletion',geo['changes']),('contradiction',geo['contradiction']),
                        ('parameters',grid),('scaling',scaling)]:
        table.to_csv(OUT/f'{name}.csv',index=False)
    tests = evaluate_locked(configs, True, True)
    tests.to_csv(OUT/'locked-test.csv', index=False)
    for family, key in configs.items():
        noise_experiment(models[key], train, val).to_csv(OUT/f'noise-{family}.csv',index=False)
    draw_boundary(geo['model'],train,'Separable training subset',True,geo['scaler'],geo['subset']).savefig(OUT/'geometry.png',dpi=160)
    plt.close('all')
    for name, key in [('linear',('linear',1.,.1)),('rbf',('rbf',1.,.1)),('local_rbf',('rbf',100.,10.))]:
        draw_boundary(models[key],train,name).savefig(OUT/f'{name}.png',dpi=150); plt.close('all')
    lin = grid[grid.kernel == 'linear']
    fig,axes = plt.subplots(1,3,figsize=(13,3.7))
    for ax, key in zip(axes,['linear_width','mean_hinge','n_sv']):
        ax.semilogx(lin.C,lin[key],'o-',color='#087c77'); ax.set(xlabel='C',ylabel=key)
    fig.tight_layout(); fig.savefig(OUT/'c-path.png',dpi=160); plt.close(fig)
    summary = {'n_train': len(train),'n_validation':len(val),'features':FEATURES,
               'geometry_w':geo['model'].coef_[0].tolist(),'geometry_b':float(geo['model'].intercept_[0]),
               'geometry_half_width':geo['half_width'], 'subset_ids':geo['subset'].sample_id.tolist(),
               'scale_score_change':scale_check,'validation_configs':configs,
               'missing_train':int(train.isna().sum().sum()),
               'linear_only_min_hinge':float(lin.mean_hinge.min()),
               'checks':{'geometry_separates':bool((geo['candidates'].training_errors==0).all()),
                         'fixed_scaler_delete_non_sv':bool(geo['changes'].iloc[0].score_change_max < 1e-5),
                         'delete_sv_changes_solution':bool(geo['changes'].iloc[1].score_change_max > 1e-3),
                         'scaled_units_invariant':bool(scale_check['True'] < 1e-5),
                         'counterfactual_infeasible':bool((geo['contradiction'].errors >= 1).all()),
                         'test_guard_closed':isinstance(evaluate_locked(configs), str)}}
    assert all(summary['checks'].values()), summary['checks']
    (OUT/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print(lin[['C','linear_width','mean_hinge','train_errors','val_balanced_accuracy','n_sv']].to_string(index=False))
    print(grid[grid.kernel=='rbf'][['C','gamma','train_balanced_accuracy','val_balanced_accuracy']].to_string(index=False))

if __name__=='__main__': run()
