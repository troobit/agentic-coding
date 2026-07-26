"""Fixture tests for claude/skills/spec-janitor/spec_lint.py (spec: spec-janitor).

TDD red phase: spec_lint.py does not exist yet (task 3). Importing this module
MUST fail with a meaningful ImportError until it lands. These tests define the
auditor's contract; the implementation tasks build against them without
changing them.

Expected interface of claude/skills/spec-janitor/spec_lint.py
-------------------------------------------------------------

    spec_lint.audit(
        repo_path,              # str | Path — target repo
        *,
        fix=False,              # apply auto-fix findings whose preconditions hold
        fix_dirty=False,        # override the dirty-specs/-tree guard
    ) -> dict                   # the JSON output model (see below)

    spec_lint.render_report(data) -> str    # human-readable report
    spec_lint.main(argv) -> int             # CLI entry; returns the exit code
    spec_lint.RULES                         # dict: mechanical rule ID -> disposition

    # rune seams (monkeypatched in tests):
    spec_lint._rune_available() -> bool
    spec_lint._rune_list(path) -> (ok: bool, stderr: str)

JSON model (design "JSON output schema", Req 1.6) — required keys pinned here;
the model may carry an additional "notices" list of report strings:

    {
      "version": 1,
      "repo": "<abs path>",
      "rune_available": bool,
      "excluded": {"specs": [...], "findings": [...]},
      "findings": [
        {"id": "<rule>:<spec>:<file>:<subject>", "rule": ..., "disposition": ...,
         "spec": ..., "subject": ..., "evidence": [{"file": ..., "excerpt": ...}],
         "fix_applied": bool, "demoted": bool}
      ]
    }

CLI (design "spec_lint.py"):

    spec_lint.py <repo-path> [--json] [--fix] [--fix-dirty]
    spec_lint.py <repo-path> exclude (--spec <spec-path> | --finding <finding-id>)
    spec_lint.py <repo-path> mark-raised --finding <finding-id>

Exit codes: 0 no findings (including a repo with no specs/, which prints a
notice), 1 findings exist, 2 usage/internal error.

Run with: python3 -m unittest discover -s tests
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "spec_lint"
FIXTURE_REPOS = FIXTURES / "repos"
SKILL_DIR = REPO_ROOT / "claude" / "skills" / "spec-janitor"
SPEC_LINT = SKILL_DIR / "spec_lint.py"
CONVENTIONS = SKILL_DIR / "references" / "spec-conventions.md"

sys.path.insert(0, str(SKILL_DIR))

try:
    import spec_lint  # noqa: E402
except ImportError as exc:  # pragma: no cover - red phase until task 3 lands
    raise ImportError(
        "claude/skills/spec-janitor/spec_lint.py does not exist yet. This is "
        "the deliberately-red TDD phase of spec spec-janitor: task 2 wrote "
        "these tests, task 3 implements the detectors against the contract in "
        "this module's docstring. Once spec_lint.py lands, this suite must "
        "run green."
    ) from exc

RUNE_AVAILABLE = shutil.which("rune") is not None
DISPOSITIONS = {"auto-fix", "gated", "detect-only"}

# A PATH with the essentials but (deterministically) no rune binary.
NO_RUNE_PATH = "/usr/bin:/bin"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class SpecLintCase(unittest.TestCase):
    """Shared helpers: materialise fixture repos in temp dirs."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="spec-lint-test-")
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)

    _seq = 0

    def make_repo(self, fixture_name, git=False):
        SpecLintCase._seq += 1
        dest = self.tmp / f"{fixture_name}-{SpecLintCase._seq}"
        shutil.copytree(FIXTURE_REPOS / fixture_name, dest)
        if git:
            self.git_init(dest)
        return dest

    def git_init(self, repo):
        for cmd in (
            ["git", "init", "-q"],
            ["git", "add", "-A"],
            ["git", "-c", "user.email=t@t", "-c", "user.name=t",
             "commit", "-qm", "fixture"],
        ):
            subprocess.run(cmd, cwd=repo, check=True, capture_output=True)

    def audit(self, repo, **kwargs):
        return spec_lint.audit(repo, **kwargs)

    def cli(self, repo, *args, rune=None):
        """Run the CLI in a subprocess. rune=False strips rune off PATH;
        rune=None inherits the environment (works with or without rune)."""
        env = None
        if rune is False:
            env = dict(os.environ, PATH=NO_RUNE_PATH)
        return subprocess.run(
            [sys.executable, str(SPEC_LINT), str(repo), *args],
            capture_output=True, text=True, env=env,
        )

    def snapshot(self, repo):
        out = {}
        for path in Path(repo).rglob("*"):
            rel = path.relative_to(repo).as_posix()
            if rel == ".git" or rel.startswith(".git/"):
                continue
            if path.is_file():
                out[rel] = sha256(path)
        return out

    # -- finding helpers ---------------------------------------------------

    def by_rule(self, data, rule, spec=None):
        return [
            f for f in data["findings"]
            if f["rule"] == rule and (spec is None or f["spec"] == spec)
        ]

    def one(self, data, rule, spec, subject=None):
        matches = [
            f for f in self.by_rule(data, rule, spec)
            if subject is None or f["subject"] == subject
        ]
        self.assertEqual(
            len(matches), 1,
            f"expected exactly one {rule} finding for {spec!r} "
            f"(subject={subject!r}), got: {matches!r}",
        )
        return matches[0]


