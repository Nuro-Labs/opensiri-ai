"""Calendar connector."""

from __future__ import annotations

from .applescript import q, run_osa
from .base import Connector, ConnectorResult


class CalendarConnector(Connector):
    name = "calendar"
    source = "calendar"
    can_read = True
    can_write = False

    def read_context(self, task: str) -> list[ConnectorResult]:
        if not any(x in task.lower() for x in ("calendar", "meeting", "free", "event")):
            return []
        script = 'tell application "Calendar" to get summary of events of calendar 1 whose start date is greater than (current date) - (time of (current date))'
        out = run_osa(script)
        return [ConnectorResult(f"Calendar today: {out[:1000]}", {"source": self.source})]

    def create_event(self, title: str, dry_run: bool = True) -> ConnectorResult:
        if dry_run or not self.can_write:
            return ConnectorResult(f"DRY RUN calendar event: {title}", {"requires_approval": True})
        script = 'tell application "Calendar" to tell calendar 1 to make new event with properties {summary:' + q(title) + ', start date:(current date), end date:(current date) + 3600}'
        return ConnectorResult(run_osa(script), {"source": self.source})
