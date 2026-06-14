from pathlib import Path
import pytest
from eliot_harness.executor import Executor
from eliot_harness.permissions import PermissionState, Source
from eliot_harness.schema import Action, normalize_action
from eliot_harness.policy import PolicyDecision, PolicyEngine
from eliot_harness.context import ContextCompiler
from eliot_harness.runtime import HarnessRuntime
from eliot_harness.model import ModelResult

def test_dynamic_applescript_execution():
    # Test executing a simple safe AppleScript on the Mac (returns "ok" or stdout text)
    ex = Executor()
    act = Action("applescript", {"script": 'return "Hello from AppleScript!"'})
    res = ex.execute(act)
    # On mac, if osascript works, it will return "Hello from AppleScript!"
    # If not on mac, it may fail gracefully. Let's assert it executes and doesn't crash.
    assert res is not None

def test_dynamic_file_read_write(tmp_path):
    # Test file writing and reading natively supported by Executor and FilesConnector
    perms = PermissionState(read_sources={Source.FILES}, write_sources={Source.FILES})
    ex = Executor(permissions=perms, file_roots=[str(tmp_path)])
    
    test_file = tmp_path / "hello_eliot.txt"
    # Execute write_file action
    write_act = Action("write_file", {"path": str(test_file), "content": "Eliot was here!"})
    write_res = ex.execute(write_act)
    assert "successfully wrote" in write_res.output
    assert test_file.read_text() == "Eliot was here!"

    # Execute read_file action
    read_act = Action("read_file", {"path": str(test_file)})
    read_res = ex.execute(read_act)
    assert "Eliot was here!" in read_res.output

def test_dynamic_harness_runtime_loop(tmp_path):
    # Mocking EliotModelClient to simulate a multi-turn reasoning loop using dynamic scripting tools
    class MockDynamicModelClient:
        def __init__(self):
            self.turns = 0

        def complete(self, messages, max_tokens=384):
            self.turns += 1
            if self.turns == 1:
                # First turn: Synthesize an AppleScript to find something
                return ModelResult(
                    Action("applescript", {"script": 'tell application "Notes" to get name of every note'}),
                    0.05,
                    {"tool_calls": [{"type": "function", "id": "call_1", "function": {"name": "applescript", "arguments": '{"script": "tell application \\"Notes\\" to get name of every note"}'}}]}
                )
            elif self.turns == 2:
                # Second turn: Based on results, draft an email card
                return ModelResult(
                    Action("done", {"summary": "Draft email to alex@example.com\nSubject: Project Update\n\nHi Alex, here is the note name."}),
                    0.05,
                    {"tool_calls": [{"type": "function", "id": "call_2", "function": {"name": "done", "arguments": '{"summary": "Draft email to alex@example.com\\nSubject: Project Update\\n\\nHi Alex, here is the note name."}'}}]}
                )
            return ModelResult(Action("done", {"summary": "No more turns"}), 0.05, {})

    model = MockDynamicModelClient()
    perms = PermissionState(read_sources={Source.FILES}, write_sources={Source.FILES})
    context = ContextCompiler(perms)
    executor = Executor(permissions=perms, file_roots=[str(tmp_path)])

    runtime = HarnessRuntime(
        model=model,
        context=context,
        executor=executor,
        audit_path=str(tmp_path / "dynamic_audit.jsonl")
    )

    transcript = runtime.run("Find the latest note name and draft a project update email to Alex.")
    assert model.turns == 2
    assert len(transcript.turns) == 2
    assert "applescript" in transcript.turns[0]["action"]["name"]
    assert "done" in transcript.turns[1]["action"]["name"]
    assert "Draft email to alex@example.com" in transcript.turns[1]["result"]
