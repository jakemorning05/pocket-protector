"""2027 NFL Draft tab: a consensus big board from several public boards, plus team needs and traded picks.

Reads data/draft_sources.json (boards typed in from the sources it names, NFL.com team needs, traded first-round picks)
and writes data/draft.json. The draft order and the mock itself are worked out in the browser from the season
simulations, so they move with every result.

Consensus: each player's average rank across the boards. A board that doesn't list a player counts him at its length
plus 16 (just past where that board stops), and a player has to be on at least two boards.
"""
import json, os, re

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')
POS = {'WR': 'WR', 'QB': 'QB', 'RB': 'RB', 'TE': 'TE', 'OT': 'OT', 'OG': 'IOL', 'C': 'IOL', 'G': 'IOL', 'G/C': 'IOL', 'IOL': 'IOL',
       'EDGE': 'EDGE', 'DE': 'EDGE', 'DT': 'DL', 'DL': 'DL', 'IDL': 'DL', 'LB': 'LB', 'OLB': 'LB', 'CB': 'CB', 'S': 'S', 'SAF': 'S'}
NEED = {'Edge': 'EDGE', 'DT': 'DL'}
SCHOOL = {'Mississippi': 'Ole Miss', 'Miami (Fla.)': 'Miami', 'Miami (FL)': 'Miami', 'Southern Cal': 'USC', 'Penn St.': 'Penn State'}
ALIAS = {'kelly jones': 'kelley jones'}


def key(name):
    k = re.sub(r"[.,]", '', name.lower())
    k = re.sub(r"\s+(jr|sr|ii|iii|iv)$", '', k).strip()
    return ALIAS.get(k, k)


def main():
    src = json.load(open(f'{D}/draft_sources.json'))
    players, ranks = {}, {}
    for b in src['boards']:
        for i, row in enumerate(b['players'], 1):
            name, pos, school = [x.strip() for x in row.split('|')]
            k = key(name)
            p = players.setdefault(k, {'name': name, 'pos': [], 'school': SCHOOL.get(school, school)})
            if b['key'] == 'pfn': p['name'] = name  # most recent board's spelling
            p['pos'].append(POS[pos.upper()] if pos.upper() in POS else POS[pos])
            ranks.setdefault(k, {})[b['key']] = i
    out = []
    for k, p in players.items():
        r = ranks[k]
        if len(r) < 2: continue
        allr = [r.get(b['key'], len(b['players']) + 16) for b in src['boards']]
        pos = max(set(p['pos']), key=p['pos'].count)
        out.append({'name': p['name'], 'pos': pos, 'school': p['school'], 'avg': round(sum(allr) / len(allr), 1),
                    'best': min(r.values()), 'worst': max(r.values()), 'n': len(r), 'ranks': r})
    out.sort(key=lambda x: (x['avg'], x['best']))
    for i, p in enumerate(out, 1): p['rank'] = i
    needs = {t: [NEED.get(n, n) for n in v] for t, v in src['needs'].items()}
    json.dump({'updated': src['updated'], 'board': out[:80], 'needs': needs, 'needs_source': src['needs_source'],
               'trades': src['trades'], 'boards': [{k: b[k] for k in ('key', 'name', 'date', 'url')} | {'n': len(b['players'])} for b in src['boards']]},
              open(f'{D}/draft.json', 'w'), separators=(',', ':'), ensure_ascii=False)
    print(f'draft board: {len(out)} players on 2+ boards; top 5:', ', '.join(f"{p['name']} {p['pos']} ({p['avg']})" for p in out[:5]))


if __name__ == '__main__':
    main()
