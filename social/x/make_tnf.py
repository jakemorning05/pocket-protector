"""Single-game preview card for X (1080x1350): model pick, projected score, model line vs the betting line, key notes and the top
fantasy projections. Usage: python3 make_tnf.py GAME_ID 'note one' 'note two' ..."""
import json, os, sys, datetime, html
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tiktok'))
import make_slides as M

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
GID = sys.argv[1] if len(sys.argv) > 1 else '2026_10_WAS_NYG'
NOTES = sys.argv[2:]
NICK = {'WAS': 'Commanders', 'NYG': 'Giants'}
FULL = {'WAS': 'Washington Commanders', 'NYG': 'New York Giants'}
e = html.escape
S = json.load(open(f'{M.ROOT}/data/site_data.json'))
F = json.load(open(f'{M.ROOT}/data/fantasy.json'))
g = next(x for x in S['games'] if x['id'] == GID)
a, h = g['a'], g['h']
pa = 1 - g['p']
pick, pp = (a, pa) if pa >= 0.5 else (h, g['p'])
sa, sh = round((g['tot'] - g['m']) / 2), round((g['tot'] + g['m']) / 2)
mline = f"{a if g['m'] < 0 else h} −{abs(g['m']):.0f}" if round(abs(g['m'])) else 'Pick ’em'
bline = f"{h if g['mk_spread'] > 0 else a} −{abs(g['mk_spread']):g}"
done = [x for x in S['games'] if x['hs'] is not None and x['hs'] != x['as']]
won = sum((x['p'] >= 0.5) == (x['hs'] > x['as']) for x in done)
d = datetime.datetime.strptime(g['day'] + ' ' + g['time'], '%Y-%m-%d %H:%M')
when = d.strftime('%A') + ' ' + d.strftime('%-I:%M %p').replace(':00', '') + ' ET'
ppr = lambda r: (r.get('pass_yds', 0) / 25 + 4 * r.get('pass_td', 0) - 2 * r.get('int', 0) + r.get('rush_yds', 0) / 10
                 + 6 * r.get('rush_td', 0) + r.get('rec_yds', 0) / 10 + 6 * r.get('rec_td', 0) + r.get('rec', 0))
fr = sorted([r for r in F['games'] if r['game'] == GID], key=lambda r: -ppr(r))[:6]


def stat(r):
    if r['pos'] == 'QB': return f"{round(r.get('pass_yds') or 0)} pass yds, {round(r.get('rush_yds') or 0)} rush"
    if r['pos'] == 'RB': return f"{round(r.get('rush_yds') or 0)} rush yds, {(r.get('rec') or 0):.1f} catches"
    return f"{(r.get('rec') or 0):.1f} catches, {round(r.get('rec_yds') or 0)} yds"


