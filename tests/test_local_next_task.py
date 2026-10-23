"""Exercise the loop with real rune ledgers and a disposable fake Codex CLI."""

import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import local_next_task as runner


FAKE_CODEX = r'''
import json
import os
from pathlib import Path
import subprocess
import sys
import time

prompt = sys.stdin.read()
calls = Path(os.environ["TEST_CALLS"])
with calls.open("a") as output:
    output.write(json.dumps({"args": sys.argv[1:], "prompt": prompt, "cwd": os.getcwd()}) + "\n")
mode = os.environ.get("TEST_MODE", "progress")
final = Path(sys.argv[sys.argv.index("--output-last-message") + 1])
if mode == "failure":
    sys.exit(7)
if mode == "event-error":
    print(json.dumps({"type": "turn.failed", "error": {"message": "model error"}}))
elif mode == "timeout":
    time.sleep(10)
elif mode == "halt-file":
    Path(".orbit").mkdir(exist_ok=True)
    Path(".orbit/halt").write_text("Need approval\n")
elif mode == "halt-output":
    final.write_text("ORBIT-HALT: Need approval\n")
elif mode == "progress":
    tasks = os.environ["TEST_TASKS"]
    data = json.loads(subprocess.check_output(["rune", "next", tasks, "--format", "json"], text=True))
    subprocess.run(["rune", "complete", tasks, data["next_task"]["id"]], check=True, capture_output=True)
    final.write_text("Completed selected task\n")
'''


