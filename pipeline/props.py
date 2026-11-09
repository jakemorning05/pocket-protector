"""Forward test: model player projections vs. posted prop markets. Log picks before games, grade after.

usage: python3 props.py log      (record picks for the props in NEW_PROPS)
       python3 props.py grade    (fill in results from nflverse weekly player stats)
"""
import json, os, sys, math
import numpy as np, pandas as pd
from scipy.stats import norm
import players as P

D = os.path.join(os.path.dirname(__file__), '..', 'data')
LOG = f'{D}/prop_log.json'
STAT_COL = {'pass_yds': 'passing_yards', 'rush_yds': 'rushing_yards', 'rec_yds': 'receiving_yards'}

# Kalshi "X+" markets for Bills at Vikings, read from Covers at 12:35 PM ET on Nov 9, 2026 (price = YES probability)
NEW_PROPS = [
    dict(game='2026_09_BUF_MIN', player='Josh Allen', stat='pass_yds', thr=225, price=0.57),
    dict(game='2026_09_BUF_MIN', player='Dalton Kincaid', stat='rec_yds', thr=40, price=0.46),
    dict(game='2026_09_BUF_MIN', player='Josh Allen', stat='rush_yds', thr=30, price=0.53),
    dict(game='2026_09_BUF_MIN', player='James Cook', stat='rec_yds', thr=10, price=0.47),
    dict(game='2026_09_BUF_MIN', player='Carson Wentz', stat='pass_yds', thr=200, price=0.58),
    dict(game='2026_09_BUF_MIN', player='Justin Jefferson', stat='rec_yds', thr=70, price=0.63),
    dict(game='2026_09_BUF_MIN', player='T.J. Hockenson', stat='rec_yds', thr=40, price=0.50),
    dict(game='2026_09_BUF_MIN', player='Aaron Jones', stat='rush_yds', thr=30, price=0.54),
]
SOURCE = 'Kalshi via Covers, Nov 9 12:35 PM ET'


def calibration():
    """From Weeks 4-9: actual = c + d*projection, and spread (sd) as a function of projection, per stat."""
    rows = []
    for wk in range(4, 10):
        H, lg, opp = P.build_context(wk)
        for p in P.W[P.W.week == wk].itertuples():
            hist = H[H.player_id == p.player_id]
            if len(hist) < 2: continue
            pr = P.project(p.player_id, p.team, p.opponent_team, H, lg, opp)
            if pr is None: continue
            if p.grp == 'QB' and hist.attempts.mean() >= 15 and p.attempts >= 10: rows.append(('pass_yds', pr['pass_yds'], p.passing_yards))
            if p.carries >= 1 or hist.carries.mean() >= 3: rows.append(('rush_yds', pr['rush_yds'], p.rushing_yards))
            if p.grp != 'QB' and hist.targets.mean() >= 2: rows.append(('rec_yds', pr['rec_yds'], p.receiving_yards))
    R = pd.DataFrame(rows, columns=['stat', 'proj', 'act'])
    cal = {}
    for st, g in R.groupby('stat'):
        d, c = np.polyfit(g.proj, g.act, 1)
        resid = g.act - (c + d * g.proj)
        g = g.assign(fit=c + d * g.proj, ares=resid.abs())
        s1, s0 = np.polyfit(g.fit, g.ares * math.sqrt(math.pi / 2), 1)  # mean abs residual -> sd
        cal[st] = {'c': float(c), 'd': float(d), 's0': float(s0), 's1': float(s1), 'n': int(len(g))}
    return cal


def prob_over(proj, thr, st, cal):
    k = cal[st]
    mu = k['c'] + k['d'] * proj
    sd = max(6.0, k['s0'] + k['s1'] * mu)
    return mu, sd, 1 - norm.cdf((thr - 0.5 - mu) / sd)


def log():
    cal = calibration()
    proj = {(p['game'], p['name'], ): p for p in json.load(open(f'{D}/players.json'))['players']}
    entries = json.load(open(LOG)) if os.path.exists(LOG) else []
    have = {(e['game'], e['player'], e['stat'], e['thr']) for e in entries}
    for pr in NEW_PROPS:
        key = (pr['game'], pr['player'], pr['stat'], pr['thr'])
        if key in have: continue
        p = next((v for (g, n), v in proj.items() if g == pr['game'] and (n == pr['player'] or n.startswith(pr['player']))), None)
        raw = p.get(pr['stat']) if p else None
        if raw is None: print('no projection for', pr); continue
        mu, sd, pov = prob_over(raw, pr['thr'], pr['stat'], cal)
        side = 'YES' if pov > pr['price'] else 'NO'
        edge = (pov - pr['price']) if side == 'YES' else ((1 - pov) - (1 - pr['price']))
        entries.append({**pr, 'source': SOURCE, 'raw_proj': round(raw, 1), 'proj': round(mu, 1), 'sd': round(sd, 1), 'p_over': round(pov, 3),
                        'pick': side, 'edge': round(edge, 3), 'actual': None, 'won': None, 'profit': None, 'pid': p['id']})
    json.dump(entries, open(LOG, 'w'), indent=1)
    json.dump(cal, open(f'{D}/prop_cal.json', 'w'), indent=1)
    return entries, cal


def grade(stats_csv=f'{D}/stats_player_week_2026.csv'):
    W = pd.read_csv(stats_csv, low_memory=False)
    entries = json.load(open(LOG))
    for e in entries:
        if e['actual'] is not None: continue
        wk = int(e['game'].split('_')[1])
        r = W[(W.player_id == e['pid']) & (W.week == wk)]
        if r.empty: continue
        a = float(r[STAT_COL[e['stat']]].iloc[0])
        over = a >= e['thr']
        e['actual'] = a
        e['won'] = (over and e['pick'] == 'YES') or (not over and e['pick'] == 'NO')
        cost = e['price'] if e['pick'] == 'YES' else 1 - e['price']
        e['profit'] = round((1 - cost) if e['won'] else -cost, 3)
    json.dump(entries, open(LOG, 'w'), indent=1)
    return entries


if __name__ == '__main__':
    if sys.argv[1:] == ['grade']:
        es = grade()
    else:
        es, cal = log()
        print({k: {kk: round(vv, 3) for kk, vv in v.items()} for k, v in cal.items()})
    for e in es:
        print(f"{e['player']:18s} {e['stat']:8s} {e['thr']:>4}+  market {e['price']:.0%}  model proj {e['proj']:6.1f} (raw {e['raw_proj']:6.1f}, sd {e['sd']:4.1f})  P(over) {e['p_over']:.0%}  pick {e['pick']:3s} edge {e['edge']:+.0%}  result {e['actual']}")
