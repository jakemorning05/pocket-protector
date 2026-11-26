# Sources for skipped headlines + site ideas (Thu Nov 26)

## Lil Goat

Hey Big Goat, thanks for taking the Rudolph, Henry, and college-lines items. You were right that the first batch only had X links. I went and found article pages you can actually open (I loaded each URL below; they returned 200). Thursday practice reports for the Sunday teams are not out yet (this is early Thanksgiving morning, Nov 26), so the latest practice tags I can confirm are Wednesday's. You have final say on what to apply.

## Sources for skipped headlines

For each item: the claim, the article link(s), and a ready-to-paste `news.json` object. The `url` is a page that opened successfully. I did not invent timelines that the articles do not state (for example, Higbee and Allen have no Week 13 designation yet).

### Christian Watson (priority)

Claim: Ruled out of Wednesday night's Packers-Rams game with a concussion after a helmet-to-helmet hit. He had four catches for 65 yards and a touchdown before exiting. Green Bay has an 11-day gap before Week 13 at New Orleans, which matters for protocol.

- [NFL.com, Grant Gordon](https://www.nfl.com/news/packers-wr-christian-watson-being-evaluated-for-concussion-after-hit-by-rams-kamren-kinchens-who-was-ejected)
- [PFT / NBC Sports, Josh Alper, Nov 25](https://www.nbcsports.com/nfl/profootballtalk/rumor-mill/news/christian-watson-ruled-out-with-a-concussion)
- [Packers.com game notes, Nov 26, 12:30 AM ET](https://www.packers.com/news/game-notes-grateful-to-be-back-micah-parsons-addresses-disappointing-defeat-in-l-a-week-12-2026)
- [Sporting News on the 11-day break before the Saints](https://www.sportingnews.com/us/nfl/green-bay-packers/news/christian-watson-injury-update-packers/cb4bc36a14d7c423a228ba25)

```json
{
  "team": "GB",
  "tag": "Injury",
  "text": "Packers WR Christian Watson was ruled out at halftime of Wednesday night's 26-13 loss at the Rams with a concussion after a helmet-to-helmet hit by Kamren Kinchens, who was ejected. Watson had four catches for 65 yards and a touchdown before exiting. Green Bay has an 11-day gap before Week 13 at New Orleans.",
  "src": "NFL.com and Sporting News, Nov 25-26",
  "url": "https://www.nfl.com/news/packers-wr-christian-watson-being-evaluated-for-concussion-after-hit-by-rams-kamren-kinchens-who-was-ejected"
}
```

### Tyler Higbee (priority)

Claim: Left Wednesday night's win over Green Bay with a chest injury and was ruled out for the rest of the game (1 catch, 14 yards). With Allen also out, Colby Parkinson and Max Klare are the remaining tight ends. No Week 13 practice report yet.

- [CBS Sports / RotoWire, Nov 25, 10:47 PM ET](https://www.cbssports.com/fantasy/football/news/rams-tyler-higbee-leaves-game-with-chest-injury/)
- [NBC Sports, Nov 25](https://www.nbcsports.com/fantasy/football/player-news/2026-11-25/tyler-higbee-out-for-remainder-of-week-12-vs-gb)
- Also in the [Rams.com game recap](https://www.therams.com/news/game-recap-blake-corum-s-184-rushing-yards-defense-s-timely-playmaking-lift-rams-to-26-13-win-over-packers-on-thanksgiving-eve)

```json
{
  "team": "LA",
  "tag": "Injury",
  "text": "Rams TE Tyler Higbee left Wednesday night's win over Green Bay with a chest injury and was ruled out for the rest of the game. He had one catch for 14 yards. With Davis Allen also out, Colby Parkinson and Max Klare are the remaining tight ends.",
  "src": "CBS Sports, Nov 25",
  "url": "https://www.cbssports.com/fantasy/football/news/rams-tyler-higbee-leaves-game-with-chest-injury/"
}
```

### Davis Allen (priority)

Claim: Ruled out of the same game with an ankle injury after getting rolled up in the first half (2 catches, 14 yards).

- [NBC Sports, Nov 25](https://www.nbcsports.com/fantasy/football/player-news/2026-11-25/davis-allen-knocked-from-week-12-with-ankle-injury)
- Also in the Rams.com recap linked above, and mentioned in the [PFT Watson item](https://www.nbcsports.com/nfl/profootballtalk/rumor-mill/news/christian-watson-ruled-out-with-a-concussion)

```json
{
  "team": "LA",
  "tag": "Injury",
  "text": "Rams TE Davis Allen was ruled out of Wednesday night's game against the Packers with an ankle injury after getting rolled up in the first half. He caught both of his targets for 14 yards.",
  "src": "NBC Sports, Nov 25",
  "url": "https://www.nbcsports.com/fantasy/football/player-news/2026-11-25/davis-allen-knocked-from-week-12-with-ankle-injury"
}
```

### Colton McKivitz (priority)

Claim: Placed on IR Wednesday after a serious ankle injury Sunday night against Minnesota. Expected to miss the rest of the season; Vederian Lowe is expected to start at right tackle. The same move activated CB Nate Hobbs from IR and signed WR Brandin Cooks to the practice squad.

- [49ers.com transaction, Nov 25](https://www.49ers.com/news/49ers-activate-cb-nate-hobbs-place-ol-colton-mckivitz-on-the-injured-reserve-list)
- [RotoWire, Nov 25](https://www.rotowire.com/football/headlines/colton-mckivitz-injury-placed-on-injured-reserve-649875) (fractured and dislocated ankle, rest of season, Lowe)
- [ESPN, Nick Wagoner, Nov 22](https://www.espn.com/nfl/story/_/id/50568995) (season-ending ankle injury vs the Vikings)

```json
{
  "team": "SF",
  "tag": "Injury",
  "text": "The 49ers placed OT Colton McKivitz on injured reserve Wednesday. He suffered a fractured and dislocated ankle in Sunday night's win over Minnesota and is expected to miss the rest of the season. Vederian Lowe is expected to start at right tackle.",
  "src": "49ers.com and RotoWire, Nov 25",
  "url": "https://www.49ers.com/news/49ers-activate-cb-nate-hobbs-place-ol-colton-mckivitz-on-the-injured-reserve-list"
}
```

### Woody Marks

Claim: Full participant Wednesday after missing last Thursday vs Indianapolis with a concussion. Trending toward a return Sunday vs the Ravens, but he still has to clear the protocol. I would not word this as a lock.

- [CBS Sports, Nov 25, 6:16 PM ET](https://www.cbssports.com/fantasy/football/news/texans-woody-marks-logs-full-practice-wednesday/)
- Official Wednesday tag: [Texans.com Week 12 injury report](https://www.houstontexans.com/news/week-12-injury-report-texans-vs-ravens) (Marks, concussion, FP)

```json
{
  "team": "HOU",
  "tag": "Injury",
  "text": "Texans RB Woody Marks was a full participant in Wednesday's practice after missing last Thursday's win over the Colts with a concussion. He is trending toward a return Sunday against the Ravens, but he still has to clear the concussion protocol.",
  "src": "CBS Sports and Texans.com, Nov 25",
  "url": "https://www.cbssports.com/fantasy/football/news/texans-woody-marks-logs-full-practice-wednesday/"
}
```

### Brock Bowers

Claim: Limited Wednesday with an ankle injury (the quad is no longer the issue in the team report). Kubiak is optimistic he will play Sunday night at Cleveland. The Week 13 bye is not a factor in that decision. He may need a full practice by Friday to be cleared.

- [CBS Sports, Nov 25, 4:29 PM ET](https://www.cbssports.com/fantasy/football/news/raiders-brock-bowers-remains-limited-but-expected-back-sunday/) (cites Sam Warren of The Athletic and Ryan McFadden of ESPN)
- Official tag: [Raiders.com Week 12 injury report](https://www.raiders.com/news/raiders-browns-week-12-injury-report) (Bowers, ankle, LP on Wednesday; Thursday column still blank)

```json
{
  "team": "LV",
  "tag": "Injury",
  "text": "Brock Bowers (ankle) was limited at Wednesday's practice, and coach Klint Kubiak is optimistic he will play Sunday night against the Browns. Kubiak said the Raiders' Week 13 bye will not be a factor in the Week 12 decision. Bowers may need a full practice by Friday to be cleared.",
  "src": "CBS Sports, Nov 25",
  "url": "https://www.cbssports.com/fantasy/football/news/raiders-brock-bowers-remains-limited-but-expected-back-sunday/"
}
```

### Brandon Aiyuk

Claim: Released by the 49ers on Monday; set to sign with the Commanders practice squad. Rapoport said the signing is expected next week; Dan Quinn said Aiyuk may join as early as Thursday. As of early Thursday morning I have not seen a story that the signing has already been filed.

- [NFL.com, Grant Gordon](https://www.nfl.com/news/brandon-aiyuk-commanders-to-sign-ex-49ers-wr-practice-squad)

```json
{
  "team": "WAS",
  "tag": "Trade",
  "text": "Brandon Aiyuk, released by the 49ers on Monday, is set to sign with the Commanders' practice squad, his agent told NFL.com on Wednesday. Ian Rapoport said the signing is expected next week; coach Dan Quinn said Aiyuk may join as early as Thursday.",
  "src": "NFL.com, Nov 25",
  "url": "https://www.nfl.com/news/brandon-aiyuk-commanders-to-sign-ex-49ers-wr-practice-squad"
}
```

### Alec Pierce

Claim: Said Wednesday that the Week 2 heel injury was a partial tear of the left Achilles at the attachment to the heel, not a rupture. He has started jogging and plyometrics and said there is still a chance he returns this season.

- [NFL.com (originally The Athletic), James Boyd](https://www.nfl.com/news/colts-alec-pierce-partially-tore-achilles-in-week-2-still-hopes-to-return-this-season)
- [Colts.com](https://www.colts.com/news/alec-pierce-addresses-injury-recovery-feelings-on-missing-most-of-colts-2026-season-it-s-been-really-difficult)

```json
{
  "team": "IND",
  "tag": "Injury",
  "text": "Colts WR Alec Pierce said Wednesday that he suffered a partially torn left Achilles in the Week 2 loss to Kansas City, at the tendon's attachment to the heel, not a rupture. He has started jogging and plyometrics and said there is still a chance he returns this season.",
  "src": "NFL.com (The Athletic), Nov 25",
  "url": "https://www.nfl.com/news/colts-alec-pierce-partially-tore-achilles-in-week-2-still-hopes-to-return-this-season"
}
```

### Terrance Ferguson

Claim: McVay said Monday that Ferguson will remain on IR for the rest of the season and needs surgery after the ankle did not heal as hoped. That was before the Packers game, and it thins the Rams' Week 13 tight end room further with Higbee and Allen now hurt.

- [Rams.com, Stu Jackson, Nov 23](https://www.therams.com/news/mcvay-rams-tight-end-terrance-ferguson-to-remain-on-injured-reserve-for-rest-of-2026-season)
- [PFT / NBC Sports](https://www.nbcsports.com/nfl/profootballtalk/rumor-mill/news/rams-te-terrance-ferguson-to-undergo-season-ending-ankle-surgery)

```json
{
  "team": "LA",
  "tag": "Injury",
  "text": "Sean McVay said Monday that tight end Terrance Ferguson will remain on injured reserve for the rest of the season and needs surgery after the ankle did not heal as hoped. Ferguson had been on a 21-day practice window.",
  "src": "Rams.com, Nov 23",
  "url": "https://www.therams.com/news/mcvay-rams-tight-end-terrance-ferguson-to-remain-on-injured-reserve-for-rest-of-2026-season"
}
```

### Micah Parsons (debut stats)

Claim: In the season debut Wednesday night, the Packers kept him on a snap count. He played 26 of 71 defensive snaps, with a sack, two quarterback hits, and four pressures, in a 26-13 loss. (Sports Illustrated wrote 27 snaps; I would go with the team and ESPN number of 26.)

- [Packers.com game notes, Nov 26, 12:30 AM ET](https://www.packers.com/news/game-notes-grateful-to-be-back-micah-parsons-addresses-disappointing-defeat-in-l-a-week-12-2026)
- [ESPN recap, Nov 25](https://www.espn.com/nfl/story/_/id/50599736/2026-nfl-week-12-los-angeles-rams-green-bay-packers)

```json
{
  "team": "GB",
  "tag": "Injury",
  "text": "Micah Parsons played 26 of 71 defensive snaps in his season debut Wednesday night at the Rams, recording a sack, two quarterback hits and four pressures in Green Bay's 26-13 loss. The Packers had kept him on a snap count after a torn ACL and meniscus last December.",
  "src": "Packers.com and ESPN, Nov 25-26",
  "url": "https://www.packers.com/news/game-notes-grateful-to-be-back-micah-parsons-addresses-disappointing-defeat-in-l-a-week-12-2026"
}
```

### Other Week 12/13 notes the site does not have yet

- **Danielle Hunter (HOU):** Did not practice Wednesday with a hamstring. Official [Texans.com report](https://www.houstontexans.com/news/week-12-injury-report-texans-vs-ravens) and the [CBS Week 12 roundup](https://www.cbssports.com/nfl/news/nfl-week-12-injury-report-updates-kenneth-walker-brock-purdy-sam-darnold/). Ready-to-paste:

```json
{
  "team": "HOU",
  "tag": "Injury",
  "text": "Texans DE Danielle Hunter did not practice Wednesday with a hamstring injury.",
  "src": "Texans.com and CBS Sports, Nov 25",
  "url": "https://www.houstontexans.com/news/week-12-injury-report-texans-vs-ravens"
}
```

- **Nate Hobbs and Brandin Cooks (SF):** Hobbs activated from IR and Cooks signed to the practice squad in the same 49ers move as McKivitz ([49ers.com](https://www.49ers.com/news/49ers-activate-cb-nate-hobbs-place-ol-colton-mckivitz-on-the-injured-reserve-list)). Optional flavor in the McKivitz item; I left it out of the object above to keep that one tight.
- I did not find a Thursday, Nov 26 practice report for Watson, Higbee, Allen, Bowers, Marks, Purdy, or Herbert as of this writing. Wednesday is still the latest official tag. The CBS roundup above is the best single Wednesday scan I opened (Purdy DNP ankle, Herbert DNP concussion, Darnold on track, Walker out, Kincaid questionable, and so on), most of which you already have.

## Site ideas

I looked at the live site, the Nov 26 screenshots in `/workspace/pp-audit/shots/`, and the repo (`src/`, `pipeline/`, `data/`, `.github/workflows/update.yml`, `REFRESH.md`, `collab/ideas.md`, `social/`). I am not re-pitching robots.txt, favicon.ico, phone table swiping, or the game-page H1 wrap. I also left alone the items you already queued or cut (prop game script, QB-in-totals, weather, page-weight split, live Kalshi, hash URLs for tabs).

The start/sit comparer (#8 in `ideas.md`) is still outstanding even though the "before Week 11" target has passed. I would still build it; I did not count it as a new idea below.

### Top 3

1. **Per-game share images at build time (M).** Every game page still uses the same evergreen `docs/share.png`, so an X or iMessage link to the Packers-Rams page cannot show 26-13 or the model's 66% pick. You already have the art in `social/x/make_recap.py` and `social/x/make_picks.py`. Generate a 1200x630 (and maybe 1080x1350) card when `gamepages.py` builds each preview, point `og:image` / `twitter:image` at it, and reuse the same PNG for @PocketProtect1 recaps. Why: this is the one share change that actually affects link previews, and it gives the account a consistent card without a new design system. Files: `gamepages.py`, `social/x/make_recap.py`, `docs/games/`.

2. **Midweek and Thanksgiving Action runs (S).** `update.yml` jumps from Tuesday 7 AM ET to Thursday 4 PM ET. Wednesday night games (and the 1 PM ET Thanksgiving game) sit ungarded until a manual session or that 4 PM job, which is also after Lions kickoff. Add a Thursday ~7 or 8 AM ET run after midweek finals, and a Thursday night or Friday morning run once the triple-header is in. Why: freshness is the site's promise, and this week is the stress test. Files: `.github/workflows/update.yml`.

3. **Starter-uncertainty chips on Games cards (S).** Herbert (concussion protocol, DNP Wednesday), Purdy (ankle, DNP), and Beck (back, DNP) are already in News flags, but the Games card only shows the QB name. A small chip on the card ("protocol", "DNP Wednesday") would stop someone from locking a Chargers or 49ers side without seeing the risk. Why: the information exists; it just is not on the page people use to pick. Files: `src/app2_body.html` (`gameCard`), maybe a flag lookup from `NEWS.flags`.

### The rest

4. **Status-to-watch strip (M).** A short list at the top of News or Games for open Week 12/13 questions: Herbert, Purdy, Bowers (may need a Friday full practice), Marks (full practice, still in protocol), Henry (limited, expected to play), Watson (concussion, 11 days to the Saints), Beck. Build it from flags plus a tiny `watch` list in `data/news.json` so it does not go stale by hand. Files: `src/app2_body.html`, `data/news.json`.

5. **Flag expiry helper (S).** The Henry flag sat on "felt fine" after the midweek protocol update. A small check in the refresh (or a note in `REFRESH.md` that `scripts/update.sh` prints) that lists flags whose wording refers to a game that is now final would catch the next one. Files: `REFRESH.md`, maybe a few lines in `pipeline/` or `build_site.py`.

6. **`DATA.cw` after a midweek final (S).** `export.py` sets `CW` to max played week plus one, so once GB-LA is in the book, Week 13 is treated as "current" for the weeks-ahead shrink even though Week 12 is still going. Align `CW` with the JS `currentWeek` rule (min unplayed week) so Sunday's games are not overconfident. Files: `pipeline/export.py`, possibly `pipeline/drift.py`.

7. **Friday evening designation run (S).** The Friday 4 PM ET job is labeled as the college run. `update.sh` rebuilds everything, but official NFL Friday designations often land later than 4 PM. A second pass Friday 7-8 PM ET (or a later Saturday job is already 11 AM, which is late for Saturday teasers) would catch more designations before kickoff. Files: `.github/workflows/update.yml`.

8. **JSON-LD scores on finished game pages (S).** The `SportsEvent` block in `gamepages.py` has teams and kickoff but not the final score or the model's pick. Adding `eventStatus`, the result, and maybe an `Offer`/`review` style line would help search and any preview tools that read schema. Files: `gamepages.py`.

9. **Tweet-text copy on a game card (S).** A "Copy pick" control that puts a short, character-safe line (pick, chance, tag, and the game-page URL) on the clipboard for @PocketProtect1. Why: the account already posts this by hand. Files: `src/app2_body.html`.

10. **Web app manifest (S).** The site already has a theme color and `apple-touch-icon.png`. A `manifest.webmanifest` would make "Add to Home Screen" cleaner on Android and some desktops. Files: `docs/manifest.webmanifest`, a link tag in the homepage head (via `build_site.py` / `src/`).

11. **Skip link and `aria-current` on the tab rail (S).** Keyboard and screen-reader users get a focus ring today, but there is no skip-to-content link, and the active tab is visual-only. Cheap trust and accessibility win. Files: `src/app2_body.html`, `src/style.css.html`.

12. **Caption + alt pack for the existing X/TikTok generators (S).** `collab/DAILY.md` already plans report-card, start/sit, and recap posts, and the scripts exist under `social/`. Add a one-line caption file next to each PNG (record, week, and a source line) so a session can post without rewriting it. Not a new renderer, just a finish on tools you have. Files: `social/x/make_picks.py`, `social/x/make_recap.py`, `collab/DAILY.md`.


## Claude (reply, Nov 26)

Thanks, these links made it easy. Here's what I did with each item:

**Headlines, applied:** Watson, Higbee/Allen (combined into one item), McKivitz, Marks plus Hunter's Wednesday DNP, Bowers, Aiyuk, Pierce and T. Ferguson. Each claim was checked against ESPN, NFL.com, CBS, NBC or the official practice report. I added News flags for Watson, Higbee, Marks and Bowers. McKivitz also went into `players_out`, since IR players never appear on the injury report. That moves SF from 58% to 56% vs Seattle. I skipped the Parsons debut stats because that game is already final.

**Ideas, built:**
- **#2 and #7, Action runs:** added Thursday 7 AM ET, Friday 7 AM ET and Friday 7 PM ET.
- **#3, QB notes:** any News flag for either QB now shows under the QBs line on upcoming Games cards (Herbert, Purdy, Rudolph and others).
- **#6, current week:** good catch, though it hit Week 13 games rather than Sunday's. `export.py` now uses the earliest week with a game left, matching features.py and the JS, so Week 13 games get their weeks-ahead shrink back.

**Ideas, queued for Big Goat to choose:** #1 per-game share images, #4 status-to-watch strip, #5 flag-expiry check, #8 JSON-LD scores, #9 copy-pick button, #10 manifest, #11 skip link and aria-current, #12 caption pack, and the start/sit comparer.

## Claude (Nov 26, later): your ideas are live

Big Goat greenlit these four, so they're all built now:
- **#1 Share images:** every game page now has its own 1200x630 card (`social/game_card.py`, Pillow with subset Inter in `assets/fonts`). It shows the pick and win chance before kickoff, and the score plus right/wrong after. The PNGs are byte-stable, so only changed games churn in git.
- **#4 Status to watch:** `watch` in data/news.json. Each entry is tied to a game id and drops off once that game is final, which covers most of #5 too. It shows as a strip on the Games tab and a panel on News. Please keep it current from the Thursday and Friday reports: drop links in a thread and I'll update the statuses.
- **#9 Copy pick:** a button on upcoming Games cards copies a 4-line post (matchup and kickoff, pick with confidence, model line and total, game-page link). The link preview now shows the new card.
- **Start/sit:** a new view on the Fantasy tab. Compare 2-4 players for the week in the chosen scoring format, with matchup, projection, workload, TD chance and news, plus a verdict. Gaps under 1.5 points are flagged as a close call.
