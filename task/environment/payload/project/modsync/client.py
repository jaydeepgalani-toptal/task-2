from __future__ import annotations

from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


class ForumClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.session = requests.Session()
        self.session.headers["User-Agent"] = "modsync/0.1"

    def get_soup(self, url: str) -> BeautifulSoup:
        response = self.session.get(url, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")

    def get_index(self) -> BeautifulSoup:
        return self.get_soup(self.base_url)

    def get_search(self, term: str) -> BeautifulSoup:
        return self.get_soup(urljoin(self.base_url, f"search?q={term}"))

    def fetch_bytes(self, url: str) -> bytes:
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return response.content

    def download(self, url: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(self.fetch_bytes(url))
