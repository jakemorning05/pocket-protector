"""Pre-game features for every regular-season game 2017-2026, using only information available before kickoff.

Output: data/features.pkl (one row per game, home perspective) and data/ratings_now.pkl (current team ratings).
"""
import pandas as pd, numpy as np, os, re, math, json

D = os.path.join(os.path.dirname(__file__), '..', 'data')
FIX = {'SD': 'LAC', 'OAK': 'LV', 'STL': 'LA', 'LAR': 'LA'}
TEAMS = sorted(['ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE', 'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAX', 'KC',
                'LV', 'LAC', 'LA', 'MIA', 'MIN', 'NE', 'NO', 'NYG', 'NYJ', 'PHI', 'PIT', 'SF', 'SEA', 'TB', 'TEN', 'WAS'])
TI = {t: i for i, t in enumerate(TEAMS)}
N = len(TEAMS)

# Home stadium coordinates and time zone (hours vs. US Eastern during the season)
SITE = {
    'ARI': (33.53, -112.26, -3), 'ATL': (33.76, -84.40, 0), 'BAL': (39.28, -76.62, 0), 'BUF': (42.77, -78.79, 0),
    'CAR': (35.23, -80.85, 0), 'CHI': (41.86, -87.62, -1), 'CIN': (39.10, -84.52, 0), 'CLE': (41.51, -81.70, 0),
    'DAL': (32.75, -97.09, -1), 'DEN': (39.74, -105.02, -2), 'DET': (42.34, -83.05, 0), 'GB': (44.50, -88.06, -1),
    'HOU': (29.68, -95.41, -1), 'IND': (39.76, -86.16, 0), 'JAX': (30.32, -81.64, 0), 'KC': (39.05, -94.48, -1),
    'LV': (36.09, -115.18, -3), 'LAC': (33.95, -118.34, -3), 'LA': (33.95, -118.34, -3), 'MIA': (25.96, -80.24, 0),
    'MIN': (44.97, -93.26, -1), 'NE': (42.09, -71.26, 0), 'NO': (29.95, -90.08, -1), 'NYG': (40.81, -74.07, 0),
    'NYJ': (40.81, -74.07, 0), 'PHI': (39.90, -75.17, 0), 'PIT': (40.45, -80.02, 0), 'SF': (37.40, -121.97, -3),
    'SEA': (47.60, -122.33, -3), 'TB': (27.98, -82.50, 0), 'TEN': (36.17, -86.77, -1), 'WAS': (38.91, -76.86, 0),
}
NEUTRAL = {
    'Wembley Stadium': (51.56, -0.28, 5), 'Tottenham Stadium': (51.60, -0.07, 5), 'Tottenham Hotspur Stadium': (51.60, -0.07, 5),
    'Twickenham Stadium': (51.46, -0.34, 5), 'Azteca Stadium': (19.30, -99.15, -1), 'Estadio Banorte': (19.30, -99.15, -1),
    'Allianz Arena': (48.22, 11.62, 6), 'FC Bayern Munich Stadium': (48.22, 11.62, 6), 'Deutsche Bank Park': (50.07, 8.65, 6),
    'Arena Corinthians': (-23.55, -46.47, 1), 'Maracana Stadium': (-22.91, -43.23, 1), 'Melbourne Cricket Ground': (-37.82, 144.98, 16),
    'Stade de France': (48.92, 2.36, 6), 'Bernabeu': (40.45, -3.69, 6),
    'State Farm Stadium': SITE['ARI'], 'TIAA Bank Stadium': SITE['JAX'], 'Ford Field': SITE['DET'], 'SoFi Stadium': SITE['LA'],
    'Acrisure Stadium': SITE['PIT'], 'FirstEnergy Stadium': SITE['CLE'], 'MetLife Stadium': SITE['NYG'], 'Lucas Oil Stadium': SITE['IND'],
    'Hard Rock Stadium': SITE['MIA'],
}


