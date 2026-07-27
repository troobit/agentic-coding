# Spec Janitor

Audit-and-repair toolchain for diluted `specs/` directories. Spec: `specs/spec-janitor/`.

## Components

| Piece | Path |
|---|---|
| Skill (8-step workflow) | `claude/skills/spec-janitor/SKILL.md` |
| Mechanical auditor | `claude/skills/spec-janitor/spec_lint.py` (stdlib-only Python 3) |
| Conventions reference (normative rules) | `claude/skills/spec-janitor/references/spec-conventions.md` |
| Report-only cloud/VS Code agent | `copilot/agents/spec-janitor.agent.md` |
| Exclusion store (per target repo) | `specs/.janitor.json` |
| Tests | `tests/test_spec_lint.py` + fixtures in `tests/fixtures/spec_lint/`; janitor cases in `tests/test_align.py`, `tests/test_sync_compat.py` |

The auditor lives inside the skill package so one align seeding entry carries the whole toolchain.

## spec_lint.py CLI and JSON contract

```
spec_lint.py <repo-path> [--json] [--fix] [--fix-dirty]
spec_lint.py <repo-path> exclude (--spec <spec-path> | --finding <finding-id>)
spec_lint.py <repo-path> mark-raised --finding <finding-id>
```

- Exit 0 = no findings (including no `specs/` at all, which prints a notice). **Exit 1 = findings, not failure.** Exit 2 = usage/internal error. Consumers must never abort on exit 1.
- Without `--fix`/`exclude`/`mark-raised` the tool never writes. `--fix` refuses on a dirty `specs/` tree or a non-git directory (no oracle → treated as dirty); `--fix-dirty` overrides. The report is still produced on refusal.
- JSON (`--json`): `version`, `repo`, `rune_available`, `excluded`, `findings[]` with `id`, `rule`, `disposition`, `spec`, `subject`, `evidence[]` (`{file, excerpt}` array), `fix_applied`, `demoted`. The `disposition` enum is closed at three values (`auto-fix` | `gated` | `detect-only`); `demoted: true` marks precondition-failed auto-fixes, it is not a fourth disposition.
- rune verification runs only when `shutil.which("rune")` succeeds; a `rune list` failure becomes SJ-TASK-001 with rune's stderr as evidence. Absent rune → skip note + `rune_available: false`, never an error.
- Spec discovery is janitor-owned, NOT specs-overview's: every leaf directory under `specs/` is audited (dotfolders and the store excluded); a folder with no recognized primary document IS the SJ-MODE-001 finding. specs-overview's discovery requires a recognized document, so it can never see the scratch-folder case.

## Disposition table location

The authoritative rule table (rule ID → detector tier → disposition → repair) lives in two places that a parity test keeps honest:

- `claude/skills/spec-janitor/references/spec-conventions.md` — normative statements, one `**Audit**` line per rule
- `claude/skills/spec-janitor/SKILL.md` — the judgment-rule table and workflow-level handling

`tests/test_spec_lint.py` (RuleIdParityTest) checks both directions between `spec_lint.RULES` and the conventions doc, including disposition agreement. Adding/changing a rule in either place without the other fails `make test`.

Only two rules are auto-fix: SJ-REF-002 (rewrite a single-segment folder-relative `references:` entry to its unique in-folder basename candidate) and SJ-TASK-002 (mint 7-char lowercase alphanumeric stable IDs for unmarked tasks — purely additive). Fix order is REF-002 before TASK-002, one pass, idempotent (re-run is byte-identical).

## Finding identity and exclusion store

Finding id: `"<rule>:<spec_path>:<file>:<subject>"` — no line numbers, so exclusions survive edits. Subjects are slugs/names, not task numbers (insertions renumber siblings). SJ-SUP-001 is emitted once per pair, under the lexicographically first spec path. Findings with identical ids merge into one finding with multiple evidence entries. Specs are named by repo-relative path under `specs/` (nested domains collide on leaf names).

`specs/.janitor.json`: `version`, `exclude_specs`, `exclude_findings`, `raised` (SJ-DRIFT-001 raise-once), `last_run` (feeds the skill's recency scan; fallback 45 days). Contract: **only** the `exclude`/`mark-raised` subcommands write it, schema-validated on write — never hand-edit or hand-merge. A corrupt store is backed up to `.janitor.json.bak-<date>` and rebuilt on the next recording, reported prominently; a plain audit run warns and ignores it but never rewrites it.

## Distribution

- Claude Code / VS Code Copilot: whole-directory `~/.claude/skills` symlink; `scripts/sync-claude.sh` additionally symlinks `copilot/agents/spec-janitor.agent.md` into the VS Code prompts dir (same line pattern as prd.agent.md).
- Cloud agent: `scripts/align.py` seeds `claude/skills/spec-janitor/**` → `.github/skills/spec-janitor/**` and `copilot/agents/spec-janitor.agent.md` → `.github/agents/spec-janitor.agent.md` (repos with `cloud_assets: true` only). Report-only is structural: the agent asset contains no write path.

### Verbatim seeding class (`agentic_lib.seed_verbatim`)

The managed-block mechanism (`write_managed`) is markdown-only by construction — `# `-commented markers re-emitted bare in a `.py` would be a SyntaxError — and `align._seed_file` skips markerless existing targets as hand-written, which would freeze a seeded `spec_lint.py` at its first copy forever. `seed_verbatim(src, dst, report)` exists for tool-owned files that carry no repo-local hand edits by contract: destination missing → copy; identical → unchanged; differing → backup (`.bak-<date>`, the existing `_backup` convention) and re-copy, reported as changed. All janitor seeded files use it; prd's managed-block seeding is untouched. (Decision 10 in the spec's decision log.)

### Stale-pack prune exemption

`_delete_stale_packs` runs before seeding, so seeded agent files under `.github/agents/` would trip the zero-matches warning on every later run. The old single `PRD_AGENT_REL` exemption was generalized to the `SEEDED_AGENT_RELS` frozenset (prd + spec-janitor agents) in `scripts/align.py`. Add any future seeded agent file there or the prune will fight the seeding.

## Gotchas

- The skill runs auto-fix (step 3) before triage (step 5) deliberately: recording exclusions dirties `specs/`, which would then block `--fix`. Ordering is a constraint, not a preference.
- Interactive-entry only: no router (nextup, orbit) dispatches the skill autonomously; headless invocation is out of contract. The cloud surface only ever gets the report-only agent.
- Plain-text `Requirements: 1.1` (no markdown link) is an SJ-TASK-001 structure finding, not an SJ-REF reference finding — the anchor grammar only applies to actual links (`<a name>` anchors or GitHub heading slugs).
- Older specs in this repo commonly use folder-relative `references:` entries (`prd.md` instead of `specs/<name>/prd.md`); these fire SJ-REF-002 and are the auto-fix's main real-world target (seen in the self-audit smoke run).
- Guardrail edits citing SJ rule IDs live in starwave-smolspec, starwave-tasks, fix-bug, next-task and make-it-so. nextup is deliberately excluded — it is a pure router that performs no spec edits.
