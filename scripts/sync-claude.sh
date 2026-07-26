#!/bin/bash
# Sync claude configuration files to ~/.claude
# The real files are in this repo's claude/ directory

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_CLAUDE_DIR="$(cd "$SCRIPT_DIR/../claude" && pwd)"

# VS Code default-profile prompts directory. User-level custom agents
# (*.agent.md) placed here are discovered by VS Code Copilot. If profile
# discovery fails (e.g. a non-default profile is active, so this User/ dir
# is not the one VS Code reads), set the VS Code setting
# "chat.agentFilesLocations" to include this repo's copilot/agents
# directory as a fallback instead.
VSCODE_PROMPTS_DIR="$HOME/Library/Application Support/Code/User/prompts"

# Ensure link-target parent directories exist. On a fresh machine neither
# ~/.claude nor the VS Code User dir exists before first launch. Paths are
# quoted throughout: the space in "Application Support" breaks unquoted
# expansion.
mkdir -p "$HOME/.claude"
mkdir -p "$VSCODE_PROMPTS_DIR"

# Create symlinks to ~/.claude
ln -sfn "$REPO_CLAUDE_DIR/CLAUDE.md" ~/.claude/CLAUDE.md
ln -sfn "$REPO_CLAUDE_DIR/agents" ~/.claude/agents
ln -sfn "$REPO_CLAUDE_DIR/hooks" ~/.claude/hooks
ln -sfn "$REPO_CLAUDE_DIR/skills" ~/.claude/skills
ln -sfn "$REPO_CLAUDE_DIR/../scripts" ~/.claude/scripts
ln -sfn "$REPO_CLAUDE_DIR/rules" ~/.claude/rules

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
