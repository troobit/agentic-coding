"""Tests for scripts/generate.py and scripts/agentic_lib.py.

Golden-fixture tests only; no test ever touches real user files —
every target path is injected into a temp directory.
"""

import sys
import tempfile
import unittest
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TESTS_DIR.parent
FIXTURES = TESTS_DIR / "fixtures"

sys.path.insert(0, str(REPO_ROOT / "scripts"))

import agentic_lib  # noqa: E402


class ConventionsAssemblyTests(unittest.TestCase):
    """Task 1: conventions assembly from shared fragments."""

    def test_claude_md_matches_golden(self):
        block = agentic_lib.build_claude_block(FIXTURES / "shared")
        text = agentic_lib.managed_file_text(block)
        golden = (FIXTURES / "golden" / "CLAUDE.md").read_text()
        self.assertEqual(text, golden)

    def test_copilot_instructions_match_golden(self):
        block = agentic_lib.build_copilot_block(FIXTURES / "shared")
        text = agentic_lib.managed_file_text(block)
        golden = (FIXTURES / "golden" / "copilot-instructions.md").read_text()
        self.assertEqual(text, golden)

    def test_copilot_output_contains_no_claude_wrapper_content(self):
        block = agentic_lib.build_copilot_block(FIXTURES / "shared")
        wrapper = (FIXTURES / "shared" / "claude-wrapper.md").read_text()
        for line in wrapper.strip().splitlines():
            if line.strip():
                self.assertNotIn(line, block)

    def test_real_copilot_output_has_no_claude_isms(self):
        """The repo's actual shared/ fragments must keep the Copilot output
        free of Claude-only mechanisms and Claude-tree paths (Req 3.3)."""
        block = agentic_lib.build_copilot_block(REPO_ROOT / "shared")
        for forbidden in (
            "AskUserQuestion",
            "rules/references",
            ".claude/scripts",
            ".claude/skills",
            "explain-like",
        ):
            self.assertNotIn(forbidden, block, f"Copilot output leaks {forbidden!r}")

    def test_real_outputs_share_conventions_verbatim(self):
        conventions = (REPO_ROOT / "shared" / "conventions.md").read_text().strip()
        claude_block = agentic_lib.build_claude_block(REPO_ROOT / "shared")
        copilot_block = agentic_lib.build_copilot_block(REPO_ROOT / "shared")
        self.assertIn(conventions, claude_block)
        self.assertIn(conventions, copilot_block)


