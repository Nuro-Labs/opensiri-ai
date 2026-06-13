"""Connector framework."""

from .base import Connector, ConnectorResult
from .calendar import CalendarConnector
from .contacts import ContactsConnector
from .files import FilesConnector
from .mail import MailConnector
from .memory import MemoryConnector
from .messages import MessagesConnector
from .notes import NotesConnector
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
    "MemoryConnector",
    "MessagesConnector",
    "NotesConnector",
    "RemindersConnector",
    "SafariConnector",
    "WebConnector",
]
