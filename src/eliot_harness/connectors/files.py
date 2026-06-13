"""Read-only file context connector."""

from __future__ import annotations

import os
import hashlib
import subprocess
from pathlib import Path

from .base import Connector, ConnectorResult


class FilesConnector(Connector):
    name = "files"

    def __init__(self, roots: list[str] | None = None):
        self.roots = [Path(r).expanduser().resolve() for r in (roots or [os.getcwd()])]

    def read_context(self, task: str) -> list[ConnectorResult]:
        results = [ConnectorResult(text=f"Files root available: {root}", metadata={"root": str(root)}) for root in self.roots]
        selected = self.selected_files()
        if selected:
            results.append(ConnectorResult(text="Selected files: " + ", ".join(str(p) for p in selected[:10]), metadata={"source": "finder_selection"}))
            for path in selected[:3]:
                text = self.extract_text(path)
                if text:
                    results.append(ConnectorResult(text=f"{path.name}: {text[:1200]}", metadata={"path": str(path), "source": "selected_file"}))
        return results[: self.max_context_items]

    def is_allowed(self, path: str) -> bool:
        p = Path(path).expanduser().resolve()
        for root in self.roots:
            try:
                p.relative_to(root)
                return True
            except ValueError:
                continue
        return False

    def selected_files(self) -> list[Path]:
        script = '''tell application "Finder"
set selectedItems to selection as alias list
set outputPaths to {}
repeat with itemAlias in selectedItems
  set end of outputPaths to POSIX path of itemAlias
end repeat
return outputPaths
end tell'''
        try:
            r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=10)
        except Exception:
            return []
        if r.returncode != 0 or not r.stdout.strip():
            return []
        paths = [Path(x.strip()).expanduser().resolve() for x in r.stdout.replace(", ", "\n").splitlines() if x.strip()]
        return [p for p in paths if self.is_allowed(str(p))]

    def list_dir(self, path: str, limit: int = 50) -> ConnectorResult:
        p = Path(path).expanduser().resolve()
        if not self.is_allowed(str(p)) or not p.is_dir():
            return ConnectorResult("error: folder not allowed or not found", {"path": str(p)})
        names = [x.name + ("/" if x.is_dir() else "") for x in sorted(p.iterdir())[:limit]]
        return ConnectorResult("\n".join(names), {"path": str(p), "count": len(names)})

    def read_file(self, path: str, max_chars: int = 12000) -> ConnectorResult:
        p = Path(path).expanduser().resolve()
        if not self.is_allowed(str(p)) or not p.is_file():
            return ConnectorResult("error: file not allowed or not found", {"path": str(p)})
        text = self.extract_text(p, max_chars=max_chars)
        return ConnectorResult(text or "error: no extractable text", {"path": str(p)})

    def compare_files(self, paths: list[str], max_chars_each: int = 5000) -> ConnectorResult:
        chunks = []
        for raw in paths[:6]:
            p = Path(raw).expanduser().resolve()
            if self.is_allowed(str(p)) and p.is_file():
                chunks.append(f"### {p.name}\n{self.extract_text(p, max_chars=max_chars_each)}")
        return ConnectorResult("\n\n".join(chunks) if chunks else "error: no readable files", {"count": len(chunks)})

    def find_recent(self, limit: int = 20) -> ConnectorResult:
        files = []
        for root in self.roots:
            if root.exists():
                files.extend([p for p in root.rglob("*") if p.is_file()][:1000])
        files = sorted(files, key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)[:limit]
        return ConnectorResult("\n".join(str(p) for p in files) or "no recent files", {"source": self.source})

    def find_large(self, limit: int = 20) -> ConnectorResult:
        files = []
        for root in self.roots:
            if root.exists():
                files.extend([p for p in root.rglob("*") if p.is_file()][:1000])
        files = sorted(files, key=lambda p: p.stat().st_size if p.exists() else 0, reverse=True)[:limit]
        return ConnectorResult("\n".join(f"{p.stat().st_size}\t{p}" for p in files) or "no large files", {"source": self.source})

    def checksum(self, path: str) -> ConnectorResult:
        p = Path(path).expanduser().resolve()
        if not self.is_allowed(str(p)) or not p.is_file():
            return ConnectorResult("error: file not allowed or not found", {"path": str(p)})
        h = hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return ConnectorResult(f"sha256 {p}: {h.hexdigest()}", {"source": self.source, "path": str(p)})

    def extract_text(self, path: Path, max_chars: int = 12000) -> str:
        if path.is_dir() or not path.exists():
            return ""
        suffix = path.suffix.lower()
        if suffix in {".txt", ".md", ".csv", ".json", ".log", ".py", ".js", ".ts", ".swift", ".html", ".xml"}:
            return path.read_text(errors="ignore")[:max_chars]
        if suffix in {".rtf", ".doc", ".docx", ".html", ".odt"}:
            try:
                r = subprocess.run(["textutil", "-convert", "txt", "-stdout", str(path)], capture_output=True, text=True, timeout=20)
                if r.returncode == 0:
                    return r.stdout[:max_chars]
            except Exception:
                pass
        if suffix == ".pdf":
            for cmd in (["pdftotext", str(path), "-"], ["mdls", "-raw", "-name", "kMDItemTextContent", str(path)]):
                try:
                    r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    if r.returncode == 0 and r.stdout.strip() and r.stdout.strip() != "(null)":
                        return r.stdout[:max_chars]
                except Exception:
                    continue
        return ""
