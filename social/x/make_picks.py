"""Weekly picks card for X: every game's model pick and win chance, flagging picks against the betting favorite.
1080x1350 PNG (4:5, shows uncropped in the X feed). Usage: python3 make_picks.py [week]"""
import json, os, sys, datetime, html
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tiktok'))
import make_slides as M

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
S = json.load(open(f'{M.ROOT}/data/site_data.json'))
WEEK = int(sys.argv[1]) if len(sys.argv) > 1 else min(g['wk'] for g in S['games'] if g['hs'] is None)
NICK = {'ARI': 'Cardinals', 'ATL': 'Falcons', 'BAL': 'Ravens', 'BUF': 'Bills', 'CAR': 'Panthers', 'CHI': 'Bears', 'CIN': 'Bengals', 'CLE': 'Browns',
        'DAL': 'Cowboys', 'DEN': 'Broncos', 'DET': 'Lions', 'GB': 'Packers', 'HOU': 'Texans', 'IND': 'Colts', 'JAX': 'Jaguars', 'KC': 'Chiefs',
        'LA': 'Rams', 'LAC': 'Chargers', 'LV': 'Raiders', 'MIA': 'Dolphins', 'MIN': 'Vikings', 'NE': 'Patriots', 'NO': 'Saints', 'NYG': 'Giants',
        'NYJ': 'Jets', 'PHI': 'Eagles', 'PIT': 'Steelers', 'SEA': 'Seahawks', 'SF': '49ers', 'TB': 'Buccaneers', 'TEN': 'Titans', 'WAS': 'Commanders'}
e = html.escape

done = [g for g in S['games'] if g['hs'] is not None and g['hs'] != g['as']]
won = sum((g['p'] >= 0.5) == (g['hs'] > g['as']) for g in done)
last = [g for g in done if g['wk'] == WEEK - 1]
won_last = sum((g['p'] >= 0.5) == (g['hs'] > g['as']) for g in last)

rows = []
for g in sorted([g for g in S['games'] if g['wk'] == WEEK], key=lambda g: (g['day'], g['time'] or '')):
    home = g['p'] >= 0.5
    pick, other, p = (g['h'], g['a'], g['p']) if home else (g['a'], g['h'], 1 - g['p'])
    mk = g.get('mk_p')
    upset = mk is not None and (mk >= 0.5) != home          # the model picks the betting underdog
    d = datetime.datetime.strptime(g['day'] + ' ' + (g['time'] or '13:00'), '%Y-%m-%d %H:%M')
    when = d.strftime('%a %-I:%M')
    w = 8 + 92 * (p - 0.5) / 0.5                              # bar length: 50% -> short, 100% -> full
    rows.append(f'''<div class="row{' up' if upset else ''}">
      <span class="when">{when}</span>
      <span class="game">{e(NICK[g['a']])} <i>@</i> {e(NICK[g['h']])}</span>
      <span class="pick">{e(NICK[pick])}{'<em>UPSET</em>' if upset else ''}</span>
      <span class="bar"><b style="width:{w:.0f}%"></b></span><span class="pct">{p:.0%}</span></div>''')

