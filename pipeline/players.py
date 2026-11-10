"""Opponent-adjusted player projections for each team's next game, plus a walk-forward backtest."""
import pandas as pd, numpy as np, json, os, math

D = os.path.join(os.path.dirname(__file__), '..', 'data')
FIX = {'SD': 'LAC', 'OAK': 'LV', 'STL': 'LA', 'LAR': 'LA'}
W = pd.read_csv(f'{D}/stats_player_week_2026.csv', low_memory=False)
W = W[W.season_type == 'REG'].copy()
for c in ['team', 'opponent_team']:
    W[c] = W[c].replace(FIX)
num = ['attempts', 'completions', 'passing_yards', 'passing_tds', 'passing_interceptions', 'carries', 'rushing_yards', 'rushing_tds',
       'targets', 'receptions', 'receiving_yards', 'receiving_tds']
W[num] = W[num].fillna(0)
W['grp'] = W.position.map(lambda p: p if p in ('QB', 'RB', 'WR', 'TE') else 'OTHER')
W = W[W.grp != 'OTHER']
DECAY = 0.9
# players traded since their last game count for their new team (QBs are handled by the starting-QB overrides)
for _t in json.load(open(f'{D}/overrides.json')).get('traded', []):
    if _t.get('pos') in ('WR', 'TE', 'RB'):
        W.loc[(W.player_display_name == _t['name']) & (W.team == _t['from']), 'team'] = _t['to']


def wavg(vals):
    vals = list(vals)[::-1]  # most recent first
    wts = [DECAY ** i for i in range(len(vals))]
    return sum(v * w for v, w in zip(vals, wts)) / sum(wts) if vals else 0.0


def build_context(before_week):
    H = W[W.week < before_week]
    # league rates
    lg = {
        'ypa': H.passing_yards.sum() / max(1, H.attempts.sum()), 'ptd': H.passing_tds.sum() / max(1, H.attempts.sum()),
        'int': H.passing_interceptions.sum() / max(1, H.attempts.sum()), 'cmp': H.completions.sum() / max(1, H.attempts.sum()),
        'ypc': H.rushing_yards.sum() / max(1, H.carries.sum()), 'rtd': H.rushing_tds.sum() / max(1, H.carries.sum()),
    }
    for g in ('WR', 'TE', 'RB'):
        x = H[H.grp == g]
        lg['ypt_' + g] = x.receiving_yards.sum() / max(1, x.targets.sum())
        lg['ctch_' + g] = x.receptions.sum() / max(1, x.targets.sum())
        lg['rectd_' + g] = x.receiving_tds.sum() / max(1, x.targets.sum())
    # opponent factors (allowed per unit vs league), shrunk
    opp = {}
    for t, x in H.groupby('opponent_team'):
        f = {}
        att = x.attempts.sum(); f['pass'] = ((x.passing_yards.sum() + 120 * lg['ypa']) / (att + 120)) / lg['ypa']
        f['ptd'] = ((x.passing_tds.sum() + 120 * lg['ptd']) / (att + 120)) / lg['ptd'] if lg['ptd'] else 1
        car = x.carries.sum(); f['rush'] = ((x.rushing_yards.sum() + 60 * lg['ypc']) / (car + 60)) / lg['ypc']
        for g in ('WR', 'TE', 'RB'):
            y = x[x.grp == g]; tg = y.targets.sum()
            f['rec_' + g] = ((y.receiving_yards.sum() + 40 * lg['ypt_' + g]) / (tg + 40)) / lg['ypt_' + g]
        opp[t] = f
    return H, lg, opp


def project(pid, team, opp_team, H, lg, opp, starter=False):
    x = H[H.player_id == pid].sort_values('week')
    if x.empty: return None
    grp = x.grp.iloc[0]
    o = opp.get(opp_team, {})
    r = {'id': pid, 'name': x.player_display_name.iloc[-1], 'pos': grp, 'team': team, 'opp': opp_team, 'g': int(len(x))}
    car = wavg(x.carries); r_ypc = (x.rushing_yards.sum() + 40 * lg['ypc']) / (x.carries.sum() + 40)
    r['rush_yds'] = car * r_ypc * o.get('rush', 1); r['carries'] = car
    r_rtd = (x.rushing_tds.sum() + 40 * lg['rtd']) / (x.carries.sum() + 40)
    td = car * r_rtd
    r['rush_td'] = car * r_rtd
    if grp == 'QB':
        tw = H[(H.team == team) & (H.grp == 'QB')].groupby('week').attempts.sum()
        att = 0.5 * wavg(tw.values) + 0.5 * (wavg(x.attempts) if len(x) >= 3 else wavg(tw.values))
        ypa = (x.passing_yards.sum() + 150 * lg['ypa']) / (x.attempts.sum() + 150)
        ptd = (x.passing_tds.sum() + 300 * lg['ptd']) / (x.attempts.sum() + 300)
        it = (x.passing_interceptions.sum() + 150 * lg['int']) / (x.attempts.sum() + 150)
        r.update({'att': att, 'pass_yds': att * ypa * o.get('pass', 1), 'pass_td': att * ptd * o.get('ptd', 1), 'int': att * it})
    else:
        tg = wavg(x.targets)
        ypt = (x.receiving_yards.sum() + 25 * lg['ypt_' + grp]) / (x.targets.sum() + 25)
        ct = (x.receptions.sum() + 25 * lg['ctch_' + grp]) / (x.targets.sum() + 25)
        rtd = (x.receiving_tds.sum() + 25 * lg['rectd_' + grp]) / (x.targets.sum() + 25)
        r.update({'targets': tg, 'rec': tg * ct, 'rec_yds': tg * ypt * o.get('rec_' + grp, 1)})
        td += tg * rtd
        r['rec_td'] = tg * rtd
    r['td_p'] = 1 - math.exp(-td)
    return r


