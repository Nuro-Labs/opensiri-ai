"""Connector framework."""

from .base import Connector, ConnectorResult
from .calendar import CalendarConnector
from .contacts import ContactsConnector
from .files import FilesConnector
from .mail import MailConnector
from .maps import MapsConnector
from .memory import MemoryConnector
from .messages import MessagesConnector
from .messages_index import MessagesIndexConnector
from .music import MusicConnector
from .notes import NotesConnector
from .podcasts import PodcastsConnector
from .photos import PhotosConnector
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
    "MessagesIndexConnector",
    "MusicConnector",
    "NotesConnector",
    "PodcastsConnector",
    "PhotosConnector",
    "RemindersConnector",
    "SafariConnector",
    "WebConnector",
]
