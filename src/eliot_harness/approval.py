"""Approval providers for guarded actions."""

from __future__ import annotations

from dataclasses import dataclass

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
        ans = input(f"Allow {action.name} ({verdict.reason})? y/N> ").strip().lower()
        return ApprovalDecision(ans in ("y", "yes"), "console approval" if ans in ("y", "yes") else "console denied")


class AutoApprove(ApprovalProvider):
    def approve(self, action: Action, verdict: Verdict) -> ApprovalDecision:
        return ApprovalDecision(True, "auto-approved for test")
