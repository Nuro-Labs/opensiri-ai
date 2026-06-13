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
        text = self.ocr_image(path)
        if text:
            return ConnectorResult(f"screenshot captured: {path}\nOCR:\n{text[:2000]}", {"path": str(path), "source": self.source, "ocr": True})
        return ConnectorResult(f"screenshot captured: {path}", {"path": str(path), "source": self.source, "ocr": False})

    def ocr_image(self, path: str | Path) -> str:
        helper = Path(__file__).resolve().parents[3] / "scripts" / "ocr_image.swift"
        if not helper.exists():
            return ""
        try:
            r = subprocess.run(["swift", str(helper), str(path)], capture_output=True, text=True, timeout=60)
        except Exception:
            return ""
        return r.stdout.strip() if r.returncode == 0 else ""

    def read_context(self, task: str) -> list[ConnectorResult]:
        if any(x in task.lower() for x in ("screen", "screenshot", "image", "looking at", "movie is this")):
            if not self.can_read:
                return [ConnectorResult("Visual connector available but disabled by default. Enable visual capture to inspect screenshots.", {"source": self.source})]
            return [self.capture_interactive()]
        return []
