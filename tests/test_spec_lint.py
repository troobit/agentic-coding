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
import re
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


_ID_MARKER_RE = re.compile(r" <!-- id:[a-z0-9]{7} -->$")


class FixTest(SpecLintCase):
    """Task 4: --fix pipeline, preconditions, demotion, safety guards
    (Req 3.2-3.4, 4.1-4.3)."""

    def fix_run(self, repo, *extra):
        proc = self.cli(repo, "--fix", "--json", *extra)
        self.assertIn(proc.returncode, (0, 1), proc.stderr)
        return json.loads(proc.stdout)

    def test_ref002_rewritten_to_unique_candidate(self):
        repo = self.make_repo("survey", git=True)
        data = self.fix_run(repo)
        finding = self.one(data, "SJ-REF-002", "captcha", "smolspec.md")
        self.assertTrue(finding["fix_applied"])
        self.assertFalse(finding["demoted"])
        text = (repo / "specs/captcha/tasks.md").read_text()
        self.assertIn("specs/captcha/smolspec.md", text)
        self.assertNotIn("\n    - smolspec.md\n", text)

    def test_ref002_precondition_failures_demote_and_never_write(self):
        repo = self.make_repo("survey", git=True)
        before_sdd = sha256(repo / "specs/sdd-ui/tasks-agent-bridge.md")
        before_cross = sha256(repo / "specs/crossref/tasks.md")
        data = self.fix_run(repo)
        # Zero candidates in the leaf folder: demoted, not guessed at.
        finding = self.one(data, "SJ-REF-002", "sdd-ui", "requirements.md")
        self.assertTrue(finding["demoted"])
        self.assertFalse(finding["fix_applied"])
        # Cross-folder path: demoted, not guessed at.
        finding = self.one(
            data, "SJ-REF-002", "crossref", "specs/other-spec/requirements.md"
        )
        self.assertTrue(finding["demoted"])
        self.assertFalse(finding["fix_applied"])
        self.assertEqual(sha256(repo / "specs/sdd-ui/tasks-agent-bridge.md"), before_sdd)
        self.assertEqual(sha256(repo / "specs/crossref/tasks.md"), before_cross)

    def test_task002_minting_is_purely_additive(self):
        repo = self.make_repo("survey", git=True)
        before = (repo / "specs/captcha/tasks.md").read_text().split("\n")
        data = self.fix_run(repo)
        finding = self.one(data, "SJ-TASK-002", "captcha", "tasks.md")
        self.assertTrue(finding["fix_applied"])
        after = (repo / "specs/captcha/tasks.md").read_text().split("\n")
        self.assertEqual(len(before), len(after), "minting must not add or drop lines")
        body_start = after.index("---", 1) + 1  # the REF-002 rewrite owns the
        for old, new in zip(before[body_start:], after[body_start:]):  # front matter
            if old == new:
                continue
            # The only permitted change: a stable-ID marker appended to a
            # previously unmarked task line.
            self.assertTrue(
                new.startswith(old) and _ID_MARKER_RE.search(new),
                f"non-additive change: {old!r} -> {new!r}",
            )
        # Every top-level task now carries a valid marker; pre-existing
        # markers are untouched.
        task_lines = [l for l in after if l.startswith("- [")]
        for line in task_lines:
            self.assertRegex(line, r"<!-- id:[a-z0-9]{7} -->$")
        self.assertIn("<!-- id:c1a2b3c -->", "\n".join(after))
        ids = [m.group(1) for l in task_lines
               for m in [re.search(r"id:([a-z0-9]{7})", l)] if m]
        self.assertEqual(len(ids), len(set(ids)), "minted IDs must be unique")

    @unittest.skipUnless(RUNE_AVAILABLE, "rune CLI not installed")
    def test_fixed_file_round_trips_rune_list(self):
        repo = self.make_repo("survey", git=True)
        self.fix_run(repo)
        proc = subprocess.run(
            ["rune", "list", str(repo / "specs/captcha/tasks.md")],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_fix_only_mutates_auto_fix_rules(self):
        repo = self.make_repo("survey", git=True)
        before = self.snapshot(repo)
        self.fix_run(repo)
        after = self.snapshot(repo)
        changed = {rel for rel in before if before[rel] != after.get(rel)}
        self.assertEqual(
            changed, {"specs/captcha/tasks.md"},
            "only files with applicable auto-fixes may change",
        )

    def test_fix_ordering_ref002_before_task002(self):
        repo = self.make_repo("survey", git=True)
        proc = self.cli(repo, "--fix")
        applied = [
            line for line in proc.stdout.splitlines() if "applied" in line.lower()
        ]
        ref = [i for i, l in enumerate(applied) if "SJ-REF-002" in l]
        task = [i for i, l in enumerate(applied) if "SJ-TASK-002" in l]
        self.assertTrue(ref and task, f"both applied fixes must be listed: {applied!r}")
        self.assertLess(max(ref), min(task), "SJ-REF-002 fixes apply before SJ-TASK-002")

    def test_fix_idempotent_rerun_quiet_and_byte_identical(self):
        repo = self.make_repo("survey", git=True)
        first = self.fix_run(repo)
        fixed_ids = {f["id"] for f in first["findings"] if f["fix_applied"]}
        self.assertTrue(fixed_ids)
        after_first = self.snapshot(repo)
        second = self.fix_run(repo)
        second_ids = {f["id"] for f in second["findings"]}
        self.assertFalse(
            fixed_ids & second_ids,
            "re-run must produce zero findings for fixed items",
        )
        self.assertFalse(any(f["fix_applied"] for f in second["findings"]))
        self.assertEqual(
            self.snapshot(repo), after_first,
            "immediate re-run must leave the tree byte-identical",
        )

    def test_dirty_specs_tree_refuses_fix_but_reports(self):
        repo = self.make_repo("survey", git=True)
        (repo / "specs/scratch/notes.md").write_text("uncommitted edit\n")
        before = self.snapshot(repo)
        proc = self.cli(repo, "--fix", "--json")
        self.assertEqual(proc.returncode, 1, "the report is still produced")
        data = json.loads(proc.stdout)
        self.assertTrue(data["findings"])
        self.assertFalse(any(f["fix_applied"] for f in data["findings"]))
        self.assertEqual(self.snapshot(repo), before, "refusal means no writes")
        self.assertTrue(
            any("--fix" in n for n in data["notices"]),
            f"the refusal must be reported: {data['notices']!r}",
        )

    def test_fix_dirty_overrides_the_guard(self):
        repo = self.make_repo("survey", git=True)
        (repo / "specs/scratch/notes.md").write_text("uncommitted edit\n")
        data = self.fix_run(repo, "--fix-dirty")
        self.assertTrue(any(f["fix_applied"] for f in data["findings"]))
        self.assertIn(
            "specs/captcha/smolspec.md",
            (repo / "specs/captcha/tasks.md").read_text(),
        )

    def test_dirty_outside_specs_does_not_block_fix(self):
        repo = self.make_repo("survey", git=True)
        (repo / "README.md").write_text("uncommitted but outside specs/\n")
        data = self.fix_run(repo)
        self.assertTrue(any(f["fix_applied"] for f in data["findings"]))

    def test_non_git_directory_refuses_fix(self):
        repo = self.make_repo("survey", git=False)
        before = self.snapshot(repo)
        proc = self.cli(repo, "--fix", "--json")
        self.assertEqual(proc.returncode, 1)
        data = json.loads(proc.stdout)
        self.assertFalse(any(f["fix_applied"] for f in data["findings"]))
        self.assertEqual(
            self.snapshot(repo), before,
            "no git oracle -> treated as dirty -> no writes",
        )
        data = self.fix_run(repo, "--fix-dirty")
        self.assertTrue(
            any(f["fix_applied"] for f in data["findings"]),
            "--fix-dirty proceeds even without git",
        )


TARGET_FINDING = "SJ-TASK-003:widget:tasks.md:post-implementation"

WIDGET_TASKS = """\
---
references:
    - specs/widget/smolspec.md
---
# Widget Tasks

- [x] 1. Build the widget <!-- id:h1a2b3c -->
  - Assemble the parts
- [x] 2. Ship the widget <!-- id:h1a2b3d -->
  - Package and deliver
- [ ] 5. Post implementation <!-- id:h1a2b3e -->
  - Cleanup pass appended by a later run
"""

WIDGET_SMOLSPEC = """\
# Smolspec: Widget

## Scope

A widget, specified small.
"""


class StoreCase(SpecLintCase):
    """Task 6 harness: a minimal repo with one stable SJ-TASK-003 finding."""

    def make_widget_repo(self):
        SpecLintCase._seq += 1
        repo = self.tmp / f"widget-{SpecLintCase._seq}"
        spec = repo / "specs" / "widget"
        spec.mkdir(parents=True)
        (spec / "smolspec.md").write_text(WIDGET_SMOLSPEC)
        (spec / "tasks.md").write_text(WIDGET_TASKS)
        return repo

    def store_path(self, repo):
        return repo / "specs" / ".janitor.json"

    def read_store(self, repo):
        return json.loads(self.store_path(repo).read_text())


class StoreWriteTest(StoreCase):
    """exclude / mark-raised are the only writers; schema-validated on
    write (Req 5.1-5.3, design store contract)."""

    def test_exclude_spec_writes_schema_valid_store_and_skips_spec(self):
        repo = self.make_widget_repo()
        proc = self.cli(repo, "exclude", "--spec", "widget")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        store = self.read_store(repo)
        self.assertEqual(store["version"], 1)
        self.assertEqual(store["exclude_specs"], ["widget"])
        self.assertEqual(store["exclude_findings"], [])
        self.assertEqual(store["raised"], [])
        self.assertRegex(store["last_run"], r"^\d{4}-\d{2}-\d{2}$")
        # Recording twice must not duplicate the entry.
        self.cli(repo, "exclude", "--spec", "widget")
        self.assertEqual(self.read_store(repo)["exclude_specs"], ["widget"])
        # The spec is skipped and listed (Req 5.3).
        data = self.audit(repo)
        self.assertEqual(
            [f for f in data["findings"] if f["spec"] == "widget"], []
        )
        self.assertIn("widget", data["excluded"]["specs"])
        report = self.cli(repo).stdout
        self.assertIn("widget", report)

    def test_exclude_finding_suppresses_and_lists(self):
        repo = self.make_widget_repo()
        self.assertIn(
            TARGET_FINDING, {f["id"] for f in self.audit(repo)["findings"]}
        )
        proc = self.cli(repo, "exclude", "--finding", TARGET_FINDING)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(
            self.read_store(repo)["exclude_findings"], [TARGET_FINDING]
        )
        data = self.audit(repo)
        self.assertNotIn(TARGET_FINDING, {f["id"] for f in data["findings"]})
        self.assertIn(TARGET_FINDING, data["excluded"]["findings"])

    def test_subcommand_usage_errors_exit_2(self):
        repo = self.make_widget_repo()
        self.assertEqual(self.cli(repo, "exclude").returncode, 2)
        self.assertEqual(
            self.cli(repo, "exclude", "--spec", "a", "--finding", "b").returncode, 2
        )
        self.assertEqual(self.cli(repo, "mark-raised").returncode, 2)

    def test_audit_never_writes_the_store(self):
        repo = self.make_widget_repo()
        self.cli(repo, "--json")
        self.assertFalse(self.store_path(repo).exists())
        self.cli(repo, "exclude", "--spec", "other")
        before = sha256(self.store_path(repo))
        self.cli(repo, "--json")
        self.assertEqual(sha256(self.store_path(repo)), before)


class FindingIdentityTest(StoreCase):
    """Req 5.4: finding identity survives unrelated edits and line moves
    (slug subjects, not numbers)."""

    def test_exclusion_survives_line_insertions(self):
        repo = self.make_widget_repo()
        self.cli(repo, "exclude", "--finding", TARGET_FINDING)
        tasks = repo / "specs/widget/tasks.md"
        text = tasks.read_text().replace(
            "# Widget Tasks",
            "# Widget Tasks\n\nA new preamble paragraph.\n\nMore prose.",
        )
        tasks.write_text(text)
        data = self.audit(repo)
        self.assertEqual(
            self.by_rule(data, "SJ-TASK-003", "widget"), [],
            "the excluded finding must keep matching after line insertions",
        )

    def test_exclusion_survives_task_inserted_above_subject(self):
        repo = self.make_widget_repo()
        self.cli(repo, "exclude", "--finding", TARGET_FINDING)
        tasks = repo / "specs/widget/tasks.md"
        text = tasks.read_text().replace(
            "- [ ] 5. Post implementation",
            "- [x] 3. Document the widget <!-- id:h1a2b3f -->\n"
            "  - Write the docs\n"
            "- [ ] 5. Post implementation",
        )
        tasks.write_text(text)
        data = self.audit(repo)
        self.assertEqual(
            self.by_rule(data, "SJ-TASK-003", "widget"), [],
            "a task inserted above the subject must not re-key the finding",
        )


class MarkRaisedTest(StoreCase):
    """Req 5.6: raised entries are raise-once - never re-raised."""

    def test_mark_raised_records_and_suppresses(self):
        repo = self.make_widget_repo()
        proc = self.cli(repo, "mark-raised", "--finding", TARGET_FINDING)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.read_store(repo)["raised"], [TARGET_FINDING])
        self.assertEqual(self.read_store(repo)["exclude_findings"], [])
        data = self.audit(repo)
        self.assertNotIn(
            TARGET_FINDING, {f["id"] for f in data["findings"]},
            "raised entries suppress re-raising on later runs",
        )


