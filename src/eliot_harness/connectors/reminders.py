"""Reminders connector."""

from __future__ import annotations

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
        out = run_osa('tell application "Reminders" to get name of reminders 1 thru 10')
        return [ConnectorResult(f"Visible reminders: {out}", {"source": self.source})]

    def add_reminder(self, text: str, dry_run: bool = True) -> ConnectorResult:
        if dry_run or not self.can_write:
            return ConnectorResult(f"DRY RUN reminder: {text}", {"requires_approval": True})
        script = 'tell application "Reminders" to make new reminder with properties {name:' + q(text) + '}'
        return ConnectorResult(run_osa(script), {"source": self.source})
