"""CLI for the Eliot harness."""

from __future__ import annotations

import argparse

from .approval import AutoApprove, ConsoleApproval, DenyAllApproval
from .connectors.memory import MemoryConnector
from .context import ContextCompiler
from .executor import Executor
from .hypersave import HypersaveClient
from .model import EliotModelClient
from .permissions import PermissionState, Source
from .runtime import HarnessRuntime


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--model-url", default="http://localhost:8081")
    ap.add_argument("--model-name", default="default_model")
    ap.add_argument("--transcript", default="results/transcript.json")
    ap.add_argument("--audit-log", default="results/audit.jsonl")
    ap.add_argument("--approval", choices=["deny", "console", "yes"], default="deny")
    ap.add_argument("--enable-memory", action="store_true")
    args = ap.parse_args()

    memory_client = HypersaveClient.from_env() if args.enable_memory else None
    memory = MemoryConnector(memory_client)
    perms = PermissionState(read_sources={Source.HYPERSAVE} if memory_client else set())
    approval = {"deny": DenyAllApproval(), "console": ConsoleApproval(), "yes": AutoApprove()}[args.approval]
    runtime = HarnessRuntime(
        model=EliotModelClient(args.model_url, args.model_name),
        context=ContextCompiler(perms, memory_client),
        executor=Executor(memory),
        approval=approval,
        audit_path=args.audit_log,
    )
    tr = runtime.run(args.task, transcript_path=args.transcript)
    print(tr.turns[-1]["result"] if tr.turns else "no result")


if __name__ == "__main__":
    main()
