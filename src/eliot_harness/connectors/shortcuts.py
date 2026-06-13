"""Shortcuts connector."""

from __future__ import annotations

import subprocess

from .base import Connector, ConnectorResult


class ShortcutsConnector(Connector):
    name = "shortcuts"
    source = "shortcuts"
    can_read = True
    can_write = False

    def list_shortcuts(self) -> ConnectorResult:
        try:
            r = subprocess.run(["shortcuts", "list"], capture_output=True, text=True, timeout=15)
            return ConnectorResult(r.stdout.strip()[:2000] if r.returncode == 0 else "shortcuts list unavailable", {"source": self.source})
        except Exception:
            return ConnectorResult("shortcuts CLI unavailable", {"source": self.source})

    def run_shortcut(self, name: str, dry_run: bool = True) -> ConnectorResult:
        if dry_run or not self.can_write:
            return ConnectorResult(f"DRY RUN run shortcut: {name}", {"requires_approval": True})
        r = subprocess.run(["shortcuts", "run", name], capture_output=True, text=True, timeout=60)
        return ConnectorResult(r.stdout.strip() or r.stderr.strip() or "shortcut run requested", {"source": self.source})

    def create_automation(self, description: str, dry_run: bool = True) -> ConnectorResult:
        return ConnectorResult(f"DRY RUN shortcut automation plan: {description}", {"source": self.source, "requires_approval": True})
