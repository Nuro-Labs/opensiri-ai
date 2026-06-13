"""AppleScript helpers for macOS app connectors."""

from __future__ import annotations

import subprocess


def q(value) -> str:
    return '"' + str(value).replace('"', '\\"') + '"'


def run_osa(script: str, timeout: float = 30.0) -> str:
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        return "error: " + (r.stderr.strip() or f"osascript exit {r.returncode}")[:500]
    return r.stdout.strip() or "ok"


def tell(app: str, body: str) -> str:
    return f'tell application {q(app)} to {body}'
