"""Optional local vision-language image understanding client."""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import urllib.request
from pathlib import Path


class ImageUnderstandingClient:
    """OpenAI-compatible VLM client.

    Configure with `OPENSIRI_VLM_URL`, `OPENSIRI_VLM_MODEL`, and optional
    `OPENSIRI_VLM_API_KEY`. The URL may be either a base URL or a full
    `/chat/completions` Foundry/OpenAI-compatible target URI.
    """

    def __init__(self, base_url: str | None = None, model: str | None = None, api_key: str | None = None, auth_header: str | None = None, timeout: float = 90.0):
        vlm_model = model if model is not None else os.environ.get("OPENSIRI_VLM_MODEL", "")
        vlm_base_url = base_url if base_url is not None else os.environ.get("OPENSIRI_VLM_URL", "")
        
        # Auto-configure for Grok if specified and unconfigured
        is_grok = vlm_model and "grok" in vlm_model.lower()
        if is_grok:
            if not vlm_base_url:
                vlm_base_url = "https://api.x.ai/v1"
            auth_header = auth_header or os.environ.get("OPENSIRI_VLM_AUTH_HEADER") or "Authorization"
        else:
            auth_header = auth_header or os.environ.get("OPENSIRI_VLM_AUTH_HEADER") or "api-key"
            
        self.base_url = vlm_base_url.rstrip("/")
        self.model = vlm_model
        
        # Resolve API Key
        vlm_api_key = api_key if api_key is not None else os.environ.get("OPENSIRI_VLM_API_KEY", "")
        if not vlm_api_key and is_grok:
            vlm_api_key = os.environ.get("XAI_API_KEY", "")
        self.api_key = vlm_api_key
        self.auth_header = auth_header
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.model)

    def chat_url(self) -> str:
        if self.base_url.endswith("/chat/completions"):
            return self.base_url
        return self.base_url + "/v1/chat/completions"

    def describe(self, image_path: str | Path, prompt: str = "Describe this image for a personal assistant. Mention visible text, people, objects, places, and anything useful for search.") -> str:
        if not self.configured:
            return ""
        path = Path(image_path)
        mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
        data_url = "data:" + mime + ";base64," + base64.b64encode(path.read_bytes()).decode("ascii")
        payload = {
            "model": self.model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }],
            "temperature": 0.1,
            "max_tokens": 500,
        }
        headers = {"Content-Type": "application/json", "User-Agent": "opensiri-ai/0.1"}
        if self.api_key:
            headers[self.auth_header] = self.api_key if self.auth_header.lower() != "authorization" else "Bearer " + self.api_key
        req = urllib.request.Request(self.chat_url(), data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return f"vision model unavailable: {type(e).__name__}"
        try:
            return str(raw["choices"][0]["message"]["content"]).strip()
        except Exception:
            return "vision model returned an unreadable response"
