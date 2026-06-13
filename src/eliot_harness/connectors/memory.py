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
        try:
            data = self.client.ask(query)
            answer = str(data.get("answer") or data)
            if "don't have any saved information" not in answer.lower() and "could not find" not in answer.lower():
                return answer
            # Fallback to raw search; fresh async writes sometimes index before answer synthesis sees them.
            search = self.client.search(query, limit=5)
            snippets = []
            for key in ("results", "memories", "documents", "facts"):
                vals = search.get(key)
                if isinstance(vals, list):
                    for item in vals[:5]:
                        text = item.get("content") or item.get("text") or item.get("summary") or item.get("value") or str(item)
                        s = str(text).strip()
                        if s and "undefined" not in s.lower():
                            snippets.append(s[:300])
                    break
            return "\n".join(snippets) if snippets else answer
        except Exception as e:
            return f"memory unavailable: {type(e).__name__}"

    def save(self, content: str, source: str, sensitivity: str = "medium") -> str:
        if not self.client:
            return "memory unavailable"
        try:
            return str(self.client.save_and_wait(content, source=source, sensitivity=sensitivity))
        except Exception as e:
            return f"memory unavailable: {type(e).__name__}"
