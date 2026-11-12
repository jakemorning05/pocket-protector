"""Fantasy playoff schedules (Weeks 15-17): easiest and toughest matchups for startable players, by how many PPR points each
defense has allowed to the position so far this season. One player per slide."""
import json, os
import pandas as pd
import make_slides as M

OUT = os.path.dirname(os.path.abspath(__file__))
WEEKS = (15, 16, 17)
NICK = {'ARI': 'Cardinals', 'ATL': 'Falcons', 'BAL': 'Ravens', 'BUF': 'Bills', 'CAR': 'Panthers', 'CHI': 'Bears', 'CIN': 'Bengals', 'CLE': 'Browns',
        'DAL': 'Cowboys', 'DEN': 'Broncos', 'DET': 'Lions', 'GB': 'Packers', 'HOU': 'Texans', 'IND': 'Colts', 'JAX': 'Jaguars', 'KC': 'Chiefs',
        'LA': 'Rams', 'LAC': 'Chargers', 'LV': 'Raiders', 'MIA': 'Dolphins', 'MIN': 'Vikings', 'NE': 'Patriots', 'NO': 'Saints', 'NYG': 'Giants',
        'NYJ': 'Jets', 'PHI': 'Eagles', 'PIT': 'Steelers', 'SEA': 'Seahawks', 'SF': '49ers', 'TB': 'Buccaneers', 'TEN': 'Titans', 'WAS': 'Commanders'}
M.TEAM.update({'CIN': 'Cincinnati Bengals', 'TB': 'Tampa Bay Buccaneers', 'MIN': 'Minnesota Vikings', 'DAL': 'Dallas Cowboys',
               'CAR': 'Carolina Panthers', 'WAS': 'Washington Commanders'})

EASY = [
    ('Chase Brown', "Brown’s playoff run starts against two of the most generous run defenses in the league. He also has just one touchdown "
                    "on 142 touches this season, so this could be when his luck turns."),
    ('Bucky Irving', "Irving opens the playoffs against New Orleans, which gives up the most running back points in the league, then visits "
                     "Atlanta. Week 17 against the Rams is tougher, but two great matchups out of three is a strong path."),
    ('T.J. Hockenson', "No startable tight end has an easier path: Detroit gives up the most tight end points and Washington the 3rd-most. "
                       "With Kirk Cousins now his quarterback, he’s a cheap trade target who could swing a playoff week."),
]
TOUGH = [
    ('Javonte Williams', "Dallas faces three of the stingiest run defenses in the playoffs. Keep him, since he’s still an RB1, but plan "
                         "for smaller playoff scores and see what a contender would pay."),
    ('Tetairoa McMillan', "McMillan’s playoff run ends against Seattle, which gives up the fewest receiver points in the league, after a "
                          "trip to Pittsburgh. Still a starter, but one to sell if a WR1-level return is on the table."),
    ('Jayden Daniels', "Week 16 at Minnesota is the toughest quarterback matchup in football: the Vikings give up the fewest QB points. "
                       "In superflex, line up a backup plan for that week."),
]

S = json.load(open(f'{M.ROOT}/data/site_data.json'))
F = json.load(open(f'{M.ROOT}/data/fantasy.json'))
W = M.W
pp = W[W.position.isin(['QB', 'RB', 'WR', 'TE'])].groupby(['opponent_team', 'position', 'week']).fantasy_points_ppr.sum().reset_index()
FPA = pp.groupby(['opponent_team', 'position']).fantasy_points_ppr.mean().unstack()
FRK = FPA.rank(ascending=False).astype(int)
LG = FPA.mean()
SCHED = {}
for g in S['games']:
    if g['wk'] in WEEKS:
        SCHED.setdefault(g['a'], []).append((g['wk'], g['h'], 'at')); SCHED.setdefault(g['h'], []).append((g['wk'], g['a'], 'vs'))
