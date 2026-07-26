"""Drift-class fixture tests for scripts/align.py (spec: toolset-agnostic-starwave).

TDD red phase: scripts/align.py does not exist yet (task 11). Importing this
module MUST fail with a meaningful ImportError until it lands. These tests
define align's contract; task 11 implements against them without changing them.

Expected interface of scripts/align.py
--------------------------------------

    align.run(
        repo_path,                  # str | Path — target repo; must be a git checkout
        *,
        assume_yes=False,           # --yes: apply even on a first (manifest-inferring) run
        servers_json=None,          # canonical MCP definitions; default <agentic-coding>/mcp/servers.json
        stale_packs_json=None,      # default <agentic-coding>/scripts/stale-packs.json
        seed_root=None,             # root holding copilot/agents/prd.agent.md,
                                    #   copilot/instructions/copilot-instructions.md,
                                    #   claude/skills/prd/**; default: the agentic-coding repo root
    ) -> AlignReport

    class AlignReport:
        applied: bool        # False when the run only wrote the manifest and printed a plan
        changes: list[dict]  # one per (planned or applied) change; keys: "path" (repo-relative
                             #   posix path), "action" (str); optional "detail"
        warnings: list[str]
        skipped: list[str]   # repo-relative paths of markerless hand-written files left untouched
        preserved: list[str] # free-text reports of preserved non-canonical entries / unmatched
                             #   files; each mentions the entry name or file path

    class AlignError(Exception)   # raised e.g. for a non-git directory

Behavioural contract pinned here (from requirements 5.1-5.3, 6.1 and the design):

- Pipeline: JSON validity -> path portability -> MCP convergence -> stale-pack
  deletion -> cloud seeding with managed blocks.
- Managed files ONLY: .mcp.json, .vscode/mcp.json, .agentic.json,
  .github/copilot-instructions.md, .github/agents/prd.agent.md,
  .github/skills/prd/**, plus stale-pack files under .github/agents/.
- Path fixes produce portable forms: the bare command name when the basename is
  PATH-resolvable at fix time, otherwise ${HOME}/... in .mcp.json and
  ${env:HOME}/... in .vscode/mcp.json — never bare $HOME, never a literal
  substitution of the current username.
- Idempotence is the core invariant: an immediate second applying run reports
  zero changes on every drift fixture (warnings may repeat; changes may not).
- First run with no .agentic.json infers the manifest from default_for rules,
  writes ONLY the manifest, and reports the plan without applying anything.
- A seed-target file without <!-- agentic:begin/end --> markers is hand-written:
  reported, skipped, never overwritten. Files seeded by align (e.g.
  .github/agents/prd.agent.md) must not trigger the zero-stale-pack-matches
  warning on later runs.
- Nextup template step (PRD nextup-starwave-refinement, Align tooling reqs
  1-5): seed nextup.example.md verbatim when absent; otherwise converge only
  the machine zone (first <!-- LM --> marker down) to canonical, preserving
  the user zone byte-for-byte; ensure .gitignore carries a nextup.md entry;
  never create, modify, or delete the target's session-local nextup.md.

Run with: python3 -m unittest discover -s tests
"""

import getpass
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "align"
FIXTURE_REPOS = FIXTURES / "repos"
STALE_PACKS_JSON = REPO_ROOT / "scripts" / "stale-packs.json"

sys.path.insert(0, str(REPO_ROOT / "scripts"))

try:
    import align  # noqa: E402
except ImportError as exc:  # pragma: no cover - red phase until task 11 lands
    raise ImportError(
        "scripts/align.py does not exist yet. This is the deliberately-red TDD "
        "phase of spec toolset-agnostic-starwave: task 9 wrote these tests, "
        "task 11 implements align.py against the contract in this module's "
        "docstring. Once scripts/align.py lands, this suite must run green."
    ) from exc

import agentic_lib  # noqa: E402

