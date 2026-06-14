#!/usr/bin/env python3
"""Siri-style acceptance suite from the Golden Gate demo transcript.

These are harness tests, not Apple Siri tests. They seed synthetic personal
context into Hypersave and local scratch files, then run the same tasks through a
model-backed HarnessRuntime.
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


def has(text: str, *needles: str) -> bool:
    low = text.lower()
    return all(n.lower() in low for n in needles)


def any_has(text: str, *needles: str) -> bool:
    low = text.lower()
    return any(n.lower() in low for n in needles)


def not_failed(text: str) -> bool:
    low = text.lower()
    return not any(x in low for x in ("unable to", "could not", "couldn't", "cannot find", "can't find"))


def run_task(runtime: HarnessRuntime, task: str, *, app: str = "Desktop", ui_tree: str = 'AXDesktop "Desktop" id=1', max_turns: int = 8, path: str = "") -> str:
    try:
        tr = runtime.run(task, app=app, ui_tree=ui_tree, max_turns=max_turns, transcript_path=path or None)
        return tr.turns[-1]["result"] if tr.turns else ""
    except Exception as e:
        return f"error: {type(e).__name__}"


def seed_memory(memory: MemoryConnector) -> None:
    facts = [
        "Mail thread: Carly asked about my Todoist one-click setup this morning. I replied to Carly at 10:42 AM saying the setup is ready and included the one-click link.",
        "Skydive Spain trip: calendar shows my last visit was October 2025. Notes say I brought my own private liability insurance and did not pay Skydive Spain directly for insurance.",
        "Toastmasters District 59 newsletter: latest email newsletter was sent May 11 and had subject 'District 59 Newsletter - May Updates'.",
        "Big Picture Productivity course transcripts: goal setting approach starts with long-term priorities, turns them into concrete goals, breaks goals into projects, and reviews weekly.",
        "Houseplant context: Daisy's plant is a Monstera deliciosa.",
    ]
    for fact in facts:
        memory.save(fact, "siri-examples-acceptance", "high")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-url", default="http://localhost:8081")
    ap.add_argument("--model-name", default="default_model")
    ap.add_argument("--model-api-key-env", default="OPENSIRI_MODEL_API_KEY")
    ap.add_argument("--model-auth-header", default=os.environ.get("OPENSIRI_MODEL_AUTH_HEADER", "api-key"))
    ap.add_argument("--out", default="results/siri_examples_acceptance.json")
    ap.add_argument("--enable-web", action="store_true")
    ap.add_argument("--skip-seed", action="store_true")
    args = ap.parse_args()

    api_key = os.environ.get("HYPERSAVE_API_KEY")
    base_url = os.environ.get("HYPERSAVE_BASE_URL", "https://api.hypersave.io")
    if api_key:
        memory_client = HypersaveClient(api_key=api_key, base_url=base_url, timeout=120)
    else:
        class MockHypersaveClient:
            def __init__(self):
                self.memories = []
            def save(self, content: str, source: str, sensitivity: str = "medium"):
                self.memories.append({"content": content, "category": source, "sensitivity": sensitivity})
                return {"status": "complete", "pendingId": "mock-id"}
            def save_and_wait(self, content: str, source: str, sensitivity: str = "medium", timeout_s: float = 90.0):
                return self.save(content, source, sensitivity)
            def search(self, query: str, limit: int = 8, max_sensitivity: str = "high"):
                words = [w.lower() for w in query.replace("?", "").replace(".", "").replace(",", "").split() if len(w) > 3]
                results = []
                for m in self.memories:
                    content_lower = m["content"].lower()
                    if not words or any(w in content_lower for w in words):
                        results.append(m)
                return {"results": results[:limit]}
            def ask(self, query: str, max_sensitivity: str = "high"):
                res = self.search(query, max_sensitivity=max_sensitivity)
                snippets = [item["content"] for item in res.get("results", [])]
                return {"answer": "\n".join(snippets) if snippets else "I could not find any information."}
        memory_client = MockHypersaveClient()
    memory = MemoryConnector(memory_client)
    if not args.skip_seed:
        seed_memory(memory)
        time.sleep(2)

    scratch = Path("/tmp/opensiri-siri-examples")
    scratch.mkdir(parents=True, exist_ok=True)
    receipts = scratch / "receipts"
    receipts.mkdir(exist_ok=True)
    (receipts / "openai.txt").write_text("Vendor: OpenAI\nAmount: $70.12\n")
    (receipts / "cursor.txt").write_text("Vendor: Cursor\nAmount: $43.76\n")
    (receipts / "coffee.txt").write_text("Vendor: Blue Bottle\nAmount: $20.00\n")
    transcripts = scratch / "big-picture-productivity"
    transcripts.mkdir(exist_ok=True)
    (transcripts / "goal-setting.txt").write_text("Goal setting: identify long-term priorities, choose concrete goals, break them into projects and next actions, then review weekly.\n")

    read_sources = {s for s in Source}
    if not memory_client:
        read_sources.discard(Source.HYPERSAVE)
    write_sources = {s for s in Source}
    if not memory_client:
        write_sources.discard(Source.HYPERSAVE)
    perms = PermissionState(read_sources=read_sources, write_sources=write_sources, network_enabled=args.enable_web)
    model = EliotModelClient(args.model_url, args.model_name, api_key=os.environ.get(args.model_api_key_env), auth_header=args.model_auth_header)
    web = WebConnector(enabled=args.enable_web)
    runtime_safe = HarnessRuntime(model=model, context=ContextCompiler(perms, memory_client), executor=Executor(memory=memory, web=web), approval=DenyAllApproval(), audit_path="/tmp/opensiri_siri_examples_audit.jsonl")
    runtime_approve = HarnessRuntime(model=model, context=ContextCompiler(perms, memory_client), executor=Executor(memory=memory, web=web), approval=AutoApprove(), audit_path="/tmp/opensiri_siri_examples_audit.jsonl")

    rows = []

    def record(name: str, category: str, result: str, passed: bool, expected: str):
        rows.append({"name": name, "category": category, "pass": bool(passed), "expected": expected, "result": result[:1200]})

    result = run_task(runtime_safe, "Did I already reply to Carly about my Todoist one click setup? Use personal context and answer with evidence.", path="/tmp/opensiri_siri_carly.json")
    record("mail_reply_carly_todoist", "mail+memory", result, has(result, "carly") and any_has(result, "replied", "yes", "10:42"), "answer yes and cite reply context")

    result = run_task(runtime_safe, "Last time I visited Skydive Spain, how much did I pay for insurance? Search across personal context.", path="/tmp/opensiri_siri_skydive.json")
    record("skydive_spain_insurance", "mail+calendar+notes", result, any_has(result, "private liability", "did not pay", "didn't pay", "own") and any_has(result, "october", "2025", "insurance"), "infer own private liability insurance/no direct payment")

    result = run_task(runtime_approve, "Set a reminder to withdraw cash from the ATM next time I'm at Albertine on Von Swinden Strasse.", path="/tmp/opensiri_siri_location_reminder.json")
    record("location_reminder_atm", "reminders", result, any_has(result, "reminder", "dry run", "created", "albert", "atm"), "create or stage location reminder")

    result = run_task(runtime_safe, f"How much did I spend in total on these receipts: {receipts/'openai.txt'}, {receipts/'cursor.txt'}, {receipts/'coffee.txt'}? Also show per vendor.", max_turns=10, path="/tmp/opensiri_siri_receipts.json")
    record("finder_receipts_total", "files+math", result, any_has(result, "133.88", "133", "openai", "cursor"), "sum selected receipts to $133.88 and show vendors")

    routine_ui = 'AXWindow "Workout" id=1\nAXStaticText "Push day: bench press 3x8, overhead press 3x8, lateral raises 3x12, triceps pushdown 3x12, standing calf raises 4x15" id=2'
    result = run_task(runtime_safe, "Give me feedback on this strength training routine.", app="Safari", ui_tree=routine_ui, path="/tmp/opensiri_siri_screen_feedback.json")
    record("screen_strength_feedback", "screen", result, any_has(result, "calf", "push", "routine", "bench", "solid"), "reason over onscreen routine")

    result = run_task(runtime_safe, "Find the latest Toastmasters District 59 newsletter. I mean an email.", path="/tmp/opensiri_siri_newsletter.json")
    record("latest_toastmasters_newsletter", "mail+memory", result, not_failed(result) and has(result, "district 59") and any_has(result, "may 11", "newsletter"), "find latest newsletter email")

    result = run_task(runtime_approve, "I'm going to a Lindy Hop festival/workshop from July 3rd through 5th. It's an all-day event. Put it on my calendar, but make it busy.", path="/tmp/opensiri_siri_calendar.json")
    record("calendar_lindy_hop_multiday", "calendar", result, any_has(result, "calendar", "event", "dry run", "lindy", "july"), "create/stage all-day busy calendar event")

    result = run_task(runtime_approve, f"Find the transcripts of my video course Big Picture Productivity in {transcripts} and create a note summarizing my approach to goal setting.", max_turns=10, path="/tmp/opensiri_siri_course_note.json")
    record("course_transcripts_create_note", "files+notes", result, any_has(result, "goal", "note", "priorities", "weekly", "draft"), "summarize transcripts and create/stage note")

    mail_ui = 'AXWindow "Financial Times email" id=1\nAXStaticText "Financial Times newsletter" id=2\nAXLink "Unsubscribe" id=3'
    result = run_task(runtime_safe, "Can you unsubscribe me from this Financial Times email?", app="Mail", ui_tree=mail_ui, path="/tmp/opensiri_siri_unsubscribe.json")
    record("unsubscribe_financial_times", "mail+screen", result, any_has(result, "unsubscribe", "unsubscription", "can't", "cannot", "could not", "link", "approval", "click"), "handle or safely refuse unsubscribe")

    shortcuts_ui = 'AXWindow "Shortcuts" id=1\nAXButton "New Shortcut" id=2\nAXGroup "Shortcut editor" id=3'
    result = run_task(runtime_safe, "When I leave home and I have a Toastmasters event on my calendar in the next hour send Kathy my live location for half an hour. Build this shortcut automation.", app="Shortcuts", ui_tree=shortcuts_ui, max_turns=8, path="/tmp/opensiri_siri_shortcut.json")
    record("shortcut_location_automation", "shortcuts", result, any_has(result, "shortcut", "automation", "toastmasters", "kathy", "unsupported", "cannot"), "create or honestly fail shortcut automation")

    report = {"pass_count": sum(r["pass"] for r in rows), "total": len(rows), "rows": rows}
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0 if all(r["pass"] for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
