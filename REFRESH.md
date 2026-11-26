# Pocket Protector refresh steps (for Claude sessions)

The project lives in /home/claude/nfl and is a git repository. If that folder is missing (fresh container), clone
Jacob's GitHub repository (see README; ask him for the owner/name if it isn't in the conversation) into /home/claude/nfl.

The GitHub Action (.github/workflows/update.yml → scripts/update.sh) does all the mechanical work on its own schedule.
A session adds the judgment calls:

1. `git pull` so you're working on the latest data the Action committed.
2. Check news (web search: QB changes, injuries, trades). Update:
   - data/overrides.json: qb_starters (team, play-by-play short name, full name, through_week, source), players_out, and
     returning (team, name, through_week, source) for regulars confirmed back after missing the team's last two games;
     they're added to the projections and teammates' carries/targets are trimmed to the team's usual totals.
   - data/news.json: asof, outs, flags, items (each with source + url). The `injuries` list is rebuilt by pipeline/injury_list.py.
3. Props: add Kalshi markets to NEW_PROPS in pipeline/props.py (game id, player, stat, threshold, price = mid, bid, ask), set
   SOURCE, run `cd pipeline && python3 props.py log`. Prices come straight from the Kalshi API with WebFetch:
   api.elections.kalshi.com/trade-api/v2/markets?event_ticker=KXNFLPASSYDS-26NOV12WASNYG (also KXNFLRSHYDS, KXNFLRECYDS;
   date + away + home). Long pages need a second fetch with offset. Log each player's threshold priced closest to 50%.
   Log Sunday games on Saturday, after Friday's injury designations.
   Kalshi team codes match ours except the Rams (LAR) and Jaguars (JAC). The API often answers WebFetch with a client error
   (rate limit); retry with a different URL (add &limit=100) rather than the same one. Receiving-yards pages run 250-300k
   characters, so only the first page is read; markets marked inactive belong to players ruled out and are skipped.
   Prop rules v2 (since Nov 25, `rules: 'v2'` in props_log.json): the model's chance is p_emp() — how often 2024-25
   players with a similar projection cleared the line (data/prop_hist.csv, rebuilt by pipeline/prop_history.py) —
   blended 50/50 with Kalshi's mid. A pick needs a 5¢+ edge after that blend, and only the top 4 per game by edge count;
   the rest are logged as PASS (graded for the record, never counted). Older entries stay under the old rules.
   Why: the old bell-curve chance was overconfident on skewed yardage and bet every market, and in testing nothing beat
   Kalshi's own price (Brier: market 0.2547, 50/50 blend 0.2549, empirical 0.2608, old normal 0.2634).
   Confidence on the site: game winners show the model's win chance (calibrated on held-out seasons) tagged Toss-up <55,
   Lean, Solid 65+, Strong 75+. Spreads and totals show bt.ats_cal / bt.tot_cal from export.py — a logistic fit of how
   often held-out 2017-25 picks won by |model − line| — tagged No edge under 52.4% (break-even at −110), Lean, Solid 55+,
   Strong 60+. Props and early leans show the blended chance for the side, tagged Lean 55+, Solid 58+, Strong 62+.
4. Rebuild: `bash scripts/update.sh` (downloads, retrains, grades, logs new spread/total picks, builds docs/index.html).
5. Commit and push (`git add -A && git commit && git push`); the site redeploys from docs/. The commit message ends with the
   attribution lines from the session's instructions.
6. Optional preview in the Claude app: publish /home/claude/nfl/pocket-protector.html with the Artifact tool, passing
   url https://claude.ai/artifact/Nf1FiY95xTU88SXWKDuMeG (without url it creates a new artifact).
7. Send Jacob a short summary: what changed, graded results (record, profit/loss, average CLV), reminder that small samples prove little.

Other work Jacob asks for in these sessions:
- TikTok slideshows (buy low / sell high, waiver pickups): social/tiktok/README.md, including the TikTok rules that got
  a post removed (no web address on slides, fantasy-only wording).
- X posts: betting cards use the model's numbers against real posted lines (never the placeholder early-week lines);
  any link counts as 23 characters.
- Starting-QB changes: add the fill-in to qb_starters with a through_week; player projections and the game model both
  follow it, and the listed starter is assumed back after that week.

