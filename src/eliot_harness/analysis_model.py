"""Optional analysis model for bounded extracted text."""

from __future__ import annotations

import json
import os
import urllib.request


class AnalysisModelClient:
    def __init__(self, base_url: str | None = None, model: str | None = None, api_key: str | None = None, auth_header: str | None = None, timeout: float = 120.0):
        self.base_url = (base_url if base_url is not None else os.environ.get("OPENSIRI_ANALYSIS_URL", "")).rstrip("/")
        self.model = model if model is not None else os.environ.get("OPENSIRI_ANALYSIS_MODEL", "")
        self.api_key = api_key if api_key is not None else os.environ.get("OPENSIRI_ANALYSIS_API_KEY", "")
        self.auth_header = auth_header or os.environ.get("OPENSIRI_ANALYSIS_AUTH_HEADER") or "api-key"
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.model)

    def chat_url(self) -> str:
        if self.base_url.endswith("/chat/completions"):
            return self.base_url
        return self.base_url + "/v1/chat/completions"

    def analyze(self, prompt: str, text: str, max_chars: int = 16000) -> str:
        if not self.configured:
            return ""
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You analyze extracted local user documents. Be concise, cite evidence from the provided text, and do not invent missing details."},
                {"role": "user", "content": prompt + "\n\nEXTRACTED DOCUMENT TEXT:\n" + text[:max_chars]},
            ],
            "temperature": 0.1,
            "max_tokens": 700,
        }
        headers = {"Content-Type": "application/json", "User-Agent": "opensiri-ai/0.1"}
        if self.api_key:
            headers[self.auth_header] = self.api_key if self.auth_header.lower() != "authorization" else "Bearer " + self.api_key
        req = urllib.request.Request(self.chat_url(), data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
            return str(raw["choices"][0]["message"]["content"]).strip()
        except Exception as e:
            return f"analysis model unavailable: {type(e).__name__}"
