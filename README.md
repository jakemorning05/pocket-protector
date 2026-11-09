# Pocket Protector

NFL game predictions, pick'em and survivor pool tools, fantasy projections and a betting test bench, all from one statistical model. The site is a single page in `docs/` served by GitHub Pages, and a scheduled GitHub Action rebuilds it with fresh data three times a week.

## One-time setup

1. **Turn on GitHub Pages.** Repository **Settings → Pages**. Under *Build and deployment*, set *Source* to **Deploy from a branch**, branch **main**, folder **/docs**, and save. The site appears at `https://<your-username>.github.io/pocket-protector/` within a minute or two.
2. **Run the first update.** Open the **Actions** tab, pick **Update site**, and click **Run workflow**. It takes about 5 minutes.
3. **If that run fails at "Publish changes"** with a permission error: **Settings → Actions → General → Workflow permissions**, choose **Read and write permissions**, save, and run it again.

## How it updates

`.github/workflows/update.yml` runs `scripts/update.sh`:

| When (Eastern) | Why |
| --- | --- |
| Tuesday ~7 AM | Monday night results are in; grades last week's picks and logs the new week's |
| Thursday ~4 PM | Thursday injury reports |
| Saturday ~11 AM | Final injury reports before Sunday |

It also runs whenever you change `data/overrides.json`, `data/news.json` or the page source, and any time you press **Run workflow**.

Each run downloads play-by-play, schedules, lines, injury reports and snap counts from [nflverse](https://github.com/nflverse/nflverse-data), retrains the ratings, re-projects players, locks each pick at kickoff (`data/pick_log.json`), grades past picks, rebuilds `docs/index.html` and commits the result.

## What you edit by hand

The official data can't know everything. Two small files cover the rest. Edit them right on GitHub (open the file, click the pencil, **Commit changes**), and the site rebuilds in about 5 minutes.

- **`data/overrides.json`**: who's starting at quarterback when the news says it isn't last week's starter, and through which week; plus regulars ruled out in the news before the official report lists them.
- **`data/news.json`**: the headlines on the News tab (`items`), players to drop from fantasy rankings (`outs`) and short notes shown on players (`flags`). The injured-starters list in the same file updates itself.

## Layout

```
docs/          the built site (GitHub Pages serves this folder)
src/           page template, styles and the Pools tab script
pipeline/      Python: features, model, exports, player projections, betting and prop logs
data/*.json    model outputs, logs and the hand-edited files (raw downloads are not committed)
scripts/       update.sh, the whole refresh in one command
build_site.py  assembles docs/index.html from src/ and data/
gamepages.py   writes a preview page per game to docs/games/ and docs/sitemap.xml
```

Run it yourself with Python 3.13: `pip install -r requirements.txt`, then `bash scripts/update.sh`.

## Custom domain

Buy the domain from any registrar, then **Settings → Pages → Custom domain**, enter it, and add the DNS records GitHub shows ([GitHub's guide](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site)). Tick **Enforce HTTPS** once it's available. Then change `SITE_URL` at the top of `build_site.py` to the new address.

## Next season

The season year (2026) is written into `scripts/update.sh` and most scripts in `pipeline/` (search the repository for `2026`). Moving to 2027 means updating those and checking that last season's ratings carry over, best done before Week 1.

## Disclaimer

Predictions are estimates, not betting advice. Over past seasons the model has not beaten point spreads. Not affiliated with the NFL or any team. Data from nflverse.