class ManagedBlockWriterTests(unittest.TestCase):
    """Task 1: managed-block semantics (Decision 15)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def test_missing_file_is_created_with_markers(self):
        target = self.dir / "out.md"
        report = []
        changed = agentic_lib.write_managed(target, "hello", report)
        self.assertTrue(changed)
        text = target.read_text()
        self.assertTrue(text.startswith(agentic_lib.BEGIN_MARKER))
        self.assertIn("hello", text)
        self.assertIn(agentic_lib.END_MARKER, text)

    def test_content_outside_markers_survives_regeneration(self):
        """Claude memory appends after the block must survive (Decision 15)."""
        target = self.dir / "CLAUDE.md"
        agentic_lib.write_managed(target, "generated v1", [])
        memory = "\n# Memories\n\n- remember the thing\n"
        target.write_text(target.read_text() + memory)
        agentic_lib.write_managed(target, "generated v2", [])
        text = target.read_text()
        self.assertIn("generated v2", text)
        self.assertNotIn("generated v1", text)
        self.assertIn("- remember the thing", text)

    def test_head_content_before_markers_survives(self):
        target = self.dir / "out.md"
        agentic_lib.write_managed(target, "body", [])
        target.write_text("hand-written header\n" + target.read_text())
        agentic_lib.write_managed(target, "body2", [])
        text = target.read_text()
        self.assertTrue(text.startswith("hand-written header\n"))
        self.assertIn("body2", text)

    def test_markerless_existing_file_is_skipped_and_reported(self):
        target = self.dir / "out.md"
        target.write_text("hand-written, no markers\n")
        report = []
        changed = agentic_lib.write_managed(target, "generated", report)
        self.assertFalse(changed)
        self.assertEqual(target.read_text(), "hand-written, no markers\n")
        self.assertTrue(any("out.md" in r and "marker" in r.lower() for r in report))

    def test_rewrite_with_same_content_reports_no_change(self):
        target = self.dir / "out.md"
        agentic_lib.write_managed(target, "same", [])
        changed = agentic_lib.write_managed(target, "same", [])
        self.assertFalse(changed)


def _load_fixture_servers():
    return agentic_lib.load_servers(FIXTURES / "servers.json")


def _golden_json(name):
    import json
    return json.loads((FIXTURES / "golden" / name).read_text())


class McpEmissionTests(unittest.TestCase):
    """Task 4: per-target MCP config shapes from a fixture servers.json."""

    def setUp(self):
        self.defs = _load_fixture_servers()

    def test_repo_mcp_matches_golden(self):
        got = agentic_lib.emit_repo_mcp(self.defs, None)
        self.assertEqual(got, _golden_json("repo-mcp.json"))

    def test_vscode_mcp_matches_golden(self):
        got = agentic_lib.emit_vscode_mcp(self.defs, None)
        self.assertEqual(got, _golden_json("vscode-mcp.json"))

    def test_cloud_config_matches_golden(self):
        got = agentic_lib.emit_cloud_config(self.defs, None)
        self.assertEqual(got, _golden_json("cloud-mcp.json"))

    def test_cloud_json_is_paste_ready_string(self):
        import json
        text = agentic_lib.emit_cloud_json(self.defs, None)
        self.assertEqual(json.loads(text), _golden_json("cloud-mcp.json"))

    def test_subset_selection(self):
        """Req 4.4: per-repo generation supports a subset of the set."""
        got = agentic_lib.emit_repo_mcp(self.defs, ["alpha"])
        self.assertEqual(sorted(got["mcpServers"]), ["alpha"])

    def test_unknown_server_in_subset_errors_with_canonical_names(self):
        with self.assertRaises(agentic_lib.GenerationError) as ctx:
            agentic_lib.emit_repo_mcp(self.defs, ["nope"])
        self.assertIn("nope", str(ctx.exception))
        self.assertIn("alpha", str(ctx.exception))

    def test_surface_filtering(self):
        """zulu is vscode-only; claude and cloud shapes must exclude it."""
        self.assertNotIn("zulu", agentic_lib.emit_repo_mcp(self.defs, None)["mcpServers"])
        self.assertNotIn("zulu", agentic_lib.emit_cloud_config(self.defs, None)["mcpServers"])
        self.assertIn("zulu", agentic_lib.emit_vscode_mcp(self.defs, None)["servers"])

    def test_no_secret_values_in_any_output(self):
        """Req 4.3: outputs reference secrets, never contain values."""
        import json
        for emitted in (
            agentic_lib.emit_repo_mcp(self.defs, None),
            agentic_lib.emit_vscode_mcp(self.defs, None),
            agentic_lib.emit_cloud_config(self.defs, None),
        ):
            text = json.dumps(emitted)
            self.assertNotIn("some-secret-value", text)

    def test_unmappable_secret_aborts_naming_server_and_target(self):
        broken = agentic_lib.load_servers(FIXTURES / "servers-broken.json")
        for emitter, target in (
            (agentic_lib.emit_repo_mcp, "claude"),
            (agentic_lib.emit_vscode_mcp, "vscode"),
            (agentic_lib.emit_cloud_config, "cloud"),
        ):
            with self.assertRaises(agentic_lib.GenerationError) as ctx:
                emitter(broken, None)
            msg = str(ctx.exception)
            self.assertIn("broken", msg, f"target {target}: server not named")
            self.assertIn(target, msg, f"target {target}: target not named")


class McpMergeTests(unittest.TestCase):
    """Task 4: managed-merge behavior against existing target files."""

    def setUp(self):
        self.defs = _load_fixture_servers()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def test_repo_generation_preserves_non_canonical_and_converges(self):
        import json
        repo = self.dir / "repo"
        repo.mkdir()
        existing = {
            "mcpServers": {
                "custom": {"type": "stdio", "command": "my-own-thing"},
                "alpha": {"type": "stdio", "command": "/Users/ronan/stale/alpha"},
            }
        }
        (repo / ".mcp.json").write_text(json.dumps(existing))
        report = []
        agentic_lib.generate_repo_configs(repo, self.defs, None, report)
        result = json.loads((repo / ".mcp.json").read_text())
        self.assertEqual(result["mcpServers"]["custom"],
                         existing["mcpServers"]["custom"])
        self.assertEqual(result["mcpServers"]["alpha"],
                         _golden_json("repo-mcp.json")["mcpServers"]["alpha"])
        self.assertTrue(any("custom" in r for r in report),
                        "preserved non-canonical entry must be reported")
        vs = json.loads((repo / ".vscode" / "mcp.json").read_text())
        self.assertEqual(vs, _golden_json("vscode-mcp.json"))

    def test_repo_generation_is_idempotent(self):
        repo = self.dir / "repo"
        repo.mkdir()
        agentic_lib.generate_repo_configs(repo, self.defs, None, [])
        report = []
        agentic_lib.generate_repo_configs(repo, self.defs, None, report)
        self.assertEqual([r for r in report if "preserved" not in r], [])

    def test_invalid_target_json_backed_up_and_regenerated(self):
        import json
        repo = self.dir / "repo"
        (repo / ".vscode").mkdir(parents=True)
        bad = "{ not json !!!"
        (repo / ".vscode" / "mcp.json").write_text(bad)
        report = []
        agentic_lib.generate_repo_configs(repo, self.defs, None, report)
        result = json.loads((repo / ".vscode" / "mcp.json").read_text())
        self.assertEqual(result, _golden_json("vscode-mcp.json"))
        baks = list((repo / ".vscode").glob("mcp.json.bak-*"))
        self.assertEqual(len(baks), 1)
        self.assertEqual(baks[0].read_text(), bad)
        self.assertTrue(
            any("non-canonical" in r and "backup" in r for r in report),
            "report must warn that non-canonical entries may be in the backup")

    def test_claude_user_config_merge_preserves_unrelated_keys(self):
        import json
        cfg = self.dir / "claude.json"
        existing = {
            "theme": "dark",
            "projects": {"/some/path": {"history": [1, 2, 3]}},
            "mcpServers": {
                "custom": {"type": "stdio", "command": "keep-me"},
                "alpha": {"type": "stdio", "command": "/Users/ronan/go/bin/alpha"},
            },
        }
        cfg.write_text(json.dumps(existing))
        report = []
        agentic_lib.update_claude_user_config(cfg, self.defs, None, report,
                                              use_cli=False)
        result = json.loads(cfg.read_text())
        self.assertEqual(result["theme"], "dark")
        self.assertEqual(result["projects"], existing["projects"])
        self.assertEqual(result["mcpServers"]["custom"],
                         existing["mcpServers"]["custom"])
        golden = _golden_json("repo-mcp.json")["mcpServers"]
        for name, spec in golden.items():
            self.assertEqual(result["mcpServers"][name], spec)
        self.assertTrue(any("custom" in r for r in report))

    def test_claude_cli_commands_use_user_scope(self):
        cmds = agentic_lib.build_claude_cli_commands(self.defs, None)
        self.assertTrue(cmds)
        for cmd in cmds:
            self.assertEqual(cmd[:3], ["claude", "mcp", "add-json"])
            self.assertIn("--scope", cmd)
            self.assertEqual(cmd[cmd.index("--scope") + 1], "user")


class VscodeSettingsMergeTests(unittest.TestCase):
    """Task 7: VS Code user settings.json merge (generate.py --user)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.settings = self.dir / "settings.json"
        self.repo_root = self.dir / "agentic-coding"

    def test_merge_preserves_unrelated_keys_and_seeds_managed_ones(self):
        import json
        existing = {
            "editor.fontSize": 13,
            "workbench.colorTheme": "Default Dark+",
            "chat.instructionsFilesLocations": {"/somewhere/else": True},
        }
        self.settings.write_text(json.dumps(existing))
        report = []
        agentic_lib.merge_vscode_settings(self.settings, self.repo_root, report)
        result = json.loads(self.settings.read_text())
        # unrelated keys untouched
        self.assertEqual(result["editor.fontSize"], 13)
        self.assertEqual(result["workbench.colorTheme"], "Default Dark+")
        # existing instructions locations preserved, ours added
        locations = result["chat.instructionsFilesLocations"]
        self.assertTrue(locations["/somewhere/else"])
        ours = str(self.repo_root / "copilot" / "instructions")
        self.assertTrue(locations[ours])
        # localml provider seeded
        models = result["github.copilot.chat.customOAIModels"]
        entry = models[agentic_lib.LOCALML_PLACEHOLDER_MODEL_ID]
        self.assertEqual(entry["url"], "http://127.0.0.1:8080/v1")

    def test_use_claude_md_file_is_never_enabled(self):
        import json
        self.settings.write_text("{}")
        agentic_lib.merge_vscode_settings(self.settings, self.repo_root, [])
        result = json.loads(self.settings.read_text())
        self.assertNotEqual(result.get("chat.useClaudeMdFile"), True)

    def test_missing_settings_file_is_created(self):
        import json
        report = []
        agentic_lib.merge_vscode_settings(self.settings, self.repo_root, report)
        result = json.loads(self.settings.read_text())
        self.assertIn("chat.instructionsFilesLocations", result)
        self.assertIn("github.copilot.chat.customOAIModels", result)

    def test_jsonc_settings_backed_up_and_never_clobbered(self):
        jsonc = ('{\n'
                 '  // my carefully tuned settings\n'
                 '  "editor.fontSize": 13,\n'
                 '}\n')
        self.settings.write_text(jsonc)
        report = []
        changed = agentic_lib.merge_vscode_settings(self.settings,
                                                    self.repo_root, report)
        self.assertFalse(changed)
        self.assertEqual(self.settings.read_text(), jsonc,
                         "unparseable settings.json must never be clobbered")
        baks = list(self.dir.glob("settings.json.bak-*"))
        self.assertEqual(len(baks), 1)
        self.assertEqual(baks[0].read_text(), jsonc)
        self.assertTrue(any("settings.json" in r for r in report))

    def test_merge_is_idempotent(self):
        agentic_lib.merge_vscode_settings(self.settings, self.repo_root, [])
        before = self.settings.read_text()
        report = []
        changed = agentic_lib.merge_vscode_settings(self.settings,
                                                    self.repo_root, report)
        self.assertFalse(changed)
        self.assertEqual(self.settings.read_text(), before)
        self.assertEqual(report, [])

    def test_existing_model_entry_is_converged(self):
        import json
        self.settings.write_text(json.dumps({
            "github.copilot.chat.customOAIModels": {
                "my-other-model": {"url": "http://example/v1"},
                agentic_lib.LOCALML_PLACEHOLDER_MODEL_ID: {"url": "http://stale:9999/v1"},
            }
        }))
        agentic_lib.merge_vscode_settings(self.settings, self.repo_root, [])
        result = json.loads(self.settings.read_text())
        models = result["github.copilot.chat.customOAIModels"]
        self.assertEqual(models["my-other-model"], {"url": "http://example/v1"})
        self.assertEqual(
            models[agentic_lib.LOCALML_PLACEHOLDER_MODEL_ID]["url"],
            "http://127.0.0.1:8080/v1")


