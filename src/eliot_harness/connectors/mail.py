"""Mail connector.

Sending always requires approval; by default this connector only drafts.
"""

from __future__ import annotations

import re

from .applescript import q, run_osa
from .base import Connector, ConnectorResult


STOPWORDS = {
    "about", "already", "email", "emails", "find", "from", "have", "mail", "meeting", "message", "messages", "please", "show", "that", "the", "with",
}


class MailConnector(Connector):
    name = "mail"
    source = "mail"
    can_read = False
    can_write = False

    def read_context(self, task: str) -> list[ConnectorResult]:
        if not self.can_read or not any(x in task.lower() for x in ("email", "mail", "inbox")):
            return []
        if any(x in task.lower() for x in ("selected", "this email", "current email", "open email")):
            selected = self.selected_messages(limit=5)
            if selected:
                return selected
        searched = self.search_messages(task, limit=5)
        if searched:
            return searched
        selected = self.selected_messages(limit=3)
        if selected and any(x in task.lower() for x in ("latest", "recent", "inbox")):
            return selected
        return self.recent_messages(limit=5)

    def search_messages(self, query: str, days: int = 365, scan_limit: int = 120, limit: int = 10) -> list[ConnectorResult]:
        terms = [t for t in re.findall(r"[A-Za-z0-9][A-Za-z0-9+.-]{2,}", query.lower()) if t not in STOPWORDS]
        if not terms:
            return []
        contains_checks = " or ".join(["subject of m contains " + q(term) + " or sender of m contains " + q(term) for term in terms[:6]])
        script = '''set cutoff to (current date) - (''' + str(days) + ''' * days)
tell application "Mail"
set out to {}
set i to 0
set matches to messages of inbox whose date received is greater than cutoff
repeat with m in matches
  if ''' + contains_checks + ''' then
    set i to i + 1
    set end of out to "Subject: " & (subject of m) & " | From: " & (sender of m) & " | Date: " & ((date received of m) as string)
    if i >= ''' + str(scan_limit) + ''' then exit repeat
  end if
end repeat
return out
end tell'''
        out = run_osa(script, timeout=30)
        rows = self._split_results(out, "mail_search_scan")
        ranked: list[tuple[int, ConnectorResult]] = []
        for row in rows:
            low = row.text.lower()
            score = sum(1 for term in terms if term in low)
            if score:
                ranked.append((score, ConnectorResult(row.text, {"source": self.source, "kind": "mail_search", "terms": terms, "score": score})))
        ranked.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in ranked[:limit]]

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
        return [ConnectorResult(row[:1200], {"source": self.source, "kind": kind}) for row in rows[: max(self.max_context_items, 20)]]

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
