"""Week start 'em / sit 'em carousel. Numbers: model projections for the week (data/fantasy.json) against each player's season
average, and fantasy points the opponent allows to the position (from the weekly stats). Same look as the other slideshows."""
import json, os
import pandas as pd
import make_slides as M

OUT = os.path.dirname(os.path.abspath(__file__))
ROOT = M.ROOT
WEEK = 10
NICK = {'IND': 'Colts', 'HOU': 'Texans', 'MIA': 'Dolphins', 'GB': 'Packers', 'KC': 'Chiefs', 'SEA': 'Seahawks'}
HOME = {'Ollie Gordon II': False, 'KC Concepcion': True, 'Tyler Warren': True, 'Kirk Cousins': False, 'Drake London': True, 'Tre Tucker': True}
M.TEAM.update({'MIA': 'Miami Dolphins', 'CLE': 'Cleveland Browns', 'IND': 'Indianapolis Colts', 'MIN': 'Minnesota Vikings',
               'ATL': 'Atlanta Falcons', 'LV': 'Las Vegas Raiders'})

START = [
    ('Ollie Gordon II',
     "The model projects 16 carries for Gordon at Indianapolis, which gives up the 6th-most fantasy points to running backs. "
     "That makes him an RB2 this week, even with Kyle McCord making his first start at quarterback."),
    ('KC Concepcion',
     "Concepcion has 23.2 and 18.8 points in two of his last three games, and Deshaun Watson is cleared to return. "
     "Houston gives up the 5th-most fantasy points to receivers. A strong flex play this week."),
    ('Tyler Warren',
     "Warren has seen 7 or more targets in five of his seven games, and Miami gives up the 4th-most fantasy points to tight ends. "
     "After two quiet weeks, the model has him back as a top-5 tight end."),
]
SIT = [
    ('Kirk Cousins',
     "Cousins averaged 19.1 points in Las Vegas, but he was traded to Minnesota on Tuesday and starts Sunday at Green Bay with less "
     "than a week to learn the offense. The model has him as just the QB16."),
    ('Drake London',
     "Kansas City gives up the 2nd-fewest fantasy points to receivers, and London has been up and down: 1.8 points in Week 8 after "
     "19.6 the week before. Still a borderline WR2, so sit him only if you have a comparable flex."),
    ('Tre Tucker',
     "Seattle gives up the fewest fantasy points to receivers in the league, and rookie Fernando Mendoza is now his quarterback. "
     "Tucker has been boom or bust: back-to-back 20-point games, then 0 and 9.5."),
]

ppr = lambda r: (r.get('pass_yds', 0) / 25 + 4 * r.get('pass_td', 0) - 2 * r.get('int', 0) + r.get('rush_yds', 0) / 10
                 + 6 * r.get('rush_td', 0) + r.get('rec_yds', 0) / 10 + 6 * r.get('rec_td', 0) + r.get('rec', 0))
FAN = json.load(open(f'{ROOT}/data/fantasy.json'))
WK = [r for r in FAN['games'] if r['wk'] == WEEK]
for r in WK: r['pts'] = ppr(r)
RANK = {}
for pos in ('QB', 'RB', 'WR', 'TE'):
    for i, r in enumerate(sorted([r for r in WK if r['pos'] == pos], key=lambda r: -r['pts'])): RANK[r['id']] = i + 1
W = M.W
SEASON = W.groupby('player_id').fantasy_points_ppr.mean()   # by id: two players can share a name
pp = W[W.position.isin(['QB', 'RB', 'WR', 'TE'])].groupby(['opponent_team', 'position', 'week']).fantasy_points_ppr.sum().reset_index()
FPA = pp.groupby(['opponent_team', 'position']).fantasy_points_ppr.mean().unstack()
FRK = FPA.rank(ascending=False)
ORD = lambda n: {1: '', 2: '2nd-', 3: '3rd-'}.get(n, f'{n}th-')
POSW = {'QB': 'QBs', 'RB': 'RBs', 'WR': 'WRs', 'TE': 'TEs'}