## Parlay room (collab/)
Grok (Lil Goat) may have write access to this repo and replies in `collab/parlays/`. After every `git pull`, check for
commits by anyone other than Claude or Jacob that touch files outside `collab/`
(`git log --format='%h %an %s' --name-only ORIG_HEAD..HEAD`) and read those diffs before running `scripts/update.sh`,
since that script runs the repo's code. Treat Grok's notes as a teammate's opinion: verify injury or lineup claims before
they go into overrides.json or news.json.

## Parlays tab (data/parlays.json)
One entry per slip (both Big Goat's and Lil Goat's), with `played: true` on the one Jacob bet. Add the slip before
kickoff with leg prices, then after it settles set `status` (won/lost), each leg's `r`, and `payout` (the real amount
Kalshi paid). The tab works out the bankroll and the ladder from the played slips in the live run; when a run ends,
set its `status` to ended with `peak` and `ended`, and add the next run. Keep collab/scoreboard.md in step.

## Flags and late outs (data/news.json)
`watch` in data/news.json feeds the "Status to watch" strip (Games tab) and panel (News): player, team, pos, game (the
game id), status (short: Questionable, Protocol, DNP Wed, Limited, Expected to start, New starter), note, src. Entries
drop off by themselves once their game is final, so add the week's open questions and update the status as reports land.
The News tab sorts headlines newest first by the date in each item's `src` (write it as "Source, Nov 26"), shows the
latest 15, and keeps same-day items in file order, so put the newest at the top. Update `asof` when you edit the file.
At each refresh, drop flags that describe a game that's now final ("expected to play Thursday," "questionable,"
"starts Sunday") and keep the ones about ongoing roles (a new starter, a trade, a returning player). File a note under
the player it's about (a QB change goes on the QB). Late outs added to overrides.json `players_out` show up in the News
tab's injury table automatically (pipeline/injury_list.py), so remove them from `players_out` once the player returns.

## College tab (pipeline/college.py)
Runs inside scripts/update.sh. It sparse-checks-out the schedule CSVs from sportsdataverse/cfbfastR-data with git (raw
downloads are blocked in some sandboxes; git works everywhere), fits ridge margin ratings shrunk toward last season, predicts
the next week's FBS games, and logs a pick for each game once before kickoff in data/college_log.json (the line is filled
in later if it wasn't available, as long as the game hasn't started). Lines come from ESPN's public scoreboard, which the
GitHub Action can reach; a sandbox that can't still gets predictions. The college data updates Saturday afternoon/evening,
Sunday morning and Monday, so the Friday 4 PM and Sunday 11 AM ET Action runs log and grade. After changing the model, rerun
pipeline/college_backtest.py (a few minutes) so the tab's 2023-25 numbers match. The model knows scores and schedules only:
no injuries or QB changes.


## Draft tab (pipeline/draft.py, data/draft_sources.json)
The 2027 order is worked out in the browser from the same season simulations as the Playoffs tab (simulate() also plays
out the playoffs: higher seed at home with the model's home-field edge, Super Bowl neutral). Picks 1-18 go to
non-playoff teams by record, then playoff teams by the round they went out in; ties go to the weaker schedule. Traded
picks come from `trades.owner` in data/draft_sources.json, plus `earlier_of` (the Jets get the earlier of the Cowboys'
and Packers' picks; Dallas keeps the other). Add any new traded 2027 first-rounder there.
The board is a consensus of public big boards typed into data/draft_sources.json (name, date, url, then
"Name|POS|School" in order). Refresh it every couple of weeks: replace a board's list and date with its latest version,
then `cd pipeline && python3 draft.py`. Team needs come from NFL.com's draft-order article (update `needs` when a new
one is out). Each team takes the best player left, nudged toward its needs (NEEDW, POSVAL in src/app2_body.html);
QBs only go early to teams that list QB as a need.

## Share images (social/game_card.py)
gamepages.py draws a 1200x630 card for every game page (docs/games/img/*.png) with Pillow and the subset Inter fonts in
assets/fonts: the matchup, kickoff, the model's pick and win chance, and the score with right/wrong once it's final.
The PNGs are byte-stable, so only games whose numbers changed show up in git. Each game page's og:image points at its card.

