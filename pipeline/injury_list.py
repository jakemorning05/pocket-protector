"""Refresh the injured-starters list on the News tab from the latest official injury report.

Keeps everything else in data/news.json (headlines, outs, flags) as it is.
A player is listed if he's Out, Doubtful or Questionable and played 50%+ of snaps over his last 3 games (QBs always).
Late outs from data/overrides.json players_out are added (same snap rule) so the table matches what the model assumes.
"""
import json, os, re
import pandas as pd

D = os.path.join(os.path.dirname(__file__), '..', 'data')
FIX = {'SD': 'LAC', 'OAK': 'LV', 'STL': 'LA', 'LAR': 'LA'}
SEASON = 2026


def norm(n):
    return re.sub(r"\b(jr|sr|ii|iii|iv|v)\b", "", re.sub(r"[^a-z ]", "", str(n).lower())).strip()


def main():
    inj = pd.read_csv(f'{D}/injuries_{SEASON}.csv'); inj['team'] = inj.team.replace(FIX)
    wk = int(inj.week.max())
    sn = pd.read_csv(f'{D}/snap_counts_{SEASON}.csv'); sn['team'] = sn.team.replace(FIX)
    sn['key'] = sn.player.map(norm)
    x = inj[(inj.week == wk) & inj.report_status.isin(['Out', 'Doubtful', 'Questionable'])].copy()
    x['key'] = x.full_name.map(norm)
    rows = []
    for r in x.itertuples():
        s = sn[(sn.team == r.team) & (sn.key == r.key) & (sn.week < wk)].sort_values('week').tail(3)
        share = max(s.offense_pct.mean() if len(s) else 0, s.defense_pct.mean() if len(s) else 0)
        if share >= 0.5 or r.position == 'QB':
            rows.append({'team': r.team, 'name': r.full_name, 'pos': r.position, 'status': r.report_status,
                         'injury': r.report_primary_injury if isinstance(r.report_primary_injury, str) else '', 'snap': round(float(share), 2)})
    # late news the model already uses (data/overrides.json players_out) but the official report may not show yet
    O = json.load(open(f'{D}/overrides.json'))
    have = {(r['team'], norm(r['name'])) for r in rows}
    for o in O.get('players_out', []):
        src = o.get('source', '')
        if src.startswith('Traded') or (o['team'], norm(o['name'])) in have:
            continue
        s = sn[(sn.team == o['team']) & (sn.key == norm(o['name']))].sort_values('week').tail(3)
        # peak role over his last 3 games: the game he got hurt in drags an average down
        share = max(s.offense_pct.max() if len(s) else 0, s.defense_pct.max() if len(s) else 0)
        pos = s.position.iloc[-1] if len(s) else ''
        if share >= 0.5 or pos == 'QB':
            why = re.search(r'\(([^)]+)\)', src)
            note = why.group(1) if why else src.split(':', 1)[-1].strip().split(',')[0]
            rows.append({'team': o['team'], 'name': o['name'], 'pos': pos, 'status': 'Out',
                         'injury': note[:1].upper() + note[1:] + ' (late news)', 'snap': round(float(share), 2)})
    n = json.load(open(f'{D}/news.json'))
    n['injuries'] = sorted(rows, key=lambda r: (r['team'], -r['snap'])); n['injury_week'] = wk
    json.dump(n, open(f'{D}/news.json', 'w'), indent=1)
    print(len(rows), 'regulars on the Week', wk, 'injury report')


if __name__ == '__main__':
    main()
