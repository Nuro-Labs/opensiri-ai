from pathlib import Path

from eliot_harness.audit import append_audit
from eliot_harness.context import ContextCompiler
from eliot_harness.guard import classify
from eliot_harness.model import EliotModelClient
from eliot_harness.permissions import PermissionState
from eliot_harness.policy import PolicyDecision, PolicyEngine
from eliot_harness.writing import is_draft_only_task, draft_from_context
from eliot_harness.references import ReferenceStore
from eliot_harness.sources import MANIFESTS, manifest_table
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


def test_local_index_roundtrip(tmp_path):
    from eliot_harness.local_index import LocalIndex
    idx = LocalIndex(tmp_path / "idx.sqlite3")
    idx.upsert("mail", "Google Cloud meeting", "Meeting with Google Cloud Associate tomorrow", "mail://1", "hyper")
    hits = idx.search("Google Cloud Associate")
    assert hits and hits[0].source == "mail"


def test_executor_local_search_tool(tmp_path):
    from eliot_harness.executor import Executor
    from eliot_harness.local_index import LocalIndex
    from eliot_harness.schema import Action
    idx = LocalIndex(tmp_path / "idx.sqlite3")
    idx.upsert("files", "budget.txt", "Q3 budget spreadsheet", "/tmp/budget.txt", "high")
    result = Executor(local_index=idx).execute(Action("local_search", {"query": "Q3 budget", "limit": 3}))
    assert "budget" in result.output.lower()


def test_system_control_dry_run():
    from eliot_harness.connectors.system_control import SystemControlConnector
    assert "DRY RUN" in SystemControlConnector().set_volume(25).text


def test_model_parse_action_structured():
    client = EliotModelClient()
    msg = {"tool_calls": [{"function": {"name": "open_app", "arguments": '{"name":"Notes"}'}}]}
    assert client._parse_action(msg).args["name"] == "Notes"


def test_model_repairs_natural_final_answer():
    client = EliotModelClient()
    action = client._parse_action({"content": "Yes, a Notes window is visible."})
    assert action and action.name == "done" and "Notes" in action.args["summary"]


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


def test_file_approval_times_out(tmp_path):
    from eliot_harness.approval import FileApproval
    from eliot_harness.guard import classify
    from eliot_harness.schema import Action
    action = Action("run_shell", {"cmd": "rm /tmp/x"})
    decision = FileApproval(tmp_path, timeout_s=0).approve(action, classify(action.__dict__))
    assert not decision.approved and "timed out" in decision.reason


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


def test_executor_applies_note_write_permission():
    from eliot_harness.executor import Executor
    from eliot_harness.permissions import PermissionState, Source
    ex = Executor(permissions=PermissionState(write_sources={Source.NOTES, Source.REMINDERS}))
    assert ex.notes.can_write
    assert ex.reminders.can_write


def test_native_helper_scripts_exist():
    assert Path("scripts/eventkit_bridge.swift").exists()
    assert Path("scripts/ocr_image.swift").exists()


def test_mail_messages_do_not_send_by_default():
    from eliot_harness.connectors.mail import MailConnector
    from eliot_harness.connectors.messages import MessagesConnector
    assert "Draft email" in MailConnector().draft_email("a@example.test", "S", "B").text
    assert "SEND REQUIRES APPROVAL" in MailConnector().send_email("a@example.test", "S", "B").text
    assert "Draft message" in MessagesConnector().draft_message("Alex", "Hi").text
    assert "SEND REQUIRES APPROVAL" in MessagesConnector().send_message("Alex", "Hi").text


def test_maps_music_podcasts_dry_runs():
    from eliot_harness.connectors.maps import MapsConnector
    from eliot_harness.connectors.music import MusicConnector
    from eliot_harness.connectors.podcasts import PodcastsConnector
    assert "maps.apple.com" in MapsConnector().open_directions("San Francisco").text
    assert "DRY RUN" in MusicConnector().play_query("Blue in Green").text
    assert "podcasts.apple.com" in PodcastsConnector().open_search("Waveform").text


def test_sensitive_indexers_fail_safely():
    from eliot_harness.connectors.messages_index import MessagesIndexConnector
    from eliot_harness.connectors.photos import PhotosConnector
    m = MessagesIndexConnector(db_path="/definitely/missing/chat.db")
    m.can_read = True
    assert "unavailable" in m.recent_messages()[0].text.lower()
    p = PhotosConnector()
    assert p.read_context("photos") == []


def test_photos_connector_requires_enable_for_export(tmp_path):
    from eliot_harness.connectors.photos import PhotosConnector
    c = PhotosConnector()
    assert c.export_selection(tmp_path) == []


def test_vision_client_unconfigured(tmp_path):
    from eliot_harness.vision import ImageUnderstandingClient
    img = tmp_path / "x.jpg"
    img.write_bytes(b"not really an image")
    assert ImageUnderstandingClient(base_url="", model="").describe(img) == ""


def test_vision_full_foundry_url():
    from eliot_harness.vision import ImageUnderstandingClient
    url = "https://example.services.ai.azure.com/openai/v1/chat/completions"
    assert ImageUnderstandingClient(base_url=url, model="grok-4.3").chat_url() == url


def test_model_full_foundry_url():
    from eliot_harness.model import EliotModelClient
    url = "https://example.services.ai.azure.com/openai/v1/chat/completions"
    assert EliotModelClient(base_url=url, model="grok-4.3").chat_url() == url


def test_reference_resolver_latest_draft():
    store = ReferenceStore()
    store.add("draft", "email draft", "hello")
    assert store.resolve_text("send it").value == "hello"


def test_source_manifests_cover_core_sources():
    for name in ["hypersave", "files", "calendar", "contacts", "notes", "reminders", "mail", "messages", "maps", "music", "podcasts", "safari", "photos", "web"]:
        assert name in MANIFESTS
    assert "Calendar" in manifest_table()


def test_files_connector_path_boundary(tmp_path):
    from eliot_harness.connectors.files import FilesConnector
    root = tmp_path / "root"
    root.mkdir()
    good = root / "a.txt"
    good.write_text("hello")
    bad = tmp_path / "root2.txt"
    bad.write_text("bad")
    c = FilesConnector([str(root)])
    assert c.is_allowed(str(good))
    assert not c.is_allowed(str(bad))
    assert "hello" in c.read_file(str(good)).text


def test_registry_applies_config():
    from eliot_harness.config import HarnessConfig
    from eliot_harness.connectors.registry import build_registry
    cfg = HarnessConfig()
    cfg.sources["files"].read = True
    reg = build_registry(cfg, None, ["/tmp"])
    assert reg.get("files").can_read


def test_session_store_roundtrip(tmp_path):
    from eliot_harness.session import SessionState
    from eliot_harness.session_store import save_session, load_session
    s = SessionState(task="hello")
    s.references.add("draft", "draft", "body")
    p = save_session(s, tmp_path)
    loaded = load_session(p.stem, tmp_path)
    assert loaded and loaded.references.latest("draft").value == "body"


def test_visual_connector_disabled():
    from eliot_harness.connectors.visual import VisualConnector
    c = VisualConnector()
    assert "disabled" in c.capture_interactive().text


def test_indexer_unsupported_source():
    from eliot_harness.indexer import unsupported_source
    item = unsupported_source("unknown")
    assert item.source == "unknown" and "not implemented" in item.content
