# Dependencies for the agentic-coding toolchain, installed by
# scripts/bootstrap.sh via `brew bundle` (Req 8.1).
#
# rune is intentionally NOT installed via brew: the arjenschwarz/rune tap
# formula is a broken v0.0.0 placeholder (its tarball 404s), and modern
# `brew bundle` fetches everything up front and installs NOTHING if any
# fetch fails — so the broken formula blocked every other entry here.
# bootstrap.sh installs rune with `go install` alongside orbit instead.
# (No third-party taps remain; if one is ever added, see the tap-trust
# note above the brew bundle step in scripts/bootstrap.sh.)

brew "gh"     # GitHub CLI: auth, PRs, and cloning private repos during bootstrap
brew "uv"     # Python tool runner used by uvx-launched MCP servers and scripts
brew "node"   # provides npx for npx-launched MCP servers
brew "podman" # container runtime for the container-based MCP servers
brew "go"     # `go install` of orbit, mcp-devtools, and rune in bootstrap.sh
brew "shellcheck" # required by `make lint` (lint-shell)

# OpenAI Codex CLI — peer review external (peer-review-validator agent).
# Distributed as a Homebrew cask (prebuilt binary from the openai/codex
# releases), not a formula; equivalent to `npm install -g @openai/codex`.
cask "codex"

cask "visual-studio-code" # Copilot surface; its profile User/prompts/ dir receives the PRD agent link
