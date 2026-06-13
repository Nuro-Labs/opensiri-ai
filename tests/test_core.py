from pathlib import Path

from eliot_harness.audit import append_audit
from eliot_harness.context import ContextCompiler
from eliot_harness.guard import classify
from eliot_harness.model import EliotModelClient
from eliot_harness.permissions import PermissionState
from eliot_harness.policy import PolicyDecision, PolicyEngine
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