CSS = '''
:root{--bg:#0D1120;--bg-2:#11162A;--surface:#161C34;--line:#252D50;--ink:#F2F4FF;--ink-2:#B9C1DF;--muted:#828BB0;--accent:#FFD23F;--on-accent:#191304;--pink:#FF5D8F;--mint:#3DDC97}
*{box-sizing:border-box;margin:0;padding:0} body{background:#000;font-family:Inter,sans-serif;color:var(--ink);-webkit-font-smoothing:antialiased}
.card{position:relative;width:1080px;height:1350px;background:var(--bg);padding:56px 60px;overflow:hidden}
.card::before{content:"";position:absolute;width:900px;height:900px;border-radius:50%;right:-420px;top:-460px;background:radial-gradient(circle,var(--accent),transparent 65%);opacity:.13}
.card>*{position:relative}
.brand{display:flex;align-items:center;gap:14px}.brand svg{width:56px;height:56px}
.brand .word{font-family:'Inter Display';font-weight:800;font-size:36px;letter-spacing:-.02em}.brand .word b{color:var(--accent)}
.brand .wk{margin-left:auto;font-weight:700;font-size:22px;letter-spacing:.08em;color:var(--ink-2);border:2px solid var(--line);background:var(--bg-2);padding:6px 16px;border-radius:999px}
h1{font-family:'Inter Display';font-weight:900;font-size:96px;letter-spacing:-.04em;line-height:1;margin-top:34px}
h1 span{color:var(--accent)}
.rec{margin-top:14px;font-size:27px;font-weight:600;color:var(--ink-2)} .rec b{color:var(--ink)}
.list{margin-top:30px;background:var(--surface);border:2px solid var(--line);border-radius:28px;padding:10px 26px}
.row{display:grid;grid-template-columns:108px 1fr 236px 128px 64px;align-items:center;gap:12px;height:58px;border-bottom:1.5px solid var(--line);font-size:24px}
.row:last-child{border-bottom:0}
.when{color:var(--muted);font-weight:600;font-size:20px}
.game{color:var(--ink-2);font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis} .game i{font-style:normal;color:var(--muted)}
.pick{font-weight:800;display:flex;align-items:center;gap:8px;white-space:nowrap}
.pick em{font-style:normal;font-size:14px;font-weight:800;letter-spacing:.06em;background:var(--pink);color:var(--on-accent);padding:3px 7px;border-radius:6px}
.bar{height:12px;background:var(--bg-2);border-radius:6px;overflow:hidden} .bar b{display:block;height:100%;background:var(--accent);border-radius:6px}
.up .bar b{background:var(--pink)}
.pct{font-weight:800;text-align:right;font-variant-numeric:tabular-nums}
.foot{position:absolute;left:60px;right:60px;bottom:48px;display:flex;flex-direction:column;gap:8px;font-size:21px;color:var(--muted);font-weight:600}
.foot .url{color:var(--accent);font-weight:700;font-size:28px}
'''
doc = f'''<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body><div class="card">
  <div class="brand">{M.LOGO}<span class="word">Pocket <b>Protector</b></span><span class="wk">NFL WEEK {WEEK}</span></div>
  <h1>Week {WEEK} <span>picks</span></h1>
  <p class="rec">Model record picking winners: <b>{won}-{len(done) - won}</b> ({won / len(done):.0%}) · Week {WEEK - 1}: <b>{won_last}-{len(last) - won_last}</b></p>
  <div class="list">{''.join(rows)}</div>
  <div class="foot"><span>Model win chance · <span style="color:var(--pink);font-weight:800">UPSET</span> = model picks the betting underdog</span><span class="url">{{URL}}</span></div>
</div></body></html>'''.replace('{URL}', 'jakemorning05.github.io/pocket-protector')
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, f'week{WEEK}_picks.html'), 'w').write(doc)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1080, 'height': 1350}, device_scale_factor=1)
    pg.goto('file://' + os.path.join(OUT, f'week{WEEK}_picks.html'))
    pg.evaluate('() => document.fonts.ready')
    print(pg.evaluate('''() => { const l = document.querySelector('.list').getBoundingClientRect(), f = document.querySelector('.foot').getBoundingClientRect();
        const over = [...document.querySelectorAll('.game,.pick')].filter(x => x.scrollWidth > x.clientWidth + 1).map(x => x.textContent);
        return {list_bottom: Math.round(l.bottom), foot_top: Math.round(f.top), clipped: over}; }'''))
    pg.locator('.card').screenshot(path=os.path.join(OUT, f'week{WEEK}_picks.png'))
    b.close()
print(f'{won}-{len(done) - won}', f'last week {won_last}-{len(last) - won_last}', os.path.join(OUT, f'week{WEEK}_picks.png'))
