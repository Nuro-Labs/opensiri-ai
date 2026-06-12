"""Local sanity checks for the harness package."""

from __future__ import annotations

from pathlib import Path

from .audit import append_audit
from .context import ContextCompiler
from .guard import classify
from .permissions import PermissionState, Source
from .schema import make_observation


def main() -> None:
    assert classify({"name": "run_shell", "args": {"cmd": "rm /tmp/x"}}).destructive
    assert classify({"name": "web_search", "args": {"query": "x"}}).destructive
    new_file = Path("/tmp/eliot_harness_new_file.txt")
    if new_file.exists():
        new_file.unlink()
    assert not classify({"name": "run_shell", "args": {"cmd": f"echo hi > {new_file}"}}).destructive
    perms = PermissionState(read_sources={Source.HYPERSAVE})
    ctx = ContextCompiler(perms).compile("what is my next meeting").render()
    assert "PERMISSIONS" in ctx
    obs = make_observation("Open Notes", "Desktop", 'AXDesktop "Desktop" id=1', "none", ctx)
    assert "TASK: Open Notes" in obs and "PERSONAL_CONTEXT" in obs
    audit = Path("/tmp/eliot_harness_audit.jsonl")
    append_audit(audit, {"token": "sk-test-secret"})
    assert "sk-test" not in audit.read_text()
    print("eliot-harness checks: PASS")


if __name__ == "__main__":
    main()