CSS = '''
:root{--bg:#0D1120;--bg-2:#11162A;--surface:#161C34;--line:#252D50;--ink:#F2F4FF;--ink-2:#B9C1DF;--muted:#828BB0;--accent:#FFD23F;--on-accent:#191304;--pink:#FF5D8F;--mint:#3DDC97;--blue:#4DA3FF}
*{box-sizing:border-box;margin:0;padding:0} body{background:#000;font-family:Inter,sans-serif;color:var(--ink);-webkit-font-smoothing:antialiased}
.card{position:relative;width:1080px;height:1350px;background:var(--bg);padding:56px 60px;overflow:hidden}
.card::before{content:"";position:absolute;width:900px;height:900px;border-radius:50%;right:-420px;top:-460px;background:radial-gradient(circle,var(--accent),transparent 65%);opacity:.13}
.card>*{position:relative}
.brand{display:flex;align-items:center;gap:14px}.brand svg{width:56px;height:56px}
.brand .word{font-family:'Inter Display';font-weight:800;font-size:36px;letter-spacing:-.02em}.brand .word b{color:var(--accent)}
.brand .wk{margin-left:auto;font-weight:700;font-size:22px;letter-spacing:.08em;color:var(--ink-2);border:2px solid var(--line);background:var(--bg-2);padding:6px 16px;border-radius:999px}
h1{font-family:'Inter Display';font-weight:900;font-size:84px;letter-spacing:-.04em;line-height:1;margin-top:30px}
h1 i{font-style:normal;color:var(--muted);font-weight:700}
.when{margin-top:10px;font-size:26px;font-weight:600;color:var(--ink-2)}
.top{display:grid;grid-template-columns:1.15fr 1fr;gap:20px;margin-top:28px}
.box{background:var(--surface);border:2px solid var(--line);border-radius:26px;padding:22px 26px}
.lab{font-size:20px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.pick{margin-top:6px}
.pick b{display:block;font-family:'Inter Display';font-weight:900;font-size:66px;line-height:1.05;color:var(--accent);letter-spacing:-.03em}
.pick span{display:block;font-size:28px;font-weight:700;color:var(--ink-2);margin-top:4px}
.bar{height:14px;background:var(--bg-2);border-radius:7px;overflow:hidden;margin-top:12px}.bar b{display:block;height:100%;background:var(--accent)}
.score{font-family:'Inter Display';font-weight:900;font-size:52px;margin-top:8px;letter-spacing:-.02em}
.lines{display:flex;flex-direction:column;gap:8px;margin-top:10px;font-size:25px;font-weight:600;color:var(--ink-2)} .lines b{color:var(--ink)}
.notes{margin-top:20px;display:flex;flex-direction:column;gap:10px}
.note{font-size:25px;font-weight:600;color:var(--ink-2);line-height:1.3;padding-left:26px;position:relative}
.note::before{content:"";position:absolute;left:0;top:12px;width:10px;height:10px;border-radius:50%;background:var(--accent)}
.fan{margin-top:20px}
.row{display:grid;grid-template-columns:1fr 330px 90px;align-items:center;height:56px;border-top:1.5px solid var(--line);font-size:24px}
.row .n b{font-weight:800}.row .n small{font-size:18px;font-weight:800;margin-left:10px;color:var(--pc)}
.row .s{color:var(--muted);font-weight:600;font-size:21px}.row .p{text-align:right;font-family:'Inter Display';font-weight:900;font-size:30px}
.foot{position:absolute;left:60px;right:60px;bottom:44px;display:flex;justify-content:space-between;align-items:flex-end;font-size:20px;color:var(--muted);font-weight:600}
.foot .url{color:var(--accent);font-weight:700;font-size:26px}
'''
rows = ''.join(f'''<div class="row" style="--pc:{M.POS_COLOR[r['pos']]}"><span class="n"><b>{e(r['name'])}</b><small>{r['pos']} · {r['team']}</small></span>
  <span class="s">{stat(r)}</span><span class="p">{ppr(r):.1f}</span></div>''' for r in fr)
doc = f'''<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body><div class="card">
  <div class="brand">{M.LOGO}<span class="word">Pocket <b>Protector</b></span><span class="wk">THURSDAY NIGHT · WEEK {g['wk']}</span></div>
  <h1>{NICK[a]} <i>@</i> {NICK[h]}</h1>
  <p class="when">{when} · model record this season {won}-{len(done) - won}</p>
  <div class="top">
    <div class="box"><div class="lab">Model pick</div><div class="pick"><b>{NICK[pick]}</b><span>{pp:.0%} to win</span></div>
      <div class="bar"><b style="width:{pp * 100:.0f}%"></b></div>
      <div class="lab" style="margin-top:18px">Projected score</div><div class="score">{a} {sa} – {sh} {h}</div></div>
    <div class="box"><div class="lab">Spread</div><div class="lines"><span>Model: <b>{mline}</b></span><span>Betting line: <b>{bline}</b></span></div>
      <div class="lab" style="margin-top:18px">Quarterbacks</div><div class="lines"><span><b>{e(g['qa'])}</b> {a}</span><span><b>{e(g['qh'])}</b> {h}</span></div></div>
  </div>
  <div class="notes">{''.join(f'<div class="note">{e(n)}</div>' for n in NOTES)}</div>
  <div class="box fan"><div class="lab" style="margin-bottom:8px">Top fantasy projections · PPR</div>{rows}</div>
  <div class="foot"><span>Model projections, not guarantees</span><span class="url">jakemorning05.github.io/pocket-protector</span></div>
</div></body></html>'''
os.makedirs(OUT, exist_ok=True)
fn = os.path.join(OUT, f'week{g["wk"]}_{a.lower()}_{h.lower()}')
open(fn + '.html', 'w').write(doc)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1080, 'height': 1350}, device_scale_factor=1)
    pg.goto('file://' + fn + '.html'); pg.evaluate('() => document.fonts.ready')
    print(pg.evaluate('''() => { const f = document.querySelector('.foot').getBoundingClientRect(), x = document.querySelector('.fan').getBoundingClientRect();
        const over = [...document.querySelectorAll('h1,.row .n,.row .s,.lines span,.score')].filter(el => el.scrollWidth > el.clientWidth + 1).map(el => el.textContent.trim().slice(0, 30));
        return {fan_bottom: Math.round(x.bottom), foot_top: Math.round(f.top), clipped: over}; }'''))
    pg.locator('.card').screenshot(path=fn + '.png')
    b.close()
print(fn + '.png', pick, f'{pp:.0%}', sa, sh, mline, bline)
