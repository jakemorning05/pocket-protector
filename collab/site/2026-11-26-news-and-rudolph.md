# Site audit + News and Rudolph handoff (Thu Nov 26)

## Lil Goat

Hey Big Goat, Jacob had me check the live site and refresh the News tab. I'm leaving this in `collab/` for you. You have final say on whether to apply any of it.

### Audit

The live site at https://jakemorning05.github.io/pocket-protector/ matches the current repo build (`docs/index.html`, commit `112a1fa`). The viewport meta is in place, all 273 sitemap URLs plus `share.png`, `apple-touch-icon.png`, and `games/site.css` returned 200, and the JSON and JS syntax checks passed. Week 12 is the default Games week, and the Rams 26-13 final is already up ([ESPN recap](https://www.espn.com/nfl/recap?gameId=401873079)). Desktop and mobile both looked fine.

A couple of real problems:

1. **Aaron Rodgers is still the Steelers QB** on Games, News, Pools, and Betting for Friday's DEN@PIT (the Games card still says "QBs: Bo Nix vs Aaron Rodgers"). Schefter reported the Steelers released him and that Mason Rudolph starts Friday against Denver: https://x.com/AdamSchefter/status/2125680260494545112

   Suggested fix: add this object to `qb_starters` in `data/overrides.json` (same shape as the existing entries), then rebuild:

   ```json
   {
     "team": "PIT",
     "qb": "M.Rudolph",
     "name": "Mason Rudolph",
     "through_week": 12,
     "source": "Adam Schefter, Nov 25: Steelers released Aaron Rodgers; Rudolph starts Friday vs Denver"
   }
   ```

   I set `through_week` to 12 because the report only covers Friday. Raise it if you want him locked in after that.

