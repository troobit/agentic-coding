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
  `emit_cloud_json`). Lib functions report structured `ReportEntry`
  objects (kind/path/detail); `_harvest()` buckets by `kind` ("warning" ->
  warnings, "preserved" -> preserved, "skipped" -> skipped, "changed" ->
  changes; "unchanged" is dropped) and converts paths to repo-relative
  posix. No string parsing of report lines anywhere.
- Plan-only first run: the pipeline executes for real against a shadow copy
  of ONLY the managed file set (`.mcp.json`, `.vscode/mcp.json`, `.github/`
  tree) in a temp dir. That is how the plan lists pending fixes with zero
  side effects on the target repo.
- JSON validity (step 1) backs up an unparseable file AND unlinks it, so
  the merge in step 3 reports "created" and `_load_json_or_backup` does not
  produce a second backup.
- Path portability rewrites `/Users/<name>` prefixes recursively over
  string values in the managed JSON. Forms: bare command name when the
  string is a user-anchored path whose basename is PATH-resolvable at fix
  time (via `align._which`, monkeypatched in tests for determinism);
  otherwise the per-target home token — `${HOME}/...` in `.mcp.json`,
  `${env:HOME}/...` in `.vscode/mcp.json`. Never bare `$HOME`, never the
  current username. It runs before the MCP merge; when a file's only drift
  is a stale path in a NON-canonical entry, the reported change comes
  solely from the path step (the merge then sees no data diff and does not
  rewrite).
- Step 1 (JSON validity) also treats a parseable non-dict root (top-level
  array) as invalid: backup + unlink, step 3 regenerates (fixture repo
  `non-dict-root`). No AttributeError paths remain for non-object roots.
- Seeding: a missing target gets a verbatim copy of the seed file (this
  preserves front matter that lives OUTSIDE the markers, e.g. the
  prd.agent.md YAML header — `write_managed` on a fresh file would drop
  it); an existing marked target gets `write_managed` with the block
  extracted from between the seed source's markers.
- The REAL seed sources (`copilot/agents/prd.agent.md`,
  `claude/skills/prd/SKILL.md`) carry the agentic markers around the BODY,
  frontmatter outside. Gotcha: the block must sit flush against the markers
  (no blank line after begin / before end — the `write_managed` normal
  form), or the run after a verbatim seed rewrites the block once.
  `SeedSourceMarkerTests` in test_generate.py pins both properties.
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
  headers. User-facing steps (paste location on github.com, `copilot`
  environment secrets) live in `docs/runbooks/cloud-agent-mcp.md`; with the
  current canonical set `COPILOT_MCP_GITHUB_AUTH_TOKEN` is the only secret
  name. Note `make align` passes no repo argument, so runbooks document the
  direct `python3 scripts/align.py <repo>` invocation.

## Nextup-template step (PRD nextup-starwave-refinement)

Pipeline step 6, `_converge_nextup_template`, runs unconditionally (not gated
on `cloud_assets`) after the other five steps:

- A repo without `nextup.example.md` gets a verbatim `shutil.copy2` of the
  canonical copy at the seed root (`REPO_ROOT/nextup.example.md` by default;
  `--seed-root` overrides, and align errors if the seed root lacks the file
  or the canonical copy lacks the `<!-- LM -->` marker).
- An existing `nextup.example.md` is split at the FIRST `<!-- LM -->` marker:
  the user zone (everything above the marker) is preserved byte-for-byte, and
  the machine zone (marker down) is replaced with the canonical machine zone.
  No write happens when the merge equals the existing bytes, so a converged
  file reports no change.
- A markerless `nextup.example.md` is treated as hand-written: reported under
  `skipped`, never overwritten — same contract as markerless cloud assets.
- Either way the step ensures the target's `.gitignore` has a `nextup.md`
  entry (`nextup.md` or `/nextup.md` both count as present); it appends one
  line when missing and creates `.gitignore` containing just that line when
  absent.
- The target's `nextup.md` is NEVER created, modified, or deleted. It is
  session-local state (gitignored by the entry above): the first `/nextup`
  session seeds it from `nextup.example.md`, and after that it holds live
  user instructions plus the machine-zone progress record — align clobbering
  it would destroy in-flight session state.
- Plan-only support: `_shadow_copy` includes `nextup.example.md` and
  `.gitignore` in the managed file set it copies, so a first run without
  `--yes` plans the seed/convergence and gitignore fix against the shadow
  with zero target-side effects (only `.agentic.json` is written).

## Fixture provenance

- `invalid-json/.vscode/mcp.json` is modeled byte-for-byte on the real sanarte
  breakage: a server wrongly keyed `"mcpServers"` plus a trailing comma.
- `stale-agent-pack/.github/agents/` holds real bytes: `janitor.agent.md` from
  rtob, `reviewer.agent.md` from workscripts (exercises the two-hash case).
- `scripts/stale-packs.json` was generated 2026-07-04 from the actual file bytes
  in `/Users/r/repos/rtob` and `/Users/r/repos/workscripts` `.github/agents/`.
  It is a frozen record of known-stale content — append new hashes if more
  drifted copies surface; never rewrite existing ones.

## Gitignore interaction

A repo that blanket-ignores `.vscode/` ends up with an on-disk but uncommitted `.vscode/mcp.json` after align (align does not force-add against ignore rules). The fix is the standard selective pattern — `.vscode/*` plus `!.vscode/settings.json`, `!tasks.json`, `!launch.json`, `!extensions.json`, `!mcp.json` — applied to betscraper on 2026-07-05. Check for this whenever align reports a written-but-untracked `.vscode/mcp.json`.
