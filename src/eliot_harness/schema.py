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
    "local_search",
    "mail_search",
    "messages_search",
    "file_search",
    "reminders_list",
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
    "local_search",
    "mail_search",
    "messages_search",
    "file_search",
    "reminders_list",
    "ask_user",
    "done",
]


OPENAI_TOOLS = [
    {"type": "function", "function": {"name": "click", "description": "Click/select a UI element by id.", "parameters": {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]}}},
    {"type": "function", "function": {"name": "type", "description": "Type text into a UI element by id.", "parameters": {"type": "object", "properties": {"id": {"type": "integer"}, "text": {"type": "string"}}, "required": ["id", "text"]}}},
    {"type": "function", "function": {"name": "open_app", "description": "Open or foreground a macOS app.", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "read", "description": "Read a UI element by id.", "parameters": {"type": "object", "properties": {"id": {"type": "integer"}}, "required": ["id"]}}},
    {"type": "function", "function": {"name": "run_shell", "description": "Run a local shell command through the harness.", "parameters": {"type": "object", "properties": {"cmd": {"type": "string"}}, "required": ["cmd"]}}},
    {"type": "function", "function": {"name": "web_search", "description": "Use bounded harness web search.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "max_results": {"type": "integer"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "invoke_intent", "description": "Invoke a structured app intent.", "parameters": {"type": "object", "properties": {"app": {"type": "string"}, "intent": {"type": "string"}, "params": {"type": "object"}}, "required": ["app", "intent", "params"]}}},
    {"type": "function", "function": {"name": "memory_search", "description": "Search approved personal memory.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "memory_ask", "description": "Ask approved personal memory.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "memory_save", "description": "Save content to memory after approval.", "parameters": {"type": "object", "properties": {"content": {"type": "string"}, "source": {"type": "string"}, "sensitivity": {"type": "string"}}, "required": ["content", "source"]}}},
    {"type": "function", "function": {"name": "local_search", "description": "Search the local background full-text index across files, mail, messages, notes, reminders, calendar, photos, and browser context. Use this before opening apps for personal context lookups.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "mail_search", "description": "Search Mail backend read-only for matching emails. Returns sender, subject, date, and snippet. Never sends or modifies mail.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "messages_search", "description": "Search local Messages read-only index/database for matching recent messages. Requires explicit Messages access.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "file_search", "description": "Search allowed local file roots by filename/content through the local index. Use before opening Finder.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "reminders_list", "description": "List visible Apple Reminders read-only. Does not create, complete, or delete reminders.", "parameters": {"type": "object", "properties": {"limit": {"type": "integer"}}, "required": []}}},
    {"type": "function", "function": {"name": "ask_user", "description": "Ask the user for confirmation or clarification.", "parameters": {"type": "object", "properties": {"question": {"type": "string"}}, "required": ["question"]}}},
    {"type": "function", "function": {"name": "done", "description": "Finish the task.", "parameters": {"type": "object", "properties": {"summary": {"type": "string"}}, "required": ["summary"]}}},
]


def normalize_action(raw: dict[str, Any] | None) -> Action | None:
    if not raw or not isinstance(raw, dict):
        return None
    name = raw.get("name")
    args = raw.get("args") or {}
    if name not in TOOLS or not isinstance(args, dict):
        return None
    return Action(name=name, args=args)  # type: ignore[arg-type]
