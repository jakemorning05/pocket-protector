# TikTok slideshows

1080×1920 PNG carousels in the site's style. Built from the site's own numbers, so rebuild the site first.

1. `node export_buy_sell.js` and/or `node export_waiver.js`: read the built page (docs/index.html) and write mkt.json / waiv.json here.
2. Edit the player lists and the 2–3 sentences in `make_slides.py` (buy low / sell high), `make_slides2.py` (a second set
   that reuses the same layout) or `make_waiver.py` (waivers; roster % comes from Yahoo's waiver articles). Every sentence
   should come from real stats; the scripts only render.
3. `python3 make_slides.py` (or the others; `make_startsit.py` does a weekly start/sit set from data/fantasy.json). PNGs land in png/, part2/ or waiver/ here (git-ignored).

TikTok rules learned the hard way (a slideshow was removed for "community guidelines"):
- No web address on the slides. Name and logo only, "link in bio". The bio link should go to the site's #fantasy tab.
- Keep the account fantasy-only: no betting lines, Kalshi, odds or "picks/locks/parlay" wording in slides or captions.
- Keep text out of the bottom ~320 px and the right ~140 px (TikTok's buttons and caption).
