"""Fill in final scores from overrides.json 'results' for games nflverse hasn't posted yet (it usually catches up the next
morning, and its numbers win once they're in). Runs right after the download step in scripts/update.sh."""
import json, os
import pandas as pd

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
res = [r for r in json.load(open(f'{D}/overrides.json')).get('results', []) if isinstance(r, dict)]
g = pd.read_csv(f'{D}/games.csv', low_memory=False)
n = 0
for r in res:
    m = (g.game_id == r['game']) & g.home_score.isna()
    if m.any():
        g.loc[m, ['away_score', 'home_score']] = [r['away'], r['home']]
        g.loc[m, 'result'] = r['home'] - r['away']; g.loc[m, 'total'] = r['home'] + r['away']
        g.loc[m, 'overtime'] = int(r.get('overtime', 0)); n += 1
if n:
    g.to_csv(f'{D}/games.csv', index=False)
print(f'manual results applied: {n}')
