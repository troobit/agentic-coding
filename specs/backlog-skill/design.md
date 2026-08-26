# Design: backlog-skill

## Overview

One new skill (`claude/skills/backlog/SKILL.md`) plus surgical changes to the toolchain, the removal of two skills, and a test/fixture rewrite. The skill is LLM-instruction markdown like every other skill in the tree — no new runtime; the executable changes are in `process_status.py`, `align.py`, `sync-claude.sh`, the generated convention text, and four skill files that hard-code the supersede convention.

## Architecture

### Touch map

| Path | Action | Requirements |
|---|---|---|
| `claude/skills/backlog/SKILL.md` | new | 1, 2, 3.6, 4 |
| `claude/skills/nextup/`, `claude/skills/spout/` | delete | 6.1 |
| `README.md` | registry entry swap | 6.1 |
| `nextup.example.md` | delete (same commit as align change) | 6.2 |
| `scripts/align.py` | delete step 6 (see Components) | 6.2 |
| `scripts/process_status.py` | drop nextup columns; add BACKLOG column + schema check; rewrite module docstring and argparse text | 3.5, 6.3 |
| `scripts/sync-claude.sh` | add owned-link prune | 6.4 |
| `shared/conventions.md` | decision_mode rules in Documentation Standards | 5.3, 5.4 |
| `claude/rules/references/decision-log-format.md` | "Revising a decision" section: both modes + manifest read | 5.4 |
| `claude/skills/spec-janitor/SKILL.md` + `references/spec-conventions.md` | decision_mode awareness (its supersede mandate at SKILL.md:97 conflicts with overwrite mode); also reword nextup mention | 5.3, 6.5 |
| `claude/skills/make-it-so/SKILL.md`, `claude/skills/next-task/SKILL.md` | decision_mode awareness in their "Mid-Implementation Spec Edits" clauses (:91, :33) | 5.3 |
| `.gitignore` (this repo) | remove `/nextup.md`, `/SPOUT.md` entries and their comments | 6.5 |
| `tests/`, `tests/fixtures/align/` | rewrite (see Testing) | 6.5 |
| `docs/agent-notes/`, `docs/runbooks/process-onboarding.md`, `scripts/README.md`, `claude/uplift-candidates.md` | purge/rewrite nextup+spout references | 6.5 |

Generated files (`claude/CLAUDE.md`, `copilot/instructions/copilot-instructions.md`, `codex/AGENTS.md`) pick up the conventions change via `make generate`; `make lint-drift` enforces it. Codex additionally reads `~/.codex/AGENTS.md`, written only by `generate.py --user` — a re-run after the conventions change is a rollout step, otherwise Codex sessions keep the old text indefinitely.

### Sunset reference audit (AC 6.5)

The gate is a test that greps **git-tracked files only** (`git ls-files` sourced), case-insensitive `nextup|spout`, exempting `specs/`, `CHANGELOG.md`, the test file itself, and `claude/skills/backlog/SKILL.md` (Decision 15 — that file must name the legacy filenames `nextup.md`/`SPOUT.md` to detect and exclude them, a functional reference rather than leftover debris). Tracked-only is both the correct scope (AC 6.5 concerns the committed toolchain) and what makes the gate stable: untracked working files, the `.worktrees/` sibling checkout, and caches are out by construction. The tracked-tree scope is a superset of AC 6.5's enumerated surfaces — stricter is acceptable.

Work list (every tracked reference at design time):

