from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date


def _env_bool(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    run_date: str = os.getenv("RUN_DATE", date.today().isoformat())
    min_ab: int = int(os.getenv("MIN_AB", "3"))
    min_hits: int = int(os.getenv("MIN_HITS", "1"))
    min_hit_rate: float = float(os.getenv("MIN_HIT_RATE", "0.333"))
    max_hitters_per_game: int = int(os.getenv("MAX_HITTERS_PER_GAME", "0"))
    search_mode: str = os.getenv("SEARCH_MODE", "all_hitters").strip().lower()
    discord_webhook_url: str | None = os.getenv("DISCORD_WEBHOOK_URL")
    lineup_file: str = os.getenv("LINEUP_FILE", "lineups.json")
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
    last_ab_window: int = int(os.getenv("LAST_AB_WINDOW", "10"))
    output_dir: str = os.getenv("OUTPUT_DIR", "output")
    output_base_name: str | None = os.getenv("OUTPUT_BASE_NAME")
    include_all_matchups_csv: bool = _env_bool("INCLUDE_ALL_MATCHUPS_CSV", "0")
    latest_file_name: str = os.getenv("LATEST_FILE_NAME", "latest_qualified.csv")
    write_latest_csv: bool = _env_bool("WRITE_LATEST_CSV", "1")


SETTINGS = Settings()
