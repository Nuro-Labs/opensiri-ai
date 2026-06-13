"""Notes connector."""

from __future__ import annotations

from .applescript import q, run_osa
from .base import Connector, ConnectorResult


class NotesConnector(Connector):
    name = "notes"
    source = "notes"
    can_read = True
    can_write = False

    def read_context(self, task: str) -> list[ConnectorResult]:
        if "note" not in task.lower():
            return []
        script = 'tell application "Notes" to get name of notes 1 thru 5'
        out = run_osa(script)
        return [ConnectorResult(f"Recent Notes: {out}", {"source": self.source})]

    def create_note(self, title: str, body: str, dry_run: bool = True) -> ConnectorResult:
        if dry_run or not self.can_write:
            return ConnectorResult(f"DRY RUN note: {title}\n{body}", {"requires_approval": True})
        script = 'tell application "Notes" to make new note at folder "Notes" with properties {name:' + q(title) + ', body:' + q(body) + '}'
        return ConnectorResult(run_osa(script), {"source": self.source})
