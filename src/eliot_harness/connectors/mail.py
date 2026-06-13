"""Mail connector.

Sending always requires approval; by default this connector only drafts.
"""

from __future__ import annotations

import re
import subprocess
import time
from email import policy
from email.parser import BytesParser
from pathlib import Path

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
        limit = max(1, min(limit, 25))

        results: list[ConnectorResult] = []
        seen: set[str] = set()
        for batch in (
            self._applescript_metadata_search(terms, days=days, scan_limit=scan_limit, limit=limit),
            self.spotlight_search(query, limit=limit),
            self.emlx_search(query, limit=max(limit, 20)),
        ):
            for row in batch:
                key = row.text.lower()
                if key in seen:
                    continue
                seen.add(key)
                results.append(row)
                if len(results) >= limit:
                    return results
        return results

    def _applescript_metadata_search(self, terms: list[str], days: int = 365, scan_limit: int = 120, limit: int = 10) -> list[ConnectorResult]:
        days = max(1, min(days, 3650))
        scan_limit = max(1, min(scan_limit, 250))
        limit = max(1, min(limit, 25))
        contains_checks = " or ".join(["subject contains " + q(term) + " or sender contains " + q(term) for term in terms[:6]])
        script = '''set cutoff to (current date) - (''' + str(days) + ''' * days)
tell application "Mail"
set out to {}
set i to 0
repeat with box in mailboxes
  try
    set matches to messages of box whose date received is greater than cutoff and (''' + contains_checks + ''')
    repeat with m in matches
      set i to i + 1
      set end of out to "Subject: " & (subject of m) & " | From: " & (sender of m) & " | Date: " & ((date received of m) as string) & " | Mailbox: " & (name of box)
      if i >= ''' + str(scan_limit) + ''' then exit repeat
    end repeat
    if i >= ''' + str(scan_limit) + ''' then exit repeat
  end try
end repeat
return out
end tell'''
        out = run_osa(script, timeout=20)
        rows = self._split_results(out, "mail_search_scan")
        ranked: list[tuple[int, ConnectorResult]] = []
        for row in rows:
            low = row.text.lower()
            score = sum(1 for term in terms if term in low)
            if score:
                ranked.append((score, ConnectorResult(row.text, {"source": self.source, "kind": "mail_search", "terms": terms, "score": score})))
        ranked.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in ranked[:limit]]

    def spotlight_search(self, query: str, limit: int = 10) -> list[ConnectorResult]:
        terms = [t for t in re.findall(r"[A-Za-z0-9][A-Za-z0-9+.-]{2,}", query.lower()) if t not in STOPWORDS]
        if not terms:
            return []
        limit = max(1, min(limit, 25))
        mail_root = (Path.home() / "Library" / "Mail").expanduser()
        if not mail_root.exists():
            return []
        needle = " && ".join([self._mdfind_term(term) for term in terms[:4]])
        metadata_query = 'kMDItemFSName == "*.emlx"c && (' + needle + ')'
        try:
            proc = subprocess.run(
                ["mdfind", "-onlyin", str(mail_root), metadata_query],
                capture_output=True,
                text=True,
                timeout=6,
            )
        except (OSError, subprocess.TimeoutExpired):
            return []
        if proc.returncode != 0:
            return []
        paths: list[Path] = []
        for raw in proc.stdout.splitlines()[: limit * 4]:
            path = Path(raw)
            if path.suffix == ".emlx" and self._is_under(path, mail_root):
                paths.append(path)
            if len(paths) >= limit * 2:
                break
        return self._search_emlx_paths(paths, terms, limit=limit, kind="mail_spotlight")

    def emlx_search(self, query: str, limit: int = 20, max_files: int = 1000) -> list[ConnectorResult]:
        terms = [t for t in re.findall(r"[A-Za-z0-9][A-Za-z0-9+.-]{2,}", query.lower()) if t not in STOPWORDS]
        if not terms:
            return []
        limit = max(1, min(limit, 50))
        max_files = max(1, min(max_files, 5000))
        mail_root = (Path.home() / "Library" / "Mail").expanduser()
        if not mail_root.exists():
            return []
        paths: list[Path] = []
        started = time.monotonic()
        try:
            for path in mail_root.rglob("*.emlx"):
                if time.monotonic() - started > 8:
                    break
                paths.append(path)
                if len(paths) >= max_files:
                    break
        except OSError:
            return []
        return self._search_emlx_paths(paths, terms, limit=limit, kind="mail_emlx")

    def _search_emlx_paths(self, paths: list[Path], terms: list[str], limit: int, kind: str) -> list[ConnectorResult]:
        ranked: list[tuple[int, ConnectorResult]] = []
        started = time.monotonic()
        for path in paths:
            if len(ranked) >= limit or time.monotonic() - started > 8:
                break
            result = self._parse_emlx_match(path, terms, kind)
            if result:
                score = int(result.metadata.get("score", 1) if result.metadata else 1)
                ranked.append((score, result))
        ranked.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in ranked[:limit]]

    def _parse_emlx_match(self, path: Path, terms: list[str], kind: str) -> ConnectorResult | None:
        try:
            with path.open("rb") as f:
                raw = f.read(128_000)
        except OSError:
            return None
        size_line, _, rest = raw.partition(b"\n")
        if not rest:
            return None
        try:
            declared_size = int(size_line.strip())
        except ValueError:
            declared_size = len(rest)
        payload = rest[:declared_size]
        try:
            msg = BytesParser(policy=policy.default).parsebytes(payload)
        except Exception:
            return None
        subject = str(msg.get("subject", ""))[:240]
        sender = str(msg.get("from", ""))[:240]
        date = str(msg.get("date", ""))[:120]
        body = self._message_text(msg)[:4000]
        searchable = " ".join([subject, sender, date, body]).lower()
        score = sum(1 for term in terms if term in searchable)
        if not score:
            return None
        snippet = self._snippet(body, terms)
        text = f"Subject: {subject} | From: {sender} | Date: {date}"
        if snippet:
            text += f" | Snippet: {snippet}"
        return ConnectorResult(text[:1200], {"source": self.source, "kind": kind, "terms": terms, "score": score})

    def _message_text(self, msg) -> str:
        if msg.is_multipart():
            parts: list[str] = []
            for part in msg.walk():
                if part.get_content_type() != "text/plain":
                    continue
                try:
                    parts.append(part.get_content())
                except Exception:
                    continue
            return "\n".join(parts)
        try:
            content = msg.get_content()
        except Exception:
            return ""
        return content if isinstance(content, str) else ""

    def _snippet(self, text: str, terms: list[str], radius: int = 120) -> str:
        compact = re.sub(r"\s+", " ", text).strip()
        low = compact.lower()
        positions = [low.find(term) for term in terms if low.find(term) >= 0]
        if not positions:
            return compact[: radius * 2]
        pos = min(positions)
        start = max(0, pos - radius)
        end = min(len(compact), pos + radius)
        return compact[start:end]

    def _mdfind_term(self, term: str) -> str:
        safe = term.replace('"', '\\"')
        return '(kMDItemTextContent == "*' + safe + '*"cd || kMDItemDisplayName == "*' + safe + '*"cd || kMDItemAuthors == "*' + safe + '*"cd)'

    def _is_under(self, path: Path, root: Path) -> bool:
        try:
            path.resolve().relative_to(root.resolve())
        except (OSError, ValueError):
            return False
        return True

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

    def flag_selected(self, dry_run: bool = True) -> ConnectorResult:
        if dry_run or not self.can_write:
            return ConnectorResult("DRY RUN flag selected Mail messages", {"requires_approval": True})
        return ConnectorResult(run_osa('tell application "Mail" to set flagged status of selection to true'), {"source": self.source})

    def mark_selected_unread(self, dry_run: bool = True) -> ConnectorResult:
        if dry_run or not self.can_write:
            return ConnectorResult("DRY RUN mark selected Mail messages unread", {"requires_approval": True})
        return ConnectorResult(run_osa('tell application "Mail" to set read status of selection to false'), {"source": self.source})

    def archive_selected(self, dry_run: bool = True) -> ConnectorResult:
        if dry_run or not self.can_write:
            return ConnectorResult("DRY RUN archive selected Mail messages", {"requires_approval": True})
        script = '''tell application "Mail"
repeat with m in selection
  move m to mailbox "Archive"
end repeat
end tell'''
        return ConnectorResult(run_osa(script), {"source": self.source})

    def selected_attachments(self, limit: int = 20) -> list[ConnectorResult]:
        script = '''tell application "Mail"
set out to {}
set i to 0
repeat with m in selection
  repeat with a in mail attachments of m
    set i to i + 1
    set end of out to "Attachment: " & (name of a) & " | Message: " & (subject of m)
    if i >= ''' + str(max(1, min(limit, 100))) + ''' then exit repeat
  end repeat
end repeat
return out
end tell'''
        out = run_osa(script)
        return self._split_results(out, "mail_attachments")

    def thread_summary(self, query: str) -> ConnectorResult:
        results = self.search_messages(query, limit=10)
        if not results:
            return ConnectorResult("no matching mail thread found", {"source": self.source})
        return ConnectorResult("\n".join(r.text for r in results), {"source": self.source, "count": len(results)})
