"""Grade the college model on past seasons, week by week, using only games played before each week, with the same
settings and code as pipeline/college.py. Compares against the median closing spread across books. Writes
data/college_backtest.json for the College tab. Slow (a few minutes); run by hand after changing the model.
Usage: python3 pipeline/college_backtest.py"""
import json, os, subprocess
import numpy as np, pandas as pd
import college as C

SEASONS = (2023, 2024, 2025)


def lines():
    repo = os.path.join(C.CACHE, 'repo')
    subprocess.run(['git', '-C', repo, '-c', 'gc.auto=0', 'checkout', 'HEAD', '--', 'betting/csv/cfb_line_odds.csv.gz'], check=True, capture_output=True)
    L = pd.read_csv(os.path.join(repo, 'betting/csv/cfb_line_odds.csv.gz'), low_memory=False)
    L = L[(L.market_type == 'spread') & (L.season >= min(SEASONS))]
    L = L[L.abbr == L.game_desc.str.split('@').str[-1]]          # the home team's line
    return (-L.groupby('game_id').lines.median()).to_dict()      # expected home margin


def main():
    paths = C.fetch(tuple(range(min(SEASONS) - 1, max(SEASONS) + 1)))
    mk = lines()
    rows = []
    for yr in SEASONS:
        prev = C.load(paths[yr - 1]); prev = prev[prev.done & prev.margin.notna()]
        cur = C.load(paths[yr]); cur = cur[cur.done & cur.margin.notna()]
        prior = {t: C.CARRY * v for t, v in C.fit(prev, {}, 1.0, C.FCS_PRIOR).items()}
        for wk in sorted(cur.wk.unique()):
            rt = C.fit(cur[cur.wk < wk], prior, C.LAM, C.FCS_PRIOR * C.CARRY)
            for g in cur[cur.wk == wk].itertuples():
                if g.margin == 0: continue
                m, p = C.predict(rt, g, C.FCS_PRIOR * C.CARRY)
                rows.append({'season': yr, 'm': m, 'p': p, 'act': g.margin, 'mk': mk.get(int(g.game_id))})
    o = pd.DataFrame(rows)
    out = {'seasons': list(SEASONS), 'by_season': []}
    for yr, x in list(o.groupby('season')) + [('all', o)]:
        l = x[x.mk.notna() & (x.mk != 0)]
        a = l[l.act != l.mk]
        ats_w = int(((a.m > a.mk) == (a.act > a.mk)).sum())
        out['by_season'].append({'season': yr, 'n': len(x), 'su': round(float(((x.m > 0) == (x.act > 0)).mean()), 3),
                                 'lined': len(l), 'su_lined': round(float(((l.m > 0) == (l.act > 0)).mean()), 3),
                                 'su_market': round(float(((l.mk > 0) == (l.act > 0)).mean()), 3),
                                 'mae': round(float((l.m - l.act).abs().mean()), 1), 'mae_market': round(float((l.mk - l.act).abs().mean()), 1),
                                 'ats_w': ats_w, 'ats_l': len(a) - ats_w})
    # how often the favorite wins by model confidence (for the tab's calibration line)
    o['bucket'] = pd.cut(o.p.where(o.p >= 0.5, 1 - o.p), [0.5, 0.6, 0.7, 0.8, 0.9, 1.0], include_lowest=True)
    out['calibration'] = [{'range': f'{max(50, round(b.left * 100))}-{round(b.right * 100)}%', 'n': int(len(x)),
                           'won': round(float(((x.m > 0) == (x.act > 0)).mean()), 3)} for b, x in o.groupby('bucket', observed=True)]
    json.dump(out, open(os.path.join(C.D, 'college_backtest.json'), 'w'), indent=1)
    print(json.dumps(out['by_season'][-1]), out['calibration'])


if __name__ == '__main__':
    main()
