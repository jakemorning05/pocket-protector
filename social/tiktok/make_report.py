"""Weekly model report card for TikTok: grades for last week plus the biggest projection hits and misses.

Projections are re-run with only the data available before that week (same as the backtest), because the site's pre-game numbers
weren't archived before the repo existed. From Week 10 on, the site's own pre-game data/fantasy.json in git history can be used.
Usage: python3 make_report.py [week]"""
import json, os, sys
import pandas as pd
import make_slides as M
sys.path.insert(0, os.path.join(M.ROOT, 'pipeline'))
_cwd = os.getcwd(); os.chdir(os.path.join(M.ROOT, 'pipeline'))
import players as P
os.chdir(_cwd)

OUT = os.path.dirname(os.path.abspath(__file__))
WEEK = int(sys.argv[1]) if len(sys.argv) > 1 else 9
M.TEAM.update({'BUF': 'Buffalo Bills', 'SEA': 'Seattle Seahawks', 'BAL': 'Baltimore Ravens', 'DET': 'Detroit Lions', 'CHI': 'Chicago Bears', 'HOU': 'Houston Texans'})

HITS = [
    ('Josh Allen', '234 yards, 1 TD, 1 INT', 'Week 9 at Minnesota, 15 rushing yards',
     "Allen was averaging 26.8 points, but the model had him well under that at Minnesota. His rushing touchdowns dried up and he finished with 12.9."),
    ('Jadarian Price', '4 catches for 54 yards', 'Week 9 vs Arizona, plus 9 carries',
     "The model projected nearly double Price’s 4.9-point average, and he delivered 11.8, mostly as a receiver."),
    ('Derrick Henry', '17 carries, 57 yards', 'Week 9 vs Jacksonville, no touchdown',
     "The model was below his 17.1-point average, and Baltimore fell behind in a 33-10 loss. Henry finished with 5.6 points."),
]
MISSES = [
    ('Jared Goff', '170 yards, 0 TD, 1 INT', 'Week 9 at Miami',
     "The model liked Goff against Miami. Instead Detroit ran more than it threw in a 19-9 win, and Goff had his worst game of the season."),
    ("D'Andre Swift", '12 carries, 31 yards', 'Week 9 vs Tampa Bay, 1 target, 0 catches',
     "Swift had been averaging 18.8 points, and the model expected about the same. He got 31 yards on the ground and nothing as a receiver."),
    ('C.J. Stroud', '384 yards, 5 TDs', 'Week 9 at the Chargers',
     "The good kind of miss. The model had Stroud at 17.2, about his usual, and he threw five touchdowns in a 44-22 win."),
]

cal = json.load(open(f'{M.ROOT}/data/prop_cal.json'))
calib = lambda s, v: max(0.0, cal[s]['c'] + cal[s]['d'] * v) if v else 0.0
ppr = lambda r: (r.get('pass_yds', 0) / 25 + 4 * r.get('pass_td', 0) - 2 * r.get('int', 0) + r.get('rush_yds', 0) / 10
                 + 6 * r.get('rush_td', 0) + r.get('rec_yds', 0) / 10 + 6 * r.get('rec_td', 0) + r.get('rec', 0))


def rerun(week):
    """Projection for every player who played `week`, using only data from before it; plus his season average to that point."""
    H, lg, opp = P.build_context(week)
    rows = []
    for p in P.W[P.W.week == week].itertuples():
        if p.grp == 'QB' and (p.attempts or 0) < 10: continue
        hist = H[H.player_id == p.player_id]
        if len(hist) < 3: continue
        r = P.project(p.player_id, p.team, p.opponent_team, H, lg, opp, q_new=P.QW.get((p.team0, week)))
        if r is None: continue
        for s in ('pass_yds', 'rush_yds', 'rec_yds'):
            if r.get(s) is not None: r[s] = calib(s, r[s])
        rows.append({'name': p.player_display_name, 'pos': p.grp, 'team': p.team, 'proj': ppr(r), 'act': p.fantasy_points_ppr, 'avg': hist.fantasy_points_ppr.mean()})
    R = pd.DataFrame(rows)
    return R[(R.proj >= 8) | (R.act >= 15)]