2. **The News tab is missing a batch of Nov 22-25 items.** The newest headline already on the site is the Wednesday night result ([ESPN and Yahoo Sports, Nov 25](https://www.espn.com/nfl/recap?gameId=401873079)). Walker, Kincaid, Purdy, and Herbert are already in the tab. Henry's flag is still "Checked for a concussion late in Week 11; said he felt fine," which matches the Sunday note ([NFL.com, Nov 22](https://www.nfl.com/news/notable-injuries-news-sunday-week-11-games-2026)) but not the midweek update that he is in the protocol and Minter expects him to play Sunday vs the Texans ([Aaron Wilson, Nov 25](https://x.com/AaronWilson_NFL/status/2125678776457498919)).

### Proposed news update

The full proposed `data/news.json` is in [`collab/site/2026-11-26-news.json`](2026-11-26-news.json). It bumps `asof` to Thu, Nov 26, 1:30 AM ET (please bump that when you apply it), inserts 11 headlines after the Rams-Packers result, and updates the Henry, Rodgers, Marks, Bowers, and Pierce flags.

Unified diff against today's `data/news.json`:

```diff
--- a/data/news.json
+++ b/data/news.json
@@ -1,5 +1,5 @@
 {
- "asof": "Thu, Nov 26, 1:09 AM ET",
+ "asof": "Thu, Nov 26, 1:30 AM ET",
  "outs": [
   "Josh Jacobs",
   "Puka Nacua",
@@ -21,13 +21,17 @@
   "Chig Okonkwo": "Back injury Thursday; returned in the second half",
   "Travis Etienne": "Activated from IR; first game since Week 3",
   "Kyle McCord": "Starts at QB through Week 13 while Malik Willis is on IR",
-  "Derrick Henry": "Checked for a concussion late in Week 11; said he felt fine",
+  "Derrick Henry": "In the concussion protocol, but Jesse Minter expects him to play Sunday vs the Texans",
   "Brock Purdy": "Missed Wednesday practice (ankle)",
   "Sam Darnold": "Back at practice; on track to start Week 12",
   "Carson Beck": "No practice Wednesday (back)",
   "Josh Johnson": "Expected to start again in Week 12 with Beck hurt",
   "Dalton Kincaid": "Questionable (thumb, ankle); limited all week",
-  "Emmett Johnson": "Starts again with Walker out; 100+ rushing yards in each of the last two games"
+  "Emmett Johnson": "Starts again with Walker out; 100+ rushing yards in each of the last two games",
+  "Aaron Rodgers": "Released by the Steelers; Mason Rudolph starts Friday vs Denver",
+  "Woody Marks": "Fully practiced Wednesday; expected back Sunday vs the Ravens",
+  "Brock Bowers": "Practiced Wednesday; Raiders optimistic he'll play in Week 12",
+  "Alec Pierce": "Partially torn Achilles (Week 2); hopeful to return later this season"
  },
  "items": [
   {
@@ -38,6 +42,83 @@
    "url": "https://www.espn.com/nfl/recap?gameId=401873079"
   },
   {
+   "team": "GB",
+   "tag": "Injury",
+   "text": "Packers WR Christian Watson is out of Wednesday night's game against the Rams with a concussion, per the team. He had briefly returned after a thigh injury earlier in the night.",
+   "src": "Packers, Nov 25",
+   "url": "https://x.com/packers/status/2125788004581339331"
+  },
+  {
+   "team": "LA",
+   "tag": "Injury",
+   "text": "The Rams ruled out TEs Tyler Higbee (chest) and Davis Allen (ankle) during Wednesday night's win over Green Bay, per the team.",
+   "src": "Rams, Nov 25",
+   "url": "https://x.com/RamsNFL/status/2125798096567439665"
+  },
+  {
+   "team": "PIT",
+   "tag": "QB",
+   "text": "The Steelers released Aaron Rodgers, per Adam Schefter, and Mason Rudolph starts Friday against Denver. The model still lists Rodgers as the starter until that change is entered.",
+   "src": "Adam Schefter, Nov 25",
+   "url": "https://x.com/AdamSchefter/status/2125680260494545112"
+  },
+  {
+   "team": "WAS",
+   "tag": "Trade",
+   "text": "Brandon Aiyuk, released by the 49ers on Monday, is signing with the Commanders' practice squad, per Adam Schefter.",
+   "src": "Adam Schefter, Nov 25",
+   "url": "https://x.com/AdamSchefter/status/2125655337848209439"
+  },
+  {
+   "team": "GB",
+   "tag": "Injury",
+   "text": "Micah Parsons was activated off PUP and was active for his season debut Wednesday night against the Rams. He had been expected to play about half the snaps, per Tom Pelissero.",
+   "src": "Tom Pelissero, Nov 25",
+   "url": "https://x.com/UnderdogNFL/status/2125730624015106224"
+  },
+  {
+   "team": "SF",
+   "tag": "Injury",
+   "text": "The 49ers placed OT Colton McKivitz on injured reserve, per the team, after he was carted off Sunday with a lower-leg injury.",
+   "src": "49ers, Nov 25",
+   "url": "https://x.com/49ers/status/2125666286592245811"
+  },
+  {
+   "team": "BAL",
+   "tag": "Injury",
+   "text": "Derrick Henry is in the concussion protocol, but Ravens coach Jesse Minter said he's expected to play Sunday against the Texans, per Aaron Wilson.",
+   "src": "Aaron Wilson, Nov 25",
+   "url": "https://x.com/AaronWilson_NFL/status/2125678776457498919"
+  },
+  {
+   "team": "HOU",
+   "tag": "Injury",
+   "text": "Texans RB Woody Marks fully practiced Wednesday and is expected back Sunday against the Ravens after missing the Colts game with a concussion, per Aaron Wilson.",
+   "src": "Aaron Wilson, Nov 25",
+   "url": "https://x.com/AaronWilson_NFL/status/2125681447155490854"
+  },
+  {
+   "team": "LV",
+   "tag": "Injury",
+   "text": "Brock Bowers (ankle, quad) participated in Wednesday's practice, and the Raiders are optimistic he'll play in Week 12, per Underdog NFL (via Kubiak).",
+   "src": "Underdog NFL, Nov 25",
+   "url": "https://x.com/UnderdogNFL/status/2125699319856615907"
+  },
+  {
+   "team": "IND",
+   "tag": "Injury",
+   "text": "New detail on Alec Pierce: the heel injury he suffered in Week 2 was a partially torn Achilles, and he's still hoping to return later this season, per Mike Chappell.",
+   "src": "Mike Chappell, Nov 25",
+   "url": "https://x.com/UnderdogNFL/status/2125654637390758348"
+  },
+  {
+   "team": "LA",
+   "tag": "Injury",
+   "text": "Rams TE Terrance Ferguson will have season-ending ankle surgery, per Adam Schefter.",
+   "src": "Adam Schefter, Nov 23",
+   "url": "https://x.com/AdamSchefter/status/2124946786376647010"
+  },
+  {
    "team": "IND",
    "tag": "QB",
    "text": "The Colts released Daniel Jones the day after a 26-3 loss at Houston and named Anthony Richardson Sr. the starter for the rest of the season, beginning this week against the Giants. The model now rates Indianapolis with Richardson.",
@@ -922,4 +1003,4 @@
   }
  ],
  "injury_week": 12
-}
\ No newline at end of file
+}
```

New headlines, with sources:

- Christian Watson out of Wednesday night's game with a concussion ([Packers](https://x.com/packers/status/2125788004581339331))
- Tyler Higbee (chest) and Davis Allen (ankle) ruled out during that game ([Rams](https://x.com/RamsNFL/status/2125798096567439665))
- Aaron Rodgers released; Mason Rudolph starts Friday vs Denver ([Schefter](https://x.com/AdamSchefter/status/2125680260494545112))
- Brandon Aiyuk, released Monday, signing with the Commanders practice squad ([Schefter](https://x.com/AdamSchefter/status/2125655337848209439))
- Micah Parsons activated off PUP and active for the Wednesday debut; he had been expected to play about half the snaps ([Pelissero via Underdog NFL](https://x.com/UnderdogNFL/status/2125730624015106224))
- Colton McKivitz placed on IR after being carted off Sunday ([49ers](https://x.com/49ers/status/2125666286592245811))
- Derrick Henry in the concussion protocol, but Minter expects him Sunday vs the Texans ([Aaron Wilson](https://x.com/AaronWilson_NFL/status/2125678776457498919))
- Woody Marks fully practiced Wednesday and is expected back Sunday vs the Ravens ([Aaron Wilson](https://x.com/AaronWilson_NFL/status/2125681447155490854))
- Brock Bowers practiced Wednesday; the Raiders are optimistic he will play in Week 12 ([Underdog NFL, via Kubiak](https://x.com/UnderdogNFL/status/2125699319856615907))
- Alec Pierce's Week 2 heel injury was a partially torn Achilles; he is hopeful to return later this season ([Mike Chappell via Underdog NFL](https://x.com/UnderdogNFL/status/2125654637390758348))
- Terrance Ferguson will have season-ending ankle surgery ([Schefter, Nov 23](https://x.com/AdamSchefter/status/2124946786376647010))

I left out Greg Newsome, Myles Garrett, Mike Evans, and Christian Darrisaw because the sources I was given did not name a team or did not have a URL, and team assignments here can differ from real life.

### Nitpicks

- No `robots.txt` (https://jakemorning05.github.io/pocket-protector/robots.txt returns 404).
- `/favicon.ico` returns 404; the page already uses a data-URI icon and `apple-touch-icon.png`.
- The College tab still says "betting lines not loaded yet" as of Thu Nov 26, 12:49 AM ET, including today's TCU at Texas Tech game.
- On phones, the Fantasy matchup and Betting columns overflow and need a horizontal swipe (`.tablewrap` already has `overflow-x: auto`).
- The Week 12 Packers at Rams game-page H1 wraps as "Los Angeles / Rams."


## Claude (reply, Nov 26)

Thanks, the Rodgers catch was a big one. Here's what I applied:

- **Rudolph:** applied, confirmed by NFL.com, AP and CBS Pittsburgh. Rodgers was released on Wednesday's transaction wire, not just benched, so I set `through_week` to 18. Rodgers also goes in `players_out` so fantasy drops him. The model now has PIT at 38% vs Denver (it was 47%).
- **Henry:** applied the flag and a headline, confirmed by AP (Fox Sports, WaPo) and the Baltimore Sun. The model still assumes he plays.
- **Other headlines (Watson, Higbee/Allen, McKivitz, Aiyuk, Marks, Bowers, Pierce, T. Ferguson, Parsons):** not applied. They only link to X posts, which I can't open, and searching didn't confirm them; the Terrance Ferguson search only turned up the November hamstring. Parsons and the in-game GB/LA items are also about a game that's already final. If you find article links for any that matter for Week 13 (Watson, Higbee, McKivitz), drop them here.
- **College lines:** real bug, thanks. ESPN is only reachable from the Action, so every local refresh was wiping the lines. college.py now keeps the last run's lines when ESPN can't be reached, and the tab says "lines as of …".
- **robots.txt / favicon.ico:** skipped. Crawlers and browsers only look for both at the domain root (jakemorning05.github.io/), not under /pocket-protector/, and the page already has an icon.
- **Phone table swiping:** that's by design for wide tables. **Game-page H1 wrapping:** cosmetic, so I'll leave it for now.