| Site | Action |
|---|---|
| `tests/fixtures/align/repos/nextup-*` — **8 repos** (canonical, gitignore-append, gitignore-create, markerless, missing, plan-only, session-file, user-zone) + their `.gitignore` files + `seed-root/nextup.example.md` | delete fixtures |
| `tests/test_align.py` (~51 refs) | delete step-6 test classes; keep unrelated convergence tests |
| `tests/test_process_status.py` | rewrite nextup-column assertions to BACKLOG assertions |
| `tests/test_sync_compat.py` | update if it enumerates skills; add prune coverage |
| `scripts/process_status.py` module docstring (:4–16) and argparse description (:252) | rewrite |
| `docs/agent-notes/align-tooling.md`, `process-status.md` | rewrite sections describing step 6 / nextup columns |
| `docs/agent-notes/spec-janitor.md`, `transit-integration.md` | drop or reword passing references |
| `docs/runbooks/process-onboarding.md` | rewrite: onboarding no longer seeds nextup; points at `/backlog` |
| `scripts/README.md` | rewrite align step list and status column description |
| `claude/skills/spec-janitor/SKILL.md` | reword its nextup mention |
| `claude/uplift-candidates.md` | purge or delete (closed historical report) |
| `.gitignore` | remove the nextup/spout entries and comments (dead once the tooling is gone; the sunset commit owns this repo's cleanup — rollout owns other repos') |

## Components and Interfaces

### The /backlog skill

`claude/skills/backlog/SKILL.md`, frontmatter description covering triggers ("add this to the backlog", "capture these notes", "file this idea", bare `/backlog`). Workflow, in order:

1. **Preflight** — `git rev-parse --show-toplevel`; `rune list specs/BACKLOG.md` if the file exists. Parse failure → report and stop; no writes of any kind this run (AC 3.6). Missing rune binary → warn and refuse all BACKLOG.md writes this run (unparseability cannot be detected without the parser); routing into spec files may proceed, and no source is deleted (items destined for the backlog are unhandled, so no source becomes delete-eligible).
2. **Reconcile** (AC 2.6) — for each entry: if its `→ spec:` target exists under `specs/`, or the entry's content is realized in the repo, remove and report. Spec folders are authoritative; `specs/OVERVIEW.md` is a hint only (regenerated on demand, may be stale or absent).
3. **Gather** — free-form argument text; named file paths; bare invocation detects a root `nextup.md` (any tracked status, user zone only — machine markers `<!-- LM -->`, `<!-- ML -->`, `<!-- nextup:machine -->` end the zone; `<!-- USER -->` belongs to it; no marker → whole file) plus untracked/gitignored `*.md` at root and under `specs/` outside spec folders. A **spec folder** is any directory under `specs/` containing at least one of requirements.md, design.md, smolspec.md, prd.md, tasks*.md, or decision_log.md. Excluded from detection: `SPOUT.md` (generated), `specs/BACKLOG.md` and `specs/OVERVIEW.md` (the skill's own artifact and the generated index). Candidates are presented before capture.
4. **Route** (Req 2) — per item, one destination with a one-line reason. Task-file selection: the spec's only task file; else the `tasks-*.md` whose name/stream matches the item, else `tasks.md`; create `tasks.md` if none. Requirement amendments are confirmed per item before writing, never renumber existing anchors, and append a staleness task ("re-run design/tasks for requirement X") to the selected task file.
5. **File** — backlog entries appended to the matching phase, numbered max-existing + 1. File and `specs/` created on first capture.
6. **Clear** (Req 4) — per-source outcome listing (filed/dropped/failed per item), always shown when anything was captured. Tracked sources: marked retained, removal is the user's. Delete-eligible sources: one approval for the batch, then delete. Decline → no source touched.

Contract notes: the skill never runs rune write commands on BACKLOG.md (AC 3.4) — appends and removals are text edits; it never commits. Duplicate detection (AC 1.5/2.6) uses the repo-realization criterion of Decision 13: an item matches if its substance exists in the backlog, a spec document, or shipped work recorded in the repo (code, CHANGELOG) — consumed intent zones are typically realized via commits, not spec text. The match target is always reported.

### BACKLOG.md schema check in process_status.py

Replace the two presence-only nextup columns (`NEXTUP`, `EXAMPLE`: info keys :118–119, assigns :131–132, header :188, `_row` :205–206 — there is no nextup drift wiring to remove) with one `BACKLOG` column: `-` (absent, never drift, AC 3.1), `ok`, or `drift`; a `backlog-drift` flag joins `drift_flags()` with the reason in the repo's detail lines, mirroring `rune-drift`.

The check is a hybrid — each layer covers a hole in the other:

1. **Parse gate**: `_rune_parses` (existing) on `specs/BACKLOG.md`. rune missing → existing warning path, skip.
2. **Phase set/order**: raw-text scan of `^##[ ]` headings, right-trimmed, case-sensitive — must equal exactly `["Idea", "Needs Spec"]`. Raw scan rather than rune's JSON because an empty backlog yields `PhaseMarkers: []` (phases with zero entries are invisible to rune), and an empty-but-valid file is the normal post-reconciliation state. `## idea` is drift.
3. **Unchecked invariant**: `rune list --format json` → `Stats.Pending == Stats.Total`. This is authoritative where a raw checkbox regex is not: rune counts nested subtasks (`  - [x] …`), which a `^- \[` scan misses. (The parse gate has already run, so fenced-content evasion of the raw scans is not possible — rune rejects such files.)
4. **H1 presence**: raw scan for a leading `# ` title (rune parses files without one; AC 3.2 requires it).

Deliberately out of the check's scope: detail-line grammar (source/date/arrow). AC 3.5 enumerates parse failures, phase violations, and non-pending entries; detail-line drift is visible in review diffs and correctable by the skill's next run, and enforcing prose grammar by regex is brittleness without payoff.

### align.py step-6 removal

Delete: `NEXTUP_EXAMPLE` (:90), `NEXTUP_LM_MARKER` (:94), `_ensure_nextup_gitignore` (:346), `_converge_nextup_template` (:371), the call at :420, the seed-root existence error (:548), the "Managed files" docstring list entry (:48), and the step-6 docstring text; renumber the remaining steps. `_shadow_copy` (:443) iterates `MANAGED_JSON + (NEXTUP_EXAMPLE, ".gitignore")` — both `NEXTUP_EXAMPLE` and `".gitignore"` leave the tuple: gitignore management existed only for the nextup entry, so align no longer touches `.gitignore` at all. No replacement behavior: align does not seed or manage BACKLOG.md (AC 3.1).

### sync-claude.sh prune

After the per-skill link loop: for each entry in `~/.agents/skills/` (nullglob-guarded), if it is a symlink (`[ -L ]`) whose literal target string is prefixed by `$REPO_CLAUDE_DIR/skills/` and the target does not exist (`[ ! -e ]`), remove it. Literal prefix comparison suffices — the script only ever creates absolute links (`ln -s "$skill_dir"`). Links resolving elsewhere are never touched (AC 6.4). `~/.claude/skills` is a single whole-directory link and self-heals. Dangling `nextup`/`spout` links already exist on this machine, so the prune has immediate work.

### decision_mode plumbing

Two delivery channels, both required — generated conventions alone do not override skill-local instructions:

- `shared/conventions.md` § Documentation Standards gains the rule: before revising a decision, read `.agentic.json` → `decision_mode`; `overwrite` → edit the entry in place (same ID, new date, no superseding entry); `supersede`/absent → today's behavior. Reaches all three toolchains via generation; this is also how Codex/Copilot learn the mode rules (the deep format reference under `claude/rules/` stays Claude-side — AC 5.4's "all three toolchains" is satisfied by the conventions block they each receive).
- Per-skill edits to every skill whose text mandates supersession: `spec-janitor/SKILL.md:97` and `spec-janitor/references/spec-conventions.md` (its audit must not flag overwrite-mode logs as drift), `make-it-so/SKILL.md:91`, `next-task/SKILL.md:33`. Each gains one sentence deferring to the repo's declared mode.
- `claude/rules/references/decision-log-format.md` gains a "Revising a decision" section describing both modes and the manifest read.

AC 5.3's workflow list is behavior-scoped per Decision 14: the skills whose instructions direct decision-log creation or revision (starwave skills, smolspec, spec-janitor, make-it-so, next-task).

## Data Models

BACKLOG.md grammar (rune-strict; both phases always present in this order, even when empty):

```markdown
# Backlog

## Idea

- [ ] 1. <one-line item>
  - <source>, <YYYY-MM-DD>

## Needs Spec

- [ ] 2. <one-line item>
  - <source>, <YYYY-MM-DD> → spec: <kebab-name>
```

