---
name: spec-janitor
description: Audit and repair a diluted specs/ directory. Runs the mechanical auditor (spec_lint.py) for structural breakage, layers a judgment audit on top (duplicate/superseding specs, contradictions, scope mismatch, ghost changes, mis-filed items), applies auto-fixes, and triages gated repairs in approved batches. Use when the user asks to clean up specs, audit the specs directory, check spec hygiene, or find spec drift — e.g. "clean up the specs", "audit specs/", "run the spec janitor", "is anything wrong with our specs?".
---

# Spec Janitor

Audit a repository's `specs/` directory for dilution — broken cross-references, unparseable task files, duplicate or silently superseded specs, contradictions, mis-filed items — and repair it under tiered authority: auto-fix what has exactly one correct fix, gate everything else on explicit approval, and only ever report what needs authored content.

The normative rules live in [references/spec-conventions.md](references/spec-conventions.md) (stable `SJ-*` identifiers). Every finding cites exactly one rule ID; read the reference before the judgment audit so citations are exact.

## Entry Contract

This is an **interactive-entry skill**: no router (nextup, engage, orbit) dispatches it autonomously, and headless invocation of the full skill is out of contract. The cloud surface (GitHub Copilot coding agent) reaches the janitor only through the report-only agent asset, which runs the mechanical audit and nothing else — no auto-fixes, no gated repairs, no exclusion writes.

## The Auditor

`spec_lint.py` sits alongside this SKILL.md (in seeded repos: `.github/skills/spec-janitor/spec_lint.py`). It is stdlib-only Python 3. Its exact CLI:

```
spec_lint.py <repo-path> [--json] [--fix] [--fix-dirty]
spec_lint.py <repo-path> exclude (--spec <spec-path> | --finding <finding-id>)
spec_lint.py <repo-path> mark-raised --finding <finding-id>
```

- **Exit codes**: 0 = no findings (including a repo with no `specs/`, which prints a notice); 1 = findings exist; **2** = usage or internal error. **Exit 1 means findings, not failure** — treat it as success-with-findings and never abort on it.
- Without `--fix` / `exclude` / `mark-raised` the tool never writes anything.
- `--fix` refuses when `specs/` has uncommitted changes (or the directory is not a git repo); `--fix-dirty` overrides.
- `exclude` and `mark-raised` are the **only** writers of the exclusion store `specs/.janitor.json`. NEVER hand-edit that file — the subcommands schema-validate on write; hand-merged JSON is the store's most likely corruption source.

## Workflow

### 1. Preflight

- Confirm `specs/` exists in the target repo. If it does not, run the auditor anyway (it reports this and exits 0) and stop after relaying the notice — create nothing.
- Capture `git status --porcelain -- specs/` to know whether the tree is clean before step 3.

### 2. Mechanical audit

Run `python3 <skill-dir>/spec_lint.py . --json` and present the findings as a human-readable report grouped by spec, each finding tagged with its rule ID and disposition (`auto-fix` | `gated` | `demoted` | `detect-only`). Findings with `demoted: true` are precondition-failed auto-fixes — they join the gated batches in step 5, never guessed at.

### 3. Auto-fix

- **Clean `specs/` tree**: run `python3 <skill-dir>/spec_lint.py . --fix` and list **every** applied fix in the report.
- **Dirty tree**: do NOT fix silently. Warn that uncommitted changes under `specs/` block auto-fixes, and offer the override via AskUserQuestion: proceed with `--fix-dirty`, or continue report-only. Default to report-only.

Auto-fix runs before triage deliberately: recording exclusions in step 5 dirties `specs/`, so reversing the order would block the fixes. This ordering is a constraint, not a preference.

### 4. Judgment audit

Read and reason over spec content — this is the half the auditor cannot do.

**Recency scan first** (this prioritises active drift over historical drift):

- Read `last_run` from `specs/.janitor.json`; fall back to **45 days** (the default constant) when the store or field is absent.
- Per spec: `git log --format=%ad --date=short -- specs/<dir>` — specs touched since the cutoff are marked `active: true` and audited first.
- For active drift, name the development pattern that produced it from the commit sequence (e.g. `autonomous-run-layering` for repeated make-it-so/engage passes stacking unreconciled edits, `parallel-spec-authoring` for sibling specs created concurrently without cross-references) in the finding's `pattern` field.
- Shallow or missing git history: note it in the report, skip the scan, and treat all specs as active — never a hard stop.

**Check the judgment rules** against the conventions reference:

| Rule | Looks for | Disposition |
|---|---|---|
| `SJ-SUP-001` | Two specs addressing the same problem without referencing each other's resolution | gated |
| `SJ-SUP-002` | Later sections contradicting earlier ones after a direction change, earlier not marked superseded | gated |
| `SJ-SCOPE-001` | Task-file scope not matching the spec document's scope | gated |
| `SJ-GHOST-001` | Spec references work no spec folder covers (never confirmed against code or git) | detect-only |
| `SJ-FLOW-001` | Spec abandoned mid-workflow | gated |
| `SJ-FILE-001` | Mis-filed item (bugfix shape outside `bugfixes/`, non-bug work inside it) | gated |
| `SJ-DRIFT-001` | Benign drift in a completed spec (raise once, via `mark-raised`) | detect-only |

Emit judgment findings in the same JSON finding model the auditor uses, so exclusions and triage share one vocabulary:

- `id` is `"<rule>:<spec_path>:<file>:<subject>"` — no line numbers; specs are named by repo-relative path under `specs/` (e.g. `estimation/pipeline`).
- `subject` per family: `SJ-SUP-001` — the *other* spec's path, and the finding is emitted **once per pair under the lexicographically first spec path** (canonical ordering, one identity per pair); `SJ-SUP-002` — kebab-slug of the contradicted section heading; `SJ-SCOPE-001` — the task-file name; `SJ-GHOST-001` — kebab-slug of the referenced unspecced work; `SJ-FLOW-001` — the literal `abandoned`; `SJ-FILE-001` — the mis-filed path; `SJ-DRIFT-001` — kebab-slug of the drift kind (e.g. `bare-numeric-ids`).
- `evidence` is an array of `{file, excerpt}` entries quoting the content the finding rests on (judgment findings routinely quote multiple files).
- Optional fields: `related_spec` (the SJ-SUP-001 pair), `active` (touched since last run), `pattern` (named drift-producing pattern), `proposal` (repair or follow-up text).

For large repos, an optional read-only subagent fan-out per domain folder is fine — subagents report findings in this model and write nothing.

### 5. Triage

Present gated findings (including demoted auto-fixes) in **batches by rule family, largest active cluster first**, via AskUserQuestion. Per batch: approve, decline, or split.

On decline, offer to record a durable exclusion at the granularity the user chooses:

- Whole spec: `python3 <skill-dir>/spec_lint.py . exclude --spec <spec-path>`
- Single finding: `python3 <skill-dir>/spec_lint.py . exclude --finding <finding-id>`

A declined finding without an exclusion will be re-proposed next run — say so when offering. `SJ-DRIFT-001` findings the user wants left alone are recorded with `mark-raised --finding <finding-id>` so they are raised at most once.

### 6. Apply

Apply **approved batches only**. Rules:

- **Moves** (`SJ-FILE-001`): the move and the rewrite of all inbound references within `specs/` happen in the same batch; inbound references outside `specs/` (docs/, README) are reported as follow-ups, never edited.
- **Supersession** (`SJ-SUP-*`, `SJ-FLOW-001`): annotate, never delete. Decision-log entries follow the decision-log format (`superseded by Decision X` status markers); documents mark discarded sections superseded in place; and supersession between specs is recorded in **both directions** — the superseded spec names its successor and the superseding spec names what it replaces.
- If a file changed between audit and apply, re-run the mechanical audit before proceeding.

### 7. Index

- `specs/OVERVIEW.md` missing and specs exist: run `/specs-overview` to create it.
- Repairs changed any spec's status or supersession: run `/specs-overview` to regenerate so index rows match the repaired state.
- `/specs-overview` unavailable in the environment: note it in the report and continue.

### 8. Summary

Report, with every item citing its rule ID:

- Auto-fixes applied (each one listed).
- Gated batches applied, declined, and excluded (with the granularity recorded).
- Detect-only findings with their proposed follow-ups (`SJ-GHOST-001` follow-up specs, `SJ-MODE-002` task authoring via the tasks/engage workflows, `SJ-DRIFT-001` normalization only if the user asks).
- Excluded specs and findings (from the store), and whether the overview was created or regenerated.

## Constraints

- MUST NOT delete spec folders or erase spec history — supersession is annotated, never removed.
- MUST NOT edit files outside `specs/` (detection may read the whole repo; stale outside content becomes follow-ups).
- MUST NOT hand-edit `specs/.janitor.json` — only the `exclude`/`mark-raised` subcommands write it.
- MUST treat spec_lint.py exit 1 as findings, never as a failed command; exit 2 is the error case.
- Re-running immediately after a completed run MUST produce no new findings for repaired items and no writes.