ppr = lambda r: (r.get('pass_yds', 0) / 25 + 4 * r.get('pass_td', 0) - 2 * r.get('int', 0) + r.get('rush_yds', 0) / 10
                 + 6 * r.get('rush_td', 0) + r.get('rec_yds', 0) / 10 + 6 * r.get('rec_td', 0) + r.get('rec', 0))
BASE = {}
for r in F['games']: BASE.setdefault(r['name'], r)
ROS = {BASE_n: None for BASE_n in BASE}
rows = []
for i, t in F['ros'].items():
    r = next((x for x in F['games'] if x['id'] == i), None)
    if r and t['n']: rows.append((r['name'], r['pos'], ppr(t) / t['n']))
RR = pd.DataFrame(rows, columns=['name', 'pos', 'pg']); RR['rk'] = RR.groupby('pos').pg.rank(ascending=False).astype(int); RR = RR.set_index('name')
POSW = {'QB': 'QBs', 'RB': 'RBs', 'WR': 'WRs', 'TE': 'TEs'}
ORD = lambda n: {1: '1st', 2: '2nd', 3: '3rd'}.get(n, f'{n}th') if n not in (21, 22, 23) else {21: '21st', 22: '22nd', 23: '23rd'}[n]
RANKTXT = lambda k: ('most' if k == 1 else f'{ORD(k)}-most') if k <= 16 else ('fewest' if k == 32 else f'{ORD(33 - k)}-fewest')


def slide(kind, i, total, name, why):
    easy = kind == 'easy'
    r = BASE[name]; pos = r['pos']; team = r['team']
    games = sorted(SCHED[team])
    avg = sum(FPA.loc[o, pos] for _, o, _ in games) / 3
    first, _, last = name.partition(' ')
    mrows = ''.join(f'''<div class="mu"><span class="w">Wk {w}</span><span class="o">{h} {NICK[o]}</span>
        <span class="a">{FPA.loc[o, pos]:.1f}</span><span class="r {('good' if FRK.loc[o, pos] <= 10 else 'bad' if FRK.loc[o, pos] >= 23 else '')}">{RANKTXT(FRK.loc[o, pos])}</span></div>'''
                    for w, o, h in games)
    return f'''
<section class="slide {'buy' if easy else 'sell'}">
  <div class="glow"></div>
  {M.brand().replace(f'WEEK {M.WEEK}', 'WEEKS 15–17')}
  <div class="tagrow"><span class="tag">{'EASY PLAYOFFS' if easy else 'TOUGH PLAYOFFS'}</span><span class="count">{i} / {total}</span></div>
  <div class="name"><span class="first">{M.e(first)}</span><span class="last fit">{M.e(last)}</span></div>
  <div class="meta"><span class="pos" style="--pc:{M.POS_COLOR[pos]}">{pos}</span>{M.e(M.TEAM[team])}</div>
  <div class="card">
    <div class="nums">
      <div><div class="lab">Opponents allow</div><div class="big">{avg:.1f}</div></div>
      <div class="arrow" style="font-size:34px;padding-bottom:22px">vs</div>
      <div><div class="lab">League avg</div><div class="big" style="color:var(--muted)">{LG[pos]:.1f}</div></div>
      <div class="chg">{avg - LG[pos]:+.1f}<small>pts to {POSW[pos]}</small></div>
    </div>
    <div class="clab"><span>Fantasy playoff matchups</span><span class="pl" style="font-size:22px;color:var(--muted)">pts allowed to {POSW[pos]} / game</span></div>
    <div class="mus">{mrows}</div>
  </div>
  <div class="key"><b>{RR.loc[name].pg:.1f} pts a game the rest of the way</b><span>{pos}{RR.loc[name].rk} in the model’s rest-of-season rankings</span></div>
  <p class="why">{M.e(why)}</p>
  <div class="foot"><span class="url">Full fantasy rankings: link in bio</span><span class="fine">PPR · points each defense has allowed so far this season</span></div>
</section>'''


