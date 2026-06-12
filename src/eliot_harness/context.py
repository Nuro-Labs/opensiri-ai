"""Compile task, screen, permissions, and optional memory into Eliot context."""

from __future__ import annotations

from dataclasses import dataclass, field

from .hypersave import HypersaveClient
from .permissions import PermissionState, Source


@dataclass
class ContextBundle:
    memory_lines: list[str] = field(default_factory=list)
    permission_lines: list[str] = field(default_factory=list)

    def render(self) -> str:
        parts: list[str] = []
        if self.permission_lines:
            parts.append("PERMISSIONS:\n" + "\n".join(f"- {x}" for x in self.permission_lines))
        if self.memory_lines:
            parts.append("MEMORY:\n" + "\n".join(f"- {x}" for x in self.memory_lines))
        return "\n".join(parts)


class ContextCompiler:
    def __init__(self, permissions: PermissionState, memory: HypersaveClient | None = None):
        self.permissions = permissions
        self.memory = memory

    def compile(self, task: str) -> ContextBundle:
        bundle = ContextBundle()
        bundle.permission_lines.extend(self._permission_summary())
        if self.memory and self.permissions.can_read(Source.HYPERSAVE):
            bundle.memory_lines.extend(self._memory_for_task(task))
        return bundle

    def _permission_summary(self) -> list[str]:
        return [
            "destructive actions require explicit user approval",
            "network is " + ("enabled with approval" if self.permissions.network_enabled else "disabled unless explicitly approved"),
            "memory read is " + ("enabled" if self.permissions.can_read(Source.HYPERSAVE) else "disabled"),
            "memory write is " + ("enabled with approval" if self.permissions.can_write(Source.HYPERSAVE) else "disabled"),
        ]

    def _memory_for_task(self, task: str) -> list[str]:
        try:
            result = self.memory.search(task, limit=5) if self.memory else {}
        except Exception as e:
            return [f"memory unavailable: {type(e).__name__}"]
        lines: list[str] = []
        for key in ("results", "memories", "documents", "facts"):
            values = result.get(key)
            if isinstance(values, list):
                for item in values[:5]:
                    text = item.get("content") or item.get("text") or item.get("summary") or str(item)
                    s = str(text).strip()
                    if not s or "undefined" in s.lower():
                        continue
                    lines.append(s[:300])
                break
        return lines[:5]
