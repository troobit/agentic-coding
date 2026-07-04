# Dependencies for the agentic-coding toolchain, installed by
# scripts/bootstrap.sh via `brew bundle` (Req 8.1).

tap "arjenschwarz/rune"

brew "gh"     # GitHub CLI: auth, PRs, and cloning private repos during bootstrap
brew "uv"     # Python tool runner used by uvx-launched MCP servers and scripts
brew "node"   # provides npx for npx-launched MCP servers
brew "podman" # container runtime for the container-based MCP servers
brew "go"     # `go install` of orbit and mcp-devtools in bootstrap.sh
brew "shellcheck" # required by `make lint` (lint-shell)
brew "arjenschwarz/rune/rune" # rune task CLI (starwave/PRD task files)

# OpenAI Codex CLI — peer review external (peer-review-validator agent).
# Distributed as a Homebrew cask (prebuilt binary from the openai/codex
# releases), not a formula; equivalent to `npm install -g @openai/codex`.
cask "codex"

cask "visual-studio-code" # Copilot surface; its profile User/prompts/ dir receives the PRD agent link
