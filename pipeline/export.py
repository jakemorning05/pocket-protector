"""Train the final models and export everything the site needs to site_data.json."""
import pandas as pd, numpy as np, json, os, math
from scipy.stats import norm
from sklearn.linear_model import Ridge
import train as T
from features import SITE, TEAMS, METRICS, km

D = os.path.join(os.path.dirname(__file__), '..', 'data')
F = T.F.copy()
FULL = T.SETS['+ market ratings']
OLD = T.SETS['points only (old site)']
ALPHA = 1.0
GROUPS = {
    'Home field': ['hfa'], 'Quarterbacks': ['d_qb', 'd_qb_x'],
    'Offense & defense efficiency': ['d_epa', 'd_sr', 'd_pass_epa', 'd_rush_epa', 'd_early_epa', 'd_neutral_epa', 'd_explosive', 'd_ypp'],
    'Points scored & allowed': ['d_pts'], 'Turnovers': ['d_turnovers'], 'Special teams': ['d_st'],
    'Rest & travel': ['rest_diff', 'd_bye', 'travel_diff', 'tz_diff', 'west_early'], 'Division game': ['div'],
    'Injuries': ['d_inj_off', 'd_inj_def'], 'Betting market’s earlier view': ['d_mkt'],
}

P = F[F.played]
hist = P[(P.season >= 2017) & (P.season <= 2025)].reset_index(drop=True)
m_new = Ridge(alpha=ALPHA, fit_intercept=False).fit(hist[FULL].values, hist.margin.values)
sigma = float(np.std(hist.margin.values - m_new.predict(hist[FULL].values)))
coef = dict(zip(FULL, m_new.coef_.tolist()))

# league scoring level to date (for totals)
F['lg_total'] = np.nan
for s in sorted(F.season.unique()):
    for w in sorted(F[F.season == s].week.unique()):
        prev = F[(F.season == s) & (F.week < w) & F.played].total_pts
        last = F[(F.season == s - 1) & F.played].total_pts
        n_last = 32 if len(last) else 0
        F.loc[(F.season == s) & (F.week == w), 'lg_total'] = (prev.sum() + (last.mean() * n_last if n_last else 0)) / max(1, len(prev) + n_last) if (len(prev) + n_last) else 44.0
F['one'] = 1.0
TC = ['one', 'lg_total', 's_pts', 's_epa', 's_pass_epa', 's_rush_epa', 's_early_epa', 's_neutral_epa', 's_explosive', 's_ypp', 's_turnovers', 's_mkt', 'wind', 'cold', 'dome']
H2 = F[F.played & (F.season >= 2017) & (F.season <= 2025)]
m_tot = Ridge(alpha=1.0, fit_intercept=False).fit(H2[TC].values, H2.total_pts.values)
tcoef = dict(zip(TC, m_tot.coef_.tolist()))


def ml_prob(hml, aml):
    if pd.isna(hml) or pd.isna(aml): return None
    imp = lambda x: 100 / (x + 100) if x > 0 else -x / (-x + 100)
    ph, pa = imp(hml), imp(aml)
    return ph / (ph + pa)


# ---------- 2026 games ----------
S = F[F.season == 2026].copy()
S['pred'] = m_new.predict(S[FULL].values)
# games further out are less certain (ratings move, QBs change, late-season resting): widen sigma by weeks ahead (drift.py)
CW = int(S[S.played].week.max()) + 1
try:
    DRIFT_C = json.load(open(f'{D}/drift.json'))['c']
except FileNotFoundError:
    DRIFT_C = 0.0
S['k_ahead'] = np.where(S.played, 0, np.clip(S.week - CW, 0, None))
S['p_home'] = norm.cdf(S.pred / (sigma * (1 + DRIFT_C * S.k_ahead)))
S['pred_total'] = m_tot.predict(S[TC].values)
games = []
for r in S.sort_values(['gameday', 'gametime', 'game_id']).itertuples():
    contrib = {g: round(float(sum(coef[c] * getattr(r, c) for c in cols)), 2) for g, cols in GROUPS.items()}
    mp = ml_prob(r.home_ml, r.away_ml)
    games.append({
        'id': r.game_id, 'wk': int(r.week), 'day': r.gameday, 'time': r.gametime, 'a': r.away, 'h': r.home,
        'as': None if pd.isna(r.away_score) else int(r.away_score), 'hs': None if pd.isna(r.home_score) else int(r.home_score),
        'm': round(float(r.pred), 2), 'p': round(float(r.p_home), 4), 'tot': round(float(r.pred_total), 1),
        'mk_spread': None if pd.isna(r.spread_line) else float(r.spread_line), 'mk_total': None if pd.isna(r.total_line) else float(r.total_line),
        'mk_p': None if mp is None else round(mp, 4), 'qa': r.away_qb, 'qh': r.home_qb, 'c': contrib,
        'neutral': int(r.neutral), 'div': int(r.div), 'wind': r.wind, 'temp': None if pd.isna(r.temp) else r.temp, 'dome': int(r.dome),
    })