MARKER_BEGIN = "<!-- agentic:begin -->"
MARKER_END = "<!-- agentic:end -->"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class AlignFixtureCase(unittest.TestCase):
    """Shared helpers: materialise fixture repos as real git checkouts."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="align-test-")
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)

    def make_repo(self, fixture_name, git=True):
        """Copy a fixture repo into a temp dir and (optionally) git-init it."""
        dest = self.tmp / fixture_name
        src = FIXTURE_REPOS / fixture_name
        if src.exists():
            shutil.copytree(src, dest)
        else:
            dest.mkdir(parents=True)
        if git:
            subprocess.run(
                ["git", "init", "-q"], cwd=dest, check=True, capture_output=True
            )
        return dest

    def run_align(self, repo, **kwargs):
        kwargs.setdefault("assume_yes", True)
        kwargs.setdefault("servers_json", FIXTURES / "servers.json")
        kwargs.setdefault("stale_packs_json", STALE_PACKS_JSON)
        kwargs.setdefault("seed_root", FIXTURES / "seed-root")
        return align.run(repo, **kwargs)

    def snapshot(self, repo):
        """Map of repo-relative posix path -> content hash, ignoring .git."""
        out = {}
        for path in Path(repo).rglob("*"):
            rel = path.relative_to(repo).as_posix()
            if rel == ".git" or rel.startswith(".git/"):
                continue
            if path.is_file():
                out[rel] = sha256(path)
        return out

    def change_paths(self, report):
        return {change["path"] for change in report.changes}

    def assert_portable_command(self, command, home_token):
        """Portable = bare PATH-resolved name, or exactly the per-target
        home-token form (${HOME}/... in .mcp.json, ${env:HOME}/... in
        .vscode/mcp.json). Bare $HOME is never acceptable."""
        self.assertNotIn(
            "/Users/", command,
            f"user-specific absolute path survived or was username-substituted: {command!r}",
        )
        if "/" in command:
            self.assertTrue(
                command.startswith(home_token + "/"),
                f"expected a {home_token}/... form: {command!r}",
            )

    def assert_no_user_paths(self, text, context):
        self.assertNotIn("/Users/ronan", text, f"stale user path survived in {context}")
        current_user_path = f"/Users/{getpass.getuser()}"
        self.assertNotIn(
            current_user_path, text,
            f"{context} contains {current_user_path!r}: path fixes must be portable, "
            "never a literal substitution of the current username",
        )
        self.assertNotIn(
            "$HOME/", text,
            f"{context} contains bare $HOME: fixes must use ${{HOME}} "
            "(.mcp.json) or ${{env:HOME}} (.vscode/mcp.json)",
        )


class StaleUserPathTest(AlignFixtureCase):
    """Drift class 1: /Users/ronan/... absolute paths in .mcp.json and .vscode/mcp.json."""

    HOME_TOKENS = {".mcp.json": "${HOME}", ".vscode/mcp.json": "${env:HOME}"}

    def test_single_run_fixes_all_stale_paths_portably(self):
        repo = self.make_repo("stale-user-path")
        # Deterministic PATH resolution: mcp-devtools resolves (-> bare
        # command name); run-local-mcp and everything else does not.
        with mock.patch.object(
            align, "_which", lambda name: name == "mcp-devtools"
        ):
            report = self.run_align(repo)

        for rel, home_token in self.HOME_TOKENS.items():
            with self.subTest(file=rel):
                text = (repo / rel).read_text()
                self.assert_no_user_paths(text, rel)
                data = json.loads(text)
                servers = data.get("mcpServers") or data.get("servers")
                self.assertIn(
                    "dev-tools", servers,
                    "non-canonical dev-tools entry must be preserved, not renamed/removed",
                )
                self.assertEqual(
                    servers["dev-tools"]["command"], "mcp-devtools",
                    "a PATH-resolvable basename must become the bare command name",
                )
                self.assert_portable_command(servers["dev-tools"]["command"], home_token)
                self.assertEqual(
                    servers["my-scripts"]["command"],
                    f"{home_token}/tools/run-local-mcp",
                    f"a non-resolvable path must become the {home_token} form",
                )
                self.assertEqual(
                    servers["my-scripts"]["args"],
                    ["--config", f"{home_token}/tools/mcp.conf"],
                    "argument paths get the home-token form too",
                )
                self.assertIn(rel, self.change_paths(report), "fix must be reported per file")

    def test_unmanaged_files_never_touched(self):
        repo = self.make_repo("stale-user-path")
        before = sha256(repo / "README.md")
        report = self.run_align(repo)
        self.assertEqual(
            sha256(repo / "README.md"), before,
            "README.md is not a managed file; align must not touch it",
        )
        self.assertNotIn("README.md", self.change_paths(report))

    def test_cloud_assets_false_seeds_nothing(self):
        repo = self.make_repo("stale-user-path")
        self.run_align(repo)
        self.assertFalse(
            (repo / ".github").exists(),
            "cloud_assets is false: align must not seed .github/",
        )


class InvalidJsonTest(AlignFixtureCase):
    """Drift class 2: unparseable managed config (real sanarte breakage:
    a server keyed "mcpServers" plus trailing commas)."""

    def test_invalid_file_backed_up_and_regenerated(self):
        repo = self.make_repo("invalid-json")
        report = self.run_align(repo)

        # Live file is valid again and contains the manifest servers.
        data = json.loads((repo / ".vscode/mcp.json").read_text())
        server_names = set(data.get("servers", {}))
        self.assertIn("devtools", server_names)
        self.assertIn("svelte", server_names)
        self.assertNotIn(
            "mcpServers", server_names,
            "the bogus server keyed 'mcpServers' must not be carried into the regenerated file",
        )

        # Original bytes live on in a .bak alongside.
        backups = [
            p for p in (repo / ".vscode").iterdir() if ".bak" in p.name and p.is_file()
        ]
        self.assertTrue(backups, "invalid JSON must be backed up alongside as .bak-<date>")
        self.assertTrue(
            any("azure" in p.read_text() for p in backups),
            "backup must preserve the original (invalid) content",
        )

        # The report warns that non-canonical entries may remain only in the .bak.
        self.assertTrue(
            any("bak" in w.lower() and "non-canonical" in w.lower() for w in report.warnings),
            f"expected a non-canonical-entries-in-.bak warning, got: {report.warnings!r}",
        )
        self.assertIn(".vscode/mcp.json", self.change_paths(report))


class NonDictRootTest(AlignFixtureCase):
    """Drift class 2b: parseable JSON whose root is not an object (e.g. a
    top-level array) must take the backup+regenerate path, never crash."""

    def test_array_root_backed_up_and_regenerated(self):
        repo = self.make_repo("non-dict-root")
        report = self.run_align(repo)

        data = json.loads((repo / ".mcp.json").read_text())
        self.assertIsInstance(data, dict)
        self.assertIn("devtools", data["mcpServers"])

        backups = [
            p for p in repo.iterdir() if ".bak" in p.name and p.is_file()
        ]
        self.assertTrue(backups, "non-dict root must be backed up as .bak-<date>")
        self.assertTrue(
            any("top-level array" in p.read_text() for p in backups),
            "backup must preserve the original content",
        )
        self.assertTrue(
            any("bak" in w.lower() for w in report.warnings),
            f"expected a backup warning, got: {report.warnings!r}",
        )
        self.assertIn(".mcp.json", self.change_paths(report))


class DriftedCanonicalTest(AlignFixtureCase):
    """Drift class 3: a canonical-named MCP entry diverging from the canonical set."""

    def test_canonical_entry_converged_non_canonical_preserved(self):
        repo = self.make_repo("drifted-canonical")
        canonical = json.loads((FIXTURES / "servers.json").read_text())
        report = self.run_align(repo)

        data = json.loads((repo / ".mcp.json").read_text())
        devtools = data["mcpServers"]["devtools"]
        self.assertEqual(devtools["command"], "mcp-devtools")
        self.assertEqual(devtools.get("env"), canonical["devtools"]["transport"]["env"])

        self.assertEqual(
            data["mcpServers"]["my-local-server"],
            {"type": "stdio", "command": "node", "args": ["./tools/local-mcp.js"]},
            "non-canonical entry must be preserved verbatim",
        )
        self.assertTrue(
            any("my-local-server" in item for item in report.preserved),
            "preserved non-canonical entries must be reported",
        )
        self.assertIn(".mcp.json", self.change_paths(report))


class StaleAgentPackTest(AlignFixtureCase):
    """Drift class 4: duplicated agent-pack files under .github/agents/."""

    def test_checksum_matches_deleted_others_preserved_and_reported(self):
        repo = self.make_repo("stale-agent-pack")
        report = self.run_align(repo)

        self.assertFalse((repo / ".github/agents/janitor.agent.md").exists())
        self.assertFalse(
            (repo / ".github/agents/reviewer.agent.md").exists(),
            "the workscripts reviewer variant must match via its own recorded hash",
        )
        changed = self.change_paths(report)
        self.assertIn(".github/agents/janitor.agent.md", changed)
        self.assertIn(".github/agents/reviewer.agent.md", changed)

        custom = repo / ".github/agents/custom.agent.md"
        self.assertTrue(custom.exists(), "non-matching agent files must be left in place")
        self.assertEqual(
            sha256(custom),
            sha256(FIXTURE_REPOS / "stale-agent-pack/.github/agents/custom.agent.md"),
        )
        self.assertTrue(
            any("custom.agent.md" in item for item in report.preserved),
            "unmatched .github/agents files must be reported",
        )

    def test_zero_matches_warns_instead_of_silent_noop(self):
        repo = self.make_repo("near-miss", git=True)
        (repo / ".agentic.json").write_text(
            json.dumps({"servers": ["devtools"], "cloud_assets": False}) + "\n"
        )
        agents = repo / ".github/agents"
        agents.mkdir(parents=True)
        shutil.copy(
            FIXTURE_REPOS / "stale-agent-pack/.github/agents/custom.agent.md",
            agents / "custom.agent.md",
        )
        report = self.run_align(repo)
        self.assertTrue(
            any(".github/agents" in w for w in report.warnings),
            "files under .github/agents with zero checksum matches must produce a warning "
            f"(a near-miss must not silently no-op); got: {report.warnings!r}",
        )
        self.assertTrue((agents / "custom.agent.md").exists())


class MissingCloudAssetsTest(AlignFixtureCase):
    """Drift class 5: cloud_assets true but no seeded repo-level Copilot assets."""

    SEEDED = (
        ".github/agents/prd.agent.md",
        ".github/copilot-instructions.md",
        ".github/skills/prd/SKILL.md",
    )

    def test_seeds_cloud_assets_with_managed_blocks(self):
        repo = self.make_repo("missing-cloud-assets")
        report = self.run_align(repo)
        for rel in self.SEEDED:
            with self.subTest(file=rel):
                target = repo / rel
                self.assertTrue(target.exists(), f"{rel} must be seeded")
                text = target.read_text()
                self.assertIn(MARKER_BEGIN, text, "seeded files must carry managed-block markers")
                self.assertIn(MARKER_END, text)
                self.assertIn(rel, self.change_paths(report))

    def test_creates_repo_mcp_configs_for_manifest_servers(self):
        repo = self.make_repo("missing-cloud-assets")
        self.run_align(repo)
        mcp = json.loads((repo / ".mcp.json").read_text())
        self.assertIn("devtools", mcp["mcpServers"])
        vscode = json.loads((repo / ".vscode/mcp.json").read_text())
        self.assertIn("devtools", vscode["servers"])

    def test_seeded_prd_agent_does_not_trigger_near_miss_warning(self):
        repo = self.make_repo("missing-cloud-assets")
        self.run_align(repo)
        second = self.run_align(repo)
        self.assertEqual(second.changes, [])
        self.assertFalse(
            any(".github/agents" in w for w in second.warnings),
            "align's own seeded prd.agent.md must not count as a stale-pack near-miss",
        )


class LocalAdditionsTest(AlignFixtureCase):
    """Drift class 6: seeded file whose managed block drifted, with repo-local
    additions outside the block."""

    def test_block_converged_outside_content_preserved_verbatim(self):
        repo = self.make_repo("local-additions")
        report = self.run_align(repo)
        text = (repo / ".github/copilot-instructions.md").read_text()

        self.assertIn("# Local preamble kept by align", text)
        self.assertIn(
            "This repo-specific line above the managed block must survive re-alignment.", text
        )
        self.assertIn("## Local build quirks", text)
        self.assertIn(
            "This repo-specific tail below the managed block must survive re-alignment.", text
        )

        self.assertNotIn("STALE DRIFTED SEEDED CONTENT", text)
        self.assertIn(
            "Canonical instruction content for align fixtures.", text,
            "managed block must be converged to the seed source's content",
        )
        self.assertIn(MARKER_BEGIN, text)
        self.assertIn(MARKER_END, text)
        self.assertIn(".github/copilot-instructions.md", self.change_paths(report))


class MarkerlessFileTest(AlignFixtureCase):
    """Drift class 7: hand-written (markerless) file at a seed target."""

    def test_markerless_seed_target_skipped_and_reported_never_overwritten(self):
        repo = self.make_repo("markerless-file")
        target = repo / ".github/copilot-instructions.md"
        before = sha256(target)
        report = self.run_align(repo)

        self.assertEqual(sha256(target), before, "hand-written file must never be overwritten")
        self.assertIn(".github/copilot-instructions.md", report.skipped)
        self.assertNotIn(".github/copilot-instructions.md", self.change_paths(report))

        # The other cloud assets have no hand-written blocker and are still seeded.
        self.assertTrue((repo / ".github/agents/prd.agent.md").exists())
        self.assertTrue((repo / ".github/skills/prd/SKILL.md").exists())

    def test_second_run_still_reports_skip_without_changes(self):
        repo = self.make_repo("markerless-file")
        self.run_align(repo)
        second = self.run_align(repo)
        self.assertEqual(second.changes, [])
        self.assertIn(".github/copilot-instructions.md", second.skipped)


class FirstRunManifestTest(AlignFixtureCase):
    """First run with no .agentic.json: write manifest + print plan, apply nothing."""

    def test_first_run_writes_manifest_and_plan_only(self):
        repo = self.make_repo("no-manifest")
        before = self.snapshot(repo)
        report = self.run_align(repo, assume_yes=False)

        manifest_path = repo / ".agentic.json"
        self.assertTrue(manifest_path.exists(), "first run must write the inferred manifest")
        manifest = json.loads(manifest_path.read_text())
        self.assertIn("devtools", manifest["servers"], 'default_for "*" must always be included')
        self.assertIn(
            "svelte", manifest["servers"],
            "svelte.config.js marker file must trigger the svelte default_for rule",
        )
        self.assertIsInstance(manifest["cloud_assets"], bool)

        self.assertFalse(report.applied)
        self.assertTrue(report.changes, "the plan must list the pending fixes")

        after = self.snapshot(repo)
        after.pop(".agentic.json", None)
        self.assertEqual(after, before, "a plan-only run must change nothing but the manifest")
        self.assertIn(
            "/Users/ronan", (repo / ".mcp.json").read_text(),
            "drift must remain untouched until the manifest has been seen",
        )

    def test_next_run_with_manifest_applies(self):
        repo = self.make_repo("no-manifest")
        self.run_align(repo, assume_yes=False)
        report = self.run_align(repo, assume_yes=False)
        self.assertTrue(report.applied)
        self.assert_no_user_paths((repo / ".mcp.json").read_text(), ".mcp.json")

    def test_yes_applies_on_first_run(self):
        repo = self.make_repo("no-manifest")
        report = self.run_align(repo, assume_yes=True)
        self.assertTrue(report.applied)
        self.assertTrue((repo / ".agentic.json").exists())
        self.assert_no_user_paths((repo / ".mcp.json").read_text(), ".mcp.json")


class ManifestPreservationTest(AlignFixtureCase):
    """Optional manifest keys (e.g. transit_project) must survive align runs:
    an existing .agentic.json is read-only to align, never rewritten."""

    def test_transit_project_survives_applying_run(self):
        repo = self.make_repo("stale-user-path")
        manifest_path = repo / ".agentic.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "servers": ["devtools"],
                    "cloud_assets": False,
                    "transit_project": "my-transit-project",
                },
                indent=2,
            )
            + "\n"
        )
        before = sha256(manifest_path)

        report = self.run_align(repo)

        self.assertTrue(report.applied)
        self.assertTrue(
            report.changes,
            "the fixture has drift; align must have done real work for this "
            "preservation check to mean anything",
        )
        self.assertEqual(
            sha256(manifest_path), before,
            "an existing .agentic.json must never be rewritten by align",
        )
        manifest = json.loads(manifest_path.read_text())
        self.assertEqual(manifest["transit_project"], "my-transit-project")
        self.assertNotIn(".agentic.json", self.change_paths(report))

        second = self.run_align(repo)
        self.assertEqual(second.changes, [])
        self.assertEqual(
            sha256(manifest_path), before,
            "transit_project must survive repeated align runs",
        )


LM_MARKER = "<!-- LM -->"
CANONICAL_NEXTUP = FIXTURES / "seed-root" / "nextup.example.md"


class NextupTemplateSeedTest(AlignFixtureCase):
    """PRD nextup-starwave-refinement, Align tooling req 1: seed the template
    when absent; a second run reports no pending changes."""

    def test_seeds_byte_identical_copy_when_absent(self):
        repo = self.make_repo("nextup-missing")
        report = self.run_align(repo)
        self.assertEqual(
            sha256(repo / "nextup.example.md"), sha256(CANONICAL_NEXTUP),
            "seeded nextup.example.md must be byte-identical to the canonical copy",
        )
        self.assertIn("nextup.example.md", self.change_paths(report))

    def test_second_run_reports_no_pending_changes(self):
        repo = self.make_repo("nextup-missing")
        self.run_align(repo)
        after_first = self.snapshot(repo)
        second = self.run_align(repo)
        self.assertEqual(second.changes, [], "the seed must be idempotent")
        self.assertEqual(self.snapshot(repo), after_first)


class NextupTemplateConvergenceTest(AlignFixtureCase):
    """Req 2: converge the machine zone (first <!-- LM --> marker down) to
    canonical; preserve the user zone byte-for-byte."""

    def test_user_zone_preserved_machine_zone_converged(self):
        repo = self.make_repo("nextup-user-zone")
        fixture = (FIXTURE_REPOS / "nextup-user-zone" / "nextup.example.md").read_text()
        canonical = CANONICAL_NEXTUP.read_text()
        report = self.run_align(repo)

        text = (repo / "nextup.example.md").read_text()
        self.assertEqual(
            text[: text.index(LM_MARKER)],
            fixture[: fixture.index(LM_MARKER)],
            "user zone above the first LM marker must survive byte-for-byte",
        )
        self.assertEqual(
            text[text.index(LM_MARKER):],
            canonical[canonical.index(LM_MARKER):],
            "machine zone from the first LM marker down must converge to canonical",
        )
        self.assertNotIn("STALE DRIFTED MACHINE ZONE", text)
        self.assertIn("nextup.example.md", self.change_paths(report))

    def test_already_canonical_reports_no_change(self):
        repo = self.make_repo("nextup-canonical")
        before = sha256(repo / "nextup.example.md")
        report = self.run_align(repo)
        self.assertEqual(sha256(repo / "nextup.example.md"), before)
        self.assertNotIn("nextup.example.md", self.change_paths(report))

    def test_markerless_template_skipped_never_overwritten(self):
        repo = self.make_repo("nextup-markerless")
        before = sha256(repo / "nextup.example.md")
        report = self.run_align(repo)
        self.assertEqual(
            sha256(repo / "nextup.example.md"), before,
            "a template with no LM marker is hand-written and must not be touched",
        )
        self.assertIn("nextup.example.md", report.skipped)
        self.assertNotIn("nextup.example.md", self.change_paths(report))


class NextupGitignoreTest(AlignFixtureCase):
    """Req 3: ensure the target's .gitignore carries a nextup.md entry."""

    def test_appends_exactly_one_entry_when_missing(self):
        repo = self.make_repo("nextup-gitignore-append")
        fixture_lines = (
            (FIXTURE_REPOS / "nextup-gitignore-append" / ".gitignore")
            .read_text().splitlines()
        )
        report = self.run_align(repo)
        lines = (repo / ".gitignore").read_text().splitlines()
        self.assertEqual(
            lines, fixture_lines + ["nextup.md"],
            "exactly one nextup.md line must be appended, existing rules kept",
        )
        self.assertIn(".gitignore", self.change_paths(report))

        second = self.run_align(repo)
        self.assertEqual(second.changes, [])
        self.assertEqual(
            (repo / ".gitignore").read_text().splitlines().count("nextup.md"), 1,
            "repeated runs must never duplicate the entry",
        )

    def test_already_ignoring_repo_is_unchanged(self):
        repo = self.make_repo("nextup-missing")  # fixture already ignores nextup.md
        before = sha256(repo / ".gitignore")
        report = self.run_align(repo)
        self.assertEqual(sha256(repo / ".gitignore"), before)
        self.assertNotIn(".gitignore", self.change_paths(report))

    def test_creates_gitignore_when_absent(self):
        repo = self.make_repo("nextup-gitignore-create")
        report = self.run_align(repo)
        self.assertEqual((repo / ".gitignore").read_text(), "nextup.md\n")
        self.assertIn(".gitignore", self.change_paths(report))


