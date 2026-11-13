"""Single-game recap card for X (1080x1350): the model's pre-game pick and projected score against the final, the logged picks
against the line, and the graded Kalshi props. Usage: python3 make_recap.py GAME_ID"""
import json, os, sys, html
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'tiktok'))
import make_slides as M

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'out')
GID = sys.argv[1] if len(sys.argv) > 1 else '2026_10_WAS_NYG'
NICK = {'WAS': 'Commanders', 'NYG': 'Giants'}
SN = {'pass_yds': 'pass yds', 'rush_yds': 'rush yds', 'rec_yds': 'rec yds'}
e = html.escape
D = f'{M.ROOT}/data'
S = json.load(open(f'{D}/site_data.json'))
g = next(x for x in S['games'] if x['id'] == GID)
a, h = g['a'], g['h']
pa = 1 - g['p']
pick, pp = (a, pa) if pa >= 0.5 else (h, g['p'])
sa, sh = round((g['tot'] - g['m']) / 2), round((g['tot'] + g['m']) / 2)
right = (pick == h) == (g['hs'] > g['as'])
done = [x for x in S['games'] if x['hs'] is not None and x['hs'] != x['as']]
won = sum((x['p'] >= 0.5) == (x['hs'] > x['as']) for x in done)
B = json.load(open(f'{D}/bet_log.json')); B = B if isinstance(B, list) else B.get('bets', [])
bets = [b for b in B if b.get('game') == GID and b.get('result')]
L = json.load(open(f'{D}/prop_log.json'))
props = [p for p in L if p['game'] == GID and p.get('won') is not None]
pw = sum(p['won'] for p in props); pu = sum(p['profit'] for p in props)
allp = [p for p in L if p.get('won') is not None]
aw = sum(p['won'] for p in allp)
# highlights: the biggest hits and misses by how far the result landed from the line
key = lambda p: abs(p['actual'] - p['thr']) / p['thr']   # relative to the line, so low lines count too
show = sorted([p for p in props if p['won']], key=key, reverse=True)[:4] + sorted([p for p in props if not p['won']], key=key, reverse=True)[:3]
mark = lambda ok: '<em class="ok">✓</em>' if ok else '<em class="no">✗</em>'


def prow(p):
    side = f"{p['thr']}+ {SN[p['stat']]}" if p['pick'] == 'YES' else f"Under {p['thr']} {SN[p['stat']]}"
    return f'''<div class="row">{mark(p['won'])}<span class="n"><b>{e(p['player'])}</b> {side}</span><span class="r">{p['actual']:g}</span></div>'''


def brow(b):
    side = b.get('side'); line = b.get('line')
    txt = f"{NICK.get(side, side)} {'+' if line > 0 else ''}{line:g}" if side in (a, h) else f"{side} {line:g}"
    return f'<div class="row">{mark(b["result"] == "win")}<span class="n"><b>{e(txt)}</b></span><span class="r">{g["as"]}-{g["hs"]}</span></div>'


