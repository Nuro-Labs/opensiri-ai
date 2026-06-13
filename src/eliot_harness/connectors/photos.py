"""Opt-in Photos connector with metadata, export, OCR, and optional VLM captions."""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

from .applescript import q, run_osa
from .base import Connector, ConnectorResult
from .visual import VisualConnector
from ..vision import ImageUnderstandingClient


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif", ".tif", ".tiff", ".gif"}


@dataclass
class PhotoAnalysis:
    path: Path
    ocr: str = ""
    caption: str = ""

    def render(self) -> str:
        parts = [f"Photo export: {self.path.name}"]
        if self.ocr:
            parts.append("OCR: " + self.ocr[:1200])
        if self.caption:
            parts.append("Vision: " + self.caption[:1200])
        return "\n".join(parts)


class PhotosConnector(Connector):
    name = "photos"
    source = "photos"
    can_read = False
    can_write = False
    max_context_items = 5

    def read_context(self, task: str) -> list[ConnectorResult]:
        lower = task.lower()
        if not self.can_read or not any(x in lower for x in ("photo", "photos", "album", "picture", "image")):
            return []
        if any(x in lower for x in ("selected", "this photo", "this image", "what is in", "what's in", "describe", "read text")):
            understood = self.understand_selection(task)
            if understood:
                return understood
        metadata = self.selected_metadata(limit=5) or self.recent_metadata(limit=5)
        if metadata:
            return metadata
        albums = self.album_names(limit=20)
        if albums:
            return [ConnectorResult("Photos albums: " + ", ".join(albums), {"source": self.source, "kind": "albums"})]
        return [ConnectorResult("Photos unavailable. Grant Photos permission or select images in Photos and try again.", {"source": self.source})]

    def album_names(self, limit: int = 20) -> list[str]:
        out = run_osa('tell application "Photos" to get name of albums', timeout=20)
        if not out or out.startswith("error"):
            return []
        return [x.strip() for x in out.split(",") if x.strip()][:limit]

    def selected_metadata(self, limit: int = 10) -> list[ConnectorResult]:
        script = '''tell application "Photos"
set out to {}
set i to 0
repeat with m in selection
  set i to i + 1
  set itemName to "untitled"
  try
    set itemName to name of m
  end try
  set itemDate to "unknown date"
  try
    set itemDate to (date of m as string)
  end try
  set end of out to "Selected photo: " & itemName & " | Date: " & itemDate
  if i >= ''' + str(limit) + ''' then exit repeat
end repeat
return out
end tell'''
        out = run_osa(script, timeout=20)
        return self._rows(out, "selected_metadata")

    def recent_metadata(self, limit: int = 10) -> list[ConnectorResult]:
        script = '''tell application "Photos"
set out to {}
set i to 0
repeat with m in media items
  set i to i + 1
  set itemName to "untitled"
  try
    set itemName to name of m
  end try
  set itemDate to "unknown date"
  try
    set itemDate to (date of m as string)
  end try
  set end of out to "Photo: " & itemName & " | Date: " & itemDate
  if i >= ''' + str(limit) + ''' then exit repeat
end repeat
return out
end tell'''
        out = run_osa(script, timeout=30)
        return self._rows(out, "recent_metadata")

    def search_metadata(self, query: str, limit: int = 10) -> list[ConnectorResult]:
        script = '''tell application "Photos"
set out to {}
set i to 0
repeat with m in media items
  set itemName to ""
  try
    set itemName to name of m
  end try
  if itemName contains ''' + q(query) + ''' then
    set i to i + 1
    set end of out to "Photo match: " & itemName
  end if
  if i >= ''' + str(limit) + ''' then exit repeat
end repeat
return out
end tell'''
        out = run_osa(script, timeout=30)
        return self._rows(out, "search_metadata")

    def export_selection(self, dest_dir: str | Path | None = None, limit: int = 5) -> list[Path]:
        if not self.can_read:
            return []
        target = Path(dest_dir) if dest_dir else Path(tempfile.mkdtemp(prefix="opensiri-photos-"))
        target.mkdir(parents=True, exist_ok=True)
        script = '''set exportFolder to (POSIX file ''' + q(str(target)) + ''') as alias
  export selection to exportFolder with using originals
end tell'''
        out = run_osa(script, timeout=120)
        if out.startswith("error"):
            return []
        paths = [p for p in target.rglob("*") if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
        return sorted(paths, key=lambda p: p.stat().st_mtime, reverse=True)[:limit]

    def understand_selection(self, prompt: str = "Describe the selected Photos images.", limit: int = 3) -> list[ConnectorResult]:
        paths = self.export_selection(limit=limit)
        if not paths:
            return []
        visual = VisualConnector()
        vlm = ImageUnderstandingClient()
        results: list[ConnectorResult] = []
        for path in paths[:limit]:
            ocr = visual.ocr_image(path)
            caption = vlm.describe(path, prompt) if vlm.configured else ""
            analysis = PhotoAnalysis(path=path, ocr=ocr, caption=caption)
            text = analysis.render()
            if not caption and not ocr:
                text += "\nVision model is not configured. Set OPENSIRI_VLM_URL and OPENSIRI_VLM_MODEL for image understanding."
            results.append(ConnectorResult(text, {"source": self.source, "kind": "image_understanding", "path": str(path), "ocr": bool(ocr), "vision": bool(caption)}))
        return results

    def add_to_album(self, album: str, dry_run: bool = True) -> ConnectorResult:
        if dry_run or not self.can_write:
            return ConnectorResult(f"DRY RUN Photos album update: {album}", {"requires_approval": True})
        return ConnectorResult("Photos write not implemented yet", {"requires_approval": True})

    def _rows(self, out: str, kind: str) -> list[ConnectorResult]:
        if not out or out.startswith("error") or out == "ok":
            return []
        rows = [x.strip() for x in out.replace(", Selected photo:", "\nSelected photo:").replace(", Photo:", "\nPhoto:").replace(", Photo match:", "\nPhoto match:").splitlines() if x.strip()]
        return [ConnectorResult(row[:1000], {"source": self.source, "kind": kind}) for row in rows[: self.max_context_items]]
