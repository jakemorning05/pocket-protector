"""Writes collab/briefing.md: a plain-text snapshot of the model for the parlay room (upcoming games, quarterbacks, injury
flags, logged Kalshi props with the model's chance, and records). Run by scripts/update.sh after the site build."""
import json, os, datetime
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
S = json.load(open(f'{D}/site_data.json')); N = json.load(open(f'{D}/news.json')); L = json.load(open(f'{D}/prop_log.json'))
B = json.load(open(f'{D}/bet_log.json')); B = B if isinstance(B, list) else B.get('bets', [])
done = [g for g in S['games'] if g['hs'] is not None and g['hs'] != g['as']]
won = sum((g['p'] >= 0.5) == (g['hs'] > g['as']) for g in done)
fav = [g for g in done if g.get('mk_p') is not None]
fwon = sum((g['mk_p'] > 0.5) == (g['hs'] > g['as']) for g in fav)
up = sorted([g for g in S['games'] if g['hs'] is None], key=lambda g: (g['day'], g['time'] or ''))
wk = min((g['wk'] for g in up), default=None)
graded = [p for p in L if p.get('won') is not None]
out = [f'# Model briefing (updated {N.get("asof", "")})', '',
       f'- Picking winners this season: {won}-{len(done) - won}. Betting favorites on the same games: {fwon}-{len(fav) - fwon}.',
       f'- Prop test vs. Kalshi (since Week 9): {sum(p["won"] for p in graded)}-{len(graded) - sum(p["won"] for p in graded)}, '
       f'{sum(p["profit"] for p in graded):+.2f} units at one contract each.', '',
       f'## Week {wk} games still to play', '',
       '| Game | Kickoff (ET) | QBs | Model win % (home) | Market win % (home) | Model margin (home) | Line (home) | Model total | Market total |',
       '|---|---|---|---|---|---|---|---|---|']
for g in up:
    if g['wk'] != wk: continue
    sp = g.get('mk_spread')
    out.append(f"| {g['a']} @ {g['h']} | {g['day']} {g['time'] or ''} | {g.get('qa')} / {g.get('qh')} | {g['p']:.0%} | "
               f"{(g.get('mk_p') or 0):.0%} | {g['m']:+.1f} | {('-' if sp and sp > 0 else '+') + str(abs(sp)) if sp else 'n/a'} | "
               f"{g['tot']:.1f} | {g.get('mk_total') or 'n/a'} |")
ids = {g['id'] for g in up if g['wk'] == wk}
out += ['', '## Logged Kalshi props for those games (model chance of YES vs. price)', '',
        '| Game | Player | Line | Price | Model | Model side |', '|---|---|---|---|---|---|']
for p in sorted([p for p in L if p['game'] in ids], key=lambda p: (p['game'], -abs(p['p_over'] - p['price']))):
    out.append(f"| {p['game'][8:].replace('_', ' @ ')} | {p['player']} | {p['thr']}+ {p['stat'].replace('_', ' ')} | {p['price']:.0%} | {p['p_over']:.0%} | {p['pick']} |")
out += ['', '## Injury and role notes the model is using', '']
out += [f'- {k}: {v}' for k, v in N.get('flags', {}).items()]
out += ['', '## Recent headlines', ''] + [f"- {it['team']}: {it['text']} ({it['src']})" for it in N.get('items', [])[:12]]
out += ['', 'Known model weak spots: backups who inherit a starter\'s carries are underprojected; running back props ignore game',
        'script (trailing teams run less); very low receiving lines (10-15 yards) are overrated for YES; no weather inputs.']
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'briefing.md'), 'w').write('\n'.join(out) + '\n')
print('collab/briefing.md written', len(out), 'lines')
