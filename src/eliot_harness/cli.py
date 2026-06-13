"""CLI for the Eliot harness."""

from __future__ import annotations

import argparse

from .approval import AutoApprove, ConsoleApproval, DenyAllApproval, FileApproval
from .config import load_config
from .connectors.memory import MemoryConnector
from .connectors.registry import build_registry
from .connectors.web import WebConnector
from .context import ContextCompiler
from .executor import Executor
from .hypersave import HypersaveClient
from .local_index import LocalIndex, DEFAULT_INDEX_PATH
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
    ap.add_argument("--approval", choices=["deny", "console", "app", "yes"], default="deny")
    ap.add_argument("--approval-dir", default="results/approvals")
    ap.add_argument("--enable-memory", action="store_true")
    ap.add_argument("--enable-memory-write", action="store_true")
    ap.add_argument("--enable-local-index", action="store_true")
    ap.add_argument("--index-path", default=str(DEFAULT_INDEX_PATH))
    ap.add_argument("--enable-web", action="store_true")
    ap.add_argument("--enable-files", action="store_true")
    ap.add_argument("--enable-mail", action="store_true")
    ap.add_argument("--enable-mail-write", action="store_true")
    ap.add_argument("--enable-messages", action="store_true")
    ap.add_argument("--enable-messages-write", action="store_true")
    ap.add_argument("--enable-photos", action="store_true")
    ap.add_argument("--enable-reminders", action="store_true")
    ap.add_argument("--enable-calendar", action="store_true")
    ap.add_argument("--enable-contacts", action="store_true")
    ap.add_argument("--enable-browser", action="store_true")
    ap.add_argument("--enable-browser-write", action="store_true")
    ap.add_argument("--enable-system", action="store_true")
    ap.add_argument("--enable-system-write", action="store_true")
    ap.add_argument("--enable-notes-write", action="store_true")
    ap.add_argument("--enable-reminders-write", action="store_true")
    ap.add_argument("--files-root", action="append", default=[])
    ap.add_argument("--config", default=None)
    ap.add_argument("--enable-visual", action="store_true")
    ap.add_argument("--enable-maps", action="store_true")
    ap.add_argument("--enable-music", action="store_true")
    ap.add_argument("--enable-podcasts", action="store_true")
    ap.add_argument("--live-ax", action="store_true", help="observe the live macOS Accessibility tree each turn")
    args = ap.parse_args()

    cfg = load_config(args.config) if args.config else load_config()
    if args.enable_web:
        cfg.network_enabled = True
        cfg.sources["web"].read = True
    if args.enable_files:
        cfg.sources["files"].read = True
    if args.enable_visual:
        cfg.sources["visual"].read = True
    if args.enable_photos:
        cfg.sources["photos"].read = True
    if args.enable_mail:
        cfg.sources["mail"].read = True
    if args.enable_mail_write:
        cfg.sources["mail"].read = True
        cfg.sources["mail"].write = True
    if args.enable_messages:
        cfg.sources["messages"].read = True
        cfg.sources["messages_index"].read = True
    if args.enable_messages_write:
        cfg.sources["messages"].read = True
        cfg.sources["messages"].write = True
        cfg.sources["messages_index"].read = True
    if args.enable_reminders:
        cfg.sources["reminders"].read = True
    if args.enable_calendar:
        cfg.sources["calendar"].read = True
    if args.enable_contacts:
        cfg.sources["contacts"].read = True
    if args.enable_browser:
        cfg.sources["browser"].read = True
    if args.enable_browser_write:
        cfg.sources["browser"].read = True
        cfg.sources["browser"].write = True
    if args.enable_system:
        cfg.sources["system"].read = True
    if args.enable_system_write:
        cfg.sources["system"].read = True
        cfg.sources["system"].write = True
    if args.enable_notes_write:
        cfg.sources["notes"].read = True
        cfg.sources["notes"].write = True
    if args.enable_reminders_write:
        cfg.sources["reminders"].read = True
        cfg.sources["reminders"].write = True
    for flag, source in [(args.enable_maps, "maps"), (args.enable_music, "music"), (args.enable_podcasts, "podcasts")]:
        if flag:
            cfg.sources[source].read = True
    if args.enable_memory:
        cfg.sources["hypersave"].read = True
    if args.enable_memory_write:
        cfg.sources["hypersave"].read = True
        cfg.sources["hypersave"].write = True
    memory_client = HypersaveClient.from_env() if cfg.sources["hypersave"].read else None
    local_index = LocalIndex(args.index_path) if args.enable_local_index else None
    memory = MemoryConnector(memory_client)
    registry = build_registry(cfg, memory_client, args.files_root or None)
    read_sources = {Source.HYPERSAVE} if memory_client else set()
    write_sources = {Source.HYPERSAVE} if memory_client and cfg.sources["hypersave"].write else set()
    if cfg.sources["notes"].write:
        write_sources.add(Source.NOTES)
    if cfg.sources["reminders"].write:
        write_sources.add(Source.REMINDERS)
    for source in ("mail", "messages", "browser", "system"):
        if cfg.sources[source].write:
            write_sources.add(Source(source))
    if cfg.network_enabled:
        read_sources.add(Source.WEB)
    if cfg.sources["files"].read:
        read_sources.add(Source.FILES)
    for source in ("mail", "messages", "reminders", "calendar", "contacts", "browser", "system", "photos", "visual", "maps", "music", "podcasts"):
        if cfg.sources[source].read:
            read_sources.add(Source(source))
    perms = PermissionState(read_sources=read_sources, write_sources=write_sources, network_enabled=cfg.network_enabled)
    approval = {"deny": DenyAllApproval(), "console": ConsoleApproval(), "app": FileApproval(args.approval_dir), "yes": AutoApprove()}[args.approval]
    runtime = HarnessRuntime(
        model=EliotModelClient(args.model_url, args.model_name),
        context=ContextCompiler(perms, memory_client, registry, local_index),
        executor=Executor(memory, web=WebConnector(enabled=cfg.network_enabled), permissions=perms, local_index=local_index, file_roots=args.files_root or None),
        approval=approval,
        audit_path=args.audit_log,
    )
    tr = runtime.run(args.task, transcript_path=args.transcript, live_ax=args.live_ax)
    print(tr.turns[-1]["result"] if tr.turns else "no result")


if __name__ == "__main__":
    main()
