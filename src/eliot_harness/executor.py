"""Safe executor boundary for Eliot actions."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

from .connectors.files import FilesConnector
from .connectors.browser import BrowserConnector
from .connectors.contacts import ContactsConnector
from .connectors.mail import MailConnector
from .connectors.memory import MemoryConnector
from .connectors.messages_index import MessagesIndexConnector
from .connectors.messages import MessagesConnector
from .connectors.web import WebConnector
from .connectors.notes import NotesConnector
from .connectors.reminders import RemindersConnector
from .connectors.calendar import CalendarConnector
from .connectors.system_control import SystemControlConnector
from . import mac_ax
from .local_index import LocalIndex
from .permissions import PermissionState, Source
from .schema import Action
from .tool_catalog import MAC_TOOL_BY_ID, catalog_summary


@dataclass
class ExecutionResult:
    output: str
    terminal: bool = False


class Executor:
    def __init__(self, memory: MemoryConnector | None = None, web: WebConnector | None = None, shell_timeout: float = 30.0, permissions: PermissionState | None = None, local_index: LocalIndex | None = None, file_roots: list[str] | None = None):
        self.memory = memory
        self.web = web
        self.local_index = local_index
        self.files = FilesConnector(file_roots)
        self.browser = BrowserConnector()
        self.contacts = ContactsConnector()
        self.mail = MailConnector()
        self.messages_index = MessagesIndexConnector()
        self.messages = MessagesConnector()
        self.notes = NotesConnector()
        self.reminders = RemindersConnector()
        self.calendar = CalendarConnector()
        self.system = SystemControlConnector()
        if permissions:
            self.files.can_read = permissions.can_read(Source.FILES)
            self.mail.can_read = permissions.can_read(Source.MAIL)
            self.mail.can_write = permissions.can_write(Source.MAIL)
            self.messages_index.can_read = permissions.can_read(Source.MESSAGES)
            self.messages.can_write = permissions.can_write(Source.MESSAGES)
            self.browser.can_read = permissions.can_read(Source.BROWSER)
            self.browser.can_write = permissions.can_write(Source.BROWSER)
            self.system.can_write = permissions.can_write(Source.SYSTEM)
            self.notes.can_write = permissions.can_write(Source.NOTES)
            self.reminders.can_write = permissions.can_write(Source.REMINDERS)
            self.calendar.can_write = permissions.can_write(Source.CALENDAR)
            self.reminders.can_read = permissions.can_read(Source.REMINDERS)
        self.shell_timeout = shell_timeout

    def execute(self, action: Action, snapshot=None) -> ExecutionResult:
        name, args = action.name, action.args
        if name == "done":
            return ExecutionResult(str(args.get("summary", "done")), terminal=True)
        if name == "ask_user":
            return ExecutionResult(f"user approval requested: {args.get('question', '')}")
        if name == "open_app":
            return ExecutionResult(mac_ax.open_app(str(args.get("name", ""))))
        if name == "run_shell":
            cmd = str(args.get("cmd", ""))
            r = subprocess.run(["/bin/zsh", "-c", cmd], capture_output=True, text=True, timeout=self.shell_timeout)
            out = (r.stdout + r.stderr).strip()
            return ExecutionResult(out[:2000] if out else ("" if r.returncode == 0 else f"error: exit {r.returncode}"))
        if name == "memory_search":
            if not self.memory:
                return ExecutionResult("memory unavailable")
            return ExecutionResult("\n".join(x.text for x in self.memory.read_context(str(args.get("query", "")))))
        if name == "memory_ask":
            return ExecutionResult(self.memory.ask(str(args.get("query", ""))) if self.memory else "memory unavailable")
        if name == "memory_save":
            return ExecutionResult(self.memory.save(str(args.get("content", "")), str(args.get("source", "eliot")), str(args.get("sensitivity", "medium"))) if self.memory else "memory unavailable")
        if name == "local_search":
            return ExecutionResult(self._local_search(str(args.get("query", "")), int(args.get("limit", 8))), terminal=True)
        if name == "mail_search":
            return ExecutionResult(self._mail_search(str(args.get("query", "")), int(args.get("limit", 8))), terminal=True)
        if name == "mail_draft":
            return ExecutionResult(self.mail.draft_email(str(args.get("to", "")), str(args.get("subject", "")), str(args.get("body", "")), dry_run=True).text, terminal=True)
        if name == "mail_send":
            return ExecutionResult(self.mail.draft_email(str(args.get("to", "")), str(args.get("subject", "")), str(args.get("body", "")), dry_run=not self.mail.can_write).text, terminal=True)
        if name == "messages_search":
            return ExecutionResult(self._messages_search(str(args.get("query", "")), int(args.get("limit", 8))), terminal=True)
        if name == "message_draft":
            return ExecutionResult(self.messages.draft_message(str(args.get("recipient", "")), str(args.get("text", ""))).text, terminal=True)
        if name == "message_send":
            return ExecutionResult(self.messages.send_message(str(args.get("recipient", "")), str(args.get("text", ""))).text, terminal=True)
        if name == "file_search":
            return ExecutionResult(self._file_search(str(args.get("query", "")), int(args.get("limit", 8))), terminal=True)
        if name == "reminders_list":
            return ExecutionResult(self._reminders_list(int(args.get("limit", 20))), terminal=True)
        if name == "calendar_free_busy":
            return ExecutionResult(self.calendar.free_busy(args.get("day"), args.get("time_text")).text, terminal=True)
        if name == "contacts_resolve":
            return ExecutionResult("\n".join(r.text for r in self.contacts.resolve_contact(str(args.get("name", "")), int(args.get("limit", 5)))), terminal=True)
        if name == "browser_open_url":
            if not self.browser.can_write:
                return ExecutionResult(self.browser.open_url(str(args.get("url", "")), str(args.get("browser", "Google Chrome")), dry_run=True).text, terminal=True)
            return ExecutionResult(self.browser.open_url(str(args.get("url", "")), str(args.get("browser", "Google Chrome")), dry_run=False).text)
        if name == "browser_history_search":
            return ExecutionResult("\n".join(r.text for r in self.browser.search_history(str(args.get("query", "")), int(args.get("limit", 10)))) or "no browser history results", terminal=True)
        if name == "browser_open_youtube_liked":
            if not self.browser.can_write:
                return ExecutionResult(self.browser.open_youtube_liked(dry_run=True).text, terminal=True)
            return ExecutionResult(self.browser.open_youtube_liked(dry_run=False).text)
        if name == "browser_play_youtube":
            if not self.browser.can_write:
                return ExecutionResult(self.browser.play_first_visible_youtube_video(dry_run=True).text, terminal=True)
            return ExecutionResult(self.browser.play_first_visible_youtube_video(dry_run=False).text)
        if name == "system_control":
            return ExecutionResult(self.system.execute(str(args.get("action", "status")), args).text, terminal=True)
        if name == "mac_tool":
            return self._mac_tool(str(args.get("id", "")), args.get("args") if isinstance(args.get("args"), dict) else {})
        if name == "web_search":
            return ExecutionResult(self.web.execute("web_search", args).text if self.web else "web access unavailable")
        if name == "invoke_intent":
            app = str(args.get("app", ""))
            intent = str(args.get("intent", ""))
            params = args.get("params") or {}
            if app == "Reminders" and intent == "AddReminder":
                return ExecutionResult(self.reminders.add_reminder(str(params.get("text", "")), dry_run=not self.reminders.can_write).text)
            if app == "Notes" and intent == "CreateNote":
                return ExecutionResult(self.notes.create_note(str(params.get("title", "Untitled")), str(params.get("body", "")), dry_run=not self.notes.can_write).text)
            if app == "Calendar" and intent == "CreateEvent":
                return ExecutionResult(self.calendar.create_event(str(params.get("title", "Eliot Event")), dry_run=not self.calendar.can_write).text)
            return ExecutionResult(self._invoke_intent(app, intent, params))
        if name == "read":
            return ExecutionResult("read is available in the full Mac executor; generic executor has no UI element map")
        if name in ("click", "type"):
            return ExecutionResult(f"{name} requires a live Accessibility element map")
        return ExecutionResult(f"not implemented by generic executor: {name}")

    def _local_search(self, query: str, limit: int) -> str:
        if not self.local_index:
            return "local index unavailable"
        hits = self.local_index.search(query, limit=limit)
        return "\n\n".join(f"[{h.source}] {h.title}\nURI: {h.uri}\n{h.content[:900]}" for h in hits) or "no local index results"

    def _mail_search(self, query: str, limit: int) -> str:
        if not self.mail.can_read:
            return "mail access not enabled"
        results = self.mail.search_messages(query, limit=limit)
        return "\n\n".join(r.text for r in results) or "no matching mail found"

    def _messages_search(self, query: str, limit: int) -> str:
        if not self.messages_index.can_read:
            return "messages access not enabled"
        rows = self.messages_index.recent_messages(limit=max(limit, 30))
        terms = [x.lower() for x in query.split() if len(x) > 2]
        matches = [r for r in rows if any(t in r.text.lower() for t in terms)] if terms else rows
        return "\n\n".join(r.text for r in matches[:limit]) or "no matching messages found"

    def _file_search(self, query: str, limit: int) -> str:
        if self.local_index:
            hits = [h for h in self.local_index.search(query, limit=limit) if h.source == "files"]
            if hits:
                return "\n\n".join(f"{h.title}\nURI: {h.uri}\n{h.content[:900]}" for h in hits)
        return "no matching files found in local index"

    def _reminders_list(self, limit: int) -> str:
        if not self.reminders.can_read:
            return "reminders access not enabled"
        return "\n".join(r.text for r in self.reminders.read_context("reminders")[:limit]) or "no reminders found"

    def _mac_tool(self, tool_id: str, args: dict) -> ExecutionResult:
        if tool_id == "catalog.list":
            return ExecutionResult(catalog_summary(), terminal=True)
        tool = MAC_TOOL_BY_ID.get(tool_id)
        if not tool:
            return ExecutionResult(f"unknown Mac tool: {tool_id}", terminal=True)
        mapping = {
            "app.open": lambda: self.execute(Action("open_app", {"name": args.get("name", "")})),
            "mail.search": lambda: self.execute(Action("mail_search", {"query": args.get("query", ""), "limit": args.get("limit", 8)})),
            "mail.draft": lambda: self.execute(Action("mail_draft", {"to": args.get("to", ""), "subject": args.get("subject", ""), "body": args.get("body", "")})),
            "mail.send": lambda: self.execute(Action("mail_send", {"to": args.get("to", ""), "subject": args.get("subject", ""), "body": args.get("body", "")})),
            "messages.search": lambda: self.execute(Action("messages_search", {"query": args.get("query", ""), "limit": args.get("limit", 8)})),
            "messages.draft": lambda: self.execute(Action("message_draft", {"recipient": args.get("recipient", ""), "text": args.get("text", "")})),
            "messages.send": lambda: self.execute(Action("message_send", {"recipient": args.get("recipient", ""), "text": args.get("text", "")})),
            "files.search": lambda: self.execute(Action("file_search", {"query": args.get("query", ""), "limit": args.get("limit", 8)})),
            "files.local_search": lambda: self.execute(Action("local_search", {"query": args.get("query", ""), "limit": args.get("limit", 8)})),
            "memory.search": lambda: self.execute(Action("memory_search", {"query": args.get("query", "")})),
            "memory.ask": lambda: self.execute(Action("memory_ask", {"query": args.get("query", "")})),
            "memory.save": lambda: self.execute(Action("memory_save", {"content": args.get("content", ""), "source": args.get("source", "mac_tool")})),
            "reminders.list": lambda: self.execute(Action("reminders_list", {"limit": args.get("limit", 20)})),
            "reminders.create": lambda: self.execute(Action("invoke_intent", {"app": "Reminders", "intent": "AddReminder", "params": {"text": args.get("text", args.get("title", ""))}})),
            "notes.create": lambda: self.execute(Action("invoke_intent", {"app": "Notes", "intent": "CreateNote", "params": {"title": args.get("title", "Untitled"), "body": args.get("body", "")}})),
            "calendar.free_busy": lambda: self.execute(Action("calendar_free_busy", {"day": args.get("day"), "time_text": args.get("time_text")})),
            "calendar.create_event": lambda: self.execute(Action("invoke_intent", {"app": "Calendar", "intent": "CreateEvent", "params": {"title": args.get("title", "Event")}})),
            "contacts.resolve": lambda: self.execute(Action("contacts_resolve", {"name": args.get("name", ""), "limit": args.get("limit", 5)})),
            "browser.open_url": lambda: self.execute(Action("browser_open_url", {"url": args.get("url", ""), "browser": args.get("browser", "Google Chrome")})),
            "browser.history_search": lambda: self.execute(Action("browser_history_search", {"query": args.get("query", ""), "limit": args.get("limit", 10)})),
            "browser.youtube_liked": lambda: self.execute(Action("browser_open_youtube_liked", {})),
            "browser.youtube_play_visible": lambda: self.execute(Action("browser_play_youtube", {})),
            "web.search": lambda: self.execute(Action("web_search", {"query": args.get("query", ""), "max_results": args.get("max_results", 3)})),
            "system.status": lambda: self.execute(Action("system_control", {"action": "status"})),
            "system.volume": lambda: self.execute(Action("system_control", {"action": "set_volume", "level": args.get("level", 50)})),
            "system.brightness": lambda: self.execute(Action("system_control", {"action": "set_brightness", "level": args.get("level", 50)})),
            "system.dark_mode": lambda: self.execute(Action("system_control", {"action": "dark_mode", "enabled": args.get("enabled")})),
            "system.dnd": lambda: self.execute(Action("system_control", {"action": "dnd", "enabled": args.get("enabled", True)})),
            "system.lock": lambda: self.execute(Action("system_control", {"action": "lock_screen"})),
            "system.sleep_display": lambda: self.execute(Action("system_control", {"action": "sleep_display"})),
        }
        if tool_id in mapping:
            return mapping[tool_id]()
        return ExecutionResult(f"Mac tool catalog entry exists but is not implemented yet: {tool_id} ({tool.description})", terminal=True)

    def _invoke_intent(self, app: str, intent: str, params: dict) -> str:
        osa = None
        if app == "Reminders" and intent == "AddReminder":
            osa = 'tell application "Reminders" to make new reminder with properties {name:' + _q(params.get("text", "")) + '}'
        elif app == "Notes" and intent == "CreateNote":
            osa = ('tell application "Notes" to make new note at folder "Notes" with properties '
                   '{name:' + _q(params.get("title", "")) + ', body:' + _q(params.get("body", "")) + '}')
        elif app == "Calendar" and intent == "CreateEvent":
            title = _q(params.get("title", "Eliot Event"))
            # Minimal safe fallback: create an all-day event today if no parser is available.
            osa = 'tell application "Calendar" to tell calendar 1 to make new event with properties {summary:' + title + ', start date:(current date), end date:(current date) + 3600}'
        if osa is None:
            return f"error: unsupported intent {app}/{intent}"
        r = subprocess.run(["osascript", "-e", osa], capture_output=True, text=True, timeout=30)
        return "ok" + ((": " + r.stdout.strip()[:300]) if r.stdout.strip() else "") if r.returncode == 0 else "error: " + r.stderr.strip()[:300]


def _q(value) -> str:
    return '"' + str(value).replace('"', '\\"') + '"'
