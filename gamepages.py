"""Write one preview page per game to docs/games/ (plain HTML, for search engines and sharing) plus docs/sitemap.xml."""
import os, json, html, datetime
from zoneinfo import ZoneInfo

B = os.path.dirname(os.path.abspath(__file__))
P = lambda *a: os.path.join(B, *a)
ET = ZoneInfo('America/New_York')
NAMES = {
    'ARI': ('Arizona', 'Cardinals'), 'ATL': ('Atlanta', 'Falcons'), 'BAL': ('Baltimore', 'Ravens'), 'BUF': ('Buffalo', 'Bills'),
    'CAR': ('Carolina', 'Panthers'), 'CHI': ('Chicago', 'Bears'), 'CIN': ('Cincinnati', 'Bengals'), 'CLE': ('Cleveland', 'Browns'),
    'DAL': ('Dallas', 'Cowboys'), 'DEN': ('Denver', 'Broncos'), 'DET': ('Detroit', 'Lions'), 'GB': ('Green Bay', 'Packers'),
    'HOU': ('Houston', 'Texans'), 'IND': ('Indianapolis', 'Colts'), 'JAX': ('Jacksonville', 'Jaguars'), 'KC': ('Kansas City', 'Chiefs'),
    'LV': ('Las Vegas', 'Raiders'), 'LAC': ('Los Angeles', 'Chargers'), 'LA': ('Los Angeles', 'Rams'), 'MIA': ('Miami', 'Dolphins'),
    'MIN': ('Minnesota', 'Vikings'), 'NE': ('New England', 'Patriots'), 'NO': ('New Orleans', 'Saints'), 'NYG': ('New York', 'Giants'),
    'NYJ': ('New York', 'Jets'), 'PHI': ('Philadelphia', 'Eagles'), 'PIT': ('Pittsburgh', 'Steelers'), 'SF': ('San Francisco', '49ers'),
    'SEA': ('Seattle', 'Seahawks'), 'TB': ('Tampa Bay', 'Buccaneers'), 'TEN': ('Tennessee', 'Titans'), 'WAS': ('Washington', 'Commanders'),
}
full = lambda t: ' '.join(NAMES[t])
nick = lambda t: NAMES[t][1]
esc = html.escape
slug = lambda g: f"week-{g['wk']}-{nick(g['a']).lower()}-at-{nick(g['h']).lower()}-prediction"
pct = lambda p: f'{round(p * 100)}%'
# how each factor reads in a sentence; {t} is the team it favors
PHRASE = {
    'Quarterbacks': '{t} have the edge at quarterback',
    'Offense & defense efficiency': '{t} have been the more efficient team play for play',
    'Points scored & allowed': '{t} have the better scoring margin',
    'Turnovers': '{t} have the better turnover profile',
    'Special teams': '{t} have the stronger special teams',
    'Rest & travel': '{t} get the better of rest and travel',
    'Injuries': '{t} are the healthier team',
    'Past betting lines': 'oddsmakers have rated {t} higher in recent weeks',
}
LOGO = ('<svg viewBox="0 0 32 32" aria-hidden="true"><rect x="8" y="3.5" width="3.4" height="12" rx="1.7" fill="var(--pen-pink)"/>'
        '<path d="M17 15.5V9.5M13.4 9.5h7.2M13.4 9.5V3M20.6 9.5V3" stroke="var(--pen-mint)" stroke-width="2.2" stroke-linecap="round" fill="none"/>'
        '<rect x="22.4" y="5.5" width="3.4" height="10" rx="1.7" fill="var(--pen-sky)"/>'
        '<path d="M5.5 13.5h21v11.5a4 4 0 0 1-4 4h-13a4 4 0 0 1-4-4z" fill="var(--accent)"/></svg>')


def line_txt(g, margin):
    r = round(abs(margin) * 2) / 2
    if r < 0.5:
        return 'Pick’em'
    return f"{g['h'] if margin > 0 else g['a']} −{r:g}"


def fp(r):  # PPR fantasy points
    return ((r.get('pass_yds') or 0) / 25 + 4 * (r.get('pass_td') or 0) - 2 * (r.get('int') or 0) + (r.get('rush_yds') or 0) / 10
            + 6 * (r.get('rush_td') or 0) + (r.get('rec_yds') or 0) / 10 + 6 * (r.get('rec_td') or 0) + (r.get('rec') or 0))