R = rerun(WEEK).set_index('name')
mae_m, mae_a = (R.act - R.proj).abs().mean(), (R.act - R.avg).abs().mean()
S = json.load(open(f'{M.ROOT}/data/site_data.json'))
G = [g for g in S['games'] if g['wk'] == WEEK and g['hs'] is not None and g['hs'] != g['as']]
gw = sum((g['p'] >= 0.5) == (g['hs'] > g['as']) for g in G)
grade = lambda x: 'A+' if x >= .93 else 'A' if x >= .85 else 'B' if x >= .72 else 'C' if x >= .6 else 'D'
pgrade = 'A' if mae_m < mae_a * 0.9 else 'B' if mae_m < mae_a * 0.97 else 'C' if mae_m < mae_a * 1.03 else 'D'


def slide(kind, i, total, name, key, sub, why):
    r = R.loc[name]
    hit = kind == 'hit'
    first, _, last = name.partition(' ')
    pos = r.pos
    return f'''
<section class="slide {'buy' if hit else 'sell'}">
  <div class="glow"></div>
  {M.brand().replace(f'WEEK {M.WEEK}', f'WEEK {WEEK} RECAP')}
  <div class="tagrow"><span class="tag">{'HIT' if hit else 'MISS'}</span><span class="count">{i} / {total}</span></div>
  <div class="name"><span class="first">{M.e(first)}</span><span class="last fit">{M.e(last)}</span></div>
  <div class="meta"><span class="pos" style="--pc:{M.POS_COLOR[pos]}">{pos}</span>{M.e(M.TEAM[r.team])}</div>
  <div class="card">
    <div class="nums">
      <div><div class="lab">Projected</div><div class="big">{r.proj:.1f}</div></div>
      <div class="arrow">→</div>
      <div><div class="lab">Actual</div><div class="big">{r.act:.1f}</div></div>
      <div class="chg">{r.avg:.1f}<small>season avg</small></div>
    </div>
    <div class="clab"><span>Fantasy points by week</span><span class="pl"><i></i>Week {WEEK} proj {r.proj:.1f}</span></div>
    {chart(name, r.proj, '#3DDC97' if hit else '#FF5D8F')}
  </div>
  <div class="key"><b>{M.e(key)}</b><span>{M.e(sub)}</span></div>
  <p class="why">{M.e(why)}</p>
  <div class="foot"><span class="url">Full fantasy rankings: link in bio</span><span class="fine">PPR · Week {WEEK} projection re-run with only data through Week {WEEK - 1}</span></div>
</section>'''


def chart(name, proj, color):
    """The usual weekly bars, limited to weeks through the graded week."""
    keep = M.LAST_WEEK
    M.LAST_WEEK = WEEK
    try: return M.chart(name, proj, color)
    finally: M.LAST_WEEK = keep


def cover():
    tile = lambda g, t, s, c: f'<div class="gt"><div class="g" style="color:{c}">{g}</div><div><div class="gt-t">{t}</div><div class="gt-s">{s}</div></div></div>'
    better = sum(1 for w in range(4, WEEK + 1) if WEEK_MAE[w][0] < WEEK_MAE[w][1])
    return f'''
<section class="slide cover">
  <div class="glow g1"></div><div class="glow g2"></div>
  {M.brand().replace(f'WEEK {M.WEEK}', f'WEEK {WEEK} RECAP')}
  <div class="kicker">We grade ourselves every week</div>
  <h2><span class="b">MODEL</span><span class="s">REPORT CARD</span></h2>
  <div class="grades">
    {tile(grade(gw / len(G)), 'Game winners', f'{gw} of {len(G)} right', 'var(--mint)')}
    {tile(pgrade, 'Fantasy projections', f'Missed by {mae_m:.1f} pts on average. Using each player’s season average would have missed by {mae_a:.1f}.', 'var(--accent)')}
  </div>
  <p class="sub sm">Week {WEEK} was the projections’ worst week. Since Week 4 they’ve beaten season averages in {better} of {WEEK - 3} weeks.</p>
  <div class="swipe">Swipe for the hits and misses →</div>
  <div class="foot"><span class="url">Full fantasy rankings: link in bio</span><span class="fine">PPR · projections re-run with only data available before each week</span></div>
</section>'''