class NextupSessionFileTest(AlignFixtureCase):
    """Req 4: nextup.md is session-local — align must never create, modify,
    or delete it in the target repo."""

    def test_existing_nextup_md_ends_bit_identical(self):
        repo = self.make_repo("nextup-session-file")
        before = sha256(repo / "nextup.md")
        report = self.run_align(repo)
        self.assertEqual(
            sha256(repo / "nextup.md"), before,
            "nextup.md must end the run bit-identical",
        )
        self.assertNotIn("nextup.md", self.change_paths(report))
        self.assertTrue(
            (repo / "nextup.example.md").exists(),
            "the template must still be seeded alongside the untouched nextup.md",
        )

    def test_align_never_creates_nextup_md(self):
        repo = self.make_repo("nextup-missing")
        self.run_align(repo)
        self.assertFalse(
            (repo / "nextup.md").exists(),
            "align must not create the session-local nextup.md",
        )


class NextupPlanOnlyTest(AlignFixtureCase):
    """Req 5: the plan-only contract covers nextup-template fixes — pending
    seed/convergence is reported but not applied; nothing but the first-run
    .agentic.json changes on disk."""

    def test_plan_only_reports_pending_convergence_without_applying(self):
        repo = self.make_repo("nextup-plan-only")
        before = self.snapshot(repo)
        report = self.run_align(repo, assume_yes=False)

        self.assertFalse(report.applied)
        changed = self.change_paths(report)
        self.assertIn("nextup.example.md", changed, "pending convergence must be listed")
        self.assertIn(".gitignore", changed, "pending gitignore fix must be listed")

        after = self.snapshot(repo)
        after.pop(".agentic.json", None)
        self.assertEqual(
            after, before,
            "a plan-only run must change nothing but the first-run manifest",
        )

    def test_plan_only_reports_pending_seed_when_template_absent(self):
        repo = self.make_repo("no-manifest")
        report = self.run_align(repo, assume_yes=False)
        self.assertFalse(report.applied)
        self.assertIn("nextup.example.md", self.change_paths(report))
        self.assertFalse(
            (repo / "nextup.example.md").exists(),
            "the seed must not land on disk in a plan-only run",
        )


