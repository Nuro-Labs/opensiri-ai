"""Visual/screenshot connector scaffold."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from .base import Connector, ConnectorResult


class VisualConnector(Connector):
    name = "visual"
    source = "visual"
    can_read = False
    can_write = False

    def capture_interactive(self) -> ConnectorResult:
        if not self.can_read:
            return ConnectorResult("visual capture disabled", {"requires_permission": "Screen Recording"})
        path = Path(tempfile.gettempdir()) / "opensiri-capture.png"
        try:
            r = subprocess.run(["screencapture", "-i", str(path)], capture_output=True, text=True, timeout=120)
        except Exception as e:
            return ConnectorResult(f"screenshot failed: {type(e).__name__}")
        if r.returncode != 0 or not path.exists():
            return ConnectorResult("screenshot cancelled or failed")
        return ConnectorResult(f"screenshot captured: {path}", {"path": str(path), "source": self.source})

    def read_context(self, task: str) -> list[ConnectorResult]:
        if any(x in task.lower() for x in ("screen", "screenshot", "image", "photo", "looking at", "movie is this")):
            return [ConnectorResult("Visual connector available but disabled by default. Enable visual capture to inspect screenshots.", {"source": self.source})]
        return []
