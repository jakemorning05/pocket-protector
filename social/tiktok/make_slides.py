"""Buy low / sell high TikTok carousel: 1080x1920 PNG slides in the Pocket Protector style."""
import json, os, html
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
OUT = os.path.dirname(os.path.abspath(__file__))
WEEK = 10
URL = 'Full fantasy rankings: link in bio'

mkt = {r['name']: r for r in json.load(open(os.path.join(OUT, 'mkt.json')))}
W = pd.read_csv(f'{ROOT}/data/stats_player_week_2026.csv', low_memory=False)
W = W[W.season_type == 'REG']
LAST_WEEK = int(W.week.max())

TEAM = {'DEN': 'Denver Broncos', 'TEN': 'Tennessee Titans', 'LAC': 'Los Angeles Chargers', 'PHI': 'Philadelphia Eagles',
        'HOU': 'Houston Texans', 'CIN': 'Cincinnati Bengals', 'BUF': 'Buffalo Bills', 'KC': 'Kansas City Chiefs', 'SEA': 'Seattle Seahawks'}
POS_COLOR = {'QB': '#FF5D8F', 'RB': '#3DDC97', 'WR': '#4DA3FF', 'TE': '#FF9F43'}

BUY = [
    ('Bo Nix', '6.0 yards per pass', 'league average 7.2',
     "Nix is averaging just 6.0 yards per pass attempt, well under the league’s 7.2, and the model expects that to climb: "
     "about 227 passing yards a game the rest of the way, up from 192. He’s already heating up, with 15+ points in three of his last four."),
    ('Cam Ward', '2.4% touchdown rate', 'league average 4.8%',
     "Only 2.4% of Ward’s throws have gone for touchdowns, half the league rate, and gaps that big usually close. "
     "Week 8 showed the upside: 304 yards, two scores and 41 rushing yards for 26 points."),
    ('Justin Herbert', '6 TD, 11 INT', 'on 235 throws',
     "Six touchdowns against 11 interceptions is far below Herbert’s usual level, and the model expects both numbers to even out. "
     "The finger scare checked out: imaging was negative, no fracture. Best as a superflex or 2-QB target."),
    ('Makai Lemon', '8, 9, 9 targets', 'in his last three games',
     "The first-round rookie’s role keeps growing: 8, 9 and 9 targets the last three games, after about 5 a game before that. "
     "He has just one touchdown on 37 catches, and the model expects more as the targets pile up. A cheap flex with room to rise."),
    ('Woody Marks', '15, 19, 18 carries', 'last three games, zero TDs',
     "With David Montgomery out the last three games (groin), Marks has carried 15, 19 and 18 times but hasn’t scored once. "
     "That much work usually turns into touchdowns. The risk: when Montgomery returns, the carries get split, so pay a flex price."),
]
SELL = [
    ('Joe Burrow', '7.8% touchdown rate', 'league average 4.8%',
     "Burrow leads the NFL with 23 touchdown passes, 16 of them in his last four games. That’s 7.8% of his throws, and rates "
     "that high almost always come back down. Still a QB1, so only sell if the offer pays for 25 points a game."),
    ('Josh Allen', '9 rushing TDs', 'on 61 carries, most by any QB',
     "Allen has nine rushing touchdowns in eight games, the most of any quarterback. The model expects about six in his last "
     "eight: still great, just not this pace. He’s elite either way, so sell only for a true RB1 or WR1 back."),
    ('Kenneth Walker III', '4 receiving TDs', 'on 26 catches, most by any RB',
     "Walker has 11 touchdowns in eight games, and four came on just 26 catches, the most receiving scores of any running back. "
     "The workload is real at 23 touches a game, but that receiving-TD rate rarely lasts. See what a contender will pay."),
    ('Jaxon Smith-Njigba', '10.5 yards per target', '1,036 yards in nine games',
     "JSN leads all wide receivers at 25.8 points a game, with 1,036 yards and nine scores. That’s 10.5 yards every time he’s "
     "targeted, a pace even elite receivers rarely keep. Don’t dump him: sell only if someone pays like he’s the WR1 overall."),
    ('Mike Gesicki', '6 TDs on 19 catches', 'tied for most among TEs',
     "Gesicki has six touchdowns on just 19 catches, tied for the most among tight ends. He’s seen three or fewer targets in four "
     "of his seven games, so nearly all his value is scoring. Sell while the TDs make him look like a must-start."),
]