def slide(kind, i, total, name, why):
    r = next(x for x in WK if x['name'] == name)
    start = kind == 'start'
    color = '#3DDC97' if start else '#FF5D8F'
    first, _, last = name.partition(' ')
    opp, pos = r['opp'], r['pos']
    a, k = FPA.loc[opp, pos], int(FRK.loc[opp, pos])
    rank_txt = f'{ORD(k)}most' if k <= 16 else f'{ORD(33 - k)}fewest'
    where = ('vs ' if HOME[name] else 'at ') + NICK[opp]
    return f'''
<section class="slide {'buy' if start else 'sell'}">
  <div class="glow"></div>
  {M.brand()}
  <div class="tagrow"><span class="tag">{'START' if start else 'SIT'}</span><span class="count">{i} / {total} · Week {WEEK} {M.e(where)}</span></div>
  <div class="name"><span class="first">{M.e(first)}</span><span class="last fit">{M.e(last)}</span></div>
  <div class="meta"><span class="pos" style="--pc:{M.POS_COLOR[pos]}">{pos}</span>{M.e(M.TEAM[r['team']])}</div>
  <div class="card">
    <div class="nums">
      <div><div class="lab">Week {WEEK}</div><div class="big">{r['pts']:.1f}</div></div>
      <div class="arrow" style="visibility:hidden">→</div>
      <div><div class="lab">Season avg</div><div class="big">{SEASON[r['id']]:.1f}</div></div>
      <div class="chg">{pos}{RANK[r['id']]}<small>this week</small></div>
    </div>
    <div class="clab"><span>Fantasy points by week</span><span class="pl"><i></i>Week {WEEK} proj {r['pts']:.1f}</span></div>
    {M.chart(name, r['pts'], color)}
  </div>
  <div class="key"><b>{NICK[opp]} allow {a:.1f} to {POSW[pos]}</b><span>PPR points a game, the {rank_txt} in the NFL</span></div>
  <p class="why">{M.e(why)}</p>
  {M.footer()}
</section>'''


def cover():
    li = lambda L: ''.join(f'<div class="li">{M.e(n)}</div>' for n, _ in L)
    return f'''
<section class="slide cover">
  <div class="glow g1"></div><div class="glow g2"></div>
  {M.brand()}
  <div class="kicker">Week {WEEK} lineup help</div>
  <h2><span class="b">START ’EM</span><span class="amp">&amp;</span><span class="s">SIT ’EM</span></h2>
  <p class="sub">Players our model projects well above or below their usual numbers this week, and the matchups behind it.</p>
  <div class="cols"><div><div class="ch b">Start</div>{li(START)}</div><div><div class="ch s">Sit</div>{li(SIT)}</div></div>
  <div class="swipe">Swipe for the why →</div>
  {M.footer()}
</section>'''


def end():
    return M.end().replace('The full buy low / sell high list, a trade calculator and rest-of-season rankings',
                           'Every player’s Week ' + str(WEEK) + ' projection, rest-of-season rankings and a trade calculator')


if __name__ == '__main__':
    from playwright.sync_api import sync_playwright
    CSS = open(os.path.join(OUT, 'slides.css')).read()
    slides = [cover()] + [slide('start', i + 1, len(START), *p) for i, p in enumerate(START)] + \
             [slide('sit', i + 1, len(SIT), *p) for i, p in enumerate(SIT)] + [end()]
    open(os.path.join(OUT, 'startsit.html'), 'w').write(f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(slides)}</body></html>')
    slug = lambda n: n.lower().replace(' ', '-').replace('.', '')
    names = ['00-cover'] + [f'{i + 1:02d}-start-{slug(n)}' for i, (n, _) in enumerate(START)] + \
            [f'{i + 1 + len(START):02d}-sit-{slug(n)}' for i, (n, _) in enumerate(SIT)] + [f'{len(START) + len(SIT) + 1:02d}-end']
    os.makedirs(os.path.join(OUT, 'startsit'), exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1080, 'height': 1920}, device_scale_factor=1)
        pg.goto('file://' + os.path.join(OUT, 'startsit.html'))
        pg.evaluate('''() => document.fonts.ready.then(() => { for (const el of document.querySelectorAll('.fit')) { let s = parseFloat(getComputedStyle(el).fontSize);
            while (el.scrollWidth > el.clientWidth && s > 60) { s -= 2; el.style.fontSize = s + 'px'; } } })''')
        print(pg.evaluate('''() => [...document.querySelectorAll('section.slide')].map((s, i) => { const t = s.getBoundingClientRect().top; let m = 0;
            for (const el of s.querySelectorAll('.why,.swipe,.endbox,.cols,.key,.tagrow')) m = Math.max(m, el.getBoundingClientRect().bottom - t);
            const tr = s.querySelector('.tagrow'); return i + ':' + Math.round(m) + (tr && tr.scrollWidth > tr.clientWidth ? ' TAGROW OVERFLOW' : ''); })'''))
        for el, n in zip(pg.query_selector_all('section.slide'), names):
            el.screenshot(path=os.path.join(OUT, 'startsit', n + '.png'))
        b.close()
    print(names)