class NonGitDirectoryTest(AlignFixtureCase):
    def test_refuses_non_git_directory(self):
        repo = self.make_repo("not-a-repo", git=False)
        (repo / ".mcp.json").write_text("{}\n")
        with self.assertRaises(align.AlignError):
            self.run_align(repo)


class IdempotenceTest(AlignFixtureCase):
    """Req 5.3 hard contract: on every drift fixture, one applying run fixes all
    instances and an immediate second applying run reports zero changes."""

    def test_second_applying_run_reports_zero_changes_on_every_fixture(self):
        for fixture in sorted(p.name for p in FIXTURE_REPOS.iterdir() if p.is_dir()):
            with self.subTest(fixture=fixture):
                repo = self.make_repo(fixture)
                first = self.run_align(repo, assume_yes=True)
                self.assertTrue(first.applied)
                after_first = self.snapshot(repo)
                second = self.run_align(repo, assume_yes=True)
                self.assertEqual(
                    second.changes, [],
                    f"second applying run on {fixture} must report zero changes",
                )
                self.assertEqual(
                    self.snapshot(repo), after_first,
                    f"second applying run on {fixture} must not modify any file",
                )


class StalePacksFileTest(unittest.TestCase):
    """Sanity of the task-10 artifact scripts/stale-packs.json (real file)."""

    EXPECTED_FILES = {
        "agent-yolo.agent.md",
        "janitor.agent.md",
        "orchestrator.agent.md",
        "planner.agent.md",
        "prompt-engineer.agent.md",
        "reviewer.agent.md",
        "worker.agent.md",
    }

    def test_schema_and_provenance(self):
        data = json.loads(STALE_PACKS_JSON.read_text())
        self.assertIn("_comment", data)
        self.assertEqual(set(data["packs"]), self.EXPECTED_FILES)
        for name, hashes in data["packs"].items():
            with self.subTest(file=name):
                self.assertIsInstance(hashes, list)
                self.assertTrue(1 <= len(hashes) <= 2, "one hash per distinct repo variant")
                for value in hashes:
                    self.assertRegex(value, r"^[0-9a-f]{64}$")

    def test_fixture_pack_files_are_listed(self):
        data = json.loads(STALE_PACKS_JSON.read_text())
        pack_dir = FIXTURE_REPOS / "stale-agent-pack/.github/agents"
        self.assertIn(sha256(pack_dir / "janitor.agent.md"), data["packs"]["janitor.agent.md"])
        self.assertIn(sha256(pack_dir / "reviewer.agent.md"), data["packs"]["reviewer.agent.md"])
        custom_hash = sha256(pack_dir / "custom.agent.md")
        all_hashes = {h for hashes in data["packs"].values() for h in hashes}
        self.assertNotIn(custom_hash, all_hashes)