def preview(g, done):
    pH = g['p']; fav, dog = (g['h'], g['a']) if pH >= 0.5 else (g['a'], g['h']); p = max(pH, 1 - pH)
    hs, as_ = (g['tot'] + g['m']) / 2, (g['tot'] - g['m']) / 2
    fs, ds = (hs, as_) if fav == g['h'] else (as_, hs)
    where = 'at home against' if fav == g['h'] and not g['neutral'] else 'on the road against' if not g['neutral'] else 'against'
    verb = 'gave' if done else 'gives'
    out = [f"The model {verb} the {esc(full(fav))} a {pct(p)} chance to win {where} the {esc(full(dog))}, with a projected score of {fav} {round(fs)}, {dog} {round(ds) if round(ds) != round(fs) else round(ds) - 1}."]
    facs = sorted(((k, v) for k, v in g['c'].items() if k in PHRASE and abs(v) >= 0.8), key=lambda kv: -abs(kv[1]))[:3]
    if facs:
        bits = [PHRASE[k].format(t='the ' + nick(g['h'] if v > 0 else g['a'])) + f' (worth about {abs(v):.1f} points)' for k, v in facs]
        bits[0] = bits[0][0].upper() + bits[0][1:]
        out.append('; '.join(bits) + '.')
    if abs(g['c'].get('Home field', 0)) > 0.5:
        out.append(f"Home field adds about {abs(g['c']['Home field']):.1f} points for {nick(g['h'])}.")
    if g['div']:
        out.append('It’s a division game, and those tend to be closer than the ratings suggest.')
    if p < 0.55:
        out.append('This one is close to a coin flip.')
    elif p >= 0.7:
        out.append('That makes it one of the model’s stronger picks of the week; picks at 70% or higher have won about three times in four.')
    if g.get('mk_spread') is not None:
        gap = g['m'] - g['mk_spread']
        cmp_ = 'in line with' if abs(gap) < 1 else f"{abs(gap):.1f} points more toward {nick(g['h'] if gap > 0 else g['a'])} than"
        out.append(f"The betting line {'closed at' if done else 'is'} {line_txt(g, g['mk_spread'])} with a total of {g['mk_total']:g}; the model’s number is {line_txt(g, g['m'])} and {round(g['tot'] * 2) / 2:g}, {cmp_} the market on the spread.")
    return out