def mae_by_week():
    out = {}
    for w in range(4, WEEK + 1):
        x = R if w == WEEK else rerun(w)
        out[w] = ((x.act - x.proj).abs().mean(), (x.act - x.avg).abs().mean())
    return out


EXTRA_CSS = '''
.cover h2 .b,.cover h2 .s{white-space:nowrap}
.grades{display:flex;flex-direction:column;gap:22px;margin-top:48px}
.gt{display:flex;align-items:center;gap:30px;background:var(--surface);border:2px solid var(--line);border-radius:28px;padding:26px 30px}
.gt .g{font-family:'Inter Display';font-weight:900;font-size:120px;line-height:1;width:150px;text-align:center}
.gt-t{font-family:'Inter Display';font-weight:800;font-size:40px} .gt-s{font-size:27px;color:var(--ink-2);font-weight:600;margin-top:6px;line-height:1.35}
.sub.sm{font-size:32px;margin-top:36px}
'''

if __name__ == '__main__':
    from playwright.sync_api import sync_playwright
    WEEK_MAE = mae_by_week()
    print({w: tuple(round(v, 2) for v in t) for w, t in WEEK_MAE.items()}, 'games', gw, len(G), 'grades', grade(gw / len(G)), pgrade)
    CSS = open(os.path.join(OUT, 'slides.css')).read() + EXTRA_CSS
    end = M.end().replace('The full buy low / sell high list, a trade calculator and rest-of-season rankings',
                          'Weekly projections, rest-of-season rankings and a trade calculator, graded in public').replace(f'WEEK {M.WEEK}<', f'WEEK {WEEK} RECAP<')
    slides = [cover()] + [slide('hit', i + 1, len(HITS), *h) for i, h in enumerate(HITS)] + \
             [slide('miss', i + 1, len(MISSES), *m) for i, m in enumerate(MISSES)] + [end]
    open(os.path.join(OUT, 'report.html'), 'w').write(f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(slides)}</body></html>')
    slug = lambda n: n.lower().replace(' ', '-').replace('.', '').replace("'", '')
    names = ['00-cover'] + [f'{i + 1:02d}-hit-{slug(n)}' for i, (n, *_) in enumerate(HITS)] + \
            [f'{i + 1 + len(HITS):02d}-miss-{slug(n)}' for i, (n, *_) in enumerate(MISSES)] + [f'{len(HITS) + len(MISSES) + 1:02d}-end']
    d = os.path.join(OUT, f'report_wk{WEEK}'); os.makedirs(d, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1080, 'height': 1920}, device_scale_factor=1)
        pg.goto('file://' + os.path.join(OUT, 'report.html'))
        pg.evaluate('''() => document.fonts.ready.then(() => { for (const el of document.querySelectorAll('.fit')) { let s = parseFloat(getComputedStyle(el).fontSize);
            while (el.scrollWidth > el.clientWidth && s > 60) { s -= 2; el.style.fontSize = s + 'px'; } } })''')
        print(pg.evaluate('''() => [...document.querySelectorAll('section.slide')].map((s, i) => { const t = s.getBoundingClientRect().top; let m = 0;
            for (const el of s.querySelectorAll('.why,.swipe,.endbox,.grades,.sub,.key')) m = Math.max(m, el.getBoundingClientRect().bottom - t); return i + ':' + Math.round(m); })'''))
        for el, n in zip(pg.query_selector_all('section.slide'), names):
            el.screenshot(path=os.path.join(d, n + '.png'))
        b.close()
    print(names)