CSS = '''
:root{--bg:#0D1120;--bg-2:#11162A;--surface:#161C34;--line:#252D50;--ink:#F2F4FF;--ink-2:#B9C1DF;--muted:#828BB0;--accent:#FFD23F;--pink:#FF5D8F;--mint:#3DDC97}
*{box-sizing:border-box;margin:0;padding:0} body{background:#000;font-family:Inter,sans-serif;color:var(--ink);-webkit-font-smoothing:antialiased}
.card{position:relative;width:1080px;height:1350px;background:var(--bg);padding:56px 60px;overflow:hidden}
.card::before{content:"";position:absolute;width:900px;height:900px;border-radius:50%;right:-420px;top:-460px;background:radial-gradient(circle,var(--mint),transparent 65%);opacity:.12}
.card>*{position:relative}
.brand{display:flex;align-items:center;gap:14px}.brand svg{width:56px;height:56px}
.brand .word{font-family:'Inter Display';font-weight:800;font-size:36px;letter-spacing:-.02em}.brand .word b{color:var(--accent)}
.brand .wk{margin-left:auto;font-weight:700;font-size:22px;letter-spacing:.08em;color:var(--ink-2);border:2px solid var(--line);background:var(--bg-2);padding:6px 16px;border-radius:999px}
h1{font-family:'Inter Display';font-weight:900;font-size:92px;letter-spacing:-.04em;line-height:1;margin-top:30px} h1 span{color:var(--mint)}
.final{margin-top:12px;font-size:34px;font-weight:700;color:var(--ink-2)}
.top{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:26px}
.box{background:var(--surface);border:2px solid var(--line);border-radius:26px;padding:20px 26px}
.lab{font-size:20px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.big{font-family:'Inter Display';font-weight:900;font-size:50px;margin-top:6px;letter-spacing:-.02em;white-space:nowrap}
.sm{font-size:24px;font-weight:600;color:var(--ink-2);margin-top:4px}
.sec{margin-top:20px}
.head{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:6px}
.head b{font-family:'Inter Display';font-weight:900;font-size:34px}
.row{display:flex;align-items:center;gap:16px;height:52px;border-top:1.5px solid var(--line);font-size:24px}
.row em{font-style:normal;font-weight:900;font-size:28px;width:30px;text-align:center} .row em.ok{color:var(--mint)} .row em.no{color:var(--pink)}
.row .n{color:var(--ink-2);font-weight:600;white-space:nowrap} .row .n b{color:var(--ink);font-weight:800}
.row .r{margin-left:auto;font-family:'Inter Display';font-weight:900;font-size:28px}
.foot{position:absolute;left:60px;right:60px;bottom:44px;display:flex;justify-content:space-between;align-items:flex-end;font-size:21px;color:var(--muted);font-weight:600}
.foot .url{color:var(--accent);font-weight:700;font-size:26px}
'''
doc = f'''<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body><div class="card">
  <div class="brand">{M.LOGO}<span class="word">Pocket <b>Protector</b></span><span class="wk">WEEK {g['wk']} · THURSDAY RECAP</span></div>
  <h1>{'Called it.' if right else 'Missed it.'} <span>{'✓' if right else ''}</span></h1>
  <p class="final">Final: {NICK[a]} {g['as']}, {NICK[h]} {g['hs']}</p>
  <div class="top">
    <div class="box"><div class="lab">Model pick</div><div class="big">{NICK[pick]} {mark(right)}</div><div class="sm">{pp:.0%} to win before kickoff</div></div>
    <div class="box"><div class="lab">Projected score</div><div class="big">{sa}–{sh}</div><div class="sm">Final {g['as']}–{g['hs']}</div></div>
  </div>
  <div class="box sec"><div class="head"><span class="lab">Picks against the line · logged Monday</span><b>{sum(b['result'] == 'win' for b in bets)}–{sum(b['result'] == 'loss' for b in bets)}</b></div>
    {''.join(brow(b) for b in bets)}</div>
  <div class="box sec"><div class="head"><span class="lab">Player props vs. Kalshi prices · {len(props)} logged</span><b>{pw}–{len(props) - pw}</b></div>
    {''.join(prow(p) for p in show)}</div>
  <p class="sm" style="margin-top:16px">Season: <b style="color:var(--ink)">{won}–{len(done) - won}</b> picking winners · prop test since Week 9: {aw}–{len(allp) - aw}</p>
  <div class="foot"><span>Every pick logged before kickoff</span><span class="url">jakemorning05.github.io/pocket-protector</span></div>
</div></body></html>'''
os.makedirs(OUT, exist_ok=True)
fn = os.path.join(OUT, f'week{g["wk"]}_{a.lower()}_{h.lower()}_recap')
open(fn + '.html', 'w').write(doc)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1080, 'height': 1350}, device_scale_factor=1)
    pg.goto('file://' + fn + '.html'); pg.evaluate('() => document.fonts.ready')
    print(pg.evaluate('''() => { const f = document.querySelector('.foot').getBoundingClientRect(); const s = [...document.querySelectorAll('.sm')].pop().getBoundingClientRect();
        const over = [...document.querySelectorAll('h1,.big,.row .n')].filter(el => el.scrollWidth > el.clientWidth + 1).map(el => el.textContent.trim().slice(0, 30));
        return {last_bottom: Math.round(s.bottom), foot_top: Math.round(f.top), clipped: over}; }'''))
    pg.locator('.card').screenshot(path=fn + '.png')
    b.close()
print(fn + '.png', pw, len(props), round(pu, 2), won, len(done), aw, len(allp))