class UserConfigWiringTests(unittest.TestCase):
    """Task 8: generate_user_configs writes all three injected targets."""

    def test_user_generation_with_injected_paths(self):
        import json
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            claude_cfg = d / "claude.json"
            vs_mcp = d / "User" / "mcp.json"
            vs_settings = d / "User" / "settings.json"
            defs = _load_fixture_servers()
            report = []
            agentic_lib.generate_user_configs(
                defs, None, report, repo_root=d / "repo",
                claude_config_path=claude_cfg,
                vscode_mcp_path=vs_mcp,
                vscode_settings_path=vs_settings,
                use_cli=False)
            self.assertEqual(json.loads(claude_cfg.read_text()),
                             _golden_json("repo-mcp.json"))
            self.assertEqual(json.loads(vs_mcp.read_text()),
                             _golden_json("vscode-mcp.json"))
            settings = json.loads(vs_settings.read_text())
            self.assertIn("github.copilot.chat.customOAIModels", settings)
            self.assertNotEqual(settings.get("chat.useClaudeMdFile"), True)


class CanonicalServersFileTests(unittest.TestCase):
    """Task 5: sanity checks on the real mcp/servers.json."""

    def test_canonical_set_and_portability(self):
        defs = agentic_lib.load_servers(REPO_ROOT / "mcp" / "servers.json")
        self.assertEqual(
            sorted(defs),
            ["awesome-copilot", "azure", "devtools", "github",
             "svelte", "terraform", "transit"])
        for name, spec in defs.items():
            transport = spec["transport"]
            self.assertIn(transport["type"], ("stdio", "http"))
            self.assertIn("surfaces", spec)
            self.assertIn("default_for", spec)
            self.assertIn("secrets", spec)
            cmd = transport.get("command", "")
            self.assertFalse(cmd.startswith("/"),
                             f"{name}: command must be PATH-resolved, not absolute")
            self.assertNotIn("/Users/", str(spec))


if __name__ == "__main__":
    unittest.main()