Normative detail-line grammar: exactly one physical line per entry, `- <source>, <date>` with an optional ` → spec: <kebab-name>` suffix that appears on every Needs Spec entry and no Idea entry. `<source>` is the captured file's repo-relative path or `conversation` (AC 3.7); `<date>` is ISO `YYYY-MM-DD`. Entry titles are single lines and may not contain ` → spec: ` (the suffix is parsed from the line end). Numbering is file-global: a new entry takes max-existing + 1, and reconciliation removals never renumber survivors, so gaps are normal. Verified against the installed rune: gapped numbering parses, and rune assigns its own sequential display IDs — the written number is the stable reference.

`.agentic.json`: optional top-level `"decision_mode": "overwrite" | "supersede"`; absent means `supersede`. align preserves unknown keys, so no align change is needed for it.

## Error Handling

| Failure | Behavior |
|---|---|
| BACKLOG.md unparseable at preflight | Report, stop; zero writes (AC 3.6) |
| rune binary missing | Skill: refuse BACKLOG.md writes and source deletion this run; spec-file routing may proceed. process-status: existing warning path |
| Item cannot be routed/filed | Outcome `failed`; its source is never deleted that run (AC 4.3) |
| Tracked-status ambiguity | `git ls-files --error-unmatch <path>` decides; tracked → retained (AC 4.4/4.5) |
| Source deletion fails mid-batch | Report per file; already-filed entries stay (filing is complete before any deletion starts) |

## Testing Strategy

- **test_align.py**: delete the step-6 classes and all 8 nextup fixture repos plus the seed-root template; assert align runs clean against a fixture repo *with* a stray `nextup.example.md` present (align must ignore it — stop-managing means no touch, not delete) and that align no longer writes `.gitignore`.
- **test_process_status.py**: fixture BACKLOG.md variants asserting column value and drift detail — absent (`-`, no drift), valid, **empty-but-valid** (both phases, zero entries → `ok`), gapped numbering (`ok`), U+2192 arrow detail line (`ok`), trailing-whitespace heading (`ok`), rune-unparseable, wrong/extra/case-variant phase, checked entry, **nested checked subtask** (drift via Stats), missing H1. Nextup-column assertions removed.
- **test_sync_compat.py**: dangling owned link (removed), dangling foreign link (kept), live owned link (kept), empty skills dir (no-op).
- **test_generate.py**: golden-file update — the decision_mode rules appear in all three generated outputs.
- **Sunset grep test** (new): `git ls-files` sourced, case-insensitive `nextup|spout`, exempting `specs/`, `CHANGELOG.md`, itself, and `claude/skills/backlog/SKILL.md` (Decision 15); permanent guard against reintroduction.
- The skill itself is instruction markdown — exercised by the rollout migration (rollout.md carries acceptance scenarios for Requirements 1, 2, and 4), not unit tests; the schema check is what keeps skill drift detectable.
- Tasks file: encode the AC 6.6 ordering (skill commit before sunset commit) as rune `blocked-by` dependencies so the sequence is mechanical.

PBT is not warranted: the only parser is rune (external, already trusted), and the schema check's failure space is enumerable and covered by the fixtures above.

## Requirements traceability

| Requirement | Design element |
|---|---|
| 1.1–1.5 | Skill steps 3–5; spec-folder definition; SPOUT/BACKLOG/OVERVIEW exclusions |
| 2.1–2.6 | Skill steps 2, 4; task-file selection rule; amendment confirmation |
| 3.1–3.4, 3.7 | BACKLOG grammar; skill step 5; no-rune-writes contract |
| 3.5 | Hybrid `_backlog_status` check in process_status.py |
| 3.6 | Skill step 1 preflight |
| 4.1–4.5 | Skill step 6 |
| 5.1–5.4 | conventions.md + format reference + per-skill edits (spec-janitor, make-it-so, next-task) |
| 6.1 | skill dir deletions + README |
| 6.2 | align step-6 removal + template deletion, same commit |
| 6.3 | process_status column swap + docstring/argparse rewrite |
| 6.4 | sync-claude.sh prune |
| 6.5 | reference audit table + tracked-files grep gate |
| 6.6 | skill commit precedes sunset commit; encoded as task dependencies |
