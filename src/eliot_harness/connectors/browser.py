"""Self-contained browser connector for macOS browser handoffs.

This module intentionally avoids registration side effects. Mutating methods are
dry-run by default and only use AppleScript/open handoffs when explicitly run.
"""

from __future__ import annotations

import datetime as dt
import os
import shutil
import sqlite3
import tempfile
import urllib.parse
from pathlib import Path

from .applescript import q, run_osa
from .base import Connector, ConnectorResult


CHROME_EPOCH = dt.datetime(1601, 1, 1, tzinfo=dt.UTC)
YOUTUBE_LIKED_URL = "https://www.youtube.com/playlist?list=LL"
YOUTUBE_HOME_URL = "https://www.youtube.com/"


class BrowserConnector(Connector):
    name = "browser"
    source = "browser"
    can_read = True
    can_write = False

    def open_url(self, url: str, browser: str = "Google Chrome", dry_run: bool = True) -> ConnectorResult:
        """Open a URL in the requested browser via AppleScript.

        The default is a dry run because opening a URL changes local UI state and
        can trigger network requests.
        """
        normalized = self._normalize_url(url)
        if dry_run:
            return ConnectorResult(
                f"DRY RUN open URL in {browser}: {normalized}",
                {"url": normalized, "browser": browser, "requires_approval": False},
            )

        script = f"tell application {q(browser)} to open location {q(normalized)}"
        return ConnectorResult(run_osa(script), {"source": self.source, "url": normalized, "browser": browser})

    def list_tabs(self, browser: str = "Google Chrome") -> list[ConnectorResult]:
        """Return open tab titles and URLs using read-only AppleScript."""
        script = f'''
tell application {q(browser)}
  set out to {{}}
  repeat with w in windows
    repeat with t in tabs of w
      set end of out to (title of t) & " | " & (URL of t)
    end repeat
  end repeat
  set AppleScript's text item delimiters to linefeed
  set joined to out as text
  set AppleScript's text item delimiters to ""
  return joined
end tell'''
        out = run_osa(script)
        if not out or out.startswith("error:"):
            return [ConnectorResult(out or "no browser tab output", {"source": self.source, "browser": browser, "error": True})]

        rows = [row.strip() for row in out.splitlines() if row.strip()]
        results: list[ConnectorResult] = []
        for row in rows:
            title, _, url = row.partition(" | ")
            results.append(
                ConnectorResult(
                    row[:1200],
                    {"source": self.source, "browser": browser, "title": title, "url": url or None, "kind": "browser_tab"},
                )
            )
        return results

    def active_tab(self, browser: str = "Google Chrome") -> ConnectorResult:
        script = f'tell application {q(browser)} to return (title of active tab of front window) & " | " & (URL of active tab of front window)'
        out = run_osa(script)
        return ConnectorResult(out, {"source": self.source, "browser": browser, "kind": "active_tab"})

    def close_active_tab(self, browser: str = "Google Chrome", dry_run: bool = True) -> ConnectorResult:
        if dry_run:
            return ConnectorResult(f"DRY RUN close active tab in {browser}", {"source": self.source})
        script = f'tell application {q(browser)} to close active tab of front window'
        return ConnectorResult(run_osa(script), {"source": self.source, "browser": browser})

    def open_downloads(self, dry_run: bool = True) -> ConnectorResult:
        path = Path.home() / "Downloads"
        if dry_run:
            return ConnectorResult(f"DRY RUN open Downloads: {path}", {"source": self.source, "path": str(path)})
        subprocess.run(["open", str(path)], capture_output=True, text=True, timeout=10)
        return ConnectorResult(f"opened Downloads: {path}", {"source": self.source, "path": str(path)})

    def search_history(self, query: str, limit: int = 10) -> list[ConnectorResult]:
        """Search Chrome History SQLite files read-only when accessible.

        Chrome often keeps the History database locked. To avoid mutating the
        live profile, this method copies readable History files to a temporary
        location before querying them.
        """
        cleaned = query.strip()
        if not cleaned:
            return []

        safe_limit = max(1, min(int(limit or 10), 50))
        rows: list[ConnectorResult] = []
        seen: set[str] = set()
        for history_path in self._chrome_history_paths():
            if not os.access(history_path, os.R_OK):
                continue
            profile = history_path.parent.name
            for item in self._search_history_file(history_path, cleaned, safe_limit):
                url = str(item["url"])
                if url in seen:
                    continue
                seen.add(url)
                title = str(item["title"] or "Untitled")
                visited_at = item.get("visited_at")
                text = f"{title} | {url}"
                if visited_at:
                    text += f" | Last visited: {visited_at}"
                rows.append(
                    ConnectorResult(
                        text[:1200],
                        {"source": self.source, "kind": "chrome_history", "profile": profile, **item},
                    )
                )
                if len(rows) >= safe_limit:
                    return rows
        return rows

    def open_youtube_liked(self, dry_run: bool = True) -> ConnectorResult:
        """Open the signed-in user's YouTube liked videos playlist."""
        return self.open_url(YOUTUBE_LIKED_URL, dry_run=dry_run)

    def play_first_visible_youtube_video(self, dry_run: bool = True) -> ConnectorResult:
        """Navigate/play the first visible YouTube video in the active Chrome tab.

        If the active tab is not on YouTube, the non-dry-run path opens YouTube
        instead of attempting page scripting elsewhere.
        """
        if dry_run:
            return ConnectorResult(
                "DRY RUN play first visible YouTube video in active Google Chrome tab",
                {"browser": "Google Chrome", "requires_approval": False},
            )

        current_url = run_osa('tell application "Google Chrome" to get URL of active tab of front window')
        if current_url.startswith("error:"):
            return ConnectorResult(current_url, {"source": self.source, "browser": "Google Chrome", "error": True})
        host = urllib.parse.urlparse(current_url).netloc.lower()
        if "youtube.com" not in host and "youtu.be" not in host:
            return self.open_url(YOUTUBE_HOME_URL, dry_run=False)

        javascript = r'''
(function() {
  const visible = (el) => {
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && r.bottom >= 0 && r.right >= 0 && r.top <= innerHeight && r.left <= innerWidth;
  };
  const video = document.querySelector('video');
  if (video && visible(video)) {
    video.play();
    return 'played visible video element';
  }
  const links = Array.from(document.querySelectorAll('a[href*="/watch?v="]'));
  const link = links.find(visible);
  if (link) {
    location.href = link.href;
    return 'opened ' + link.href;
  }
  return 'no visible YouTube video found';
})()'''.strip()
        script = 'tell application "Google Chrome" to execute active tab of front window javascript ' + q(javascript)
        return ConnectorResult(run_osa(script), {"source": self.source, "browser": "Google Chrome"})

    def _chrome_history_paths(self) -> list[Path]:
        base = Path.home() / "Library" / "Application Support" / "Google" / "Chrome"
        if not base.exists():
            return []

        paths = []
        for profile in [base / "Default", *sorted(base.glob("Profile *"))]:
            history = profile / "History"
            if history.exists() and history.is_file():
                paths.append(history)
        return paths

    def _search_history_file(self, history_path: Path, query: str, limit: int) -> list[dict[str, object]]:
        tmp_name = ""
        try:
            with tempfile.NamedTemporaryFile(prefix="eliot_chrome_history_", suffix=".sqlite", delete=False) as tmp:
                tmp_name = tmp.name
            shutil.copy2(history_path, tmp_name)
            with sqlite3.connect(f"file:{tmp_name}?mode=ro", uri=True) as conn:
                conn.row_factory = sqlite3.Row
                like = f"%{query}%"
                cur = conn.execute(
                    """
                    select title, url, last_visit_time, visit_count
                    from urls
                    where title like ? or url like ?
                    order by last_visit_time desc
                    limit ?
                    """,
                    (like, like, limit),
                )
                return [self._history_row(row) for row in cur.fetchall()]
        except (OSError, sqlite3.Error):
            return []
        finally:
            if tmp_name:
                try:
                    os.unlink(tmp_name)
                except OSError:
                    pass

    def _history_row(self, row: sqlite3.Row) -> dict[str, object]:
        last_visit_time = int(row["last_visit_time"] or 0)
        visited_at = None
        if last_visit_time > 0:
            visited_at = (CHROME_EPOCH + dt.timedelta(microseconds=last_visit_time)).isoformat()
        return {
            "title": row["title"],
            "url": row["url"],
            "last_visit_time": last_visit_time,
            "visited_at": visited_at,
            "visit_count": row["visit_count"],
        }

    def _normalize_url(self, url: str) -> str:
        value = url.strip()
        parsed = urllib.parse.urlparse(value)
        if not parsed.scheme:
            value = "https://" + value
            parsed = urllib.parse.urlparse(value)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError(f"unsupported browser URL scheme: {parsed.scheme}")
        return value
