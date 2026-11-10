"""Early player leans for the coming week, before prop lines are posted.

For each game's main players it compares the model's projection with the player's season median for that stat
(roughly where sportsbooks open their lines) and keeps the strongest leans. Rebuilt on every refresh, so the leans
move with injuries and starting-QB news until kickoff. When real prices are posted, log them in props.py instead.
Writes data/early_props.json.
"""
import json, os, math, datetime
from zoneinfo import ZoneInfo
import pandas as pd
from props import prob_over, STAT_COL

D = os.path.join(os.path.dirname(__file__), '..', 'data')
ET = ZoneInfo('America/New_York')
STAT_NAME = {'pass_yds': 'passing yards', 'rush_yds': 'rushing yards', 'rec_yds': 'receiving yards'}
MIN_GAMES = 3
# only players with roles big enough that books post a line for them
MIN_LINE = {'pass_yds': 150, 'rush_yds': 30, 'rec_yds': 25}


def main():
    cal = json.load(open(f'{D}/prop_cal.json'))
    raw = {(p['game'], p['id']): p for p in json.load(open(f'{D}/players.json'))['players']}
    fan = json.load(open(f'{D}/fantasy.json'))
    site = json.load(open(f'{D}/site_data.json'))
    W = pd.read_csv(f'{D}/stats_player_week_2026.csv', low_memory=False)
    W = W[W.season_type == 'REG'] if 'season_type' in W else W
    # the coming week is the first week with no game played yet
    wk = min(g['wk'] for g in site['games'] if g['hs'] is None and not any(x['wk'] == g['wk'] and x['hs'] is not None for x in site['games']))
    pool = [r for r in fan['games'] if r['wk'] == wk]  # main players, injured players already removed
    out = []
    for g in sorted([g for g in site['games'] if g['wk'] == wk], key=lambda g: (g['day'], g['time'] or '')):
        cands = []
        for team in (g['a'], g['h']):
            ps = [r for r in pool if r['game'] == g['id'] and r['team'] == team]
            qb = [r for r in ps if r['pos'] == 'QB'][:1]
            rb = sorted([r for r in ps if r['pos'] == 'RB'], key=lambda r: -r['carries'])[:1]
            rc = sorted([r for r in ps if r['pos'] in ('WR', 'TE')], key=lambda r: -(r.get('targets') or 0))[:3]
            for r, st in [(r, 'pass_yds') for r in qb] + [(r, 'rush_yds') for r in rb] + [(r, 'rec_yds') for r in rc]:
                p = raw.get((g['id'], r['id']))
                hist = W[W.player_id == r['id']][STAT_COL[st]].dropna()
                if not p or p.get(st) is None or len(hist) < MIN_GAMES:
                    continue
                line = math.floor(float(hist.median())) + 0.5  # books post .5 lines near a player's typical game
                if line < MIN_LINE[st]:
                    continue
                mu, sd, pov = prob_over(p[st], line + 0.5, st, cal)
                cands.append({'player': r['name'], 'team': team, 'pos': r['pos'], 'stat': st, 'line': line, 'proj': round(mu, 1),
                              'p_over': round(float(pov), 3), 'side': 'Over' if pov >= 0.5 else 'Under', 'games': int(len(hist))})
        cands.sort(key=lambda c: -abs(c['p_over'] - 0.5))
        td = sorted([r for r in pool if r['game'] == g['id']], key=lambda r: -(r.get('td_p') or 0))[:2]
        out.append({'id': g['id'], 'a': g['a'], 'h': g['h'], 'day': g['day'], 'time': g['time'], 'leans': cands[:3],
                    'td': [{'player': r['name'], 'team': r['team'], 'pos': r['pos'], 'p': round(r['td_p'], 3)} for r in td]})
    stamp = datetime.datetime.now(ET).strftime('%a, %b %-d, %-I:%M %p ET')
    json.dump({'week': wk, 'asof': stamp, 'games': out}, open(f'{D}/early_props.json', 'w'), indent=1)
    print(f'early leans for Week {wk}: {sum(len(x["leans"]) for x in out)} across {len(out)} games')
    for x in out:
        print(f"{x['a']}@{x['h']}: " + '; '.join(f"{c['player']} {c['side']} {c['line']} {c['stat']} ({max(c['p_over'], 1 - c['p_over']):.0%}, proj {c['proj']})" for c in x['leans']))


if __name__ == '__main__':
    main()
