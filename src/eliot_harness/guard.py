"""Deterministic pre-execution guard for Eliot tool calls."""

from __future__ import annotations

import re
import shlex
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Verdict:
    destructive: bool
    reason: str = ""
    tier: str = "read_local"


_REDIRECT_RE = re.compile(r"(?<!>)>(?!>)\s*([^|>&\s]+)")
_SHELL_RULES = [
    (r"\b(rm|rmdir|unlink)\b", "file deletion", "destructive"),
    (r"\bfind\b.+\s-delete\b", "file deletion", "destructive"),
    (r"\b(trash|gio\s+trash)\b", "move to trash", "destructive"),
    (r"\bmv\b.+(?:~?/\.Trash|/Trash)\b", "move to trash", "destructive"),
    (r"\bsudo\b", "privilege escalation", "credential"),
    (r"(^|[;&|]\s*):\s*>\s*[^|>&\s]", "shell truncation", "destructive"),
    (r"\b(tee|dd|truncate)\b", "overwrite/truncation utility", "destructive"),
    (r"\b(sed|perl)\b\s+[^;&|]*-(?:[^;&|]*i|p?i)\b", "in-place file edit", "destructive"),
    (r"\b(curl|wget|http|httpie|aria2c|ftp|sftp|scp|ssh|nc|ncat|telnet)\b", "network egress", "external"),
    (r"\b(npm|pnpm|yarn)\s+publish\b|\btwine\s+upload\b|\bgh\s+release\s+(create|upload)\b", "publish/release", "external"),
    (r"\b(kubectl|docker)\b[^;&|]*\b(delete|rm|rmi|prune|kill)\b", "orchestrator destructive op", "destructive"),
    (r"(^|[\s\"'=:])(/System|/usr|/etc|/var|/bin|/sbin)\b", "system path", "destructive"),
    (r"~/Library|/Library", "Library path", "destructive"),
]
_LABEL_RULES = [
    (r"\b(delete|remove|trash|move to trash|empty trash)\b", "delete/trash", "destructive"),
    (r"\b(send|reply|reply all|forward)\b", "send message", "external"),
    (r"\b(pay|purchase|buy|checkout|place order|confirm payment)\b", "payment", "external"),
    (r"\b(overwrite|replace|save over|discard|don't save)\b", "overwrite/discard", "destructive"),
]
_SECURE_FIELD = re.compile(r"password|passcode|secure|AXSecureTextField|credit\s*card|cvv|ssn", re.I)


def _redirect_target_exists(cmd: str) -> bool | None:
    m = _REDIRECT_RE.search(cmd)
    if not m:
        return None
    try:
        parts = shlex.split(cmd[m.end(0) - len(m.group(1)):])
    except ValueError:
        return None
    if not parts:
        return None
    target = parts[0]
    if target == "/dev/null":
        return False
    if "$" in target or "`" in target or target.startswith(("&", ">")):
        return None
    return Path(target).expanduser().exists()


def _find_label(obs: str | None, nid) -> str:
    if obs is None or nid is None:
        return ""
    for line in obs.splitlines():
        m = re.search(r"\bid=(\d+)\b", line)
        if m and m.group(1) == str(nid):
            return line
    return ""


def classify(action: dict, obs: str | None = None) -> Verdict:
    if not action or not isinstance(action, dict):
        return Verdict(False)
    name = action.get("name")
    args = action.get("args") or {}

    if name == "run_shell":
        cmd = str(args.get("cmd", ""))
        redir_exists = _redirect_target_exists(cmd)
        if redir_exists:
            return Verdict(True, "run_shell: output redirection would overwrite existing file", "destructive")
        if redir_exists is None and _REDIRECT_RE.search(cmd):
            return Verdict(True, "run_shell: output redirection target unclear", "destructive")
        for pat, why, tier in _SHELL_RULES:
            if re.search(pat, cmd, re.I):
                return Verdict(True, f"run_shell: {why}", tier)
        return Verdict(False)

    if name == "web_search":
        return Verdict(True, "web_search: network egress requires approval", "external")
    if name in ("memory_save",):
        return Verdict(True, "memory write requires approval", "mutate_local")

    if name == "invoke_intent":
        blob = (str(args.get("intent", "")) + " " + str(args.get("params", ""))).lower()
        for pat, why, tier in _LABEL_RULES:
            if re.search(pat, blob, re.I):
                return Verdict(True, f"invoke_intent: {why}", tier)
        return Verdict(False)

    if name == "click":
        line = _find_label(obs, args.get("id"))
        for pat, why, tier in _LABEL_RULES:
            if re.search(pat, line, re.I):
                return Verdict(True, f"click: {why}", tier)
        return Verdict(False)

    if name == "type":
        line = _find_label(obs, args.get("id"))
        if _SECURE_FIELD.search(line):
            return Verdict(True, "type: secure field", "credential")
        return Verdict(False)

    return Verdict(False)
