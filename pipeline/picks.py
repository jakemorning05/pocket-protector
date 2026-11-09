"""Lock each game's pick at kickoff.

Every run rewrites the entry for games that haven't kicked off yet with the model's latest numbers. Once kickoff has
passed the entry is never touched again, so the site's record is built from picks that were public before the game.
Results are filled in when the game is final. Games played before the log existed have no entry.
"""
import json, os, datetime
from zoneinfo import ZoneInfo

D = os.path.join(os.path.dirname(__file__), '..', 'data')
ET = ZoneInfo('America/New_York')


def main(now=None):
    now = now or datetime.datetime.now(ET)
    site = json.load(open(f'{D}/site_data.json'))
    path = f'{D}/pick_log.json'
    log = json.load(open(path)) if os.path.exists(path) else {}
    stamp = now.strftime('%b %-d, %-I:%M %p ET')
    new = upd = graded = 0
    for g in site['games']:
        kick = datetime.datetime.strptime(g['day'] + ' ' + (g['time'] or '13:00'), '%Y-%m-%d %H:%M').replace(tzinfo=ET)
        e = log.get(g['id'])
        if g['hs'] is None and kick > now:
            new += e is None; upd += e is not None
            log[g['id']] = {'wk': g['wk'], 'a': g['a'], 'h': g['h'], 'p': g['p'], 'm': g['m'], 'tot': g['tot'], 'c': g['c'],
                            'pick': g['h'] if g['p'] >= 0.5 else g['a'], 'mk_spread': g['mk_spread'], 'mk_total': g['mk_total'],
                            'first': (e or {}).get('first', stamp), 'stamp': stamp, 'kick': kick.isoformat()}
        elif e is not None and g['hs'] is not None and 'won' not in e:
            e['hs'], e['as'] = g['hs'], g['as']
            e['won'] = None if g['hs'] == g['as'] else (e['pick'] == (g['h'] if g['hs'] > g['as'] else g['a']))
            graded += 1
    json.dump(log, open(path, 'w'), indent=0)
    done = [e for e in log.values() if e.get('won') is not None]
    print(f'pick log: {new} new, {upd} refreshed, {graded} graded; locked record {sum(e["won"] for e in done)}-{sum(not e["won"] for e in done)}')


if __name__ == '__main__':
    main()
