from __future__ import annotations

import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def build_session() -> requests.Session:
    session = requests.Session()
    retries = Retry(
        total=4,
        backoff_factor=1,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(
        {
            "User-Agent": "hr-matchup-bot/1.0",
            "Accept": "application/json, text/csv;q=0.9, */*;q=0.8",
        }
    )
    return session


class HttpClient:
    def __init__(self, timeout: int = 30) -> None:
        self.session = build_session()
        self.timeout = timeout

    def get_json(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def get_text(self, url: str, params: dict[str, Any] | None = None) -> str:
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.text

    def post_json(self, url: str, payload: dict[str, Any]) -> None:
        response = self.session.post(url, json=payload, timeout=self.timeout)
        if response.status_code == 429:
            time.sleep(2)
            response = self.session.post(url, json=payload, timeout=self.timeout)
        response.raise_for_status()
