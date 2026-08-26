# Decision Log: backlog-skill

## Decision 1: Feature name and scope

**Date**: 2026-08-26
**Status**: accepted

### Context

The nextup skill has been sunset (it did not do what was needed) and spout is slated for removal. Both failed the same way: ephemeral output — nextup zones were never cleared and went stale; SPOUT.md was gitignored and stale the moment HEAD moved. A cross-repo assessment (2026-08-26) found forward intent across all repos living in gitignored or untracked files with no tracked home.

### Decision

Build one replacement feature named `backlog-skill`: a `/backlog` skill plus the sunset of nextup and spout, specced together in `specs/backlog-skill/`.

### Rationale

The replacement and the removal are one change — the migration of nextup.md zones only makes sense with the new destination in place, and shipping the skill without the sunset would leave two competing entry points.

### Alternatives Considered

- **`backlog` as the name**: matches the invocation `/backlog` - Rejected because the folder name would not distinguish the skill from the BACKLOG.md artifact it manages.
- **`nextup-spout-sunset`**: names the removal - Rejected because it hides the new capability, which is the larger half of the work.

### Consequences

**Positive:**
- One spec covers the full round trip: new skill, toolchain retirement, migration.

**Negative:**
- Larger spec surface than a skill-only feature; the migration adds multi-repo coordination.

---

## Decision 2: Enroll the operator's remaining active repos; migrate all participants

**Date**: 2026-08-26
**Status**: accepted

### Context

A set of repos already participates in align; several of the operator's active repos do not, and assessment found the unenrolled ones hold some of the richest untracked backlogs. (This log is committed, so repos are referred to by role; the concrete list is session-local operator state.)

### Decision

Enroll the operator-designated unenrolled repos as align participants within this feature's rollout, and run the nextup.md migration across all participants.

### Alternatives Considered

- **Existing participants only**: defer enrollment - Rejected because the unenrolled repos are where the migration pays off most.
- **This repo only, others ad hoc**: smallest scope - Rejected because ad hoc migration is exactly the untracked-intent pattern being retired.

### Consequences

**Positive:**
- The repos with the largest untracked backlogs get a tracked home in the same pass.

**Negative:**
- Enrollment adds per-repo `.agentic.json` setup and align verification to the rollout.

---

## Decision 3: BACKLOG.md holds pre-spec work only

**Date**: 2026-08-26
**Status**: accepted

### Context

BACKLOG.md needs a lifecycle contract: either track work through its whole life (mirroring all five Transit columns) or hold only pre-spec intent.

### Decision

