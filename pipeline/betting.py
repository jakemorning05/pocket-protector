"""Side and total picks vs. current lines, logged for closing-line-value (CLV) tracking.

usage: python3 betting.py log     (log picks for unplayed games that have lines and aren't logged yet)
       python3 betting.py grade   (fill in closing lines, results and CLV from the refreshed schedule file)
"""
import json, os, sys, datetime
import pandas as pd
from scipy.stats import norm

D = os.path.join(os.path.dirname(__file__), '..', 'data')
LOG = f'{D}/bet_log.json'
TOTAL_SD = 13.5  # spread of actual totals around the model's total (2017-2025 held-out error)


def log(stamp):
    site = json.load(open(f'{D}/site_data.json'))
    sig = site['sigma']
    entries = json.load(open(LOG)) if os.path.exists(LOG) else []
    have = {(e['game'], e['kind']) for e in entries}
    for g in site['games']:
        if g['hs'] is not None or g['mk_spread'] is None: continue
        L, m = g['mk_spread'], g['m']
        p_home = 1 - norm.cdf((L - m) / sig)  # home covers if margin > L
        side = g['h'] if m > L else g['a']
        p = p_home if side == g['h'] else 1 - p_home
        if (g['id'], 'spread') not in have:
            entries.append({'game': g['id'], 'wk': g['wk'], 'a': g['a'], 'h': g['h'], 'kind': 'spread', 'side': side, 'line': L,
                            'model': round(m, 2), 'p': round(p, 3), 'ev': round(p * 100 / 110 - (1 - p), 3), 'logged': stamp,
                            'close': None, 'clv': None, 'result': None})
        if g['mk_total'] is not None and (g['id'], 'total') not in have:
            T, t = g['mk_total'], g['tot']
            p_over = 1 - norm.cdf((T - t) / TOTAL_SD)
            side = 'Over' if t > T else 'Under'
            p = p_over if side == 'Over' else 1 - p_over
            entries.append({'game': g['id'], 'wk': g['wk'], 'a': g['a'], 'h': g['h'], 'kind': 'total', 'side': side, 'line': T,
                            'model': round(t, 1), 'p': round(p, 3), 'ev': round(p * 100 / 110 - (1 - p), 3), 'logged': stamp,
                            'close': None, 'clv': None, 'result': None})
    json.dump(entries, open(LOG, 'w'), indent=1)
    return entries


def grade():
    g = pd.read_csv(f'{D}/games.csv'); g = g[g.season == 2026].set_index('game_id')
    entries = json.load(open(LOG))
    for e in entries:
        if e['result'] is not None or e['game'] not in g.index: continue
        r = g.loc[e['game']]
        if pd.isna(r.home_score): continue
        if e['kind'] == 'spread':
            close = float(r.spread_line); margin = r.home_score - r.away_score
            home = e['side'] == e['h']
            e['clv'] = round((close - e['line']) if home else (e['line'] - close), 1)
            c = (margin - e['line']) if home else (e['line'] - margin)
        else:
            close = float(r.total_line); tot = r.home_score + r.away_score
            over = e['side'] == 'Over'
            e['clv'] = round((close - e['line']) if over else (e['line'] - close), 1)
            c = (tot - e['line']) if over else (e['line'] - tot)
        e['close'] = close
        e['result'] = 'push' if c == 0 else ('win' if c > 0 else 'loss')
    json.dump(entries, open(LOG, 'w'), indent=1)
    return entries


if __name__ == '__main__':
    if sys.argv[1:] == ['grade']:
        es = grade()
    else:
        es = log(sys.argv[2] if len(sys.argv) > 2 else datetime.datetime.now().strftime('%b %-d %-I:%M %p'))
    for e in es:
        print(f"wk{e['wk']} {e['a']}@{e['h']} {e['kind']:6s} {e['side']:5s} {e['line']:>6}  model {e['model']:>6}  p {e['p']:.0%}  ev {e['ev']:+.1%}  {e['result'] or ''}")
