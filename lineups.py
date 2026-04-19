from __future__ import annotations

import json
from pathlib import Path

from mlb import Hitter, Team


def load_manual_lineups(path: str, teams: list[Team]) -> dict[str, list[str]]:
    file_path = Path(path)
    if not file_path.exists():
        return {}
    raw = json.loads(file_path.read_text())
    valid = {team.abbreviation.upper() for team in teams}
    output: dict[str, list[str]] = {}
    for key, value in raw.items():
        team_key = key.upper()
        if team_key in valid and isinstance(value, list):
            output[team_key] = [str(name).strip() for name in value if str(name).strip()]
    return output


def choose_hitters(team: Team, roster_hitters: list[Hitter], manual_lineups: dict[str, list[str]]) -> list[Hitter]:
    wanted_names = manual_lineups.get(team.abbreviation.upper())
    if not wanted_names:
        return sorted(roster_hitters, key=lambda h: (h.position or "", h.full_name))

    lookup = {h.full_name.lower(): h for h in roster_hitters}
    selected: list[Hitter] = []
    for name in wanted_names:
        hitter = lookup.get(name.lower())
        if hitter:
            selected.append(hitter)
    return selected
