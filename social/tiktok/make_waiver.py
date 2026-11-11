"""Week 10 waiver wire TikTok carousel, same style as the buy low / sell high slides."""
import json, os, html
import pandas as pd
from make_slides import LOGO, POS_COLOR, chart, brand, URL, W, LAST_WEEK, e  # reuses the chart and brand bar

OUT = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(OUT, 'waiv.json')))
R = {r['name']: r for r in D['ros']}
TEAM = {'HOU': 'Houston Texans', 'NO': 'New Orleans Saints', 'MIA': 'Miami Dolphins', 'CAR': 'Carolina Panthers', 'NE': 'New England Patriots', 'NYJ': 'New York Jets'}
NICK = {'CLE': 'Browns', 'CAR': 'Panthers', 'IND': 'Colts', 'NO': 'Saints', 'DET': 'Lions', 'BUF': 'Bills'}
HOME = {'Tank Dell': False, 'Audric Estimé': True, 'Caleb Douglas': False, 'Darren Waller': False, 'DeMario Douglas': False, 'Geno Smith': True}

# name, Yahoo rostered %, verdict, key stat, key sub, why
PICKS = [
    ('Tank Dell', 13, 'Add now', '9 targets, 105 yards, 1 TD', 'Week 9, his second game back',
     "In his second game back from injury, Dell led Houston with 9 targets and turned them into 105 yards and a touchdown. "
     "The model has him at 10.9 points a game the rest of the way, the WR29, which is starter level in a 12-team league."),
    ('Audric Estimé', 4, 'Add now', '15 of 22 Saints RB carries', 'Week 9, plus a touchdown',
     "New Orleans released Kendre Miller and has Travis Etienne Jr. on IR, and Estimé took 15 of the team’s 22 running back carries in Week 9. "
     "The model projects 10.2 points a game the rest of the way, the RB30. Alvin Kamara still takes some of the work."),
    ('Caleb Douglas', 29, 'Add now', '3 → 6 → 8 targets', 'last three games, team high in Week 9',
     "The rookie’s targets have climbed three games in a row, ending with a team-high 8 against Detroit. "
     "The model has him at 10.7 points a game the rest of the way, the WR31, and 10.9 at Indianapolis this week."),
    ('Darren Waller', 7, 'TE streamer', '8 catches, 90 yards, 1 TD', 'on 10 targets in Week 9',
     "Waller led Carolina in targets, catches and yards against Denver for 23 points. He’d seen just 2 targets in each of the "
     "three games before, so treat him as a streamer: the model has him as the TE14 the rest of the way."),
    ('DeMario Douglas', 46, 'Flex depth', '4 TDs in his last 5 games', 'plus 102 yards in Week 9',
     "Douglas has scored four times in his last five games and just posted 102 yards against Green Bay. "
     "The model has him at 10.2 points a game the rest of the way, a solid flex. He’s on 46% of Yahoo rosters, so check fast."),
    ('Geno Smith', 18, 'Bye-week QB', '3 games of 18+ points', 'this season',
     "With four teams on bye, Geno is a fill-in: the model projects 15.5 points at home against Buffalo and 15.9 a game the rest of the way, the QB19. "
     "Check Garrett Wilson’s concussion status before you start him."),
]


def pick_slide(i, name, pct, verdict, key, key_sub, why):
    r = R[name]; w = r['wk']
    first, _, last = name.partition(' ')
    opp = ('vs ' if HOME[name] else 'at ') + NICK[w['opp']]
    if name == 'DeMario Douglas': opp = 'vs Lions in Germany'
    return f'''
<section class="slide waiv">
  <div class="glow"></div>
  {brand()}
  <div class="tagrow"><span class="tag">#{i} PICKUP</span><span class="count">{e(verdict)}</span><span class="rost"><b>{pct}%</b> rostered</span></div>
  <div class="name"><span class="first">{e(first)}</span><span class="last fit">{e(last)}</span></div>
  <div class="meta"><span class="pos" style="--pc:{POS_COLOR[r['pos']]}">{r['pos']}</span>{e(TEAM[r['team']])}</div>
  <div class="card">
    <div class="nums">
      <div><div class="lab">Week 10</div><div class="big">{w['pts']:.1f}</div></div>
      <div class="arrow" style="visibility:hidden">→</div>
      <div><div class="lab">Rest of season</div><div class="big">{r['pg']:.1f}</div></div>
      <div class="chg">{r['pos']}{r['rk']}<small>rest of season</small></div>
    </div>
    <div class="clab"><span>Fantasy points by week</span><span class="pl"><i></i>Projected {r['pg']:.1f}</span></div>
    {chart(name, r['pg'], '#FFD23F')}
  </div>
  <div class="key"><b>{e(key)}</b><span>{e(key_sub)} · Week 10 {e(opp)}</span></div>
  <p class="why">{e(why)}</p>
  <div class="foot"><span class="url">{URL}</span><span class="fine">PPR projections · rostered % from Yahoo, Nov. 9</span></div>
</section>'''


