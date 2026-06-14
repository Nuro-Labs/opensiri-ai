"""Shortcuts connector."""

from __future__ import annotations

from ..process import run_command_robust
from .base import Connector, ConnectorResult


class ShortcutsConnector(Connector):
    name = "shortcuts"
    source = "shortcuts"
    can_read = True
    can_write = False

    def list_shortcuts(self) -> ConnectorResult:
        res = run_command_robust(["shortcuts", "list"], timeout=15)
        if res.timed_out:
            return ConnectorResult("shortcuts list timed out", {"source": self.source})
        if res.error:
            return ConnectorResult(f"shortcuts CLI error: {res.error}", {"source": self.source})
        return ConnectorResult(res.stdout.strip()[:2000] if res.returncode == 0 else "shortcuts list unavailable", {"source": self.source})

    def run_shortcut(self, name: str, dry_run: bool = True) -> ConnectorResult:
        if dry_run or not self.can_write:
            return ConnectorResult(f"DRY RUN run shortcut: {name}", {"requires_approval": True})
        res = run_command_robust(["shortcuts", "run", name], timeout=60)
        if res.timed_out:
            return ConnectorResult("shortcuts execution timed out", {"source": self.source})
        if res.error:
            return ConnectorResult(f"shortcuts execution error: {res.error}", {"source": self.source})
        return ConnectorResult(res.stdout.strip() or res.stderr.strip() or "shortcut run requested", {"source": self.source})

    def create_automation(self, description: str, dry_run: bool = True) -> ConnectorResult:
        return ConnectorResult(f"DRY RUN shortcut automation plan: {description}", {"source": self.source, "requires_approval": True})
