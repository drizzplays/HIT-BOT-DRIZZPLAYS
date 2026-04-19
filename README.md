# Hits Matchup Bot (GitHub + Google Sheets Ready)

A Python bot that pulls MLB probable starters, checks hitter vs starting-pitcher history, and writes **qualified hits matchups** into CSV files that work cleanly with GitHub and Google Sheets.

## What this build does

- Focuses on **qualified matchups only**
- Writes the dated output file
- Also writes a stable file named **`latest_qualified.csv`** for GitHub
- Keeps overview export
- Keeps full-board export optional and off by default

## Radar filter

A hitter qualifies when all three pass:

- `MIN_AB` = 3 or more
- `MIN_HITS` = 1 or more
- `MIN_HIT_RATE` = `.333` or higher

Important: this is **hit rate vs pitcher** based on `hits / AB`, not true OBP.

## Main output files

Default output:

```bash
output/hits_matchups_YYYY-MM-DD_overview.csv
output/hits_matchups_YYYY-MM-DD_qualified.csv
output/latest_qualified.csv
```

Optional full board:

```bash
output/hits_matchups_YYYY-MM-DD_all_matchups.csv
```

## Why `latest_qualified.csv` matters

That file name never changes.

So in Google Sheets you can use one formula forever:

```excel
=IMPORTDATA("https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/output/latest_qualified.csv")
```

That is the clean GitHub workflow.

## What each qualified row shows

- batter
- pitcher
- hits
- AB
- hit rate (`hits / AB`)
- hit breakdown (`1B`, `2B`, `3B`, `HR`)
- recent AB sequence
- tier
- matchup string like `5-for-8`

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Environment variables

| Variable | What it does |
|---|---|
| `RUN_DATE` | Date to run, format `YYYY-MM-DD` |
| `MIN_AB` | Minimum historical AB to qualify |
| `MIN_HITS` | Minimum hits to qualify |
| `MIN_HIT_RATE` | Minimum hits / AB to qualify |
| `MAX_HITTERS_PER_GAME` | Optional cap per game. `0` = no cap |
| `SEARCH_MODE` | `all_hitters` or `manual_or_roster` |
| `REQUEST_TIMEOUT` | HTTP timeout in seconds |
| `LINEUP_FILE` | JSON file with manual lineups |
| `LAST_AB_WINDOW` | Number of recent AB results to show |
| `OUTPUT_DIR` | Folder where the CSV files are saved |
| `OUTPUT_BASE_NAME` | Optional custom filename prefix |
| `WRITE_LATEST_CSV` | `1` = also write stable latest file, default is on |
| `LATEST_FILE_NAME` | Stable latest file name, default `latest_qualified.csv` |
| `INCLUDE_ALL_MATCHUPS_CSV` | `1` = also export the full board, default is off |

## GitHub Actions setup

The included workflow will:

- run the bot manually or on schedule
- update the output files
- commit the refreshed CSVs back to the repo

To make Google Sheets refresh cleanly, your repo should be **public** or the CSV URL will not be readable by `IMPORTDATA`.

## Good default thresholds

```bash
MIN_AB=3
MIN_HITS=1
MIN_HIT_RATE=0.333
MAX_HITTERS_PER_GAME=0
SEARCH_MODE=all_hitters
LAST_AB_WINDOW=10
WRITE_LATEST_CSV=1
LATEST_FILE_NAME=latest_qualified.csv
```

## Notes

- `latest_qualified.csv` is the file you want for GitHub + Google Sheets.
- `*_qualified.csv` keeps the dated archive.
- `All Matchups` is optional and off by default.
- Tier labels help you sort fast. They are not the bet by themselves.
