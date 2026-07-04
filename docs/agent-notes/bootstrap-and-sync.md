# Bootstrap, Brewfile, Makefile, and sync-claude.sh

## Brewfile

- Installed by `scripts/bootstrap.sh` via `brew bundle` (Req 8.1 of toolset-agnostic-starwave).
- OpenAI Codex CLI is a Homebrew **cask** named `codex` (prebuilt binary from openai/codex releases) — there is no formula. Verified 2026-07-04.
- rune comes from the `arjenschwarz/rune` tap; orbit and mcp-devtools are NOT brew — bootstrap `go install`s them (hence `brew "go"`).

## Makefile

- `lint` = `lint-shell` (shellcheck on `scripts/*.sh`, hard-fails if shellcheck is not installed) + `lint-drift`.
- `lint-drift` avoids needing a temp-output flag on generate.py: it snapshots the two checked-in generated files, runs `python3 scripts/generate.py` in place, diffs, then always restores the snapshots — so a drifting lint run never leaves the working tree modified.
- `generate`/`align` reference `scripts/generate.py` and `scripts/align.py` by path; those are owned by other streams of the feature.

## sync-claude.sh

- The six original `~/.claude` symlink lines must stay byte-for-byte identical (Req 9.1). `tests/test_sync_compat.py` enforces the exact target->source map (and that no seventh `~/.claude/*` link appears) plus the presence of every pre-feature skill directory.
- New: `mkdir -p` for `$HOME/.claude` and the VS Code prompts dir (fresh machine: neither exists), and a symlink `"$HOME/Library/Application Support/Code/User/prompts/prd.agent.md"` -> repo `copilot/agents/prd.agent.md`. The space in "Application Support" means every use must be quoted.
- If VS Code profile discovery fails (non-default profile active), the fallback is the `chat.agentFilesLocations` setting pointing at the repo's `copilot/agents/` dir — documented in the script header comment.
- The link target `copilot/agents/prd.agent.md` may not exist yet (created by another stream); `ln -sfn` happily creates a dangling link, which resolves once the file lands.
