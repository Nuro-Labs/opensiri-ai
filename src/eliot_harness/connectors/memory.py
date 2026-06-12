"""Hypersave connector."""

from __future__ import annotations

from .base import Connector, ConnectorResult
from ..hypersave import HypersaveClient


class MemoryConnector(Connector):
    name = "hypersave"

    def __init__(self, client: HypersaveClient | None):
        self.client = client

    def read_context(self, task: str) -> list[ConnectorResult]:
        if not self.client:
            return []
        try:
            data = self.client.search(task, limit=5)
        except Exception as e:
            return [ConnectorResult(text=f"Hypersave unavailable: {type(e).__name__}")]
        out: list[ConnectorResult] = []
        for key in ("results", "memories", "documents", "facts"):
            vals = data.get(key)
            if isinstance(vals, list):
                for item in vals[:5]:
                    text = item.get("content") or item.get("text") or item.get("summary") or str(item)
                    s = str(text).strip()
                    if not s or "undefined" in s.lower():
                        continue
                    out.append(ConnectorResult(text=s[:300], metadata={"source": key}))
                break
        return out

    def ask(self, query: str) -> str:
        if not self.client:
            return "memory unavailable"
        data = self.client.ask(query)
        return str(data.get("answer") or data)

    def save(self, content: str, source: str, sensitivity: str = "medium") -> str:
        if not self.client:
            return "memory unavailable"
        return str(self.client.save(content, source=source, sensitivity=sensitivity))
