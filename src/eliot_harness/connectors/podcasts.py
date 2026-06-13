"""Podcasts connector."""

from __future__ import annotations

import subprocess
import urllib.parse

from .base import Connector, ConnectorResult


class PodcastsConnector(Connector):
    name = "podcasts"
    source = "podcasts"
    can_read = True
    can_write = False

    def search_url(self, query: str) -> str:
        return "https://podcasts.apple.com/search?" + urllib.parse.urlencode({"term": query})

    def open_search(self, query: str, dry_run: bool = True) -> ConnectorResult:
        url = self.search_url(query)
        if dry_run:
            return ConnectorResult(f"DRY RUN Podcasts search: {url}", {"url": url})
        subprocess.run(["open", url], check=False)
        return ConnectorResult(f"Opened Podcasts search for {query}", {"url": url})
