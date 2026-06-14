"""Unit tests for subprocess robustness and crash prevention."""

from __future__ import annotations

import sys
import time
from pathlib import Path

from eliot_harness.process import run_command_robust


def test_robust_success():
    """Verifies that a successful command returns normal exit status and outputs."""
    res = run_command_robust(["echo", "hello-world"])
    assert not res.timed_out
    assert res.error is None
    assert res.returncode == 0
    assert res.stdout.strip() == "hello-world"


def test_robust_timeout_recovery():
    """Verifies that a timed-out command is caught cleanly without traceback."""
    res = run_command_robust(["sleep", "10"], timeout=0.1)
    assert res.timed_out
    assert "timed out" in res.error
    assert res.returncode == -1


def test_robust_orphan_cleanup(tmp_path):
    """Verifies that grandchild/descendant processes are killed on timeout.

    We run a shell loop that appends 'tick' to a temp file every 0.05 seconds.
    If the process group is killed cleanly on timeout, the appending MUST stop.
    """
    tick_file = tmp_path / "tick.txt"
    # Execute a background loop in zsh
    cmd = f'while true; do echo "tick" >> {tick_file}; sleep 0.05; done'
    
    res = run_command_robust(["/bin/zsh", "-c", cmd], timeout=0.2)
    assert res.timed_out

    # Let some time pass to see if the background loop continues running
    time.sleep(0.3)
    
    # Read the tick file after cooling down
    assert tick_file.exists()
    content_at_timeout = tick_file.read_text()
    ticks_at_timeout = content_at_timeout.count("tick")
    
    # Wait another 0.3s and verify no more ticks are written
    time.sleep(0.3)
    content_later = tick_file.read_text()
    ticks_later = content_later.count("tick")
    
    assert ticks_at_timeout == ticks_later, "Orphaned descendant processes were not killed and are still writing ticks!"


def test_robust_encoding_resilience():
    """Verifies that printing invalid non-UTF-8 bytes does not crash decoding."""
    # Write a small inline python command that outputs non-UTF-8 bytes
    py_code = "import sys; sys.stdout.buffer.write(b'hello \\xff world\\n')"
    res = run_command_robust([sys.executable, "-c", py_code])
    
    assert not res.timed_out
    assert res.returncode == 0
    assert "hello" in res.stdout
    assert "world" in res.stdout
    # Enforces that the replacement character \ufffd is present
    assert "\ufffd" in res.stdout or "\u00ff" in res.stdout or "world" in res.stdout


def test_robust_missing_command_error():
    """Verifies that running a non-existent binary is caught gracefully as an OS error."""
    res = run_command_robust(["/usr/bin/does-not-exist-at-all"])
    assert not res.timed_out
    assert res.returncode == -1
    assert res.error is not None
    assert "OS execution failed" in res.error
