"""Fixture tests for scripts/process_status.py (rune-drift and PRD-lane
visibility from PRD agreement-invoice-skills).

Fixture repos are real git checkouts built in a temp dir (same pattern as
tests/test_align.py) with pinned commit dates, so every report column can
be asserted exactly. Drift-flag fixtures are constructed so each drift
condition produces that flag and only that flag (PRD Req 3), and the
read-only test pins that a run leaves target trees bit-identical (Req 4).
RuneDriftTest needs the real rune binary on PATH (bootstrap installs it).

Run with: python3 -m unittest discover -s tests
"""

import contextlib
import hashlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import process_status  # noqa: E402

COMMIT_DATE = "2026-07-01T12:00:00 +0000"

GIT_ENV_ARGS = ["-c", "user.name=fixture", "-c", "user.email=fix@example.com"]

# A task file rune parses, and a hand-written checklist it rejects
# ("invalid task format: missing task number").
RUNE_TASKS = "# Tasks\n\n- [ ] 1. First thing\n- [x] 2. Done thing\n"
HAND_TASKS = "# TODO\n\n- [ ] write the thing\n- [x] ship it\n"


class StatusFixtureCase(unittest.TestCase):
    """Shared helper: materialise fixture repos as real git checkouts."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="status-test-")
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)

    def _git(self, repo, *args):
        subprocess.run(["git", "-C", str(repo), *GIT_ENV_ARGS, *args],
                       check=True, capture_output=True)

    def make_repo(self, name, *, agentic=True,
                  specs=None, files=None, git=True, commit=True, dirty=False):
        """Build a fixture repo.

        specs: dict of subfolder name -> iterable of spec doc filenames to
        create. files: dict of repo-relative path -> exact text, for files
        whose content matters (e.g. rune task files). The default kwargs
        produce a repo with zero drift flags.
        """
        repo = self.tmp / name
        repo.mkdir(parents=True)
        if agentic:
            (repo / ".agentic.json").write_text('{"servers": []}\n')
        for folder, docs in (specs or {}).items():
            sub = repo / "specs" / folder
            sub.mkdir(parents=True)
            for doc in docs:
                (sub / doc).write_text(f"# {doc}\n")
        for relpath, text in (files or {}).items():
            path = repo / relpath
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        if git:
            self._git(repo, "init", "-q", "-b", "main")
            if commit:
                self._git(repo, "add", "-A")
                # Pin the committer date (%cs is what the report shows).
                env = dict(os.environ,
                           GIT_AUTHOR_DATE=COMMIT_DATE,
                           GIT_COMMITTER_DATE=COMMIT_DATE)
                subprocess.run(
                    ["git", "-C", str(repo), *GIT_ENV_ARGS, "commit", "-q",
                     "--allow-empty", "-m", "fixture"],
                    check=True, capture_output=True, env=env)
        if dirty:
            (repo / "uncommitted.txt").write_text("dirty\n")
        return repo

    def flags(self, repo):
        return process_status.drift_flags(process_status.collect(repo))


class CollectColumnsTest(StatusFixtureCase):
    """Req 2: every column matches a fixture repo with known contents."""

    def test_all_columns_match_fixture(self):
        repo = self.make_repo(
            "known",
            specs={
                "full": ("requirements.md", "design.md", "tasks.md"),
                "smol": ("smolspec.md", "tasks.md"),
                "prd-only": ("prd.md",),
                "empty": (),
            })
        info = process_status.collect(repo)
        self.assertTrue(info["exists"])
        self.assertTrue(info["git"])
        self.assertEqual(info["name"], "known")
        self.assertTrue(info["agentic_json"])
        self.assertEqual(info["specs"], {
            "empty": [],
            "full": ["requirements.md", "design.md", "tasks.md"],
            "prd-only": ["prd.md"],
            # Docs appear in SPEC_DOCS order, not alphabetically.
            "smol": ["tasks.md", "smolspec.md"],
        })
        self.assertEqual(info["branch"], "main")
        self.assertFalse(info["dirty"])
        self.assertEqual(info["last_commit"], "2026-07-01")

    def test_dirty_tree_and_absent_optional_files(self):
        repo = self.make_repo("bare", agentic=False, dirty=True)
        info = process_status.collect(repo)
        self.assertFalse(info["agentic_json"])
        self.assertEqual(info["specs"], {})
        self.assertTrue(info["dirty"])

    def test_missing_repo_path_reports_gracefully(self):
        info = process_status.collect(self.tmp / "nope")
        self.assertFalse(info["exists"])
        self.assertEqual(self.flags(self.tmp / "nope"), [])

    def test_non_git_directory_reports_gracefully(self):
        repo = self.make_repo("plain", git=False)
        info = process_status.collect(repo)
        self.assertTrue(info["exists"])
        self.assertFalse(info["git"])
        self.assertIsNone(info["branch"])
        self.assertIsNone(info["dirty"])
        self.assertIsNone(info["last_commit"])


class DriftFlagTest(StatusFixtureCase):
    """Req 3: each drift fixture produces that flag and only that flag."""

    def test_clean_fixture_has_no_flags(self):
        self.assertEqual(self.flags(self.make_repo("clean")), [])

    def test_spec_gap_requirements_without_design_or_tasks(self):
        repo = self.make_repo("gap",
                              specs={"orphan": ("requirements.md",)})
        self.assertEqual(self.flags(repo), ["spec-gap"])

    def test_requirements_with_design_or_tasks_is_not_a_gap(self):
        repo = self.make_repo(
            "no-gap",
            specs={"designed": ("requirements.md", "design.md"),
                   "tasked": ("requirements.md", "tasks.md")})
        self.assertEqual(self.flags(repo), [])

    def test_missing_agentic_json(self):
        repo = self.make_repo("no-manifest", agentic=False)
        self.assertEqual(self.flags(repo), ["no-agentic-json"])


class RuneDriftTest(StatusFixtureCase):
    """PRD agreement-invoice-skills Req 1: rune-drift flag and detail lines."""

    def test_hand_written_tasks_md_is_flagged(self):
        repo = self.make_repo("hand",
                              files={"specs/feat/tasks.md": HAND_TASKS})
        info = process_status.collect(repo)
        self.assertEqual(info["rune_drift"], {"feat": ["tasks.md"]})
        self.assertFalse(info["rune_missing"])
        self.assertEqual(self.flags(repo), ["rune-drift"])

    def test_rune_format_file_is_not_flagged(self):
        repo = self.make_repo("live",
                              files={"specs/feat/tasks.md": RUNE_TASKS})
        info = process_status.collect(repo)
        self.assertEqual(info["rune_drift"], {})
        self.assertEqual(self.flags(repo), [])

    def test_only_the_failing_split_file_is_named(self):
        repo = self.make_repo(
            "split",
            files={"specs/feat/tasks.md": RUNE_TASKS,
                   "specs/feat/tasks-extra.md": HAND_TASKS})
        info = process_status.collect(repo)
        self.assertEqual(info["rune_drift"], {"feat": ["tasks-extra.md"]})

    def test_detail_line_names_the_failing_file(self):
        repo = self.make_repo("named",
                              files={"specs/feat/tasks.md": HAND_TASKS})
        output = process_status.render([process_status.collect(repo)])
        self.assertIn("specs/feat: tasks.md [rune-drift: tasks.md]", output)
        self.assertIn("rune-drift", output.splitlines()[1])

    def test_missing_rune_binary_warns_and_never_flags(self):
        repo = self.make_repo("no-rune",
                              files={"specs/feat/tasks.md": HAND_TASKS})
        with mock.patch("process_status.shutil.which", return_value=None):
            info = process_status.collect(repo)
        self.assertTrue(info["rune_missing"])
        self.assertEqual(info["rune_drift"], {})
        self.assertEqual(process_status.drift_flags(info), [])
        output = process_status.render([info])
        self.assertIn("warning: rune binary not found; "
                      "task-file parsing not checked", output)

    def test_repo_without_task_files_never_probes_or_warns(self):
        repo = self.make_repo("no-tasks",
                              specs={"prd-only": ("prd.md",)})
        with mock.patch("process_status.shutil.which", return_value=None):
            info = process_status.collect(repo)
        self.assertFalse(info["rune_missing"])
        self.assertEqual(self.flags(repo), [])


class BacklogStatusTest(StatusFixtureCase):
    """Req 3.5, AC 6.3: BACKLOG.md schema check and the BACKLOG column.

    Hybrid check: rune parse gate, then a raw-text phase set/order scan
    (an empty-but-valid backlog has no PhaseMarkers in rune's JSON), the
    pending-only invariant via rune's Stats (catches nested checked
    subtasks a top-level-only checkbox scan would miss), and a raw H1
    presence scan.
    """

    VALID = ("# Backlog\n"
             "\n"
             "## Idea\n"
             "\n"
             "- [ ] 1. First idea\n"
             "  - conversation, 2026-08-26\n"
             "\n"
             "## Needs Spec\n"
             "\n"
             "- [ ] 2. Second idea\n"
             "  - conversation, 2026-08-26 → spec: foo-bar\n"
             "\n"
             "## Outstanding\n"
             "\n"
             "- [ ] 3. foo-bar: 4 tasks outstanding, 1 blocked\n"
             "  - specs/foo-bar/tasks.md, 2026-08-26 → run: /next-task\n")

    def backlog(self, text):
        repo = self.make_repo("repo", files={"specs/BACKLOG.md": text})
        return process_status.collect(repo)

    # -- ok fixtures --

    def test_absent_backlog_renders_dash_and_is_not_drift(self):
        repo = self.make_repo("no-backlog", specs={"feat": ("requirements.md",
                                                             "design.md")})
        info = process_status.collect(repo)
        self.assertEqual(info["backlog"], "-")
        self.assertNotIn("backlog-drift", self.flags(repo))

    def test_valid_backlog_is_ok(self):
        info = self.backlog(self.VALID)
        self.assertEqual(info["backlog"], "ok")
        self.assertEqual(process_status.drift_flags(info), [])

    def test_empty_but_valid_backlog_is_ok(self):
        # All three phases present, zero entries — the normal state for a
        # repo with nothing captured and nothing outstanding. rune's JSON
        # has no PhaseMarkers at all for an empty file, so this must come
        # from the raw-text phase scan, not rune's Stats.
        info = self.backlog(
            "# Backlog\n\n## Idea\n\n## Needs Spec\n\n## Outstanding\n")
        self.assertEqual(info["backlog"], "ok")
        self.assertEqual(process_status.drift_flags(info), [])

    def test_gapped_numbering_is_ok(self):
        info = self.backlog(
            "# Backlog\n"
            "\n"
            "## Idea\n"
            "\n"
            "- [ ] 1. First idea\n"
            "  - conversation, 2026-08-26\n"
            "\n"
            "- [ ] 3. Third idea\n"
            "  - conversation, 2026-08-26\n"
            "\n"
            "## Needs Spec\n"
            "\n"
            "## Outstanding\n")
        self.assertEqual(info["backlog"], "ok")

    def test_arrow_detail_line_is_ok(self):
        info = self.backlog(
            "# Backlog\n"
            "\n"
            "## Idea\n"
            "\n"
            "## Needs Spec\n"
            "\n"
            "- [ ] 1. Something\n"
            "  - conversation, 2026-08-26 → spec: foo-bar\n"
            "\n"
            "## Outstanding\n")
        self.assertEqual(info["backlog"], "ok")

    def test_trailing_whitespace_heading_is_ok(self):
        info = self.backlog(
            "# Backlog\n"
            "\n"
            "## Idea \n"
            "\n"
            "- [ ] 1. First idea\n"
            "  - conversation, 2026-08-26\n"
            "\n"
            "## Needs Spec\n"
            "\n"
            "## Outstanding\n")
        self.assertEqual(info["backlog"], "ok")

    # -- drift fixtures --

    def test_unparseable_backlog_is_drift(self):
        info = self.backlog(
            "# Backlog\n"
            "\n"
            "## Idea\n"
            "\n"
            "- missing checkbox format\n"
            "\n"
            "## Needs Spec\n"
            "\n"
            "## Outstanding\n")
        self.assertEqual(info["backlog"], "drift")
        self.assertEqual(process_status.drift_flags(info), ["backlog-drift"])

    def test_wrong_phase_name_is_drift(self):
        info = self.backlog(
            "# Backlog\n\n## idea\n\n## Needs Spec\n\n## Outstanding\n")
        self.assertEqual(info["backlog"], "drift")
        self.assertEqual(process_status.drift_flags(info), ["backlog-drift"])

    def test_extra_phase_is_drift(self):
        info = self.backlog(
            "# Backlog\n\n## Idea\n\n## Needs Spec\n\n## Outstanding\n"
            "\n## Someday\n")
        self.assertEqual(info["backlog"], "drift")

    def test_missing_phase_is_drift(self):
        info = self.backlog("# Backlog\n\n## Idea\n")
        self.assertEqual(info["backlog"], "drift")

    def test_missing_outstanding_phase_is_drift(self):
        # The pre-Outstanding two-phase shape: a backlog written before the
        # rebuild step existed, or one whose rebuild never ran. Absent means
        # stale, not idle — an idle rebuild leaves the phase present-but-empty.
        info = self.backlog("# Backlog\n\n## Idea\n\n## Needs Spec\n")
        self.assertEqual(info["backlog"], "drift")
        self.assertEqual(process_status.drift_flags(info), ["backlog-drift"])

    def test_phase_order_is_drift(self):
        info = self.backlog(
            "# Backlog\n\n## Idea\n\n## Outstanding\n\n## Needs Spec\n")
        self.assertEqual(info["backlog"], "drift")

    def test_checked_entry_is_drift(self):
        info = self.backlog(
            "# Backlog\n"
            "\n"
            "## Idea\n"
            "\n"
            "- [x] 1. Checked entry\n"
            "  - conversation, 2026-08-26\n"
            "\n"
            "## Needs Spec\n"
            "\n"
            "## Outstanding\n")
        self.assertEqual(info["backlog"], "drift")
        self.assertEqual(process_status.drift_flags(info), ["backlog-drift"])

    def test_nested_checked_subtask_is_drift(self):
        # Only the Stats-based check catches this: a naive top-level-only
        # `^- \[` scan sees just the unchecked parent line.
        info = self.backlog(
            "# Backlog\n"
            "\n"
            "## Idea\n"
            "\n"
            "- [ ] 1. Parent idea\n"
            "  - [x] 1.1. Nested sub\n"
            "\n"
            "## Needs Spec\n"
            "\n"
            "## Outstanding\n")
        self.assertEqual(info["backlog"], "drift")
        self.assertEqual(process_status.drift_flags(info), ["backlog-drift"])

    def test_missing_h1_is_drift(self):
        info = self.backlog("## Idea\n\n## Needs Spec\n\n## Outstanding\n")
        self.assertEqual(info["backlog"], "drift")

    def test_drift_reason_appears_in_detail_lines(self):
        repo = self.make_repo(
            "reasoned",
            files={"specs/BACKLOG.md":
                   "## Idea\n\n## Needs Spec\n\n## Outstanding\n"})
        output = process_status.render([process_status.collect(repo)])
        self.assertIn(
            "specs/BACKLOG.md: missing H1 title [backlog-drift]", output)
        self.assertIn("backlog-drift", output.splitlines()[1])


class ReadOnlyTest(StatusFixtureCase):
    """Req 4: target trees are bit-identical before and after a run."""

    def tree_digest(self, root):
        digest = {}
        for path in sorted(Path(root).rglob("*")):
            if path.is_file():
                digest[str(path.relative_to(root))] = hashlib.sha256(
                    path.read_bytes()).hexdigest()
        return digest

    def test_run_leaves_target_trees_bit_identical(self):
        repos = [
            self.make_repo("ro-clean",
                           specs={"gap": ("requirements.md",)}),
            self.make_repo("ro-dirty", agentic=False,
                           dirty=True),
            self.make_repo("ro-plain", git=False),
        ]
        before = [self.tree_digest(repo) for repo in repos]
        with contextlib.redirect_stdout(io.StringIO()):
            exit_code = process_status.main([str(repo) for repo in repos])
        self.assertEqual(exit_code, 0)
        self.assertEqual([self.tree_digest(repo) for repo in repos], before)


class CliTest(StatusFixtureCase):
    """Req 1: default list vs explicit paths, and graceful missing rows."""

    def run_main(self, argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exit_code = process_status.main(argv)
        return exit_code, out.getvalue()

    def test_default_repos_are_this_repo_plus_checked_in_list(self):
        repos = process_status.default_repos()
        self.assertEqual(repos[0], process_status.REPO_ROOT)
        home = Path.home()
        self.assertEqual(repos[1:], [
            home / "repos" / name
            for name in ("medata", "netmap", "tocs", "rtob", "localml",
                         "loshop")])

    def test_explicit_paths_report_only_those(self):
        one = self.make_repo("only-one")
        exit_code, output = self.run_main([str(one)])
        self.assertEqual(exit_code, 0)
        lines = output.strip().splitlines()
        rows = [line for line in lines if not line.startswith(" ")]
        self.assertEqual(len(rows), 2)  # header + exactly one repo row
        self.assertIn("only-one", rows[1])

    def test_summary_row_carries_every_column(self):
        repo = self.make_repo(
            "rowcheck",
            specs={"feat": ("requirements.md", "design.md", "tasks.md")})
        _, output = self.run_main([str(repo)])
        row = output.splitlines()[1]
        for cell in ("rowcheck", "main", "clean", "2026-07-01", "yes"):
            self.assertIn(cell, row)
        self.assertIn("specs/feat: requirements.md design.md tasks.md",
                      output)

    def test_prd_only_spec_folder_appears_in_detail_lines(self):
        # PRD agreement-invoice-skills Req 5: PRD-lane folders are visible.
        repo = self.make_repo("prd-lane",
                              specs={"autonomous": ("prd.md",)})
        _, output = self.run_main([str(repo)])
        self.assertIn("specs/autonomous: prd.md", output)

    def test_missing_path_row_is_graceful(self):
        missing = self.tmp / "gone"
        exit_code, output = self.run_main([str(missing)])
        self.assertEqual(exit_code, 0)
        self.assertIn("missing-path", output)
        self.assertIn(str(missing), output)


if __name__ == "__main__":
    unittest.main()
