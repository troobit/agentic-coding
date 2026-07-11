# Bootstrap, Brewfile, Makefile, and sync-claude.sh

## bootstrap.sh

- One-script new-machine setup (Req 8); order is fixed by design.md's
  Bootstrap section: Homebrew → `brew bundle` → Claude Code installer →
  `go install` orbit + mcp-devtools + rune → `mkdir -p` targets → `sync-claude.sh`
  → `generate.py --user` → remove stale `~/.copilot/agents/prd.agent.md`
  → print manual auth steps, ending with "re-run scripts/bootstrap.sh after
  authenticating".
- No `set -e`: per-step failures are reported (`FAILED:`) and independent
  later steps still run; exit code is 1 if anything hard-failed. Steps
  blocked on missing auth use `skip_for_auth`, which both reports the skip
  and appends the redo instruction to the manual-steps list.
- Every step prints exactly one of `did:` / `already done:` / `skipped:` /
  `dry-run: would ...` — a second run on a configured machine is all
  `already done` (plus generate.py's own "no changes").
- `--dry-run` mutates nothing. The only commands it runs are read-only
  probes (`command -v`, `brew bundle check`, `go env GOPATH`).
- Module paths: orbit `github.com/arjenschwarz/orbit/cmd/orbit@latest`;
  mcp-devtools `github.com/sammcj/mcp-devtools@latest` (main package at the
  module root — verified against its go.mod 2026-07-04; upstream README
  suggests `@HEAD`, `@latest` works); rune
  `github.com/arjenschwarz/rune@latest` (main package at the module root,
  public tags up to v1.3.0 — verified 2026-07-04). rune moved here from the
  Brewfile because its brew tap formula is broken (see Brewfile section).
  Go tools are skipped as `already done` when the binary is on PATH or in
  `$(go env GOPATH)/bin` — bootstrap does not upgrade them; re-run
  `go install` manually for that.
- Step 4b (agreement-invoice-skills Req 3): when `which rune` fails but a
  local build exists at `~/repos/rune/rune`, symlink it into
  `~/.local/bin/rune` (`ln -sfn`; a matching existing symlink reports
  `already done`, and a PATH note prints if `~/.local/bin` is not on PATH).
  Runs after the go_tool calls, so `go install` remains the fresh-machine
  path and the symlink only covers the local-dev-build case.
- Homebrew discovery checks PATH then `/opt/homebrew/bin/brew` and
  `/usr/local/bin/brew` (fresh installs aren't on PATH yet); after the
  Homebrew step it `eval "$($BREW shellenv)"` so the rest of the run sees
  brew and everything brew bundle installed.
- All JSON work (user MCP configs, VS Code settings merge) is delegated to
  `generate.py --user` per Decision 12 — the shell only mkdirs, symlinks
  (via sync-claude.sh), and removes the one known stale file.
- `make bootstrap` wraps it. shellcheck 0.11.0 is installed (via the
  Brewfile) and `make lint` passes clean; claude-remote.sh carries a
  justified `shellcheck disable=SC2153` (`IS_SANDBOX` is an env var set by
  the sandbox environment, not a typo of the local `IN_SANDBOX` flag).
- The manual-steps list includes `export GITHUB_AUTH_TOKEN="Bearer <PAT>"`
  for the github MCP server (Claude expands it from the environment); the
  VS Code prompt input takes the same `Bearer <PAT>` value (its
  description in mcp/servers.json says so).

## Brewfile

- Installed by `scripts/bootstrap.sh` via `brew bundle` (Req 8.1 of toolset-agnostic-starwave).
- Includes `shellcheck` because `make lint` (lint-shell) hard-fails without it.
- OpenAI Codex CLI is a Homebrew **cask** named `codex` (prebuilt binary from openai/codex releases) — there is no formula. Verified 2026-07-04.
- rune, orbit, and mcp-devtools are NOT brew — bootstrap `go install`s them (hence `brew "go"`). rune was originally in the Brewfile via the `arjenschwarz/rune` tap, but that formula is a broken v0.0.0 placeholder whose tarball 404s (found in the first real bootstrap run 2026-07-04).
- Modern `brew bundle` is **all-or-nothing**: it fetches every formula/cask up front and installs NOTHING if any fetch fails. The broken rune formula therefore also blocked shellcheck and everything else. Do not assume brew bundle continues past individual failures — it doesn't.
- The Brewfile currently has no third-party taps. If one is ever added, bootstrap must `brew tap` it and `brew trust` it (guarded — `brew trust` only exists on newer brew) before `brew bundle`, or the untrusted-tap failure blocks the whole bundle. The pattern is documented in a comment above the brew bundle step in bootstrap.sh.

## Makefile

- `lint` = `lint-shell` (shellcheck on `scripts/*.sh`, hard-fails if shellcheck is not installed) + `lint-drift`.
- `lint-drift` avoids needing a temp-output flag on generate.py: it snapshots the two checked-in generated files, runs `python3 scripts/generate.py` in place, diffs, then always restores the snapshots — so a drifting lint run never leaves the working tree modified.
- `generate`/`align` reference `scripts/generate.py` and `scripts/align.py` by path; those are owned by other streams of the feature.

## sync-claude.sh

- The six original `~/.claude` symlink lines must stay byte-for-byte identical (Req 9.1). `tests/test_sync_compat.py` enforces the exact target->source map (and that no seventh `~/.claude/*` link appears) plus the presence of every pre-feature skill directory.
- New: `mkdir -p` for `$HOME/.claude` and the VS Code prompts dir (fresh machine: neither exists), and a symlink `"$HOME/Library/Application Support/Code/User/prompts/prd.agent.md"` -> repo `copilot/agents/prd.agent.md`. The space in "Application Support" means every use must be quoted.
- If VS Code profile discovery fails (non-default profile active), the fallback is the `chat.agentFilesLocations` setting pointing at the repo's `copilot/agents/` dir — documented in the script header comment.
- The link target `copilot/agents/prd.agent.md` may not exist yet (created by another stream); `ln -sfn` happily creates a dangling link, which resolves once the file lands.
