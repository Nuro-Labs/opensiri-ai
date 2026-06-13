"""Music connector."""

from __future__ import annotations

from .applescript import q, run_osa
from .base import Connector, ConnectorResult


class MusicConnector(Connector):
    name = "music"
    source = "music"
    can_read = True
    can_write = False

    def play_query(self, query: str, dry_run: bool = True) -> ConnectorResult:
        if dry_run:
            return ConnectorResult(f"DRY RUN Music play search: {query}", {"requires_approval": False})
        script = 'tell application "Music" to set matches to search library playlist 1 for ' + q(query) + ' only songs\n' + 'tell application "Music" to if matches is not {} then play item 1 of matches'
        return ConnectorResult(run_osa(script), {"source": self.source})

    def play_pause(self, dry_run: bool = True) -> ConnectorResult:
        if dry_run:
            return ConnectorResult("DRY RUN Music play/pause", {"requires_approval": False})
        return ConnectorResult(run_osa('tell application "Music" to playpause'), {"source": self.source})
