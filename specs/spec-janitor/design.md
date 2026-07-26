# Design: Spec Janitor

## Overview

An audit-and-repair toolchain for diluted `specs/` directories: a stdlib-Python mechanical auditor, a `/spec-janitor` skill layering judgment audit and gated repair on top of it, a normative conventions reference both derive from, and guardrail edits to the skills that create the observed dilution patterns. Distributed via the skills symlink for Claude Code / VS Code Copilot and align.py seeding for the cloud agent — with a new verbatim-seeding class, because the managed-block mechanism is markdown-only by construction.

## Architecture

### Components and placement

| Component | Path | Notes |
|---|---|---|
| Skill | `claude/skills/spec-janitor/SKILL.md` | Skill name `spec-janitor` (unnamespaced — serves both lanes plus bugfixes, like `specs-overview`) |
| Mechanical auditor | `claude/skills/spec-janitor/spec_lint.py` | Lives inside the skill package so one seeding entry carries the whole toolchain (Req 9.4); stdlib only |
| Conventions reference | `claude/skills/spec-janitor/references/spec-conventions.md` | Normative rules with stable IDs (Req 7); travels with the skill |
| Copilot agent | `copilot/agents/spec-janitor.agent.md` | Cloud/VS Code custom agent; report-only by construction (Req 9.2) |
| Exclusion store | `specs/.janitor.json` in each target repo | Committed; dotfile, outside spec discovery (Req 5.5); machine-written only (see store contract) |
| align/lib changes | `scripts/align.py`, `scripts/agentic_lib.py` | Verbatim-seed class, seeding pairs, stale-pack prune exclusion |
| Sync change | `scripts/sync-claude.sh` | Symlink `spec-janitor.agent.md` into the VS Code prompts dir (same line pattern as prd) |
| Tests | `tests/test_spec_lint.py`, additions to `tests/test_align.py`, `tests/test_sync_compat.py` | Fixtures under `tests/fixtures/spec_lint/` |

### Distribution and surface capability matrix (Req 9)

| Surface | Delivery | Capability |
|---|---|---|
| Claude Code | `~/.claude/skills` symlink (whole-directory; no sync change needed for the skill itself) | Full: audit, auto-fix, gated repair, exclusion triage |
| VS Code Copilot | Same symlink for the skill; `sync-claude.sh` gains one symlink line for the agent file | Full |
| Cloud coding agent | align.py seeding: `claude/skills/spec-janitor/**` → `.github/skills/spec-janitor/**`, `copilot/agents/spec-janitor.agent.md` → `.github/agents/spec-janitor.agent.md` | Report-only: the agent asset only ever runs `spec_lint.py` without `--fix` (Req 9.2) |

