# Codex Sync

## Approach

Keep `claude/skills/` as the source of truth. Move Codex's per-skill linking and
owned dangling-link pruning from `scripts/sync-claude.sh` into the sibling
`scripts/sync-codex.sh`. Only visible directories containing `SKILL.md` qualify;
this excludes downloaded `synced/` containers and `.trash/`. Preserve conflicting
files, directories, and foreign symlinks. Fail on filesystem errors.

Add `generate.py --codex` for Codex user targets only. Extract
`generate_codex_user_configs` in `agentic_lib.py`, shared with `--user`, and honor
`CODEX_HOME` with a `~/.codex` fallback. The sync script invokes this generator
and then links skills. Support `--servers a,b` through the generator. Configuration
selection never changes the user skill location, which remains `~/.agents/skills`.

Canonical server definitions carry an optional `codex_enabled` boolean. Set it
to false for GitHub, Terraform, and Transit and emit
`enabled = false` in their Codex MCP tables. GitHub and Terraform are disabled
by user request; Transit is opt-in because its app is unavailable.
Remove Awesome Copilot entirely and record its retired name so JSON, Claude CLI,
and TOML convergence delete old entries. Keep other definitions for other
clients. Fix TOML section stripping to resume preservation at every unrelated
table, including tables following a
canonical server's nested environment table.

`make sync` runs both scripts; `make sync-claude` and `make sync-codex` run them
independently. Bootstrap runs both before its existing full user generation.
Reuse the existing managed Markdown and TOML writers rather than introducing
another configuration format or an MCP installer.

## Portability assumptions

- Codex supports symlinked skill folders in `$HOME/.agents/skills` and reads
  user MCP configuration from `$CODEX_HOME/config.toml` (default `~/.codex`).
- Skill instructions can name Claude-specific tools. Discovery does not make
  those tools available; Codex follows the existing wrapper's host adaptation rule.
- Shell scripts remain compatible with macOS Bash 3.2. Python uses the standard
  library and retains Python 3.9 compatibility.
- Sync registers services; server dependencies and authentication remain separate.
- The running conversation's skill catalog may require a fresh session to update.
  A fresh native app-server listing verifies host discovery independently.

## Validation

Use temporary homes and a small synthetic repo to cover discovery paths,
non-skill filtering, conflicts, owned pruning, idempotence, custom `CODEX_HOME`,
and separation from Claude/VS Code. Exercise the real Codex app server's
`skills/list` when the CLI is available. Check `codex mcp list` for disabled
GitHub/Terraform and run `make test` and `make lint`.

Document exact Starwave invocation names with `$` and `/skills`. Native listing
must confirm the Starwave entries are enabled; a filesystem check does not
verify the desktop app's slash-menu rendering. Do not rename shared skill names
based on an unverified client-menu filtering assumption.

## Scope

No skill-body rewrites, plugin packaging, server installation, or changes to
unrelated working-tree edits. A dangling `~/.codex/skills -> claude/skills` link
and its `skills.legacy-link` backup are removed, and the directory restored so
Codex can install bundled system skills. Foreign links are left alone. See
Decision 1 for the script boundary.
