from pathlib import Path

from eliot_harness.audit import append_audit
from eliot_harness.context import ContextCompiler
from eliot_harness.guard import classify
from eliot_harness.model import EliotModelClient
from eliot_harness.permissions import PermissionState
from eliot_harness.policy import PolicyDecision, PolicyEngine
from eliot_harness.writing import is_draft_only_task, draft_from_context
from eliot_harness.schema import normalize_action


def test_guard_blocks_delete():
    assert classify({"name": "run_shell", "args": {"cmd": "rm /tmp/x"}}).destructive


def test_guard_allows_new_file_creation():
    p = Path("/tmp/eliot_harness_test_new.txt")
    if p.exists():
        p.unlink()
    assert not classify({"name": "run_shell", "args": {"cmd": f"echo hi > {p}"}}).destructive


def test_audit_redacts_secret():
    p = Path("/tmp/eliot_harness_test_audit.jsonl")
    append_audit(p, {"token": "sk-test-secret"})
    assert "sk-test" not in p.read_text()


def test_normalize_action_rejects_unknown():
    assert normalize_action({"name": "open_app", "args": {"name": "Notes"}}).name == "open_app"
    assert normalize_action({"name": "bad", "args": {}}) is None


def test_context_compiler_renders_permissions():
    ctx = ContextCompiler(PermissionState()).compile("hello").render()
    assert "PERMISSIONS" in ctx


def test_model_parse_action_structured():
    client = EliotModelClient()
    msg = {"tool_calls": [{"function": {"name": "open_app", "arguments": '{"name":"Notes"}'}}]}
    assert client._parse_action(msg).args["name"] == "Notes"


def test_memory_connector_handles_missing_client():
    from eliot_harness.connectors.memory import MemoryConnector
    c = MemoryConnector(None)
    assert c.ask("x") == "memory unavailable"
    assert c.save("x", "test") == "memory unavailable"


def test_policy_denies_memory_without_permission():
    engine = PolicyEngine(PermissionState())
    result = engine.evaluate(normalize_action({"name": "memory_ask", "args": {"query": "x"}}))
    assert result.decision == PolicyDecision.DENY


def test_policy_requires_approval_for_delete():
    engine = PolicyEngine(PermissionState())
    result = engine.evaluate(normalize_action({"name": "run_shell", "args": {"cmd": "rm /tmp/x"}}))
    assert result.decision == PolicyDecision.REQUIRE_APPROVAL


def test_draft_only_detection_and_output():
    assert is_draft_only_task("Draft an email to Alex. Do not send it.")
    draft = draft_from_context("Draft an email asking to accelerate delivery. Do not send it.", "Alex Chen alex@example.test ventilation 240V concise")
    assert "Draft email" in draft and "Subject:" in draft and "delivery" in draft.lower()


def test_app_connectors_dry_run_writes():
    from eliot_harness.connectors.notes import NotesConnector
    from eliot_harness.connectors.reminders import RemindersConnector
    from eliot_harness.connectors.calendar import CalendarConnector
    assert "DRY RUN" in NotesConnector().create_note("T", "B").text
    assert "DRY RUN" in RemindersConnector().add_reminder("Water plant").text
    assert "DRY RUN" in CalendarConnector().create_event("Meeting").text


def test_mail_messages_do_not_send_by_default():
    from eliot_harness.connectors.mail import MailConnector
    from eliot_harness.connectors.messages import MessagesConnector
    assert "Draft email" in MailConnector().draft_email("a@example.test", "S", "B").text
    assert "SEND REQUIRES APPROVAL" in MailConnector().send_email("a@example.test", "S", "B").text
    assert "Draft message" in MessagesConnector().draft_message("Alex", "Hi").text
    assert "SEND REQUIRES APPROVAL" in MessagesConnector().send_message("Alex", "Hi").text
