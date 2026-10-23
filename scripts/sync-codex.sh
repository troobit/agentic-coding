#!/bin/bash
# Sync repo Agent Skills, user instructions, and MCP settings for Codex.
# Usage: scripts/sync-codex.sh [--servers a,b]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_SKILLS_DIR="$REPO_ROOT/claude/skills"
AGENTS_SKILLS_DIR="$HOME/.agents/skills"

for arg in "$@"; do
    case "$arg" in
        -h|--help) exec python3 "$SCRIPT_DIR/generate.py" --codex --help ;;
    esac
done

# Reuse the managed writers, without touching Claude or VS Code files.
# Validate generator arguments before creating skill links.
python3 "$SCRIPT_DIR/generate.py" --codex "$@"

# A previous manual setup left this exact relative link dangling.
# Remove it (and its old backup) so bundled Codex skills can install.
CODEX_CONFIG_DIR="${CODEX_HOME:-$HOME/.codex}"
for legacy_link in "$CODEX_CONFIG_DIR/skills" "$CODEX_CONFIG_DIR/skills.legacy-link"; do
    if [ -L "$legacy_link" ] && [ ! -e "$legacy_link" ] \
        && [ "$(readlink "$legacy_link")" = "claude/skills" ]; then
        rm "$legacy_link"
        echo "Removed broken legacy skills link: $legacy_link"
    fi
done
mkdir -p "$CODEX_CONFIG_DIR/skills"

mkdir -p "$AGENTS_SKILLS_DIR"

linked=0
existing=0
skipped=0
for skill_dir in "$REPO_SKILLS_DIR"/*; do
    [ -d "$skill_dir" ] && [ -f "$skill_dir/SKILL.md" ] || continue
    skill_name="$(basename "$skill_dir")"
    target="$AGENTS_SKILLS_DIR/$skill_name"
    if [ -L "$target" ] && [ "$(readlink "$target")" = "$skill_dir" ]; then
        existing=$((existing + 1))
    elif [ -e "$target" ] || [ -L "$target" ]; then
        echo "Skipped Codex skill link: $target exists and is not this repo's $skill_name skill"
        skipped=$((skipped + 1))
    else
        ln -s "$skill_dir" "$target"
        linked=$((linked + 1))
    fi
done

# Remove only dangling links into this repo's source directory.
pruned=0
shopt -s nullglob
for link in "$AGENTS_SKILLS_DIR"/*; do
    [ -L "$link" ] || continue
    link_target="$(readlink "$link")"
    case "$link_target" in
        "$REPO_SKILLS_DIR/"*)
            if [ ! -e "$link" ]; then
                rm "$link"
                pruned=$((pruned + 1))
            fi
            ;;
    esac
done

echo "Codex skills in $AGENTS_SKILLS_DIR:"
echo "  linked: $linked, already linked: $existing, skipped conflicts: $skipped, pruned dangling: $pruned"
