#!/bin/bash
# Sync claude configuration files to ~/.claude
# The real files are in this repo's claude/ directory. Agent Skills are
# also linked individually into ~/.agents/skills for Codex, preserving
# any existing user-installed Codex skills.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_CLAUDE_DIR="$(cd "$SCRIPT_DIR/../claude" && pwd)"

# VS Code default-profile prompts directory. User-level custom agents
# (*.agent.md) placed here are discovered by VS Code Copilot. If profile
# discovery fails (e.g. a non-default profile is active, so this User/ dir
# is not the one VS Code reads), set the VS Code setting
# "chat.agentFilesLocations" to include this repo's copilot/agents
# directory as a fallback instead.
VSCODE_PROMPTS_DIR="$HOME/Library/Application Support/Code/User/prompts"
AGENTS_SKILLS_DIR="$HOME/.agents/skills"

# Ensure link-target parent directories exist. On a fresh machine neither
# ~/.claude nor the VS Code User dir exists before first launch. Paths are
# quoted throughout: the space in "Application Support" breaks unquoted
# expansion.
mkdir -p "$HOME/.claude"
mkdir -p "$VSCODE_PROMPTS_DIR"
mkdir -p "$AGENTS_SKILLS_DIR"

# Create symlinks to ~/.claude
ln -sfn "$REPO_CLAUDE_DIR/CLAUDE.md" ~/.claude/CLAUDE.md
ln -sfn "$REPO_CLAUDE_DIR/agents" ~/.claude/agents
ln -sfn "$REPO_CLAUDE_DIR/hooks" ~/.claude/hooks
ln -sfn "$REPO_CLAUDE_DIR/skills" ~/.claude/skills
ln -sfn "$REPO_CLAUDE_DIR/../scripts" ~/.claude/scripts
ln -sfn "$REPO_CLAUDE_DIR/rules" ~/.claude/rules

# Codex Agent Skills: Codex discovers user skills from ~/.agents/skills and
# supports symlinked skill folders. Link per skill so existing curated/user
# skills in that directory are preserved.
codex_linked=0
codex_existing=0
codex_skipped=0
for skill_dir in "$REPO_CLAUDE_DIR/skills"/*; do
    [ -d "$skill_dir" ] || continue
    skill_name="$(basename "$skill_dir")"
    target="$AGENTS_SKILLS_DIR/$skill_name"
    if [ -L "$target" ] && [ "$(readlink "$target")" = "$skill_dir" ]; then
        codex_existing=$((codex_existing + 1))
    elif [ -e "$target" ] || [ -L "$target" ]; then
        echo "Skipped Codex skill link: $target exists and is not this repo's $skill_name skill"
        codex_skipped=$((codex_skipped + 1))
    else
        ln -s "$skill_dir" "$target"
        codex_linked=$((codex_linked + 1))
    fi
done

# Prune dangling owned links: a symlink under ~/.agents/skills whose
# target is one of this repo's skill dirs, but that skill dir no longer
# exists (renamed or removed skill). Foreign links, and links whose
# target still exists, are never touched. Literal prefix comparison is
# sufficient since the loop above only ever creates absolute links.
codex_pruned=0
shopt -s nullglob
for link in "$AGENTS_SKILLS_DIR"/*; do
    [ -L "$link" ] || continue
    link_target="$(readlink "$link")"
    case "$link_target" in
        "$REPO_CLAUDE_DIR/skills/"*)
            if [ ! -e "$link" ]; then
                rm "$link"
                codex_pruned=$((codex_pruned + 1))
            fi
            ;;
    esac
done
shopt -u nullglob

# VS Code Copilot: user-level PRD custom agent (Req 3.1, 3.4)
ln -sfn "$REPO_CLAUDE_DIR/../copilot/agents/prd.agent.md" "$VSCODE_PROMPTS_DIR/prd.agent.md"

# VS Code Copilot: user-level spec-janitor custom agent (Req 9.1)
ln -sfn "$REPO_CLAUDE_DIR/../copilot/agents/spec-janitor.agent.md" "$VSCODE_PROMPTS_DIR/spec-janitor.agent.md"

echo "Symlinked to ~/.claude:"
echo "  CLAUDE.md -> $REPO_CLAUDE_DIR/CLAUDE.md"
echo "  agents/   -> $REPO_CLAUDE_DIR/agents"
echo "  hooks/    -> $REPO_CLAUDE_DIR/hooks"
echo "  skills/   -> $REPO_CLAUDE_DIR/skills"
echo "  scripts/  -> $REPO_CLAUDE_DIR/../scripts"
echo "  rules/    -> $REPO_CLAUDE_DIR/rules"
echo "Symlinked to VS Code profile:"
echo "  $VSCODE_PROMPTS_DIR/prd.agent.md -> $REPO_CLAUDE_DIR/../copilot/agents/prd.agent.md"
echo "  $VSCODE_PROMPTS_DIR/spec-janitor.agent.md -> $REPO_CLAUDE_DIR/../copilot/agents/spec-janitor.agent.md"
echo "Codex skills in ~/.agents/skills:"
echo "  linked: $codex_linked, already linked: $codex_existing, skipped conflicts: $codex_skipped, pruned dangling: $codex_pruned"
