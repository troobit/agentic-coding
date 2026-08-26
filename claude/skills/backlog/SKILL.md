---
name: backlog
description: Capture loose ideas, note files, and audit findings into a tracked, rune-parseable specs/BACKLOG.md, route each item to where the work belongs — an existing spec's tasks, an existing spec's requirements, or the backlog itself — and clear the sources once filed. Replaces the sunset nextup and spout skills. Use when the user says "add this to the backlog", "capture these notes", "file this idea", "/backlog", or hands over loose text/files with forward intent and no tracked home.
---

# Backlog

`/backlog` is the one tracked entry point for forward intent. It captures free-form text, named files, or (bare) whatever loose intent files exist in the repo, routes each captured item to where the work actually belongs, and clears the sources it consumed. Its only artifacts are `specs/BACKLOG.md` and, when an item belongs to an existing spec, edits inside that spec's own files — no scratch output, no gitignored report, no orientation summary.

Every run ends with every captured item in exactly one state: **filed** (written to a backlog entry, a spec task, or a requirement amendment), **dropped** (already in the backlog or already realized in the repo), or **failed** (could not be processed). Filed and dropped together are **handled**.

## Preflight

1. `git rev-parse --show-toplevel` for the repo root — `specs/BACKLOG.md` always lives there, under `specs/`.
2. If `rune` is not on PATH: warn once, and this run refuses every BACKLOG.md write (unparseability can't be checked without the parser) and deletes no source (items destined for the backlog are unhandled, so nothing becomes delete-eligible). Routing into existing spec files may still proceed.
3. If `specs/BACKLOG.md` exists, run `rune list specs/BACKLOG.md`. A parse failure is a hard stop: report the violation and make **no changes** to BACKLOG.md, spec files, or source files until the file is repaired — nothing in this run is worth doing against a broken backlog.

## 1. Reconcile

Before capturing anything new, sweep the existing backlog: for each entry, check whether its proposed spec now exists under `specs/`, or its content is now realized in the repo (see [Duplicate criterion](#duplicate-criterion)). Remove and report every entry that matches. Spec folders are authoritative for this check; `specs/OVERVIEW.md` is a hint only — it is regenerated on demand and may be stale or absent, so never trust it over the folders themselves.

## 2. Gather

- **Free-form argument text** — treat it as one or more items directly; route each in the same run.
- **A named file path** — capture from it regardless of its tracked status.
- **Bare invocation** — detect candidate sources and present them before capturing anything:
  - A root `nextup.md`, regardless of tracked status, **user zone only**: everything above the first recognised machine marker (`<!-- LM -->`, legacy `<!-- ML -->`, or `<!-- nextup:machine -->`) ends the zone; a `<!-- USER -->` marker belongs to the zone it opens; with no marker at all, the whole file is the zone.
  - Untracked or gitignored `*.md` files at the repo root and under `specs/` that do not belong to a **spec folder** — any directory under `specs/` containing at least one of `requirements.md`, `design.md`, `smolspec.md`, `prd.md`, `tasks*.md`, or `decision_log.md`.
  - Excluded from detection, always: `SPOUT.md` (a generated artifact from the retired spout skill, if still present), `specs/BACKLOG.md` (this skill's own artifact), and `specs/OVERVIEW.md` (the generated index).

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

Append backlog entries to the matching phase (`## Idea` or `## Needs Spec`), numbered **max-existing + 1** across the whole file — reconciliation removals never renumber survivors, so gaps in the numbering are normal and expected. Create `specs/` and `specs/BACKLOG.md` together on first capture, using the grammar below.

### The BACKLOG.md grammar

Rune-strict; both phases always present, in this order, even when empty:

```markdown
# Backlog

## Idea

- [ ] 1. <one-line item>
  - <source>, <YYYY-MM-DD>

## Needs Spec

- [ ] 2. <one-line item>
  - <source>, <YYYY-MM-DD> → spec: <kebab-name>
```

- H1 title, exactly two H2 phases — `## Idea` and `## Needs Spec` — as the status carriers. Phase membership *is* the status; there is no other status field.
- Every entry is an unchecked task item with exactly one indented detail line: `- <source>, <date>`, with an optional ` → spec: <kebab-name>` suffix that appears on every `Needs Spec` entry and no `Idea` entry.
- `<source>` is the captured file's repo-relative path, or `conversation` for free-form input — it is historical provenance and is never required to resolve to an existing file. `<date>` is ISO `YYYY-MM-DD`.
- Entry titles are single lines and never contain the literal ` → spec: ` — that string is parsed from the line end.
- **Every entry stays unchecked, forever.** Work that starts leaves the backlog entirely (reconciliation removes it once its spec exists); a checked or in-progress entry is a defect, not a state to produce. **Never run rune write commands (`rune add`, `rune update`, `rune complete`, …) against `specs/BACKLOG.md`** — every change to it is a plain text edit.
- Never delete a tracked file, regardless of how it entered a run.

## 5. Clear

Show the outcome of every item, grouped by source, always — even when a source's items were all dropped as duplicates. Then:

- **Delete-eligible sources**: not tracked by git, at least one item was read from them, and every item read from them was handled (filed or dropped) with none failed. Ask for approval **once per run**, covering every delete-eligible source together, before deleting any of them.
- Decline → leave every source file untouched. The filed entries stay filed; a later run will again offer the (now all-duplicate) source for deletion.
- A source with any failed item is never deleted that run, regardless of the batch decision.
- A tracked source is never deleted, full stop — it appears in the outcome listing marked **retained**, with removal noted as a user action.

## Duplicate criterion

An item is a duplicate — dropped, not filed — when its substance already exists in one of: the backlog, a spec document, or shipped work recorded in the repository (code, `CHANGELOG.md`). This is deliberately wider than "already in a spec": consumed intent zones (an old `nextup.md`, a loose proposal) are typically realized via commits and changelog entries, not spec text, so a narrower check would re-file work that has already shipped. Always report the match target — which backlog entry, spec, or commit/changelog line the item matched.

## Contract notes

- The skill never commits. It edits files; committing stays a user action.
- No rune write commands ever touch `specs/BACKLOG.md` (see the grammar above) — additions and reconciliation removals are text edits.
- `specs/BACKLOG.md`'s absence is never reported as drift — it's created on first capture, not seeded ahead of time.

## Error handling

| Situation | Behavior |
|---|---|
| `specs/BACKLOG.md` unparseable at preflight | Report the violation, make zero writes anywhere this run |
| `rune` binary missing | Refuse BACKLOG.md writes and source deletion this run; spec-file routing may still proceed |
| An item can't be routed or filed | Outcome `failed`; its source is never deleted this run |
| Tracked-status of a source is ambiguous | `git ls-files --error-unmatch <path>` decides; tracked → retained |
| Deletion fails partway through a batch | Report per file; already-filed entries are unaffected — filing always completes before any deletion starts |

## Constraints

- MUST NOT run any rune write command (`add`, `update`, `complete`, …) against `specs/BACKLOG.md`.
- MUST NOT delete a tracked file, ever — not as a source, not anywhere.
- MUST stop with zero writes when `specs/BACKLOG.md` fails to parse at preflight.
- MUST confirm a requirement amendment with the user before writing it, and MUST NOT renumber an existing acceptance-criterion anchor.
- MUST show the per-source outcome listing whenever anything was captured, and MUST ask for delete approval at most once per run, covering the whole batch of delete-eligible sources.
- MUST treat `specs/OVERVIEW.md` as a hint only during reconciliation — spec folders are authoritative.
- MUST exclude `SPOUT.md`, `specs/BACKLOG.md`, and `specs/OVERVIEW.md` from source detection.