The backlog holds only pre-spec items with statuses `idea` and `needs-spec` (mapping to Transit's Idea and Planning columns). Promotion to a spec removes the entry; specs/OVERVIEW.md and task files own the work from there.

### Rationale

Duplicated state that goes stale is the failure mode that killed nextup and SPOUT.md. In-progress and done states are already tracked by the spec system; mirroring them would reintroduce drift.

### Alternatives Considered

- **Full Transit mirror**: entries persist through idea → done - Rejected because it duplicates OVERVIEW.md/task state and will drift.
- **Promoted-pointer hybrid**: promotion rewrites entries to pointers - Rejected as accumulating clutter that needs periodic pruning, a maintenance chore with no consumer.

### Consequences

**Positive:**
- Nothing in the backlog can contradict the spec system; the file only shrinks when work starts.
- Transit import later maps cleanly: backlog statuses → Idea/Planning columns.

**Negative:**
- No single file shows the full pipeline; answering "what is in flight" still needs OVERVIEW.md.

---

## Decision 4: Confirm once per run, then delete sources

**Date**: 2026-08-26
**Status**: accepted

### Context

Consumed sources (nextup.md zones, loose proposals) are mostly gitignored or untracked, so deletion is unrecoverable. The clearing step must balance safety against leaving stale husks.

### Decision

The skill shows what it filed from each source and asks for approval once per run before deleting the source files. Declining leaves all sources untouched while keeping the filed entries.

### Alternatives Considered

- **Delete only after commit**: strongest guarantee - Rejected because it forces a commit into the skill's flow, and committing stays a user action.
- **Empty, never delete**: truncate to a template - Rejected because empty husk files are exactly the clutter being retired.

### Consequences

**Positive:**
- Untracked content is safe: by the time sources are deleted, it lives in the tracked backlog.

**Negative:**
- A declined confirmation leaves content duplicated between source and backlog until the next run.

---

## Decision 5: Routing can amend requirements, not just append tasks

**Date**: 2026-08-26
**Status**: accepted

### Context

A captured item that belongs to an existing spec could be filed as a task (fits existing requirements) or could change the spec's scope. Filing scope changes as tasks would silently bypass the requirements gate.

### Decision

Routing has three destinations: existing-spec task, existing-spec requirement amendment (which flags design/tasks as stale so those workflows re-run), or backlog entry (`needs-spec` / `idea`). Items are filed directly — the backlog only ever holds work with no spec home.

### Rationale

Requirement amendments make downstream change salient and re-engage the design/tasks workflows rather than letting scope creep in through the task list. The user accepted the resulting rebuild churn as a cost.

### Alternatives Considered

- **Always park in BACKLOG.md first**: human promotes later - Rejected as adding a manual step to every item; the backlog would accumulate routed-but-unmoved entries.
- **Tasks-only routing**: never touch requirements - Rejected because scope changes filed as tasks bypass the requirements gate.

### Consequences

**Positive:**
- Scope changes surface as requirement diffs, not buried tasks.

**Negative:**
- A requirement amendment obligates a design/tasks re-run — heavier than dropping in a task.

---

## Decision 6: Decision overwrite mode, per-repo opt-in

**Date**: 2026-08-26
**Status**: accepted

### Context

For some projects the supersede convention (mark old entry superseded, append new) buries the current state of a decision under its history. The user wants decisions overwritten in place for several of their application repos, so changes to design and downstream documents stay salient — accepting fragile renumbering in code comments and rebuild churn as a cost.

### Decision

A `decision_mode` key in `.agentic.json`: `overwrite` edits decision entries in place (same ID, updated date, no superseding entry); unset or `supersede` keeps today's behavior. The rollout sets `overwrite` in the repos the operator designates.

### Alternatives Considered

- **Overwrite as the global default, supersede opt-in**: covers "etc." without a list - Rejected by the user in favor of explicit opt-in.
- **Global overwrite, supersede retired**: simplest - Rejected because repos where decision history matters (this repo among them) lose the audit trail.

### Consequences

**Positive:**
- Decision logs in overwrite repos always read as current state; no archaeology through superseded entries.

**Negative:**
- Overwrite repos lose in-file decision history (git history still holds it).
- References to decision IDs in code comments and documents can silently drift when entries are rewritten.

---

## Decision 7: BACKLOG.md encoding — phases as status, pending-only invariant

**Date**: 2026-08-26
**Status**: accepted

### Context

Rune's parser is strict (H1, H2 phases, checkbox task items, indented detail lines; free prose fails) and its status model is only pending/in-progress/completed. The requirements demanded rune-parseability and custom statuses (`idea`, `needs-spec`) without saying how the two coexist — flagged as a blocker by the design-critic and confirmed by peer review.

### Decision

Statuses are H2 phases: `## Idea` and `## Needs Spec`. Phase membership is the status. All entries stay unchecked forever — since promotion removes an entry (Decision 3), a checked or in-progress entry is a defect, not a state. Capture date, source, and proposed spec name are indented detail lines. Rune write commands are not used on BACKLOG.md, and the process-status report rune-parses the file to enforce the contract.

### Rationale

Phases are first-class in rune, entries move between statuses without touching detail lines, and "everything reads as Pending" converts from an apparent limitation into a checkable invariant. Detail-line statuses would be invisible to every parser and forfeit the point of rune-parseability.

### Alternatives Considered

- **Detail-line status (`Status: idea`)**: keeps one phase - Rejected because no parser can select on it, forcing a bespoke Transit importer later.
- **Rune's native checkbox states as status**: no custom encoding - Rejected because pre-spec statuses do not map onto pending/in-progress/completed.

### Consequences

**Positive:**
- The contract is mechanically checkable today (process-status parse) and importable later (phases → Transit columns).

**Negative:**
- Rune's write/renumber commands must be avoided on this one file; hand-edits that break parsing block the skill until repaired.

---

## Decision 8: decision_mode is read from .agentic.json at run time

**Date**: 2026-08-26
**Status**: accepted

### Context

The draft said the mode would be "generated into each repo's agent instructions" — but review verified no per-repo agent-instruction generation path exists for any repo (align writes only MCP configs into targets; copilot-instructions is gated on `cloud_assets`, which is false in the repos the mode targets). The convention agents actually follow is a globally symlinked format reference that cannot express per-repo modes.

### Decision

Decision-writing workflows read `decision_mode` from the repo's `.agentic.json` at run time, defaulting to `supersede`. The global decision-log format reference and the shared convention text in all three toolchain wrappers (Claude, Codex, Copilot) document both modes and the manifest read. The named workflows: starwave skills, smolspec, fix-bug, spec-janitor, /backlog.

### Alternatives Considered

- **Per-repo generated instruction text**: static per-repo files - Rejected because the generation path doesn't exist and would have to be built, and generated text goes stale against the manifest.
- **Global convention only, no manifest**: simplest - Rejected because it cannot express per-repo modes at all.

### Consequences

**Positive:**
- One source of truth per repo; no new generation machinery.

**Negative:**
- Every decision-writing workflow gains a manifest-read step, and a repo without `.agentic.json` silently stays in supersede mode.

---

## Decision 9: Backlog/spec consistency via /backlog reconciliation, not starwave hooks

**Date**: 2026-08-26
**Status**: accepted

### Context

"Promotion removes the entry" had no owner: specs are normally created by the starwave workflow, which this feature does not modify, so entries for promoted work would linger — the drift Decision 3 exists to prevent.

### Decision

`/backlog` owns consistency: every run starts with a reconciliation pass that removes and reports entries whose proposed spec now exists. The starwave skills are untouched.

### Alternatives Considered

- **Modify starwave-creating-spec to prune the backlog**: removal at the moment of promotion - Rejected because it couples the spec workflow to the backlog and widens this feature into skills it otherwise doesn't touch.
- **Manual removal**: human obligation - Rejected as the unenforced-discipline pattern that failed before.

### Consequences

**Positive:**
- One owner; the spec workflow stays ignorant of the backlog.

**Negative:**
- Stale entries persist between /backlog runs (bounded by run frequency, and visible in the tracked file).

---

## Decision 10: Requirement amendments leave a tracked staleness task

**Date**: 2026-08-26
**Status**: accepted

### Context

Routing an item as a requirement amendment makes design.md/tasks.md stale. Reporting that only in-session is the ephemeral-state failure mode this feature exists to kill.

### Decision

An amendment appends a task to the amended spec's own task file naming the stale documents and the workflows to re-run. Amendments never renumber existing acceptance-criterion anchors.

### Alternatives Considered

- **Status flag in specs/OVERVIEW.md**: central visibility - Rejected because OVERVIEW.md is regenerated by the specs-overview skill and hand-set flags would be overwritten.
- **In-session report only**: no artifact - Rejected as ephemeral state, the pattern being retired.

### Consequences

**Positive:**
- Staleness is tracked, rune-visible, and surfaced by existing process-status drift checks.

**Negative:**
- The staleness task must be kept honest — completing the re-run must check it off.

---

## Decision 11: Sunset ordering — skill first, migrate, then remove

**Date**: 2026-08-26
**Status**: accepted

### Context

align raises an error if its seed root lacks `nextup.example.md`, so deleting the canonical template before updating align breaks every align run. Review also found the sunset's real footprint is ~5x the skill directories: five test fixtures, three test files, four agent notes, a runbook, scripts/README, and a spec-janitor reference.

### Decision

Strict ordering: (1) the /backlog skill lands and syncs; (2) migration runs across participating repos; (3) the sunset removes the skills, align seeding + canonical template in the same change, tests/fixtures, and documentation. Since no seeded `nextup.example.md` copies exist in any target repo, align gets no removal behavior — residual cleanup belongs to the migration flow with human eyes on it.

### Alternatives Considered

- **align converges the absence of nextup.example.md**: automated cleanup - Rejected because zero seeded copies exist to clean, and post-deletion align has no canonical to judge "previously seeded" against without risking user content.
- **No mandated ordering**: land as convenient - Rejected because one wrong merge order breaks align for every repo.

### Consequences

**Positive:**
- No intermediate state where align is broken or intent files are orphaned without a destination.

**Negative:**
- The feature cannot ship as independent parallel streams; migration gates the sunset.

---

## Decision 12: Rollout administration is not a requirement

**Date**: 2026-08-26
**Status**: accepted

### Context

The draft requirements carried per-repo rollout actions — enrolling new participants, setting `decision_mode` in designated repos, migration checklists, residual-file cleanup in other repos. The user's review: adoption or removal of tools in other repos is post-build administration, not system design; keeping it in requirements pollutes context and intent. A follow-up ruling extended this: committed spec documents must not name repos outside this one or machine-local paths — they would publish what the developer works on and reference ephemeral resources.

### Decision

Requirements describe only system behavior — what `/backlog` does in whatever repo it runs in, and what the sunset changes in this repo's toolchain. All per-repo rollout actions move to `rollout.md` in this spec folder as a checklist. Decisions 2 (enrollment scope) and 11 (skill → migrate → sunset ordering) stand, but their per-repo substance is executed via rollout.md, and the requirements retain only the toolchain-internal ordering constraint (skill present before sunset lands).

### Rationale

Behaviors like nextup.md user-zone capture, duplicate dropping, and all-duplicate delete eligibility are system requirements because they hold wherever the skill runs; visiting thirteen repos is a one-time operation with no design content. Separating them keeps the requirements testable against the system rather than against the state of the user's filesystem.

### Alternatives Considered

- **Keep rollout in requirements as a numbered section**: everything in one document - Rejected by the user: it pollutes design context and intent with administration.
- **Rollout as tasks in the task phase**: tracked with the implementation - Rejected because the task phase is coding-only by convention, and repo visits are not coding.

### Consequences

**Positive:**
- Requirements stay about the system; the design phase inherits no per-repo noise.
- Rollout has a checkable home with exit criteria instead of being implied by ACs.

**Negative:**
- rollout.md is a new document kind in the spec folder; completion tracking is manual checkboxes, not rune.

---

## Decision 13: Duplicate detection matches repo-realized work, not only specs

**Date**: 2026-08-26
**Status**: accepted

### Context

The design's contract notes widened the drop criterion from "realized in a spec" to shipped work generally — flagged by the design-critic as a requirements change smuggled through the design, feeding delete-eligibility of unrecoverable untracked sources. But the narrower criterion fails on the feature's own worked examples: consumed intent zones are typically realized via commits and changelog entries, not spec text, so migration would re-file already-shipped work.

### Decision

An item is a duplicate when its substance exists in the backlog, a spec document, or shipped work recorded in the repository (code, CHANGELOG). ACs 1.5 and 2.6 are amended accordingly; the match target is always reported, and the per-run deletion approval remains the backstop.

### Alternatives Considered

- **Spec-realization only**: as originally approved - Rejected because consumed zones would never register as duplicates and migration would re-file shipped work.
- **Backlog-only matching**: cheapest check - Rejected because it re-files anything that skipped the backlog on its way to shipping, which is most historical work.

### Consequences

**Positive:**
- Migration recognizes consumed zones; the backlog stays free of already-shipped work.

**Negative:**
- The judgment surface is larger (code and changelog, not just specs), so dedup quality depends more on session diligence; the deletion approval gate is the control.

---

## Decision 14: decision_mode delivery is two-channel; AC 5.3 scoped by behavior

**Date**: 2026-08-26
**Status**: accepted

### Context

The design claimed one paragraph in shared conventions would reach all decision-writing workflows with no per-skill edits. Review disproved this: three skills hard-code the supersede convention in their own instructions (spec-janitor's audit mandate, and the mid-implementation edit clauses in make-it-so and next-task), and skill-local instructions beat generic convention text at runtime. Review also found AC 5.3's named list was wrong: fix-bug contains no decision-log behavior, and /backlog itself writes none.

### Decision

Deliver the mode through both channels: the generated conventions text (all three toolchains), plus one-sentence edits to every skill whose instructions direct decision-log revision — spec-janitor (SKILL.md and its spec-conventions reference), make-it-so, next-task. AC 5.3 is amended to name workflows by behavior: skills whose instructions direct decision-log creation or revision.

### Alternatives Considered

- **Conventions text only**: single edit - Rejected because skill-local supersede mandates override it; spec-janitor would flag overwrite-mode logs as drift.
- **Per-skill edits only, no conventions text**: precise - Rejected because ad-hoc decision writing outside any skill (common in sessions) would never learn the mode.

### Consequences

**Positive:**
- No skill contradicts the mode; sessions without a skill still get the rule from conventions.

**Negative:**
- Four skill files gain a mode-awareness sentence that future skill authors must remember to include when a new skill touches decision logs.

---

## Decision 15: Sunset grep gate exempts the /backlog skill's own functional legacy-filename references

**Date**: 2026-08-26
**Status**: accepted

### Context

Implementing task 7.1 (the sunset grep test itself) surfaced that `claude/skills/backlog/SKILL.md` legitimately contains the literal strings `nextup` (in `nextup.md`) and `spout` (in `SPOUT.md`), because the skill's own job is to detect a legacy `nextup.md` file and exclude a generated `SPOUT.md` file by name. AC 6.5's exemption list (`specs/`, `CHANGELOG.md`, the test file) did not anticipate this: without an added exemption, the grep gate would stay red forever after task 7.2's removals land, flagging load-bearing skill behavior as if it were leftover sunset debris.

### Decision

Add `claude/skills/backlog/SKILL.md` to the sunset grep gate's exemption list, alongside `specs/` and `CHANGELOG.md`.

### Rationale

Exempting the whole file is the smallest fix that doesn't compromise the file's own correctness — its filename references are load-bearing spec behavior (Requirement 1.2's `nextup.md` detection, 1.3's `SPOUT.md` exclusion), not cleanup debris, and no rewording describes "detect a file named nextup.md" without the literal string.

### Alternatives Considered

- **Reword SKILL.md to avoid literal filename strings**: describe rather than name the files - Rejected because the skill's job is literally to look for files with those names; obscuring the string makes the instructions harder to follow correctly, for zero grep-gate benefit.
- **Narrow the grep pattern to exclude filename-shaped matches**: keep the exemption list short - Rejected as fragile pattern engineering that would also blind the gate to genuine future regressions elsewhere.

### Consequences

**Positive:**
- The grep gate can actually reach green once 7.2 lands; the exemption is narrow (one file) rather than a broad pattern change.

**Negative:**
- A fourth exempt path (beyond the original three-item list) is something future maintainers must remember when reasoning about what "exempt" covers.

---
