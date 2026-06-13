"""OpenAI-compatible client for Eliot."""

from __future__ import annotations

import json
import os
import re
import time
import urllib.request
from dataclasses import dataclass
from typing import Any

from .schema import Action, OPENAI_TOOLS, normalize_action

TC_RE = re.compile(r"<tool_call>\n?<function=([^>]+)>\n(.*?)</function>\n?</tool_call>", re.S)
PARAM_RE = re.compile(r"<parameter=([^>]+)>\n(.*?)\n</parameter>", re.S)


@dataclass
class ModelResult:
    action: Action | None
    latency_s: float
    raw: dict[str, Any]


class EliotModelClient:
    def __init__(self, base_url: str = "http://localhost:8081", model: str = "default_model", thinking: bool = False, api_key: str | None = None, auth_header: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.thinking = thinking
        self.api_key = api_key or os.environ.get("OPENSIRI_MODEL_API_KEY") or ""
        self.auth_header = auth_header or os.environ.get("OPENSIRI_MODEL_AUTH_HEADER") or "api-key"

    def chat_url(self) -> str:
        if self.base_url.endswith("/chat/completions"):
            return self.base_url
        return self.base_url + "/v1/chat/completions"

    def complete(self, messages: list[dict[str, Any]], max_tokens: int = 384) -> ModelResult:
        body = {
            "model": self.model,
            "messages": messages,
            "tools": OPENAI_TOOLS,
            "max_tokens": max_tokens,
            "temperature": 0.0,
        }
        if self.thinking:
            body["chat_template_kwargs"] = {"enable_thinking": True}
        headers = {"Content-Type": "application/json", "User-Agent": "opensiri-ai/0.1"}
        if self.api_key:
            headers[self.auth_header] = self.api_key if self.auth_header.lower() != "authorization" else "Bearer " + self.api_key
        req = urllib.request.Request(self.chat_url(), data=json.dumps(body).encode(), headers=headers)
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=600) as r:
            msg = json.load(r)["choices"][0]["message"]
        return ModelResult(action=self._parse_action(msg), latency_s=time.time() - t0, raw=msg)

    def _parse_action(self, msg: dict[str, Any]) -> Action | None:
        tcs = msg.get("tool_calls") or []
        if tcs:
            fn = tcs[0].get("function", tcs[0])
            args = fn.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    return None
            return normalize_action({"name": fn.get("name"), "args": args})
        content = msg.get("content") or ""
        m = TC_RE.search(content)
        if not m:
            content = content.strip()
            if "<tool_call" in content:
                return None
            if content:
                return normalize_action({"name": "done", "args": {"summary": content}})
            return None
        return normalize_action({"name": m.group(1), "args": {pm.group(1): pm.group(2) for pm in PARAM_RE.finditer(m.group(2))}})
