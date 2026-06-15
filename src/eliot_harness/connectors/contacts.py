"""Contacts connector."""

from __future__ import annotations

from typing import Any

from .applescript import q, run_osa
from .base import Connector, ConnectorResult


class ContactsConnector(Connector):
    name = "contacts"
    source = "contacts"
    can_read = True
    can_write = False

    def read_context(self, task: str) -> list[ConnectorResult]:
        # Avoid broad contact dumps. Only resolve obvious capitalized names.
        names = [w for w in task.replace("?", "").split() if w[:1].isupper() and len(w) > 2][:3]
        out: list[ConnectorResult] = []
        for name in names:
            out.extend(self.resolve_contact(name, limit=3))
        return out

    def execute(self, action_name: str, args: dict[str, Any]) -> ConnectorResult:
        if action_name == "resolve_contact":
            try:
                limit = int(args.get("limit", 5))
            except (TypeError, ValueError):
                limit = 5
            results = self.resolve_contact(str(args.get("name", "")), limit)
            return ConnectorResult("\n".join(x.text for x in results), {"source": self.source, "count": len(results)})
        return ConnectorResult(f"Unsupported contacts action: {action_name}", {"source": self.source})

    def resolve_contact(self, name: str, limit: int = 5) -> list[ConnectorResult]:
        query = name.strip()
        if len(query) < 2:
            return [ConnectorResult("Contact resolution needs at least 2 characters.", {"source": self.source, "query": query})]
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 5
        limit = max(1, min(limit, 20))
        script = f'''
set queryText to {q(query)}
set maxItems to {limit}
set contactLines to {{}}
tell application "Contacts"
    set matches to people whose name contains queryText
    set itemCount to 0
    repeat with personRef in matches
        if itemCount is greater than or equal to maxItems then exit repeat
        set personName to name of personRef
        set emailItems to {{}}
        repeat with emailRef in emails of personRef
            set end of emailItems to value of emailRef
        end repeat
        set phoneItems to {{}}
        repeat with phoneRef in phones of personRef
            set end of phoneItems to value of phoneRef
        end repeat
        set AppleScript's text item delimiters to ", "
        set emailText to emailItems as text
        set phoneText to phoneItems as text
        set AppleScript's text item delimiters to ""
        set end of contactLines to personName & " | emails: " & emailText & " | phones: " & phoneText
        set itemCount to itemCount + 1
    end repeat
end tell
set AppleScript's text item delimiters to linefeed
set out to contactLines as text
set AppleScript's text item delimiters to ""
return out
'''
        got = run_osa(script, timeout=10)
        if got.startswith("error"):
            return [ConnectorResult(f"Contacts unavailable for {query}: {got}", {"source": self.source, "query": query})]
        if got.strip().lower() == "ok":
            return [ConnectorResult(f"No contacts matching {query}.", {"source": self.source, "query": query, "count": 0})]
        lines = [line for line in got.splitlines() if line.strip() and line.strip().lower() != "ok"]
        if not lines:
            return [ConnectorResult(f"No contacts matching {query}.", {"source": self.source, "query": query, "count": 0})]
        return [ConnectorResult(f"Contact match for {query}: {line}", {"source": self.source, "query": query}) for line in lines[:limit]]
