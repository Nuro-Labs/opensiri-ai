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
    "mail_draft",
    "mail_send",
    "mail_action",
    "messages_search",
    "message_draft",
    "message_send",
    "file_search",
    "reminders_list",
    "calendar_free_busy",
    "contacts_resolve",
    "browser_open_url",
    "browser_history_search",
    "browser_tabs",
    "browser_close_tab",
    "browser_open_downloads",
    "browser_open_youtube_liked",
    "browser_play_youtube",
    "system_control",
    "finder_action",
    "mac_tool",
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
    "mail_draft",
    "mail_send",
    "mail_action",
    "messages_search",
    "message_draft",
    "message_send",
    "file_search",
    "reminders_list",
    "calendar_free_busy",
    "contacts_resolve",
    "browser_open_url",
    "browser_history_search",
    "browser_tabs",
    "browser_close_tab",
    "browser_open_downloads",
    "browser_open_youtube_liked",
    "browser_play_youtube",
    "system_control",
    "finder_action",
    "mac_tool",
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
    {"type": "function", "function": {"name": "mail_draft", "description": "Draft an email without sending it.", "parameters": {"type": "object", "properties": {"to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}}, "required": ["to", "subject", "body"]}}},
    {"type": "function", "function": {"name": "mail_send", "description": "Send an email. Always requires explicit user approval and mail write permission.", "parameters": {"type": "object", "properties": {"to": {"type": "string"}, "subject": {"type": "string"}, "body": {"type": "string"}}, "required": ["to", "subject", "body"]}}},
    {"type": "function", "function": {"name": "mail_action", "description": "Mail utility action: thread_summary, attachments, flag_selected, unread_selected, archive_selected. Mutations require approval.", "parameters": {"type": "object", "properties": {"action": {"type": "string"}, "query": {"type": "string"}}, "required": ["action"]}}},
    {"type": "function", "function": {"name": "messages_search", "description": "Search local Messages read-only index/database for matching recent messages. Requires explicit Messages access.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "message_draft", "description": "Draft an iMessage/SMS without sending it.", "parameters": {"type": "object", "properties": {"recipient": {"type": "string"}, "text": {"type": "string"}}, "required": ["recipient", "text"]}}},
    {"type": "function", "function": {"name": "message_send", "description": "Send an iMessage/SMS. Always requires explicit user approval and Messages write permission.", "parameters": {"type": "object", "properties": {"recipient": {"type": "string"}, "text": {"type": "string"}}, "required": ["recipient", "text"]}}},
    {"type": "function", "function": {"name": "file_search", "description": "Search allowed local file roots by filename/content through the local index. Use before opening Finder.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "reminders_list", "description": "List visible Apple Reminders read-only. Does not create, complete, or delete reminders.", "parameters": {"type": "object", "properties": {"limit": {"type": "integer"}}, "required": []}}},
    {"type": "function", "function": {"name": "calendar_free_busy", "description": "Check Calendar availability/events for a day or time, read-only.", "parameters": {"type": "object", "properties": {"day": {"type": "string"}, "time_text": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "contacts_resolve", "description": "Resolve a contact name to matching contacts, emails, and phone numbers. Avoid broad dumps.", "parameters": {"type": "object", "properties": {"name": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["name"]}}},
    {"type": "function", "function": {"name": "browser_open_url", "description": "Open a URL in a browser. Use for explicit browser/navigation requests.", "parameters": {"type": "object", "properties": {"url": {"type": "string"}, "browser": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "browser_history_search", "description": "Search Chrome browser history read-only.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "browser_tabs", "description": "List open browser tabs read-only.", "parameters": {"type": "object", "properties": {"browser": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "browser_close_tab", "description": "Close the active browser tab. Requires approval/browser write permission.", "parameters": {"type": "object", "properties": {"browser": {"type": "string"}}, "required": []}}},
    {"type": "function", "function": {"name": "browser_open_downloads", "description": "Open the Downloads folder. Requires approval/browser or Finder write permission.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "browser_open_youtube_liked", "description": "Open the signed-in user's YouTube liked videos page in Chrome.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "browser_play_youtube", "description": "Play or open the first visible YouTube video in Chrome.", "parameters": {"type": "object", "properties": {}, "required": []}}},
    {"type": "function", "function": {"name": "system_control", "description": "Read or change local Mac system controls: status, set_volume, set_brightness, dark_mode, dnd, lock_screen, sleep_display.", "parameters": {"type": "object", "properties": {"action": {"type": "string"}, "level": {"type": "integer"}, "enabled": {"type": "boolean"}, "dry_run": {"type": "boolean"}}, "required": ["action"]}}},
    {"type": "function", "function": {"name": "finder_action", "description": "Finder/file action within allowed roots: info, reveal, open, quicklook, rename, copy, move, tag, compress, trash. Mutations require approval and Finder write permission.", "parameters": {"type": "object", "properties": {"action": {"type": "string"}, "path": {"type": "string"}, "dest": {"type": "string"}, "new_name": {"type": "string"}, "tag": {"type": "string"}, "dry_run": {"type": "boolean"}}, "required": ["action", "path"]}}},
    {"type": "function", "function": {"name": "mac_tool", "description": "Dispatch one of the 487 cataloged Mac tools by id. Prefer explicit tools when available; use this for catalog capabilities and aliases.", "parameters": {"type": "object", "properties": {"id": {"type": "string"}, "args": {"type": "object"}}, "required": ["id"]}}},
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
