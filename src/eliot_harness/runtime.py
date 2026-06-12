"""End-to-end Eliot harness runtime loop."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .approval import ApprovalProvider, DenyAllApproval
from .audit import append_audit
from .context import ContextCompiler
from .executor import Executor
from .guard import classify
from .model import EliotModelClient
from .prompt import ELIOT_SYSTEM
from .schema import make_observation
from .transcript import Transcript
from . import mac_ax


class HarnessRuntime:
    def __init__(self, model: EliotModelClient, context: ContextCompiler, executor: Executor, approval: ApprovalProvider | None = None, audit_path: str = "results/audit.jsonl"):
        self.model = model
        self.context = context
        self.executor = executor
        self.approval = approval or DenyAllApproval()
        self.audit_path = audit_path

    def run(self, task: str, app: str = "Desktop", ui_tree: str = 'AXDesktop "Desktop" id=1', max_turns: int = 12, transcript_path: str | None = None, live_ax: bool = False) -> Transcript:
        transcript = Transcript(task=task)
        messages: list[dict[str, Any]] = [{"role": "system", "content": ELIOT_SYSTEM}]
        result = "none"
        for turn in range(max_turns):
            if live_ax:
                snap = mac_ax.observe()
                app, ui_tree = snap.app_name, snap.tree_text
            ctx = self.context.compile(task).render()
            obs = make_observation(task, app, ui_tree, result, ctx)
            messages.append({"role": "user" if turn == 0 else "tool", "content": obs})
            model_result = self.model.complete(messages)
            action = model_result.action
            rec: dict[str, Any] = {"turn": turn, "obs": obs, "action": action.__dict__ if action else None, "latency_s": round(model_result.latency_s, 3)}
            if action is None:
                rec["result"] = "error: unparseable model output"
                transcript.add(rec)
                append_audit(self.audit_path, {"event": "unparseable", "record": rec})
                break
            messages.append({"role": "assistant", "content": "", "tool_calls": [{"type": "function", "id": f"call_{turn}", "function": {"name": action.name, "arguments": json.dumps(action.args)}}]})
            verdict = classify(action.__dict__, obs)
            if verdict.destructive:
                decision = self.approval.approve(action, verdict)
                rec["guard"] = verdict.__dict__
                rec["approval"] = decision.__dict__
                if not decision.approved:
                    rec["result"] = "blocked-by-guard"
                    transcript.add(rec)
                    append_audit(self.audit_path, {"event": "guard_block", "record": rec})
                    result = 'user: "No — blocked by safety guard."'
                    continue
            executed = self.executor.execute(action)
            rec["result"] = executed.output[:1000]
            transcript.add(rec)
            append_audit(self.audit_path, {"event": "tool_result", "record": rec})
            result = executed.output
            if executed.terminal:
                break
        if transcript_path:
            transcript.write(Path(transcript_path))
        return transcript
