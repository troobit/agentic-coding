# Copilot Integration (verified 2026-07-04)

Facts verified against live docs/issues during the toolset-agnostic-starwave spec; re-verify anything load-bearing before relying on it months later.

## Surfaces and discovery

- Copilot supports Anthropic's Agent Skills standard natively. VS Code reads `~/.claude/skills` and in-repo `.claude/skills` automatically; the cloud coding agent reads repo-level skill dirs (`.github/skills/` etc.). Same SKILL.md frontmatter; `allowed-tools` vocabulary differs (Copilot documents `shell`/`bash`, not Claude tool names).
- Custom agents are `*.agent.md` (`.chatmode.md` is deprecated). Repo: `.github/agents/`; VS Code user-level: profile `User/prompts/` dir (verify) or `chat.agentFilesLocations`.
- Prompt files (`*.prompt.md`) are IDE-only — not read by Copilot CLI or github.com.
- Copilot CLI config lives in `~/.copilot/`; CLI stopped reading `~/.claude/` in v1.0.61. CLI is out of scope for this repo's setup (Decision 3/10).
- Symlinked skill roots scan correctly as of Copilot CLI 1.0.68 (2026-07-01 changelog); history of breakage before that, and Windows git materializes symlinks as text files.
- Cloud coding agent MCP is configured in github.com repo settings UI with `COPILOT_MCP_*`-prefixed Actions secrets (copilot environment) — no file in the repo delivers it.
- VS Code BYOK: OpenAI-compatible providers configurable via `github.copilot.chat.customOAIModels` / `chatLanguageModels.json`; API key goes to secret storage via prompt (localml accepts any non-empty string). `chat.useClaudeMdFile` exists but must stay off in our setup — it would feed the Claude wrapper to Copilot.

## Executors

- orbit: public, `go install github.com/arjenschwarz/orbit/cmd/orbit@latest`; auto-detects tasks file from branch; `.orbit/run.lock` is per checkout, so parallel orbit runs need one worktree each.
- make-it-so stream branches (`stream/<phase>-<N>`) are repo-global — parallel multi-context execution must context-qualify names.

## Session tooling state (2026-07-04)

- Peer review externals are down on this machine: `gemini` CLI not installed, `codex` returns 401 (needs `codex login`, no `~/.codex/auth.json`). Restoration steps are on bootstrap's manual-auth list (spec task 17).
- Improvement idea (unscheduled): peer-review-validator should detect missing externals immediately and fall back fast instead of spending minutes discovering it.

## Config drift — FIXED in the 2026-07-04 rollout

- `/Users/ronan/...` paths, invalid JSON (sanarte), and 14 stale agent-pack files were fixed by running `scripts/align.py` across rtob, sanarte, workscripts, betscraper, template, and this repo (committed per repo, not pushed). Original broken configs survive as `.bak-2026-07-04` files in rtob/sanarte. Keeping repos aligned is now `make align` / `scripts/align.py <repo>` — see docs/agent-notes/align-tooling.md.
- The rune brew tap (`arjenschwarz/rune`) ships a broken v0.0.0 placeholder — rune installs via `go install github.com/arjenschwarz/rune@latest` (bootstrap does this).
