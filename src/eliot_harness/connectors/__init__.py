"""Connector framework."""

from .base import Connector, ConnectorResult
from .files import FilesConnector
from .memory import MemoryConnector

__all__ = ["Connector", "ConnectorResult", "FilesConnector", "MemoryConnector"]
