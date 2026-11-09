"""Train margin + total models on 2017-2025 and test on 2026 (walk-forward features), compare feature sets and the market."""
import pandas as pd, numpy as np, os, json, sys
from scipy.stats import norm
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor

D = os.path.join(os.path.dirname(__file__), '..', 'data')
F = pd.read_pickle(f'{D}/features.pkl')
F['hfa'] = 1 - F.neutral
F['d_bye'] = F.home_bye - F.away_bye
F['tz_diff'] = F.tz_away - F.tz_home
F['d_inj_off'] = F.inj_off_h - F.inj_off_a
F['d_inj_def'] = F.inj_def_h - F.inj_def_a
F['d_qb_x'] = F.d_qbdelta * 35  # EPA per dropback -> EPA per game scale

SETS = {
    'points only (old site)': ['hfa', 'd_pts'],
    '+ EPA': ['hfa', 'd_pts', 'd_epa'],
    '+ efficiency splits': ['hfa', 'd_pts', 'd_epa', 'd_sr', 'd_pass_epa', 'd_rush_epa', 'd_early_epa', 'd_neutral_epa', 'd_explosive', 'd_ypp', 'd_turnovers', 'd_st'],
    '+ QB': ['hfa', 'd_pts', 'd_epa', 'd_sr', 'd_pass_epa', 'd_rush_epa', 'd_early_epa', 'd_neutral_epa', 'd_explosive', 'd_ypp', 'd_turnovers', 'd_st', 'd_qb_x', 'd_qb'],
    '+ rest/travel/division': ['hfa', 'd_pts', 'd_epa', 'd_sr', 'd_pass_epa', 'd_rush_epa', 'd_early_epa', 'd_neutral_epa', 'd_explosive', 'd_ypp', 'd_turnovers', 'd_st', 'd_qb_x', 'd_qb', 'rest_diff', 'd_bye', 'travel_diff', 'tz_diff', 'west_early', 'div'],
    '+ injuries': ['hfa', 'd_pts', 'd_epa', 'd_sr', 'd_pass_epa', 'd_rush_epa', 'd_early_epa', 'd_neutral_epa', 'd_explosive', 'd_ypp', 'd_turnovers', 'd_st', 'd_qb_x', 'd_qb', 'rest_diff', 'd_bye', 'travel_diff', 'tz_diff', 'west_early', 'div', 'd_inj_off', 'd_inj_def'],
}


def scores(pred_margin, sigma, y):
    p = norm.cdf(pred_margin / sigma)
    won = np.where(y > 0, 1.0, np.where(y < 0, 0.0, 0.5))
    dec = won != 0.5
    acc = ((p[dec] >= 0.5) == (won[dec] == 1)).mean()
    brier = ((p - won) ** 2).mean()
    pc = np.clip(p, 1e-4, 1 - 1e-4)
    ll = -(won * np.log(pc) + (1 - won) * np.log(1 - pc)).mean()
    mae = np.abs(pred_margin - y).mean()
    return dict(acc=acc, brier=brier, logloss=ll, mae=mae, n=int(dec.sum()))


def fit_eval(cols, train, test, alpha=10.0, model='ridge'):
    X, y = train[cols].values, train.margin.values
    if model == 'ridge':
        m = Ridge(alpha=alpha, fit_intercept=False).fit(X, y)
    else:
        m = HistGradientBoostingRegressor(max_iter=300, learning_rate=0.03, max_depth=3, min_samples_leaf=40, l2_regularization=1.0, random_state=0).fit(X, y)
    resid_sd = np.std(y - m.predict(X))
    return m, resid_sd, m.predict(test[cols].values)


def loso(cols, data, alpha=10.0, model='ridge'):
    preds = np.zeros(len(data)); sd = []
    for s in sorted(data.season.unique()):
        tr, te = data[data.season != s], data[data.season == s]
        m, rsd, p = fit_eval(cols, tr, te, alpha, model)
        preds[(data.season == s).values] = p; sd.append(rsd)
    return preds, float(np.mean(sd))


if __name__ == '__main__':
    P = F[F.played].copy()
    hist = P[(P.season >= 2017) & (P.season <= 2025)].reset_index(drop=True)
    test = P[P.season == 2026].reset_index(drop=True)
    rows = []
    mk_sigma = 13.5
    for name, cols in SETS.items():
        cvp, sd = loso(cols, hist)
        m, rsd, tp = fit_eval(cols, hist, test)
        rows.append((name, scores(cvp, sd, hist.margin.values), scores(tp, rsd, test.margin.values)))
    # gradient boosting on the full set
    cols = SETS['+ injuries']
    cvp, sd = loso(cols, hist, model='gbm'); m, rsd, tp = fit_eval(cols, hist, test, model='gbm')
    rows.append(('gradient boosting, all features', scores(cvp, sd, hist.margin.values), scores(tp, rsd, test.margin.values)))
    # market
    hm = hist[hist.spread_line.notna()]; tm = test[test.spread_line.notna()]
    rows.append(('BETTING MARKET (closing spread)', scores(hm.spread_line.values, mk_sigma, hm.margin.values), scores(tm.spread_line.values, mk_sigma, tm.margin.values)))
    print(f"{'model':38s} | {'2017-25 (held-out seasons)':38s} | 2026 weeks 1-9")
    for n, a, b in rows:
        f = lambda d: f"acc {d['acc']*100:5.1f}% brier {d['brier']:.4f} mae {d['mae']:5.2f}"
        print(f"{n:38s} | {f(a)} | {f(b)} (n={b['n']})")
    # alpha check for best linear set
    for alpha in [1, 10, 50, 200]:
        cvp, sd = loso(SETS['+ injuries'], hist, alpha)
        print('alpha', alpha, scores(cvp, sd, hist.margin.values))