LOGO = ('<svg viewBox="0 0 32 32" aria-hidden="true"><rect x="8" y="3.5" width="3.4" height="12" rx="1.7" fill="#FF5D8F"/>'
        '<path d="M17 15.5V9.5M13.4 9.5h7.2M13.4 9.5V3M20.6 9.5V3" stroke="#3DDC97" stroke-width="2.2" stroke-linecap="round" fill="none"/>'
        '<rect x="22.4" y="5.5" width="3.4" height="10" rx="1.7" fill="#4DA3FF"/>'
        '<path d="M5.5 13.5h21v11.5a4 4 0 0 1-4 4h-13a4 4 0 0 1-4-4z" fill="#FFD23F"/>'
        '<path d="M5.5 13.5h21v3.6h-21z" fill="#191304" opacity="0.16"/></svg>')

e = html.escape


def brand():
    return (f'<div class="brand">{LOGO}<span class="word">Pocket <b>Protector</b></span>'
            f'<span class="wk">WEEK {WEEK}</span></div>')


def footer():
    return f'<div class="foot"><span class="url">{URL}</span><span class="fine">PPR points per game · model projections</span></div>'


def chart(name, proj, color):
    d = W[W.player_display_name == name].groupby('week').fantasy_points_ppr.sum()
    weeks = list(range(1, LAST_WEEK + 1))
    vals = [d.get(w) for w in weeks]
    top = max(max(v for v in vals if v is not None), proj) * 1.06
    cw, ch, pad_b, pad_t = 808, 210, 44, 8
    n = len(weeks); slot = cw / n; bw = slot - 14
    plot_h = ch - pad_b - pad_t
    y = lambda v: pad_t + plot_h * (1 - v / top)
    parts = []
    for i, (w, v) in enumerate(zip(weeks, vals)):
        x = i * slot + (slot - bw) / 2
        if v is None:
            parts.append(f'<text x="{x + bw / 2:.1f}" y="{pad_t + plot_h - 8:.1f}" class="nogame" text-anchor="middle">–</text>')
        else:
            h = max(6, plot_h - (y(v) - pad_t))
            y0 = pad_t + plot_h - h
            r = min(8, bw / 2)
            # rounded top only, square at the baseline
            parts.append(f'<path d="M{x:.1f},{pad_t + plot_h:.1f} V{y0 + r:.1f} Q{x:.1f},{y0:.1f} {x + r:.1f},{y0:.1f} '
                         f'H{x + bw - r:.1f} Q{x + bw:.1f},{y0:.1f} {x + bw:.1f},{y0 + r:.1f} V{pad_t + plot_h:.1f} Z" fill="{color}"/>')
        parts.append(f'<text x="{x + bw / 2:.1f}" y="{ch - 8}" class="wkl" text-anchor="middle">W{w}</text>')
    yp = y(proj)
    parts.append(f'<line x1="0" x2="{cw}" y1="{yp:.1f}" y2="{yp:.1f}" class="projline"/>')
    parts.append(f'<line x1="0" x2="{cw}" y1="{pad_t + plot_h:.1f}" y2="{pad_t + plot_h:.1f}" class="base"/>')
    return f'<svg class="chart" viewBox="0 0 {cw} {ch}" width="{cw}" height="{ch}">{"".join(parts)}</svg>'


def player_slide(kind, i, total, name, key, key_sub, why):
    r = mkt[name]
    buy = kind == 'buy'
    color = '#3DDC97' if buy else '#FF5D8F'
    first, _, last = name.partition(' ')
    chg = r['proj'] - r['act']
    return f'''
<section class="slide {kind}">
  <div class="glow"></div>
  {brand()}
  <div class="tagrow"><span class="tag">{'BUY LOW' if buy else 'SELL HIGH'}</span><span class="count">{i} / {total}</span></div>
  <div class="name"><span class="first">{e(first)}</span><span class="last fit">{e(last)}</span></div>
  <div class="meta"><span class="pos" style="--pc:{POS_COLOR[r['pos']]}">{r['pos']}</span>{e(TEAM[r['team']])}</div>
  <div class="card">
    <div class="nums">
      <div><div class="lab">So far</div><div class="big">{r['act']:.1f}</div></div>
      <div class="arrow">→</div>
      <div><div class="lab">Projected</div><div class="big">{r['proj']:.1f}</div></div>
      <div class="chg">{chg:+.1f}<small>pts/game</small></div>
    </div>
    <div class="clab"><span>Fantasy points by week</span><span class="pl"><i></i>Projected {r['proj']:.1f}</span></div>
    {chart(name, r['proj'], color)}
  </div>
  <div class="key"><b>{e(key)}</b><span>{e(key_sub)}</span></div>
  <p class="why">{e(why)}</p>
  {footer()}
</section>'''


