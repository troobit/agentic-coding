"""Permanent guard against reintroducing two retired skills (Req 6.5).

Sources its file set from `git ls-files` — tracked files only, so
untracked working files, the .worktrees/ sibling checkout, and caches
are out of scope by construction. Checks each tracked file's path and
its contents case-insensitively against PATTERN: the retired footprint
included fixture directories and files whose *names* carried it as well
as prose and code that merely mentioned it.

Exempt: specs/ and CHANGELOG.md (historical record), this test file
itself, and tests/test_sync_compat.py (its RETIRED_SKILLS list must
name them literally to assert their directories stay gone). Nothing
else is exempt — a tracked file needing to name either one is a
finding, not a case for a new exemption.
"""

import re
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
THIS_FILE = Path(__file__).resolve().relative_to(REPO_ROOT).as_posix()

PATTERN = re.compile(r"nextup|spout", re.IGNORECASE)

EXEMPT_PATH_PREFIXES = ("specs/",)
EXEMPT_FILES = {
    "CHANGELOG.md",
    THIS_FILE,
    "tests/test_sync_compat.py",
}


def _tracked_files():
    """Return repo-relative paths of every git-tracked file."""
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def _is_exempt(rel_path):
    if rel_path in EXEMPT_FILES:
        return True
    return any(rel_path.startswith(prefix) for prefix in EXEMPT_PATH_PREFIXES)


class SunsetGrepTest(unittest.TestCase):
    """AC 6.5: no tracked retired-skill references outside the exempt set."""

    def test_no_tracked_retired_skill_references(self):
        offenders = []

        for rel_path in _tracked_files():
            if _is_exempt(rel_path):
                continue

            if PATTERN.search(rel_path):
                offenders.append(f"{rel_path}: path matches PATTERN")
                continue

            full_path = REPO_ROOT / rel_path
            try:
                raw = full_path.read_bytes()
            except OSError:
                continue  # e.g. a tracked symlink to a missing target
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                continue  # binary file; not a text reference

            if PATTERN.search(text):
                offenders.append(f"{rel_path}: content matches PATTERN")

        self.assertEqual(
            offenders,
            [],
            "Tracked references to a retired skill remain:\n"
            + "\n".join(offenders),
        )


if __name__ == "__main__":
    unittest.main()
