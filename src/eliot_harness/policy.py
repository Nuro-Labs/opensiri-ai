"""Central policy engine for action routing and permission decisions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .guard import Verdict, classify
from .permissions import PermissionState, PermissionTier, Source
from .schema import Action


class PolicyDecision(str, Enum):
    ALLOW = "allow"
    REQUIRE_APPROVAL = "require_approval"
    DENY = "deny"


@dataclass
class PolicyResult:
    decision: PolicyDecision
    reason: str
    tier: PermissionTier
    guard: Verdict


class PolicyEngine:
    """Maps model actions to allow/approval/deny decisions.

    This is separate from the guard classifier so product permissions can evolve
    without weakening deterministic risky-action detection.
    """

    def __init__(self, permissions: PermissionState):
        self.permissions = permissions

    def evaluate(self, action: Action, obs: str | None = None) -> PolicyResult:
        guard = classify(action.__dict__, obs)
        tier = self._tier_from_guard(guard)
        if guard.destructive:
            if tier == PermissionTier.EXTERNAL and not self.permissions.network_enabled:
                return PolicyResult(PolicyDecision.REQUIRE_APPROVAL, guard.reason, tier, guard)
            return PolicyResult(PolicyDecision.REQUIRE_APPROVAL, guard.reason, tier, guard)

        if action.name in ("memory_search", "memory_ask"):
            if not self.permissions.can_read(Source.HYPERSAVE):
                return PolicyResult(PolicyDecision.DENY, "memory read is not enabled", PermissionTier.READ_LOCAL, guard)
        if action.name == "memory_save":
            if not self.permissions.can_write(Source.HYPERSAVE):
                return PolicyResult(PolicyDecision.REQUIRE_APPROVAL, "memory write requires approval", PermissionTier.MUTATE_LOCAL, guard)
        if action.name in ("mail_send", "message_send"):
            return PolicyResult(PolicyDecision.REQUIRE_APPROVAL, "external send requires explicit approval", PermissionTier.EXTERNAL, guard)
        if action.name == "mail_action" and str(action.args.get("action", "")) in ("flag_selected", "unread_selected", "archive_selected"):
            return PolicyResult(PolicyDecision.REQUIRE_APPROVAL, "Mail state change requires approval", PermissionTier.MUTATE_LOCAL, guard)
        if action.name in ("browser_open_url", "browser_open_youtube_liked", "browser_play_youtube", "browser_close_tab", "browser_open_downloads"):
            return PolicyResult(PolicyDecision.REQUIRE_APPROVAL, "browser action requires approval", PermissionTier.EXTERNAL, guard)
        if action.name == "system_control" and str(action.args.get("action", "status")) != "status":
            return PolicyResult(PolicyDecision.REQUIRE_APPROVAL, "system control change requires approval", PermissionTier.MUTATE_LOCAL, guard)
        if action.name == "finder_action" and str(action.args.get("action", "info")) not in ("info",):
            return PolicyResult(PolicyDecision.REQUIRE_APPROVAL, "Finder action requires approval", PermissionTier.MUTATE_LOCAL, guard)
        return PolicyResult(PolicyDecision.ALLOW, "allowed", tier, guard)

    @staticmethod
    def _tier_from_guard(guard: Verdict) -> PermissionTier:
        try:
            return PermissionTier(guard.tier)
        except ValueError:
            return PermissionTier.READ_LOCAL
