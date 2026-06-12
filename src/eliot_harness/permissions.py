"""Permission model for a Siri-class local assistant harness."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class PermissionTier(str, Enum):
    READ_LOCAL = "read_local"
    MUTATE_LOCAL = "mutate_local"
    DESTRUCTIVE = "destructive"
    EXTERNAL = "external"
    CREDENTIAL = "credential"


class Source(str, Enum):
    FILES = "files"
    CALENDAR = "calendar"
    CONTACTS = "contacts"
    NOTES = "notes"
    REMINDERS = "reminders"
    MAIL = "mail"
    MESSAGES = "messages"
    SAFARI = "safari"
    PHOTOS = "photos"
    HYPERSAVE = "hypersave"
    WEB = "web"


@dataclass
class PermissionState:
    read_sources: set[Source] = field(default_factory=set)
    write_sources: set[Source] = field(default_factory=set)
    network_enabled: bool = False
    external_send_enabled: bool = False

    def can_read(self, source: Source) -> bool:
        return source in self.read_sources

    def can_write(self, source: Source) -> bool:
        return source in self.write_sources