def home_site(team, season):
    if team == 'LV' and season <= 2019: return (37.75, -122.20, -3)  # Oakland
    if team == 'LAC' and season == 2016: return (32.78, -117.12, -3)  # San Diego
    return SITE[team]


def km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def schedules():
    g = pd.read_csv(f'{D}/games.csv')
    g = g[(g.season >= 2016) & (g.game_type == 'REG')].copy()
    for c in ['home_team', 'away_team']:
        g[c] = g[c].replace(FIX)
    g['neutral'] = (g.location == 'Neutral').astype(int)
    g['played'] = g.home_score.notna()
    g['margin'] = g.home_score - g.away_score
    g['total_pts'] = g.home_score + g.away_score
    return g.reset_index(drop=True)


# ---------- opponent-adjusted ridge ratings ----------
def ridge(rows, y, prior_off, prior_def, lam, hfa_prior, hfa_lam, wts=None):
    """rows: arrays t, o, h (home=+1, away=-1, neutral=0). Model y = mu + off[t] - def[o] + h*hfa/2."""
    P = 2 * N + 2
    A = np.zeros((P, P)); b = np.zeros(P)
    t, o, h = rows
    X = np.zeros((len(y), P))
    X[np.arange(len(y)), t] = 1
    X[np.arange(len(y)), N + o] = -1
    X[:, 2 * N] = 1
    X[:, 2 * N + 1] = h / 2
    if wts is None: wts = np.ones(len(y))
    Xw = X * wts[:, None]
    A += X.T @ Xw; b += Xw.T @ y
    idx = np.arange(2 * N)
    A[idx, idx] += lam
    b[:N] += lam * prior_off; b[N:2 * N] += lam * prior_def
    A[2 * N + 1, 2 * N + 1] += hfa_lam; b[2 * N + 1] += hfa_lam * hfa_prior
    A[2 * N, 2 * N] += 1e-6
    x = np.linalg.solve(A, b)
    return x[:N], x[N:2 * N], x[2 * N], x[2 * N + 1]


METRICS = {  # name: (lambda in games, regression to mean for next season, hfa prior, hfa strength)
    'pts': (3.0, 0.45, 1.5, 30), 'epa': (4.0, 0.55, 0.0, 30), 'sr': (4.0, 0.55, 0.0, 30), 'pass_epa': (4.0, 0.55, 0.0, 30),
    'rush_epa': (6.0, 0.45, 0.0, 30), 'early_epa': (4.0, 0.55, 0.0, 30), 'neutral_epa': (4.0, 0.55, 0.0, 30),
    'explosive': (5.0, 0.5, 0.0, 30), 'ypp': (4.0, 0.55, 0.0, 30), 'turnovers': (8.0, 0.2, 0.0, 30),
}


# Tuned on held-out seasons 2017-2025 (exp2.py): stronger shrinkage, more carryover from last season,
# no extra recency weighting, and unknown QBs assumed clearly below average.
PARAMS = {'lam_mult': 1.6, 'rho_mult': 1.3, 'hl': None, 'qb_k': 300.0, 'qb_prior': -0.14}
INJ_GROUPS = ['OL', 'SK', 'RB', 'DL', 'LB', 'DB']
POS_GROUP = {**{p: 'OL' for p in ['T', 'G', 'C', 'OT', 'OG', 'OL', 'LT', 'RT', 'LG', 'RG']}, 'WR': 'SK', 'TE': 'SK', 'RB': 'RB', 'FB': 'RB', 'HB': 'RB',
             **{p: 'DL' for p in ['DE', 'DT', 'NT', 'DL', 'EDGE']}, **{p: 'LB' for p in ['LB', 'ILB', 'OLB', 'MLB']}, **{p: 'DB' for p in ['CB', 'S', 'FS', 'SS', 'DB']}}