**Verbatim seeding class (new).** `agentic_lib.write_managed` reconstructs managed blocks in a way that only works for markdown (`# `-commented markers in a `.py` would be re-emitted bare at column 0 — a SyntaxError), and `align._seed_file` skips markerless existing targets as hand-written — so a seeded `spec_lint.py` would freeze at its first copy. Fix: a `seed_verbatim(src, dst, report)` helper in `agentic_lib` for tool-owned files — dst missing → copy; dst == src → unchanged; dst differs → back up (`.bak-<date>`, same convention as align's JSON-validity step) and re-copy, reported as changed. All `spec-janitor` seeded files are tool-owned and use verbatim seeding (declared in the seeding pair list); prd's managed-block seeding is untouched. Rationale: janitor assets carry no repo-local hand edits by contract — the conventions reference and script must be identical on every surface.

**Stale-pack prune exclusion.** `_delete_stale_packs` currently exempts only `PRD_AGENT_REL`; it runs before seeding, so a seeded `.github/agents/spec-janitor.agent.md` would trigger the zero-matches warning on every later run. Change: generalize the exemption to a `SEEDED_AGENT_RELS` set containing both agent paths. Regression test added; existing tests unmodified.

The janitor is an interactive-entry skill: no router (nextup, engage, orbit) dispatches it autonomously, and the cloud surface reaches it only through the report-only agent asset. Headless invocation of the full skill is out of contract; SKILL.md states this.

### Conventions reference (Req 7)

`spec-conventions.md` defines rules with stable IDs, grouped by family. Rule IDs are the shared vocabulary across the auditor's output, the skill's findings, exclusion keys, and guardrail citations.

| Family | Covers |
|---|---|
| `SJ-MODE-*` | Spec modes and canonical files. Mode is recognized from primary documents alone — full: requirements.md+design.md; smol: smolspec.md; PRD lane: prd.md; bugfix: report.md (optional solution-comparison.md). Task files are checked *after* mode recognition (a full spec missing tasks.md is `SJ-MODE-002`, not unrecognized). Recognized extras: implementation.md, review-*.md, prerequisites.md, verification reports |
| `SJ-REF-*` | Cross-reference integrity: task requirement anchors, `references:` front-matter, anchor grammar |
| `SJ-TASK-*` | Task-file structure: front-matter, phase H2s, `- [ ] N. Title <!-- id:x -->`, `Blocked-by:`/`Stream:`/`Requirements:` metadata, sequential numbering, uniform schema within a file, the stable-ID format (rune's exhibited scheme: 7-char lowercase alphanumeric; normative here, verified by rune round-trip when rune is present) |
| `SJ-SUP-*` | Supersession: direction changes mark discarded sections superseded; superseding and superseded specs reference each other; decision-log status annotations |
| `SJ-FILE-*` | Filing: one feature per kebab-case folder; bugs under `specs/bugfixes/`; non-bug work never under bugfixes; scratch files discouraged |
| `SJ-DRIFT-*` | Benign drift definitions (older ID styles, casing variance) — tolerated in completed specs, raised at most once |

Contract: every rule ID emitted by `spec_lint.py` exists in the conventions reference and vice versa for mechanical rules; pinned by a parity test (Req 7.2).

### Spec discovery (janitor-owned)

The janitor does **not** reuse specs-overview's discovery (that definition requires at least one recognized document, so a folder of scratch files would never be visited — exactly the `SJ-MODE-001` target). Janitor rule: **every leaf directory under `specs/`** is audited, excluding dotfolders (`.orbit`, etc.) and the exclusion store; containing no recognized primary document *is* the `SJ-MODE-001` finding. `specs/bugfixes/*` is checked against the bugfix shape; a bugfix-shaped folder outside `bugfixes/` is visible to `SJ-FILE-001`. Nested domains supported; a spec is always named by its repo-relative path under `specs/` (e.g. `estimation/pipeline`) in findings, exclusions, and reports — leaf names alone collide across domains (Req 1.7).

### Finding model and disposition table (Req 3)

Finding identity (Req 5.4): `"<rule>:<spec_path>:<file>:<subject>"` — no line numbers. Findings that would produce an identical id are merged into one finding with multiple evidence entries. `subject` per family:

| Rule | `subject` |
|---|---|
| `SJ-REF-*` | The broken reference text verbatim |
| `SJ-TASK-001/002` | Task-file name |
| `SJ-TASK-003` | Kebab-slug of the out-of-order task's title (not its number — insertions renumber siblings) |
| `SJ-MODE-*` | Folder path, or missing/malformed file name |
| `SJ-SUP-001` | The *other* spec's path; the finding is emitted once, under the lexicographically first spec path of the pair (canonical ordering — one identity per pair) |
| `SJ-SUP-002` | Kebab-slug of the contradicted section heading as of detection; if a repair renames that heading, the finding is re-keyed, which is correct — the old finding was resolved |
| `SJ-SCOPE-001` | Task-file name |
| `SJ-GHOST-001` | Kebab-slug of the referenced unspecced work (e.g. `enterprise-assessment-migration`) |
| `SJ-FLOW-001` | The literal `abandoned` |
| `SJ-FILE-001` | The misfiled path |
| `SJ-DRIFT-001` | Kebab-slug of the drift kind (e.g. `bare-numeric-ids`) |

| Rule (finding type) | Detector | Disposition | Repair (if any) |
|---|---|---|---|
| `SJ-REF-001` dangling task requirement anchor | lint | **gated** | Retargeting requires deciding intent |
| `SJ-REF-002` `references:` entry points at missing file | lint | **auto-fix**, preconditions: the entry has no path separator beyond the spec folder (single-segment, folder-relative) AND exactly one existing file in the same leaf folder has that basename | Rewrite to the unique candidate; cross-folder references or multiple candidates demote to gated (Req 3.3) |
| `SJ-TASK-001` task file violates structure rules | lint | **detect-only** | Reconstruction is never deterministic |
| `SJ-TASK-002` mixed stable-ID presence | lint | **auto-fix** | Mint unique IDs for unmarked tasks only — purely additive, rewrites nothing. Format per `SJ-TASK-*`; when rune is present, the fixed file must round-trip `rune list` (pinned by test) |
| `SJ-TASK-003` out-of-sequence numbering | lint | **detect-only** | Renumbering rewrites identifiers referenced from commits/logs |
| `SJ-MODE-001` folder matches no recognized mode | lint | **detect-only** | Needs authored content or a gated move |
| `SJ-MODE-002` recognized mode missing its task file | lint | **detect-only** | Task authoring belongs to tasks/engage, proposed as follow-up |
| `SJ-MODE-003` bugfix entry not matching report shape | lint | **detect-only** | — |
| `SJ-SUP-001` duplicate / silently superseding specs | skill | **gated** | Cross-annotation both directions (Req 6.3) |
| `SJ-SUP-002` internal contradiction after direction change | skill | **gated** | Mark superseded sections; never delete (Req 3.5) |
| `SJ-SCOPE-001` task-file scope ≠ spec document scope | skill | **gated** | Options: extend spec doc, or split/annotate task file |
| `SJ-GHOST-001` spec references unspecced work | skill | **detect-only** | Report proposes a follow-up spec |
| `SJ-FLOW-001` spec abandoned mid-workflow | skill | **gated** | Annotate abandoned/superseded, or queue completion |
| `SJ-FILE-001` mis-filed item | skill | **gated** (move) | Move + inbound-reference rewrite in the same batch (Req 3.6) |
| `SJ-DRIFT-001` benign drift in completed spec | skill | **detect-only**, raise-once reporting via `raised` (Req 5.6) | Normalization only as a gated repair the user requests |

Auto-fix eligibility (refines Req 3.2's wording, amendment noted at the gate): a single transformation that is *deterministic or purely additive*, and rewrites no identifier referenced from elsewhere. Exactly two rules qualify; `detect-once` is not a fourth disposition — `SJ-DRIFT-001` is detect-only with raise-once reporting, and the JSON `disposition` enum stays closed at three.

## Components and Interfaces

### spec_lint.py

```
spec_lint.py <repo-path> [--json] [--fix] [--fix-dirty]
spec_lint.py <repo-path> exclude (--spec <spec-path> | --finding <finding-id>)
spec_lint.py <repo-path> mark-raised --finding <finding-id>
```

- Exit 0: no findings (including no-`specs/`, which prints a notice — Req 1.8). Exit 1: findings. Exit 2: usage/internal error. Consumers (cloud agent, skill) treat exit 1 as success-with-findings.
- Default output: human-readable report grouped by spec, each finding tagged with rule ID and disposition. `--json`: schema below.
- `--fix`: applies auto-fix findings whose preconditions hold; refuses (report + warning) when `git status --porcelain -- specs/` is non-empty or the directory is not a git repo (no oracle → treat as dirty), unless `--fix-dirty` (Req 4.2). Without `--fix`/`exclude`/`mark-raised`, the tool never writes (Req 4.1).
- `exclude` / `mark-raised` subcommands are the **only** writers of `specs/.janitor.json` — the store is machine-written and schema-validated, never hand-merged by the skill (prevents silent store corruption). Interactive surfaces only; the cloud agent asset never invokes them.
- rune verification (Req 1.3): if `shutil.which("rune")`, run `rune list <file>` per task file; failure adds `SJ-TASK-001` with rune's stderr as evidence. Absent → report line "rune verification skipped", JSON `rune_available: false`.
- Anchor grammar for `SJ-REF-001` (Req 1.1): markdown links targeting `<file>.md#<fragment>`; a fragment resolves via `<a name="...">` or GitHub heading slug. Plain-text `Requirements: 1.1` without links is a structure concern (`SJ-TASK-001` family), not a reference check.
- Ordering/idempotence: detection on a snapshot read; fixes computed then applied in one pass, `SJ-REF-002` before `SJ-TASK-002`. Immediate re-run: no findings for fixed items, no writes (Req 4.3); pinned by tests.

### JSON output schema (Req 1.6)

```json
{
  "version": 1,
  "repo": "<abs path>",
  "rune_available": true,
  "excluded": {"specs": ["..."], "findings": ["..."]},
  "findings": [
    {
      "id": "SJ-REF-002:sdd-ui:tasks-agent-bridge.md:requirements.md#1.1",
      "rule": "SJ-REF-002",
      "disposition": "auto-fix",
      "spec": "sdd-ui",
      "subject": "requirements.md#1.1",
      "evidence": [{"file": "specs/sdd-ui/tasks-agent-bridge.md", "excerpt": "..."}],
      "fix_applied": false,
      "demoted": false
    }
  ]
}
```

- `evidence` is an array — judgment findings quote from multiple files (Req 2.5).
- `demoted: true` marks precondition-failed auto-fixes for the skill's gated batches (Req 3.3).
- Judgment findings (skill-produced) use the same shape plus optional fields: `related_spec` (SJ-SUP-001 pair), `active` (touched since last run — Req 2.6), `pattern` (named drift-production pattern, e.g. `autonomous-run-layering`), `proposal` (repair or follow-up text). The skill emits them into its report in this model so exclusions and triage use one vocabulary; they are not produced by `spec_lint.py`.

### Exclusion store — `specs/.janitor.json` (Req 5)

```json
{
  "version": 1,
  "exclude_specs": ["textspinner"],
  "exclude_findings": ["SJ-TASK-003:contactsimplifier:tasks.md:post-implementation"],
  "raised": ["SJ-DRIFT-001:initial-version:tasks.md:bare-numeric-ids"],
  "last_run": "2026-07-26"
}
```

- Spec names are repo-relative paths under `specs/`. `raised` implements raise-once (Req 5.6); `last_run` feeds the recency default.
- Corrupt store: backed up to `.janitor.json.bak-<date>` and rebuilt from the current session's recordings, reported prominently (mirrors align's JSON-validity convention). Never silently dropped.
- Written only via the `exclude`/`mark-raised` subcommands during interactive triage; committed with the repo.

### SKILL.md workflow

1. **Preflight** — confirm `specs/` exists; capture `git status`. The skill is interactive-entry only (see Architecture); it does not attempt to detect autonomy.
2. **Mechanical audit** — `spec_lint.py . --json`; present the human report.
3. **Auto-fix** — clean `specs/` tree: run `--fix`, list every applied fix (Req 3.4). Dirty tree: warn and offer the override (`--fix-dirty`) via AskUserQuestion (Req 4.2's explicit override, surfaced).
4. **Judgment audit** — recency scan per spec: `git log --format=%ad --date=short -- specs/<dir>`; specs touched since `last_run` (fallback: 45 days, a documented default constant) are audited first and marked `active`; the producing pattern is named from the commit sequence (Req 2.6). Checks `SJ-SUP/SCOPE/GHOST/FLOW/FILE/DRIFT` rules against the conventions reference; findings emitted in the JSON finding model. Optional read-only subagent fan-out per domain for large repos.
5. **Triage** — gated findings in batches by rule family (largest active cluster first) via AskUserQuestion. Decline → offer exclusion, spec- or finding-granularity chosen by the user, recorded via the `exclude` subcommand (Req 5.1–5.2). Note: recording exclusions dirties `specs/`, which is why auto-fix runs at step 3 — this ordering is a constraint, not a preference.
6. **Apply** — approved batches only. Moves rewrite inbound refs within `specs/` in the same change; outside refs become follow-ups (Req 3.6). Supersession annotations follow the decision-log format, both directions (Req 6.3).
7. **Index** — no `specs/OVERVIEW.md` and specs exist: run `/specs-overview` to create; repairs changed status/supersession: regenerate (Req 6.1–6.2).
8. **Summary** — applied auto-fixes, applied/declined/excluded batches, detect-only findings with proposed follow-ups, each citing its rule ID (Req 2.5).

### Copilot agent (`spec-janitor.agent.md`)

Runs `python3 .github/skills/spec-janitor/spec_lint.py .` (human report, no `--json`, no `--fix`, no subcommands) and includes the report in its output; states that exit 1 means findings, not failure. Report-only is structural: the asset contains no write path (Req 9.2).

### Guardrail edits (Req 8)

| File | Edit |
|---|---|
| `claude/skills/engage/SKILL.md` | Task derivation: requirement references anchor `prd.md` sections; never emit `requirements.md#…` when the folder has no requirements.md (8.1) |
| `claude/skills/starwave-smolspec/SKILL.md` | Direction-changing revision passes mark the discarded sections superseded in the same edit, citing `SJ-SUP-*` (8.2) |
| `claude/skills/starwave-tasks/SKILL.md` | Task list scope must match the source document; appended tasks carry the same schema as existing ones (8.3) |
| `claude/skills/fix-bug/SKILL.md` | Filing rule: bugfixes/ entries follow the report shape; non-bug work goes to a regular spec via smolspec (8.4) |
| `claude/skills/next-task/SKILL.md`, `claude/skills/make-it-so/SKILL.md` | Shared paragraph: mid-implementation spec edits follow the conventions reference — supersession annotation and task-schema consistency (8.5). nextup is deliberately excluded: it is a pure router that performs no spec edits; the skills it routes to are the ones guarded |

Each edit is a short addition citing the conventions reference; no restructuring.

## Error Handling

- `spec_lint.py` never raises on malformed spec content — malformed input *is* the finding. Internal errors (unreadable file) exit 2. Corrupt `.janitor.json`: backup + rebuild + prominent report (see store contract).
- `--fix` mid-apply failure (file changed between snapshot and write): abort remaining fixes, report which applied; the skill re-runs the audit before proceeding.
- Skill-level degradations (report note, never a hard stop): rune absent, `/specs-overview` unavailable, shallow/missing git history (recency scan skipped, all specs treated as active).

## Testing Strategy

`tests/test_spec_lint.py` (stdlib unittest, hermetic fixtures under `tests/fixtures/spec_lint/`):

- **Fixture corpus reproduces the survey**: dangling anchors (sdd-ui), mixed-ID task file (captcha), out-of-sequence numbering (contactsimplifier), zero-recognized-document folder (fires `SJ-MODE-001` — pins janitor-owned discovery), bugfix-shape violations, bugfix-shaped folder outside `bugfixes/`, nested-domain layout, PRD multi-task-file spec, clean repo (zero findings), no-`specs/` repo (exit 0 + notice).
- **Disposition honesty**: `SJ-REF-002` with two candidates or a cross-folder path → `demoted: true`, no write; `--fix` mutates only auto-fix rules.
- **Idempotence** (Req 4.3): `--fix` then re-run → zero findings for fixed items, byte-identical tree.
- **Dirty-tree guard** (Req 4.2): uncommitted change under `specs/` → `--fix` refuses; `--fix-dirty` proceeds; non-git directory refuses.
- **rune paths**: rune absent → `rune_available: false` + skip note; rune present (monkeypatched runner) → failure becomes `SJ-TASK-001`; minted IDs round-trip `rune list` (skipped when rune unavailable).
- **Exclusions** (Req 5.3–5.4): excluded finding keeps matching after line insertions *and* after inserting a new task above the subject task (slug subjects, not numbers); excluded spec skipped and listed; `exclude`/`mark-raised` subcommands write schema-valid stores; corrupt store → backup + rebuild.
- **Rule-ID parity** (Req 7.2): bidirectional between `spec_lint.py` and `spec-conventions.md` mechanical rules.
- **JSON schema and exit codes** pinned, including evidence-array shape and the closed three-value disposition enum.

`tests/test_align.py` additions (existing tests unmodified): verbatim seeding — first copy, unchanged no-op, **modified target backed up and re-copied** (pins the C1 fix; the old skip-markerless behavior must NOT apply to janitor assets); stale-pack prune exempts `.github/agents/spec-janitor.agent.md` with no zero-matches warning; second aligned run reports no changes.

`tests/test_sync_compat.py` addition: `spec-janitor.agent.md` symlink present in the VS Code prompts target set.

Wired into the existing `make test`.
