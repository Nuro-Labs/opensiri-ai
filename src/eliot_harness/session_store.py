"""Persistent session/reference storage."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .references import ReferenceObject, ReferenceStore
from .session import SessionState


DEFAULT_SESSION_DIR = Path.home() / ".local" / "share" / "opensiri-ai" / "sessions"


def save_session(session: SessionState, root: str | Path = DEFAULT_SESSION_DIR) -> Path:
    d = Path(root).expanduser()
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{session.session_id}.json"
    data = asdict(session)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    return p


def load_session(session_id: str, root: str | Path = DEFAULT_SESSION_DIR) -> SessionState | None:
    p = Path(root).expanduser() / f"{session_id}.json"
    if not p.exists():
        return None
    raw = json.loads(p.read_text())
    session = SessionState(task=raw.get("task", ""), session_id=raw.get("session_id", session_id))
    session.started_at = raw.get("started_at", session.started_at)
    session.current_app = raw.get("current_app")
    session.goal = raw.get("goal")
    session.facts_used = raw.get("facts_used", [])
    session.decisions = raw.get("decisions", [])
    session.turns = raw.get("turns", 0)
    refs = raw.get("references", {}).get("objects", []) if isinstance(raw.get("references"), dict) else []
    session.references = ReferenceStore([ReferenceObject(**r) for r in refs])
    return session


def latest_session(root: str | Path = DEFAULT_SESSION_DIR) -> SessionState | None:
    d = Path(root).expanduser()
    if not d.exists():
        return None
    files = sorted(d.glob("sess_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return load_session(files[0].stem, d) if files else None
