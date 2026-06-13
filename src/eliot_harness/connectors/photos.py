"""Photos metadata connector scaffold."""

from __future__ import annotations

from .applescript import run_osa
from .base import Connector, ConnectorResult


class PhotosConnector(Connector):
    name = "photos"
    source = "photos"
    can_read = False
    can_write = False

    def read_context(self, task: str) -> list[ConnectorResult]:
        if not self.can_read or not any(x in task.lower() for x in ("photo", "album", "picture", "image")):
            return []
        out = run_osa('tell application "Photos" to get name of albums 1 thru 20', timeout=20)
        if not out or out.startswith("error"):
            return [ConnectorResult("Photos metadata unavailable. Enable Photos permission or use visual screenshot capture.", {"source": self.source})]
        return [ConnectorResult(f"Photos albums: {out}", {"source": self.source})]

    def add_to_album(self, album: str, dry_run: bool = True) -> ConnectorResult:
        if dry_run or not self.can_write:
            return ConnectorResult(f"DRY RUN Photos album update: {album}", {"requires_approval": True})
        return ConnectorResult("Photos write not implemented yet", {"requires_approval": True})
