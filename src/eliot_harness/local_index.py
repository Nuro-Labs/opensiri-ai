"""Local SQLite full-text index for backend personal context search."""

from __future__ import annotations

import hashlib
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path


DEFAULT_INDEX_PATH = Path.home() / ".local" / "share" / "opensiri-ai" / "index.sqlite3"


@dataclass
class SearchHit:
    source: str
    title: str
    content: str
    uri: str
    sensitivity: str
    score: float


class LocalIndex:
    def __init__(self, path: str | Path = DEFAULT_INDEX_PATH):
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS documents USING fts5(doc_id UNINDEXED, source UNINDEXED, title, content, uri UNINDEXED, sensitivity UNINDEXED, updated_at UNINDEXED)"
        )
        self.conn.commit()

    def upsert(self, source: str, title: str, content: str, uri: str = "", sensitivity: str = "high") -> str:
        doc_id = hashlib.sha256(f"{source}\0{uri}\0{title}".encode("utf-8")).hexdigest()[:32]
        self.conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
        self.conn.execute(
            "INSERT INTO documents(doc_id, source, title, content, uri, sensitivity, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (doc_id, source, title, content[:50000], uri, sensitivity, str(time.time())),
        )
        self.conn.commit()
        return doc_id

    def search(self, query: str, limit: int = 8) -> list[SearchHit]:
        clean = " ".join(x.replace('"', "") for x in query.split() if len(x) > 1)
        if not clean:
            return []
        rows = []
        try:
            rows = self.conn.execute(
                "SELECT source, title, content, uri, sensitivity, bm25(documents) AS score FROM documents WHERE documents MATCH ? ORDER BY score LIMIT ?",
                (clean, limit),
            ).fetchall()
        except sqlite3.OperationalError:
            rows = []
        if not rows:
            terms = " OR ".join(x for x in clean.split()[:8])
            try:
                rows = self.conn.execute(
                    "SELECT source, title, content, uri, sensitivity, bm25(documents) AS score FROM documents WHERE documents MATCH ? ORDER BY score LIMIT ?",
                    (terms, limit),
                ).fetchall() if terms else []
            except sqlite3.OperationalError:
                rows = []
        return [SearchHit(source=s, title=t, content=c, uri=u, sensitivity=se, score=float(sc)) for s, t, c, u, se, sc in rows]

    def count(self) -> int:
        return int(self.conn.execute("SELECT count(*) FROM documents").fetchone()[0])

    def close(self) -> None:
        self.conn.close()
