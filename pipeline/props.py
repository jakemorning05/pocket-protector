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

# Kalshi "X+" markets for Commanders at Giants (Thursday night), from the Kalshi API at 12:15 PM ET on Nov 12, 2026: for each player,
# the threshold whose price is closest to 50%. price = midpoint of the YES bid and ask; a YES pick costs the ask, a NO pick costs 1 - bid.
NEW_PROPS = [
    dict(game='2026_10_WAS_NYG', player='Jayden Daniels', stat='pass_yds', thr=200, price=0.495, bid=0.49, ask=0.5),
    dict(game='2026_10_WAS_NYG', player='J.J. McCarthy', stat='pass_yds', thr=200, price=0.565, bid=0.56, ask=0.57),
    dict(game='2026_10_WAS_NYG', player='Jayden Daniels', stat='rush_yds', thr=40, price=0.41, bid=0.4, ask=0.42),
    dict(game='2026_10_WAS_NYG', player='Rachaad White', stat='rush_yds', thr=40, price=0.475, bid=0.45, ask=0.5),
    dict(game='2026_10_WAS_NYG', player='Austin Ekeler', stat='rush_yds', thr=25, price=0.515, bid=0.49, ask=0.54),
    dict(game='2026_10_WAS_NYG', player='Devin Singletary', stat='rush_yds', thr=25, price=0.515, bid=0.5, ask=0.53),
    dict(game='2026_10_WAS_NYG', player='Malik Nabers', stat='rec_yds', thr=70, price=0.49, bid=0.48, ask=0.5),
    dict(game='2026_10_WAS_NYG', player='Isaiah Likely', stat='rec_yds', thr=50, price=0.49, bid=0.48, ask=0.5),
    dict(game='2026_10_WAS_NYG', player='Antonio Williams', stat='rec_yds', thr=40, price=0.545, bid=0.53, ask=0.56),
    dict(game='2026_10_WAS_NYG', player='Stefon Diggs', stat='rec_yds', thr=50, price=0.39, bid=0.37, ask=0.41),
    dict(game='2026_10_WAS_NYG', player='Chig Okonkwo', stat='rec_yds', thr=40, price=0.465, bid=0.44, ask=0.49),
    dict(game='2026_10_WAS_NYG', player='Malachi Fields', stat='rec_yds', thr=20, price=0.59, bid=0.57, ask=0.61),
    dict(game='2026_10_WAS_NYG', player='Darnell Mooney', stat='rec_yds', thr=15, price=0.53, bid=0.51, ask=0.55),
    dict(game='2026_10_WAS_NYG', player='Van Jefferson', stat='rec_yds', thr=15, price=0.515, bid=0.49, ask=0.54),
    dict(game='2026_10_WAS_NYG', player='Rachaad White', stat='rec_yds', thr=15, price=0.45, bid=0.43, ask=0.47),
    dict(game='2026_10_WAS_NYG', player='Austin Ekeler', stat='rec_yds', thr=10, price=0.425, bid=0.4, ask=0.45),
]
SOURCE = 'Kalshi API, Nov 12 12:15 PM ET'


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
        bid, ask = pr.get('bid', pr['price']), pr.get('ask', pr['price'])   # buy YES at the ask; buy NO at 1 - bid
        side = 'YES' if pov - ask > bid - pov else 'NO'
        edge = (pov - ask) if side == 'YES' else (bid - pov)
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
        cost = e.get('ask', e['price']) if e['pick'] == 'YES' else 1 - e.get('bid', e['price'])
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
