"""Messages connector. Sending is approval-only."""

from __future__ import annotations

from .applescript import q, run_osa
from .base import Connector, ConnectorResult


class MessagesConnector(Connector):
    name = "messages"
    source = "messages"
    can_read = False
    can_write = False

    def draft_message(self, recipient: str, text: str) -> ConnectorResult:
        return ConnectorResult(f"Draft message to {recipient}: {text}", {"requires_approval": False})

    def send_message(self, recipient: str, text: str) -> ConnectorResult:
        if not self.can_write:
            return ConnectorResult(f"SEND REQUIRES APPROVAL: {recipient}: {text}", {"requires_approval": True, "tier": "external"})
        script = 'tell application "Messages" to send ' + q(text) + ' to buddy ' + q(recipient)
        return ConnectorResult(run_osa(script), {"source": self.source})
