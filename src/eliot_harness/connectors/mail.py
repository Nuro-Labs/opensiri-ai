"""Mail connector.

Sending always requires approval; by default this connector only drafts.
"""

from __future__ import annotations

from .applescript import q, run_osa
from .base import Connector, ConnectorResult


class MailConnector(Connector):
    name = "mail"
    source = "mail"
    can_read = False
    can_write = False

    def read_context(self, task: str) -> list[ConnectorResult]:
        if not self.can_read or not any(x in task.lower() for x in ("email", "mail", "inbox")):
            return []
        out = run_osa('tell application "Mail" to get subject of messages 1 thru 5 of inbox')
        return [ConnectorResult(f"Recent Mail subjects: {out}", {"source": self.source})]

    def draft_email(self, to: str, subject: str, body: str, dry_run: bool = True) -> ConnectorResult:
        if dry_run or not self.can_write:
            return ConnectorResult(f"Draft email to {to}\nSubject: {subject}\n\n{body}", {"requires_approval": False})
        script = (
            'tell application "Mail" to make new outgoing message with properties '
            '{visible:true, subject:' + q(subject) + ', content:' + q(body) + '} '
            'with make new to recipient at end of to recipients with properties {address:' + q(to) + '}'
        )
        return ConnectorResult(run_osa(script), {"source": self.source})

    def send_email(self, to: str, subject: str, body: str) -> ConnectorResult:
        return ConnectorResult(f"SEND REQUIRES APPROVAL: {to} / {subject}", {"requires_approval": True, "tier": "external"})
