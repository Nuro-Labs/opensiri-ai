"""Thin Hypersave API client for personal-context retrieval."""

from __future__ import annotations

import json
import os
import time
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass
class HypersaveClient:
    api_key: str
    base_url: str = "https://api.hypersave.io"
    timeout: float = 30.0

    @classmethod
    def from_env(cls) -> "HypersaveClient | None":
        key = os.environ.get("HYPERSAVE_API_KEY")
        if not key:
            return None
        return cls(api_key=key, base_url=os.environ.get("HYPERSAVE_BASE_URL", "https://api.hypersave.io"))

    def _request(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        data = json.dumps(body or {}).encode() if body is not None else None
        req = urllib.request.Request(
            self.base_url.rstrip("/") + path,
            data=data,
            method=method,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": self.api_key,
                "User-Agent": "opensiri-ai/0.1 (+https://github.com/Nuro-Labs/opensiri-ai)",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Hypersave HTTP {e.code}") from e

    def ask(self, query: str, max_sensitivity: str = "high") -> dict[str, Any]:
        return self._request("POST", "/v1/ask", {"query": query, "maxSensitivity": max_sensitivity})

    def search(self, query: str, limit: int = 8, max_sensitivity: str = "high") -> dict[str, Any]:
        return self._request("POST", "/v1/search", {"query": query, "limit": limit, "maxSensitivity": max_sensitivity})

    def save(self, content: str, source: str, sensitivity: str = "medium") -> dict[str, Any]:
        return self._request("POST", "/v1/save", {"content": content, "type": "text", "category": source, "sensitivity": sensitivity})

    def save_and_wait(self, content: str, source: str, sensitivity: str = "medium", timeout_s: float = 90.0) -> dict[str, Any]:
        result = self.save(content, source, sensitivity)
        pending_id = result.get("pendingId") or result.get("data", {}).get("pendingId")
        if not pending_id:
            return result
        deadline = time.time() + timeout_s
        last: dict[str, Any] = result
        while time.time() < deadline:
            time.sleep(3)
            try:
                last = self.save_status(str(pending_id))
            except Exception:
                continue
            status = str(last.get("status") or last.get("data", {}).get("status") or "").lower()
            if status in ("complete", "completed", "done", "failed"):
                return last
        return last

    def save_status(self, pending_id: str) -> dict[str, Any]:
        return self._request("GET", f"/v1/save/status/{pending_id}")

    def facts(self) -> dict[str, Any]:
        return self._request("GET", "/v1/facts")

    def profile(self) -> dict[str, Any]:
        return self._request("GET", "/v1/profile")
