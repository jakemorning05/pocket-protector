"""College football: power ratings, this week's FBS predictions, and a pick log graded after each game.

Ratings are opponent- and home-adjusted point margins, fit by ridge regression and shrunk toward last season's final
rating (full carryover). Settings were chosen by grading every week of 2023-2025 using only games played before that
week (see pipeline/college_backtest.py): 74.4% of winners picked, vs 75.6% for the betting favorite, and no edge against
the spread. A second fit on points scored and allowed gives each team's offense and defense, for projected scores.

Data: cfbfastR-data on GitHub (schedules and results, fetched with a sparse git checkout so it works anywhere git does).
Lines: ESPN's public scoreboard feed when it can be reached (the GitHub Action can; some sandboxes can't); without it the
games still get predictions, just no line.
Writes data/college.json (embedded in the site) and data/college_log.json (picks logged before kickoff, then graded).
Usage: python3 pipeline/college.py"""
import json, os, subprocess, datetime, urllib.request
from math import erf, sqrt
from zoneinfo import ZoneInfo
import numpy as np, pandas as pd

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
CACHE = os.path.join(D, 'cfb_cache')
REPO = 'https://github.com/sportsdataverse/cfbfastR-data'
SEASON = 2026
LAM, HFA, CARRY, SD = 3.0, 3.5, 1.0, 15.5            # tuned on 2023-2025 (college_backtest.py)
FCS_PRIOR = -18.0                                   # starting point for a team with no rating last season
ET = ZoneInfo('America/New_York')
Phi = lambda z: 0.5 * (1 + erf(z / sqrt(2)))


def fetch(seasons):
    """Sparse-checkout the schedule CSVs we need from cfbfastR-data (blobs are fetched only for these files)."""
    repo = os.path.join(CACHE, 'repo')
    files = [f'schedules/csv/cfb_schedules_{y}.csv' for y in seasons]
    run = lambda *a: subprocess.run(['git', '-C', repo, *a], check=True, capture_output=True, text=True)
    if not os.path.isdir(os.path.join(repo, '.git')):
        os.makedirs(CACHE, exist_ok=True)
        subprocess.run(['git', 'clone', '-q', '--depth', '1', '--filter=blob:none', '--no-checkout', REPO, repo], check=True)
    else:
        run('fetch', '-q', '--depth', '1', '--filter=blob:none', 'origin', 'main')
    run('-c', 'gc.auto=0', 'checkout', 'origin/main' if os.path.exists(os.path.join(repo, '.git', 'FETCH_HEAD')) else 'HEAD', '--', *files)
    return {y: os.path.join(repo, f) for y, f in zip(seasons, files)}


def load(path):
    s = pd.read_csv(path, low_memory=False)
    s['done'] = s.completed.astype(str).str.upper() == 'TRUE'
    s['neutral'] = s.neutral_site.astype(str).str.upper() == 'TRUE'
    s['margin'] = s.home_points - s.away_points
    s['post'] = s.season_type == 'postseason'
    s['wk'] = np.where(s.post, 20 + s.week, s.week)   # bowls after the regular season
    s = s[(s.home_division == 'fbs') | (s.away_division == 'fbs')]
    return s


def fit(games, prior, lam, default, col=None):
    """Ridge ratings: margin = r_home - r_away + HFA (0 at neutral sites), shrunk toward prior."""
    teams = sorted(set(games.home_team) | set(games.away_team) | set(prior))
    ix = {t: i for i, t in enumerate(teams)}; n = len(teams)
    A = np.zeros((len(games), n)); y = np.zeros(len(games))
    for k, g in enumerate(games.itertuples()):
        A[k, ix[g.home_team]] = 1; A[k, ix[g.away_team]] = -1
        y[k] = g.margin - (0 if g.neutral else HFA)
    P = np.array([prior.get(t, default) for t in teams])
    r = np.linalg.solve(A.T @ A + lam * np.eye(n), A.T @ y + lam * P)
    return dict(zip(teams, r))


def fit_points(games, prior_o, prior_d, lam):
    """Offense/defense for projected scores: points = mu + off(team) + def(opponent) +/- HFA/2."""
    teams = sorted(set(games.home_team) | set(games.away_team) | set(prior_o))
    ix = {t: i for i, t in enumerate(teams)}; n = len(teams)
    rows, y = [], []
    for g in games.itertuples():
        h = 0 if g.neutral else HFA / 2
        for off, de, pts, sgn in ((g.home_team, g.away_team, g.home_points, 1), (g.away_team, g.home_team, g.away_points, -1)):
            r = np.zeros(2 * n + 1); r[ix[off]] = 1; r[n + ix[de]] = 1; r[-1] = 1
            rows.append(r); y.append(pts - sgn * h)
    A = np.array(rows); y = np.array(y)
    P = np.r_[[prior_o.get(t, -5.0) for t in teams], [prior_d.get(t, 5.0) for t in teams], 0.0]
    reg = lam * np.r_[np.ones(2 * n), 0.0]
    x = np.linalg.solve(A.T @ A + np.diag(reg), A.T @ y + reg * P)
    return {t: x[ix[t]] for t in teams}, {t: x[n + ix[t]] for t in teams}, x[-1]


