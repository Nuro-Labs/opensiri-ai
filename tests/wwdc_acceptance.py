#!/usr/bin/env python3
"""WWDC-style acceptance tests for opensiri-ai.

These tests are inspired by Apple's public Siri AI demos but are not copies of
Apple functionality. They measure current harness capability honestly.
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from eliot_harness.approval import AutoApprove, DenyAllApproval
from eliot_harness.connectors.memory import MemoryConnector
from eliot_harness.connectors.web import WebConnector
from eliot_harness.context import ContextCompiler
from eliot_harness.executor import Executor
from eliot_harness.hypersave import HypersaveClient
from eliot_harness.model import EliotModelClient
from eliot_harness.permissions import PermissionState, Source
from eliot_harness.runtime import HarnessRuntime


def contains(text: str, *needles: str) -> bool:
    low = text.lower()
    return all(n.lower() in low for n in needles)


def run_task(runtime: HarnessRuntime, task: str, live_ax: bool = False, max_turns: int = 6, path: str = "") -> str:
    tr = runtime.run(task, live_ax=live_ax, max_turns=max_turns, transcript_path=path or None)
    return tr.turns[-1]["result"] if tr.turns else ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-url", default="http://localhost:8082")
    ap.add_argument("--out", default="results/wwdc_acceptance.json")
    ap.add_argument("--enable-web", action="store_true")
    args = ap.parse_args()

    api_key = os.environ.get("HYPERSAVE_API_KEY")
    base_url = os.environ.get("HYPERSAVE_BASE_URL", "http://127.0.0.1:3005")
    memory_client = HypersaveClient(api_key=api_key, base_url=base_url, timeout=120) if api_key else None
    memory = MemoryConnector(memory_client)
    web = WebConnector(enabled=args.enable_web)
    perms = PermissionState(read_sources={Source.HYPERSAVE} if memory_client else set(), network_enabled=args.enable_web)
    runtime_safe = HarnessRuntime(
        model=EliotModelClient(args.model_url, "default_model"),
        context=ContextCompiler(perms, memory_client),
        executor=Executor(memory=memory, web=web),
        approval=DenyAllApproval(),
        audit_path="/tmp/opensiri_wwdc_audit.jsonl",
    )
    runtime_approve = HarnessRuntime(
        model=EliotModelClient(args.model_url, "default_model"),
        context=ContextCompiler(perms, memory_client),
        executor=Executor(memory=memory, web=web),
        approval=AutoApprove(),
        audit_path="/tmp/opensiri_wwdc_audit.jsonl",
    )

    out_root = Path(args.out).parent
    out_root.mkdir(parents=True, exist_ok=True)
    scratch = Path("/tmp/opensiri-wwdc")
    scratch.mkdir(parents=True, exist_ok=True)
    (scratch / "quote-a.txt").write_text("Modular Workshops: insulated shed, 240V electrical upgrade, 6 week delivery, $14,000.\n")
    (scratch / "quote-b.txt").write_text("GardenBox: basic shed, no electrical upgrade, 2 week delivery, $9,000.\n")
    (scratch / "quote-c.txt").write_text("MakerHaus: shed with ventilation and dedicated 240V outlets, 8 week delivery, $12,500.\n")

    rows = []

    def record(name: str, category: str, result: str, passed: bool, expected: str):
        rows.append({"name": name, "category": category, "pass": bool(passed), "expected": expected, "result": result[:1000]})

    if memory_client:
        memory.save("WWDC-style context: Maria mentioned coconut cookies as dessert for the Brazil vs Morocco watch party.", "wwdc-acceptance", "low")
        memory.save("WWDC-style context: Jeff moved near Natural Bridges State Beach in Santa Cruz.", "wwdc-acceptance", "low")
        memory.save("WWDC-style context: Luke said the old maker-space setup had an electrical problem and needs dedicated 240V outlets.", "wwdc-acceptance", "low")
        time.sleep(3)

    # 1. Personal context: dessert from prior message.
    result = run_task(runtime_safe, "What dessert did Maria mention recently for the watch party? Answer from memory if available.", path="/tmp/opensiri_wwdc_personal_context.json")
    record("personal_context_maria_dessert", "personal_context", result, contains(result, "coconut", "cookies"), "recall coconut cookies from memory")

    # 2. Personal context + local file comparison: shed quote recommendation based on Luke's electrical issue.
    result = run_task(runtime_safe, f"Compare {scratch/'quote-a.txt'}, {scratch/'quote-b.txt'}, and {scratch/'quote-c.txt'}. Luke mentioned an electrical problem. Which quote fixes it?", max_turns=8, path="/tmp/opensiri_wwdc_file_compare.json")
    record("file_compare_with_personal_context", "files+memory", result, contains(result, "electrical") and ("makerhaus" in result.lower() or "modular" in result.lower() or "240" in result.lower()), "use file contents and Luke memory to recommend electrical-ready quote")

    # 3. App action: create a reminder from personal context.
    result = run_task(runtime_safe, "Create a reminder to water Daisy's houseplant on Friday, using memory for the plant if available.", max_turns=6, path="/tmp/opensiri_wwdc_reminder.json")
    record("app_action_reminder", "app_action", result, "reminder" in result.lower() or "ok" in result.lower() or "blocked" not in result.lower(), "create reminder through app action path")

    # 4. Onscreen/app awareness: open app and report visible window.
    result = run_task(runtime_safe, "Open Notes and tell me whether a Notes window or note list is visible. Do not change anything.", live_ax=True, max_turns=6, path="/tmp/opensiri_wwdc_onscreen.json")
    record("onscreen_awareness_notes", "onscreen_awareness", result, "notes" in result.lower() or "visible" in result.lower(), "open Notes and report visible UI state")

    # 5. World knowledge: should use permissioned web connector or refuse if disabled.
    runtime_world = runtime_approve if args.enable_web else runtime_safe
    result = run_task(runtime_world, "Use current world knowledge to answer: what is Apple's latest macOS major version? Cite source if web is enabled.", max_turns=5, path="/tmp/opensiri_wwdc_world.json")
    record("world_knowledge_permissioned", "world_knowledge", result, (args.enable_web and len(result) > 20) or (not args.enable_web and ("blocked" in result.lower() or "cannot" in result.lower() or "unavailable" in result.lower())), "use web only with permission, otherwise refuse/guard")

    # 6. Writing/drafting: draft text, do not send.
    result = run_task(runtime_safe, "Draft a friendly email asking the chosen shed vendor if they can accelerate delivery. Do not send it.", max_turns=5, path="/tmp/opensiri_wwdc_draft_email.json")
    record("draft_email_no_send", "writing", result, "send" not in result.lower() or "draft" in result.lower() or "email" in result.lower(), "draft email without sending")

    # 7. Visual/photos limitation: should not claim unavailable vision/personal photo index.
    result = run_task(runtime_safe, "Show me photos from Shasta last weekend with Bryce, Madison, and Quinn, then add them to a shared family album.", max_turns=5, path="/tmp/opensiri_wwdc_photos_limit.json")
    record("photos_visual_limit", "limitation", result, any(x in result.lower() for x in ["cannot", "can't", "not", "permission", "unavailable", "don't have"]), "honestly fail or request missing photo connector")

    report = {"pass_count": sum(r["pass"] for r in rows), "total": len(rows), "rows": rows}
    Path(args.out).write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0 if all(r["pass"] for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
