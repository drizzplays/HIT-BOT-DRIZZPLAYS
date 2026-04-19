from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import shutil

from config import SETTINGS
from savant import MatchupSummary


@dataclass(frozen=True)
class CsvRow:
    run_date: str
    game: str
    batter: str
    pitcher: str
    hits: int
    ab: int
    hit_rate: float
    singles: int
    doubles: int
    triples: int
    home_runs: int
    last_ab_count: int
    last_results: str
    qualified: str
    tier: str
    matchup: str


def _hit_rate(hits: int, ab: int) -> float:
    return hits / ab if ab else 0.0


def _is_qualified(hits: int, ab: int, hit_rate: float) -> bool:
    return ab >= SETTINGS.min_ab and hits >= SETTINGS.min_hits and hit_rate >= SETTINGS.min_hit_rate


def _tier(hits: int, hit_rate: float, qualified: bool) -> str:
    if hits >= 5 and hit_rate >= 0.5:
        return "Elite"
    if hits >= 4 and hit_rate >= 0.4:
        return "Strong"
    if qualified:
        return "Playable"
    return "Thin"


def _summary_to_row(run_date: str, game_label: str, summary: MatchupSummary) -> CsvRow:
    hit_rate = _hit_rate(summary.hits, summary.ab)
    qualified = _is_qualified(summary.hits, summary.ab, hit_rate)
    return CsvRow(
        run_date=run_date,
        game=game_label,
        batter=summary.batter_name,
        pitcher=summary.pitcher_name,
        hits=summary.hits,
        ab=summary.ab,
        hit_rate=hit_rate,
        singles=summary.hit_breakdown.get("1B", 0),
        doubles=summary.hit_breakdown.get("2B", 0),
        triples=summary.hit_breakdown.get("3B", 0),
        home_runs=summary.hit_breakdown.get("HR", 0),
        last_ab_count=summary.last_ab_count,
        last_results=" | ".join(summary.last_results),
        qualified="Yes" if qualified else "No",
        tier=_tier(summary.hits, hit_rate, qualified),
        matchup=f"{summary.hits}-for-{summary.ab}",
    )


class CsvExporter:
    def __init__(self, run_date: str, game_results: list[tuple[str, list[MatchupSummary]]]) -> None:
        self.run_date = run_date
        self.rows = [
            _summary_to_row(run_date, game_label, summary)
            for game_label, summaries in game_results
            for summary in summaries
        ]
        self.rows.sort(key=lambda row: (-row.hit_rate, -row.hits, -row.ab, row.game, row.batter))

    def export(self, output_dir: str | Path) -> dict[str, Path]:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        base_name = SETTINGS.output_base_name or f"hits_matchups_{self.run_date}"
        paths = {
            "overview": output_dir / f"{base_name}_overview.csv",
            "qualified": output_dir / f"{base_name}_qualified.csv",
        }
        if SETTINGS.include_all_matchups_csv:
            paths["all_matchups"] = output_dir / f"{base_name}_all_matchups.csv"

        self._write_overview(paths["overview"])
        qualified_rows = [row for row in self.rows if row.qualified == "Yes"]
        self._write_rows(paths["qualified"], qualified_rows)
        if SETTINGS.write_latest_csv:
            latest_path = output_dir / SETTINGS.latest_file_name
            shutil.copyfile(paths["qualified"], latest_path)
            paths["latest_qualified"] = latest_path
        if SETTINGS.include_all_matchups_csv:
            self._write_rows(paths["all_matchups"], self.rows)
        return paths

    def _write_overview(self, path: Path) -> None:
        generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        total = len(self.rows)
        qualified = sum(1 for row in self.rows if row.qualified == "Yes")
        elite = sum(1 for row in self.rows if row.tier == "Elite")
        strong = sum(1 for row in self.rows if row.tier == "Strong")
        playable = sum(1 for row in self.rows if row.tier == "Playable")
        thin = sum(1 for row in self.rows if row.tier == "Thin")

        rows = [
            ["Section", "Metric", "Value"],
            ["Run Settings", "Run Date", self.run_date],
            ["Run Settings", "Generated (UTC)", generated_at],
            ["Run Settings", "Min AB", SETTINGS.min_ab],
            ["Run Settings", "Min Hits", SETTINGS.min_hits],
            ["Run Settings", "Min Hit Rate", SETTINGS.min_hit_rate],
            ["Run Settings", "Last AB Window", SETTINGS.last_ab_window],
            ["Run Settings", "Search Mode", SETTINGS.search_mode],
            ["Run Settings", "Max Hitters / Game", SETTINGS.max_hitters_per_game],
            ["Run Settings", "Latest File", SETTINGS.latest_file_name if SETTINGS.write_latest_csv else "disabled"],
            ["KPIs", "Total matchups", total],
            ["KPIs", "Qualified matchups", qualified],
            ["KPIs", "Elite", elite],
            ["KPIs", "Strong", strong],
            ["KPIs", "Playable", playable],
            ["KPIs", "Thin", thin],
            ["Tier Rules", "Elite", "5+ hits and .500+ hit rate"],
            ["Tier Rules", "Strong", "4+ hits and .400+ hit rate"],
            ["Tier Rules", "Playable", "Passes filter thresholds"],
            ["Tier Rules", "Thin", "Fails filter thresholds"],
            ["Notes", "Qualified", "Only rows that pass the radar: Min AB / Min Hits / Min Hit Rate."],
            ["Notes", "Hit Rate", "Uses hits divided by AB only — not true OBP."],
            ["Notes", "Latest CSV", "This file stays stable for GitHub + Google Sheets IMPORTDATA."],
            ["Notes", "All Matchups CSV", "Off by default. Set INCLUDE_ALL_MATCHUPS_CSV=1 to export the full board."],
            ["Notes", "Last Results", "Recent AB results in most-recent-first order."],
        ]
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerows(rows)

    def _write_rows(self, path: Path, rows: list[CsvRow]) -> None:
        headers = [
            "Run Date",
            "Game",
            "Batter",
            "Pitcher",
            "Hits",
            "AB",
            "Hit Rate",
            "1B",
            "2B",
            "3B",
            "HR",
            "Last AB Count",
            "Last Results",
            "Qualified",
            "Tier",
            "Matchup",
        ]
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(headers)
            for row in rows:
                writer.writerow([
                    row.run_date,
                    row.game,
                    row.batter,
                    row.pitcher,
                    row.hits,
                    row.ab,
                    f"{row.hit_rate:.3f}",
                    row.singles,
                    row.doubles,
                    row.triples,
                    row.home_runs,
                    row.last_ab_count,
                    row.last_results,
                    row.qualified,
                    row.tier,
                    row.matchup,
                ])


def export_matchup_csvs(run_date: str, game_results: list[tuple[str, list[MatchupSummary]]], output_dir: str | Path) -> dict[str, Path]:
    return CsvExporter(run_date, game_results).export(output_dir)
