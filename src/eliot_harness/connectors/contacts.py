"""Contacts connector."""

from __future__ import annotations

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
        out = []
        for name in names:
            script = 'tell application "Contacts" to get name of people whose name contains ' + q(name)
            got = run_osa(script)
            if got and not got.startswith("error"):
                out.append(f"Contacts matching {name}: {got}")
        return [ConnectorResult(x, {"source": self.source}) for x in out]
