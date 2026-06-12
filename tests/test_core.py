from pathlib import Path

from eliot_harness.audit import append_audit
from eliot_harness.guard import classify


def test_guard_blocks_delete():
    assert classify({"name": "run_shell", "args": {"cmd": "rm /tmp/x"}}).destructive


def test_guard_allows_new_file_creation():
    p = Path("/tmp/eliot_harness_test_new.txt")
    if p.exists():
        p.unlink()
    assert not classify({"name": "run_shell", "args": {"cmd": f"echo hi > {p}"}}).destructive


def test_audit_redacts_secret():
    p = Path("/tmp/eliot_harness_test_audit.jsonl")
    append_audit(p, {"token": "sk-test-secret"})
    assert "sk-test" not in p.read_text()
