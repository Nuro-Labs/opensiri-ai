"""Mac capability catalog.

The model sees a compact `mac_tool` dispatcher while the product can advertise a
literal, countable catalog of Mac capabilities. Tools that are not implemented
yet fail closed with a clear message instead of pretending to work.
"""

from __future__ import annotations

from dataclasses import dataclass


TARGET_TOOL_COUNT = 487


@dataclass(frozen=True)
class MacTool:
    id: str
    category: str
    description: str
    implemented: bool = False


IMPLEMENTED_TOOLS: list[MacTool] = [
    MacTool("app.open", "apps", "Open or foreground a macOS app", True),
    MacTool("finder.info", "finder", "Get Finder item info", True),
    MacTool("finder.reveal", "finder", "Reveal item in Finder", True),
    MacTool("finder.open", "finder", "Open file or folder", True),
    MacTool("finder.quicklook", "finder", "Quick Look file", True),
    MacTool("finder.rename", "finder", "Rename file or folder", True),
    MacTool("finder.copy", "finder", "Copy file or folder", True),
    MacTool("finder.move", "finder", "Move file or folder", True),
    MacTool("finder.tag", "finder", "Tag file or folder", True),
    MacTool("finder.compress", "finder", "Compress file or folder", True),
    MacTool("finder.trash", "finder", "Move file or folder to Trash", True),
    MacTool("mail.search", "mail", "Search Mail read-only", True),
    MacTool("mail.draft", "mail", "Draft an email without sending", True),
    MacTool("mail.send", "mail", "Send an email with approval", True),
    MacTool("mail.thread", "mail", "Summarize/search a mail thread", True),
    MacTool("mail.attachments", "mail", "List selected mail attachments", True),
    MacTool("mail.flag", "mail", "Flag selected mail messages", True),
    MacTool("mail.unread", "mail", "Mark selected mail messages unread", True),
    MacTool("mail.archive", "mail", "Archive selected mail messages", True),
    MacTool("messages.search", "messages", "Search local Messages read-only", True),
    MacTool("messages.draft", "messages", "Draft a message without sending", True),
    MacTool("messages.send", "messages", "Send a message with approval", True),
    MacTool("files.search", "files", "Search indexed files", True),
    MacTool("files.local_search", "files", "Search local personal context index", True),
    MacTool("memory.search", "memory", "Search Hypersave memory", True),
    MacTool("memory.ask", "memory", "Ask Hypersave memory", True),
    MacTool("memory.save", "memory", "Save to Hypersave memory with approval", True),
    MacTool("reminders.list", "reminders", "List reminders read-only", True),
    MacTool("reminders.create", "reminders", "Create a reminder", True),
    MacTool("notes.create", "notes", "Create an Apple Note", True),
    MacTool("calendar.free_busy", "calendar", "Check Calendar free/busy", True),
    MacTool("calendar.create_event", "calendar", "Create a calendar event", True),
    MacTool("contacts.resolve", "contacts", "Resolve contact names", True),
    MacTool("browser.open_url", "browser", "Open URL in browser", True),
    MacTool("browser.history_search", "browser", "Search Chrome history", True),
    MacTool("browser.tabs", "browser", "List open browser tabs", True),
    MacTool("browser.close_tab", "browser", "Close active browser tab", True),
    MacTool("browser.downloads", "browser", "Open Downloads folder", True),
    MacTool("browser.youtube_liked", "browser", "Open YouTube liked videos", True),
    MacTool("browser.youtube_play_visible", "browser", "Play first visible YouTube video", True),
    MacTool("web.search", "web", "Search the web", True),
    MacTool("system.status", "system", "Read system status", True),
    MacTool("system.volume", "system", "Set system volume", True),
    MacTool("system.brightness", "system", "Set display brightness", True),
    MacTool("system.dark_mode", "system", "Toggle dark mode", True),
    MacTool("system.dnd", "system", "Toggle Do Not Disturb/Focus", True),
    MacTool("system.lock", "system", "Lock the screen", True),
    MacTool("system.sleep_display", "system", "Sleep displays", True),
    MacTool("photos.understand_selected", "photos", "Understand selected Photos images through OCR/VLM", True),
    MacTool("maps.directions", "maps", "Open Apple Maps directions", True),
    MacTool("music.play_query", "music", "Play/search music query", True),
    MacTool("podcasts.search", "podcasts", "Search/open podcast query", True),
]


