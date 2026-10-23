"""Codex-only sync behavior, plus opt-in native host discovery."""

from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class CodexSyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.home = self.root / "home with spaces"
        self.home.mkdir()
        self.repo = self.root / "repo with spaces"
        for directory in ("scripts", "shared", "mcp"):
            (self.repo / directory).mkdir(parents=True)
        for name in ("sync-codex.sh", "generate.py", "agentic_lib.py"):
            shutil.copy2(REPO_ROOT / "scripts" / name, self.repo / "scripts" / name)
        for name in ("conventions.md", "codex-wrapper.md"):
            shutil.copy2(REPO_ROOT / "shared" / name, self.repo / "shared" / name)
        shutil.copy2(REPO_ROOT / "mcp" / "servers.json", self.repo / "mcp")
        for name in ("valid", ".trash/hidden", "synced/imported"):
            skill = self.repo / "claude" / "skills" / name
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                f"---\nname: {Path(name).name}\ndescription: A test skill.\n---\nTest.\n")
        self.env = dict(os.environ, HOME=str(self.home), PYTHONDONTWRITEBYTECODE="1")
        self.env.pop("CODEX_HOME", None)

    def sync(self, *args, check=True):
        return subprocess.run(
            ["bash", str(self.repo / "scripts" / "sync-codex.sh"), *args],
            env=self.env, cwd=self.repo, check=check, capture_output=True, text=True)

    def test_filters_containers_and_is_idempotent_without_other_client_writes(self):
        self.sync()
        skills = self.home / ".agents" / "skills"
        self.assertEqual([p.name for p in skills.iterdir()], ["valid"])
        self.assertEqual((skills / "valid").resolve(),
                         self.repo / "claude" / "skills" / "valid")
        config = self.home / ".codex" / "config.toml"
        before = config.read_bytes()
        result = self.sync()
        self.assertEqual(config.read_bytes(), before)
        self.assertIn("already linked: 1", result.stdout)
        self.assertIn("no changes", result.stdout)
        self.assertFalse((self.home / ".claude").exists())
        self.assertFalse((self.home / ".claude.json").exists())
        self.assertFalse((self.home / "Library").exists())

    def test_codex_home_changes_configs_but_not_skill_location(self):
        codex_dir = self.root / "custom codex"
        self.env["CODEX_HOME"] = str(codex_dir)
        self.sync("--servers", "devtools")
        self.assertTrue((codex_dir / "AGENTS.md").is_file())
        self.assertIn("[mcp_servers.devtools]", (codex_dir / "config.toml").read_text())
        self.assertFalse((self.home / ".codex").exists())
        self.assertTrue((self.home / ".agents" / "skills" / "valid").is_symlink())

    def test_requested_servers_stay_disabled_after_repeated_sync(self):
        self.sync()
        self.sync()
        text = (self.home / ".codex" / "config.toml").read_text()
        self.assertNotIn("awesome-copilot", text)
        for name in ("github", "terraform", "transit"):
            table = text.split(f"[mcp_servers.{name}]\n", 1)[1].split("\n[", 1)[0]
            self.assertIn("enabled = false", table)

    def test_preserves_markerless_instructions_and_foreign_dangling_link(self):
        agents = self.home / ".codex" / "AGENTS.md"
        agents.parent.mkdir()
        agents.write_text("My instructions\n")
        target = self.home / ".agents" / "skills" / "valid"
        target.parent.mkdir(parents=True)
        target.symlink_to(self.root / "foreign-missing-skill")
        result = self.sync()
        self.assertEqual(agents.read_text(), "My instructions\n")
        self.assertEqual(os.readlink(target), str(self.root / "foreign-missing-skill"))
        self.assertIn("skipped conflicts: 1", result.stdout)
        self.assertIn("hand-written, skipped", result.stdout)

    def test_invalid_arguments_do_not_write_files(self):
        self.assertNotEqual(self.sync("--servers", "missing", check=False).returncode, 0)
        self.assertEqual(list(self.home.iterdir()), [])
        self.assertEqual(self.sync("--help").returncode, 0)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_removes_known_broken_legacy_link_and_its_old_backup(self):
        legacy = self.home / ".codex" / "skills"
        legacy.parent.mkdir()
        legacy.symlink_to("claude/skills")
        backup = legacy.with_name("skills.legacy-link")
        backup.symlink_to("claude/skills")
        self.sync()
        self.assertTrue(legacy.is_dir())
        self.assertFalse(legacy.is_symlink())
        self.assertFalse(backup.is_symlink())
        self.sync()
        self.assertFalse(backup.is_symlink())

    @unittest.skipUnless(os.environ.get("AGENTIC_CODEX_INTEGRATION") == "1"
                         and shutil.which("codex"), "run make test-codex for native discovery")
    def test_native_codex_discovers_the_linked_skill(self):
        self.sync()
        with NativeCodex(self.env) as client:
            result = client.request("skills/list", {
                "cwds": [str(self.repo)], "forceReload": True})
        entries = result["data"]
        self.assertTrue(entries)
        entry = entries[0]
        self.assertEqual(entry["errors"], [])
        discovered = {skill["name"] for skill in entry["skills"]
                      if str(self.repo / "claude" / "skills") in skill["path"]}
        self.assertEqual(discovered, {"valid"})


class NativeCodex:
    """Small protocol client: no model turn or external tool calls."""

    def __init__(self, env):
        self.env = env
        self.messages = queue.Queue()
        self.request_id = 0

    def __enter__(self):
        self.process = subprocess.Popen(
            ["codex", "app-server"], env=self.env, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        self.reader = threading.Thread(target=self.read_messages, daemon=True)
        self.reader.start()
        try:
            self.request("initialize", {"clientInfo": {
                "name": "agentic-sync-test", "version": "1.0"}})
            self.send({"method": "initialized"})
        except Exception:
            self.__exit__(None, None, None)
            raise
        return self

    def read_messages(self):
        for line in self.process.stdout:
            self.messages.put(json.loads(line))
        self.messages.put(None)

    def send(self, message):
        self.process.stdin.write(json.dumps(message) + "\n")
        self.process.stdin.flush()

    def request(self, method, params):
        self.request_id += 1
        self.send({"id": self.request_id, "method": method, "params": params})
        while True:
            response = self.messages.get(timeout=45)
            if response is None:
                raise RuntimeError("Codex app server exited before responding")
            if response.get("id") == self.request_id:
                if "error" in response:
                    raise RuntimeError(response["error"])
                return response["result"]

    def __exit__(self, *_):
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
        self.reader.join(timeout=5)
        self.process.stdin.close()
        self.process.stdout.close()