# ---------- backtests ----------
def summ(pred, sd, y):
    d = T.scores(np.asarray(pred), sd, np.asarray(y)); return {k: round(float(v), 4) for k, v in d.items()}

cv_new, sd_new = T.loso(FULL, hist, ALPHA)
cv_old, sd_old = T.loso(OLD, hist, ALPHA)
hm = hist.spread_line.notna().values
bt = {
    'hist': {'new': summ(cv_new, sd_new, hist.margin), 'old': summ(cv_old, sd_old, hist.margin),
             'market': summ(hist.spread_line[hm], 13.5, hist.margin[hm]), 'games': int(len(hist)), 'seasons': '2017–2025'},
}
p26 = S[S.played]
m_old26 = Ridge(alpha=ALPHA, fit_intercept=False).fit(hist[OLD].values, hist.margin.values)
sd_o = float(np.std(hist.margin.values - m_old26.predict(hist[OLD].values)))
bt['y2026'] = {'new': summ(p26.pred, sigma, p26.margin), 'old': summ(m_old26.predict(p26[OLD].values), sd_o, p26.margin),
               'market': summ(p26.spread_line, 13.5, p26.margin), 'games': int(len(p26))}
# confidence tiers (held-out seasons, large sample) and 2026
def tiers(pred, sd, y):
    p = norm.cdf(np.asarray(pred) / sd); y = np.asarray(y)
    fav = np.maximum(p, 1 - p); won = np.where(y > 0, 1, np.where(y < 0, 0, 0.5)); right = np.where(p >= .5, won, 1 - won)
    out = []
    for lo, hi in [(.5, .6), (.6, .7), (.7, .8), (.8, 1.01)]:
        s = (fav >= lo) & (fav < hi) & (won != 0.5)
        out.append({'lo': lo, 'hi': min(hi, 1), 'n': int(s.sum()), 'pred': round(float(fav[s].mean()), 4) if s.any() else None, 'won': int(right[s].sum())})
    return out
bt['tiers_hist'] = tiers(cv_new, sd_new, hist.margin)
bt['tiers_2026'] = tiers(p26.pred, sigma, p26.margin)
# against the spread when the model disagrees with the market
hh = hist[hm].copy(); hh['cv'] = cv_new[hm]
ats = []
for thr in [1, 2, 3, 4, 5]:
    d = hh.cv - hh.spread_line; sel = d.abs() >= thr
    res = np.sign(hh.margin - hh.spread_line)[sel] * np.sign(d[sel])
    ats.append({'thr': thr, 'w': int((res > 0).sum()), 'l': int((res < 0).sum())})
bt['ats'] = ats
# weekly 2026 accuracy, model vs market
wk = []
for w_, g_ in p26.groupby('week'):
    dec = g_.margin != 0
    wk.append({'wk': int(w_), 'n': int(dec.sum()), 'model': int(((g_.pred > 0) == (g_.margin > 0))[dec].sum()), 'market': int(((g_.spread_line > 0) == (g_.margin > 0))[dec].sum())})
bt['weekly'] = wk
# feature group importance: std of each group's contribution across history
imp = {g: round(float(np.std(sum(coef[c] * hist[c] for c in cols))), 2) for g, cols in GROUPS.items()}
bt['importance'] = dict(sorted(imp.items(), key=lambda kv: -kv[1]))
bt['totals'] = {'model_mae_hist': None}

