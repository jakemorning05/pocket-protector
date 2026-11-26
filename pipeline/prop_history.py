"""Builds data/prop_hist.csv: the model's walk-forward projection and the actual result for every prop-sized role
(QBs with 20+ attempts a game, RBs with 8+ carries, WRs/TEs with 4+ targets over their last 4 games) in 2024 and 2025.
props.py prices each prop from how often similar projections actually cleared the line here, instead of assuming a
bell curve (yardage is skewed: lots of quiet games, a few big ones). Rerun after changing the projection model.
Needs the 2024-25 nflverse weekly stats in .work/hist/ (stats_player/stats_player_week_YEAR.csv from nflverse-data releases).
Usage: python3 pipeline/prop_history.py"""
import sys, os, json, math, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import players as P

rows = []
for yr in (2024, 2025):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.work', 'hist', f'stats_player_week_{yr}.csv')
    W = pd.read_csv(path, low_memory=False)
    W = W[W.season_type == 'REG'].copy()
    for c in ['team', 'opponent_team']: W[c] = W[c].replace(P.FIX)
    num = ['attempts', 'completions', 'passing_yards', 'passing_tds', 'passing_interceptions', 'carries', 'rushing_yards', 'rushing_tds',
           'targets', 'receptions', 'receiving_yards', 'receiving_tds']
    W[num] = W[num].fillna(0)
    W['grp'] = W.position.map(lambda p: p if p in ('QB', 'RB', 'WR', 'TE') else 'OTHER')
    W = W[W.grp != 'OTHER']; W['team0'] = W.team
    P.W = W
    last = int(W.week.max())
    for wk in range(4, last + 1):
        H, lg, opp = P.build_context(wk)
        for p in W[W.week == wk].itertuples():
            hist = H[H.player_id == p.player_id].sort_values('week').tail(4)
            if len(hist) < 2: continue
            try:
                pr = P.project(p.player_id, p.team, p.opponent_team, H, lg, opp)
            except Exception:
                pr = None
            if pr is None: continue
            # prop-sized roles: the players Kalshi posts markets for
            if p.grp == 'QB' and hist.attempts.mean() >= 20 and p.attempts >= 10: rows.append((yr, wk, 'pass_yds', pr['pass_yds'], p.passing_yards))
            if p.grp == 'RB' and hist.carries.mean() >= 8: rows.append((yr, wk, 'rush_yds', pr['rush_yds'], p.rushing_yards))
            if p.grp in ('WR', 'TE') and hist.targets.mean() >= 4: rows.append((yr, wk, 'rec_yds', pr['rec_yds'], p.receiving_yards))
    print(yr, 'done', len(rows), flush=True)
R = pd.DataFrame(rows, columns=['season', 'wk', 'stat', 'proj', 'act'])
R[['season', 'stat', 'proj', 'act']].round({'proj': 1}).to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'prop_hist.csv'), index=False)
for (st), g in R.groupby('stat'):
    print(st)
    for yr, x in g.groupby('season'):
        d, c = np.polyfit(x.proj, x.act, 1)
        print(f'  {yr}: n={len(x)} avg proj {x.proj.mean():.1f} avg actual {x.act.mean():.1f} bias {x.act.mean() - x.proj.mean():+.1f} | fit actual = {c:.1f} + {d:.2f}*proj | sd of residual {(x.act - x.proj).std():.1f}')
