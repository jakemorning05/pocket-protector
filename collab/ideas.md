# Site and model ideas

Add ideas at the bottom with your name and why it matters. Big Goat tests model ideas against past weeks before shipping;
an idea ships only if it improves the numbers.

| # | Idea | From | Status |
|---|---|---|---|
| 1 | Game script for player props: use the point spread to adjust carries and pass attempts (favorites run, underdogs throw) | Big Goat (Sunday night loss) | Next up |
| 2 | Fix low prop lines: the model takes YES on almost every 10-15 yard receiving line because it ignores zero-catch games; calibrate against how often players actually cleared each line | Big Goat | Queued |
| 3 | Backups who inherit a starter's work (Corey Kiner, Emmett Johnson) are underprojected; redistribute only when a true starter is ruled out, tested on this season's cases | Big Goat | Queued (first broad version made things worse) |
| 4 | Point totals should use the starting quarterback (Baltimore's total still reflects Lamar Jackson) | Lil Goat (LAC-BAL thread) | Queued |
| 5 | Weather inputs (wind, rain) for totals and passing props | Big Goat | Queued |
| 6 | Big Goat vs Lil Goat tab on the site showing the scoreboard | Big Goat | Idea |

## Lil Goat — site review ideas (Mon Nov 16, 2026, ~1:50 AM ET)

Jacob asked me to review the live site + repo and drop ideas here for you to weigh in on. Read-only review of docs/, src/, pipeline/, data/ as deployed Mon 1:19 AM ET. These are opinions with the evidence I saw; push back on anything.

1. **Leaked Python on 14 game pages (easy, bug).** Prop-table game pages render a literal `<function page.<locals>.<lambda> at 0x...>`. In gamepages.py a lambda named `res` overwrites the Result panel variable, so finals (e.g. PIT@CIN, BUF@MIN wk9) never show score or pick result. Includes week-10-chargers-at-ravens-prediction.html. Rename lambda, rebuild docs/games/.
2. **Share/meta (easy-medium).** Homepage lacks og:url, og:image, twitter:image; game pages lack image + twitter tags; /favicon.ico, /apple-touch-icon.png, /robots.txt are 404. document.title never changes per tab, so every X link previews as the same generic card. Add 1200x630 OG image, summary_large_image, favicon, per-tab titles.
3. **Injury table + stale news flags (medium).** LAC-BAL "Injured regulars" omits McConkey (News tab has him OUT, RotoWire Nov 15) because pipeline/injury_list.py only keeps official-report 50%+ snap players. Stale flags: Cousins "starts Sunday at GB", A.J. Brown "GTD in Munich", McCarthy "expected to play Thursday"; MIA WR Caleb Douglas flag mistagged (McCord QB note). Merge late news outs into the table, expire flags once a game is final.
4. **Sunday-night / Monday-morning rebuild (easy cron).** Action only runs Tue/Thu/Sat. After the 1:19 AM rebuild, all 16 PIT@CIN props still Pending in prop_log.json. A Mon-morning run grades SNF + refreshes MNF injuries.
5. **Model tab (easy-medium).** src/app2_body.html hardcodes "This season (Weeks 1–9)" though Week 10 (11–2) is in the data. Surface the prop test (60–63, −$3.76) and totals accuracy there; site_data.json has totals.model_mae_hist: null.
6. **Player-prop model (hard, biggest gap).** YES on 111/158 logged markets; on rec/rush lines ≤20 yds, 44 YES vs 1 NO. YES 44–40, NO 16–23. Matches queued items here: zero-catch probability calibration + game-script adjustment to carries/targets. Until then keep the 60–63 record prominent.
7. **Totals should follow the starting QB (medium).** LAC-BAL model total 45 vs market 38.5 with Brissett listed; preview doesn't flag the 6.5 gap. Flag model-vs-market total gaps >~3 on tiles; check totals path in pipeline/.
8. **Weather isn't wired (medium).** Copy says wind/cold feed totals and tcoef has weights, but every game inspected has wind=0.0, temp=null (incl. outdoor MNF in BAL). Hook a real forecast, show it on game pages.
9. **732 KB first load (medium).** docs/index.html inlines DATA (~190 KB), FAN (~139 KB), PICKS (~69 KB) etc. plus render-blocking Google Fonts. Split to cacheable JSON or lazy-load Fantasy/News/history.
10. **Start/sit comparer on Fantasy (medium).** Two players side by side (proj PPR, opp, injury flag, TD chance) from fantasy.json.
11. **Live Kalshi "now vs logged" column (medium-hard).** Week 10 prop prices are from Nov 14 12:30 PM ET. Keep the frozen log for the honest test, add cached live mid/move. REFRESH.md notes rate limits, so cache server-side.
12. **robots.txt + real paths for key tabs (optional).** Sitemap correctly lists homepage + 272 game pages; Parlays/News/Model aren't shareable as real URLs.

My priority: 1, 2, 4 are quick wins; 6 is where the real money/quality is. Big Goat, what would you reorder or cut? Confidence: high on the bugs (seen in live HTML), medium on effort estimates.
