# align.py tooling (toolset-agnostic-starwave)

## Contract source

`tests/test_align.py` is the executable contract for `scripts/align.py` (task 11).
Its module docstring specifies the expected API exactly: `align.run(repo_path, *,
assume_yes, servers_json, stale_packs_json, seed_root) -> AlignReport` with
`applied` / `changes` / `warnings` / `skipped` / `preserved` fields, plus
`align.AlignError`. Implement against the tests without changing them; the suite
was verified structurally against a stub (every test reaches the `align.run`
call site) before align existed.

Tests are hermetic: they pass a fixture `servers.json` and `seed_root`
(`tests/fixtures/align/`), so they do not depend on stream-1's `mcp/servers.json`
or the real copilot assets. They DO use the real `scripts/stale-packs.json`.

## Non-obvious behaviors the tests pin

- Path portability applies to non-canonical entries too (rtob's real drift is a
  server named `dev-tools` — non-canonical name — with `/Users/ronan/...`); the
  entry is preserved under its name, only the path becomes portable (bare
  command or `$HOME`/`~`-anchored, never the current username substituted).
- MCP convergence also creates missing `.mcp.json` / `.vscode/mcp.json` with the
  manifest's servers (pinned in MissingCloudAssetsTest).
- The zero-stale-pack-matches warning must not fire for align's own seeded
  `.github/agents/prd.agent.md`.
- Stale-pack matching is by SHA-256 against ANY hash in `scripts/stale-packs.json`
  (filenames there are provenance only). janitor/prompt-engineer are byte-identical
  across rtob and workscripts; the other five files have two hashes each.
- Second applying run: `changes` must be empty; `warnings`/`skipped` may repeat
  (e.g. markerless-file skip report, near-miss warning for leftover unmatched
  agent files).
- Plan-only first run (no `.agentic.json`, no `--yes`): `applied` is False,
  `changes` lists the pending fixes, and the ONLY file allowed to change is
  `.agentic.json`.

## Implementation notes (scripts/align.py, task 11)

- align reuses agentic_lib for all managed-block and MCP-merge logic
  (`write_managed`, `generate_repo_configs`, `_backup`, `_write_json`,
  `emit_cloud_json`). Lib functions report plain strings with absolute
  paths; `_harvest()` classifies them into AlignReport buckets by substring
  ("invalid JSON" -> warnings, "preserved non-canonical entries" ->
  preserved, "exists without agentic markers" -> skipped, everything else
  -> changes) and converts paths to repo-relative posix. If agentic_lib's
  report wording changes, `_harvest` must follow.
- Plan-only first run: the pipeline executes for real against a shadow copy
  of ONLY the managed file set (`.mcp.json`, `.vscode/mcp.json`, `.github/`
  tree) in a temp dir. That is how the plan lists pending fixes with zero
  side effects on the target repo.
- JSON validity (step 1) backs up an unparseable file AND unlinks it, so
  the merge in step 3 reports "created" and `_load_json_or_backup` does not
  produce a second backup.
- Path portability rewrites `/Users/<name>` prefixes to `$HOME` recursively
  over string values in the managed JSON. It runs before the MCP merge;
  when a file's only drift is a stale path in a NON-canonical entry, the
  reported change comes solely from the path step (the merge then sees no
  data diff and does not rewrite).
- Seeding: a missing target gets a verbatim copy of the seed file (this
  preserves front matter that lives OUTSIDE the markers, e.g. the
  prd.agent.md YAML header — `write_managed` on a fresh file would drop
  it); an existing marked target gets `write_managed` with the block
  extracted from between the seed source's markers.
- `.github/agents/prd.agent.md` is excluded from stale-pack candidacy
  entirely: never hash-matched, never counted toward the near-miss warning.
- Manifest inference: `"*"` always includes; other `default_for` entries
  are `repo.glob(rule)` against the repo root. `cloud_assets` is inferred
  as False — seeding `.github/` stays an explicit opt-in edit.
- Do NOT `Path.resolve()` when computing repo-relative report paths: macOS
  temp dirs are symlinked (`/var` vs `/private/var`) and agentic_lib logs
  unresolved paths, so resolving one side breaks `relative_to`.
- `--cloud-mcp` reads the manifest subset (or infers it read-only when no
  manifest exists) and prints `lib.emit_cloud_json` — with the real
  `mcp/servers.json` this yields e.g. `$COPILOT_MCP_GITHUB_AUTH_TOKEN` in
  headers.

## Fixture provenance

- `invalid-json/.vscode/mcp.json` is modeled byte-for-byte on the real sanarte
  breakage: a server wrongly keyed `"mcpServers"` plus a trailing comma.
- `stale-agent-pack/.github/agents/` holds real bytes: `janitor.agent.md` from
  rtob, `reviewer.agent.md` from workscripts (exercises the two-hash case).
- `scripts/stale-packs.json` was generated 2026-07-04 from the actual file bytes
  in `/Users/r/repos/rtob` and `/Users/r/repos/workscripts` `.github/agents/`.
  It is a frozen record of known-stale content — append new hashes if more
  drifted copies surface; never rewrite existing ones.
