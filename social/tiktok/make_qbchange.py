"""'New QB, new value': fantasy winners and losers from quarterback changes. Each slide compares the player's projection for the
week with his usual quarterbacks (projections run without the starting-QB adjustment) against the projection with the new starter.

Needs a second fantasy.json made without the QB adjustment: copy pipeline/ and data/ somewhere, make players.starter_q return None,
run fantasy.py there, and point NOQB at that data/fantasy.json."""
import json, os, sys
import make_slides as M

OUT = os.path.dirname(os.path.abspath(__file__))
WEEK = 10
NOQB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT, 'fantasy_noqb.json')
M.TEAM.update({'SF': 'San Francisco 49ers', 'KC': 'Kansas City Chiefs', 'LV': 'Las Vegas Raiders', 'ARI': 'Arizona Cardinals', 'MIA': 'Miami Dolphins'})

UP = [
    ('Keenan Allen', 'Brock Purdy', 'was Daniel Jones in Indianapolis', 'at Cowboys',
     "The deadline trade moves Allen from Daniel Jones to Brock Purdy, a big step up by the model's QB ratings. San Francisco is thin at "
     "receiver too, with Ricky Pearsall out for the season and Mike Evans banged up."),
    ('Josh Downs', 'Patrick Mahomes', 'was Daniel Jones in Indianapolis', 'at Falcons',
     "Downs averaged 8.3 points a game in Indianapolis. Now he catches passes from Patrick Mahomes, and Kansas City is without "
     "Tyquan Thornton for months. Flex range in deeper leagues."),
]
DOWN = [
    ('Brock Bowers', 'Fernando Mendoza', 'rookie, No. 1 overall pick', 'vs Seahawks',
     "Kirk Cousins was traded to Minnesota, so No. 1 pick Fernando Mendoza takes over in Las Vegas. Bowers is still the TE1, "
     "so keep starting him; just expect fewer monster games."),
    ('Trey McBride', 'Carson Beck', 'rookie, first NFL start', 'vs Rams',
     "Gardner Minshew is out for the season, so third-round rookie Carson Beck makes his first start. McBride has 94 targets "
     "in nine games, and he's still a must-start tight end."),
    ('Caleb Douglas', 'Kyle McCord', 'first NFL start; Willis on IR', 'at Colts',
     "Malik Willis is on IR, so Kyle McCord, a 2025 sixth-round pick, makes his first start. Hold Douglas: "
     "Willis can return for Week 14, right before the fantasy playoffs."),
]

ppr = lambda r: (r.get('pass_yds', 0) / 25 + 4 * r.get('pass_td', 0) - 2 * r.get('int', 0) + r.get('rush_yds', 0) / 10
                 + 6 * r.get('rush_td', 0) + r.get('rec_yds', 0) / 10 + 6 * r.get('rec_td', 0) + r.get('rec', 0))
A = {r['name']: r for r in json.load(open(f'{M.ROOT}/data/fantasy.json'))['games'] if r['wk'] == WEEK}
B = {r['name']: r for r in json.load(open(NOQB))['games'] if r['wk'] == WEEK}


def slide(kind, i, total, name, qb, qb_sub, where, why):
    up = kind == 'up'
    new, old = ppr(A[name]), ppr(B[name])
    first, _, last = name.partition(' ')
    pos = A[name]['pos']
    return f'''
<section class="slide {'buy' if up else 'sell'}">
  <div class="glow"></div>
  {M.brand()}
  <div class="tagrow"><span class="tag">{'QB UPGRADE' if up else 'QB DOWNGRADE'}</span><span class="count">{i} / {total} · {M.e(where)}</span></div>
  <div class="name"><span class="first">{M.e(first)}</span><span class="last fit">{M.e(last)}</span></div>
  <div class="meta"><span class="pos" style="--pc:{M.POS_COLOR[pos]}">{pos}</span>{M.e(M.TEAM[A[name]['team']])}</div>
  <div class="card">
    <div class="nums">
      <div><div class="lab">{'Old QB' if up else 'Usual QB'}</div><div class="big">{old:.1f}</div></div>
      <div class="arrow">→</div>
      <div><div class="lab">New QB</div><div class="big">{new:.1f}</div></div>
      <div class="chg">{new - old:+.1f}<small>Week {WEEK} pts</small></div>
    </div>
    <div class="clab"><span>Fantasy points by week</span><span class="pl"><i></i>Week {WEEK} proj {new:.1f}</span></div>
    {M.chart(name, new, '#3DDC97' if up else '#FF5D8F')}
  </div>
  <div class="key"><b>New QB: {M.e(qb)}</b><span>{M.e(qb_sub)}</span></div>
  <p class="why">{M.e(why)}</p>
  {M.footer()}
</section>'''


