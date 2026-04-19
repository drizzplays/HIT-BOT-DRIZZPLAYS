from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from http_client import HttpClient

BASE_URL = "https://statsapi.mlb.com/api/v1"
POSITION_PLAYER_CODES = {"1B", "2B", "3B", "SS", "LF", "CF", "RF", "C", "DH", "OF", "IF", "UT"}


@dataclass(frozen=True)
class Team:
    id: int
    name: str
    abbreviation: str


@dataclass(frozen=True)
class Pitcher:
    id: int
    full_name: str
    team: Team


@dataclass(frozen=True)
class Hitter:
    id: int
    full_name: str
    team: Team
    position: str | None


@dataclass(frozen=True)
class Game:
    game_pk: int
    home_team: Team
    away_team: Team
    home_pitcher: Pitcher | None
    away_pitcher: Pitcher | None


def _team_from_api(blob: dict[str, Any]) -> Team:
    return Team(
        id=int(blob["id"]),
        name=blob["name"],
        abbreviation=blob.get("abbreviation") or blob.get("teamCode") or blob.get("fileCode", "").upper(),
    )


def _pitcher_from_api(blob: dict[str, Any] | None, team: Team) -> Pitcher | None:
    if not blob or not blob.get("id"):
        return None
    return Pitcher(id=int(blob["id"]), full_name=blob["fullName"], team=team)


def get_schedule(client: HttpClient, run_date: str) -> list[Game]:
    data = client.get_json(
        f"{BASE_URL}/schedule",
        params={"sportId": 1, "date": run_date, "hydrate": "probablePitcher,team"},
    )

    games: list[Game] = []
    for day in data.get("dates", []):
        for item in day.get("games", []):
            home = _team_from_api(item["teams"]["home"]["team"])
            away = _team_from_api(item["teams"]["away"]["team"])
            games.append(
                Game(
                    game_pk=int(item["gamePk"]),
                    home_team=home,
                    away_team=away,
                    home_pitcher=_pitcher_from_api(item["teams"]["home"].get("probablePitcher"), home),
                    away_pitcher=_pitcher_from_api(item["teams"]["away"].get("probablePitcher"), away),
                )
            )
    return games


def get_active_hitters(client: HttpClient, team: Team) -> list[Hitter]:
    data = client.get_json(
        f"{BASE_URL}/teams/{team.id}/roster",
        params={"rosterType": "active", "hydrate": "person(position)"},
    )
    hitters: list[Hitter] = []
    for entry in data.get("roster", []):
        person = entry.get("person", {})
        position = entry.get("position", {})
        abbr = position.get("abbreviation")
        if abbr in POSITION_PLAYER_CODES:
            hitters.append(
                Hitter(
                    id=int(person["id"]),
                    full_name=person["fullName"],
                    team=team,
                    position=abbr,
                )
            )
    return hitters
