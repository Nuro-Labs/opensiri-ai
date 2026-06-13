"""Safe executor boundary for Eliot actions."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

from .connectors.files import FilesConnector
from .connectors.finder import FinderConnector
from .connectors.browser import BrowserConnector
from .connectors.contacts import ContactsConnector
from .connectors.mail import MailConnector
from .connectors.memory import MemoryConnector
from .connectors.messages_index import MessagesIndexConnector
from .connectors.messages import MessagesConnector
from .connectors.maps import MapsConnector
from .connectors.music import MusicConnector
from .connectors.podcasts import PodcastsConnector
from .connectors.photos import PhotosConnector
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
        self.finder = FinderConnector(file_roots)
        self.browser = BrowserConnector()
        self.contacts = ContactsConnector()
        self.mail = MailConnector()
        self.messages_index = MessagesIndexConnector()
        self.messages = MessagesConnector()
        self.maps = MapsConnector()
        self.music = MusicConnector()
        self.podcasts = PodcastsConnector()
        self.photos = PhotosConnector()
        self.notes = NotesConnector()
        self.reminders = RemindersConnector()
        self.calendar = CalendarConnector()
        self.system = SystemControlConnector()
        if permissions:
            self.files.can_read = permissions.can_read(Source.FILES)
            self.finder.can_read = permissions.can_read(Source.FINDER)
            self.finder.can_write = permissions.can_write(Source.FINDER)
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
        if name == "mail_action":
            return ExecutionResult(self._mail_action(args), terminal=True)
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
        if name == "browser_tabs":
            return ExecutionResult("\n".join(r.text for r in self.browser.list_tabs(str(args.get("browser", "Google Chrome")))) or "no browser tabs", terminal=True)
        if name == "browser_close_tab":
            return ExecutionResult(self.browser.close_active_tab(str(args.get("browser", "Google Chrome")), dry_run=not self.browser.can_write).text, terminal=True)
        if name == "browser_open_downloads":
            return ExecutionResult(self.browser.open_downloads(dry_run=not self.browser.can_write).text, terminal=True)
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
        if name == "finder_action":
            return ExecutionResult(self._finder_action(args).text, terminal=True)
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
            "mail.thread": lambda: self.execute(Action("mail_action", {"action": "thread_summary", "query": args.get("query", "")})),
            "mail.attachments": lambda: self.execute(Action("mail_action", {"action": "attachments"})),
            "mail.flag": lambda: self.execute(Action("mail_action", {"action": "flag_selected"})),
            "mail.unread": lambda: self.execute(Action("mail_action", {"action": "unread_selected"})),
            "mail.archive": lambda: self.execute(Action("mail_action", {"action": "archive_selected"})),
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
            "browser.tabs": lambda: self.execute(Action("browser_tabs", {"browser": args.get("browser", "Google Chrome")})),
            "browser.close_tab": lambda: self.execute(Action("browser_close_tab", {"browser": args.get("browser", "Google Chrome")})),
            "browser.downloads": lambda: self.execute(Action("browser_open_downloads", {})),
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
            "finder.info": lambda: self.execute(Action("finder_action", {"action": "info", "path": args.get("path", "")})),
            "finder.reveal": lambda: self.execute(Action("finder_action", {"action": "reveal", "path": args.get("path", "")})),
            "finder.open": lambda: self.execute(Action("finder_action", {"action": "open", "path": args.get("path", "")})),
            "finder.quicklook": lambda: self.execute(Action("finder_action", {"action": "quicklook", "path": args.get("path", "")})),
            "finder.rename": lambda: self.execute(Action("finder_action", {"action": "rename", "path": args.get("path", ""), "new_name": args.get("new_name", "")})),
            "finder.copy": lambda: self.execute(Action("finder_action", {"action": "copy", "path": args.get("path", ""), "dest": args.get("dest", "")})),
            "finder.move": lambda: self.execute(Action("finder_action", {"action": "move", "path": args.get("path", ""), "dest": args.get("dest", "")})),
            "finder.tag": lambda: self.execute(Action("finder_action", {"action": "tag", "path": args.get("path", ""), "tag": args.get("tag", "")})),
            "finder.compress": lambda: self.execute(Action("finder_action", {"action": "compress", "path": args.get("path", ""), "dest": args.get("dest")})),
            "finder.trash": lambda: self.execute(Action("finder_action", {"action": "trash", "path": args.get("path", "")})),
        }
        if tool_id in mapping:
            return mapping[tool_id]()
        alias = self._mac_tool_alias(tool_id, args)
        if alias:
            return alias
        return ExecutionResult(f"Mac tool catalog entry exists but is not implemented yet: {tool_id} ({tool.description})", terminal=True)

    def _mac_tool_alias(self, tool_id: str, args: dict) -> ExecutionResult | None:
        category, _, rest = tool_id.partition(".")
        verb = rest.rsplit("_", 1)[0] if "_" in rest else rest
        if category == "finder" and verb in {"search", "open", "reveal", "copy", "move", "rename", "tag", "compress", "trash", "info", "quicklook"}:
            finder_action = "info" if verb == "search" else verb
            return self.execute(Action("finder_action", {"action": finder_action, **args}))
        if category == "files":
            return ExecutionResult(self._files_alias(verb, args), terminal=True)
        if category == "mail":
            action = {"search": "mail_search", "thread": "mail_action", "summarize": "mail_action", "draft": "mail_draft", "reply": "mail_draft", "send": "mail_send"}.get(verb)
            if verb in {"archive", "flag", "unread", "attachments"}:
                return self.execute(Action("mail_action", {"action": {"archive": "archive_selected", "flag": "flag_selected", "unread": "unread_selected", "attachments": "attachments"}[verb], **args}))
            if action == "mail_search":
                return self.execute(Action("mail_search", {"query": args.get("query", ""), "limit": args.get("limit", 8)}))
            if action == "mail_action":
                return self.execute(Action("mail_action", {"action": "thread_summary", "query": args.get("query", "")}))
            if action in {"mail_draft", "mail_send"}:
                return self.execute(Action(action, {"to": args.get("to", ""), "subject": args.get("subject", ""), "body": args.get("body", args.get("text", ""))}))
        if category == "messages" and verb in {"search", "summarize", "recent", "contact", "thread"}:
            return self.execute(Action("messages_search", {"query": args.get("query", args.get("contact", "")), "limit": args.get("limit", 8)}))
        if category == "messages" and verb in {"draft", "send"}:
            return self.execute(Action("message_draft" if verb == "draft" else "message_send", {"recipient": args.get("recipient", ""), "text": args.get("text", "")}))
        if category == "calendar" and verb in {"free_busy", "conflicts", "travel_time"}:
            return self.execute(Action("calendar_free_busy", {"day": args.get("day"), "time_text": args.get("time_text")}))
        if category == "calendar" and verb == "create":
            return self.execute(Action("invoke_intent", {"app": "Calendar", "intent": "CreateEvent", "params": {"title": args.get("title", "Event")}}))
        if category == "reminders" and verb == "list":
            return self.execute(Action("reminders_list", {"limit": args.get("limit", 20)}))
        if category == "reminders" and verb == "create":
            return self.execute(Action("invoke_intent", {"app": "Reminders", "intent": "AddReminder", "params": {"text": args.get("text", args.get("title", ""))}}))
        if category == "contacts" and verb in {"resolve", "email", "phone", "company", "birthday", "address"}:
            return self.execute(Action("contacts_resolve", {"name": args.get("name", args.get("query", "")), "limit": args.get("limit", 5)}))
        if category == "notes" and verb in {"search", "read", "summarize"}:
            return self.execute(Action("local_search", {"query": args.get("query", "notes"), "limit": args.get("limit", 8)}))
        if category == "notes" and verb == "create":
            return self.execute(Action("invoke_intent", {"app": "Notes", "intent": "CreateNote", "params": {"title": args.get("title", "Untitled"), "body": args.get("body", "")}}))
        if category == "browser":
            return self._browser_alias(verb, args)
        if category == "system":
            return self._system_alias(verb, args)
        if category == "media":
            return self._media_alias(verb, args)
        if category == "photos" and verb in {"search", "album", "metadata"}:
            return ExecutionResult("\n".join(r.text for r in self.photos.read_context(args.get("query", "photos"))) or "no photo metadata", terminal=True)
        if category == "photos" and verb in {"ocr", "caption", "export"}:
            return ExecutionResult("\n".join(r.text for r in self.photos.understand_selection(args.get("prompt", "Describe selected photos"))) or "no selected photos understood", terminal=True)
        if category == "web" and verb in {"search", "open", "summarize", "cite", "compare", "news"}:
            return self.execute(Action("web_search", {"query": args.get("query", ""), "max_results": args.get("max_results", 3)}))
        if category == "memory" and verb in {"search", "timeline", "facts"}:
            return self.execute(Action("memory_search", {"query": args.get("query", "")}))
        if category == "memory" and verb == "ask":
            return self.execute(Action("memory_ask", {"query": args.get("query", "")}))
        if category == "memory" and verb == "save":
            return self.execute(Action("memory_save", {"content": args.get("content", ""), "source": args.get("source", "mac_tool")}))
        if category == "security":
            return ExecutionResult("security capability is enforced by approvals, audit logs, redaction, and permission gates", terminal=True)
        return None

    def _files_alias(self, verb: str, args: dict) -> str:
        if verb in {"read", "summarize", "extract_pdf", "extract_doc"}:
            return self.files.read_file(str(args.get("path", ""))).text
        if verb == "compare":
            return self.files.compare_files(args.get("paths", []) if isinstance(args.get("paths"), list) else [str(args.get("path", "")), str(args.get("other", ""))]).text
        if verb == "find_recent":
            return self.files.find_recent(int(args.get("limit", 20))).text
        if verb == "find_large":
            return self.files.find_large(int(args.get("limit", 20))).text
        if verb == "checksum":
            return self.files.checksum(str(args.get("path", ""))).text
        return self._file_search(str(args.get("query", "")), int(args.get("limit", 8)))

    def _browser_alias(self, verb: str, args: dict) -> ExecutionResult:
        if verb == "open_url":
            return self.execute(Action("browser_open_url", {"url": args.get("url", ""), "browser": args.get("browser", "Google Chrome")}))
        if verb == "tabs":
            return self.execute(Action("browser_tabs", {"browser": args.get("browser", "Google Chrome")}))
        if verb == "history":
            return self.execute(Action("browser_history_search", {"query": args.get("query", ""), "limit": args.get("limit", 10)}))
        if verb == "youtube":
            return self.execute(Action("browser_open_youtube_liked", {}))
        if verb == "download":
            return self.execute(Action("browser_open_downloads", {}))
        return ExecutionResult(f"browser {verb} is not implemented yet", terminal=True)

    def _system_alias(self, verb: str, args: dict) -> ExecutionResult:
        action = {"volume": "set_volume", "brightness": "set_brightness", "dnd": "dnd", "focus": "dnd", "dark_mode": "dark_mode", "wifi": "wifi", "bluetooth": "bluetooth", "battery": "battery", "display": "status", "lock": "lock_screen", "sleep": "sleep_display"}.get(verb, "status")
        payload = {"action": action, **args}
        return self.execute(Action("system_control", payload))

    def _media_alias(self, verb: str, args: dict) -> ExecutionResult:
        query = str(args.get("query", args.get("text", "")))
        if verb in {"music", "play", "search"}:
            return ExecutionResult(self.music.play_query(query or "music", dry_run=not self.music.can_write).text, terminal=True)
        if verb in {"pause", "volume"}:
            return ExecutionResult(self.music.play_pause(dry_run=not self.music.can_write).text, terminal=True)
        if verb == "podcast":
            return ExecutionResult(self.podcasts.open_search(query or "podcast", dry_run=not self.podcasts.can_write).text, terminal=True)
        return ExecutionResult(f"media {verb} is not implemented yet", terminal=True)

    def _finder_action(self, args: dict):
        action = str(args.get("action", "info"))
        path = str(args.get("path", ""))
        dry_run = bool(args.get("dry_run", False)) or not self.finder.can_write
        if action == "info":
            return self.finder.info(path)
        if action == "reveal":
            return self.finder.reveal(path, dry_run=dry_run)
        if action == "open":
            return self.finder.open_path(path, dry_run=dry_run)
        if action == "quicklook":
            return self.finder.quicklook(path, dry_run=dry_run)
        if action == "rename":
            return self.finder.rename(path, str(args.get("new_name", "")), dry_run=dry_run)
        if action == "copy":
            return self.finder.copy(path, str(args.get("dest", "")), dry_run=dry_run)
        if action == "move":
            return self.finder.move(path, str(args.get("dest", "")), dry_run=dry_run)
        if action == "tag":
            return self.finder.tag(path, str(args.get("tag", "")), dry_run=dry_run)
        if action == "compress":
            return self.finder.compress(path, args.get("dest"), dry_run=dry_run)
        if action == "trash":
            return self.finder.trash(path, dry_run=dry_run)
        return self.finder.info(path)

    def _mail_action(self, args: dict) -> str:
        action = str(args.get("action", "thread_summary"))
        dry_run = not self.mail.can_write
        if action == "thread_summary":
            return self.mail.thread_summary(str(args.get("query", ""))).text
        if action == "attachments":
            return "\n".join(r.text for r in self.mail.selected_attachments()) or "no selected mail attachments found"
        if action == "flag_selected":
            return self.mail.flag_selected(dry_run=dry_run).text
        if action == "unread_selected":
            return self.mail.mark_selected_unread(dry_run=dry_run).text
        if action == "archive_selected":
            return self.mail.archive_selected(dry_run=dry_run).text
        return "unsupported mail action"

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
