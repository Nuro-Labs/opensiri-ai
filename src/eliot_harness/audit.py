"""Redacted audit logging for tool execution."""

from __future__ import annotations

import copy
import json
import re
import time
from pathlib import Path
from typing import Any

SECRET_RE = re.compile(r"\b(sk-[A-Za-z0-9_-]+|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9_]+|hs_live_[A-Za-z0-9_-]+)\b")


def redact(value: Any) -> Any:
    if isinstance(value, str):
        return SECRET_RE.sub("[REDACTED_SECRET]", value)
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, dict):
        return {k: redact(v) for k, v in value.items()}
    return value


def append_audit(path: str | Path, event: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    rec = redact(copy.deepcopy(event))
    rec["ts"] = time.time()
    with p.open("a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