class SeedVerbatimTest(unittest.TestCase):
    """Spec spec-janitor Req 9.3 / Decision 10: agentic_lib.seed_verbatim —
    the verbatim-seeding class for tool-owned files (no managed blocks).

    Contract: destination missing -> copy; identical -> unchanged (no
    "changed" entry, returns False); differing -> back up as .bak-<date>
    (the existing _backup convention) and re-copy, reported as changed.
    Markerless existing targets are NOT skipped as hand-written: the
    managed-block skip must not apply to verbatim-class seeds.
    """

    SEED_CONTENT = (
        "#!/usr/bin/env python3\n"
        '"""Tool-owned fixture auditor; no agentic markers anywhere."""\n'
        'print("canonical")\n'
    )

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="seed-verbatim-test-")
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.src = self.tmp / "seed" / "spec_lint.py"
        self.src.parent.mkdir()
        self.src.write_text(self.SEED_CONTENT)
        self.dst = self.tmp / "repo" / ".github" / "skills" / "spec_lint.py"

    def kinds(self, report):
        return [entry.kind for entry in report]

    def test_missing_destination_copied_and_reported_changed(self):
        report = []
        changed = agentic_lib.seed_verbatim(self.src, self.dst, report)
        self.assertTrue(changed, "a fresh copy must be reported as a change")
        self.assertEqual(
            self.dst.read_bytes(), self.src.read_bytes(),
            "seeded file must be byte-identical to the seed source",
        )
        self.assertIn("changed", self.kinds(report))
        self.assertNotIn("skipped", self.kinds(report))

    def test_identical_destination_is_unchanged(self):
        self.dst.parent.mkdir(parents=True)
        self.dst.write_text(self.SEED_CONTENT)
        report = []
        changed = agentic_lib.seed_verbatim(self.src, self.dst, report)
        self.assertFalse(changed, "an identical destination is converged")
        self.assertNotIn("changed", self.kinds(report))
        self.assertEqual(
            list(self.dst.parent.glob("*.bak-*")), [],
            "an identical destination must never be backed up",
        )

    def test_differing_destination_backed_up_and_recopied(self):
        self.dst.parent.mkdir(parents=True)
        stale = "print('hand-modified stale copy')\n"
        self.dst.write_text(stale)
        report = []
        changed = agentic_lib.seed_verbatim(self.src, self.dst, report)
        self.assertTrue(changed)
        self.assertEqual(
            self.dst.read_bytes(), self.src.read_bytes(),
            "a differing destination must be re-copied verbatim",
        )
        backups = list(self.dst.parent.glob(self.dst.name + ".bak-*"))
        self.assertTrue(
            backups,
            "the previous content must be backed up as <name>.bak-<date>",
        )
        self.assertEqual(
            backups[0].read_text(), stale,
            "the backup must preserve the previous content byte-for-byte",
        )
        self.assertIn("changed", self.kinds(report))

    def test_markerless_existing_target_is_not_skipped_as_hand_written(self):
        """The write_managed markerless skip must NOT apply here: janitor
        assets are tool-owned by contract, so a markerless existing target
        (e.g. a previously seeded .py file) is converged, never frozen."""
        self.dst.parent.mkdir(parents=True)
        markerless = "# no agentic markers here\nprint('old seeded copy')\n"
        self.dst.write_text(markerless)
        report = []
        changed = agentic_lib.seed_verbatim(self.src, self.dst, report)
        self.assertTrue(
            changed,
            "a markerless verbatim-class target must be converged, not "
            "skipped as hand-written",
        )
        self.assertNotIn("skipped", self.kinds(report))
        self.assertEqual(self.dst.read_bytes(), self.src.read_bytes())


