"""Held-out-season tests of injury groups, rating settings, recency and QB shrinkage."""
import sys, json, itertools
import numpy as np, pandas as pd
import features as FE
import train as T

BASE = T.SETS['+ injuries']
GROUPED = [c for c in BASE if c not in ('d_inj_off', 'd_inj_def')] + ['d_inj_' + g for g in FE.INJ_GROUPS]


def prep(F):
    F = F.copy()
    F['hfa'] = 1 - F.neutral; F['d_bye'] = F.home_bye - F.away_bye; F['tz_diff'] = F.tz_away - F.tz_home
    F['d_inj_off'] = F.inj_off_h - F.inj_off_a; F['d_inj_def'] = F.inj_def_h - F.inj_def_a; F['d_qb_x'] = F.d_qbdelta * 35
    return F


def evaluate(F, cols, alpha=1.0):
    P = F[F.played]
    hist = P[(P.season >= 2017) & (P.season <= 2025)].reset_index(drop=True)
    test = P[P.season == 2026].reset_index(drop=True)
    cvp, sd = T.loso(cols, hist, alpha)
    m, rsd, tp = T.fit_eval(cols, hist, test, alpha)
    a = T.scores(cvp, sd, hist.margin.values); b = T.scores(tp, rsd, test.margin.values)
    return {'acc': round(a['acc'] * 100, 2), 'brier': round(a['brier'], 5), 'll': round(a['logloss'], 5), 'acc26': round(b['acc'] * 100, 1), 'brier26': round(b['brier'], 4)}


def run(params):
    return prep(FE.build(params, out_path='/tmp/claude-0/-home-claude/daea9209-2fd0-5f1c-ae7d-fcea506e371f/scratchpad/f.pkl', write_extras=False))


if __name__ == '__main__':
    stage = sys.argv[1]
    if stage == 'inj':
        F = run({})
        print('baseline (off/def injuries)', evaluate(F, BASE))
        print('position-group injuries   ', evaluate(F, GROUPED))
        print('both                      ', evaluate(F, BASE + ['d_inj_' + g for g in FE.INJ_GROUPS]))
    elif stage == 'grid':
        cols = GROUPED if sys.argv[2] == 'grouped' else BASE
        res = []
        for hl, lm, rm, qk in itertools.product([None, 8, 5], [0.6, 1.0, 1.6], [0.8, 1.0, 1.3], [220.0]):
            r = evaluate(run({'hl': hl, 'lam_mult': lm, 'rho_mult': rm, 'qb_k': qk}), cols)
            res.append(({'hl': hl, 'lam': lm, 'rho': rm, 'qbk': qk}, r)); print(res[-1], flush=True)
        res.sort(key=lambda x: x[1]['brier'])
        print('BEST'); [print(x) for x in res[:5]]
    elif stage == 'qb':
        cols = GROUPED if sys.argv[2] == 'grouped' else BASE
        best = json.loads(sys.argv[3])
        for qk in [100.0, 220.0, 400.0]:
            for qp in [-0.10, -0.06, -0.02]:
                print(qk, qp, evaluate(run({**best, 'qb_k': qk, 'qb_prior': qp}), cols), flush=True)
