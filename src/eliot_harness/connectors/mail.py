"""Mail connector.

Sending always requires approval; by default this connector only drafts.
"""

from __future__ import annotations

from .applescript import q, run_osa
from .base import Connector, ConnectorResult


class MailConnector(Connector):
    name = "mail"
    source = "mail"
    can_read = False
    can_write = False

    def read_context(self, task: str) -> list[ConnectorResult]:
        if not self.can_read or not any(x in task.lower() for x in ("email", "mail", "inbox")):
            return []
        selected = self.selected_messages(limit=5)
        if selected:
            return selected
        return self.recent_messages(limit=5)

    def selected_messages(self, limit: int = 10) -> list[ConnectorResult]:
        script = '''tell application "Mail"
set out to {}
set i to 0
repeat with m in selection
  set i to i + 1
  set end of out to "Subject: " & (subject of m) & " | From: " & (sender of m) & " | Date: " & ((date received of m) as string) & " | Body: " & (content of m)
  if i >= ''' + str(limit) + ''' then exit repeat
end repeat
return out
end tell'''
        out = run_osa(script)
        return self._split_results(out, "selected_mail")

    def recent_messages(self, days: int = 7, limit: int = 20) -> list[ConnectorResult]:
        script = '''set cutoff to (current date) - (''' + str(days) + ''' * days)
tell application "Mail"
set out to {}
set i to 0
set matches to messages of inbox whose date received is greater than cutoff
repeat with m in matches
  set i to i + 1
  set end of out to "Subject: " & (subject of m) & " | From: " & (sender of m) & " | Date: " & ((date received of m) as string) & " | Body: " & (content of m)
  if i >= ''' + str(limit) + ''' then exit repeat
end repeat
return out
end tell'''
        out = run_osa(script, timeout=45)
        return self._split_results(out, "recent_mail")

    def _split_results(self, out: str, kind: str) -> list[ConnectorResult]:
        if not out or out.startswith("error"):
            return []
        rows = [x.strip() for x in out.replace(", Subject:", "\nSubject:").splitlines() if x.strip()]
        return [ConnectorResult(row[:1200], {"source": self.source, "kind": kind}) for row in rows[: self.max_context_items]]

    def draft_email(self, to: str, subject: str, body: str, dry_run: bool = True) -> ConnectorResult:
        if dry_run or not self.can_write:
            return ConnectorResult(f"Draft email to {to}\nSubject: {subject}\n\n{body}", {"requires_approval": False})
        script = (
            'tell application "Mail" to make new outgoing message with properties '
            '{visible:true, subject:' + q(subject) + ', content:' + q(body) + '} '
            'with make new to recipient at end of to recipients with properties {address:' + q(to) + '}'
        )
        return ConnectorResult(run_osa(script), {"source": self.source})

    def send_email(self, to: str, subject: str, body: str) -> ConnectorResult:
        return ConnectorResult(f"SEND REQUIRES APPROVAL: {to} / {subject}", {"requires_approval": True, "tier": "external"})
