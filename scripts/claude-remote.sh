#!/bin/bash
set -e

# Detect sandbox or CI environments
IN_SANDBOX=false
# shellcheck disable=SC2153 # IS_SANDBOX is set by the Claude Code sandbox
# environment itself; it is not a misspelling of the local IN_SANDBOX flag.
if [[ "${CLAUDE_CODE_REMOTE}" == "true" ]] || \
   [[ "${IS_SANDBOX}" == "yes" ]] || \
   [[ "${GITHUB_ACTIONS}" == "true" ]]; then
  IN_SANDBOX=true
fi

if [[ "$IN_SANDBOX" != "true" ]]; then
  exit 0
fi

REPO_DIR="$HOME/.agentic-coding"

if [[ ! -d "$REPO_DIR" ]]; then
  git clone --depth 1 https://github.com/troobit/agentic-coding "$REPO_DIR"
fi

bash "$REPO_DIR/scripts/sync-claude.sh"
