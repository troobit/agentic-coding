"""Fixture tests for scripts/process_status.py (PRD: nextup-starwave-refinement;
rune-drift and PRD-lane visibility from PRD agreement-invoice-skills).

Fixture repos are real git checkouts built in a temp dir (same pattern as
tests/test_align.py) with pinned commit dates, so every report column can
be asserted exactly. Drift-flag fixtures are constructed so each drift
condition produces that flag and only that flag (PRD Req 3), and the
read-only test pins that a run leaves target trees bit-identical (Req 4).
RuneDriftTest needs the real rune binary on PATH (bootstrap installs it).

Run with: python3 -m unittest discover -s tests
"""

import contextlib
import datetime
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

TODAY = datetime.date(2026, 7, 10)
COMMIT_DATE = "2026-07-01T12:00:00 +0000"

GIT_ENV_ARGS = ["-c", "user.name=fixture", "-c", "user.email=fix@example.com"]

# A task file rune parses, and a hand-written checklist it rejects
# ("invalid task format: missing task number").
RUNE_TASKS = "# Tasks\n\n- [ ] 1. First thing\n- [x] 2. Done thing\n"
HAND_TASKS = "# TODO\n\n- [ ] write the thing\n- [x] ship it\n"


def nextup_text(marker="<!-- LM -->", note_dates=("2026-07-01",),
                extra_zone_lines=()):
    """A nextup.md with a user zone, one machine marker, and dated notes."""
    lines = [
        "<!-- USER -->",
        "",
        "free-form user instructions",
        "- 2020-01-01 — a decoy note in the USER zone, ignored",
        "",
        marker,
        "",
        "## Where things stand",
        "",
        "**Notes (latest first):**",
    ]
    lines += [f"- {date} — did a thing" for date in note_dates]
    lines += list(extra_zone_lines)
    return "\n".join(lines) + "\n"