def predict(r, g, default):
    m = r.get(g.home_team, default) - r.get(g.away_team, default) + (0 if g.neutral else HFA)
    return m, Phi(m / SD)


def espn_lines(week, post):
    """Home-team spread for each game id from ESPN's public scoreboard (home -4 means home favored by 4)."""
    url = ('https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard'
           f'?dates={SEASON}&seasontype={3 if post else 2}&week={week}&groups=80&limit=400')
    try:
        data = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=20))
    except Exception as e:
        print(f'college lines: ESPN not reachable ({type(e).__name__}); predictions only')
        return {}
    out = {}
    for ev in data.get('events', []):
        try:
            comp = ev['competitions'][0]; odds = (comp.get('odds') or [None])[0]
            if not odds: continue
            side = {c['homeAway']: c['team'].get('abbreviation', '') for c in comp['competitors']}
            spread = odds.get('spread'); det = (odds.get('details') or '').strip()
            hf = (odds.get('homeTeamOdds') or {}).get('favorite'); af = (odds.get('awayTeamOdds') or {}).get('favorite')
            if det.upper() in ('EVEN', 'PK', 'PICK'):
                line = 0.0
            elif spread is not None and (hf or af):
                line = -abs(float(spread)) if hf else abs(float(spread))
            elif det and ' ' in det:
                abbr, num = det.rsplit(' ', 1); num = float(num)
                line = num if abbr == side.get('home') else -num
            else:
                continue
            out[int(ev['id'])] = {'line': line, 'total': odds.get('overUnder'), 'book': (odds.get('provider') or {}).get('name')}
        except (KeyError, ValueError, TypeError, IndexError):
            continue
    print(f'college lines: {len(out)} games from ESPN')
    return out


def kickoff(g):
    t = datetime.datetime.fromisoformat(str(g.start_date).replace('Z', '+00:00')).astimezone(ET)
    tbd = str(g.start_time_tbd).upper() == 'TRUE'
    return t, t.strftime('%Y-%m-%d'), ('' if tbd else t.strftime('%H:%M'))


