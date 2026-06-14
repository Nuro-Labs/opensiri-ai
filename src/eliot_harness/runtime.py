"""End-to-end Eliot harness runtime loop."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .approval import ApprovalProvider, DenyAllApproval
from .audit import append_audit
from .context import ContextCompiler
from .executor import Executor
from .guard import Verdict, classify
from .model import EliotModelClient
from .policy import PolicyDecision, PolicyEngine
from .prompt import ELIOT_SYSTEM
from .schema import Action, make_observation
from .transcript import Transcript
from . import mac_ax
from .session import SessionState
from .session_store import save_session


class HarnessRuntime:
    def __init__(self, model: EliotModelClient, context: ContextCompiler, executor: Executor, approval: ApprovalProvider | None = None, audit_path: str = "results/audit.jsonl"):
        self.model = model
        self.context = context
        self.executor = executor
        self.approval = approval or DenyAllApproval()
        self.audit_path = audit_path
        self.policy = PolicyEngine(context.permissions)

    def run(self, task: str, app: str = "Desktop", ui_tree: str = 'AXDesktop "Desktop" id=1', max_turns: int = 12, transcript_path: str | None = None, live_ax: bool = False) -> Transcript:
        transcript = Transcript(task=task)
        session = SessionState(task=task)
        messages: list[dict[str, Any]] = [{"role": "system", "content": ELIOT_SYSTEM}]
        result = "none"
        target_app: str | None = None
        last_tool_call_id: str | None = None
        for turn in range(max_turns):
            if live_ax:
                snap = mac_ax.observe(target_app)
                app, ui_tree = snap.app_name, snap.tree_text
            ctx = self.context.compile(task).render()
            obs = make_observation(task, app, ui_tree, result, ctx)
            if turn == 0:
                messages.append({"role": "user", "content": obs})
            else:
                messages.append({"role": "tool", "tool_call_id": last_tool_call_id or f"call_{turn - 1}", "content": obs})
            model_result = self.model.complete(messages)
            action = model_result.action
            rec: dict[str, Any] = {"turn": turn, "obs": obs, "action": action.__dict__ if action else None, "latency_s": round(model_result.latency_s, 3)}
            if action is None:
                rec["result"] = "error: unparseable model output"
                transcript.add(rec)
                append_audit(self.audit_path, {"event": "unparseable", "record": rec})
                break
            raw_tool_calls = model_result.raw.get("tool_calls") or []
            assist_content = (model_result.raw.get("content") or "").strip()
            if not assist_content:
                assist_content = (model_result.raw.get("reasoning") or model_result.raw.get("thought") or "").strip()
            if raw_tool_calls:
                last_tool_call_id = raw_tool_calls[0].get("id") or f"call_{turn}"
                messages.append({"role": "assistant", "content": assist_content, "tool_calls": raw_tool_calls})
            else:
                last_tool_call_id = f"call_{turn}"
                messages.append({"role": "assistant", "content": assist_content, "tool_calls": [{"type": "function", "id": last_tool_call_id, "function": {"name": action.name, "arguments": json.dumps(action.args)}}]})
            policy = self.policy.evaluate(action, obs)
            verdict = policy.guard
            rec["policy"] = {"decision": policy.decision.value, "reason": policy.reason, "tier": policy.tier.value}
            if policy.decision == PolicyDecision.DENY:
                rec["result"] = "blocked-by-policy"
                transcript.add(rec)
                append_audit(self.audit_path, {"event": "policy_block", "record": rec})
                result = 'user: "No — blocked by permission policy."'
                continue
            if policy.decision == PolicyDecision.REQUIRE_APPROVAL:
                decision = self.approval.approve(action, verdict)
                rec["guard"] = verdict.__dict__
                rec["approval"] = decision.__dict__
                if not decision.approved:
                    rec["result"] = "blocked-by-guard"
                    transcript.add(rec)
                    append_audit(self.audit_path, {"event": "guard_block", "record": rec})
                    result = 'user: "No — blocked by safety guard."'
                    continue
            if action.name == "ask_user":
                decision = self.approval.approve(action, Verdict(True, str(action.args.get("question", "approval requested")), "external"))
                rec["approval"] = decision.__dict__
                if not decision.approved:
                    rec["result"] = "blocked-by-user"
                    transcript.add(rec)
                    append_audit(self.audit_path, {"event": "user_block", "record": rec})
                    result = 'user: "No — not approved."'
                    continue
                result = 'user: "Approved."'
                rec["result"] = result
                transcript.add(rec)
                append_audit(self.audit_path, {"event": "user_approved", "record": rec})
                continue
            if action.name == "open_app":
                target_app = str(action.args.get("name", "")) or target_app
            executed = self.executor.execute(action)
            rec["result"] = executed.output[:1000]
            if action.name in ("memory_ask", "read") and executed.output:
                session.references.add("answer", executed.output[:120], executed.output)
            if action.name == "run_shell" and executed.output:
                session.references.add("shell_result", executed.output[:120], executed.output)
            transcript.add(rec)
            append_audit(self.audit_path, {"event": "tool_result", "record": rec})
            result = executed.output
            if executed.terminal:
                break
        if transcript_path:
            transcript.write(Path(transcript_path))
        save_session(session)
        return transcript
