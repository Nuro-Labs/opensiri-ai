"""Apple Maps connector using documented Maps links."""

from __future__ import annotations

import subprocess
import urllib.parse

from .base import Connector, ConnectorResult


class MapsConnector(Connector):
    name = "maps"
    source = "maps"
    can_read = True
    can_write = False

    def directions_url(self, destination: str, source: str = "", mode: str = "d") -> str:
        params = {"daddr": destination, "dirflg": mode or "d"}
        if source:
            params["saddr"] = source
        return "http://maps.apple.com/?" + urllib.parse.urlencode(params)

    def open_directions(self, destination: str, source: str = "", mode: str = "d", dry_run: bool = True) -> ConnectorResult:
        url = self.directions_url(destination, source, mode)
        if dry_run:
            return ConnectorResult(f"DRY RUN maps directions: {url}", {"url": url, "requires_approval": False})
        subprocess.run(["open", url], check=False)
        return ConnectorResult(f"Opened Maps directions to {destination}", {"url": url})
