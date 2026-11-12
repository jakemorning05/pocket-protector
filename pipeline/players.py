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
W['team0'] = W.team  # the team he actually played for that week (kept through the trade reassignment below)
DECAY = 0.9
# players traded since their last game count for their new team (QBs are handled by the starting-QB overrides)
for _t in json.load(open(f'{D}/overrides.json')).get('traded', []):
    if _t.get('pos') in ('WR', 'TE', 'RB'):
        W.loc[(W.player_display_name == _t['name']) & (W.team == _t['from']), 'team'] = _t['to']


# ---------- starting quarterback ----------
# A team's passing rates move with its starter's quality (EPA per dropback, the same rating the game model uses) relative to the
# quarterbacks behind a player's numbers. Log-rate change per 1.0 EPA/dropback, fit on 4,078 team games from 2016 to 2026 and stable
# across eras; on held-out 2023-26 games with a real QB change it cut the error on team passing yards from 43.5 to 40.9 a game.
# A starter 0.10 worse means about 6% fewer yards, 16% fewer passing TDs, 2% fewer completions and 3% fewer attempts.
QB_EFF = {'yds': 0.594, 'td': 1.806, 'cmp': 0.186, 'int': -0.455, 'att': 0.315}
OVR = json.load(open(f'{D}/overrides.json'))


def _week_quality():
    """Pre-game rating of each team's actual starter in the games played so far: {(team, week): q}."""
    if not os.path.exists(f'{D}/features.pkl'):
        return {}
    F = pd.read_pickle(f'{D}/features.pkl')
    F = F[(F.season == 2026) & (F.week <= int(W.week.max()))]
    q = {}
    for r in F.itertuples():
        for t, v in ((r.home, r.q_h), (r.away, r.q_a)):
            if pd.notna(v): q[(FIX.get(t, t), int(r.week))] = float(v)
    return q


QW = _week_quality()
Q_LG = float(np.mean(list(QW.values()))) if QW else 0.0
CUR_QB = json.load(open(f'{D}/current.json'))['qb'] if os.path.exists(f'{D}/current.json') else {}
QB_UNTIL = {o['team']: o.get('through_week', 18) for o in OVR.get('qb_starters', [])}


def starter_q(team, week):
    """Rating of the quarterback expected to start for `team` in `week`. A fill-in named in overrides.json counts through his
    through_week; after that the team is assumed back to its usual starters (its season baseline)."""
    c = CUR_QB.get(team)
    if not c: return None
    return c['base'] if week > QB_UNTIL.get(team, 99) else c['q']


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


def hist_q(x):
    """Decay-weighted rating of the quarterbacks a player's history was played with (None if unknown)."""
    vals = [QW.get((t, int(w))) for t, w in zip(x.team0, x.week)]
    vals = [v for v in vals if v is not None]
    return wavg(vals) if vals else None


def project(pid, team, opp_team, H, lg, opp, starter=False, q_new=None):
    """q_new: rating of the quarterback expected to start this game (None = no starting-QB adjustment)."""
    x = H[H.player_id == pid].sort_values('week')
    if x.empty: return None
    grp = x.grp.iloc[0]
    o = opp.get(opp_team, {})
    r = {'id': pid, 'name': x.player_display_name.iloc[-1], 'pos': grp, 'team': team, 'opp': opp_team, 'g': int(len(x))}
    qd = 0.0
    if q_new is not None:
        if grp == 'QB':
            tq = H[(H.team == team) & (H.grp == 'QB')].groupby('week').size().index
            base = [QW[(team, int(w))] for w in tq if (team, int(w)) in QW]
            qd = q_new - (wavg(base) if base else q_new)
        else:
            q0 = hist_q(x)
            qd = 0.0 if q0 is None else q_new - q0
    m = lambda k: math.exp(QB_EFF[k] * qd)
    r['qb_adj'] = round(qd, 3)
    car = wavg(x.carries); r_ypc = (x.rushing_yards.sum() + 40 * lg['ypc']) / (x.carries.sum() + 40)
    r['rush_yds'] = car * r_ypc * o.get('rush', 1); r['carries'] = car
    r_rtd = (x.rushing_tds.sum() + 40 * lg['rtd']) / (x.carries.sum() + 40)
    td = car * r_rtd
    r['rush_td'] = car * r_rtd
    if grp == 'QB':
        tw = H[(H.team == team) & (H.grp == 'QB')].groupby('week').attempts.sum()
        team_att = wavg(tw.values) * m('att')
        att = 0.5 * team_att + 0.5 * (wavg(x.attempts) if len(x) >= 3 else team_att)
        # his own rates, shrunk toward league rates for a quarterback of his rating (not the plain league average)
        sh = (q_new - Q_LG) if q_new is not None else 0.0
        pr = lambda k, lk: lg[lk] * math.exp(QB_EFF[k] * sh)
        ypa = (x.passing_yards.sum() + 150 * pr('yds', 'ypa')) / (x.attempts.sum() + 150)
        ptd = (x.passing_tds.sum() + 300 * pr('td', 'ptd')) / (x.attempts.sum() + 300)
        it = (x.passing_interceptions.sum() + 150 * pr('int', 'int')) / (x.attempts.sum() + 150)
        r.update({'att': att, 'pass_yds': att * ypa * o.get('pass', 1), 'pass_td': att * ptd * o.get('ptd', 1), 'int': att * it})
    else:
        tg = wavg(x.targets) * m('att')
        ypt = (x.receiving_yards.sum() + 25 * lg['ypt_' + grp]) / (x.targets.sum() + 25) * m('yds')
        ct = (x.receptions.sum() + 25 * lg['ctch_' + grp]) / (x.targets.sum() + 25) * m('cmp')
        rtd = (x.receiving_tds.sum() + 25 * lg['rectd_' + grp]) / (x.targets.sum() + 25) * m('td')
        r.update({'targets': tg, 'rec': tg * ct, 'rec_yds': tg * ypt * o.get('rec_' + grp, 1)})
        td += tg * rtd
        r['rec_td'] = tg * rtd
    r['td_p'] = 1 - math.exp(-td)
    return r


