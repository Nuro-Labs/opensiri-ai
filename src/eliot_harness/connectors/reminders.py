"""Reminders connector."""

from __future__ import annotations

import re
from datetime import datetime, timedelta

from .calendar import eventkit
from .applescript import q, run_osa
from .base import Connector, ConnectorResult


WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6,
}
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


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

    def add_reminder(self, text: str, due_text: str = "", dry_run: bool = True) -> ConnectorResult:
        due = parse_due_datetime(due_text or text)
        if dry_run or not self.can_write:
            suffix = f" due {due.strftime('%Y-%m-%d %H:%M')}" if due else ""
            return ConnectorResult(f"DRY RUN reminder: {text}{suffix}", {"requires_approval": True, "due": due.isoformat() if due else None})
        if due:
            script = reminder_script(text, due)
            out = run_osa(script)
        else:
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


def parse_due_datetime(text: str) -> datetime | None:
    raw = text.lower()
    if not any(x in raw for x in ("today", "tomorrow", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", " at ", "am", "pm")):
        return None
    now = datetime.now()
    target = now
    if "tomorrow" in raw:
        target = now + timedelta(days=1)
    else:
        for name, idx in WEEKDAYS.items():
            if name in raw:
                days = (idx - now.weekday()) % 7
                if days == 0 and "next" in raw:
                    days = 7
                target = now + timedelta(days=days)
                break
    hour, minute = 9, 0
    m = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", raw)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2) or 0)
        if m.group(3) == "pm" and hour != 12:
            hour += 12
        if m.group(3) == "am" and hour == 12:
            hour = 0
    else:
        m = re.search(r"\bat\s+(\d{1,2})(?::(\d{2}))?\b", raw)
        if m:
            hour = int(m.group(1)); minute = int(m.group(2) or 0)
    if hour > 23 or minute > 59:
        return None
    return target.replace(hour=hour, minute=minute, second=0, microsecond=0)


def reminder_script(text: str, due: datetime) -> str:
    return f'''set dueDate to current date
set year of dueDate to {due.year}
set month of dueDate to {MONTHS[due.month - 1]}
set day of dueDate to {due.day}
set time of dueDate to ({due.hour} * hours + {due.minute} * minutes)
tell application "Reminders"
  make new reminder with properties {{name:{q(text)}, remind me date:dueDate}}
end tell'''
