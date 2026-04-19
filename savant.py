from __future__ import annotations

from dataclasses import dataclass
from io import StringIO

import pandas as pd
from pandas.errors import EmptyDataError

from http_client import HttpClient

CSV_URL = "https://baseballsavant.mlb.com/statcast_search/csv"
NON_AB_EVENTS = {"walk", "intent_walk", "hit_by_pitch", "sac_bunt", "sac_fly", "catcher_interf"}
HIT_EVENTS = {"single", "double", "triple", "home_run"}
EVENT_MAP = {
    "home_run": "HR",
    "single": "1B",
    "double": "2B",
    "triple": "3B",
    "strikeout": "K",
    "strikeout_double_play": "KDP",
    "field_out": "FO",
    "groundout": "GO",
    "flyout": "FO",
    "lineout": "LO",
    "pop_out": "PO",
    "force_out": "FORCE",
    "double_play": "DP",
    "grounded_into_double_play": "GIDP",
    "fielders_choice": "FC",
    "fielders_choice_out": "FCO",
    "sac_fly": "SF",
    "sac_bunt": "SAC",
    "walk": "BB",
    "intent_walk": "IBB",
    "hit_by_pitch": "HBP",
}


@dataclass(frozen=True)
class MatchupSummary:
    batter_id: int
    pitcher_id: int
    batter_name: str
    pitcher_name: str
    ab: int
    hits: int
    hit_rate: float
    hit_breakdown: dict[str, int]
    last_ab_count: int
    last_results: list[str]


class SavantClient:
    def __init__(self, client: HttpClient) -> None:
        self.client = client

    def fetch_matchup_rows(self, batter_id: int, pitcher_id: int) -> pd.DataFrame:
        params = {
            "all": "true",
            "player_type": "batter",
            "game_date_gt": "2015-01-01",
            "game_date_lt": "2099-12-31",
            "min_pas": 0,
            "min_results": 0,
            "group_by": "",
            "sort_col": "game_date",
            "sort_order": "desc",
            "batters_lookup[]": batter_id,
            "pitchers_lookup[]": pitcher_id,
            "hfGT": "R|PO|S|",
        }
        text = self.client.get_text(CSV_URL, params=params)
        cleaned = text.strip()
        if not cleaned:
            return pd.DataFrame()

        # Baseball Savant will occasionally return an empty body, a stray newline,
        # or even an HTML error page with status 200. Do not let one bad response
        # kill the full slate run.
        lowered = cleaned.lower()
        if cleaned.startswith("<") or "<html" in lowered or "<!doctype" in lowered:
            return pd.DataFrame()

        try:
            df = pd.read_csv(StringIO(cleaned))
        except EmptyDataError:
            return pd.DataFrame()
        except Exception:
            return pd.DataFrame()

        if df.empty:
            return df
        if "events" not in df.columns:
            return pd.DataFrame()
        return df

    def summarize_matchup(
        self,
        batter_id: int,
        pitcher_id: int,
        batter_name: str,
        pitcher_name: str,
        last_ab_window: int = 10,
    ) -> MatchupSummary | None:
        df = self.fetch_matchup_rows(batter_id=batter_id, pitcher_id=pitcher_id)
        if df.empty:
            return None

        pa_df = df.dropna(subset=["events"]).copy()
        if pa_df.empty:
            return None

        ab_df = pa_df[~pa_df["events"].isin(NON_AB_EVENTS)].copy()
        if ab_df.empty:
            return None

        sort_cols = [c for c in ["game_date", "game_pk", "at_bat_number", "pitch_number"] if c in ab_df.columns]
        if sort_cols:
            ab_df = ab_df.sort_values(sort_cols, ascending=False)

        hits = int(ab_df["events"].isin(HIT_EVENTS).sum())
        hit_breakdown = {
            "1B": int((ab_df["events"] == "single").sum()),
            "2B": int((ab_df["events"] == "double").sum()),
            "3B": int((ab_df["events"] == "triple").sum()),
            "HR": int((ab_df["events"] == "home_run").sum()),
        }
        last_n = ab_df.head(last_ab_window)
        results = [EVENT_MAP.get(str(ev), str(ev).upper()) for ev in last_n["events"].tolist()]
        ab = len(ab_df)

        return MatchupSummary(
            batter_id=batter_id,
            pitcher_id=pitcher_id,
            batter_name=batter_name,
            pitcher_name=pitcher_name,
            ab=ab,
            hits=hits,
            hit_rate=(hits / ab) if ab else 0.0,
            hit_breakdown=hit_breakdown,
            last_ab_count=len(last_n),
            last_results=results,
        )
