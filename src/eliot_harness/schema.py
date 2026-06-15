"""Canonical tool schema and observation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


ActionName = Literal[
    "open_app", "run_shell", "read_file", "write_file",
    "web_search", "memory_search", "memory_ask", "memory_save",
    "local_search", "mail_search", "mail_draft", "mail_send", "mail_action",
    "messages_search", "message_draft", "message_send",
    "file_search", "file_analyze",
    "reminders_list", "reminders_create", "reminders_complete",
    "calendar_free_busy", "contacts_resolve",
    "browser_open_url", "browser_history_search", "browser_tabs", "browser_open_downloads",
    "browser_open_youtube_liked", "browser_play_last_youtube", "browser_play_youtube", "browser_close_tab",
    "system_control", "finder_action", "mac_tool",
    "propose_tool",
    "ask_user", "done", "applescript",
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


TOOLS = list(ActionName.__args__)  # type: ignore[attr-defined]


def tool(name: str, description: str, props: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {"type": "function", "function": {"name": name, "description": description, "parameters": {"type": "object", "properties": props, "required": required or []}}}


OPENAI_TOOLS = [
    tool("mail_search", "Fast backend Mail search. Use for email queries before any AppleScript.", {"query": {"type": "string"}, "limit": {"type": "integer"}}, ["query"]),
    tool("file_analyze", "Find and summarize/analyze a local file from allowed roots. Use for 'what is this paper/file about'.", {"query": {"type": "string"}, "question": {"type": "string"}, "path": {"type": "string"}}, ["query"]),
    tool("file_search", "Fast file search across allowed roots and local index.", {"query": {"type": "string"}, "limit": {"type": "integer"}}, ["query"]),
    tool("local_search", "Search local background index across files, mail, notes, messages, and memory snippets.", {"query": {"type": "string"}, "limit": {"type": "integer"}}, ["query"]),
    tool("messages_search", "Fast read-only local Messages search.", {"query": {"type": "string"}, "limit": {"type": "integer"}}, ["query"]),
    tool("calendar_free_busy", "Check Calendar availability/events for a day or time.", {"day": {"type": "string"}, "time_text": {"type": "string"}}),
    tool("reminders_list", "List reminders read-only.", {"limit": {"type": "integer"}}),
    tool("reminders_create", "Create a reminder when reminder write permission is enabled. Use due_text for natural due dates such as 'tomorrow at 9am' or 'Friday 3pm'.", {"text": {"type": "string"}, "due_text": {"type": "string"}}, ["text"]),
    tool("contacts_resolve", "Resolve contact names without dumping all contacts.", {"name": {"type": "string"}, "limit": {"type": "integer"}}, ["name"]),
    tool("browser_history_search", "Search Chrome browser history read-only.", {"query": {"type": "string"}, "limit": {"type": "integer"}}, ["query"]),
    tool("browser_play_last_youtube", "Open the most recently watched YouTube video from browser history.", {}),
    tool("browser_open_url", "Open URL in browser. Requires approval/write permission.", {"url": {"type": "string"}, "browser": {"type": "string"}}, ["url"]),
    tool("system_control", "Read or change system controls. Non-status actions require approval.", {"action": {"type": "string"}, "level": {"type": "integer"}, "enabled": {"type": "boolean"}}, ["action"]),
    tool("mac_tool", "Dispatch one of the 487 cataloged Mac capabilities by id. Use when a catalog capability exists but no dedicated tool name is exposed.", {"id": {"type": "string"}, "args": {"type": "object"}}, ["id"]),
    tool("propose_tool", "Use only when no available tool can satisfy the user's request. Propose the missing connector/tool design; do not pretend it executed.", {"name": {"type": "string"}, "purpose": {"type": "string"}, "inputs": {"type": "object"}, "safety": {"type": "string"}}, ["name", "purpose"]),
    tool("memory_search", "Search Hypersave memory if enabled.", {"query": {"type": "string"}, "limit": {"type": "integer"}}, ["query"]),
    tool("memory_ask", "Ask Hypersave memory if enabled.", {"query": {"type": "string"}}, ["query"]),
    tool("memory_save", "Save memory; requires approval.", {"content": {"type": "string"}, "source": {"type": "string"}, "sensitivity": {"type": "string"}}, ["content", "source"]),
    tool("open_app", "Open/foreground a macOS app.", {"name": {"type": "string"}}, ["name"]),
    tool("web_search", "Use bounded web search for live/current facts.", {"query": {"type": "string"}, "max_results": {"type": "integer"}}, ["query"]),
    tool("ask_user", "Ask for clarification or approval.", {"question": {"type": "string"}}, ["question"]),
    tool("done", "Finish with final answer.", {"summary": {"type": "string"}}, ["summary"]),
]


def normalize_action(raw: dict[str, Any] | None) -> Action | None:
    if not raw or not isinstance(raw, dict):
        return None
    name = raw.get("name")
    args = raw.get("args") or {}
    if name not in TOOLS or not isinstance(args, dict):
        return None
    return Action(name=name, args=args)  # type: ignore[arg-type]
