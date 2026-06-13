"""macOS system control connector."""

from __future__ import annotations

import subprocess

from .applescript import q, run_osa
from .base import Connector, ConnectorResult


class SystemControlConnector(Connector):
    name = "system_control"
    source = "system"
    can_read = True
    can_write = True

    def get_status(self) -> ConnectorResult:
        volume = run_osa("output volume of (get volume settings)")
        muted = run_osa("output muted of (get volume settings)")
        dark = run_osa('tell application "System Events" to tell appearance preferences to get dark mode')
        battery = self.battery_status().text
        wifi = self.wifi_status().text
        bluetooth = self.bluetooth_status().text
        return ConnectorResult(f"Volume: {volume}; muted: {muted}; dark mode: {dark}; {battery}; {wifi}; {bluetooth}", {"source": self.source})

    def battery_status(self) -> ConnectorResult:
        try:
            r = subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True, timeout=5)
            line = " ".join(x.strip() for x in r.stdout.splitlines() if x.strip())[:300]
            return ConnectorResult("battery: " + (line or "unknown"), {"source": self.source})
        except Exception:
            return ConnectorResult("battery: unavailable", {"source": self.source})

    def wifi_status(self) -> ConnectorResult:
        try:
            r = subprocess.run(["networksetup", "-getairportpower", "en0"], capture_output=True, text=True, timeout=5)
            return ConnectorResult("wifi: " + (r.stdout.strip() or r.stderr.strip() or "unknown"), {"source": self.source})
        except Exception:
            return ConnectorResult("wifi: unavailable", {"source": self.source})

    def bluetooth_status(self) -> ConnectorResult:
        out = run_osa('tell application "System Events" to tell process "ControlCenter" to exists', timeout=5)
        return ConnectorResult("bluetooth: status requires Control Center automation" if not out.startswith("error") else "bluetooth: unavailable", {"source": self.source})

    def set_volume(self, level: int, dry_run: bool = True) -> ConnectorResult:
        n = max(0, min(100, int(level)))
        if dry_run:
            return ConnectorResult(f"DRY RUN set volume to {n}", {"source": self.source})
        return ConnectorResult(run_osa(f"set volume output volume {n}"), {"source": self.source})

    def set_brightness(self, level: int, dry_run: bool = True) -> ConnectorResult:
        n = max(0, min(100, int(level)))
        if dry_run:
            return ConnectorResult(f"DRY RUN set brightness to {n}", {"source": self.source})
        # Apple Silicon Macs usually expose brightness through the `brightness` utility only if installed.
        try:
            r = subprocess.run(["brightness", str(n / 100)], capture_output=True, text=True, timeout=10)
            if r.returncode == 0:
                return ConnectorResult(f"brightness set to {n}", {"source": self.source})
        except Exception:
            pass
        return ConnectorResult("brightness control unavailable; install the `brightness` CLI or use display settings", {"source": self.source})

    def toggle_dark_mode(self, enabled: bool | None = None, dry_run: bool = True) -> ConnectorResult:
        if dry_run:
            return ConnectorResult(f"DRY RUN {'toggle' if enabled is None else 'set'} dark mode {enabled}", {"source": self.source})
        if enabled is None:
            script = 'tell application "System Events" to tell appearance preferences to set dark mode to not dark mode'
        else:
            script = 'tell application "System Events" to tell appearance preferences to set dark mode to ' + ("true" if enabled else "false")
        return ConnectorResult(run_osa(script), {"source": self.source})

    def set_do_not_disturb(self, enabled: bool, dry_run: bool = True) -> ConnectorResult:
        if dry_run:
            return ConnectorResult(f"DRY RUN set Do Not Disturb to {enabled}", {"source": self.source})
        state = "on" if enabled else "off"
        r = subprocess.run(["shortcuts", "run", "Set Focus", "--input", state], capture_output=True, text=True, timeout=15)
        if r.returncode == 0:
            return ConnectorResult(f"Do Not Disturb set {state}", {"source": self.source})
        return ConnectorResult("Do Not Disturb shortcut unavailable; create a Shortcuts action named Set Focus", {"source": self.source})

    def lock_screen(self, dry_run: bool = True) -> ConnectorResult:
        if dry_run:
            return ConnectorResult("DRY RUN lock screen", {"source": self.source})
        return ConnectorResult(run_osa('tell application "System Events" to keystroke "q" using {control down, command down}'), {"source": self.source})

    def sleep_display(self, dry_run: bool = True) -> ConnectorResult:
        if dry_run:
            return ConnectorResult("DRY RUN sleep display", {"source": self.source})
        r = subprocess.run(["pmset", "displaysleepnow"], capture_output=True, text=True, timeout=10)
        return ConnectorResult("display sleep requested" if r.returncode == 0 else "display sleep failed", {"source": self.source})

    def execute(self, action_name: str, args: dict) -> ConnectorResult:
        dry_run = bool(args.get("dry_run", False))
        if action_name == "status":
            return self.get_status()
        if action_name == "battery":
            return self.battery_status()
        if action_name == "wifi":
            return self.wifi_status()
        if action_name == "bluetooth":
            return self.bluetooth_status()
        if action_name == "set_volume":
            return self.set_volume(int(args.get("level", 50)), dry_run=dry_run)
        if action_name == "set_brightness":
            return self.set_brightness(int(args.get("level", 50)), dry_run=dry_run)
        if action_name == "dark_mode":
            enabled = args.get("enabled")
            return self.toggle_dark_mode(enabled if isinstance(enabled, bool) else None, dry_run=dry_run)
        if action_name == "dnd":
            return self.set_do_not_disturb(bool(args.get("enabled", True)), dry_run=dry_run)
        if action_name == "lock_screen":
            return self.lock_screen(dry_run=dry_run)
        if action_name == "sleep_display":
            return self.sleep_display(dry_run=dry_run)
        return ConnectorResult(f"unsupported system control action: {action_name}", {"source": self.source})
