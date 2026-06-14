"""Compile task, screen, permissions, and optional memory into Eliot context."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .hypersave import HypersaveClient
from .local_index import LocalIndex
from .permissions import PermissionState, Source
from .connectors.base import ConnectorRegistry


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
    def __init__(self, permissions: PermissionState, memory: HypersaveClient | None = None, registry: ConnectorRegistry | None = None, local_index: LocalIndex | None = None, transcript_path: str | None = None):
        self.permissions = permissions
        self.memory = memory
        self.registry = registry
        self.local_index = local_index
        self.transcript_path = transcript_path

    def compile(self, task: str) -> ContextBundle:
        bundle = ContextBundle()
        bundle.permission_lines.extend(self._permission_summary())
        prev_ctx = self._load_previous_transcript_context(task)
        if prev_ctx:
            bundle.memory_lines.append(prev_ctx)
        if self.memory and self.permissions.can_read(Source.HYPERSAVE):
            bundle.memory_lines.extend(self._memory_for_task(task))
        if self.local_index:
            bundle.memory_lines.extend(self._index_for_task(task))
        if self.registry:
            for item in self.registry.read_context(task):
                if item.text and "undefined" not in item.text.lower():
                    bundle.memory_lines.append(item.text[:300])
        return bundle

    def _load_previous_transcript_context(self, current_task: str) -> str | None:
        if not self.transcript_path:
            return None
        import os
        p = Path(self.transcript_path)
        if not p.exists() or os.path.getsize(p) == 0:
            return None
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            prev_task = data.get("task")
            if not prev_task or prev_task == current_task:
                return None
            turns = data.get("turns", [])
            if not turns:
                return None
            last_turn = turns[-1]
            last_result = last_turn.get("result") or ""
            if not last_result:
                return None
            return f"RECENT CHAT HISTORY:\n- User previous request: \"{prev_task}\"\n- Assistant previous final response: \"{last_result[:800]}\""
        except Exception:
            return None

    def _index_for_task(self, task: str) -> list[str]:
        try:
            hits = self.local_index.search(task, limit=6)
        except Exception as e:
            return [f"local index unavailable: {type(e).__name__}"]
        return [f"[{h.source}] {h.title} ({h.uri})\n{h.content[:500]}" for h in hits if h.content.strip()]

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
