import pandas as pd, numpy as np
from scipy.stats import norm
from sklearn.linear_model import Ridge, LinearRegression
import train as T

F = T.F
P = F[F.played].copy()
hist = P[(P.season >= 2017) & (P.season <= 2025)].reset_index(drop=True)
test = P[P.season == 2026].reset_index(drop=True)
cols = T.SETS['+ injuries']

for alpha in [0.3, 1, 3]:
    cvp, sd = T.loso(cols, hist, alpha)
    print('alpha', alpha, {k: round(float(v), 4) for k, v in T.scores(cvp, sd, hist.margin.values).items()})
ALPHA = 1.0
cvp, sd = T.loso(cols, hist, ALPHA)
m, rsd, tp = T.fit_eval(cols, hist, test, ALPHA)
hist['model'] = cvp; test['model'] = tp
print('model sd', round(sd, 2), 'resid sd', round(rsd, 2))

# --- blend with market (held-out seasons) ---
h = hist[hist.spread_line.notna()].reset_index(drop=True)
bp = np.zeros(len(h))
for s in sorted(h.season.unique()):
    tr, te = h[h.season != s], h[h.season == s]
    lr = LinearRegression(fit_intercept=False).fit(tr[['spread_line', 'model']].values, tr.margin.values)
    bp[(h.season == s).values] = lr.predict(te[['spread_line', 'model']].values)
lr = LinearRegression(fit_intercept=False).fit(h[['spread_line', 'model']].values, h.margin.values)
print('blend weights (market, model):', lr.coef_.round(3))
sig_b = np.std(h.margin.values - bp)
print('market   2017-25', {k: round(float(v), 4) for k, v in T.scores(h.spread_line.values, 13.5, h.margin.values).items()})
print('blend    2017-25', {k: round(float(v), 4) for k, v in T.scores(bp, sig_b, h.margin.values).items()})
t2 = test[test.spread_line.notna()]
tb = lr.predict(t2[['spread_line', 'model']].values)
print('market   2026   ', {k: round(float(v), 4) for k, v in T.scores(t2.spread_line.values, 13.5, t2.margin.values).items()})
print('blend    2026   ', {k: round(float(v), 4) for k, v in T.scores(tb, sig_b, t2.margin.values).items()})
print('model    2026   ', {k: round(float(v), 4) for k, v in T.scores(t2.model.values, rsd, t2.margin.values).items()})

# --- against the spread when model disagrees with market ---
for thr in [1, 2, 3, 4, 6]:
    d = h.model - h.spread_line
    sel = d.abs() >= thr
    cover = np.sign(h.margin - h.spread_line)  # +1 home covered
    pick = np.sign(d)
    res = (cover[sel] * pick[sel])
    w, l = int((res > 0).sum()), int((res < 0).sum())
    print(f'ATS when model differs from line by {thr}+ pts: {w}-{l} ({w/(w+l)*100:.1f}%)')

# --- confidence tiers ---
p = norm.cdf(hist.model / sd)
fav = np.maximum(p, 1 - p); won = np.where(hist.margin > 0, 1, np.where(hist.margin < 0, 0, 0.5))
right = np.where(p >= .5, won, 1 - won)
for lo, hi in [(.5, .6), (.6, .7), (.7, .8), (.8, 1.01)]:
    s = (fav >= lo) & (fav < hi) & (won != 0.5)
    print(f'tier {lo:.0%}-{min(hi,1):.0%}: n={s.sum()} predicted {fav[s].mean():.3f} actual {right[s].mean():.3f}')

# --- coefficient table on standardized features ---
X = hist[cols]; sdv = X.std()
full = Ridge(alpha=ALPHA, fit_intercept=False).fit(X.values, hist.margin.values)
coef = pd.Series(full.coef_, index=cols)
print((coef * sdv).sort_values(key=abs, ascending=False).round(2).to_string())

# --- totals ---
P2 = F[F.played].copy()
P2['lg_total'] = np.nan
for s in sorted(P2.season.unique()):
    for w in sorted(P2[P2.season == s].week.unique()):
        prev = P2[(P2.season == s) & (P2.week < w)].total_pts
        last = P2[P2.season == s - 1].total_pts
        val = (prev.sum() + last.mean() * 32 if len(last) else prev.sum()) / (len(prev) + (32 if len(last) else 0)) if (len(prev) or len(last)) else 44.0
        P2.loc[(P2.season == s) & (P2.week == w), 'lg_total'] = val
tcols = ['lg_total', 's_pts', 's_epa', 's_pass_epa', 's_rush_epa', 's_early_epa', 's_neutral_epa', 's_explosive', 's_ypp', 's_turnovers', 'wind', 'cold', 'dome']
P2['one'] = 1.0
tc = ['one'] + tcols
H2 = P2[(P2.season >= 2017) & (P2.season <= 2025)].reset_index(drop=True); T2 = P2[P2.season == 2026].reset_index(drop=True)
pr = np.zeros(len(H2))
for s in sorted(H2.season.unique()):
    tr, te = H2[H2.season != s], H2[H2.season == s]
    r = Ridge(alpha=1.0, fit_intercept=False).fit(tr[tc].values, tr.total_pts.values)
    pr[(H2.season == s).values] = r.predict(te[tc].values)
r = Ridge(alpha=1.0, fit_intercept=False).fit(H2[tc].values, H2.total_pts.values)
tt = r.predict(T2[tc].values)
hh = H2.total_line.notna()
print('totals MAE 2017-25 model', round(np.abs(pr - H2.total_pts).mean(), 2), 'market', round(np.abs(H2.total_line - H2.total_pts)[hh].mean(), 2))
print('totals MAE 2026    model', round(np.abs(tt - T2.total_pts).mean(), 2), 'market', round(np.abs(T2.total_line - T2.total_pts).mean(), 2))
print('total coefs', dict(zip(tc, r.coef_.round(3))))