# ---------- team data ----------
rn = json.load(open(f'{D}/ratings_now.json')); cur = json.load(open(f'{D}/current.json'))
gm = pd.read_csv(f'{D}/games.csv'); gm = gm[(gm.season == 2026)]
dome_share = {t: float((gm[gm.home_team == t].roof.isin(['dome', 'closed'])).mean()) for t in TEAMS}
tg = pd.read_pickle(f'{D}/teamgames.pkl'); tg = tg[tg.season == 2026]
off = tg.groupby('team').agg(epa=('epa', 'mean'), sr=('sr', 'mean'), pass_epa=('pass_epa', 'mean'), rush_epa=('rush_epa', 'mean'),
                             early_epa=('early_epa', 'mean'), neutral_epa=('neutral_epa', 'mean'), explosive=('explosive', 'mean'), ypp=('ypp', 'mean'),
                             to=('turnovers', 'mean'), st=('st_epa', 'mean'), pass_oe=('pass_oe', 'mean'), cpoe=('cpoe', 'mean'),
                             rz_d=('rz_drives', 'sum'), rz_td=('rz_tds', 'sum'), sacks=('sacks', 'sum'), db=('dropbacks', 'sum'),
                             fum=('fumbles', 'sum'), fum_lost=('fumbles_lost', 'sum'), g=('game_id', 'count'))
dfn = tg.groupby('opp').agg(epa=('epa', 'mean'), sr=('sr', 'mean'), pass_epa=('pass_epa', 'mean'), rush_epa=('rush_epa', 'mean'),
                            early_epa=('early_epa', 'mean'), explosive=('explosive', 'mean'), ypp=('ypp', 'mean'), to=('turnovers', 'mean'),
                            rz_d=('rz_drives', 'sum'), rz_td=('rz_tds', 'sum'), sacks=('sacks', 'sum'), db=('dropbacks', 'sum'))
teams = {}
for i, t in enumerate(TEAMS):
    o, d = off.loc[t], dfn.loc[t]
    teams[t] = {
        'r': {m: [round(rn[m]['off'][i], 4), round(rn[m]['def'][i], 4)] for m in METRICS}, 'st': round(rn['st'][i], 3), 'mk': round(rn['mkt'][i], 3), 'mkt': round(rn['mkt_tot'][i], 3),
        'qb': cur['qb'][t]['qb'], 'q': round(cur['qb'][t]['q'], 4), 'qbase': round(cur['qb'][t]['base'], 4), 'qdb': int(cur['qb'][t]['db']),
        'inj': [round(x, 2) for x in cur['inj'][t]], 'site': SITE[t], 'dome': round(dome_share[t], 2),
        'off': {'epa': o.epa, 'sr': o.sr, 'pass_epa': o.pass_epa, 'rush_epa': o.rush_epa, 'early_epa': o.early_epa, 'neutral_epa': o.neutral_epa,
                'explosive': o.explosive, 'ypp': o.ypp, 'to': o.to, 'rz': o.rz_td / o.rz_d if o.rz_d else None, 'sack': o.sacks / o.db if o.db else None,
                'pass_oe': o.pass_oe, 'cpoe': o.cpoe, 'fum_luck': (o.fum_lost / o.fum) if o.fum else None},
        'def': {'epa': d.epa, 'sr': d.sr, 'pass_epa': d.pass_epa, 'rush_epa': d.rush_epa, 'early_epa': d.early_epa, 'explosive': d.explosive,
                'ypp': d.ypp, 'to': d.to, 'rz': d.rz_td / d.rz_d if d.rz_d else None, 'sack': d.sacks / d.db if d.db else None},
        'st_epa': o.st,
    }
    for k in ('off', 'def'):
        teams[t][k] = {kk: (None if v is None or (isinstance(v, float) and math.isnan(v)) else round(float(v), 4)) for kk, v in teams[t][k].items()}
    teams[t]['st_epa'] = round(float(o.st), 3)

out = {'games': games, 'teams': teams, 'coef': coef, 'tcoef': tcoef, 'sigma': round(sigma, 3), 'cw': CW, 'drift_c': DRIFT_C, 'groups': GROUPS, 'bt': bt, 'mkt_mu': round(rn['mkt_mu'], 3),
       'lg_total_now': float(F[(F.season == 2026) & ~F.played].lg_total.iloc[0]), 'overrides': cur['overrides'], 'injury_week': cur['injury_week'],
       'metrics': list(METRICS.keys())}
json.dump(out, open(f'{D}/site_data.json', 'w'), default=lambda x: None if (isinstance(x, float) and math.isnan(x)) else x)
print('sigma', round(sigma, 2))
print(json.dumps(bt['hist'])); print(json.dumps(bt['y2026'])); print(bt['importance']); print(bt['ats']); print(bt['tiers_hist']); print(bt['tiers_2026'])
tonight = [g for g in games if g['as'] is None][0]
print('tonight', tonight)
