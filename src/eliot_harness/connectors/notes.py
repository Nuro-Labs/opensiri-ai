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

    def search_notes(self, query: str, limit: int = 10) -> list[ConnectorResult]:
        script = '''tell application "Notes"
set out to {}
set i to 0
repeat with n in notes
  if name of n contains ''' + q(query) + ''' or body of n contains ''' + q(query) + ''' then
    set i to i + 1
    set end of out to "Note: " & (name of n)
    if i >= ''' + str(max(1, min(limit, 50))) + ''' then exit repeat
  end if
end repeat
return out
end tell'''
        out = run_osa(script, timeout=20)
        return [ConnectorResult(x.strip(), {"source": self.source}) for x in out.split(",") if x.strip() and not out.startswith("error")]

    def append_note(self, title: str, body: str, dry_run: bool = True) -> ConnectorResult:
        if dry_run or not self.can_write:
            return ConnectorResult(f"DRY RUN append to note {title}: {body}", {"requires_approval": True})
        script = '''tell application "Notes"
set matches to notes whose name contains ''' + q(title) + '''
if matches is {} then
  make new note at folder "Notes" with properties {name:''' + q(title) + ''', body:''' + q(body) + '''}
else
  set body of item 1 of matches to (body of item 1 of matches) & "\n" & ''' + q(body) + '''
end if
end tell'''
        return ConnectorResult(run_osa(script), {"source": self.source})
