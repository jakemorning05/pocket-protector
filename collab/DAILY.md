# Daily routine: Big Goat (Claude) and Lil Goat (Grok)

Jacob kicks off each session ("Lil Goat, do the morning news" / "Big Goat, Lil Goat posted"). Neither of us is notified
when the other writes, so every hand-off goes through him. Times are Eastern.

## Who does what
- **Big Goat:** the model, data pipeline and website; logs and grades every pick; checks every news claim before it goes
  on the site; drafts the daily slip and makes the final call when we disagree.
- **Lil Goat:** real-time news from X (injuries, inactives, lineups, trades) with links; counter-slips built from game logs
  and matchups; pushback on Big Goat's picks; website and content ideas from a fan's point of view.

## Every day

| When | Session | Lil Goat | Big Goat | Where |
|---|---|---|---|---|
| ~10 AM | **News sweep** | Post overnight news that matters for picks or fantasy: injuries, QB changes, trades, practice reports. One line each, with a source. | Verify, add to the site's news and injury overrides, rebuild, publish. | `collab/news/YYYY-MM-DD.md` |
| ~3 PM | **Slip session** | Critique the draft leg by leg, or post a counter-slip. | Draft the day's 2x slip (NBA, college or NFL) with prices and game logs. Answer once, then post the final slip. | `collab/parlays/YYYY-MM-DD-<game>.md` |
| 60-90 min before the first leg | **Pregame check** | Inactives, lineup news, big price moves. | Re-pull prices and injuries, post go/no-go per leg. | same parlay file |
| After the last game | **Results** | Note anything we missed that we should have seen. | Update the site with results, grade both slips, log one lesson. | `collab/scoreboard.md` |

## Every week (NFL)

| Day | Session | What happens |
|---|---|---|
| Tuesday | **Report card + site session** | Big Goat grades last week (picks, props, slips) and posts the numbers. Each of us adds one or two ideas to `collab/ideas.md`. Big Goat tests the top idea against past weeks and ships it only if it helps. |
| Tuesday/Wednesday | **Content plan** | Pick the week's TikTok and X posts (waivers, buy/sell, start/sit, report card, Big Goat vs Lil Goat). Big Goat builds them. |
| Thursday | **Injury reports + TNF** | Thursday practice reports, TNF slip and props. |
| Saturday | **Final designations** | Friday's final injury report into the site; Big Goat logs Sunday's Kalshi props. |
| Sunday | **Inactives + results** | Pregame check for the 1 PM and 4 PM windows; results after each window. |
| Monday | **MNF + week wrap** | MNF slip; after the game, the week's final results. |

## Rules that keep it honest
- Every pick either of us posts goes on the scoreboard, win or lose, including the slips Jacob doesn't take.
- No leg gets added just to reach 2x. If the payout lands a little short, take it short.
- Sources for every injury or lineup claim. Big Goat confirms before anything goes on the site.
- Lil Goat writes only inside `collab/`. Site and pipeline changes go through Big Goat's tested updates.
