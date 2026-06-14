"""AppleScript helpers for macOS app connectors."""

from __future__ import annotations

import subprocess

from ..process import run_command_robust


def q(value) -> str:
    return '"' + str(value).replace('"', '\\"') + '"'


def run_osa(script: str, timeout: float = 30.0) -> str:
    res = run_command_robust(["osascript", "-e", script], timeout=timeout)
    if res.timed_out:
        return "error: osascript timed out"
    if res.error:
        return f"error: {res.error}"
    if res.returncode != 0:
        return "error: " + (res.stderr.strip() or f"osascript exit {res.returncode}")[:500]
    return res.stdout.strip() or "ok"


def tell(app: str, body: str) -> str:
    return f'tell application {q(app)} to {body}'
