"""Backwards-compatibility checks for the Claude Code setup (Req 9.1).

Asserts that scripts/sync-claude.sh still creates the six original
~/.claude symlinks with unchanged sources, and that every pre-feature
skill directory still exists under claude/skills/. New additions (extra
links such as the VS Code prd.agent.md one, or new skills like prd) are
allowed; removals and renames of the originals are not.

Deliberately retired skills are listed in RETIRED_SKILLS and excluded
from the baseline: `sendit` and `transit` were removed when the workflow
reverted to plain approve-and-continue gates and Transit ticket tracking
was dropped from this branch.
"""

import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SYNC_SCRIPT = REPO_ROOT / "scripts" / "sync-claude.sh"
SKILLS_DIR = REPO_ROOT / "claude" / "skills"

# The six original link pairs (target -> source), exactly as they appear
# in scripts/sync-claude.sh before this feature.
ORIGINAL_LINKS = {
    "~/.claude/CLAUDE.md": '"$REPO_CLAUDE_DIR/CLAUDE.md"',
    "~/.claude/agents": '"$REPO_CLAUDE_DIR/agents"',
    "~/.claude/hooks": '"$REPO_CLAUDE_DIR/hooks"',
    "~/.claude/skills": '"$REPO_CLAUDE_DIR/skills"',
    "~/.claude/scripts": '"$REPO_CLAUDE_DIR/../scripts"',
    "~/.claude/rules": '"$REPO_CLAUDE_DIR/rules"',
}

# Skills deliberately removed from this branch. Excluded from the
# baseline below so their absence is an asserted expectation rather than
# a silent gap. Restoring one means deleting it from this list.
RETIRED_SKILLS = [
    "sendit",
    "transit",
]

# Every skill directory that existed under claude/skills/ before the
# toolset-agnostic-starwave feature, minus RETIRED_SKILLS. The feature's
# new skills (prd) are deliberately NOT in this baseline: their presence
# is allowed but not required by this test.
PRE_FEATURE_SKILLS = [
    "blitz-merge",
    "bug-blitz",
    "capture-knowledge",
    "catchup",
    "claude-code-workshop",
    "code-audit",
    "code-simplifier",
    "commit",
    "design-critic",
    "efficiency-optimizer",
    "explain-like",
    "fix-bug",
    "go-test-fixer",
    "make-it-so",
    "next-task",
    "nextup",
    "permission-analyzer",
    "pr-overview",
    "pr-pilot",
    "pr-review-fixer",
    "pr-review-html",
    "pre-push-review",
    "project-init",
    "release-prep",
    "rune",
    "specs-overview",
    "starwave-creating-spec",
    "starwave-design",
    "starwave-requirements",
    "starwave-smolspec",
    "starwave-tasks",
    "swiftui-forms",
    "systematic-debugger",
    "ui-ux-reviewer",
]

# Matches `ln -sfn <source> <target>` where source/target are either a
# double-quoted string or a bare word.
LINK_RE = re.compile(
    r'^\s*ln -sfn\s+("[^"]*"|\S+)\s+("[^"]*"|\S+)\s*$', re.MULTILINE
)


def parse_links(script_text):
    """Return {target: source} for every ln -sfn line in the script."""
    return {target: source for source, target in LINK_RE.findall(script_text)}


class TestSyncScriptCompat(unittest.TestCase):
    def setUp(self):
        self.script_text = SYNC_SCRIPT.read_text()
        self.links = parse_links(self.script_text)

    def test_original_six_links_present_and_unchanged(self):
        for target, source in ORIGINAL_LINKS.items():
            with self.subTest(target=target):
                self.assertIn(
                    target,
                    self.links,
                    f"sync-claude.sh no longer creates the {target} symlink",
                )
                self.assertEqual(
                    source,
                    self.links[target],
                    f"symlink source for {target} changed",
                )

    def test_exactly_six_claude_home_links(self):
        claude_home_targets = [
            t for t in self.links if t.startswith("~/.claude/")
        ]
        self.assertCountEqual(
            claude_home_targets,
            list(ORIGINAL_LINKS),
            "the set of ~/.claude symlink targets changed",
        )


