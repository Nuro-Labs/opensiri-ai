"""OpenAI-compatible client for Eliot."""

from __future__ import annotations

import json
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
    def __init__(self, base_url: str = "http://localhost:8081", model: str = "default_model", thinking: bool = False):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.thinking = thinking

    def complete(self, messages: list[dict[str, Any]], max_tokens: int = 384) -> ModelResult:
        body = {
            "model": self.model,
            "messages": messages,
            "tools": OPENAI_TOOLS,
            "max_tokens": max_tokens,
            "temperature": 0.0,
            "chat_template_kwargs": {"enable_thinking": self.thinking},
        }
        req = urllib.request.Request(
            self.base_url + "/v1/chat/completions",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
        )
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
            return None
        return normalize_action({"name": m.group(1), "args": {pm.group(1): pm.group(2) for pm in PARAM_RE.finditer(m.group(2))}})
