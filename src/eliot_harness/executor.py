"""Safe executor boundary for Eliot actions."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass

from .connectors.memory import MemoryConnector
from .schema import Action


@dataclass
class ExecutionResult:
    output: str
    terminal: bool = False


class Executor:
    def __init__(self, memory: MemoryConnector | None = None, shell_timeout: float = 30.0):
        self.memory = memory
        self.shell_timeout = shell_timeout

    def execute(self, action: Action, snapshot=None) -> ExecutionResult:
        name, args = action.name, action.args
        if name == "done":
            return ExecutionResult(str(args.get("summary", "done")), terminal=True)
        if name == "ask_user":
            return ExecutionResult(f"user approval requested: {args.get('question', '')}")
        if name == "run_shell":
            cmd = str(args.get("cmd", ""))
            r = subprocess.run(["/bin/zsh", "-c", cmd], capture_output=True, text=True, timeout=self.shell_timeout)
            out = (r.stdout + r.stderr).strip()
            return ExecutionResult(out[:2000] if out else ("" if r.returncode == 0 else f"error: exit {r.returncode}"))
        if name == "memory_search":
            if not self.memory:
                return ExecutionResult("memory unavailable")
            return ExecutionResult("\n".join(x.text for x in self.memory.read_context(str(args.get("query", "")))))
        if name == "memory_ask":
            return ExecutionResult(self.memory.ask(str(args.get("query", ""))) if self.memory else "memory unavailable")
        if name == "memory_save":
            return ExecutionResult(self.memory.save(str(args.get("content", "")), str(args.get("source", "eliot")), str(args.get("sensitivity", "medium"))) if self.memory else "memory unavailable")
        return ExecutionResult(f"not implemented by generic executor: {name}")
