"""Build configured connector registries."""

from __future__ import annotations

from ..config import HarnessConfig
from ..hypersave import HypersaveClient
from .base import ConnectorRegistry
from .calendar import CalendarConnector
from .contacts import ContactsConnector
from .files import FilesConnector
from .mail import MailConnector
from .maps import MapsConnector
from .memory import MemoryConnector
from .messages import MessagesConnector
from .music import MusicConnector
from .notes import NotesConnector
from .podcasts import PodcastsConnector
from .reminders import RemindersConnector
from .safari import SafariConnector
from .visual import VisualConnector
from .web import WebConnector


def build_registry(config: HarnessConfig, memory_client: HypersaveClient | None = None, file_roots: list[str] | None = None) -> ConnectorRegistry:
    reg = ConnectorRegistry()
    connectors = {
        "hypersave": MemoryConnector(memory_client),
        "files": FilesConnector(file_roots),
        "calendar": CalendarConnector(),
        "contacts": ContactsConnector(),
        "notes": NotesConnector(),
        "reminders": RemindersConnector(),
        "mail": MailConnector(),
        "maps": MapsConnector(),
        "messages": MessagesConnector(),
        "music": MusicConnector(),
        "safari": SafariConnector(),
        "podcasts": PodcastsConnector(),
        "photos": VisualConnector(),
        "web": WebConnector(enabled=config.network_enabled),
    }
    for name, connector in connectors.items():
        cfg = config.sources.get(name)
        if cfg:
            connector.can_read = cfg.read
            connector.can_write = cfg.write
        reg.register(connector)
    return reg
