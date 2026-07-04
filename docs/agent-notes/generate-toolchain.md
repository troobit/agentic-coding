# Generate toolchain (scripts/generate.py + scripts/agentic_lib.py)

Python 3 stdlib only (Decision 12). Tests: `python3 -m unittest discover -s tests`
(golden fixtures under `tests/fixtures/`; no test touches real user files —
target paths are injected).

## agentic_lib.py — reusable API (align.py imports this)

- Managed block (Decision 15): `BEGIN_MARKER`/`END_MARKER`,
  `write_managed(path, block, report)` rewrites only the block, preserves
  head/tail content verbatim, and skips+reports a markerless existing file.
  Gotcha: a checked-in generated file that predates markers must be deleted
  once before generation can create it (that is how claude/CLAUDE.md was
  converted).
- Conventions: `build_claude_block` / `build_copilot_block` (conventions +
  wrapper concatenation per Decision 13), `generate_conventions(repo_root, report)`.
- MCP: `load_servers` (drops `_comment` keys), `emit_repo_mcp` (claude shape:
  `mcpServers`), `emit_vscode_mcp` (`servers` + promptString `inputs`),
  `emit_cloud_config`/`emit_cloud_json` (paste-ready, `COPILOT_MCP_*`;
  consumed by align `--cloud-mcp`), `generate_repo_configs(repo, defs, subset, report)`.
- Managed JSON merge `_merge_servers_into`: converges canonical-named entries
  (including ones outside the requested subset — never silently dropped),
  preserves and reports non-canonical entries and unrelated top-level keys;
  invalid JSON → `.bak-<date>` + regenerate + warning that non-canonical
  entries may remain only in the backup.
- Claude user scope: `update_claude_user_config` prefers
  `claude mcp add-json <name> <json> --scope user` when the CLI is on PATH
  (`use_cli=None` autodetects; tests pass `use_cli=False`), else managed merge
  into `~/.claude.json`.
- VS Code settings: `merge_vscode_settings(settings_path, repo_root, report)`
  seeds `chat.instructionsFilesLocations` (repo `copilot/instructions/`) and
  the localml entry under `github.copilot.chat.customOAIModels`
  (`LOCALML_PLACEHOLDER_MODEL_ID` = "REPLACE-WITH-SERVED-MODEL-ID", baseUrl
  `http://127.0.0.1:8080/v1`). Strict JSON only: JSONC/comments → backup +
  report + no write (never clobbered). Never sets `chat.useClaudeMdFile`.

## Secret naming scheme (Req 4.3)

For server `s` with secret `NAME`: claude targets `${S_NAME}` env expansion,
VS Code `${input:s-name}` promptString, cloud `COPILOT_MCP_S_NAME`
(header references get a `$` prefix on cloud, env names do not). A secret
spec that is neither `{"header": ...}` nor `{"env": ...}` aborts generation
naming server + target (`GenerationError`).

## mcp/servers.json facts

- transit is documented, not a placeholder: `http://localhost:3141/mcp`
  (Transit.app built-in MCP server, opt-in via Settings, default port 3141;
  localhost-only so its surfaces exclude "cloud").
- awesome-copilot is vscode-only; devtools has `default_for: ["*"]`,
  svelte `["svelte.config.js"]`.
- Commands are bare PATH-resolved names; a test enforces no `/Users/` paths.
