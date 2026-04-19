from __future__ import annotations

import json
from dataclasses import asdict

from config import SETTINGS
from http_client import HttpClient
from lineups import choose_hitters, load_manual_lineups
from mlb import Game, get_active_hitters, get_schedule
from savant import MatchupSummary, SavantClient
from csv_export import export_matchup_csvs


def _select_hitters(game: Game, client: HttpClient):
    away_roster = get_active_hitters(client, game.away_team)
    home_roster = get_active_hitters(client, game.home_team)

    if SETTINGS.search_mode == "manual_or_roster":
        teams = [game.home_team, game.away_team]
        manual_lineups = load_manual_lineups(SETTINGS.lineup_file, teams)
        away_hitters = choose_hitters(game.away_team, away_roster, manual_lineups)
        home_hitters = choose_hitters(game.home_team, home_roster, manual_lineups)
    else:
        away_hitters = sorted(away_roster, key=lambda h: (h.position or "", h.full_name))
        home_hitters = sorted(home_roster, key=lambda h: (h.position or "", h.full_name))

    return away_hitters, home_hitters


def _passes_filters(summary: MatchupSummary) -> bool:
    return (
        summary.ab >= SETTINGS.min_ab
        and summary.hits >= SETTINGS.min_hits
        and summary.hit_rate >= SETTINGS.min_hit_rate
    )


def build_game_results(game: Game, savant: SavantClient, client: HttpClient) -> tuple[str, list[MatchupSummary]]:
    label = f"{game.away_team.abbreviation} @ {game.home_team.abbreviation}"

    if not game.home_pitcher or not game.away_pitcher:
        print(f"{label}: skipped because probable pitchers missing")
        return label, []

    away_hitters, home_hitters = _select_hitters(game, client)

    print(
        f"{label}: away_hitters={len(away_hitters)} vs {game.home_pitcher.full_name}, "
        f"home_hitters={len(home_hitters)} vs {game.away_pitcher.full_name}"
    )

    summaries: list[MatchupSummary] = []

    for hitter in away_hitters:
        try:
            summary = savant.summarize_matchup(
                batter_id=hitter.id,
                pitcher_id=game.home_pitcher.id,
                batter_name=hitter.full_name,
                pitcher_name=game.home_pitcher.full_name,
                last_ab_window=SETTINGS.last_ab_window,
            )
        except Exception as exc:
            print(f"Skipping matchup {hitter.full_name} vs {game.home_pitcher.full_name}: {exc}")
            summary = None

        if summary:
            summaries.append(summary)

    for hitter in home_hitters:
        try:
            summary = savant.summarize_matchup(
                batter_id=hitter.id,
                pitcher_id=game.away_pitcher.id,
                batter_name=hitter.full_name,
                pitcher_name=game.away_pitcher.full_name,
                last_ab_window=SETTINGS.last_ab_window,
            )
        except Exception as exc:
            print(f"Skipping matchup {hitter.full_name} vs {game.away_pitcher.full_name}: {exc}")
            summary = None

        if summary:
            summaries.append(summary)

    summaries.sort(key=lambda s: (-s.hit_rate, -s.hits, -s.ab, s.batter_name))

    total_before_cap = len(summaries)
    if SETTINGS.max_hitters_per_game > 0:
        summaries = summaries[: SETTINGS.max_hitters_per_game]

    print(f"{label}: summaries_found={total_before_cap}, summaries_after_cap={len(summaries)}")
    return label, summaries


def main() -> int:
    client = HttpClient(timeout=SETTINGS.request_timeout)
    savant = SavantClient(client)
    games = get_schedule(client, SETTINGS.run_date)

    print(f"Games found: {len(games)}")

    output: list[dict[str, object]] = []
    game_results: list[tuple[str, list[MatchupSummary]]] = []
    qualified_count = 0
    all_summary_count = 0

    for game in games:
        label, summaries = build_game_results(game, savant, client)
        game_results.append((label, summaries))

        qualified = [summary for summary in summaries if _passes_filters(summary)]

        print(f"{label}: total_summaries={len(summaries)} | qualified={len(qualified)}")

        all_summary_count += len(summaries)
        qualified_count += len(qualified)

        output.append(
            {
                "game": label,
                "results": [asdict(s) for s in summaries],
                "qualified_results": [asdict(s) for s in qualified],
            }
        )

    print(f"TOTAL SUMMARIES: {all_summary_count}")
    print(f"TOTAL QUALIFIED: {qualified_count}")

    csv_paths = export_matchup_csvs(
        run_date=SETTINGS.run_date,
        game_results=game_results,
        output_dir=SETTINGS.output_dir,
    )

    print(
        json.dumps(
            {
                "run_date": SETTINGS.run_date,
                "csv_files": {key: str(value) for key, value in csv_paths.items()},
                "total_summaries": all_summary_count,
                "qualified_matchups": qualified_count,
                "games": output,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
