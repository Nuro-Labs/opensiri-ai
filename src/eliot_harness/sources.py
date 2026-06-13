"""Source manifests for permission center and connector registry."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceManifest:
    name: str
    title: str
    description: str
    sensitivity: str
    read_capabilities: tuple[str, ...]
    write_capabilities: tuple[str, ...]
    default_enabled: bool = False


MANIFESTS = {
    "hypersave": SourceManifest("hypersave", "Hypersave Memory", "Personal facts, documents, graph, and temporal memory.", "high", ("search", "ask", "facts", "profile"), ("save", "remind")),
    "files": SourceManifest("files", "Files", "Scoped local folders and documents.", "high", ("list", "read", "compare"), ("create", "copy", "move")),
    "calendar": SourceManifest("calendar", "Calendar", "Events and availability.", "medium", ("read_events", "free_busy"), ("create_event", "edit_event")),
    "contacts": SourceManifest("contacts", "Contacts", "Name and address resolution.", "high", ("resolve_contact",), ()),
    "notes": SourceManifest("notes", "Notes", "Notes metadata and note creation.", "high", ("list_notes", "read_note"), ("create_note",)),
    "reminders": SourceManifest("reminders", "Reminders", "Reminder lists and reminder creation.", "medium", ("list_reminders",), ("create_reminder", "complete_reminder")),
    "mail": SourceManifest("mail", "Mail", "Email metadata, drafting, and sending with approval.", "hyper", ("search_subjects", "read_selected"), ("draft_email", "send_email")),
    "messages": SourceManifest("messages", "Messages", "Message drafting and sending with approval.", "hyper", (), ("draft_message", "send_message")),
    "safari": SourceManifest("safari", "Safari", "Tabs, bookmarks, and browser context.", "high", ("list_tabs",), ("open_url",)),
    "photos": SourceManifest("photos", "Photos", "Photo search and visual context. Not implemented yet.", "hyper", (), ()),
    "web": SourceManifest("web", "Web", "Current world knowledge through bounded search.", "external", ("search",), ()),
}


def manifest_table() -> str:
    lines = ["| Source | Read | Write | Sensitivity |", "|---|---|---|---|"]
    for m in MANIFESTS.values():
        lines.append(f"| {m.title} | {', '.join(m.read_capabilities) or '-'} | {', '.join(m.write_capabilities) or '-'} | {m.sensitivity} |")
    return "\n".join(lines)


def enabled_sources_text(enabled: list[str]) -> str:
    return ", ".join(MANIFESTS[x].title for x in enabled if x in MANIFESTS)
