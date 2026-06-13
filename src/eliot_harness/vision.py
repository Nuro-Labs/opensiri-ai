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

    Configure with `OPENSIRI_VLM_URL` and `OPENSIRI_VLM_MODEL`. The default is
    intentionally unconfigured so image data stays local unless explicitly wired.
    """

    def __init__(self, base_url: str | None = None, model: str | None = None, timeout: float = 90.0):
        self.base_url = (base_url if base_url is not None else os.environ.get("OPENSIRI_VLM_URL", "")).rstrip("/")
        self.model = model if model is not None else os.environ.get("OPENSIRI_VLM_MODEL", "")
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.model)

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
        req = urllib.request.Request(
            self.base_url + "/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "opensiri-ai/0.1"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return f"vision model unavailable: {type(e).__name__}"
        try:
            return str(raw["choices"][0]["message"]["content"]).strip()
        except Exception:
            return "vision model returned an unreadable response"