class TestSpecJanitorAgentLink(unittest.TestCase):
    """Pins the VS Code spec-janitor agent symlink (Req 9.1)."""

    def setUp(self):
        self.script_text = SYNC_SCRIPT.read_text()
        self.links = parse_links(self.script_text)

    def test_spec_janitor_agent_link_present_and_unchanged(self):
        target = '"$VSCODE_PROMPTS_DIR/spec-janitor.agent.md"'
        self.assertIn(
            target,
            self.links,
            "sync-claude.sh no longer creates the VS Code "
            "spec-janitor.agent.md symlink",
        )
        self.assertEqual(
            '"$REPO_CLAUDE_DIR/../copilot/agents/spec-janitor.agent.md"',
            self.links[target],
            "symlink source for the VS Code spec-janitor agent changed",
        )


class TestCodexSkillLinks(unittest.TestCase):
    """Req 11: sync exposes repo Agent Skills to Codex via ~/.agents/skills."""

    def run_sync(self, home: Path):
        env = os.environ.copy()
        env["HOME"] = str(home)
        return subprocess.run(
            ["bash", str(SYNC_SCRIPT)],
            cwd=REPO_ROOT,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )

    def repo_skill_names(self):
        return sorted(
            path.name for path in SKILLS_DIR.iterdir() if path.is_dir()
        )

    def test_every_repo_skill_is_linked_for_codex(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            first = self.run_sync(home)
            self.assertIn("Codex skills in ~/.agents/skills:", first.stdout)

            codex_skills = home / ".agents" / "skills"
            for name in self.repo_skill_names():
                with self.subTest(skill=name):
                    target = codex_skills / name
                    self.assertTrue(target.is_symlink())
                    self.assertEqual(os.readlink(target),
                                     str(SKILLS_DIR / name))

            before = {
                name: os.readlink(codex_skills / name)
                for name in self.repo_skill_names()
            }
            second = self.run_sync(home)
            after = {
                name: os.readlink(codex_skills / name)
                for name in self.repo_skill_names()
            }
            self.assertEqual(before, after)
            self.assertIn("skipped conflicts: 0", second.stdout)

    def test_existing_non_matching_codex_skill_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            conflict = home / ".agents" / "skills" / "starwave-design"
            conflict.mkdir(parents=True)
            marker = conflict / "SKILL.md"
            marker.write_text("---\nname: starwave-design\n---\nlocal\n")

            result = self.run_sync(home)

            self.assertFalse(conflict.is_symlink())
            self.assertEqual(marker.read_text(),
                             "---\nname: starwave-design\n---\nlocal\n")
            self.assertIn("Skipped Codex skill link:", result.stdout)
            self.assertIn("skipped conflicts: 1", result.stdout)


class TestPreFeatureSkillsPresent(unittest.TestCase):
    def test_baseline_has_no_duplicates(self):
        self.assertEqual(len(PRE_FEATURE_SKILLS), len(set(PRE_FEATURE_SKILLS)))

    def test_every_pre_feature_skill_directory_exists(self):
        missing = [
            name
            for name in PRE_FEATURE_SKILLS
            if not (SKILLS_DIR / name).is_dir()
        ]
        self.assertEqual(
            [],
            missing,
            f"pre-feature skill directories missing from claude/skills/: {missing}",
        )

    def test_retired_skills_are_absent_and_not_in_baseline(self):
        still_present = [
            name for name in RETIRED_SKILLS if (SKILLS_DIR / name).is_dir()
        ]
        self.assertEqual(
            [],
            still_present,
            "retired skills are back under claude/skills/; remove them from "
            f"RETIRED_SKILLS if that is intended: {still_present}",
        )
        overlap = sorted(set(RETIRED_SKILLS) & set(PRE_FEATURE_SKILLS))
        self.assertEqual(
            [],
            overlap,
            f"skills cannot be both retired and required: {overlap}",
        )


if __name__ == "__main__":
    unittest.main()
