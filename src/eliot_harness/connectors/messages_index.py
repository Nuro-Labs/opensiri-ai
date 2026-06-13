"""Opt-in local Messages indexer.

Reads the local Messages SQLite database only when explicitly enabled. This may
require Full Disk Access for the calling app/terminal.
"""

from __future__ import annotations

import sqlite3
import time
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
        if not self.can_read or not any(x in task.lower() for x in ("message", "messages", "text", "texts", "imessage", "sms", "chat")):
            return []
        return self.search_messages(task, limit=20)[: self.max_context_items]

    def recent_messages(self, limit: int = 50) -> list[ConnectorResult]:
        if not self.db_path.exists():
            return [ConnectorResult("Messages database unavailable. Grant Full Disk Access or disable Messages indexing.", {"source": self.source})]
        try:
            conn = self._connect_readonly()
            rows = conn.execute(
                """
                SELECT datetime(message.date/1000000000 + strftime('%s','2001-01-01'), 'unixepoch') as ts,
                       CASE WHEN message.is_from_me = 1 THEN 'me' ELSE COALESCE(handle.uncanonicalized_id, handle.id) END as sender,
                       COALESCE(chat.display_name, chat.chat_identifier) as chat_name,
                       message.text
                FROM message
                LEFT JOIN handle ON message.handle_id = handle.ROWID
                LEFT JOIN chat_message_join ON chat_message_join.message_id = message.ROWID
                LEFT JOIN chat ON chat.ROWID = chat_message_join.chat_id
                WHERE message.text IS NOT NULL AND length(message.text) > 0
                ORDER BY message.date DESC
                LIMIT ?
                """,
                (self._bounded_limit(limit, default=50),),
            ).fetchall()
            conn.close()
        except Exception as e:
            return [ConnectorResult(f"Messages indexing unavailable: {type(e).__name__}", {"source": self.source})]
        out = []
        for ts, sender, chat_name, text in rows:
            out.append(self._result(ts, sender, chat_name, text))
        return out

    def search_messages(self, query: str, limit: int = 20) -> list[ConnectorResult]:
        if not self.db_path.exists():
            return [ConnectorResult("Messages database unavailable. Grant Full Disk Access or disable Messages indexing.", {"source": self.source})]

        terms = self._search_terms(query)
        if not terms:
            return self.recent_messages(limit=limit)

        clauses = []
        params: list[str | int] = []
        for term in terms:
            like = f"%{self._escape_like(term)}%"
            clauses.append(
                """
                (message.text LIKE ? ESCAPE '\\'
                 OR handle.id LIKE ? ESCAPE '\\'
                 OR handle.uncanonicalized_id LIKE ? ESCAPE '\\'
                 OR chat.display_name LIKE ? ESCAPE '\\'
                 OR chat.chat_identifier LIKE ? ESCAPE '\\')
                """
            )
            params.extend([like, like, like, like, like])
        params.append(self._bounded_limit(limit, default=20))

        try:
            conn = self._connect_readonly()
            deadline = time.monotonic() + 1.5
            conn.set_progress_handler(lambda: 1 if time.monotonic() > deadline else 0, 10_000)
            rows = conn.execute(
                f"""
                SELECT datetime(message.date/1000000000 + strftime('%s','2001-01-01'), 'unixepoch') as ts,
                       CASE WHEN message.is_from_me = 1 THEN 'me' ELSE COALESCE(handle.uncanonicalized_id, handle.id) END as sender,
                       COALESCE(chat.display_name, chat.chat_identifier) as chat_name,
                       message.text
                FROM message
                LEFT JOIN handle ON message.handle_id = handle.ROWID
                LEFT JOIN chat_message_join ON chat_message_join.message_id = message.ROWID
                LEFT JOIN chat ON chat.ROWID = chat_message_join.chat_id
                WHERE message.text IS NOT NULL
                  AND length(message.text) > 0
                  AND {' AND '.join(clauses)}
                ORDER BY message.date DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
            conn.close()
        except Exception as e:
            return [ConnectorResult(f"Messages search unavailable: {type(e).__name__}", {"source": self.source})]

        return [self._result(ts, sender, chat_name, text) for ts, sender, chat_name, text in rows]

    def _connect_readonly(self) -> sqlite3.Connection:
        conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True, timeout=1)
        conn.execute("PRAGMA query_only = ON")
        return conn

    def _bounded_limit(self, limit: int, default: int) -> int:
        try:
            n = int(limit)
        except (TypeError, ValueError):
            n = default
        return max(1, min(n, 100))

    def _search_terms(self, query: str) -> list[str]:
        stopwords = {"a", "about", "and", "chat", "find", "for", "from", "imessage", "in", "message", "messages", "my", "of", "on", "search", "show", "sms", "text", "texts", "the", "to", "with"}
        terms: list[str] = []
        for raw in query[:200].lower().replace("_", " ").split():
            term = "".join(ch for ch in raw if ch.isalnum() or ch in "+@.-")
            if len(term) >= 2 and term not in stopwords and term not in terms:
                terms.append(term)
            if len(terms) >= 5:
                break
        return terms

    def _escape_like(self, value: str) -> str:
        return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

    def _result(self, ts: str | None, sender: str | None, chat_name: str | None, text: str) -> ConnectorResult:
        date = ts or "unknown date"
        sender_name = sender or chat_name or "unknown"
        body = text[:800]
        where = f" in {chat_name}" if chat_name and chat_name != sender_name else ""
        return ConnectorResult(
            f"Message {date} from {sender_name}{where}: {body}",
            {"source": self.source, "date": date, "timestamp": date, "sender": sender_name, "chat": chat_name, "text": body},
        )