def main():
    paths = fetch((SEASON - 1, SEASON))
    prev, cur = load(paths[SEASON - 1]), load(paths[SEASON])
    prev = prev[prev.done & prev.margin.notna()]
    played = cur[cur.done & cur.margin.notna()]
    upcoming = cur[~cur.done]
    now = datetime.datetime.now(ET)

    # last season, fit on its own, is this season's starting point
    p_r = fit(prev, {}, 1.0, FCS_PRIOR)
    prior = {t: CARRY * v for t, v in p_r.items()}
    po, pd_, _ = fit_points(prev, {}, {}, 1.0)
    r = fit(played, prior, LAM, FCS_PRIOR * CARRY)
    off, de, mu = fit_points(played, po, pd_, LAM)

    # 2026 so far, rebuilt week by week from games before each week (not logged live)
    rebuilt = []
    for wk in sorted(played.wk.unique()):
        rt = fit(played[played.wk < wk], prior, LAM, FCS_PRIOR * CARRY)
        for g in played[played.wk == wk].itertuples():
            if g.margin == 0: continue
            m, _ = predict(rt, g, FCS_PRIOR * CARRY)
            rebuilt.append({'wk': int(wk), 'ok': bool((m > 0) == (g.margin > 0))})
    by_wk = {}
    for x in rebuilt: by_wk.setdefault(x['wk'], [0, 0])[0 if x['ok'] else 1] += 1

    # this week's games
    wk = int(upcoming.wk.min()) if len(upcoming) else None
    post = bool(wk and wk > 20)
    lines = espn_lines(wk - 20 if post else wk, post) if wk else {}
    games = []
    for g in upcoming[upcoming.wk == wk].sort_values('start_date').itertuples() if wk else []:
        m, p = predict(r, g, FCS_PRIOR * CARRY)
        h = 0 if g.neutral else HFA / 2
        hp = mu + off.get(g.home_team, -5) + de.get(g.away_team, 5) + h
        ap = mu + off.get(g.away_team, -5) + de.get(g.home_team, 5) - h
        tot = max(hp + ap, 20)
        t, day, tm = kickoff(g)
        ln = lines.get(int(g.game_id), {})
        games.append({'id': int(g.game_id), 'day': day, 'time': tm, 'start': t.isoformat(), 'a': g.away_team, 'h': g.home_team,
                      'ac': g.away_conference if isinstance(g.away_conference, str) else '', 'hc': g.home_conference if isinstance(g.home_conference, str) else '',
                      'neutral': bool(g.neutral), 'venue': g.venue if isinstance(g.venue, str) else '', 'm': round(m, 1), 'p': round(p, 3),
                      'hs': round((tot + m) / 2), 'as': round((tot - m) / 2), 'line': ln.get('line'), 'mk_total': ln.get('total'), 'book': ln.get('book')})

    # power rankings (FBS teams), with last week's rank for movement
    fbs = set(cur[cur.home_division == 'fbs'].home_team) | set(cur[cur.away_division == 'fbs'].away_team)
    conf = {}
    for g in cur.itertuples():
        if isinstance(g.home_conference, str): conf[g.home_team] = g.home_conference
        if isinstance(g.away_conference, str): conf[g.away_team] = g.away_conference
    last_wk = int(played.wk.max())
    r_prev = fit(played[played.wk < last_wk], prior, LAM, FCS_PRIOR * CARRY)
    order = lambda rt: [t for t in sorted(fbs, key=lambda t: -rt.get(t, -99))]
    prev_rank = {t: i + 1 for i, t in enumerate(order(r_prev))}
    rec = {}
    for g in played.itertuples():
        for t, won in ((g.home_team, g.margin > 0), (g.away_team, g.margin < 0)):
            w, l = rec.get(t, (0, 0)); rec[t] = (w + won, l + (not won))
    rank = [{'rk': i + 1, 'team': t, 'conf': conf.get(t, ''), 'r': round(r.get(t, 0), 1), 'off': round(off.get(t, 0), 1), 'def': round(de.get(t, 0), 1),
             'w': int(rec.get(t, (0, 0))[0]), 'l': int(rec.get(t, (0, 0))[1]), 'prev': prev_rank.get(t)} for i, t in enumerate(order(r))]

    # pick log: log each game once before kickoff (fill in a missing line until kickoff), grade once it's final
    lp = os.path.join(D, 'college_log.json')
    log = json.load(open(lp)) if os.path.exists(lp) else []
    have = {x['id']: x for x in log}
    stamp = now.strftime('%a %b %-d, %-I:%M %p ET')
    for g in games:
        if datetime.datetime.fromisoformat(g['start']) <= now: continue
        x = have.get(g['id'])
        if x is None:
            x = {'id': g['id'], 'wk': wk, 'day': g['day'], 'a': g['a'], 'h': g['h'], 'm': g['m'], 'p': g['p'],
                 'pick': g['h'] if g['m'] > 0 else g['a'], 'line': g['line'], 'logged': stamp}
            log.append(x); have[g['id']] = x
        elif x.get('line') is None and g['line'] is not None:
            x['line'] = g['line']; x['line_logged'] = stamp
    res = {int(g.game_id): (g.away_points, g.home_points) for g in played.itertuples()}
    for x in log:
        if x.get('result') is None and x['id'] in res:
            a_, h_ = res[x['id']]; mg = h_ - a_
            x['as'], x['hs'] = int(a_), int(h_)
            x['result'] = 'push' if mg == 0 else ('win' if (mg > 0) == (x['pick'] == x['h']) else 'loss')
            if x.get('line') is not None:
                mk = -x['line']; side_home = x['m'] > mk
                x['ats'] = 'push' if mg == mk else ('win' if (mg > mk) == side_home else 'loss')
    json.dump(log, open(lp, 'w'), indent=1)
    for g in games:
        if g['id'] in have: g['logged'] = have[g['id']]['logged']

    graded = [x for x in log if x.get('result') in ('win', 'loss')]
    ats = [x for x in log if x.get('ats') in ('win', 'loss')]
    bt = json.load(open(os.path.join(D, 'college_backtest.json'))) if os.path.exists(os.path.join(D, 'college_backtest.json')) else {}
    out = {'asof': stamp, 'season': SEASON, 'week': (wk - 20 if post else wk), 'post': post, 'games': games, 'rank': rank,
           'rebuilt': {str(k): v for k, v in sorted(by_wk.items())},
           'live': {'w': sum(x['result'] == 'win' for x in graded), 'l': sum(x['result'] == 'loss' for x in graded),
                    'ats_w': sum(x['ats'] == 'win' for x in ats), 'ats_l': sum(x['ats'] == 'loss' for x in ats),
                    'pending': sum(x.get('result') is None for x in log)},
           'recent': [x for x in log if x.get('result')][-40:], 'backtest': bt, 'lines': bool(lines)}
    json.dump(out, open(os.path.join(D, 'college.json'), 'w'), separators=(',', ':'))
    tot = sum(v[0] + v[1] for v in by_wk.values()); ok = sum(v[0] for v in by_wk.values())
    print(f'college: week {out["week"]}, {len(games)} games, {len(rank)} FBS teams; 2026 rebuilt {ok}-{tot - ok}; log {len(log)} ({out["live"]})')


if __name__ == '__main__':
    main()