def cover():
    li = lambda L: ''.join(f'<div class="li">{M.e(n)}</div>' for n, _ in L)
    return f'''
<section class="slide cover">
  <div class="glow g1"></div><div class="glow g2"></div>
  {M.brand().replace(f'WEEK {M.WEEK}', 'WEEKS 15–17')}
  <div class="kicker">Fantasy playoffs · Weeks 15–17</div>
  <h2><span class="b">PLAYOFF</span><span class="s">SCHEDULES</span></h2>
  <p class="sub">Trade for the easiest playoff matchups before your deadline, and know which stars face the toughest.</p>
  <div class="cols"><div><div class="ch b">Easy</div>{li(EASY)}</div><div><div class="ch s">Tough</div>{li(TOUGH)}</div></div>
  <div class="swipe">Swipe for the matchups →</div>
  {M.footer()}
</section>'''


EXTRA_CSS = '''
.cover h2 .b,.cover h2 .s{white-space:nowrap} .tag{white-space:nowrap}
.mus{margin-top:8px;padding:0 10px}
.mu{display:grid;grid-template-columns:110px 1fr 100px 220px;align-items:center;height:76px;border-top:2px solid var(--line);font-size:32px;font-weight:600}
.mu .w{color:var(--muted);font-size:26px;font-weight:700} .mu .o{color:var(--ink)} .mu .a{font-family:'Inter Display';font-weight:800;text-align:right}
.mu .r{text-align:right;font-size:24px;font-weight:700;color:var(--muted)} .mu .r.good{color:var(--mint)} .mu .r.bad{color:var(--pink)}
'''

if __name__ == '__main__':
    from playwright.sync_api import sync_playwright
    CSS = open(os.path.join(OUT, 'slides.css')).read() + EXTRA_CSS
    end = M.end().replace('The full buy low / sell high list, a trade calculator and rest-of-season rankings',
                          'Rest-of-season rankings, every playoff matchup and a trade calculator').replace(f'WEEK {M.WEEK}<', 'WEEKS 15–17<')
    slides = [cover()] + [slide('easy', i + 1, len(EASY), *p) for i, p in enumerate(EASY)] + \
             [slide('tough', i + 1, len(TOUGH), *p) for i, p in enumerate(TOUGH)] + [end]
    open(os.path.join(OUT, 'playoffs.html'), 'w').write(f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(slides)}</body></html>')
    slug = lambda n: n.lower().replace(' ', '-').replace('.', '')
    names = ['00-cover'] + [f'{i + 1:02d}-easy-{slug(n)}' for i, (n, _) in enumerate(EASY)] + \
            [f'{i + 1 + len(EASY):02d}-tough-{slug(n)}' for i, (n, _) in enumerate(TOUGH)] + [f'{len(EASY) + len(TOUGH) + 1:02d}-end']
    d = os.path.join(OUT, 'playoffs'); os.makedirs(d, exist_ok=True)
    for n, _ in EASY + TOUGH: print(n, BASE[n]['team'], sorted(SCHED[BASE[n]['team']]), [int(FRK.loc[o, BASE[n]['pos']]) for _, o, _ in sorted(SCHED[BASE[n]['team']])])
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1080, 'height': 1920}, device_scale_factor=1)
        pg.goto('file://' + os.path.join(OUT, 'playoffs.html'))
        pg.evaluate('''() => document.fonts.ready.then(() => { for (const el of document.querySelectorAll('.fit')) { let s = parseFloat(getComputedStyle(el).fontSize);
            while (el.scrollWidth > el.clientWidth && s > 60) { s -= 2; el.style.fontSize = s + 'px'; } } })''')
        print(pg.evaluate('''() => [...document.querySelectorAll('section.slide')].map((s, i) => { const t = s.getBoundingClientRect().top; let m = 0;
            for (const el of s.querySelectorAll('.why,.swipe,.endbox,.cols,.key')) m = Math.max(m, el.getBoundingClientRect().bottom - t); return i + ':' + Math.round(m); })'''))
        for el, n in zip(pg.query_selector_all('section.slide'), names):
            el.screenshot(path=os.path.join(d, n + '.png'))
        b.close()
    print(names)
