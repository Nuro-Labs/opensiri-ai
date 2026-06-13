"""Calendar connector."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .applescript import q, run_osa
from .base import Connector, ConnectorResult


def eventkit(command: str, *args: str) -> str:
    helper = Path(__file__).resolve().parents[3] / "scripts" / "eventkit_bridge.swift"
    if not helper.exists():
        return ""
    try:
        r = subprocess.run(["swift", str(helper), command, *args], capture_output=True, text=True, timeout=45)
    except Exception:
        return ""
    return r.stdout.strip() if r.returncode == 0 else ""


class CalendarConnector(Connector):
    name = "calendar"
    source = "calendar"
    can_read = True
    can_write = False

    def read_context(self, task: str) -> list[ConnectorResult]:
        if not any(x in task.lower() for x in ("calendar", "meeting", "free", "event")):
            return []
        out = eventkit("calendar-today")
        if not out:
            script = 'tell application "Calendar" to get summary of events of calendar 1 whose start date is greater than (current date) - (time of (current date))'
            out = run_osa(script)
        return [ConnectorResult(f"Calendar today: {out[:1000]}", {"source": self.source})]

    def create_event(self, title: str, dry_run: bool = True) -> ConnectorResult:
        if dry_run or not self.can_write:
            return ConnectorResult(f"DRY RUN calendar event: {title}", {"requires_approval": True})
        out = eventkit("create-event", title)
        if not out:
            script = 'tell application "Calendar" to tell calendar 1 to make new event with properties {summary:' + q(title) + ', start date:(current date), end date:(current date) + 3600}'
            out = run_osa(script)
        return ConnectorResult(out, {"source": self.source})
