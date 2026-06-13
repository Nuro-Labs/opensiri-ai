"""Opt-in local Messages indexer.

Reads the local Messages SQLite database only when explicitly enabled. This may
require Full Disk Access for the calling app/terminal.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .base import Connector, ConnectorResult


class MessagesIndexConnector(Connector):
    name = "messages_index"
    source = "messages"
    can_read = False
    can_write = False

    def __init__(self, db_path: str | None = None):
        self.db_path = Path(db_path or "~/Library/Messages/chat.db").expanduser()

    def read_context(self, task: str) -> list[ConnectorResult]:
        if not self.can_read or not any(x in task.lower() for x in ("message", "text", "pablo", "mike", "drink", "podcast")):
            return []
        return self.recent_messages(limit=20)

    def recent_messages(self, limit: int = 50) -> list[ConnectorResult]:
        if not self.db_path.exists():
            return [ConnectorResult("Messages database unavailable. Grant Full Disk Access or disable Messages indexing.", {"source": self.source})]
        try:
            conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            rows = conn.execute(
                """
                SELECT datetime(message.date/1000000000 + strftime('%s','2001-01-01'), 'unixepoch') as ts,
                       handle.id,
                       message.text
                FROM message LEFT JOIN handle ON message.handle_id = handle.ROWID
                WHERE message.text IS NOT NULL AND length(message.text) > 0
                ORDER BY message.date DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            conn.close()
        except Exception as e:
            return [ConnectorResult(f"Messages indexing unavailable: {type(e).__name__}", {"source": self.source})]
        out = []
        for ts, sender, text in rows:
            out.append(ConnectorResult(f"Message {ts} from {sender or 'unknown'}: {text[:800]}", {"source": self.source, "timestamp": ts, "sender": sender}))
        return out[: self.max_context_items]
