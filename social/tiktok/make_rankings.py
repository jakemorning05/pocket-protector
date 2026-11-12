"""Week rankings carousel for TikTok: the model's top projected players at each position (PPR), one position per slide.
Leaves out games already played or kicking off before the post (EXCLUDE). Usage: python3 make_rankings.py"""
import json, os
import make_slides as M

OUT = os.path.dirname(os.path.abspath(__file__))
WEEK = M.WEEK
EXCLUDE = {f'2026_{WEEK:02d}_WAS_NYG'}           # Thursday night
POSITIONS = [('QB', 'QUARTERBACKS', 10), ('RB', 'RUNNING BACKS', 12), ('WR', 'WIDE RECEIVERS', 12), ('TE', 'TIGHT ENDS', 10)]
SHORT = {'IND': 'Colts', 'MIA': 'Dolphins', 'NE': 'Patriots', 'DET': 'Lions', 'BUF': 'Bills', 'NYJ': 'Jets', 'SF': '49ers', 'DAL': 'Cowboys',
         'LA': 'Rams', 'ARI': 'Cardinals', 'CIN': 'Bengals', 'PIT': 'Steelers', 'CAR': 'Panthers', 'NO': 'Saints', 'HOU': 'Texans',
         'CLE': 'Browns', 'SEA': 'Seahawks', 'LV': 'Raiders', 'KC': 'Chiefs', 'ATL': 'Falcons', 'GB': 'Packers', 'MIN': 'Vikings',
         'TEN': 'Titans', 'JAX': 'Jaguars', 'BAL': 'Ravens', 'LAC': 'Chargers', 'MIA ': 'Dolphins'}

ppr = lambda r: (r.get('pass_yds', 0) / 25 + 4 * r.get('pass_td', 0) - 2 * r.get('int', 0) + r.get('rush_yds', 0) / 10
                 + 6 * r.get('rush_td', 0) + r.get('rec_yds', 0) / 10 + 6 * r.get('rec_td', 0) + r.get('rec', 0))
F = json.load(open(f'{M.ROOT}/data/fantasy.json'))
WK = [r for r in F['games'] if r['wk'] == WEEK and r['game'] not in EXCLUDE]
TOP = {pos: sorted([r for r in WK if r['pos'] == pos], key=lambda r: -ppr(r))[:n] for pos, _, n in POSITIONS}


def where(r):
    _, _, away, home = r['game'].split('_')
    return ('vs ' if r['team'] == home else '@ ') + SHORT.get(r['opp'], r['opp'])


def note(r):
    f = (r.get('flag') or '').lower()
    if 'not practic' in f or 'did not practice' in f: return 'Not practicing'
    if 'limited' in f: return 'Limited in practice'
    return ''


def slide(i, pos, title, rows):
    li = ''.join(f'''<div class="rk"><span class="n">{k + 1}</span><span class="nm"><b>{M.e(r["name"])}</b>
        <small>{r["team"]} {M.e(where(r))}{f' <i>{note(r)}</i>' if note(r) else ''}</small></span><span class="pts">{ppr(r):.1f}</span></div>'''
                 for k, r in enumerate(rows))
    return f'''
<section class="slide rank" style="--pc:{M.POS_COLOR[pos]}">
  <div class="glow"></div>
  {M.brand()}
  <div class="tagrow"><span class="tag">{pos} RANKINGS</span><span class="count">{i} / {len(POSITIONS)}</span></div>
  <div class="ptitle">{title}</div>
  <div class="plist"><div class="phead"><span>Week {WEEK} projection</span><span>PPR pts</span></div>{li}</div>
  <div class="foot"><span class="url">{M.URL}</span><span class="fine">Model projections · Sunday and Monday games</span></div>
</section>'''


def cover():
    box = lambda pos: f'''<div><div class="ch" style="color:{M.POS_COLOR[pos]}">{pos}1</div><div class="li">{M.e(TOP[pos][0]["name"])}</div>
        <div class="li sm">{ppr(TOP[pos][0]):.1f} pts {M.e(where(TOP[pos][0]))}</div></div>'''
    return f'''
<section class="slide cover">
  <div class="glow g1"></div><div class="glow g2"></div>
  {M.brand()}
  <div class="kicker">Fantasy lineup help</div>
  <h2><span class="b">WEEK {WEEK}</span><span class="s">RANKINGS</span></h2>
  <p class="sub">Our model’s top projected players at every position for Sunday and Monday.</p>
  <div class="cols c4">{''.join(box(p) for p, _, _ in POSITIONS)}</div>
  <div class="swipe">Swipe for every position →</div>
  <div class="foot"><span class="url">{M.URL}</span><span class="fine">PPR points · model projections</span></div>
</section>'''


