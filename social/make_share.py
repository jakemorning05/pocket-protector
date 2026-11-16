"""Link-preview image for the site (docs/share.png, 1200x630, used by og:image / twitter:image) and the phone home-screen
icon (docs/apple-touch-icon.png, 180x180). Evergreen on purpose: X and iMessage cache these, so no records or dates.
Usage: python3 social/make_share.py"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tiktok'))
import make_slides as M

DOCS = os.path.join(M.ROOT, 'docs')
CSS = '''
*{box-sizing:border-box;margin:0;padding:0} body{background:#0D1120;font-family:Inter,sans-serif;color:#F2F4FF;-webkit-font-smoothing:antialiased}
.card{position:relative;width:1200px;height:630px;background:#0D1120;padding:0 80px;overflow:hidden;display:flex;flex-direction:column;justify-content:center}
.card::before{content:"";position:absolute;width:820px;height:820px;border-radius:50%;right:-300px;top:-380px;background:radial-gradient(circle,#FFD23F,transparent 65%);opacity:.16}
.card::after{content:"";position:absolute;width:700px;height:700px;border-radius:50%;left:-360px;bottom:-460px;background:radial-gradient(circle,#4DA3FF,transparent 65%);opacity:.14}
.card>*{position:relative;z-index:1}
.brand{display:flex;align-items:center;gap:22px}.brand svg{width:104px;height:104px}
.word{font-family:'Inter Display';font-weight:900;font-size:84px;letter-spacing:-.035em;line-height:1}.word b{color:#FFD23F}
h1{font-family:'Inter Display';font-weight:800;font-size:54px;letter-spacing:-.025em;line-height:1.1;margin-top:50px;max-width:900px}
.pills{display:flex;gap:14px;margin-top:40px}
.pill{font-size:26px;font-weight:700;padding:12px 24px;border-radius:999px;background:#161C34;border:2px solid #252D50;color:#B9C1DF}
.pill i{display:inline-block;width:14px;height:14px;border-radius:50%;margin-right:12px;background:var(--c)}
.icon{width:180px;height:180px;background:#0D1120;display:grid;place-items:center}.icon svg{width:132px;height:132px}
'''
card = f'''<div class="card" id="card"><div class="brand">{M.LOGO}<span class="word">Pocket <b>Protector</b></span></div>
  <h1>NFL picks, pool tools and fantasy projections, by the numbers.</h1>
  <div class="pills"><span class="pill" style="--c:#FF5D8F"><i></i>Game picks</span><span class="pill" style="--c:#3DDC97"><i></i>Pick’em &amp; survivor</span>
  <span class="pill" style="--c:#4DA3FF"><i></i>Fantasy rankings</span></div></div>
<div class="icon" id="icon">{M.LOGO}</div>'''
html = f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{card}</body></html>'
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'share.html')
open(out, 'w').write(html)
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1200, 'height': 900}, device_scale_factor=1)
    pg.goto('file://' + out); pg.evaluate('() => document.fonts.ready')
    pg.locator('#card').screenshot(path=os.path.join(DOCS, 'share.png'))
    pg.locator('#icon').screenshot(path=os.path.join(DOCS, 'apple-touch-icon.png'))
    b.close()
os.remove(out)
print('wrote docs/share.png and docs/apple-touch-icon.png')
