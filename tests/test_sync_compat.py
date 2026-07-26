"""Backwards-compatibility checks for the Claude Code setup (Req 9.1).

Asserts that scripts/sync-claude.sh still creates the six original
~/.claude symlinks with unchanged sources, and that every pre-feature
skill directory still exists under claude/skills/. New additions (extra
links such as the VS Code prd.agent.md one, or new skills like prd and
engage) are allowed; removals and renames of the originals are not.
"""

import re
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

# Every skill directory that existed under claude/skills/ before the
# toolset-agnostic-starwave feature. The feature's new skills (prd,
# engage) are deliberately NOT in this baseline: their presence is
# allowed but not required by this test.
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
    "sendit",
    "specs-overview",
    "starwave-creating-spec",
    "starwave-design",
    "starwave-requirements",
    "starwave-smolspec",
    "starwave-tasks",
    "swiftui-forms",
    "systematic-debugger",
    "transit",
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


if __name__ == "__main__":
    unittest.main()