@unittest.skipUnless(shutil.which("rune"), "rune CLI required")
class LoopTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="local-next-task-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.tasks = self.root / "specs" / "example with spaces" / "tasks.md"
        self.tasks.parent.mkdir(parents=True)
        (self.tasks.parent / "design.md").write_text("# Test design\n")
        subprocess.run([
            "rune", "create", str(self.tasks), "--title", "Test tasks",
            "--reference", "specs/example with spaces/design.md",
        ], check=True, capture_output=True, cwd=self.root)
        self.rune("batch", "--input", json.dumps({"operations": [
            {"type": "add", "title": "First task"},
            {"type": "add", "title": "Second task", "blocked_by": ["1"]},
        ]}))
        binary = self.root / "bin"
        binary.mkdir()
        fake = binary / "codex"
        fake.write_text(f"#!{sys.executable}\n" + FAKE_CODEX)
        fake.chmod(0o755)
        self.calls_file = self.root / "calls.jsonl"
        environment = {
            "PATH": str(binary) + os.pathsep + os.environ["PATH"],
            "TEST_TASKS": str(self.tasks), "TEST_CALLS": str(self.calls_file),
            "TEST_MODE": "progress",
        }
        self.environment = mock.patch.dict(os.environ, environment)
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def rune(self, command, *args):
        return subprocess.run(
            ["rune", command, str(self.tasks), *args], check=True,
            capture_output=True, text=True, cwd=self.root,
        )

    def run_loop(self, *args, mode="progress"):
        output, errors = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, TEST_MODE=mode), contextlib.redirect_stdout(output), contextlib.redirect_stderr(errors):
            code = runner.main([str(self.tasks), *args])
        return code, output.getvalue() + errors.getvalue()

    def calls(self):
        if not self.calls_file.exists():
            return []
        return [json.loads(line) for line in self.calls_file.read_text().splitlines()]

    def test_fresh_sessions_advance_until_complete(self):
        code, output = self.run_loop()
        self.assertEqual(code, 0, output)
        self.assertIn("All tasks complete", output)
        calls = self.calls()
        self.assertEqual(len(calls), 2)
        self.assertEqual(calls[0]["cwd"], str(self.root))
        for call in calls:
            self.assertIn("$next-task", call["prompt"])
            self.assertIn(str(self.tasks), call["prompt"])
            self.assertIn("design.md", call["prompt"])
            self.assertIn("--oss", call["args"])
            self.assertIn("--ignore-user-config", call["args"])
            self.assertEqual(call["args"][call["args"].index("--model") + 1], "8-bit")
            self.assertNotIn("resume", call["args"])
        self.assertEqual(len(list(self.tasks.parent.glob(".orbit/local-next-task/*/*.jsonl"))), 2)

    def test_complete_ledger_does_not_call_model(self):
        self.rune("complete", "1")
        self.rune("complete", "2")
        self.assertEqual(self.run_loop()[0], 0)
        self.assertEqual(self.calls(), [])

    def test_completed_external_dependency_does_not_block_phase(self):
        self.rune("add", "--title", "Third task", "--blocked-by", "1,2")
        self.rune("complete", "1")
        code, output = self.run_loop()
        self.assertEqual(code, 0, output)
        self.assertEqual(len(self.calls()), 2)

    def test_dry_run_is_read_only_and_shows_phase_fallback(self):
        original = self.tasks.read_bytes()
        code, output = self.run_loop("--dry-run", "--model", "another-local-model")
        self.assertEqual(code, 0, output)
        self.assertIn("another-local-model", output)
        self.assertIn('"tasks":', output)
        self.assertEqual(self.calls(), [])
        self.assertEqual(self.tasks.read_bytes(), original)
        self.assertFalse((self.tasks.parent / ".orbit").exists())

    def test_stop_gate_is_never_sent_to_model(self):
        self.rune("update", "1", "--title", "STOP — human approval needed")
        code, output = self.run_loop()
        self.assertEqual(code, 2, output)
        self.assertIn("requires human review", output)
        self.assertEqual(self.calls(), [])

    def test_stop_gate_in_subtask_is_never_sent_to_model(self):
        self.rune("add", "--title", "STOP — human approval needed", "--parent", "1")
        code, output = self.run_loop()
        self.assertEqual(code, 2, output)
        self.assertIn("requires human review", output)
        self.assertEqual(self.calls(), [])

    def test_ordinary_stop_word_is_not_a_gate(self):
        self.rune("update", "1", "--title", "Stop duplicate writes")
        self.assertEqual(self.run_loop("--dry-run")[0], 0)

    def test_blocked_phase_stops_without_model(self):
        self.rune("batch", "--input", json.dumps({"operations": [
            {"type": "remove", "id": "2"},
            {"type": "remove", "id": "1"},
            {"type": "add-phase", "phase": "Before"},
            {"type": "add", "title": "Blocked task", "phase": "Before"},
            {"type": "add-phase", "phase": "Later"},
            {"type": "add", "title": "Later dependency", "phase": "Later"},
            {"type": "update", "id": "1", "blocked_by": ["2"]},
        ]}))
        code, output = self.run_loop("--phase")
        self.assertEqual(code, 2, output)
        self.assertEqual(self.calls(), [])

    def test_existing_halt_file_is_preserved(self):
        halt = self.root / ".orbit" / "halt"
        halt.parent.mkdir()
        halt.write_text("Review previous iteration\n")
        code, output = self.run_loop()
        self.assertEqual(code, 2, output)
        self.assertIn("Review previous iteration", output)
        self.assertEqual(halt.read_text(), "Review previous iteration\n")
        self.assertEqual(self.calls(), [])

    def test_agent_failures_and_stalled_work_halt_after_one_call(self):
        for mode, reason in [
            ("failure", "status 7"), ("event-error", "reported an error"),
            ("no-progress", "No tasks completed"), ("halt-output", "Need approval"),
            ("halt-file", "Need approval"),
        ]:
            with self.subTest(mode=mode):
                before = len(self.calls())
                code, output = self.run_loop(mode=mode)
                self.assertEqual(code, 2, output)
                self.assertIn(reason, output)
                self.assertEqual(len(self.calls()), before + 1)

    def test_iteration_limit_can_resume_from_ledger(self):
        code, output = self.run_loop("--max-iterations", "1")
        self.assertEqual(code, 2, output)
        self.assertIn("iteration limit", output)
        self.assertEqual(len(self.calls()), 1)
        code, output = self.run_loop("--max-iterations", "1")
        self.assertEqual(code, 0, output)
        self.assertEqual(len(self.calls()), 2)

    def test_session_timeout_stops_the_iteration(self):
        code, output = self.run_loop("--timeout", "1", mode="timeout")
        self.assertEqual(code, 2, output)
        self.assertIn("timed out", output)
        self.assertEqual(len(self.calls()), 1)


if __name__ == "__main__":
    unittest.main()