def backtest(weeks=range(4, 10)):
    err = {'pass_yds': [[], []], 'rush_yds': [[], []], 'rec_yds': [[], []]}
    for wk in weeks:
        H, lg, opp = build_context(wk)
        cur = W[W.week == wk]
        for p in cur.itertuples():
            hist = H[H.player_id == p.player_id]
            if len(hist) < 2: continue
            pr = project(p.player_id, p.team, p.opponent_team, H, lg, opp)
            if pr is None: continue
            if p.grp == 'QB' and hist.attempts.mean() >= 15 and p.attempts >= 10:
                err['pass_yds'][0].append(abs(pr['pass_yds'] - p.passing_yards)); err['pass_yds'][1].append(abs(hist.passing_yards.mean() - p.passing_yards))
            if p.grp == 'RB' and hist.carries.mean() >= 8:
                err['rush_yds'][0].append(abs(pr['rush_yds'] - p.rushing_yards)); err['rush_yds'][1].append(abs(hist.rushing_yards.mean() - p.rushing_yards))
            if p.grp in ('WR', 'TE') and hist.targets.mean() >= 4:
                err['rec_yds'][0].append(abs(pr['rec_yds'] - p.receiving_yards)); err['rec_yds'][1].append(abs(hist.receiving_yards.mean() - p.receiving_yards))
    return {k: {'n': len(v[0]), 'model_mae': round(float(np.mean(v[0])), 1), 'naive_mae': round(float(np.mean(v[1])), 1)} for k, v in err.items()}


if __name__ == '__main__':
    site = json.load(open(f'{D}/site_data.json'))
    cur = json.load(open(f'{D}/current.json'))
    inj = pd.read_csv(f'{D}/injuries_2026.csv'); inj['team'] = inj.team.replace(FIX)
    last_wk = int(inj.week.max())
    out_ids = set(inj[(inj.week == last_wk) & inj.report_status.isin(['Out', 'Doubtful'])].gsis_id)
    last_played = int(W.week.max())
    H, lg, opp = build_context(last_played + 1)
    # next unplayed game per team
    nxt = {}
    for g in site['games']:
        if g['hs'] is None:
            for t, o in ((g['a'], g['h']), (g['h'], g['a'])):
                nxt.setdefault(t, (o, g['id']))
    proj = []
    for t, (o, gid) in nxt.items():
        tp = H[H.team == t]
        recent = tp[tp.week >= tp.week.max() - 1]
        pool = recent.groupby('player_id').agg(grp=('grp', 'first'), car=('carries', 'mean'), tg=('targets', 'mean'), att=('attempts', 'mean')).reset_index()
        pool = pool[~pool.player_id.isin(out_ids)]
        # starting QB from the model's current starters (handles injuries and trades)
        qname = cur['qb'][t]['qb']
        qrow = H[(H.grp == 'QB') & (H.player_display_name == qname)]
        picks = []
        if len(qrow): picks.append(qrow.player_id.iloc[0])
        picks += pool[pool.grp == 'RB'].sort_values('car', ascending=False).player_id.head(2).tolist()
        picks += pool[pool.grp.isin(['WR', 'TE'])].sort_values('tg', ascending=False).player_id.head(4).tolist()
        for pid in picks:
            r = project(pid, t, o, H, lg, opp)
            if r and (r['pos'] == 'QB' or r.get('carries', 0) >= 3 or r.get('targets', 0) >= 2.5):
                r['game'] = gid
                proj.append({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()})
        if not len(qrow):
            proj.append({'id': None, 'name': qname, 'pos': 'QB', 'team': t, 'opp': o, 'game': gid, 'g': 0, 'note': 'No starts this season'})
    bt = backtest()
    json.dump({'players': proj, 'bt': bt, 'through_week': last_played, 'injury_week': last_wk}, open(f'{D}/players.json', 'w'))
    print(len(proj), 'player projections'); print(bt)
    for r in proj:
        if r['team'] in ('BUF', 'MIN'): print(r)
