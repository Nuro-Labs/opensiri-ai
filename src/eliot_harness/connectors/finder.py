"""Finder/file operation connector with path-boundary checks."""

from __future__ import annotations

import shutil
import subprocess
import zipfile
from pathlib import Path

from .applescript import q, run_osa
from .base import Connector, ConnectorResult


class FinderConnector(Connector):
    name = "finder"
    source = "finder"
    can_read = True
    can_write = False

    def __init__(self, roots: list[str] | None = None):
        self.roots = [Path(r).expanduser().resolve() for r in (roots or [Path.home()])]

    def is_allowed(self, path: str | Path) -> bool:
        try:
            p = Path(path).expanduser().resolve()
        except Exception:
            return False
        return any(self._within(p, root) for root in self.roots)

    def info(self, path: str) -> ConnectorResult:
        p = Path(path).expanduser().resolve()
        if not self.is_allowed(p) or not p.exists():
            return ConnectorResult("error: path not allowed or not found", {"path": str(p)})
        stat = p.stat()
        kind = "folder" if p.is_dir() else "file"
        return ConnectorResult(f"{kind}: {p}\nsize: {stat.st_size}\nmodified: {stat.st_mtime}", {"source": self.source, "path": str(p)})

    def reveal(self, path: str, dry_run: bool = True) -> ConnectorResult:
        p = Path(path).expanduser().resolve()
        if not self.is_allowed(p) or not p.exists():
            return ConnectorResult("error: path not allowed or not found", {"path": str(p)})
        if dry_run:
            return ConnectorResult(f"DRY RUN reveal in Finder: {p}", {"source": self.source, "path": str(p)})
        subprocess.run(["open", "-R", str(p)], capture_output=True, text=True, timeout=10)
        return ConnectorResult(f"revealed in Finder: {p}", {"source": self.source, "path": str(p)})

    def open_path(self, path: str, dry_run: bool = True) -> ConnectorResult:
        p = Path(path).expanduser().resolve()
        if not self.is_allowed(p) or not p.exists():
            return ConnectorResult("error: path not allowed or not found", {"path": str(p)})
        if dry_run:
            return ConnectorResult(f"DRY RUN open: {p}", {"source": self.source, "path": str(p)})
        subprocess.run(["open", str(p)], capture_output=True, text=True, timeout=10)
        return ConnectorResult(f"opened: {p}", {"source": self.source, "path": str(p)})

    def quicklook(self, path: str, dry_run: bool = True) -> ConnectorResult:
        p = Path(path).expanduser().resolve()
        if not self.is_allowed(p) or not p.exists():
            return ConnectorResult("error: path not allowed or not found", {"path": str(p)})
        if dry_run:
            return ConnectorResult(f"DRY RUN quicklook: {p}", {"source": self.source, "path": str(p)})
        subprocess.Popen(["qlmanage", "-p", str(p)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return ConnectorResult(f"quicklook opened: {p}", {"source": self.source, "path": str(p)})

    def rename(self, path: str, new_name: str, dry_run: bool = True) -> ConnectorResult:
        p = Path(path).expanduser().resolve()
        if not self._can_mutate(p) or "/" in new_name or not new_name.strip():
            return ConnectorResult("error: rename not allowed", {"path": str(p)})
        target = p.with_name(new_name.strip())
        if dry_run or not self.can_write:
            return ConnectorResult(f"DRY RUN rename {p} -> {target}", {"source": self.source})
        p.rename(target)
        return ConnectorResult(f"renamed to {target}", {"source": self.source, "path": str(target)})

    def copy(self, path: str, dest: str, dry_run: bool = True) -> ConnectorResult:
        p = Path(path).expanduser().resolve(); d = Path(dest).expanduser().resolve()
        if not self._can_mutate(p) or not self.is_allowed(d):
            return ConnectorResult("error: copy not allowed", {"path": str(p), "dest": str(d)})
        target = d / p.name if d.is_dir() else d
        if dry_run or not self.can_write:
            return ConnectorResult(f"DRY RUN copy {p} -> {target}", {"source": self.source})
        if p.is_dir():
            shutil.copytree(p, target, dirs_exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, target)
        return ConnectorResult(f"copied to {target}", {"source": self.source, "path": str(target)})

    def move(self, path: str, dest: str, dry_run: bool = True) -> ConnectorResult:
        p = Path(path).expanduser().resolve(); d = Path(dest).expanduser().resolve()
        if not self._can_mutate(p) or not self.is_allowed(d):
            return ConnectorResult("error: move not allowed", {"path": str(p), "dest": str(d)})
        target = d / p.name if d.is_dir() else d
        if dry_run or not self.can_write:
            return ConnectorResult(f"DRY RUN move {p} -> {target}", {"source": self.source})
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(p), str(target))
        return ConnectorResult(f"moved to {target}", {"source": self.source, "path": str(target)})

    def compress(self, path: str, dest: str | None = None, dry_run: bool = True) -> ConnectorResult:
        p = Path(path).expanduser().resolve()
        target = Path(dest).expanduser().resolve() if dest else p.with_suffix(p.suffix + ".zip")
        if not self._can_mutate(p) or not self.is_allowed(target):
            return ConnectorResult("error: compress not allowed", {"path": str(p), "dest": str(target)})
        if dry_run or not self.can_write:
            return ConnectorResult(f"DRY RUN compress {p} -> {target}", {"source": self.source})
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
            if p.is_dir():
                for child in p.rglob("*"):
                    if child.is_file():
                        z.write(child, child.relative_to(p.parent))
            else:
                z.write(p, p.name)
        return ConnectorResult(f"compressed to {target}", {"source": self.source, "path": str(target)})

    def tag(self, path: str, tag: str, dry_run: bool = True) -> ConnectorResult:
        p = Path(path).expanduser().resolve()
        if not self._can_mutate(p) or not tag.strip():
            return ConnectorResult("error: tag not allowed", {"path": str(p)})
        if dry_run or not self.can_write:
            return ConnectorResult(f"DRY RUN tag {p} with {tag}", {"source": self.source})
        script = 'tell application "Finder" to set label index of (POSIX file ' + q(str(p)) + ' as alias) to 2'
        return ConnectorResult(run_osa(script), {"source": self.source, "path": str(p), "tag": tag})

    def trash(self, path: str, dry_run: bool = True) -> ConnectorResult:
        p = Path(path).expanduser().resolve()
        if not self._can_mutate(p):
            return ConnectorResult("error: trash not allowed", {"path": str(p)})
        if dry_run or not self.can_write:
            return ConnectorResult(f"DRY RUN move to Trash: {p}", {"source": self.source})
        script = 'tell application "Finder" to delete (POSIX file ' + q(str(p)) + ' as alias)'
        return ConnectorResult(run_osa(script), {"source": self.source, "path": str(p)})

    def _can_mutate(self, path: Path) -> bool:
        return self.is_allowed(path) and path.exists()

    def _within(self, path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False
