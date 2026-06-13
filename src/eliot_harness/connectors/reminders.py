"""Reminders connector."""

from __future__ import annotations

from .calendar import eventkit
from .applescript import q, run_osa
from .base import Connector, ConnectorResult


class RemindersConnector(Connector):
    name = "reminders"
    source = "reminders"
    can_read = True
    can_write = False

    def read_context(self, task: str) -> list[ConnectorResult]:
        if "remind" not in task.lower():
            return []
        out = eventkit("reminders") or run_osa('tell application "Reminders" to get name of reminders 1 thru 10')
        return [ConnectorResult(f"Visible reminders: {out}", {"source": self.source})]

    def add_reminder(self, text: str, dry_run: bool = True) -> ConnectorResult:
        if dry_run or not self.can_write:
            return ConnectorResult(f"DRY RUN reminder: {text}", {"requires_approval": True})
        out = eventkit("add-reminder", text)
        if not out:
            script = 'tell application "Reminders" to make new reminder with properties {name:' + q(text) + '}'
            out = run_osa(script)
        return ConnectorResult(out, {"source": self.source})

    def complete_reminder(self, text: str, dry_run: bool = True) -> ConnectorResult:
        if dry_run or not self.can_write:
            return ConnectorResult(f"DRY RUN complete reminder matching: {text}", {"requires_approval": True})
        script = 'tell application "Reminders" to set completed of reminders whose name contains ' + q(text) + ' to true'
        return ConnectorResult(run_osa(script), {"source": self.source})

    def update_reminder(self, text: str, action: str, dry_run: bool = True) -> ConnectorResult:
        if dry_run or not self.can_write:
            return ConnectorResult(f"DRY RUN reminder {action}: {text}", {"requires_approval": True})
        return ConnectorResult(f"reminder {action} requires a native EventKit implementation", {"source": self.source})
