"""How much less certain is a prediction made k weeks before the game?

A game's margin prediction depends on each team's ratings, QB and injuries at kickoff. A prediction made k weeks
earlier uses older ratings, the QB who was starting then, and no injury report. The gap between the two
("drift") adds variance: sigma_k^2 = sigma^2 + Var(drift_k). Measured on 2017-2025, checked on outcomes.
Writes data/drift.json: {'sigma_k': [...], 'var_k': [...], 'table': [...]}.
"""
import pandas as pd, numpy as np, json, os
from scipy.stats import norm

D = os.path.join(os.path.dirname(__file__), '..', 'data')
F = pd.read_pickle(f'{D}/features.pkl')
R = pd.read_pickle(f'{D}/rating_at.pkl')
rating_at, TEAMS = R['rating_at'], R['teams']
TI = {t: i for i, t in enumerate(TEAMS)}
site = json.load(open(f'{D}/site_data.json'))
C, SIG = site['coef'], site['sigma']
METRICS = [k[2:] for k in C if k.startswith('d_') and k[2:] in site['teams'][TEAMS[0]]['r']] if 'r' in site['teams'][TEAMS[0]] else None
if not METRICS:
    METRICS = ['pts', 'epa', 'sr', 'pass_epa', 'rush_epa', 'early_epa', 'neutral_epa', 'explosive', 'ypp', 'turnovers']

# one row per (team, game) with that team's QB numbers and injury load at kickoff
rows = []
for g in F.itertuples():
    for side, t in (('h', g.home), ('a', g.away)):
        rows.append(dict(season=g.season, week=g.week, team=t, game_id=g.game_id, q=getattr(g, 'q_' + side), qd=getattr(g, 'qdelta_' + side),
                         inj_off=getattr(g, 'inj_off_' + side), inj_def=getattr(g, 'inj_def_' + side)))
TG = pd.DataFrame(rows).sort_values(['season', 'team', 'week'])


def rating_part(s, w, t):
    r = rating_at[(s, w)]; i = TI[t]
    v = sum(C['d_' + m] * (r[m][0][i] + r[m][1][i]) for m in METRICS)
    return v + C['d_st'] * r['st'][i]


def qb_part(q, qd):
    return C['d_qb'] * q + C['d_qb_x'] * 35 * qd


def inj_part(o, d):
    return C['d_inj_off'] * o + C['d_inj_def'] * d


def team_power_at_kickoff(row):
    return rating_part(row.season, row.week, row.team) + qb_part(row.q, row.qd) + inj_part(row.inj_off, row.inj_def)


def team_power_ahead(s, w0, t, tg_team):
    """What we'd have said about team t when standing at week w0: ratings before w0, QB from the latest game
    up to w0 (the week-w0 starter is usually known), no injury report."""
    prev = tg_team[tg_team.week <= w0]
    if not len(prev) or (s, w0) not in rating_at:
        return None
    last = prev.iloc[-1]
    return rating_part(s, w0, t) + qb_part(last.q, last.qd)


out = []
for (s, t), tg in TG[(TG.season >= 2017) & (TG.season <= 2025)].groupby(['season', 'team']):
    for row in tg.itertuples():
        pk = team_power_at_kickoff(row)
        for k in range(1, 10):
            w0 = row.week - k
            if w0 < 2:  # need at least one game of the season played
                continue
            pa = team_power_ahead(s, w0, t, tg)
            if pa is not None:
                out.append((row.game_id, t, k, pk - pa))
DR = pd.DataFrame(out, columns=['game_id', 'team', 'k', 'drift'])

# game-level drift = home drift - away drift, matched on the same k
G = F[(F.season >= 2017) & (F.season <= 2025) & F.played].set_index('game_id')
H = DR.merge(G[['home']], left_on=['game_id', 'team'], right_on=['game_id', 'home'])
A = DR.merge(G[['away']], left_on=['game_id', 'team'], right_on=['game_id', 'away'])
GD = H[['game_id', 'k', 'drift']].merge(A[['game_id', 'k', 'drift']], on=['game_id', 'k'], suffixes=('_h', '_a'))
GD['d'] = GD.drift_h - GD.drift_a

# outcomes check: model margin at kickoff (same coefficients as the site) and the k-weeks-ahead version
X = G.copy()
X['hfa'] = 1 - X.neutral; X['d_bye'] = X.home_bye - X.away_bye; X['tz_diff'] = X.tz_away - X.tz_home
X['d_inj_off'] = X.inj_off_h - X.inj_off_a; X['d_inj_def'] = X.inj_def_h - X.inj_def_a; X['d_qb_x'] = X.d_qbdelta * 35
X['m'] = sum(X[c] * v for c, v in C.items())
GD = GD.merge(X[['m', 'margin']], left_on='game_id', right_index=True)
GD['m_ahead'] = GD.m - GD.d
won = lambda y: np.where(y > 0, 1.0, np.where(y < 0, 0.0, 0.5))


def ll(p, y):
    p = np.clip(p, 1e-4, 1 - 1e-4); w = won(y)
    return float(-(w * np.log(p) + (1 - w) * np.log(1 - p)).mean())


GD = GD.merge(G[['week']], left_on='game_id', right_index=True)
GD['w0'] = GD.week - GD.k
# the week we're standing at now: first week after the last one with a completed game
cw = int(F[(F.season == 2026) & F.played].week.max()) + 1
lo, hi = max(2, cw - 3), min(17, cw + 2)
grid = np.arange(9.0, 24.01, 0.05)
best = lambda m, y: grid[np.argmin([ll(norm.cdf(m / sg), y) for sg in grid])]
table = []
for k in range(1, 10):
    sub = GD[(GD.k == k) & GD.w0.between(lo, hi)]
    if len(sub) < 150:
        continue
    b0, bk = best(sub.m, sub.margin), best(sub.m_ahead, sub.margin)
    table.append(dict(k=k, n=len(sub), drift_sd=round(float(sub.d.std()), 2), sigma_kickoff=round(float(b0), 2), sigma_ahead=round(float(bk), 2),
                      ratio=round(float(bk / b0), 3),
                      acc_kickoff=round(float(((sub.m > 0) == (sub.margin > 0))[sub.margin != 0].mean()), 4),
                      acc_ahead=round(float(((sub.m_ahead > 0) == (sub.margin > 0))[sub.margin != 0].mean()), 4)))
TB = pd.DataFrame(table)
# ratio_k = 1 + c*k, weighted least squares through the origin
c = float(((TB.ratio - 1) * TB.k * TB.n).sum() / ((TB.k ** 2) * TB.n).sum())
sigma_k = [round(SIG * (1 + c * k), 3) for k in range(0, 19)]
json.dump({'cw': cw, 'window': [lo, hi], 'c': round(c, 4), 'sigma_k': sigma_k, 'table': table}, open(f'{D}/drift.json', 'w'), indent=1)
print(TB.to_string(index=False))
print('standing at week', cw, 'window', lo, hi, 'c = %.4f' % c)
print('sigma_k', sigma_k[:10])
