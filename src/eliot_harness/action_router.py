"""Route structured actions to connector implementations."""

from __future__ import annotations

from .connectors.base import ConnectorRegistry, ConnectorResult
from .schema import Action


class ActionRouter:
    def __init__(self, registry: ConnectorRegistry):
        self.registry = registry

    def route(self, action: Action) -> ConnectorResult | None:
        name, args = action.name, action.args
        if name == "web_search":
            web = self.registry.get("web")
            return web.execute("web_search", args) if web else ConnectorResult("web unavailable")
        if name == "memory_search":
            mem = self.registry.get("hypersave")
            return ConnectorResult("\n".join(x.text for x in mem.read_context(str(args.get("query", ""))))) if mem else ConnectorResult("memory unavailable")
        if name == "invoke_intent":
            app = str(args.get("app", ""))
            intent = str(args.get("intent", ""))
            params = args.get("params") or {}
            if app == "Reminders" and intent == "AddReminder":
                conn = self.registry.get("reminders")
                return conn.add_reminder(str(params.get("text", "")), dry_run=not conn.can_write) if conn else None
            if app == "Notes" and intent == "CreateNote":
                conn = self.registry.get("notes")
                return conn.create_note(str(params.get("title", "Untitled")), str(params.get("body", "")), dry_run=not conn.can_write) if conn else None
            if app == "Calendar" and intent == "CreateEvent":
                conn = self.registry.get("calendar")
                return conn.create_event(str(params.get("title", "Eliot Event")), dry_run=not conn.can_write) if conn else None
        return None
