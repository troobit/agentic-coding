---
name: backlog
description: Capture loose ideas, note files, and audit findings into a rune-parseable specs/BACKLOG.md, re-derive the work already outstanding under specs/ (design missing, tasks unfinished or blocked, orbit variants unadopted), route each captured item to where the work belongs — an existing spec's tasks, an existing spec's requirements, or the backlog itself — and clear the sources once filed. Use when the user says "/backlog", or hands over loose text/files with forward intent and no tracked home.
---

# Backlog

`/backlog` is the one entry point for forward intent. It captures free-form text, named files, or (bare) whatever loose intent files exist in the repo, routes each captured item to where the work actually belongs, re-derives the work already outstanding under `specs/`, and clears the sources it consumed. Its only artifacts are `specs/BACKLOG.md` and, when an item belongs to an existing spec, edits inside that spec's own files — no scratch output, no gitignored report, no orientation summary.

`specs/BACKLOG.md` holds two kinds of entry, and the difference governs everything below:

- **Captured** entries (`## Idea`, `## Needs Spec`) come from outside the specs — conversation text, note files. They are the only record of intent whose source this skill may delete, so they persist across runs and leave only via reconciliation.
- **Derived** entries (`## Outstanding`) mirror work that already lives under `specs/`: a spec missing its design, a task file with unfinished or blocked tasks. They are torn down and rebuilt from the spec folders on every run, so a derived entry cannot outlive the state it describes.

Because half the file restates state that moves underneath it, `specs/BACKLOG.md` is a working file, not a record — regenerate it, keep it out of version control, and never cite an entry number outside the run that produced it.

Every run ends with every **captured** item in exactly one state: **filed** (written to a backlog entry, a spec task, or a requirement amendment), **dropped** (already in the backlog or already realized in the repo), or **failed** (could not be processed). Filed and dropped together are **handled**. Derived entries have none of these states: they are rebuilt, not handled.

## Preflight

1. `git rev-parse --show-toplevel` for the repo root — `specs/BACKLOG.md` always lives there, under `specs/`.
2. If `rune` is not on PATH: warn once, and this run refuses every BACKLOG.md write (rune is both the writer and the parse check) and deletes no source (items destined for the backlog are unhandled, so nothing becomes delete-eligible). Routing into existing spec files may still proceed.
3. If `specs/BACKLOG.md` exists, run `rune list specs/BACKLOG.md`. A parse failure is a hard stop: report the violation and make **no changes** to BACKLOG.md, spec files, or source files until the file is repaired — nothing in this run is worth doing against a broken backlog.
4. If `specs/BACKLOG.md` is tracked by git, note it once and carry on — it is a regenerated working file and belongs untracked. Removing it from the index is a user action; this skill never deletes a tracked file.

## 1. Reconcile and re-derive

Two passes over the existing backlog, before anything new is captured:

1. **Reconcile the captured entries** — for each `Idea` / `Needs Spec` entry, check whether its proposed spec now exists under `specs/`, or its content is now realized in the repo (see [Duplicate criterion](#duplicate-criterion)). Remove and report every entry that matches.
2. **Rebuild the derived entries** — remove the `## Outstanding` entries wholesale and re-derive the phase from the current state of the spec folders (see [Outstanding spec work](#outstanding-spec-work)). Nothing there is amended in place, so no derived entry can go stale between runs.

Spec folders are authoritative for both passes; `specs/OVERVIEW.md` is a hint only — it is regenerated on demand and may be stale or absent, so never trust it over the folders themselves.

## 2. Gather

- **Free-form argument text** — treat it as one or more items directly; route each in the same run.
- **A named file path** — capture from it regardless of its tracked status.
- **Bare invocation** — detect candidate sources and present them before capturing anything:
  - Untracked or gitignored `*.md` files at the repo root and under `specs/` that do not belong to a **spec folder** — any directory under `specs/` containing at least one of `requirements.md`, `design.md`, `smolspec.md`, `prd.md`, `tasks*.md`, or `decision_log.md`. Belonging is by ancestry, not immediate parent: a file nested deeper (an `.orbit/` run transcript, say) belongs to the spec folder above it and is never a source.
  - Excluded from detection, always: `specs/BACKLOG.md` (this skill's own artifact), and `specs/OVERVIEW.md` (the generated index).

Spec folders are never gathered as sources — their outstanding work arrives through the rebuild in step 1, not through capture, and their files are never consumed or deleted.

## 3. Route (one destination per item)

For every gathered item, propose exactly one destination with a one-line reason:

| Destination | When |
|---|---|
| Existing-spec task | The item fits inside a spec's current requirements — no scope change |
| Existing-spec requirement amendment | The item changes what a spec covers |
| Backlog entry, `needs-spec` | The item warrants a spec that doesn't exist yet — include a proposed spec name |
| Backlog entry, `idea` | The item is an idea with no actionable next step |

**Task-file selection rule** (also used for an amendment's staleness task, below): the spec's only task file if it has exactly one; otherwise the `tasks-*.md` whose name or stream matches the item; otherwise `tasks.md`. Create `tasks.md` if the spec has no task file at all.

**Requirement amendments** are heavier and gated:
- Confirm the amendment with the user, per item, before writing it.
- Add or modify the requirement in the spec's `requirements.md` **without renumbering existing acceptance-criterion anchors** — new criteria get new anchors; existing ones never move.
- Append a task, via the task-file selection rule above, naming the now-stale downstream documents (design, tasks) and which workflow re-runs them (e.g. `/starwave:design`, `/starwave:tasks`).

An item routed to a `needs-spec` backlog entry never also gets a task or requirement edit — the backlog entry *is* its filing.

## 4. File

Write entries into the matching phase — captured items to `## Idea` or `## Needs Spec`, the rebuilt work to `## Outstanding`. On first capture, create `specs/` and `specs/BACKLOG.md` together with the three phases in place.

**`rune` writes this file; nothing else does.** It is the parser the grammar below is defined against, so hand-editing invites exactly the unparseability the preflight check exists to catch:

- Create — `rune create specs/BACKLOG.md --title "Backlog"`, then `rune add-phase` for `Idea`, `Needs Spec`, `Outstanding`, in that order.
- Add an entry — `rune add specs/BACKLOG.md --title "<item>" --phase "<phase>" --details "<detail line>"`.
- Remove entries (reconciliation, and the `Outstanding` teardown) — `rune remove`, or one `rune batch` for the whole teardown-and-rebuild so the phase is never half-written.
- Verify — `rune list specs/BACKLOG.md` after the last write of the run; a parse failure there is reported, not left behind.
- **Never** `rune complete`, `rune progress`, or `rune next --claim` against this file. Entry numbering belongs to rune: it may shift between runs, which is why an entry number means nothing outside the run that printed it.

### The BACKLOG.md grammar

Rune-strict; all three phases always present, in this order, even when empty:

```markdown
# Backlog

## Idea

- [ ] 1. <one-line item>
  - <source>, <YYYY-MM-DD>

## Needs Spec

- [ ] 2. <one-line item>
  - <source>, <YYYY-MM-DD> → spec: <kebab-name>

## Outstanding

- [ ] 3. <spec-name>: 4 tasks outstanding, 1 blocked
  - specs/<spec-name>/tasks.md, <YYYY-MM-DD> → run: /next-task
```

- H1 title, exactly three H2 phases — `## Idea`, `## Needs Spec`, `## Outstanding` — as the status carriers. Phase membership *is* the status; there is no other status field.
- Every entry is an unchecked task item with exactly one indented detail line: `- <source>, <date>`, plus a suffix fixed by its phase — ` → spec: <kebab-name>` on every `Needs Spec` entry, ` → run: <command>` on every `Outstanding` entry, and nothing on an `Idea` entry.
- `<source>` is the captured file's repo-relative path, `conversation` for free-form input, or — for a derived entry — the spec folder or task file the entry was read from. On a captured entry it is historical provenance and is never required to resolve to an existing file. `<date>` is ISO `YYYY-MM-DD`.
- Entry titles are single lines and never contain the literal ` → spec: ` or ` → run: ` — those are parsed from the line end.
- **Every entry stays unchecked, forever.** Work that starts leaves the backlog entirely — a captured entry when reconciliation finds its spec, a derived entry when the next rebuild no longer finds the gap. A checked or in-progress entry is a defect, not a state to produce.
- Never delete a tracked file, regardless of how it entered a run.

## 5. Clear

Show the outcome of every captured item, grouped by source, always — even when a source's items were all dropped as duplicates. Report the `## Outstanding` rebuild separately as a count and a list; it has no sources, so nothing there is ever delete-eligible. Then:

- **Delete-eligible sources**: not tracked by git, at least one item was read from them, and every item read from them was handled (filed or dropped) with none failed. Ask for approval **once per run**, covering every delete-eligible source together, before deleting any of them.
- Decline → leave every source file untouched. The filed entries stay filed; a later run will again offer the (now all-duplicate) source for deletion.
- A source with any failed item is never deleted that run, regardless of the batch decision.
- A tracked source is never deleted, full stop — it appears in the outcome listing marked **retained**, with removal noted as a user action.

## Outstanding spec work

A spec folder is outstanding when any row below holds. Each row that matches produces its own derived entry, so one spec can yield more than one — a spec with no design *and* unfinished tasks is two entries, because they unblock differently.

| Condition | Entry title | Suffix |
|---|---|---|
| `requirements.md` present, no `design.md` / `smolspec.md` / `prd.md` | `<spec>: requirements complete, design missing` | `→ run: /starwave:design` |
| A design present, no `tasks*.md` | `<spec>: design complete, tasks missing` | `→ run: /starwave:tasks` |
| A task file with pending or in-progress tasks | `<spec>: N tasks outstanding, M blocked` | `→ run: /next-task` |
| An unadopted variant run (below) | `<spec>: N variants unadopted (opus, codex)` | `→ run: orbit status <spec>` |
| A variant worktree with no metadata entry (below) | `<spec>: orphaned variant worktree <branch>` | `→ run: orbit cleanup <spec>` |

Read task state from `rune list <task-file> --format json` — never by eyeballing checkboxes. Pending and in-progress tasks are both outstanding; a task whose `blocked-by` dependencies are unmet is additionally counted as blocked, and `, M blocked` is omitted when that count is zero. A spec whose tasks are all complete produces no entry, and neither does a spec folder with no `requirements.md` — an empty or exploratory folder is not outstanding work.

### Variant runs

`orbit run --variants N` implements a spec several times in parallel worktrees, one per agent, and leaves the work sitting on branches until someone adopts one. That is finished work nobody has picked, which is exactly what this phase is for.

The signal is `specs/<spec>/.orbit/variants.json`, not the `.orbit/` directory — a finalized run leaves its transcripts behind, so directory presence would mark every past spec outstanding forever. Read the file directly (`orbit status <spec> --format json` is the same data and fails hard when the file is absent):

- Each entry in `variants` carries `branch`, `worktree_path`, `status`, and `agent`; the root carries `base_commit`.
- A variant is **unadopted** when `git rev-list --count <base_commit>..<branch>` is non-zero — it has commits nobody has merged. Name the agents of the unadopted variants in the entry title; that is the choice the developer is being asked to make.
- A run whose variants are all `failed` or `canceled` with no commits ahead is noise, not work — no entry.
- Cross-check `git worktree list` against the metadata. A worktree on a variant branch with commits ahead and no matching `variants.json` entry is orphaned: one entry per orphan, so it gets cleaned up rather than silently holding a branch.

## Duplicate criterion

An item is a duplicate — dropped, not filed — when its substance already exists in one of: the backlog, a spec document, or shipped work recorded in the repository (code, `CHANGELOG.md`). This is deliberately wider than "already in a spec": consumed intent zones (an old scratch-note file, a loose proposal) are typically realized via commits and changelog entries, not spec text, so a narrower check would re-file work that has already shipped. Always report the match target — which backlog entry, spec, or commit/changelog line the item matched.

**Derived entries are exempt.** Restating spec state is the whole point of the `## Outstanding` phase, so a derived entry that matches an existing spec is correct rather than duplicative. The criterion applies only to captured items, and a captured item is still a duplicate when its substance appears in a spec — route it to that spec, or drop it; never file it as a second copy under `## Outstanding`.

## Contract notes

- The skill never commits. It edits files; committing stays a user action — and `specs/BACKLOG.md` is not one of the files to commit.
- `rune` is the only writer of `specs/BACKLOG.md` (see step 4) — captures, reconciliation removals, and the `Outstanding` rebuild all go through it.
- `specs/BACKLOG.md`'s absence is never reported as drift — it's created on first capture, not seeded ahead of time.

## Error handling

| Situation | Behavior |
|---|---|
| `specs/BACKLOG.md` unparseable at preflight | Report the violation, make zero writes anywhere this run |
| `rune` binary missing | Refuse BACKLOG.md writes and source deletion this run; spec-file routing may still proceed |
| A rune write against BACKLOG.md fails | Report it; the affected items are `failed`, and a half-written `Outstanding` rebuild is retried or torn down, never left partial |
| A spec's task file is unparseable during the rebuild | One derived entry naming the parse failure, suffixed `→ run: /spec-janitor`; the rest of the rebuild proceeds |
| An item can't be routed or filed | Outcome `failed`; its source is never deleted this run |
| Tracked-status of a source is ambiguous | `git ls-files --error-unmatch <path>` decides; tracked → retained |
| Deletion fails partway through a batch | Report per file; already-filed entries are unaffected — filing always completes before any deletion starts |

## Constraints

- MUST NOT delete a tracked file, ever — not as a source, not anywhere.
- MUST stop with zero writes when `specs/BACKLOG.md` fails to parse at preflight.
- MUST write `specs/BACKLOG.md` only through `rune`, MUST NOT mark any entry in it complete or in-progress, and MUST re-run `rune list` against it before the run ends.
- MUST rebuild the whole `## Outstanding` phase every run, and MUST NOT amend a derived entry in place.
- MUST NOT treat a spec folder as a capture source, and MUST NOT delete or consume any file inside one.
- MUST confirm a requirement amendment with the user before writing it, and MUST NOT renumber an existing acceptance-criterion anchor.
- MUST show the per-source outcome listing whenever anything was captured, and MUST ask for delete approval at most once per run, covering the whole batch of delete-eligible sources.
- MUST treat `specs/OVERVIEW.md` as a hint only during reconciliation — spec folders are authoritative.
- MUST exclude `specs/BACKLOG.md` and `specs/OVERVIEW.md` from source detection.
