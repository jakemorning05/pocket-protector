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