class DetectionTest(SpecLintCase):
    """Task 2: the survey corpus (Req 1.1-1.8, 5.5)."""

    def setUp(self):
        super().setUp()
        self.repo = self.make_repo("survey")
        self.data = self.audit(self.repo)

    def test_dangling_anchor_missing_target_file(self):
        finding = self.one(
            self.data, "SJ-REF-001", "sdd-ui", "requirements.md#1.2"
        )
        self.assertEqual(finding["disposition"], "gated")
        self.assertEqual(
            finding["evidence"][0]["file"],
            "specs/sdd-ui/tasks-agent-bridge.md",
        )

    def test_identical_finding_ids_merge_with_multiple_evidence(self):
        # requirements.md#1.1 is referenced twice in the same task file:
        # one finding, two evidence entries (design: finding model).
        finding = self.one(
            self.data, "SJ-REF-001", "sdd-ui", "requirements.md#1.1"
        )
        self.assertEqual(
            len(finding["evidence"]), 2,
            "identical ids must merge into one finding with merged evidence",
        )
        ids = [f["id"] for f in self.data["findings"]]
        self.assertEqual(len(ids), len(set(ids)), "finding ids must be unique")

    def test_dangling_anchor_missing_fragment(self):
        # anchor-gap: requirements.md exists but has no 9.9 anchor.
        self.one(self.data, "SJ-REF-001", "anchor-gap", "requirements.md#9.9")
        # 1.1 resolves via <a name="1.1"> and must NOT be reported.
        self.assertEqual(
            [f["subject"] for f in self.by_rule(self.data, "SJ-REF-001", "anchor-gap")],
            ["requirements.md#9.9"],
        )

    def test_heading_slug_anchor_resolves(self):
        # captcha links [Scope](smolspec.md#scope) -> "## Scope" heading slug.
        self.assertEqual(self.by_rule(self.data, "SJ-REF-001", "captcha"), [])

    def test_front_matter_reference_to_missing_file(self):
        # sdd-ui front matter lists "requirements.md": no such file anywhere.
        finding = self.one(self.data, "SJ-REF-002", "sdd-ui", "requirements.md")
        self.assertEqual(finding["disposition"], "auto-fix")
        # captcha front matter lists "smolspec.md": folder-relative entry,
        # broken under repo-root resolution.
        self.one(self.data, "SJ-REF-002", "captcha", "smolspec.md")
        # crossref points across folders at a file that is gone.
        self.one(
            self.data, "SJ-REF-002", "crossref",
            "specs/other-spec/requirements.md",
        )
        # repo-root-relative entries that resolve are not findings.
        self.assertEqual(
            self.by_rule(self.data, "SJ-REF-002", "contactsimplifier"), []
        )

    def test_mixed_stable_id_presence(self):
        finding = self.one(self.data, "SJ-TASK-002", "captcha", "tasks.md")
        self.assertEqual(finding["disposition"], "auto-fix")
        # Uniformly-ID'd and uniformly-bare files are not mixed.
        self.assertEqual(self.by_rule(self.data, "SJ-TASK-002", "contactsimplifier"), [])
        self.assertEqual(
            self.by_rule(self.data, "SJ-TASK-002", "mangled"), [],
            "a file with no stable IDs at all is benign drift, not mixed IDs",
        )

    def test_out_of_sequence_numbering_slug_subject(self):
        finding = self.one(
            self.data, "SJ-TASK-003", "contactsimplifier", "post-implementation"
        )
        self.assertEqual(finding["disposition"], "detect-only")
        # The full id format from the design is pinned verbatim.
        self.assertEqual(
            finding["id"],
            "SJ-TASK-003:contactsimplifier:tasks.md:post-implementation",
        )

    def test_structure_violations_are_task_001(self):
        finding = self.one(self.data, "SJ-TASK-001", "mangled", "tasks.md")
        self.assertEqual(finding["disposition"], "detect-only")
        excerpts = " ".join(e["excerpt"] for e in finding["evidence"])
        self.assertIn("- [] 1.", excerpts, "malformed checkbox line is evidence")

    def test_zero_recognized_document_folder_fires_mode_001(self):
        # Pins janitor-owned discovery: a folder specs-overview would never
        # visit (no recognized document) must still be audited.
        finding = self.one(self.data, "SJ-MODE-001", "scratch", "scratch")
        self.assertEqual(finding["disposition"], "detect-only")

    def test_recognized_mode_missing_task_file(self):
        self.one(self.data, "SJ-MODE-002", "missing-tasks")
        # PRD-lane multi-task-file specs satisfy the task-file requirement.
        self.assertEqual(self.by_rule(self.data, "SJ-MODE-002", "prd-multi"), [])
        self.assertEqual(self.by_rule(self.data, "SJ-MODE-001", "prd-multi"), [])

    def test_bugfix_shape_violations(self):
        self.one(self.data, "SJ-MODE-003", "bugfixes/broken-bug")
        self.one(self.data, "SJ-MODE-003", "bugfixes/empty-bug")
        self.assertEqual(
            [f for f in self.data["findings"] if f["spec"] == "bugfixes/good-bug"],
            [],
            "a conforming bugfix entry (with solution-comparison.md) is clean",
        )

    def test_bugfix_shaped_folder_outside_bugfixes(self):
        # Recognized as bugfix-shaped, so no SJ-MODE-001; the mis-filing
        # itself is SJ-FILE-001, which belongs to the skill, not the lint.
        self.assertEqual(
            [f for f in self.data["findings"] if f["spec"] == "misfiled-bug"],
            [],
        )
        self.assertEqual(
            [f for f in self.data["findings"] if f["rule"].startswith("SJ-FILE")],
            [],
            "spec_lint must not emit judgment-family rules",
        )

    def test_nested_domain_specs_named_by_relative_path(self):
        self.one(
            self.data, "SJ-REF-001", "estimation/pipeline", "requirements.md#2.2"
        )
        specs = {f["spec"] for f in self.data["findings"]}
        self.assertNotIn(
            "pipeline", specs,
            "leaf names alone collide across domains; the repo-relative "
            "path under specs/ is the spec name",
        )

    def test_dotfolders_exempt(self):
        for finding in self.data["findings"]:
            self.assertNotIn(".orbit", finding["id"])

    def test_no_writes_without_fix(self):
        repo = self.make_repo("survey")
        before = self.snapshot(repo)
        self.audit(repo)
        self.assertEqual(self.snapshot(repo), before, "audit must never write")
        self.assertFalse(
            (repo / "specs" / ".janitor.json").exists(),
            "a plain audit must not create the exclusion store",
        )


