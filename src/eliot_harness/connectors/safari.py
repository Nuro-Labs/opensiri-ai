"""Safari connector."""

from __future__ import annotations

from .applescript import run_osa
from .base import Connector, ConnectorResult


class SafariConnector(Connector):
    name = "safari"
    source = "safari"
    can_read = True
    can_write = False

    def read_context(self, task: str) -> list[ConnectorResult]:
        if not any(x in task.lower() for x in ("safari", "browser", "tab", "webpage")):
            return []
        script = 'tell application "Safari" to get name of tabs of windows'
        out = run_osa(script)
        return [ConnectorResult(f"Safari tabs: {out}", {"source": self.source})]
