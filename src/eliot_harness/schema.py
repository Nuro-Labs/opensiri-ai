"""Canonical Eliot tool schema and observation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


ActionName = Literal[
    "applescript",
    "run_shell",
    "read_file",
    "write_file",
    "web_search",
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
    "applescript",
    "run_shell",
    "read_file",
    "write_file",
    "web_search",
    "ask_user",
    "done",
]


OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "applescript",
            "description": "Run any custom AppleScript on the Mac to query and automate native macOS apps (such as Mail, Messages, Notes, Reminders, Calendar, Contacts, Finder, Safari, or System Preferences) natively and dynamically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "script": {"type": "string", "description": "The exact AppleScript code block to execute."}
                },
                "required": ["script"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": "Run a local shell command (zsh/bash) through the harness. Use this for file system checks, running python scripts, or inspecting shell output.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cmd": {"type": "string", "description": "The shell command string to run."}
                },
                "required": ["cmd"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a local text file on the system.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The absolute path of the file to read."}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create a new text file or overwrite an existing file with the specified contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "The absolute path of the file to write to."},
                    "content": {"type": "string", "description": "The text content to write into the file."}
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Use bounded harness web search to fetch live or general information from the web.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The web search query."},
                    "max_results": {"type": "integer", "description": "The maximum number of search results to return."}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ask_user",
            "description": "Ask the user for clarification, input, or confirmation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The question or confirmation prompt to show to the user."}
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "done",
            "description": "Finish the task and present the final elegant answer or summary to the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "The final detailed, perfect answer or summary of actions performed to show to the user."}
                },
                "required": ["summary"],
            },
        },
    },
]


def normalize_action(raw: dict[str, Any] | None) -> Action | None:
    if not raw or not isinstance(raw, dict):
        return None
    name = raw.get("name")
    args = raw.get("args") or {}
    if name not in TOOLS or not isinstance(args, dict):
        return None
    return Action(name=name, args=args)  # type: ignore[arg-type]