JANITOR_SEED_ROOT = FIXTURES / "seed-root"

# Seeding pairs for the spec-janitor toolchain (spec spec-janitor Req 9.3,
# 9.4): repo-relative target -> seed source in the fixture seed root. All
# verbatim class: targets must end byte-identical to their seed source.
JANITOR_SEEDED = {
    ".github/agents/spec-janitor.agent.md":
        JANITOR_SEED_ROOT / "copilot" / "agents" / "spec-janitor.agent.md",
    ".github/skills/spec-janitor/SKILL.md":
        JANITOR_SEED_ROOT / "claude" / "skills" / "spec-janitor" / "SKILL.md",
    ".github/skills/spec-janitor/spec_lint.py":
        JANITOR_SEED_ROOT / "claude" / "skills" / "spec-janitor"
        / "spec_lint.py",
    ".github/skills/spec-janitor/references/spec-conventions.md":
        JANITOR_SEED_ROOT / "claude" / "skills" / "spec-janitor"
        / "references" / "spec-conventions.md",
}


class JanitorSeedingTest(AlignFixtureCase):
    """Spec spec-janitor Req 9.3/9.4: cloud seeding of the janitor
    toolchain — claude/skills/spec-janitor/** -> .github/skills/spec-janitor/**
    and copilot/agents/spec-janitor.agent.md -> .github/agents/, verbatim
    class, cloud_assets: true repos only (the prd pattern)."""

    def test_seeds_janitor_assets_byte_identical(self):
        repo = self.make_repo("missing-cloud-assets")
        report = self.run_align(repo)
        for rel, seed in JANITOR_SEEDED.items():
            with self.subTest(file=rel):
                target = repo / rel
                self.assertTrue(target.exists(), f"{rel} must be seeded")
                self.assertEqual(
                    sha256(target), sha256(seed),
                    f"{rel} is verbatim class: it must be byte-identical "
                    "to its seed source (no managed-block rewriting)",
                )
                self.assertIn(rel, self.change_paths(report))

    def test_cloud_assets_false_seeds_no_janitor_assets(self):
        repo = self.make_repo("drifted-canonical")  # cloud_assets: false
        self.run_align(repo)
        self.assertFalse(
            (repo / ".github").exists(),
            "cloud_assets is false: janitor assets must not be seeded",
        )

    def test_second_aligned_run_reports_no_changes_or_agents_warning(self):
        repo = self.make_repo("missing-cloud-assets")
        self.run_align(repo)
        second = self.run_align(repo)
        self.assertEqual(second.changes, [], "verbatim seeding must be idempotent")
        self.assertFalse(
            any(".github/agents" in w for w in second.warnings),
            "the seeded spec-janitor.agent.md must not count as a "
            f"stale-pack near-miss; got: {second.warnings!r}",
        )


