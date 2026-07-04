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

## Fixture provenance

- `invalid-json/.vscode/mcp.json` is modeled byte-for-byte on the real sanarte
  breakage: a server wrongly keyed `"mcpServers"` plus a trailing comma.
- `stale-agent-pack/.github/agents/` holds real bytes: `janitor.agent.md` from
  rtob, `reviewer.agent.md` from workscripts (exercises the two-hash case).
- `scripts/stale-packs.json` was generated 2026-07-04 from the actual file bytes
  in `/Users/r/repos/rtob` and `/Users/r/repos/workscripts` `.github/agents/`.
  It is a frozen record of known-stale content — append new hashes if more
  drifted copies surface; never rewrite existing ones.