def project_new_qb(name, team, opp_team, H, lg, opp, q_new):
    """A starter with no NFL passes this season (a rookie or a long-time backup): team pass volume, league rates for a quarterback of
    his rating (draft slot when he has no history), and a typical starter's rushing."""
    o = opp.get(opp_team, {})
    tw = H[(H.team == team) & (H.grp == 'QB')].groupby('week').attempts.sum()
    base = [QW[(team, int(w))] for w in tw.index if (team, int(w)) in QW]
    att = wavg(tw.values) * math.exp(QB_EFF['att'] * (q_new - (wavg(base) if base else q_new)))
    sh = q_new - Q_LG
    ypa, ptd, it = (lg['ypa'] * math.exp(QB_EFF['yds'] * sh), lg['ptd'] * math.exp(QB_EFF['td'] * sh), lg['int'] * math.exp(QB_EFF['int'] * sh))
    st = H[(H.grp == 'QB') & (H.attempts >= 15)]
    car = float(st.carries.median())
    ypc, rtd = st.rushing_yards.sum() / max(1, st.carries.sum()), st.rushing_tds.sum() / max(1, st.carries.sum())
    r = {'id': 'new:' + name, 'name': name, 'pos': 'QB', 'team': team, 'opp': opp_team, 'g': 0, 'carries': car,
         'rush_yds': car * ypc * o.get('rush', 1), 'rush_td': car * rtd, 'att': att, 'pass_yds': att * ypa * o.get('pass', 1),
         'pass_td': att * ptd * o.get('ptd', 1), 'int': att * it, 'qb_adj': round(q_new - Q_LG, 3)}
    r['td_p'] = 1 - math.exp(-r['rush_td'])
    return r


def add_returning(pool, H, team, week):
    """Add players listed in overrides.json 'returning' (back from injury after missing the team's recent games) to a team's
    candidate pool, with usage from their last 4 games played. Returns the pool and the ids added."""
    names = [r.get('name') for r in OVR.get('returning', []) if isinstance(r, dict) and r.get('team') == team and week <= r.get('through_week', 99)]
    x = H[(H.team == team) & H.player_display_name.isin(names)]
    if x.empty: return pool, set()
    agg = dict(grp=('grp', 'first'), car=('carries', 'mean'), tg=('targets', 'mean'))
    if 'att' in pool.columns: agg['att'] = ('attempts', 'mean')
    rows = x.sort_values('week').groupby('player_id').tail(4).groupby('player_id').agg(**agg).reset_index()
    ids = set(rows.player_id)
    return pd.concat([pool[~pool.player_id.isin(ids)], rows], ignore_index=True), ids