def cover():
    return f'''
<section class="slide cover">
  <div class="glow g1"></div><div class="glow g2"></div>
  {brand()}
  <div class="kicker">Fantasy trade targets</div>
  <h2><span class="b">BUY LOW</span><span class="amp">&amp;</span><span class="s">SELL HIGH</span></h2>
  <p class="sub">5 players our model says are about to score more, and 5 who are about to score less.</p>
  <div class="cols">
    <div><div class="ch b">Buy low</div>{''.join(f'<div class="li">{e(n)}</div>' for n, *_ in BUY)}</div>
    <div><div class="ch s">Sell high</div>{''.join(f'<div class="li">{e(n)}</div>' for n, *_ in SELL)}</div>
  </div>
  <div class="swipe">Swipe for the why →</div>
  {footer()}
</section>'''


def end():
    return f'''
<section class="slide end">
  <div class="glow g1"></div><div class="glow g2"></div>
  {brand()}
  <div class="endbox">
    <div class="logo-big">{LOGO}</div>
    <h3>Pocket <b>Protector</b></h3>
    <p class="lead">The full buy low / sell high list, a trade calculator and rest-of-season rankings, updated three times a week.</p>
    <div class="urlbox">{URL}</div>
    <p class="fine2">Follow for weekly fantasy moves</p>
  </div>
  <p class="disc">Model projections, not guarantees. Points are PPR per game; stats through Week {LAST_WEEK}.</p>
</section>'''


if __name__ == "__main__":
    _missing = [n for n, *_ in BUY + SELL if n not in mkt]
    if _missing: raise SystemExit('No longer on the site\'s buy low / sell high list (rerun node export_buy_sell.js or pick others): ' + ', '.join(_missing))
    CSS = open(os.path.join(OUT, 'slides.css')).read()
    slides = [cover()] + [player_slide('buy', i + 1, len(BUY), *p) for i, p in enumerate(BUY)] + \
             [player_slide('sell', i + 1, len(SELL), *p) for i, p in enumerate(SELL)] + [end()]
    doc = f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(slides)}</body></html>'
    open(os.path.join(OUT, 'slides.html'), 'w').write(doc)

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': 1080, 'height': 1920}, device_scale_factor=1)
        pg.goto('file://' + os.path.join(OUT, 'slides.html'))
        pg.evaluate('''() => document.fonts.ready.then(() => {
            for (const el of document.querySelectorAll('.fit')) {
                let s = parseFloat(getComputedStyle(el).fontSize);
                while (el.scrollWidth > el.clientWidth && s > 60) { s -= 2; el.style.fontSize = s + 'px'; }
            }
        })''')
        names = ['00-cover'] + [f'{i + 1:02d}-buy-{n.lower().replace(" ", "-").replace(".", "")}' for i, (n, *_) in enumerate(BUY)] + \
                [f'{i + 6:02d}-sell-{n.lower().replace(" ", "-").replace(".", "")}' for i, (n, *_) in enumerate(SELL)] + ['11-end']
        os.makedirs(os.path.join(OUT, 'png'), exist_ok=True)
        for el, n in zip(pg.query_selector_all('section.slide'), names):
            el.screenshot(path=os.path.join(OUT, 'png', n + '.png'))
        # overflow check: anything poking past the safe area
        print(pg.evaluate('''() => [...document.querySelectorAll('section.slide')].map((s, i) => {
            const top = s.getBoundingClientRect().top; let maxB = 0, maxR = 0;
            for (const el of s.querySelectorAll('.brand,.tagrow,.name,.meta,.card,.key,.why,.cols,.swipe,.endbox,.sub,h2')) {
                const r = el.getBoundingClientRect(); maxB = Math.max(maxB, r.bottom - top); maxR = Math.max(maxR, r.right); }
            return i + ': bottom ' + Math.round(maxB) + ' right ' + Math.round(maxR); })'''))
        b.close()
    print('done')