EXTRA_CSS = '''
.rank .glow{background:radial-gradient(circle,var(--pc),transparent 65%)} .rank .tag{background:var(--pc);white-space:nowrap}
.ptitle{margin-top:26px;font-family:'Inter Display';font-weight:900;font-size:96px;letter-spacing:-.035em;line-height:1;color:var(--ink);white-space:nowrap}
.plist{margin-top:30px;background:var(--surface);border:2px solid var(--line);border-radius:28px;padding:8px 28px 6px}
.phead{display:flex;justify-content:space-between;font-size:22px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);padding:12px 0 8px;border-bottom:2px solid var(--line)}
.rk{display:flex;align-items:center;gap:20px;height:73px;border-bottom:2px solid var(--line)}
.rk:last-child{border-bottom:0}
.rk .n{font-family:'Inter Display';font-weight:900;font-size:34px;color:var(--pc);width:44px;text-align:right}
.rk .nm{display:flex;flex-direction:column;gap:5px;min-width:0}
.rk .nm b{font-size:33px;font-weight:800;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;line-height:1.05}
.rk .nm small{font-size:22px;font-weight:600;color:var(--muted);white-space:nowrap}
.rk .nm small i{font-style:normal;font-weight:800;color:var(--accent);margin-left:8px}
.rk .pts{margin-left:auto;font-family:'Inter Display';font-weight:900;font-size:40px;color:var(--ink)}
.cover h2 .b,.cover h2 .s{white-space:nowrap}
.cols.c4{grid-template-columns:1fr 1fr;gap:22px;margin-top:48px}
.cols.c4 .li{font-size:31px;font-weight:800;line-height:1.3}
.cols.c4 .li.sm{font-size:24px;font-weight:600;color:var(--ink-2)}
'''

if __name__ == '__main__':
    from playwright.sync_api import sync_playwright
    CSS = open(os.path.join(OUT, 'slides.css')).read() + EXTRA_CSS
    end = M.end().replace('The full buy low / sell high list, a trade calculator and rest-of-season rankings',
                          f'Every player’s Week {WEEK} projection, rest-of-season rankings and a trade calculator')
    slides = [cover()] + [slide(i + 1, pos, title, TOP[pos]) for i, (pos, title, _) in enumerate(POSITIONS)] + [end]
    open(os.path.join(OUT, 'rankings.html'), 'w').write(f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(slides)}</body></html>')
    names = ['00-cover'] + [f'{i + 1:02d}-{pos.lower()}' for i, (pos, _, _) in enumerate(POSITIONS)] + [f'{len(POSITIONS) + 1:02d}-end']
    d = os.path.join(OUT, f'rankings_wk{WEEK}'); os.makedirs(d, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1080, 'height': 1920}, device_scale_factor=1)
        pg.goto('file://' + os.path.join(OUT, 'rankings.html'))
        pg.evaluate('() => document.fonts.ready')
        print(pg.evaluate('''() => [...document.querySelectorAll('section.slide')].map((s, i) => { const t = s.getBoundingClientRect().top; let m = 0;
            for (const el of s.querySelectorAll('.plist,.swipe,.endbox,.cols,.sub')) m = Math.max(m, el.getBoundingClientRect().bottom - t);
            const clip = [...s.querySelectorAll('.nm b,.ptitle,.tagrow,.nm small')].filter(x => x.scrollWidth > x.clientWidth + 1).map(x => x.textContent.trim().slice(0, 30));
            return i + ':' + Math.round(m) + (clip.length ? ' CLIPPED ' + clip.join('|') : ''); })'''))
        for el, n in zip(pg.query_selector_all('section.slide'), names):
            el.screenshot(path=os.path.join(d, n + '.png'))
        b.close()
    print(names, d)
