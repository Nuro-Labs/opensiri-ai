"""Connector base classes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ConnectorResult:
    text: str
    metadata: dict[str, Any] | None = None


class Connector:
    name = "connector"
    source = "unknown"
    can_read = True
    can_write = False
    max_context_items = 5

    def read_context(self, task: str) -> list[ConnectorResult]:
        return []

    def execute(self, action_name: str, args: dict[str, Any]) -> ConnectorResult:
        raise NotImplementedError


class ConnectorRegistry:
    def __init__(self):
        self._connectors: dict[str, Connector] = {}

    def register(self, connector: Connector) -> None:
        self._connectors[connector.name] = connector

    def get(self, name: str) -> Connector | None:
        return self._connectors.get(name)

    def read_context(self, task: str) -> list[ConnectorResult]:
        results: list[ConnectorResult] = []
        for connector in self._connectors.values():
            if connector.can_read:
                results.extend(connector.read_context(task)[: connector.max_context_items])
        return results