class JanitorDriftedAssetsTest(AlignFixtureCase):
    """A drifted (hand-modified, markerless) janitor asset is tool-owned:
    align backs it up (.bak-<date>) and re-copies the seed verbatim — the
    markerless hand-written skip must NOT apply. The stale-pack prune
    exempts the janitor agent path via SEEDED_AGENT_RELS."""

    DRIFTED = (
        ".github/agents/spec-janitor.agent.md",
        ".github/skills/spec-janitor/spec_lint.py",
    )

    def test_drifted_targets_backed_up_and_recopied_not_skipped(self):
        repo = self.make_repo("janitor-drifted")
        originals = {rel: (repo / rel).read_text() for rel in self.DRIFTED}
        report = self.run_align(repo)
        for rel in self.DRIFTED:
            with self.subTest(file=rel):
                target = repo / rel
                self.assertEqual(
                    sha256(target), sha256(JANITOR_SEEDED[rel]),
                    f"{rel} must be re-copied verbatim from the seed",
                )
                backups = list(target.parent.glob(target.name + ".bak-*"))
                self.assertTrue(
                    backups,
                    f"{rel} differed from the seed: the previous content "
                    "must be backed up as <name>.bak-<date>",
                )
                self.assertEqual(
                    backups[0].read_text(), originals[rel],
                    "the backup must preserve the drifted content",
                )
                self.assertIn(rel, self.change_paths(report))
                self.assertNotIn(
                    rel, report.skipped,
                    "verbatim-class targets must never be skipped as "
                    "hand-written, markerless or not",
                )

    def test_prune_exempts_janitor_agent_without_zero_match_warning(self):
        repo = self.make_repo("janitor-drifted")
        report = self.run_align(repo)
        self.assertTrue(
            (repo / ".github/agents/spec-janitor.agent.md").exists(),
            "the janitor agent file must be exempt from stale-pack pruning",
        )
        self.assertFalse(
            any("stale-pack" in w for w in report.warnings),
            "the janitor agent path must not trigger the zero-stale-pack-"
            f"matches warning; got: {report.warnings!r}",
        )

    def test_second_aligned_run_reports_no_changes(self):
        repo = self.make_repo("janitor-drifted")
        self.run_align(repo)
        after_first = self.snapshot(repo)
        second = self.run_align(repo)
        self.assertEqual(second.changes, [])
        self.assertEqual(
            self.snapshot(repo), after_first,
            "a second aligned run must not touch any file (no new backups)",
        )


if __name__ == "__main__":
    unittest.main()