def cover():
    rows = ''.join(f'<div class="wl"><span class="n">{i}</span><span class="p" style="--pc:{POS_COLOR[R[n]["pos"]]}">{R[n]["pos"]}</span>{e(n)}<span class="r">{pct}%</span></div>'
                   for i, (n, pct, *_) in enumerate(PICKS, 1))
    return f'''
<section class="slide cover waiv">
  <div class="glow g1" style="background:radial-gradient(circle,var(--accent),transparent 65%)"></div>
  {brand()}
  <div class="kicker">Week 10 fantasy football</div>
  <h2><span>TOP 6</span><span class="y">WAIVER</span><span class="y">PICKUPS</span></h2>
  <p class="sub">Players our model projects like starters who are still on most waiver wires.</p>
  <div class="wlist">{rows}</div>
  <div class="swipe">Swipe for the why →</div>
  <div class="foot"><span class="url">{URL}</span><span class="fine">% rostered in Yahoo leagues, Nov. 9</span></div>
</section>'''


def end():
    return f'''
<section class="slide end waiv">
  <div class="glow g1" style="background:radial-gradient(circle,var(--accent),transparent 65%)"></div>
  {brand()}
  <div class="endbox">
    <div class="logo-big">{LOGO}</div>
    <h3>Pocket <b>Protector</b></h3>
    <p class="lead">Weekly rankings, usage risers, RB handcuffs and a trade calculator, updated three times a week.</p>
    <div class="urlbox">{URL}</div>
    <p class="fine2">Follow for weekly fantasy moves</p>
  </div>
  <p class="disc">Model projections, not guarantees. PPR scoring; stats through Week {LAST_WEEK}. Rostered % from Yahoo on Nov. 9 and changing fast.</p>
</section>'''


CSS = open(os.path.join(OUT, 'slides.css')).read()
slides = [cover()] + [pick_slide(i, *p) for i, p in enumerate(PICKS, 1)] + [end()]
open(os.path.join(OUT, 'waiver.html'), 'w').write(f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(slides)}</body></html>')

from playwright.sync_api import sync_playwright
names = ['00-cover'] + [f'{i:02d}-{n.lower().replace(" ", "-").replace("é", "e")}' for i, (n, *_) in enumerate(PICKS, 1)] + [f'{len(PICKS) + 1:02d}-end']
os.makedirs(os.path.join(OUT, 'waiver'), exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1080, 'height': 1920}, device_scale_factor=1)
    pg.goto('file://' + os.path.join(OUT, 'waiver.html'))
    pg.evaluate('''() => document.fonts.ready.then(() => { for (const el of document.querySelectorAll('.fit')) { let s = parseFloat(getComputedStyle(el).fontSize);
        while (el.scrollWidth > el.clientWidth && s > 60) { s -= 2; el.style.fontSize = s + 'px'; } } })''')
    print(pg.evaluate('''() => [...document.querySelectorAll('section.slide')].map((s, i) => { const t = s.getBoundingClientRect().top; let m = 0;
        for (const el of s.querySelectorAll('.why,.swipe,.endbox,.wlist,.key')) m = Math.max(m, el.getBoundingClientRect().bottom - t); return i + ':' + Math.round(m); })'''))
    for el, n in zip(pg.query_selector_all('section.slide'), names):
        el.screenshot(path=os.path.join(OUT, 'waiver', n + '.png'))
    b.close()
print(names)
