"""Opt-in app/source indexer for personal context.

The indexer syncs bounded summaries into Hypersave. It does not run by default,
and hyper-sensitive sources such as Mail, Messages, and Photos require explicit
source selection plus local OS permissions.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from dataclasses import dataclass, asdict
from pathlib import Path

from .connectors.files import FilesConnector
from .connectors.mail import MailConnector
from .connectors.messages_index import MessagesIndexConnector
from .connectors.photos import PhotosConnector
from .hypersave import HypersaveClient
from .local_index import LocalIndex, DEFAULT_INDEX_PATH


@dataclass
class IndexedItem:
    source: str
    title: str
    content: str
    uri: str = ""
    sensitivity: str = "low"


def run_osa(script: str, timeout: float = 30.0) -> str:
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=timeout)
    return r.stdout.strip() if r.returncode == 0 else ""


def sync_item(client: HypersaveClient, item: IndexedItem) -> str:
    payload = f"[{item.source}] {item.title}\nURI: {item.uri}\n{item.content}"
    return str(client.save_and_wait(payload[:20000], source=f"opensiri-index:{item.source}", sensitivity=item.sensitivity))


def add_to_local_index(index: LocalIndex, item: IndexedItem) -> str:
    return index.upsert(item.source, item.title, item.content, item.uri, item.sensitivity)


def index_files(roots: list[str], limit: int = 25) -> list[IndexedItem]:
    out: list[IndexedItem] = []
    fc = FilesConnector(roots)
    for root in fc.roots:
        if not root.exists():
            continue
        paths = [p for p in root.rglob("*") if p.is_file() and p.stat().st_size < 5_000_000]
        for p in sorted(paths, key=lambda x: x.stat().st_mtime, reverse=True)[:limit]:
            text = fc.extract_text(p, max_chars=8000)
            if text.strip():
                out.append(IndexedItem("files", p.name, text, str(p), "high"))
    return out


def index_calendar() -> list[IndexedItem]:
    script = 'tell application "Calendar" to get summary of events of calendar 1 whose start date is greater than (current date) - (time of (current date))'
    out = run_osa(script)
    return [IndexedItem("calendar", "Today calendar events", out, "calendar://today", "medium")] if out else []


def index_reminders() -> list[IndexedItem]:
    out = run_osa('tell application "Reminders" to get name of reminders 1 thru 50')
    return [IndexedItem("reminders", "Reminder names", out, "reminders://all", "medium")] if out else []


def index_notes() -> list[IndexedItem]:
    names = run_osa('tell application "Notes" to get name of notes 1 thru 20')
    return [IndexedItem("notes", "Recent note names", names, "notes://recent", "high")] if names else []


def index_safari() -> list[IndexedItem]:
    tabs = run_osa('tell application "Safari" to get name of tabs of windows')
    return [IndexedItem("safari", "Open Safari tabs", tabs, "safari://tabs", "high")] if tabs else []


def unsupported_source(name: str) -> IndexedItem:
    return IndexedItem(name, f"{name} connector not enabled", f"{name} indexing is not implemented yet. This source is intentionally skipped until explicit permissions and safe extraction are built.", sensitivity="hyper")


def index_mail(limit: int = 20) -> list[IndexedItem]:
    conn = MailConnector(); conn.can_read = True
    return [IndexedItem("mail", "Mail message", r.text, "mail://recent", "hyper") for r in conn.recent_messages(limit=limit)]


def index_messages(limit: int = 50) -> list[IndexedItem]:
    conn = MessagesIndexConnector(); conn.can_read = True
    return [IndexedItem("messages", "Message", r.text, "messages://local", "hyper") for r in conn.recent_messages(limit=limit)]


def index_photos(understand_selection: bool = False) -> list[IndexedItem]:
    conn = PhotosConnector(); conn.can_read = True
    if understand_selection:
        results = conn.understand_selection("Describe this photo for personal memory search.")
        return [IndexedItem("photos", "Photo understanding", r.text, "photos://selected", "hyper") for r in results]
    results = conn.selected_metadata(limit=10) or conn.recent_metadata(limit=10)
    if not results:
        results = conn.read_context("photos albums")
    return [IndexedItem("photos", "Photos metadata", r.text, "photos://metadata", "hyper") for r in results]


def collect_items(sources: str, files_root: list[str], photos_understand_selected: bool = False) -> list[IndexedItem]:
    items: list[IndexedItem] = []
    for source in [s.strip().lower() for s in sources.split(",") if s.strip()]:
        if source == "files":
            roots = files_root or [str(Path.home() / "Documents")]
            items.extend(index_files(roots))
        elif source == "calendar":
            items.extend(index_calendar())
        elif source == "reminders":
            items.extend(index_reminders())
        elif source == "notes":
            items.extend(index_notes())
        elif source == "safari":
            items.extend(index_safari())
        elif source == "mail":
            items.extend(index_mail())
        elif source == "messages":
            items.extend(index_messages())
        elif source == "photos":
            items.extend(index_photos(photos_understand_selected))
    return items


def run_once(args, client: HypersaveClient | None, index: LocalIndex | None) -> dict:
    items = collect_items(args.sources, args.files_root, args.photos_understand_selected)
    results = []
    for item in items:
        rec = asdict(item)
        rec["content"] = rec["content"][:500]
        if index:
            try:
                rec["index_id"] = add_to_local_index(index, item)
            except Exception as e:
                rec["index_error"] = f"{type(e).__name__}: {e}"
        if not args.dry_run and client:
            try:
                rec["save_result"] = sync_item(client, item)[:500]
            except Exception as e:
                rec["error"] = f"{type(e).__name__}: {e}"
        results.append(rec)
    return {"ts": time.time(), "count": len(items), "dry_run": args.dry_run, "items": results}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources", default="files,calendar,reminders,notes,safari,mail,messages,photos")
    ap.add_argument("--files-root", action="append", default=[])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--photos-understand-selected", action="store_true", help="export selected Photos assets and run OCR/optional VLM before indexing")
    ap.add_argument("--local-index", action="store_true", help="write indexed items to the local SQLite FTS index")
    ap.add_argument("--index-path", default=str(DEFAULT_INDEX_PATH))
    ap.add_argument("--live", action="store_true", help="poll and refresh the index continuously")
    ap.add_argument("--interval", type=float, default=300.0)
    ap.add_argument("--out", default="results/indexer_report.json")
    args = ap.parse_args()

    client = HypersaveClient.from_env()
    if not client and not args.dry_run and not args.local_index:
        raise SystemExit("HYPERSAVE_API_KEY is required unless --dry-run or --local-index is set")
    index = LocalIndex(args.index_path) if args.local_index else None

    while True:
        report = run_once(args, client, index)
        p = Path(args.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(json.dumps({"count": report["count"], "out": str(p), "dry_run": args.dry_run, "local_index": bool(index)}, indent=2))
        if not args.live:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
