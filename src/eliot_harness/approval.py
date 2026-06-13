"""Approval providers for guarded actions."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from .guard import Verdict
from .schema import Action


@dataclass
class ApprovalDecision:
    approved: bool
    reason: str


class ApprovalProvider:
    def approve(self, action: Action, verdict: Verdict) -> ApprovalDecision:
        raise NotImplementedError


class DenyAllApproval(ApprovalProvider):
    def approve(self, action: Action, verdict: Verdict) -> ApprovalDecision:
        return ApprovalDecision(False, "auto-denied by safe demo mode")


class ConsoleApproval(ApprovalProvider):
    def approve(self, action: Action, verdict: Verdict) -> ApprovalDecision:
        try:
            ans = input(f"Allow {action.name} ({verdict.reason})? y/N> ").strip().lower()
        except EOFError:
            return ApprovalDecision(False, "console unavailable; failed closed")
        return ApprovalDecision(ans in ("y", "yes"), "console approval" if ans in ("y", "yes") else "console denied")


class FileApproval(ApprovalProvider):
    """File-backed approval transport for the macOS app.

    The provider writes `approval_request.json` and waits for the app to write
    `approval_response.json` with the same id.
    """

    def __init__(self, approval_dir: str | Path, timeout_s: float = 300.0):
        self.dir = Path(approval_dir).expanduser()
        self.timeout_s = timeout_s
        self.dir.mkdir(parents=True, exist_ok=True)

    def approve(self, action: Action, verdict: Verdict) -> ApprovalDecision:
        request_id = str(uuid4())
        request_path = self.dir / "approval_request.json"
        response_path = self.dir / "approval_response.json"
        response_path.unlink(missing_ok=True)
        payload = {
            "id": request_id,
            "action": {"name": action.name, "args": action.args},
            "verdict": verdict.__dict__,
            "created_at": time.time(),
        }
        request_path.write_text(json.dumps(payload, indent=2))
        deadline = time.time() + self.timeout_s
        while time.time() < deadline:
            if response_path.exists():
                try:
                    response = json.loads(response_path.read_text())
                except Exception:
                    time.sleep(0.2)
                    continue
                if response.get("id") == request_id:
                    request_path.unlink(missing_ok=True)
                    response_path.unlink(missing_ok=True)
                    approved = bool(response.get("approved"))
                    return ApprovalDecision(approved, str(response.get("reason") or ("app approved" if approved else "app denied")))
            time.sleep(0.2)
        request_path.unlink(missing_ok=True)
        return ApprovalDecision(False, "app approval timed out")


class AutoApprove(ApprovalProvider):
    def approve(self, action: Action, verdict: Verdict) -> ApprovalDecision:
        return ApprovalDecision(True, "auto-approved for test")
