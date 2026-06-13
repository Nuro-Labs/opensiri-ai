"""Session state for multi-step assistant operation."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any
from .references import ReferenceStore


@dataclass
class SessionState:
    task: str
    session_id: str = field(default_factory=lambda: "sess_" + uuid.uuid4().hex[:12])
    started_at: float = field(default_factory=time.time)
    current_app: str | None = None
    goal: str | None = None
    facts_used: list[str] = field(default_factory=list)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    references: ReferenceStore = field(default_factory=ReferenceStore)
    turns: int = 0

    def remember_decision(self, action: str, decision: str, reason: str) -> None:
        self.decisions.append({"action": action, "decision": decision, "reason": reason, "ts": time.time()})
