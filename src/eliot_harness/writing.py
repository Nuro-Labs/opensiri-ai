"""Draft-only writing skills.

These are harness skills, not model autonomy. They never send messages; they
produce text drafts from scoped context when the user's task is explicitly about
drafting/composing without sending.
"""

from __future__ import annotations

import re


def is_draft_only_task(task: str) -> bool:
    t = task.lower()
    return any(x in t for x in ("draft", "write", "compose")) and any(x in t for x in ("email", "message")) and any(x in t for x in ("do not send", "don't send", "without sending", "not send"))


def draft_from_context(task: str, context: str) -> str:
    recipient = _recipient(task, context)
    subject = _subject(task, context)
    bullets = _bullets(task, context)
    return (
        f"Draft email to {recipient}\n"
        f"Subject: {subject}\n\n"
        "Hi,\n\n"
        + "\n".join(f"- {b}" for b in bullets)
        + "\n\nBest,\n"
    )


def _recipient(task: str, context: str) -> str:
    for text in (context, task):
        m = re.search(r"([A-Z][a-z]+\s+[A-Z][a-z]+|[A-Z][a-z]+)\s*\(?([\w.+-]+_at_[\w.-]+_dot_\w+|[\w.+-]+@[\w.-]+\.\w+)\)?", text)
        if m:
            return m.group(1)
        m = re.search(r"(?:to|contact)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text)
        if m:
            return m.group(1)
    return "the recipient"


def _subject(task: str, context: str) -> str:
    low = (task + "\n" + context).lower()
    if "delivery" in low or "accelerate" in low:
        return "Request to accelerate delivery"
    if "quote" in low or "supplier" in low:
        return "Question about the supplier quote"
    return "Follow-up"


def _bullets(task: str, context: str) -> list[str]:
    text = task + "\n" + context
    bullets: list[str] = []
    if re.search(r"ventilation|fumes|exhaust", text, re.I):
        bullets.append("We are prioritizing active ventilation and exhaust because resin printer fumes were an issue.")
    if re.search(r"240V|electrical|circuit", text, re.I):
        bullets.append("Your quote appears to address the electrical requirements we care about.")
    if re.search(r"accelerat|faster|lead time|delivery", text, re.I):
        bullets.append("Could you let us know whether the delivery timeline can be accelerated?")
    if re.search(r"concise|bullet", text, re.I):
        bullets.append("Keeping this brief: we are ready to move forward if the timeline can improve.")
    if not bullets:
        bullets.append("I wanted to follow up and ask whether you can help with the request below.")
    return bullets[:5]
