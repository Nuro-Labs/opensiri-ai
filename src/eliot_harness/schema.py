"""Canonical Eliot tool schema and observation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


ActionName = Literal[
    "click",
    "type",
    "open_app",
    "read",
    "run_shell",
    "web_search",
    "invoke_intent",
    "memory_search",
    "memory_ask",
    "memory_save",
    "ask_user",
    "done",
]


@dataclass
class Action:
    name: ActionName
    args: dict[str, Any]


def make_observation(task: str, app: str, ui_tree: str, result: str, context: str = "") -> str:
    parts = [f"TASK: {task}", f"APP: {app}"]
    if context.strip():
        parts.append("PERSONAL_CONTEXT:\n" + context.strip())
    parts.extend(["UI:", ui_tree, f"RESULT: {result}"])
    return "\n".join(parts)


TOOLS = [
    "click",
    "type",
    "open_app",
    "read",
    "run_shell",
    "web_search",
    "invoke_intent",
    "memory_search",
    "memory_ask",
    "memory_save",
    "ask_user",
    "done",
]
