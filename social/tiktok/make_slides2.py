"""Buy low / sell high, part 2: no quarterbacks. Reuses the layout from make_slides.py."""
import os
import make_slides as M

OUT = os.path.dirname(os.path.abspath(__file__))
M.TEAM.update({'CIN': 'Cincinnati Bengals', 'MIA': 'Miami Dolphins', 'TB': 'Tampa Bay Buccaneers', 'PIT': 'Pittsburgh Steelers',
               'CHI': 'Chicago Bears', 'GB': 'Green Bay Packers', 'HOU': 'Houston Texans', 'JAX': 'Jacksonville Jaguars', 'LV': 'Las Vegas Raiders'})

M.BUY = [
    ('Chase Brown', '1 TD on 142 touches', 'while the Bengals have 28 rushing and receiving TDs',
     "Cincinnati’s offense has scored 28 touchdowns, but Brown has just one on 142 touches. He’s still getting about 18 touches a game, "
     "and the model expects a couple more scores to land with him. It has him as the RB17 the rest of the way."),
    ('Ollie Gordon II', '35 carries, 14 points', 'in his last two games',
     "Gordon handled 35 carries the last two weeks but didn’t score, so he put up just 14 points total. Before that, he’d scored in four "
     "straight games. The workload is steady, and the model has him as the RB21 the rest of the way."),
    ('Emeka Egbuka', '16 targets in Week 6', 'his last game before two weeks out',
     "Egbuka missed Weeks 7 and 8 (concussion, then a foot injury), was questionable in Week 9, and Tampa Bay is on bye this week. "
     "An impatient manager may let him go cheap. The model has him as the WR19 the rest of the way."),
    ('DK Metcalf', '5.9 yards per target', 'on 64 targets, 8 a game',
     "Metcalf is getting 8 targets a game, but they’ve turned into only 33 catches, 378 yards and one touchdown, capped by a 1.4-point "
     "game before Pittsburgh’s bye. The model expects the yards to catch up: 11.1 points a game, the WR27."),
    ('Colston Loveland', '8 targets a game since Week 4', '12.5 points a game in that stretch',
     "His season average is dragged down by a slow start: 8.4 points total in Weeks 1 to 3. Since then he’s averaging 8 targets and "
     "12.5 points a game. Chicago is on bye this week, a good time to ask about him. The model has him as the TE11."),
]
M.SELL = [
    ('Christian Watson', '17.9 yards per catch', '879 yards and 7 TDs in nine games',
     "Watson’s 49 catches have gone for 17.9 yards each, and three of his nine games topped 30 points. Big plays like that come and go, "
     "and the model expects about 17.6 a game from here. Still a WR1, so sell only if the offer pays for the boom weeks."),
    ('Tee Higgins', '11.3 yards per target', '758 yards on 67 targets',
     "Higgins has turned 67 targets into 758 yards and six touchdowns, with 20+ points in five of his eight games. Cincinnati’s passing "
     "game is scoring at a pace that rarely lasts. The model still has him as the WR7: sell if someone pays for 20 a game."),
    ('Nico Collins', 'Targets: 10, 8, 7, 5, 5, 4', 'every game he’s played this season',
     "Collins’ targets have slid from 10 in Week 1 to 4 in Week 9, and Tank Dell is back after leading Houston with 9 targets last week. "
     "The model has Collins as the WR15 from here. Sell while his name is worth more than his role."),
    ('Bhayshul Tuten', '3 receiving TDs on 15 catches', 'part of 7 total touchdowns',
     "Tuten has seven touchdowns, three of them on just 15 catches, a rate that rarely holds. His touches have dipped from 18 a game to 15 "
     "the last two, with Chris Rodriguez Jr. getting 10 carries in Week 9. The model has him as the RB16."),
    ('Brock Bowers', '9.5 yards per target', '658 yards in seven games',
     "Bowers has been the best tight end in football, but Kirk Cousins was traded and rookie Fernando Mendoza is his quarterback now. "
     "The model expects some cooling, to about 19.7 a game, still the TE1. Only sell for a top running back or receiver."),
]

if __name__ == '__main__':
    from playwright.sync_api import sync_playwright
    _missing = [n for n, *_ in M.BUY + M.SELL if n not in M.mkt]
    if _missing: raise SystemExit('No longer on the site\'s buy low / sell high list (rerun node export_buy_sell.js or pick others): ' + ', '.join(_missing))
    CSS = open(os.path.join(OUT, 'slides.css')).read()
    cover = M.cover().replace('Fantasy trade targets', 'Part 2 · No quarterbacks')
    slides = [cover] + [M.player_slide('buy', i + 1, len(M.BUY), *p) for i, p in enumerate(M.BUY)] + \
             [M.player_slide('sell', i + 1, len(M.SELL), *p) for i, p in enumerate(M.SELL)] + [M.end()]
    open(os.path.join(OUT, 'slides2.html'), 'w').write(f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(slides)}</body></html>')
    slug = lambda n: n.lower().replace(' ', '-').replace('.', '')
    names = ['00-cover'] + [f'{i + 1:02d}-buy-{slug(n)}' for i, (n, *_) in enumerate(M.BUY)] + \
            [f'{i + 6:02d}-sell-{slug(n)}' for i, (n, *_) in enumerate(M.SELL)] + ['11-end']
    os.makedirs(os.path.join(OUT, 'part2'), exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1080, 'height': 1920}, device_scale_factor=1)
        pg.goto('file://' + os.path.join(OUT, 'slides2.html'))
        pg.evaluate('''() => document.fonts.ready.then(() => { for (const el of document.querySelectorAll('.fit')) { let s = parseFloat(getComputedStyle(el).fontSize);
            while (el.scrollWidth > el.clientWidth && s > 60) { s -= 2; el.style.fontSize = s + 'px'; } } })''')
        print(pg.evaluate('''() => [...document.querySelectorAll('section.slide')].map((s, i) => { const t = s.getBoundingClientRect().top; let m = 0;
            for (const el of s.querySelectorAll('.why,.swipe,.endbox,.cols,.key')) m = Math.max(m, el.getBoundingClientRect().bottom - t); return i + ':' + Math.round(m); })'''))
        for el, n in zip(pg.query_selector_all('section.slide'), names):
            el.screenshot(path=os.path.join(OUT, 'part2', n + '.png'))
        b.close()
    print(names)
