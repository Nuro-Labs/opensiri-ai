"""Reference resolver for pronouns like it/that/those."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ReferenceObject:
    ref_id: str
    kind: str
    summary: str
    value: Any


@dataclass
class ReferenceStore:
    objects: list[ReferenceObject] = field(default_factory=list)

    def add(self, kind: str, summary: str, value: Any) -> ReferenceObject:
        obj = ReferenceObject(f"ref_{len(self.objects)+1}", kind, summary, value)
        self.objects.append(obj)
        return obj

    def latest(self, kind: str | None = None) -> ReferenceObject | None:
        for obj in reversed(self.objects):
            if kind is None or obj.kind == kind:
                return obj
        return None

    def resolve_text(self, text: str) -> ReferenceObject | None:
        low = text.lower()
        if any(p in low for p in ("send it", "send that", "email it")):
            return self.latest("draft")
        if any(p in low for p in ("add that", "add it", "remind me about that", "save that")):
            return self.latest()
        if any(p in low for p in ("those", "these")):
            return self.latest("selection") or self.latest("files")
        return None
