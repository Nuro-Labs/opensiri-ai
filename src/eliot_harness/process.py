"""Robust subprocess execution engine with process group and timeout lifecycle management."""

from __future__ import annotations

import os
import signal
import subprocess
from dataclasses import dataclass


@dataclass
class ProcessResult:
    stdout: str
    stderr: str
    returncode: int
    timed_out: bool
    error: str | None = None


def run_command_robust(
    cmd_args: list[str] | str,
    timeout: float = 30.0,
    shell: bool = False,
    env: dict | None = None,
    errors: str = "replace",
) -> ProcessResult:
    """Executes a command with process group management, timeout cleanup, and encoding resilience.

    Enforces:
    1. Process group isolation (start_new_session=True) to track descendants on Unix.
    2. Complete process group SIGKILL on timeout to prevent zombie leaks.
    3. Encoding error resilience (errors="replace") to avoid decoding crashes.
    4. Safe exception boundaries catching OS errors (e.g. command not found).
    """
    try:
        proc = subprocess.Popen(
            cmd_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            errors=errors,
            shell=shell,
            env=env,
            start_new_session=True,  # Unix process group leader
        )
    except OSError as e:
        return ProcessResult(
            stdout="",
            stderr="",
            returncode=-1,
            timed_out=False,
            error=f"OS execution failed: {type(e).__name__}: {str(e)}",
        )

    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        return ProcessResult(
            stdout=stdout or "",
            stderr=stderr or "",
            returncode=proc.returncode,
            timed_out=False,
            error=None,
        )
    except subprocess.TimeoutExpired:
        # 1. Kill the entire process group (including any grandchildren/descendants)
        try:
            pgid = os.getpgid(proc.pid)
            os.killpg(pgid, signal.SIGKILL)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

        # 2. Reaping and draining remaining output buffers to prevent file descriptor leaks
        try:
            stdout, stderr = proc.communicate(timeout=2.0)
        except Exception:
            # Fallback if communication hangs even after killing
            stdout, stderr = "", ""

        return ProcessResult(
            stdout=stdout or "",
            stderr=stderr or "",
            returncode=-1,
            timed_out=True,
            error=f"Command timed out after {timeout} seconds",
        )
    except Exception as e:
        # Fallback cleanup for any unexpected exceptions
        try:
            pgid = os.getpgid(proc.pid)
            os.killpg(pgid, signal.SIGKILL)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        return ProcessResult(
            stdout="",
            stderr="",
            returncode=-1,
            timed_out=False,
            error=f"Unexpected execution error: {type(e).__name__}: {str(e)}",
        )