def cover():
    li = lambda L: ''.join(f'<div class="li">{M.e(n)}</div>' for n, *_ in L)
    return f'''
<section class="slide cover">
  <div class="glow g1"></div><div class="glow g2"></div>
  {M.brand()}
  <div class="kicker">Week {WEEK} fantasy</div>
  <h2><span class="b">NEW QB,</span><span class="s">NEW VALUE</span></h2>
  <p class="sub">Our projections now follow each team’s starting quarterback. Here’s who gains and who loses this week.</p>
  <div class="cols"><div><div class="ch b">Gains</div>{li(UP)}</div><div><div class="ch s">Loses</div>{li(DOWN)}</div></div>
  <div class="swipe">Swipe for the why →</div>
  {M.footer()}
</section>'''


if __name__ == '__main__':
    from playwright.sync_api import sync_playwright
    CSS = open(os.path.join(OUT, 'slides.css')).read() + '.cover h2 .b,.cover h2 .s{white-space:nowrap} .tag{white-space:nowrap}'
    end = M.end().replace('The full buy low / sell high list, a trade calculator and rest-of-season rankings',
                          'Weekly projections that follow every starting QB, rest-of-season rankings and a trade calculator')
    slides = [cover()] + [slide('up', i + 1, len(UP), *p) for i, p in enumerate(UP)] + \
             [slide('down', i + 1, len(DOWN), *p) for i, p in enumerate(DOWN)] + [end]
    open(os.path.join(OUT, 'qbchange.html'), 'w').write(f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(slides)}</body></html>')
    slug = lambda n: n.lower().replace(' ', '-').replace('.', '')
    names = ['00-cover'] + [f'{i + 1:02d}-up-{slug(n)}' for i, (n, *_) in enumerate(UP)] + \
            [f'{i + 1 + len(UP):02d}-down-{slug(n)}' for i, (n, *_) in enumerate(DOWN)] + [f'{len(UP) + len(DOWN) + 1:02d}-end']
    os.makedirs(os.path.join(OUT, 'qbchange'), exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1080, 'height': 1920}, device_scale_factor=1)
        pg.goto('file://' + os.path.join(OUT, 'qbchange.html'))
        pg.evaluate('''() => document.fonts.ready.then(() => { for (const el of document.querySelectorAll('.fit')) { let s = parseFloat(getComputedStyle(el).fontSize);
            while (el.scrollWidth > el.clientWidth && s > 60) { s -= 2; el.style.fontSize = s + 'px'; } } })''')
        print(pg.evaluate('''() => [...document.querySelectorAll('section.slide')].map((s, i) => { const t = s.getBoundingClientRect().top; let m = 0;
            for (const el of s.querySelectorAll('.why,.swipe,.endbox,.cols,.key')) m = Math.max(m, el.getBoundingClientRect().bottom - t);
            const tr = s.querySelector('.tagrow'); return i + ':' + Math.round(m) + (tr && tr.scrollWidth > tr.clientWidth + 1 ? ' TAGROW OVERFLOW' : ''); })'''))
        for el, n in zip(pg.query_selector_all('section.slide'), names):
            el.screenshot(path=os.path.join(OUT, 'qbchange', n + '.png'))
        b.close()
    print(names)