class JanitorStoreExemptTest(SpecLintCase):
    """Req 5.5: the janitor's own bookkeeping file is exempt from audits."""

    def test_store_file_not_audited(self):
        repo = self.make_repo("clean")
        (repo / "specs" / ".janitor.json").write_text(
            json.dumps({
                "version": 1, "exclude_specs": [], "exclude_findings": [],
                "raised": [], "last_run": "2026-07-01",
            }) + "\n"
        )
        data = self.audit(repo)
        self.assertEqual(data["findings"], [])


class JsonSchemaTest(SpecLintCase):
    """Task 2: pin the JSON schema (Req 1.6)."""

    def test_schema_shape_and_closed_disposition_enum(self):
        repo = self.make_repo("survey")
        data = self.audit(repo)
        self.assertEqual(data["version"], 1)
        self.assertTrue(Path(data["repo"]).is_absolute())
        self.assertIsInstance(data["rune_available"], bool)
        self.assertEqual(set(data["excluded"]), {"specs", "findings"})
        self.assertIsInstance(data["excluded"]["specs"], list)
        self.assertIsInstance(data["excluded"]["findings"], list)
        self.assertTrue(data["findings"], "the survey corpus must produce findings")
        for finding in data["findings"]:
            with self.subTest(finding=finding.get("id")):
                self.assertLessEqual(
                    {"id", "rule", "disposition", "spec", "subject",
                     "evidence", "fix_applied", "demoted"},
                    set(finding),
                )
                self.assertIn(
                    finding["disposition"], DISPOSITIONS,
                    "the disposition enum is closed at three values",
                )
                self.assertRegex(finding["rule"], r"^SJ-[A-Z]+-\d{3}$")
                self.assertTrue(
                    finding["id"].startswith(
                        finding["rule"] + ":" + finding["spec"] + ":"
                    )
                )
                self.assertTrue(finding["id"].endswith(":" + finding["subject"]))
                self.assertIsInstance(finding["evidence"], list)
                self.assertTrue(finding["evidence"], "evidence must not be empty")
                for entry in finding["evidence"]:
                    self.assertEqual(set(entry), {"file", "excerpt"})
                self.assertIsInstance(finding["fix_applied"], bool)
                self.assertIsInstance(finding["demoted"], bool)

    def test_cli_json_output_parses(self):
        repo = self.make_repo("survey")
        proc = self.cli(repo, "--json")
        self.assertEqual(proc.returncode, 1)
        data = json.loads(proc.stdout)
        self.assertEqual(data["version"], 1)