def page(g, lock, fan, news, site_url):
    done = g['hs'] is not None
    if lock and (done or datetime.datetime.fromisoformat(lock['kick']) <= datetime.datetime.now(ET)):
        g = {**g, 'p': lock['p'], 'm': lock['m'], 'tot': lock['tot'], 'c': lock.get('c') or g['c']}
    a, h = g['a'], g['h']; pH = g['p']; pick = h if pH >= 0.5 else a; p = max(pH, 1 - pH)
    kick = datetime.datetime.strptime(g['day'] + ' ' + (g['time'] or '13:00'), '%Y-%m-%d %H:%M').replace(tzinfo=ET)
    when = kick.strftime('%A, %B %-d, %Y at %-I:%M %p ET')
    title = f"{nick(a)} vs. {nick(h)} Prediction and Pick, Week {g['wk']} 2026"
    desc = f"Computer model pick for {full(a)} at {full(h)} (Week {g['wk']}, {kick.strftime('%b %-d')}): {full(pick)} {pct(p)} to win, projected score, key factors, injuries and fantasy projections."
    paras = ''.join(f'<p>{x}</p>' for x in preview(g, done))
    if done:
        tie = g['hs'] == g['as']; won = (g['hs'] > g['as']) == (pick == h)
        res = (f'<div class="panel"><h2>Result</h2><p><b>{a} {g["as"]}, {h} {g["hs"]}.</b> ' +
               ('The game ended in a tie.' if tie else f'The model’s pick, {esc(full(pick))}, <span class="{"good" if won else "bad"}">{"won" if won else "lost"}</span>.') + '</p></div>')
    else:
        res = ''
    hs, as_ = (g['tot'] + g['m']) / 2, (g['tot'] - g['m']) / 2
    tiles = (f'<div class="tiles num"><div class="tile"><span class="label">Model pick</span><b>{pick}</b><span class="muted small">{pct(p)} to win</span></div>'
             f'<div class="tile"><span class="label">Projected score</span><b>{round(as_)}–{round(hs)}</b><span class="muted small">{a} – {h}</span></div>'
             f'<div class="tile"><span class="label">Model line</span><b>{line_txt(g, g["m"])}</b><span class="muted small">Total {round(g["tot"] * 2) / 2:g}</span></div>' +
             (f'<div class="tile"><span class="label">Betting line</span><b>{line_txt(g, g["mk_spread"])}</b><span class="muted small">Total {g["mk_total"]:g}</span></div>' if g.get('mk_spread') is not None else '') + '</div>')
    bar = (f'<div class="probbar" role="img" aria-label="Win chance: {a} {pct(1 - pH)}, {h} {pct(pH)}"><span class="a" style="width:{(1 - pH) * 100:.1f}%"></span><span class="h" style="width:{pH * 100:.1f}%"></span></div>'
           f'<div class="prob-labels num"><span><span class="swatch a"></span><b>{a}</b> {pct(1 - pH)}</span><span>{pct(pH)} <b>{h}</b><span class="swatch h" style="margin:0 0 0 5px"></span></span></div>')
    frows = ''.join(f'<tr><td class="l">{esc(k)}</td><td class="l">{h if v > 0 else a}</td><td>{abs(v):.1f} pts</td></tr>'
                    for k, v in sorted(g['c'].items(), key=lambda kv: -abs(kv[1])) if abs(v) >= 0.05)
    factors = f'<div class="panel"><h2>What drives the pick</h2><div class="tablewrap"><table><thead><tr><th class="l">Factor</th><th class="l">Favors</th><th>Worth</th></tr></thead><tbody>{frows}</tbody></table></div><p class="muted small">Quarterbacks: {esc(g["qa"] or "?")} ({a}) vs. {esc(g["qh"] or "?")} ({h}).</p></div>'
    inj = [r for r in news.get('injuries', []) if r['team'] in (a, h) and r['status'] in ('Out', 'Doubtful', 'Questionable')]
    injuries = ''
    if inj and not done and g['wk'] <= news.get('injury_week', 0) + 1:
        injuries = ('<div class="panel"><h2>Injured regulars</h2><div class="tablewrap"><table><thead><tr><th class="l">Team</th><th class="l">Player</th><th class="l">Status</th><th class="l">Injury</th></tr></thead><tbody>' +
                    ''.join(f'<tr><td class="l"><b>{r["team"]}</b></td><td class="l">{esc(r["name"])} <span class="muted small">{esc(r["pos"])}</span></td><td class="l">{r["status"]}</td><td class="l muted">{esc(r["injury"])}</td></tr>' for r in inj) +
                    f'</tbody></table></div><p class="muted small">From the Week {news.get("injury_week")} injury report; players who took at least half their team’s snaps.</p></div>')
    fr = sorted([r for r in fan if r.get('game') == g['id']], key=lambda r: -fp(r))[:8]
    fantasy = ''
    if fr and not done:
        def stat(r):
            if r['pos'] == 'QB':
                return f"{round(r.get('pass_yds') or 0)} pass yds, {(r.get('pass_td') or 0):.1f} TD, {round(r.get('rush_yds') or 0)} rush"
            return (f"{round(r['rush_yds'])} rush, " if (r.get('rush_yds') or 0) >= 5 else '') + f"{(r.get('rec') or 0):.1f} rec, {round(r.get('rec_yds') or 0)} yds"
        fantasy = ('<div class="panel"><h2>Fantasy projections</h2><div class="tablewrap"><table><thead><tr><th class="l">Player</th><th>PPR pts</th><th class="l">Projection</th><th>TD chance</th></tr></thead><tbody>' +
                   ''.join(f'<tr><td class="l"><b>{esc(r["name"])}</b> <span class="muted small">{r["pos"]} · {r["team"]}</span></td><td><b>{fp(r):.1f}</b></td><td class="l muted small">{stat(r)}</td><td>{pct(r.get("td_p") or 0)}</td></tr>' for r in fr) +
                   '</tbody></table></div></div>')
    ld = json.dumps({'@context': 'https://schema.org', '@type': 'SportsEvent', 'name': f'{full(a)} at {full(h)}', 'startDate': kick.isoformat(),
                     'awayTeam': {'@type': 'SportsTeam', 'name': full(a)}, 'homeTeam': {'@type': 'SportsTeam', 'name': full(h)}, 'sport': 'American football'})
    url = f'{site_url}games/{slug(g)}.html'
    started = done or kick <= datetime.datetime.now(ET)
    note = ('This pick was locked at kickoff.' if lock else 'This pick was reconstructed from data available before kickoff.') if started else 'This pick updates with injury news until kickoff, then locks for good.'
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(title)} | Pocket Protector</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{url}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="article">
<meta property="og:url" content="{url}">
<meta name="theme-color" content="#11162A">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Rubik:wght@400;500;600;700;800&display=swap">
<link rel="stylesheet" href="site.css">
<script type="application/ld+json">{ld}</script>
</head>
<body>
<header class="top"><div class="wrap"><div class="brand"><a class="logo" href="../" aria-label="Pocket Protector home">{LOGO}<span class="brandname">Pocket <span>Protector</span></span></a>
<nav class="pagenav"><a href="../#week">All games</a><a href="../#pools">Pools</a><a href="../#fantasy">Fantasy</a></nav></div></div></header>
<main class="wrap gamepage">
<div><p class="label">Week {g['wk']} · {when}</p><h1>{esc(full(a))} at {esc(full(h))}: prediction and pick</h1></div>
{tiles}
<div class="panel">{bar}</div>
{res}
<div class="panel prose"><h2>{'How the model saw it' if done else 'The preview'}</h2>{paras}</div>
{factors}{injuries}{fantasy}
<p class="notice">{note} Predictions are estimates, not betting advice. <a href="../#about">About the model</a> · <a href="../#week">See every game this week</a></p>
<footer class="foot"><span>Pocket Protector · NFL picks, pools and fantasy by the numbers</span><span>Data: nflverse · Not affiliated with the NFL</span></footer>
</main>
</body>
</html>
'''


EXTRA_CSS = '''
[hidden]{display:none!important} img{max-width:100%}
.gamepage { display: grid; gap: 18px; padding-top: 22px; }
.gamepage h1 { font-size: clamp(1.5rem, 4.5vw, 2.1rem); font-weight: 800; line-height: 1.15; margin-top: 4px; }
.gamepage h2 { font-size: 1.15rem; margin-bottom: 10px; }
.brandname { font-family: var(--font-display); font-weight: 800; font-size: 1.35rem; letter-spacing: -0.02em; }
.brandname span { color: var(--accent); }
.pagenav { display: flex; gap: 6px; flex-wrap: wrap; }
.pagenav a { text-decoration: none; color: var(--ink-2); font-family: var(--font-display); font-weight: 500; padding: 7px 12px; border-radius: 999px; background: var(--surface); }
.gamepage .top, .top { padding-block: 12px; }
.good { color: var(--good); font-weight: 700; } .bad { color: var(--bad); font-weight: 700; }
body { padding-bottom: 40px; }
.gamepage td { white-space: normal; }
.gamepage td:last-child, .gamepage th:last-child { white-space: nowrap; }
@media (max-width: 520px) { .gamepage table { font-size: 0.9rem; } .gamepage .tile b { font-size: 1.7rem; } }
'''


def build(site_url):
    site = json.load(open(P('data', 'site_data.json'))); news = json.load(open(P('data', 'news.json')))
    fan = json.load(open(P('data', 'fantasy.json')))['games']
    try:
        locks = json.load(open(P('data', 'pick_log.json')))
    except FileNotFoundError:
        locks = {}
    out = P('docs', 'games'); os.makedirs(out, exist_ok=True)
    css = open(P('src', 'style.css.html'), encoding='utf-8').read().replace('<style>', '').replace('</style>', '')
    open(os.path.join(out, 'site.css'), 'w', encoding='utf-8').write(css + EXTRA_CSS)
    urls = [site_url]
    for g in site['games']:
        open(os.path.join(out, slug(g) + '.html'), 'w', encoding='utf-8').write(page(g, locks.get(g['id']), fan, news, site_url))
        urls.append(f'{site_url}games/{slug(g)}.html')
    today = datetime.date.today().isoformat()
    open(P('docs', 'sitemap.xml'), 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
                                               ''.join(f'<url><loc>{u}</loc><lastmod>{today}</lastmod></url>\n' for u in urls) + '</urlset>\n')
    return len(urls) - 1
