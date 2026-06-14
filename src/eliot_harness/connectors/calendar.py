"""Calendar connector."""

from __future__ import annotations

import subprocess
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any

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


def _parse_day(day: str | None) -> date:
    today = date.today()
    if not day:
        return today
    value = day.strip().lower()
    if value == "today":
        return today
    if value == "tomorrow":
        return today + timedelta(days=1)
    weekdays = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
    if value in weekdays:
        days = (weekdays[value] - today.weekday()) % 7
        return today + timedelta(days=days)
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(day.strip(), fmt).date()
        except ValueError:
            pass
    return today


def _parse_time(value: str | None) -> time | None:
    if not value:
        return None
    text = value.strip().lower()
    if text == "noon":
        return time(12, 0)
    if text == "midnight":
        return time(0, 0)
    for fmt in ("%I:%M %p", "%I%p", "%H:%M", "%H"):
        try:
            return datetime.strptime(text.replace(" ", ""), fmt.replace(" ", "")).time()
        except ValueError:
            pass
    return None


def _calendar_events(start: datetime, end: datetime) -> str:
    now = datetime.now()
    start_offset = int((start - now).total_seconds())
    end_offset = int((end - now).total_seconds())
    script = f'''
set startDate to (current date) + {start_offset}
set endDate to (current date) + {end_offset}
set eventLines to {{}}
tell application "Calendar"
    repeat with cal in calendars
        set calName to name of cal
        set matches to events of cal whose start date is less than endDate and end date is greater than startDate
        repeat with ev in matches
            set eventLine to ((start date of ev) as string) & " - " & ((end date of ev) as string) & ": " & (summary of ev) & " [" & calName & "]"
            set end of eventLines to eventLine
        end repeat
    end repeat
end tell
set AppleScript's text item delimiters to linefeed
set out to eventLines as text
set AppleScript's text item delimiters to ""
return out
'''
    return run_osa(script, timeout=45)


class CalendarConnector(Connector):
    name = "calendar"
    source = "calendar"
    can_read = True
    can_write = False

    def read_context(self, task: str) -> list[ConnectorResult]:
        if not any(x in task.lower() for x in ("calendar", "meeting", "free", "event")):
            return []
        return [self.free_busy()]

    def execute(self, action_name: str, args: dict[str, Any]) -> ConnectorResult:
        if action_name == "free_busy":
            return self.free_busy(args.get("day"), args.get("time_text"))
        if action_name == "create_event":
            return self.create_event(str(args.get("title", "Eliot Event")), dry_run=not self.can_write)
        return ConnectorResult(f"Unsupported calendar action: {action_name}", {"source": self.source})

    def free_busy(self, day: str | None = None, time_text: str | None = None) -> ConnectorResult:
        target_day = _parse_day(day)
        target_time = _parse_time(time_text)
        if target_time:
            start = datetime.combine(target_day, target_time)
            end = start + timedelta(hours=1)
            label = f"{target_day.isoformat()} {target_time.strftime('%H:%M')}"
        else:
            start = datetime.combine(target_day, time.min)
            end = start + timedelta(days=1)
            label = target_day.isoformat()

        out = eventkit("calendar-today") if not day and not target_time else ""
        if not out:
            out = _calendar_events(start, end)
        if out.startswith("error"):
            return ConnectorResult(f"Calendar free/busy unavailable for {label}: {out}", {"source": self.source, "day": target_day.isoformat(), "time_text": time_text})
        lines = [line for line in out.splitlines() if line.strip()][:20]
        if target_time:
            status = "busy" if lines else "free"
            text = f"Calendar appears {status} for {label}." + ("\n" + "\n".join(lines) if lines else "")
        else:
            text = f"Calendar free/busy for {label}:" + ("\n" + "\n".join(lines) if lines else " no events found")
        return ConnectorResult(text[:2000], {"source": self.source, "day": target_day.isoformat(), "time_text": time_text, "busy_count": len(lines)})

    def create_event(self, title: str, dry_run: bool = True) -> ConnectorResult:
        if dry_run or not self.can_write:
            return ConnectorResult(f"DRY RUN calendar event: {title}", {"requires_approval": True})
        out = eventkit("create-event", title)
        if not out:
            script = 'tell application "Calendar" to tell default calendar to make new event with properties {summary:' + q(title) + ', start date:(current date), end date:(current date) + 3600}'
            out = run_osa(script)
        return ConnectorResult(out, {"source": self.source})
