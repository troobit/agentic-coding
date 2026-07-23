---
name: specs-overview
description: Generate or regenerate specs/OVERVIEW.md with a tabular summary, status, and per-spec file listings
---

# Specs Overview Generator

Generate or update a `specs/OVERVIEW.md` file that catalogues all feature specs in the project's `specs/` directory.

This skill is **format-adaptive** and **preservation-first**. Repos differ: some keep flat `specs/<capability>/` folders, some nest `specs/<domain>/<capability>/`; some tag specs with a domain and mode, some don't. The skill reads what a repo already does — from an existing `OVERVIEW.md` and from the on-disk structure — and reproduces that shape rather than flattening it to a lowest common denominator. When an `OVERVIEW.md` already exists, hand-curated prose is **preserved, not regenerated** (see [Preservation](#preservation-the-core-rule)). Full mechanical generation happens only for a first-time build or for newly discovered specs.

## Prerequisites

- A `specs/` directory must exist in the project root.
- At least one spec folder must exist with spec files (`requirements.md`, `smolspec.md`, `design.md`, `prd.md`, `plan.md`, etc.).

## Process

### 1. Discover specs

A **spec** is a leaf directory under `specs/` that contains at least one spec document: `requirements.md`, `smolspec.md`, `prd.md`, `design.md`, or a `tasks*.md` file. Discover them robustly so both layouts work:

- **Flat repos:** `specs/<capability>/` — the capability directory is the spec.
- **Nested repos:** `specs/<domain>/<capability>/` — the capability (leaf) directory is the spec, and `<domain>` is the path segment(s) between `specs/` and the leaf.

Exclude `specs/bugfixes/` entirely (bug specs are tracked separately). Ignore container directories that only hold other spec folders (they are not themselves specs) and dotfolders (`.orbit`, etc.).

For each spec collect:

- **Directory path** relative to `specs/` (e.g. `estimation/pipeline` or `serving-adjust`) — used for file links.
- **Domain** — the path segment(s) before the leaf, if the repo nests; empty for flat repos. If an existing `OVERVIEW.md` records a domain for a spec (including a multi-domain tag like `data · ui`), keep that.
- **Display name** — Title Case of the leaf directory name, UNLESS an existing `OVERVIEW.md` already gives the spec a curated display name (e.g. a renamed `estimation/pipeline` shown as **Research**); then keep the existing name and its anchor.
- **Creation date** — earliest git commit that added files in the directory: `git log --diff-filter=A --format='%aI' -- 'specs/<dir>/'`; take the last (oldest) line, format `YYYY-MM-DD`.
- **Status** — see [Status derivation](#status-derivation).
- **Mode** — see [Mode derivation](#mode-derivation).
- **Summary** — for an existing spec, the current curated summary (preserved). For a new spec, a first-draft one-to-two-sentence summary from the first substantive paragraph of the primary document (check in order: `requirements.md`, `smolspec.md`, `prd.md`, `design.md`, `plan.md`).
- **Files** — all `.md` files in the directory, excluding `explanation.md` (session-scoped explain-like output — listing it creates dead links once the artefact is removed) and non-documentation items (`comparison-report/`, `.DS_Store`, artifact subdirectories).

### Status derivation

Determine status from the spec's task file(s) — `tasks.md` or, for PRD-lane specs, every `tasks-*.md` combined:

- `Done` — every task checkbox is complete.
- `In Progress` — some complete, some not.
- `Planned` — tasks exist but none are complete.
- `No Tasks` — no task file exists.

Checkbox markers: `[x]`/`[X]` count as complete; `[ ]` is open; rune's in-progress/blocked markers `[-]`, `[~]`, `[/]` count as **not** complete (so a spec whose only remaining task is a `[-]` on-device verify is `In Progress`, not `Done`). Always recompute status live — never trust the old value.

`Superseded` is a curated status, not a checkbox outcome: if the spec's `decision_log.md` or primary document marks it superseded / abandoned / retired, use `Superseded`. Preserve an existing `Superseded` status unless the spec has clearly been revived.

### Mode derivation

Include a Mode column when spec modes are meaningful in the repo (starwave / PRD lane repos — effectively all repos using this workflow). Derive from the files present:

- `prd` — a `prd.md` exists (PRD lane).
- `smol` — a `smolspec.md` exists.
- `full` — `requirements.md` + `design.md` exist.
- Fallback `full` if a `tasks.md` exists with numbered requirements-style docs.

Preserve any curated suffix an existing `OVERVIEW.md` carries (e.g. `full ·iterative`, marking a target-driven concern inside an otherwise deterministic spec) — do not invent the `·iterative` suffix; only carry it forward if already present.

## Preservation — the core rule

**When `specs/OVERVIEW.md` already exists, treat its curated content as authoritative and edit around it:**

- **Preserve** verbatim: the intro/legend block (header notes, `PROCESS.md` / `DECISIONS.md` links, the Domain/Mode legend), each existing spec's **Summary** prose, each existing spec's **detail-section prose**, curated **display names/anchors**, and curated **Domain**/**Mode**/`Superseded` tags.
- **Recompute and update** for every existing spec: **Status** (from task files), **Creation date** (from git), and the **file list** (add/remove `.md` files that appeared or disappeared). If a summary contains a mechanical task-count phrase (e.g. "8/9 tasks done"), you MAY update just that phrase to match the recomputed status; otherwise leave the summary prose alone.
- **Add** a table row and detail section for each newly discovered spec, generating a first-draft summary. Place it in the correct group and chronological position.
- **Remove** the row and detail section for any spec whose directory no longer exists.

This is an in-place reconciliation (Edit the file), not a from-scratch rewrite. Only when `OVERVIEW.md` does **not** exist do you generate the whole file mechanically.

## Output structure

### Columns (adaptive)

The table always has **Name**, **Status**, **Summary**, and a **Created** column. Add:

- a **Domain** column *iff* the repo nests specs under domain directories (or an existing `OVERVIEW.md` uses one);
- a **Mode** column *iff* modes are meaningful (see [Mode derivation](#mode-derivation)).

The medata-style full form is:

```markdown
# Specs Overview

> How specs are written, tracked, and turned into code: [PROCESS.md](PROCESS.md).
> Cross-cutting architectural decisions are distilled in the meta decision log: [DECISIONS.md](DECISIONS.md). Per-spec decision logs below remain authoritative for detail.

> **Domain** — every spec lives at `specs/<domain>/<capability>/`; the domain is one of <the domains actually present>.
> **Mode** — `full` / `smol` / `prd` / `iterative`; a `·iterative` suffix marks a target-driven concern inside an otherwise deterministic spec.

| Name | Domain | Created | Status | Mode | Summary |
|------|--------|---------|--------|------|---------|
| [Spec Name](#anchor) | domain | YYYY-MM-DD | Status | mode | One- to two-sentence summary. |
...

---

## Spec Name

Summary prose (may be a short paragraph).

- [filename.md](domain/capability/filename.md)
...
```

Only emit the `PROCESS.md` / `DECISIONS.md` legend lines that correspond to files that actually exist under `specs/`. For a flat repo with no domains, drop the Domain column and the domain legend, and the table degrades to `| Name | Created | Status | Mode | Summary |`.

### Ordering

- If the repo uses domains: **group by domain**, and within each domain sort chronologically (oldest first). Preserve the domain group order an existing `OVERVIEW.md` already uses (e.g. estimation, capture, data, ui, then top-level multi-domain PRD specs). Top-level specs with no domain directory (typically PRD-lane) group together, conventionally last.
- If the repo is flat: sort all rows chronologically, oldest first.

### Detail sections

- One H2 section per spec, in the same order as the table.
- Summary/prose below the heading (preserved for existing specs).
- A bulleted list of the spec's `.md` files, each linked relative to `specs/` (`domain/capability/filename.md` when nested).
- Anchors are the display name lowercased with spaces replaced by hyphens; keep an existing spec's established anchor.

## Write and verify

- Existing file: apply the reconciliation as targeted edits.
- No existing file: write the complete `specs/OVERVIEW.md`.
- If the repo has a spelling/lint gate for docs (e.g. a `make spell` target or `tools/check_spelling.sh`), run it after writing and fix any flagged spellings — many repos mandate Irish/British spelling.

## Constraints

- MUST NOT include specs from `specs/bugfixes/`.
- MUST use git history for creation dates, not filesystem timestamps.
- MUST examine task files to determine status (honouring rune's `[-]`/`[~]` in-progress markers), not guess from other signals.
- MUST preserve curated summaries, detail prose, display names, and the intro legend when `OVERVIEW.md` already exists — never flatten hand-maintained content to a mechanical regeneration.
- MUST reproduce the repo's existing column set and ordering rather than imposing a fixed 4-column layout.
- SHOULD parallelise git date lookups and file reads for efficiency.
- MUST NOT create or modify any file other than `specs/OVERVIEW.md`.
