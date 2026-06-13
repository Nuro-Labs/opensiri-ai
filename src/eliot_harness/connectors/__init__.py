"""Connector framework."""

from .base import Connector, ConnectorResult
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
from .web import WebConnector

__all__ = [
    "Connector",
    "ConnectorResult",
    "CalendarConnector",
    "ContactsConnector",
    "FilesConnector",
    "MailConnector",
    "MapsConnector",
    "MemoryConnector",
    "MessagesConnector",
    "MusicConnector",
    "NotesConnector",
    "PodcastsConnector",
    "RemindersConnector",
    "SafariConnector",
    "WebConnector",
]
