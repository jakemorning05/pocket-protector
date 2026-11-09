# Pocket Protector refresh steps (for Claude sessions)

The project lives in /home/claude/nfl and is a git repository. If that folder is missing (fresh container), clone
Jacob's GitHub repository (see README; ask him for the owner/name if it isn't in the conversation) into /home/claude/nfl.

The GitHub Action (.github/workflows/update.yml → scripts/update.sh) does all the mechanical work on its own schedule.
A session adds the judgment calls:

1. `git pull` so you're working on the latest data the Action committed.
2. Check news (web search: QB changes, injuries, trades). Update:
   - data/overrides.json: qb_starters (team, play-by-play short name, full name, through_week, source) and players_out.
   - data/news.json: asof, outs, flags, items (each with source + url). The `injuries` list is rebuilt by pipeline/injury_list.py.
3. Props: add Kalshi markets to NEW_PROPS in pipeline/props.py (game id, player, stat, threshold, price), set SOURCE, run
   `cd pipeline && python3 props.py log`. Prices: Covers "player props computer projections" pages list Kalshi X+ markets.
4. Rebuild: `bash scripts/update.sh` (downloads, retrains, grades, logs new spread/total picks, builds docs/index.html).
5. Commit and push (`git add -A && git commit && git push`); the site redeploys from docs/. The commit message ends with the
   attribution lines from the session's instructions.
6. Optional preview in the Claude app: publish /home/claude/nfl/pocket-protector.html with the Artifact tool, passing
   url https://claude.ai/artifact/Nf1FiY95xTU88SXWKDuMeG (without url it creates a new artifact).
7. Send Jacob a short summary: what changed, graded results (record, profit/loss, average CLV), reminder that small samples prove little.