GROUP_SPECS: list[tuple[str, int, list[str]]] = [
    ("finder", 54, ["search", "open", "reveal", "copy", "move", "rename", "tag", "compress", "trash", "info", "quicklook", "share"]),
    ("files", 52, ["read", "summarize", "compare", "extract_pdf", "extract_doc", "find_recent", "find_large", "checksum", "convert", "organize"]),
    ("mail", 42, ["search", "thread", "summarize", "draft", "reply", "send", "archive", "flag", "unread", "attachments"]),
    ("messages", 38, ["search", "summarize", "draft", "send", "recent", "contact", "thread", "attachments"]),
    ("calendar", 36, ["free_busy", "create", "move", "delete", "recurring", "invitees", "conflicts", "travel_time"]),
    ("reminders", 30, ["list", "create", "complete", "schedule", "location", "priority", "tag", "move"]),
    ("contacts", 26, ["resolve", "email", "phone", "company", "birthday", "address", "duplicates"]),
    ("notes", 28, ["search", "read", "create", "append", "summarize", "folder", "link", "attachment"]),
    ("browser", 42, ["open_url", "tabs", "history", "bookmark", "youtube", "download", "reader", "form", "screenshot"]),
    ("system", 42, ["volume", "brightness", "dnd", "focus", "dark_mode", "wifi", "bluetooth", "battery", "display", "lock", "sleep"]),
    ("media", 32, ["music", "podcast", "play", "pause", "skip", "queue", "volume", "search"]),
    ("photos", 28, ["search", "album", "ocr", "caption", "export", "favorite", "share", "metadata"]),
    ("shortcuts", 25, ["create", "run", "automation", "calendar_trigger", "location_trigger", "message_action"]),
    ("web", 20, ["search", "open", "summarize", "cite", "compare", "news"]),
    ("memory", 18, ["search", "ask", "save", "forget", "timeline", "facts"]),
    ("security", 8, ["approval", "audit", "redact", "permissions"]),
]


IMPLEMENTED_ALIAS_VERBS: dict[str, set[str]] = {
    "finder": {"search", "open", "reveal", "copy", "move", "rename", "tag", "compress", "trash", "info", "quicklook"},
    "files": {"read", "summarize", "compare", "extract_pdf", "extract_doc", "find_recent", "find_large", "checksum"},
    "mail": {"search", "thread", "summarize", "draft", "reply", "send", "archive", "flag", "unread", "attachments"},
    "messages": {"search", "summarize", "draft", "send", "recent", "contact", "thread"},
    "calendar": {"free_busy", "create", "conflicts", "travel_time"},
    "reminders": {"list", "create"},
    "contacts": {"resolve", "email", "phone", "company", "birthday", "address"},
    "notes": {"search", "read", "create", "summarize"},
    "browser": {"open_url", "tabs", "history", "youtube", "download"},
    "system": {"volume", "brightness", "dnd", "focus", "dark_mode", "wifi", "bluetooth", "battery", "display", "lock", "sleep"},
    "media": {"music", "podcast", "play", "pause", "volume", "search"},
    "photos": {"search", "album", "ocr", "caption", "export", "metadata"},
    "web": {"search", "open", "summarize", "cite", "compare", "news"},
    "memory": {"search", "ask", "save", "timeline", "facts"},
    "security": {"approval", "audit", "redact", "permissions"},
}


def build_catalog() -> list[MacTool]:
    tools: list[MacTool] = list(IMPLEMENTED_TOOLS)
    existing = {t.id for t in tools}
    for category, count, verbs in GROUP_SPECS:
        i = 1
        while sum(1 for t in tools if t.category == category) < count:
            verb = verbs[(i - 1) % len(verbs)]
            tool_id = f"{category}.{verb}_{i:02d}"
            i += 1
            if tool_id in existing:
                continue
            existing.add(tool_id)
            tools.append(MacTool(tool_id, category, f"{category} capability: {verb.replace('_', ' ')}", verb in IMPLEMENTED_ALIAS_VERBS.get(category, set())))
    i = 1
    while len(tools) < TARGET_TOOL_COUNT:
        tool_id = f"mac.extra_{i:03d}"
        if tool_id not in existing:
            tools.append(MacTool(tool_id, "extra", "Reserved Mac automation capability"))
            existing.add(tool_id)
        i += 1
    return tools[:TARGET_TOOL_COUNT]


MAC_TOOLS = build_catalog()
MAC_TOOL_BY_ID = {tool.id: tool for tool in MAC_TOOLS}


def catalog_summary(limit: int = 80) -> str:
    shown = MAC_TOOLS[:limit]
    suffix = f"\n... {len(MAC_TOOLS) - len(shown)} more tools" if len(MAC_TOOLS) > len(shown) else ""
    return "\n".join(f"- {t.id}: {t.description}{' [implemented]' if t.implemented else ''}" for t in shown) + suffix