def share_adjust(recs, H, team, back_ids):
    """When a regular returns, trim his teammates' volume so the position group's carries (RB) or targets (WR/TE) stay near the
    team's totals over its last 4 games. Only used for teams with a returning player."""
    if not back_ids: return
    tw = H[H.team == team]
    tw = tw[tw.week.isin(sorted(tw.week.unique())[-4:])]
    for grp, vol, keys in (({'RB'}, 'carries', ('carries', 'rush_yds', 'rush_td')), ({'WR', 'TE'}, 'targets', ('targets', 'rec', 'rec_yds', 'rec_td'))):
        mine = [r for r in recs if r.get('pos') in grp]
        if not any(r['id'] in back_ids for r in mine): continue
        cap = tw[tw.grp.isin(grp)].groupby('week')[vol].sum().mean()
        back = sum(r.get(vol) or 0 for r in mine if r['id'] in back_ids)
        rest = sum(r.get(vol) or 0 for r in mine if r['id'] not in back_ids)
        if rest <= 0 or back + rest <= cap: continue
        f = max(0.4, (cap - back) / rest)
        for r in mine:
            if r['id'] in back_ids: continue
            td_cut = sum(r.get(k) or 0 for k in keys if k.endswith('_td')) * (1 - f)
            for k in keys:
                if r.get(k) is not None: r[k] = r[k] * f
            if r.get('td_p') is not None:
                r['td_p'] = 1 - math.exp(-max(0.0, -math.log(max(1e-6, 1 - r['td_p'])) - td_cut))
            r['share_adj'] = round(f, 3)


def backtest(weeks=range(4, 10), use_qb=True):
    err = {'pass_yds': [[], []], 'rush_yds': [[], []], 'rec_yds': [[], []]}
    for wk in weeks:
        H, lg, opp = build_context(wk)
        cur = W[W.week == wk]
        for p in cur.itertuples():
            hist = H[H.player_id == p.player_id]
            if len(hist) < 2: continue
            pr = project(p.player_id, p.team, p.opponent_team, H, lg, opp, q_new=QW.get((p.team0, wk)) if use_qb else None)
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
                nxt.setdefault(t, (o, g['id'], g['wk']))
    proj = []
    for t, (o, gid, gwk) in nxt.items():
        qn = starter_q(t, gwk)
        tp = H[H.team == t]
        recent = tp[tp.week >= tp.week.max() - 1]
        pool = recent.groupby('player_id').agg(grp=('grp', 'first'), car=('carries', 'mean'), tg=('targets', 'mean'), att=('attempts', 'mean')).reset_index()
        pool = pool[~pool.player_id.isin(out_ids)]
        names = H.groupby('player_id').player_display_name.last()
        manual_out = set(json.load(open(f'{D}/news.json'))['outs']) | {x.get('name') for x in OVR.get('players_out', []) if isinstance(x, dict) and x.get('team') == t}
        pool = pool[~pool.player_id.map(names).isin(manual_out)]
        pool, back = add_returning(pool, H, t, gwk)
        # starting QB from the model's current starters (handles injuries and trades)
        qname = cur['qb'][t]['qb']
        qrow = H[(H.grp == 'QB') & (H.player_display_name == qname)]
        picks = []
        if len(qrow): picks.append(qrow.player_id.iloc[0])
        picks += pool[pool.grp == 'RB'].sort_values('car', ascending=False).player_id.head(2).tolist()
        picks += pool[pool.grp.isin(['WR', 'TE'])].sort_values('tg', ascending=False).player_id.head(4).tolist()
        recs = []
        for pid in picks:
            r = project(pid, t, o, H, lg, opp, q_new=qn)
            if r and (r['pos'] == 'QB' or r.get('carries', 0) >= 3 or r.get('targets', 0) >= 2.5):
                r['game'] = gid
                recs.append(r)
        share_adjust(recs, H, t, back)
        proj += [{k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()} for r in recs]
        if not len(qrow):
            if qn is not None:
                r = project_new_qb(qname, t, o, H, lg, opp, qn)
                r.update({'game': gid, 'note': 'No passes this season; projected from his rating (draft slot for a rookie)'})
                proj.append({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()})
            else:
                proj.append({'id': None, 'name': qname, 'pos': 'QB', 'team': t, 'opp': o, 'game': gid, 'g': 0, 'note': 'No starts this season'})
    bt = backtest()
    bt0 = backtest(use_qb=False)
    print('backtest without the starting-QB adjustment:', bt0)
    json.dump({'players': proj, 'bt': bt, 'through_week': last_played, 'injury_week': last_wk}, open(f'{D}/players.json', 'w'))
    print(len(proj), 'player projections'); print(bt)
    for r in proj:
        if r['team'] in ('MIA', 'LV', 'ARI') or abs(r.get('qb_adj', 0)) >= 0.05: print(r['team'], r['name'], r['pos'], 'qb_adj', r.get('qb_adj'),
              {k: r.get(k) for k in ('att', 'pass_yds', 'pass_td', 'targets', 'rec_yds', 'rec_td') if r.get(k) is not None})