class CorruptStoreTest(StoreCase):
    """Design store contract: corrupt store -> backup + rebuild on write,
    prominent report; never silently dropped."""

    def test_corrupt_store_backed_up_and_rebuilt_on_write(self):
        repo = self.make_widget_repo()
        self.store_path(repo).parent.mkdir(exist_ok=True)
        self.store_path(repo).write_text("{ this is not json\n")
        proc = self.cli(repo, "exclude", "--spec", "widget")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        backups = [
            p for p in (repo / "specs").iterdir()
            if p.name.startswith(".janitor.json.bak-")
        ]
        self.assertEqual(len(backups), 1, "corrupt store must be backed up")
        self.assertIn("this is not json", backups[0].read_text())
        self.assertEqual(self.read_store(repo)["exclude_specs"], ["widget"])
        combined = proc.stdout + proc.stderr
        self.assertIn(".bak-", combined, "the backup must be reported prominently")

    def test_schema_invalid_store_treated_as_corrupt(self):
        repo = self.make_widget_repo()
        self.store_path(repo).write_text(
            json.dumps({"version": 1, "exclude_specs": "widget"}) + "\n"
        )
        proc = self.cli(repo, "exclude", "--finding", TARGET_FINDING)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        backups = [
            p for p in (repo / "specs").iterdir()
            if p.name.startswith(".janitor.json.bak-")
        ]
        self.assertEqual(len(backups), 1)
        self.assertEqual(
            self.read_store(repo)["exclude_findings"], [TARGET_FINDING]
        )

    def test_corrupt_store_on_audit_warns_and_never_rewrites(self):
        repo = self.make_widget_repo()
        self.store_path(repo).write_text("{ broken\n")
        before = sha256(self.store_path(repo))
        proc = self.cli(repo, "--json")
        self.assertEqual(proc.returncode, 1, "findings are still produced")
        data = json.loads(proc.stdout)
        self.assertIn(TARGET_FINDING, {f["id"] for f in data["findings"]})
        self.assertTrue(
            any("janitor.json" in n for n in data["notices"]),
            f"corruption must be reported, got: {data['notices']!r}",
        )
        self.assertEqual(
            sha256(self.store_path(repo)), before,
            "an audit run must never touch the store, even a corrupt one",
        )


if __name__ == "__main__":
    unittest.main()
