"""Assemble the site from the page template and the exported data files.

Writes two copies of the same page:
  docs/index.html          full HTML document for GitHub Pages (the public site)
  pocket-protector.html    page fragment for the Claude artifact preview (the artifact host adds <html>/<head>)
"""
import os, re

B = os.path.dirname(os.path.abspath(__file__))
P = lambda *a: os.path.join(B, *a)
read = lambda *a: open(P(*a), encoding='utf-8').read()

import gamepages

SITE_URL = 'https://jakemorning05.github.io/pocket-protector/'  # change this if you move to a custom domain
TITLE = 'Pocket Protector'
DESC = 'NFL game predictions, pick’em and survivor pool tools, and fantasy projections from a statistical model.'
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Rubik:wght@400;500;600;700;800&display=swap">\n')
FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
           "%3Crect x='8' y='3.5' width='3.4' height='12' rx='1.7' fill='%23FF5D8F'/%3E"
           "%3Cpath d='M17 15.5V9.5M13.4 9.5h7.2M13.4 9.5V3M20.6 9.5V3' stroke='%233DDC97' stroke-width='2.2' stroke-linecap='round' fill='none'/%3E"
           "%3Crect x='22.4' y='5.5' width='3.4' height='10' rx='1.7' fill='%234DA3FF'/%3E"
           "%3Cpath d='M5.5 13.5h21v11.5a4 4 0 0 1-4 4h-13a4 4 0 0 1-4-4z' fill='%23FFD23F'/%3E%3C/svg%3E")


def body():
    try:
        props = read('data', 'prop_log.json')
    except FileNotFoundError:
        props = '[]'
    try:
        picks = read('data', 'pick_log.json')
    except FileNotFoundError:
        picks = '{}'
    out = read('src', 'app2_body.html')
    for key, text in [('/*__DATA__*/', read('data', 'site_data.json')), ('/*__PLAYERS__*/', read('data', 'players.json')),
                      ('/*__PROPS__*/', props), ('/*__FAN__*/', read('data', 'fantasy.json')), ('/*__BETS__*/', read('data', 'bet_log.json')),
                      ('/*__TRACK__*/', read('data', 'bet_track.json')), ('/*__NEWS__*/', read('data', 'news.json')), ('/*__PICKS__*/', picks),
                      ('/*__POOLS__*/', read('src', 'pools.js'))]:
        out = out.replace(key, text)
    assert '/*__' not in out, 'unfilled placeholder'
    return out


def main():
    style, page = read('src', 'style.css.html'), body()
    # artifact fragment
    assert page.count("'__BASE__'") == 1
    frag = (f'<meta charset="utf-8">\n<title>{TITLE}</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
            + FONTS + style + '\n' + page.replace("'__BASE__'", repr(SITE_URL)))
    open(P('pocket-protector.html'), 'w', encoding='utf-8').write(frag)
    # standalone document
    doc = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
           f'<title>{TITLE} · NFL picks, pools and fantasy</title>\n<meta name="description" content="{DESC}">\n'
           '<meta name="theme-color" content="#11162A">\n'
           f'<meta property="og:title" content="{TITLE}">\n<meta property="og:description" content="{DESC}">\n<meta property="og:type" content="website">\n'
           '<meta name="twitter:card" content="summary">\n'
           f'<link rel="icon" href="{FAVICON}">\n' + FONTS +
           '<style>[hidden]{display:none!important} img{max-width:100%} :root{padding-top:env(safe-area-inset-top,0px)}</style>\n'
           + f'<link rel="canonical" href="{SITE_URL}">\n' + style + '\n</head>\n<body>\n' + page.replace("'__BASE__'", "''") + '\n</body>\n</html>\n')
    os.makedirs(P('docs'), exist_ok=True)
    open(P('docs', 'index.html'), 'w', encoding='utf-8').write(doc)
    open(P('docs', '.nojekyll'), 'w').write('')
    # all inline scripts, for a syntax check with `node --check`
    open(P('build_check.js'), 'w', encoding='utf-8').write('\n;\n'.join(re.findall(r'<script>(.*?)</script>', page, re.S)))
    n = gamepages.build(SITE_URL)
    print(f'{n} game pages · docs/index.html {len(doc):,} bytes · pocket-protector.html {len(frag):,} bytes')


if __name__ == '__main__':
    main()