def build(params=None, out_path=None, write_extras=True):
    P_ = {**PARAMS, **(params or {})}
    sch = schedules()
    tg = pd.read_pickle(f'{D}/teamgames.pkl')
    qb = pd.read_pickle(f'{D}/qb_games.pkl')
    for c in ['team', 'opp', 'home_team', 'away_team']:
        tg[c] = tg[c].replace(FIX)
    qb['team'] = qb['team'].replace(FIX)
    # team-game rows with points from schedules
    pts = pd.concat([
        sch[sch.played][['game_id', 'season', 'week', 'home_team', 'away_team', 'home_score', 'neutral']].rename(columns={'home_team': 'team', 'away_team': 'opp', 'home_score': 'pts'}).assign(side=1),
        sch[sch.played][['game_id', 'season', 'week', 'away_team', 'home_team', 'away_score', 'neutral']].rename(columns={'away_team': 'team', 'home_team': 'opp', 'away_score': 'pts'}).assign(side=-1),
    ])
    pts['h'] = np.where(pts.neutral == 1, 0, pts.side)
    tg = pts.merge(tg.drop(columns=['season', 'week', 'opp', 'home', 'home_team', 'away_team']), on=['game_id', 'team'], how='left')
    for m in ['pass_epa', 'rush_epa', 'early_epa', 'neutral_epa']:
        tg[m] = tg[m].fillna(tg['epa'])
    tg['st_epa'] = tg['st_epa'].fillna(0)

    # ---------- ratings by season/week ----------
    seasons = sorted(sch.season.unique())
    final = {m: (np.zeros(N), np.zeros(N)) for m in METRICS}
    st_final = np.zeros(N)
    rating_at = {}  # (season, week) -> dict
    for s in seasons:
        rho = {m: min(0.9, METRICS[m][1] * P_['rho_mult']) for m in METRICS}
        prior = {m: (final[m][0] * rho[m], final[m][1] * rho[m]) for m in METRICS}
        st_prior = st_final * 0.3
        maxw = int(sch[sch.season == s].week.max())
        for w in range(1, maxw + 2):
            rows = tg[(tg.season == s) & (tg.week < w)]
            r = {}
            t = rows.team.map(TI).values; o = rows.opp.map(TI).values; h = rows.h.values.astype(float)
            wts = np.power(0.5, (w - 1 - rows.week.values) / P_['hl']) if P_['hl'] else None
            for m, (lam, _, hp, hl) in METRICS.items():
                if len(rows) == 0:
                    r[m] = (prior[m][0].copy(), prior[m][1].copy(), np.nan, hp)
                else:
                    off, de, mu, hfa = ridge((t, o, h), rows[m].values.astype(float), prior[m][0], prior[m][1], lam * P_['lam_mult'], hp, hl, wts)
                    r[m] = (off, de, mu, hfa)
            # special teams: shrunk per-game mean toward prior
            g_st = rows.groupby('team').st_epa.agg(['sum', 'count']).reindex(TEAMS).fillna(0)
            r['st'] = (g_st['sum'].values + 4 * st_prior) / (g_st['count'].values + 4)
            # turnover luck: share of own fumbles lost (league avg ~0.5); low value predictive of nothing, used as descriptive
            rating_at[(s, w)] = r
        for m in METRICS:
            final[m] = (rating_at[(s, maxw + 1)][m][0], rating_at[(s, maxw + 1)][m][1])
        st_final = rating_at[(s, maxw + 1)]['st']

    # league means per season (for pts) to anchor totals
    # ---------- QB quality ----------
    qb = qb.merge(sch[['game_id', 'gameday']], on='game_id', how='left').sort_values('gameday')
    qb_hist = {}  # qb_id -> list of (season, week, db, epa)
    for r_ in qb.itertuples():
        qb_hist.setdefault(r_.qb_id, []).append((r_.season, r_.week, r_.db, r_.epa))
    QB_PRIOR, QB_K = P_['qb_prior'], P_['qb_k']

    def qb_quality(qid, s, w):
        if not isinstance(qid, str) or qid not in qb_hist: return QB_PRIOR, 0
        num = den = 0.0
        for (ss, ww, db, epa) in qb_hist[qid]:
            if ss > s or (ss == s and ww >= w): continue
            wt = 1.0 if ss == s else 0.65 if ss == s - 1 else 0.35 if ss == s - 2 else 0.15
            num += wt * epa; den += wt * db
        return (num + QB_K * QB_PRIOR) / (den + QB_K), den

    team_qb = qb.groupby(['season', 'week', 'team']).apply(lambda x: list(zip(x.qb_id, x.db)), include_groups=False).to_dict()

    def team_baseline(team, s, w):
        """Dropback-weighted quality of QBs who played for the team in the games behind the current ratings."""
        num = den = 0.0
        weeks = [(s, ww) for ww in range(1, w)]
        if w <= 4: weeks += [(s - 1, ww) for ww in range(10, 19)]
        for key in weeks:
            for qid, db in team_qb.get((key[0], key[1], team), []):
                q, _ = qb_quality(qid, s, w)
                num += q * db; den += db
        return num / den if den else QB_PRIOR

    # ---------- injuries (non-QB), snap-weighted ----------
    def norm(n):
        n = re.sub(r"[^a-z ]", "", str(n).lower())
        return re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", n).strip()
    cache = f'{D}/inj_cache.pkl'
    if os.path.exists(cache):
        inj_load = pd.read_pickle(cache)
    else:
        inj_load = {}
        for s in range(2016, 2027):
            try:
                inj = pd.read_csv(f'{D}/injuries_{s}.csv'); sn = pd.read_csv(f'{D}/snap_counts_{s}.csv')
            except FileNotFoundError:
                continue
            inj = inj[(inj.game_type == 'REG') & inj.report_status.isin(['Out', 'Doubtful']) & (inj.position != 'QB')].copy()
            inj['team'] = inj.team.replace(FIX); sn['team'] = sn.team.replace(FIX)
            inj['key'] = inj.full_name.map(norm); sn['key'] = sn.player.map(norm)
            sn = sn[sn.game_type == 'REG'].sort_values('week')
            for (team, wk), grp in inj.groupby(['team', 'week']):
                grp = grp.drop_duplicates('key')
                prev = sn[(sn.team == team) & (sn.week < wk) & (sn.week >= wk - 3)]
                sh = prev.groupby('key')[['offense_pct', 'defense_pct']].mean()
                sub = sh.reindex(grp.key.values).fillna(0).values
                gsum = dict.fromkeys(INJ_GROUPS, 0.0)
                for pos, (wo, wd) in zip(grp.position.map(POS_GROUP).values, sub):
                    if pos in ('OL', 'SK', 'RB'): gsum[pos] += wo
                    elif pos in ('DL', 'LB', 'DB'): gsum[pos] += wd
                inj_load[(s, wk, team)] = (float(sub[:, 0].sum()), float(sub[:, 1].sum())) + tuple(gsum[g] for g in INJ_GROUPS)
        pd.to_pickle(inj_load, cache)
    ZERO = (0.0,) * (2 + len(INJ_GROUPS))

    # ---------- current starters for unplayed 2026 games ----------
    # Latest actual starter per team; data/overrides.json can name a different starter (injury news) through a given week.
    OV = json.load(open(f'{D}/overrides.json'))
    OVERRIDES = {o['team']: (o['qb'], o['name'], int(o.get('through_week', 18))) for o in OV.get('qb_starters', [])}
    name2id = qb.sort_values('season').groupby('name').qb_id.last().to_dict()
    for t, (short, full, _) in OVERRIDES.items():
        if short not in name2id:
            print(f'WARNING overrides.json: no play-by-play history for {short} ({t}); using the latest actual starter instead')
    actual = {}
    for g in sch[(sch.season == 2026) & sch.played].sort_values('gameday').itertuples():
        actual[g.home_team] = (g.home_qb_id, g.home_qb_name); actual[g.away_team] = (g.away_qb_id, g.away_qb_name)
    cw_now = int(sch[(sch.season == 2026) & sch.played].week.max()) + 1

    def starter(team, week):
        o = OVERRIDES.get(team)
        if o and week <= o[2] and o[0] in name2id:
            return (name2id[o[0]], o[1])
        return actual[team]
    latest = {t: starter(t, cw_now) for t in TEAMS}
    active_overrides = {t: o[1] for t, o in OVERRIDES.items() if cw_now <= o[2] and o[0] in name2id}
    last_report = max(w for (s, w, t) in inj_load if s == 2026)
    sch = sch.copy()
    for i, g in sch[(sch.season == 2026) & ~sch.played].iterrows():
        sch.at[i, 'home_qb_id'], sch.at[i, 'home_qb_name'] = starter(g.home_team, g.week)
        sch.at[i, 'away_qb_id'], sch.at[i, 'away_qb_name'] = starter(g.away_team, g.week)
    # next week's injury report isn't out yet: carry the latest report forward one week
    # players reported out in the news (not yet on an official report): add their recent snap share
    MANUAL_OUT = [(p['team'], p['name'], p.get('side', 'off')) for p in OV.get('players_out', [])]
    sn26 = pd.read_csv(f'{D}/snap_counts_2026.csv'); sn26['team'] = sn26.team.replace(FIX)
    for team, name, side in MANUAL_OUT:
        x = sn26[(sn26.team == team) & (sn26.player == name)].sort_values('week').tail(3)
        share = float(x.offense_pct.mean() if side == 'off' else x.defense_pct.mean()) if len(x) else 0.0
        if not len(x):
            print(f'WARNING overrides.json: no snap counts found for {name} ({team})')
        key = (2026, last_report + 1, team)
        base = list(inj_load.get(key, ZERO))
        base[0] += share if side == 'off' else 0; base[1] += share if side == 'def' else 0
        inj_load[key] = tuple(base)
    for t in TEAMS:
        if (2026, last_report + 1, t) not in inj_load and (2026, last_report, t) in inj_load:
            inj_load[(2026, last_report + 1, t)] = inj_load[(2026, last_report, t)]

    # ---------- assemble ----------
    out = []
    for g in sch[sch.season >= 2017].itertuples():
        s, w = g.season, g.week
        r = rating_at[(s, w)]
        f = {'game_id': g.game_id, 'season': s, 'week': w, 'gameday': g.gameday, 'gametime': g.gametime,
             'home': g.home_team, 'away': g.away_team, 'played': bool(g.played), 'margin': g.margin, 'total_pts': g.total_pts,
             'home_score': g.home_score, 'away_score': g.away_score,
             'spread_line': g.spread_line, 'total_line': g.total_line, 'home_ml': g.home_moneyline, 'away_ml': g.away_moneyline,
             'neutral': g.neutral, 'div': g.div_game}
        hi, ai = TI[g.home_team], TI[g.away_team]
        for m in METRICS:
            off, de, mu, hfa = r[m]
            eh, ea = off[hi] - de[ai], off[ai] - de[hi]
            f['d_' + m] = eh - ea
            f['s_' + m] = eh + ea
            f['eh_' + m], f['ea_' + m] = eh, ea
        f['d_st'] = r['st'][hi] - r['st'][ai]
        # QB
        qh, dbh = qb_quality(g.home_qb_id, s, w); qa, dba = qb_quality(g.away_qb_id, s, w)
        bh, ba = team_baseline(g.home_team, s, w), team_baseline(g.away_team, s, w)
        f.update({'home_qb': g.home_qb_name, 'away_qb': g.away_qb_name, 'home_qb_id': g.home_qb_id, 'away_qb_id': g.away_qb_id,
                  'q_h': qh, 'q_a': qa, 'qdb_h': dbh, 'qdb_a': dba, 'qdelta_h': qh - bh, 'qdelta_a': qa - ba,
                  'd_qb': qh - qa, 'd_qbdelta': (qh - bh) - (qa - ba)})
        # rest, travel
        f['rest_diff'] = float(np.clip((g.home_rest or 7) - (g.away_rest or 7), -7, 7))
        f['home_bye'] = int((g.home_rest or 7) >= 13); f['away_bye'] = int((g.away_rest or 7) >= 13)
        site = NEUTRAL.get(g.stadium, home_site(g.home_team, s)) if g.neutral else home_site(g.home_team, s)
        ah, hh = home_site(g.away_team, s), home_site(g.home_team, s)
        f['away_km'] = km(ah, site) / 1000; f['home_km'] = km(hh, site) / 1000
        f['travel_diff'] = f['away_km'] - f['home_km']
        f['tz_away'] = abs(site[2] - ah[2]); f['tz_home'] = abs(site[2] - hh[2])
        tmin = int(str(g.gametime).split(':')[0]) if isinstance(g.gametime, str) else 13
        f['west_early'] = int(ah[2] <= -3 and site[2] >= 0 and tmin <= 13) - int(hh[2] <= -3 and site[2] >= 0 and tmin <= 13 and g.neutral)
        # weather
        outdoors = g.roof in ('outdoors', 'open')
        f['dome'] = int(g.roof in ('dome', 'closed'))
        f['wind'] = float(g.wind) if outdoors and pd.notna(g.wind) else 0.0
        f['cold'] = float(max(0, 40 - g.temp)) if outdoors and pd.notna(g.temp) else 0.0
        f['temp'] = float(g.temp) if pd.notna(g.temp) else np.nan
        # injuries
        ih = inj_load.get((s, w, g.home_team), ZERO); ia = inj_load.get((s, w, g.away_team), ZERO)
        for k, gname in enumerate(INJ_GROUPS): f['d_inj_' + gname] = ih[2 + k] - ia[2 + k]
        f['inj_off_h'], f['inj_def_h'], f['inj_off_a'], f['inj_def_a'] = ih[0], ih[1], ia[0], ia[1]
        f['d_inj'] = (ih[0] + ih[1]) - (ia[0] + ia[1])
        out.append(f)
    F = pd.DataFrame(out)
    F.to_pickle(out_path or f'{D}/features.pkl')
    if not write_extras:
        return F
    pd.to_pickle({'rating_at': rating_at, 'teams': TEAMS}, f'{D}/rating_at.pkl')  # used by drift.py (future-week uncertainty)
    # current ratings for the site (season 2026, after the last played week)
    s = 2026; w = int(sch[(sch.season == s) & sch.played].week.max()) + 1
    cur = {m: {'off': rating_at[(s, w)][m][0].tolist(), 'def': rating_at[(s, w)][m][1].tolist(), 'mu': float(rating_at[(s, w)][m][2]), 'hfa': float(rating_at[(s, w)][m][3])} for m in METRICS}
    cur['st'] = rating_at[(s, w)]['st'].tolist(); cur['teams'] = TEAMS
    json.dump(cur, open(f'{D}/ratings_now.json', 'w'))
    # current QB table for the site and the matchup tool
    qcur = {}
    for t in TEAMS:
        qid, nm = latest[t]
        q, db = qb_quality(qid, s, w)
        qcur[t] = {'qb': nm, 'q': q, 'db': db, 'base': team_baseline(t, s, w)}
    inj_now = {t: inj_load.get((2026, last_report + 1, t), ZERO) for t in TEAMS}
    json.dump({'qb': qcur, 'inj': inj_now, 'overrides': active_overrides, 'injury_week': last_report}, open(f'{D}/current.json', 'w'))
    import pickle
    pickle.dump({'qb_hist': qb_hist, 'inj_load': inj_load}, open(f'{D}/aux.pkl', 'wb'))
    return F


if __name__ == '__main__':
    F = build()
    print(F.shape, F.played.sum(), 'played')
    print(F[F.season == 2026].tail(3).T.head(60))
