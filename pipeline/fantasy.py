"""Fantasy data: per-game projections for the next two weeks, rest-of-season totals, usage risers and RB handcuffs."""
import json, os, math
import numpy as np, pandas as pd
import players as P

D = os.path.join(os.path.dirname(__file__), '..', 'data')
site = json.load(open(f'{D}/site_data.json'))
cur = json.load(open(f'{D}/current.json'))
cal = json.load(open(f'{D}/prop_cal.json'))
inj = pd.read_csv(f'{D}/injuries_2026.csv'); inj['team'] = inj.team.replace(P.FIX)
last_inj = int(inj.week.max())
out_ids = set(inj[(inj.week == last_inj) & inj.report_status.isin(['Out', 'Doubtful'])].gsis_id)
q_ids = set(inj[(inj.week == last_inj) & (inj.report_status == 'Questionable')].gsis_id)
NEWS = json.load(open(f'{D}/news.json'))

W = P.W
last_played = int(W.week.max())
H, lg, opp = P.build_context(last_played + 1)
unplayed = [g for g in site['games'] if g['hs'] is None]
cw = min(g['wk'] for g in unplayed)
# the week the rest-of-season totals start from: the coming week, unless most of it is already played (only Monday night left)
cw_games = [g for g in site['games'] if g['wk'] == cw]
ros_from = cw + 1 if 2 * sum(g['hs'] is not None for g in cw_games) > len(cw_games) else cw
# manual outs from overrides.json count only for the team they're listed under (a traded player is listed as out for his old team)
OUT_BY_TEAM = {}
for _o in json.load(open(f'{D}/overrides.json')).get('players_out', []):
    if isinstance(_o, dict): OUT_BY_TEAM.setdefault(_o.get('team'), set()).add(_o.get('name'))


def calib(stat, v):
    k = cal[stat]; return max(0.0, k['c'] + k['d'] * v) if v else 0.0


def proj_line(pid, team, opp_team, week):
    qn = P.starter_q(team, week)
    if isinstance(pid, str) and pid.startswith('new:'):
        r = P.project_new_qb(pid[4:], team, opp_team, H, lg, opp, qn) if qn is not None else None
    else:
        r = P.project(pid, team, opp_team, H, lg, opp, q_new=qn)
    if r is None: return None
    out = {'id': pid, 'name': r['name'], 'pos': r['pos'], 'team': team, 'opp': opp_team,
           'rush_yds': calib('rush_yds', r.get('rush_yds', 0)), 'rush_td': r.get('rush_td', 0), 'carries': r.get('carries', 0),
           'td_p': r['td_p'], 'qb_adj': r.get('qb_adj', 0)}
    if r['pos'] == 'QB':
        out.update({'pass_yds': calib('pass_yds', r['pass_yds']), 'pass_td': r['pass_td'], 'int': r['int'], 'att': r['att']})
    else:
        out.update({'rec': r['rec'], 'rec_yds': calib('rec_yds', r['rec_yds']), 'rec_td': r['rec_td'], 'targets': r['targets']})
    return {k: (round(float(v), 3) if isinstance(v, (float, np.floating)) else v) for k, v in out.items()}


def pool(team, wk):
    tp = H[H.team == team]
    recent = tp[tp.week >= tp.week.max() - 1]
    pl = recent.groupby('player_id').agg(grp=('grp', 'first'), car=('carries', 'mean'), tg=('targets', 'mean')).reset_index()
    pl = pl[~pl.player_id.isin(out_ids)]
    names = H.groupby('player_id').player_display_name.last()
    pl = pl[~pl.player_id.map(names).isin(set(NEWS['outs']) | OUT_BY_TEAM.get(team, set()))]
    pl, back = P.add_returning(pl, H, team, wk)   # back from injury after missing recent games (overrides.json 'returning')
    ids = []
    qname = cur['qb'][team]['qb']
    qrow = H[(H.grp == 'QB') & (H.player_display_name == qname)]
    ids.append(qrow.player_id.iloc[0] if len(qrow) else 'new:' + qname)  # a starter with no passes yet is projected from his rating
    ids += pl[pl.grp == 'RB'].sort_values('car', ascending=False).player_id.head(3).tolist()
    ids += pl[pl.grp.isin(['WR', 'TE'])].sort_values('tg', ascending=False).player_id.head(5).tolist()
    return ids, back


games = []
for g in unplayed:
    if g['wk'] > cw + 1: continue
    for team, o in ((g['a'], g['h']), (g['h'], g['a'])):
        ids, back = pool(team, g['wk'])
        recs = []
        for pid in ids:
            r = proj_line(pid, team, o, g['wk'])
            if r and (r['pos'] == 'QB' or r['carries'] >= 2 or r.get('targets', 0) >= 2):
                r['game'] = g['id']; r['wk'] = g['wk']; r['q'] = pid in q_ids; r['flag'] = NEWS['flags'].get(r['name'])
                if abs(r['qb_adj']) >= 0.04 and r['pos'] != 'QB':
                    r['qbn'] = cur['qb'][team]['qb'] if g['wk'] <= P.QB_UNTIL.get(team, 99) else None
                recs.append(r)
        P.share_adjust(recs, H, team, back)
        games += [{k: (round(float(v), 3) if isinstance(v, (float, np.floating)) else v) for k, v in r.items()} for r in recs]

