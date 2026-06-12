"""Optional macOS Accessibility bridge.

This module imports PyObjC lazily so the package can be tested on non-Mac or
without Accessibility dependencies.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass


@dataclass
class Snapshot:
    app_name: str
    tree_text: str
    idmap: dict[int, object]


def ax_trusted() -> bool:
    try:
        import ApplicationServices as AS
        return bool(AS.AXIsProcessTrusted())
    except Exception:
        return False


def open_app(name: str) -> str:
    r = subprocess.run(["open", "-a", name], capture_output=True, text=True)
    time.sleep(1.0)
    return "ok" if r.returncode == 0 else f"error: {r.stderr.strip()}"


def _running_app(name: str):
    try:
        import AppKit
    except Exception:
        return None
    target = name.lower().strip()
    for app in AppKit.NSWorkspace.sharedWorkspace().runningApplications():
        ln = (app.localizedName() or "").lower()
        if ln == target or target in ln or ln in target:
            return app
    return None


def observe(target_app: str | None = None) -> Snapshot:
    try:
        import ApplicationServices as AS
        import AppKit
    except Exception:
        return Snapshot("Desktop", 'AXDesktop "Desktop" id=1', {})
    app = _running_app(target_app) if target_app else None
    if app is None:
        app = AppKit.NSWorkspace.sharedWorkspace().frontmostApplication()
    name, pid = app.localizedName(), app.processIdentifier()
    app_el = AS.AXUIElementCreateApplication(pid)
    lines: list[str] = []
    idmap: dict[int, object] = {}
    counter = 1

    def attr(el, key):
        err, val = AS.AXUIElementCopyAttributeValue(el, key, None)
        return val if err == 0 else None

    def walk(el, depth=0):
        nonlocal counter
        if depth > 5 or len(lines) > 120:
            return
        role = attr(el, "AXRole")
        if not role:
            return
        title = attr(el, "AXTitle") or attr(el, "AXDescription") or ""
        nid = counter
        counter += 1
        idmap[nid] = el
        label = f'{role} "{title}" id={nid}' if title else f"{role} id={nid}"
        lines.append("  " * depth + label)
        for ch in list(attr(el, "AXChildren") or [])[:40]:
            walk(ch, depth + 1)

    for w in list(attr(app_el, "AXWindows") or [])[:3]:
        walk(w)
    return Snapshot(name or "Desktop", "\n".join(lines) if lines else 'AXDesktop "Desktop" id=1', idmap)
