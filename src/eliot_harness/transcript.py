"""Replayable run transcript."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Transcript:
    task: str
    turns: list[dict[str, Any]] = field(default_factory=list)
    started_at: float = field(default_factory=time.time)

    def add(self, rec: dict[str, Any]) -> None:
        self.turns.append(rec)

    def write(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"task": self.task, "started_at": self.started_at, "turns": self.turns}, indent=2, ensure_ascii=False))