# rest of season: every remaining game from ros_from on, for players in the coming-week pool; each game uses that week's expected starter
ros = {}
for r in [x for x in games if x['wk'] == ros_from] + [x for x in games if x['wk'] != ros_from]:
    if r['id'] in ros: continue
    rem = [g for g in unplayed if g['wk'] >= ros_from and r['team'] in (g['a'], g['h'])]
    if r['pos'] == 'QB' and r['team'] in P.QB_UNTIL:  # a fill-in starter only counts through his listed week
        rem = [g for g in rem if g['wk'] <= P.QB_UNTIL[r['team']]]
    tot = {}
    for g in rem:
        o = g['h'] if g['a'] == r['team'] else g['a']
        p = proj_line(r['id'], r['team'], o, g['wk'])
        if not p: continue
        for k in ('pass_yds', 'pass_td', 'int', 'rush_yds', 'rush_td', 'rec', 'rec_yds', 'rec_td'):
            tot[k] = tot.get(k, 0) + p.get(k, 0)
    ros[r['id']] = {'n': len(rem), **{k: round(v, 2) for k, v in tot.items()}}

# usage risers: opportunities per game (targets + carries) last 2 games vs. earlier games
risers = []
for pid, x in W[W.grp.isin(['RB', 'WR', 'TE'])].groupby('player_id'):
    x = x.sort_values('week')
    if len(x) < 4 or pid in out_ids: continue
    team = x.team.iloc[-1]
    if x.week.iloc[-1] < W[W.team == team].week.max(): continue  # didn't play the team's latest game
    opp_ = x.targets + x.carries
    recent, before = opp_.iloc[-2:].mean(), opp_.iloc[:-2].mean()
    tshare = x.target_share.iloc[-2:].mean() if 'target_share' in x else None
    risers.append({'id': pid, 'name': x.player_display_name.iloc[-1], 'pos': x.grp.iloc[0], 'team': team,
                   'recent': round(float(recent), 1), 'before': round(float(before), 1), 'jump': round(float(recent - before), 1),
                   'tshare': None if tshare is None or pd.isna(tshare) else round(float(tshare), 3)})
risers = sorted(risers, key=lambda r: -r['jump'])[:15]

# RB handcuffs: each team's top two backs by carries over the last three games
cuffs = []
for team in sorted(W.team.unique()):
    x = W[(W.team == team) & (W.grp == 'RB') & (W.week >= W[W.team == team].week.max() - 2)]
    s = x.groupby(['player_id', 'player_display_name']).agg(car=('carries', 'sum'), tg=('targets', 'sum')).reset_index().sort_values('car', ascending=False)
    if len(s) < 2: continue
    tot = s.car.sum()
    rb1, rb2 = s.iloc[0], s.iloc[1]
    cuffs.append({'team': team, 'rb1': rb1.player_display_name, 'rb2': rb2.player_display_name, 'rb2_id': rb2.player_id,
                  'rb1_share': round(float(rb1.car / tot), 3) if tot else None, 'rb2_share': round(float(rb2.car / tot), 3) if tot else None,
                  'rb1_out': rb1.player_id in out_ids})

# season to date for every rest-of-season player: actual stat totals, plus workload in the last 2 games vs. earlier
season = {}
for pid in ros:
    x = W[W.player_id == pid].sort_values('week')
    if not len(x): continue
    f = lambda c: float(x[c].fillna(0).sum())
    touches = (x.targets.fillna(0) + x.carries.fillna(0))
    season[pid] = {'g': int(len(x)), 'pass_yds': f('passing_yards'), 'pass_td': f('passing_tds'), 'int': f('passing_interceptions'),
                   'rush_yds': f('rushing_yards'), 'rush_td': f('rushing_tds'), 'rec': f('receptions'), 'rec_yds': f('receiving_yards'), 'rec_td': f('receiving_tds'),
                   'recent': round(float(touches.iloc[-2:].mean()), 1), 'before': round(float(touches.iloc[:-2].mean()), 1) if len(x) > 2 else None}

json.dump({'games': games, 'ros': ros, 'season': season, 'risers': risers, 'cuffs': cuffs, 'cw': cw, 'through_week': last_played, 'injury_week': last_inj},
          open(f'{D}/fantasy.json', 'w'))
print(len(games), 'player-games;', len(ros), 'ROS;', len(risers), 'risers;', len(cuffs), 'cuffs')
ppr = lambda r: r.get('pass_yds', 0) / 25 + 4 * r.get('pass_td', 0) - 2 * r.get('int', 0) + r.get('rush_yds', 0) / 10 + 6 * r.get('rush_td', 0) + r.get('rec_yds', 0) / 10 + 6 * r.get('rec_td', 0) + r.get('rec', 0)
for pos in ['QB', 'RB', 'WR', 'TE']:
    top = sorted([r for r in games if r['wk'] == ros_from and r['pos'] == pos], key=lambda r: -ppr(r))[:5]
    print(pos, ', '.join(f"{r['name']} {ppr(r):.1f}" for r in top))
print('risers:', ', '.join(f"{r['name']} {r['before']}->{r['recent']}" for r in risers[:6]))
