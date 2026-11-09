#!/usr/bin/env bash
# Pocket Protector update: download fresh nflverse data, rebuild the model outputs and the site.
# Used by .github/workflows/update.yml; also runs locally (needs Python with requirements.txt and curl).
set -euo pipefail
cd "$(dirname "$0")/.."

SEASON=2026
FIRST=2016
REL=https://github.com/nflverse/nflverse-data/releases/download
mkdir -p data

get() {  # get <release path> <file name>
  curl -fsSL --retry 3 --retry-delay 5 -o "data/$2.tmp" "$REL/$1" && mv "data/$2.tmp" "data/$2"
}
echo "Downloading data"
get schedules/games.csv games.csv
for y in $(seq $FIRST $SEASON); do
  # past seasons never change: download them once (the workflow caches them between runs)
  for f in "pbp/play_by_play_$y.csv.gz:play_by_play_$y.csv.gz" "injuries/injuries_$y.csv:injuries_$y.csv" "snap_counts/snap_counts_$y.csv:snap_counts_$y.csv"; do
    src="${f%%:*}"; dst="${f##*:}"
    if [ "$y" -lt "$SEASON" ] && [ -s "data/$dst" ]; then continue; fi
    get "$src" "$dst"
  done
done
get "stats_player/stats_player_week_$SEASON.csv" "stats_player_week_$SEASON.csv"

echo "Rebuilding model outputs"
rm -f data/inj_cache.pkl   # injury reports may have changed
PY="${PYTHON:-python3}"
cd pipeline
"$PY" teamgames.py
"$PY" features.py
"$PY" export.py
"$PY" drift.py            # how much less certain later weeks are
"$PY" export.py           # again, so future-week odds use the fresh number
"$PY" players.py
"$PY" fantasy.py
"$PY" injury_list.py
"$PY" betting.py grade
"$PY" props.py grade
"$PY" betting.py log "$(TZ=America/New_York date '+%b %-d, %-I:%M %p ET')"
cd ..
"$PY" build_site.py
echo "Done"
