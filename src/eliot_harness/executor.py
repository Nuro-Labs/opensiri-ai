"""Safe executor boundary for Eliot actions."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

from .connectors.files import FilesConnector
from .connectors.mail import MailConnector
from .connectors.memory import MemoryConnector
from .connectors.messages_index import MessagesIndexConnector
from .connectors.web import WebConnector
from .connectors.notes import NotesConnector
from .connectors.reminders import RemindersConnector
from .connectors.calendar import CalendarConnector
from . import mac_ax
from .local_index import LocalIndex
from .permissions import PermissionState, Source
from .schema import Action


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
        self.mail = MailConnector()
        self.messages_index = MessagesIndexConnector()
        self.notes = NotesConnector()
        self.reminders = RemindersConnector()
        self.calendar = CalendarConnector()
        if permissions:
            self.files.can_read = permissions.can_read(Source.FILES)
            self.mail.can_read = permissions.can_read(Source.MAIL)
            self.messages_index.can_read = permissions.can_read(Source.MESSAGES)
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
        if name == "messages_search":
            return ExecutionResult(self._messages_search(str(args.get("query", "")), int(args.get("limit", 8))), terminal=True)
        if name == "file_search":
            return ExecutionResult(self._file_search(str(args.get("query", "")), int(args.get("limit", 8))), terminal=True)
        if name == "reminders_list":
            return ExecutionResult(self._reminders_list(int(args.get("limit", 20))), terminal=True)
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