class CliTest(SpecLintCase):
    """Task 2: exit codes 0/1/2 (Req 1.6, 1.8)."""

    def test_findings_exit_1(self):
        proc = self.cli(self.make_repo("survey"))
        self.assertEqual(proc.returncode, 1)

    def test_clean_repo_exit_0_zero_findings(self):
        repo = self.make_repo("clean")
        proc = self.cli(repo, "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["findings"], [])

    def test_no_specs_repo_exit_0_with_notice(self):
        repo = self.make_repo("no-specs")
        proc = self.cli(repo)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("specs", (proc.stdout + proc.stderr).lower())
        self.assertFalse(
            (repo / "specs").exists(),
            "a no-specs audit must not create anything",
        )

    def test_usage_errors_exit_2(self):
        self.assertEqual(self.cli(self.make_repo("clean"), "--bogus").returncode, 2)
        proc = subprocess.run(
            [sys.executable, str(SPEC_LINT), str(self.tmp / "does-not-exist")],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 2)

    def test_human_report_groups_by_spec_and_tags_findings(self):
        proc = self.cli(self.make_repo("survey"), rune=False)
        for token in ("sdd-ui", "contactsimplifier", "SJ-REF-001",
                      "SJ-TASK-003", "gated", "detect-only"):
            self.assertIn(token, proc.stdout)


class RuneVerificationTest(SpecLintCase):
    """Task 2 / Req 1.3: rune present -> verify; absent -> stated skip."""

    def test_rune_absent_reports_skip(self):
        proc = self.cli(self.make_repo("survey"), "--json", rune=False)
        self.assertFalse(json.loads(proc.stdout)["rune_available"])
        report = self.cli(self.make_repo("survey"), rune=False)
        self.assertIn("rune verification skipped", report.stdout)

    @unittest.skipUnless(RUNE_AVAILABLE, "rune CLI not installed")
    def test_rune_available_flag_true(self):
        proc = self.cli(self.make_repo("clean"), "--json")
        self.assertTrue(json.loads(proc.stdout)["rune_available"])

    def test_rune_failure_becomes_task_001_with_stderr_evidence(self):
        repo = self.make_repo("clean")
        with mock.patch.object(spec_lint, "_rune_available", lambda: True), \
                mock.patch.object(
                    spec_lint, "_rune_list",
                    lambda path: (False, "boom: unparseable task file"),
                ):
            data = self.audit(repo)
        finding = self.one(data, "SJ-TASK-001", "alpha", "tasks.md")
        self.assertTrue(
            any("boom" in e["excerpt"] for e in finding["evidence"]),
            "rune's stderr must be carried as evidence",
        )


if __name__ == "__main__":
    unittest.main()
