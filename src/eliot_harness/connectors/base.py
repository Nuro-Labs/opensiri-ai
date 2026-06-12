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

    def read_context(self, task: str) -> list[ConnectorResult]:
        return []

    def execute(self, action_name: str, args: dict[str, Any]) -> ConnectorResult:
        raise NotImplementedError
