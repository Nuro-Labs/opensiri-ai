"""Read-only file context connector."""

from __future__ import annotations

import os
from pathlib import Path

from .base import Connector, ConnectorResult


class FilesConnector(Connector):
    name = "files"

    def __init__(self, roots: list[str] | None = None):
        self.roots = [Path(r).expanduser().resolve() for r in (roots or [os.getcwd()])]

    def read_context(self, task: str) -> list[ConnectorResult]:
        # Minimal safe context: expose allowed roots, not file contents.
        return [ConnectorResult(text=f"Files root available: {root}", metadata={"root": str(root)}) for root in self.roots]

    def is_allowed(self, path: str) -> bool:
        p = Path(path).expanduser().resolve()
        return any(str(p).startswith(str(root)) for root in self.roots)