class StatusFixtureCase(unittest.TestCase):
    """Shared helper: materialise fixture repos as real git checkouts."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="status-test-")
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)

    def _git(self, repo, *args):
        subprocess.run(["git", "-C", str(repo), *GIT_ENV_ARGS, *args],
                       check=True, capture_output=True)

    def make_repo(self, name, *, nextup=None, example=True, agentic=True,
                  specs=None, files=None, git=True, commit=True, dirty=False):
        """Build a fixture repo.

        nextup: file text or None (file absent). specs: dict of
        subfolder name -> iterable of spec doc filenames to create.
        files: dict of repo-relative path -> exact text, for files whose
        content matters (e.g. rune task files). The default kwargs
        produce a repo with zero drift flags.
        """
        repo = self.tmp / name
        repo.mkdir(parents=True)
        if nextup is not None:
            (repo / "nextup.md").write_text(nextup)
        if example:
            (repo / "nextup.example.md").write_text("<!-- USER -->\n")
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
        return process_status.drift_flags(process_status.collect(repo),
                                          today=TODAY)


class CollectColumnsTest(StatusFixtureCase):
    """Req 2: every column matches a fixture repo with known contents."""

    def test_all_columns_match_fixture(self):
        repo = self.make_repo(
            "known",
            nextup=nextup_text(note_dates=("2026-06-01", "2026-07-01")),
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
        self.assertTrue(info["nextup"])
        self.assertEqual(info["zone"], "LM")
        self.assertEqual(info["newest_note"], datetime.date(2026, 7, 1))
        self.assertTrue(info["example"])
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
        repo = self.make_repo("bare", nextup=None, example=False,
                              agentic=False, dirty=True)
        info = process_status.collect(repo)
        self.assertFalse(info["nextup"])
        self.assertIsNone(info["zone"])
        self.assertIsNone(info["newest_note"])
        self.assertFalse(info["example"])
        self.assertFalse(info["agentic_json"])
        self.assertEqual(info["specs"], {})
        self.assertTrue(info["dirty"])

    def test_legacy_markers_are_recognised(self):
        for marker, label in (("<!-- ML -->", "ML"),
                              ("<!-- nextup:machine -->", "machine"),
                              ("# What I want", "what-i-want")):
            repo = self.make_repo(f"legacy-{label}",
                                  nextup=nextup_text(marker=marker))
            info = process_status.collect(repo)
            self.assertEqual(info["zone"], label, marker)
            self.assertEqual(info["newest_note"], datetime.date(2026, 7, 1))

    def test_first_marker_in_file_order_wins(self):
        text = nextup_text(marker="<!-- ML -->",
                           extra_zone_lines=("", "<!-- LM -->"))
        repo = self.make_repo("two-markers", nextup=text)
        self.assertEqual(process_status.collect(repo)["zone"], "ML")

    def test_notes_before_the_marker_are_ignored(self):
        # The decoy 2020 note in the USER zone must not become the newest
        # note; only zone notes count.
        repo = self.make_repo("decoy", nextup=nextup_text())
        info = process_status.collect(repo)
        self.assertEqual(info["newest_note"], datetime.date(2026, 7, 1))

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
        self.assertEqual(self.flags(self.make_repo("clean",
                                                   nextup=nextup_text())), [])

    def test_machine_zone_missing_file(self):
        repo = self.make_repo("no-nextup", nextup=None)
        self.assertEqual(self.flags(repo), ["machine-zone"])

    def test_machine_zone_missing_marker(self):
        repo = self.make_repo(
            "no-marker", nextup="# Notes\n- 2026-07-01 — dated but no zone\n")
        self.assertEqual(self.flags(repo), ["machine-zone"])

    def test_machine_zone_malformed_without_dated_note(self):
        repo = self.make_repo(
            "no-note",
            nextup="<!-- USER -->\n\n<!-- LM -->\n\n"
                   "- <date> — seeded from nextup.example.md\n")
        self.assertEqual(self.flags(repo), ["machine-zone"])

    def test_stale_note_with_dirty_tree(self):
        old = (TODAY - datetime.timedelta(days=15)).isoformat()
        repo = self.make_repo("stale-dirty",
                              nextup=nextup_text(note_dates=(old,)),
                              dirty=True)
        self.assertEqual(self.flags(repo), ["stale-nextup"])

    def test_stale_note_with_clean_tree_is_not_flagged(self):
        old = (TODAY - datetime.timedelta(days=15)).isoformat()
        repo = self.make_repo("stale-clean",
                              nextup=nextup_text(note_dates=(old,)))
        self.assertEqual(self.flags(repo), [])

    def test_note_exactly_fourteen_days_old_is_not_stale(self):
        edge = (TODAY - datetime.timedelta(days=14)).isoformat()
        repo = self.make_repo("edge", nextup=nextup_text(note_dates=(edge,)),
                              dirty=True)
        self.assertEqual(self.flags(repo), [])

    def test_spec_gap_requirements_without_design_or_tasks(self):
        repo = self.make_repo("gap", nextup=nextup_text(),
                              specs={"orphan": ("requirements.md",)})
        self.assertEqual(self.flags(repo), ["spec-gap"])

    def test_requirements_with_design_or_tasks_is_not_a_gap(self):
        repo = self.make_repo(
            "no-gap", nextup=nextup_text(),
            specs={"designed": ("requirements.md", "design.md"),
                   "tasked": ("requirements.md", "tasks.md")})
        self.assertEqual(self.flags(repo), [])

    def test_missing_agentic_json(self):
        repo = self.make_repo("no-manifest", nextup=nextup_text(),
                              agentic=False)
        self.assertEqual(self.flags(repo), ["no-agentic-json"])


class RuneDriftTest(StatusFixtureCase):
    """PRD agreement-invoice-skills Req 1: rune-drift flag and detail lines."""

    def test_hand_written_tasks_md_is_flagged(self):
        repo = self.make_repo("hand", nextup=nextup_text(),
                              files={"specs/feat/tasks.md": HAND_TASKS})
        info = process_status.collect(repo)
        self.assertEqual(info["rune_drift"], {"feat": ["tasks.md"]})
        self.assertFalse(info["rune_missing"])
        self.assertEqual(self.flags(repo), ["rune-drift"])

    def test_rune_format_file_is_not_flagged(self):
        repo = self.make_repo("live", nextup=nextup_text(),
                              files={"specs/feat/tasks.md": RUNE_TASKS})
        info = process_status.collect(repo)
        self.assertEqual(info["rune_drift"], {})
        self.assertEqual(self.flags(repo), [])

    def test_only_the_failing_split_file_is_named(self):
        repo = self.make_repo(
            "split", nextup=nextup_text(),
            files={"specs/feat/tasks.md": RUNE_TASKS,
                   "specs/feat/tasks-extra.md": HAND_TASKS})
        info = process_status.collect(repo)
        self.assertEqual(info["rune_drift"], {"feat": ["tasks-extra.md"]})

    def test_detail_line_names_the_failing_file(self):
        repo = self.make_repo("named", nextup=nextup_text(),
                              files={"specs/feat/tasks.md": HAND_TASKS})
        output = process_status.render([process_status.collect(repo)],
                                       today=TODAY)
        self.assertIn("specs/feat: tasks.md [rune-drift: tasks.md]", output)
        self.assertIn("rune-drift", output.splitlines()[1])

    def test_missing_rune_binary_warns_and_never_flags(self):
        repo = self.make_repo("no-rune", nextup=nextup_text(),
                              files={"specs/feat/tasks.md": HAND_TASKS})
        with mock.patch("process_status.shutil.which", return_value=None):
            info = process_status.collect(repo)
        self.assertTrue(info["rune_missing"])
        self.assertEqual(info["rune_drift"], {})
        self.assertEqual(process_status.drift_flags(info, today=TODAY), [])
        output = process_status.render([info], today=TODAY)
        self.assertIn("warning: rune binary not found; "
                      "task-file parsing not checked", output)

    def test_repo_without_task_files_never_probes_or_warns(self):
        repo = self.make_repo("no-tasks", nextup=nextup_text(),
                              specs={"prd-only": ("prd.md",)})
        with mock.patch("process_status.shutil.which", return_value=None):
            info = process_status.collect(repo)
        self.assertFalse(info["rune_missing"])
        self.assertEqual(self.flags(repo), [])


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
            self.make_repo("ro-clean", nextup=nextup_text(),
                           specs={"gap": ("requirements.md",)}),
            self.make_repo("ro-dirty", nextup=None, agentic=False,
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
        one = self.make_repo("only-one", nextup=nextup_text())
        exit_code, output = self.run_main([str(one)])
        self.assertEqual(exit_code, 0)
        lines = output.strip().splitlines()
        rows = [line for line in lines if not line.startswith(" ")]
        self.assertEqual(len(rows), 2)  # header + exactly one repo row
        self.assertIn("only-one", rows[1])

    def test_summary_row_carries_every_column(self):
        repo = self.make_repo(
            "rowcheck", nextup=nextup_text(),
            specs={"feat": ("requirements.md", "design.md", "tasks.md")})
        _, output = self.run_main([str(repo)])
        row = output.splitlines()[1]
        for cell in ("rowcheck", "main", "clean", "2026-07-01", "yes", "LM"):
            self.assertIn(cell, row)
        self.assertIn("specs/feat: requirements.md design.md tasks.md",
                      output)

    def test_prd_only_spec_folder_appears_in_detail_lines(self):
        # PRD agreement-invoice-skills Req 5: PRD-lane folders are visible.
        repo = self.make_repo("prd-lane", nextup=nextup_text(),
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
