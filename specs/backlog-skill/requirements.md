# Requirements: backlog-skill

## Introduction

A single `/backlog` skill replaces the sunset `nextup` and `spout` skills. It captures ideas, loose notes, and audit findings into a tracked, rune-parseable `specs/BACKLOG.md`, routes each item to where the work belongs (an existing spec's tasks, an existing spec's requirements, or the backlog itself), and clears the consumed sources. The feature also executes the sunset: removing both old skills and their toolchain footprint (align seeding, tests, fixtures, documentation), and introducing a per-repo decision overwrite mode.

## Definitions

- **Item outcome**: every captured item ends a run in exactly one state — **filed** (written to a backlog entry, spec task, or requirement amendment), **dropped** (recognized as already present in the backlog or realized in a spec), or **failed** (could not be processed). An item is **handled** when it is filed or dropped.
- **Source**: a file content was captured from. A source is **delete-eligible** when it is not tracked by git, at least one item was read from it, and every item read from it is handled with none failed.
- **User zone**: in a `nextup.md`, the user-intent content: everything except content at or below a recognized machine marker (`<!-- LM -->`, legacy `<!-- ML -->`, `<!-- nextup:machine -->`). A `<!-- USER -->` marker belongs to the zone it opens; WHERE no machine marker exists, the entire file is the zone.

## Non-Goals

- No Transit integration now — BACKLOG.md statuses are named for a clean later import, but no Transit MCP calls, `T-` ids, or column sync.
- No tracking of in-progress or completed work — once promoted to a spec, an item leaves the backlog; specs/OVERVIEW.md and task files own it from there.
- No orientation report — spout's "state of every spec" summary is retired without replacement; `specs/OVERVIEW.md` covers it.
- No regenerated scratch artifacts — the skill writes no SPOUT.md-style gitignored output; its only artifacts are the tracked backlog and spec amendments.
- No automatic commits — the skill edits files; committing remains a user action.
- No sweeping or deleting of tracked project documentation — tracked files can be capture sources only when the user names them (except a root `nextup.md`, which is always a candidate), and are never deleted.
- No changes to the starwave skills — backlog/spec consistency is owned by `/backlog`'s reconciliation pass, not by hooks in the spec workflow.
- No cross-repo rollout in these requirements — enrollment of new participating repos, per-repo migration runs, per-repo `decision_mode` configuration, and residual-file cleanup are post-build administration, tracked in this spec's `rollout.md`.

## Requirements

### 1. Capture

**User Story:** As a developer, I want to hand loose ideas and note files to one skill, so that forward intent stops living in untracked scratch.

**Acceptance Criteria:**

1. <a name="1.1"></a>WHEN invoked with free-form text, the skill SHALL capture that text as one or more items and route them per Requirement 2 in the same run  
2. <a name="1.2"></a>WHEN invoked bare, the skill SHALL detect candidate sources in the repo — a root `nextup.md` regardless of tracked status (user zone only), plus untracked or gitignored markdown files at the repo root and under `specs/` that do not belong to a spec folder — and present them for capture  
3. <a name="1.3"></a>The skill SHALL exclude known generated artifacts (`SPOUT.md`) from source detection  
4. <a name="1.4"></a>WHEN invoked with a file path, the skill SHALL capture from that file regardless of its tracked status  
5. <a name="1.5"></a>IF a captured item already exists in the backlog or is already realized in the repository (a spec, or shipped work recorded in code or the changelog), THEN the skill SHALL drop it and report what it matched  

### 2. Routing

**User Story:** As a developer, I want each captured item placed where the work actually belongs, so that the backlog holds only work with no home yet.

**Acceptance Criteria:**

1. <a name="2.1"></a>The skill SHALL propose exactly one destination per item — existing-spec task, existing-spec requirement amendment, or backlog entry — with a one-line reason  
2. <a name="2.2"></a>WHEN an item is routed to an existing spec as a task, the skill SHALL append it as a rune-parseable task to the spec's most relevant task file, creating `tasks.md` WHERE the spec has no task file  
3. <a name="2.3"></a>WHEN an item is routed to an existing spec as a requirement amendment, the skill SHALL confirm the amendment before writing, SHALL add or modify the requirement in that spec's requirements.md without renumbering existing acceptance-criterion anchors, and SHALL append a task (per the task-file selection rule of [2.2](#2.2)) naming the stale downstream documents (design, tasks) whose workflows need re-running  
4. <a name="2.4"></a>WHEN an item warrants a spec that does not exist, the skill SHALL file it as a backlog entry with status `needs-spec` and a proposed spec name  
5. <a name="2.5"></a>WHEN an item is an idea with no actionable next step, the skill SHALL file it as a backlog entry with status `idea`  
6. <a name="2.6"></a>WHEN a run starts, the skill SHALL reconcile the backlog: entries whose proposed spec now exists or whose content is now realized in the repository (per [1.5](#1.5)) SHALL be removed and reported  

### 3. The BACKLOG.md contract

**User Story:** As a developer, I want the backlog to be a tracked file with a stable format, so that it survives machines, appears in diffs, and imports into Transit later.

**Acceptance Criteria:**

1. <a name="3.1"></a>The backlog SHALL live at `specs/BACKLOG.md` in the repo the skill runs in (the git root is the unit), created together with `specs/` on first capture; its absence SHALL NOT be reported as drift  
2. <a name="3.2"></a>The backlog SHALL be parseable by `rune list`, with this schema: an H1 title, exactly two H2 phases `## Idea` and `## Needs Spec` as the status carriers, task items as unchecked entries, and capture date, source name, and (for `needs-spec`) proposed spec name as indented detail lines  
3. <a name="3.3"></a>Every entry SHALL sit in exactly one phase; phase membership IS the status, mapping to Transit's Idea and Planning columns  
4. <a name="3.4"></a>All entries SHALL remain unchecked: work that starts leaves the backlog, so a checked or in-progress entry is a defect, and rune write commands SHALL NOT be used on BACKLOG.md  
5. <a name="3.5"></a>The per-repo process-status report SHALL rune-parse `specs/BACKLOG.md` where present and flag as drift: parse failures, phases other than the two of [3.2](#3.2), and any non-pending entry  
6. <a name="3.6"></a>WHEN BACKLOG.md fails to parse at the start of a run, the skill SHALL report the violation and make no changes to BACKLOG.md, spec files, or source files until the file is repaired  
7. <a name="3.7"></a>A source name recorded in a detail line is historical provenance (free-form input records the invocation, e.g. `conversation`); it SHALL NOT be required to resolve to an existing file  

### 4. Clearing consumed sources

**User Story:** As a developer, I want consumed source files removed once their content is filed, so that stale intent files cannot lie to future sessions.

**Acceptance Criteria:**

1. <a name="4.1"></a>WHEN a run captured from any sources, the skill SHALL show the outcome of every item per source; WHEN delete-eligible sources exist, it SHALL ask for approval once per run before deleting them — including sources whose items were all dropped as duplicates  
2. <a name="4.2"></a>IF approval is declined, THEN the skill SHALL leave every source file untouched while keeping the filed entries, and a later run SHALL again offer the (now all-duplicate) source for deletion  
3. <a name="4.3"></a>A source with any failed item SHALL NOT be deleted in that run  
4. <a name="4.4"></a>The skill SHALL NOT delete tracked files, regardless of how they entered the run  
5. <a name="4.5"></a>A fully-handled tracked source SHALL appear in the per-source outcome listing of [4.1](#4.1) marked as retained, with removal noted as a user action  

### 5. Decision overwrite mode

**User Story:** As a developer, I want a repo to be able to declare that decision log entries are overwritten in place instead of superseded, so that changes to design and downstream documents stay salient.

**Acceptance Criteria:**

1. <a name="5.1"></a>WHERE a repo's `.agentic.json` sets `decision_mode` to `overwrite`, workflows that revise a decision SHALL edit the existing entry in place, keeping its ID and updating its date, with no superseding entry appended  
2. <a name="5.2"></a>WHERE `decision_mode` is unset or `supersede`, decision revisions SHALL keep today's behavior: the old entry is marked superseded and a new entry is appended  
3. <a name="5.3"></a>Workflows whose instructions direct decision-log creation or revision (the starwave skills, smolspec, spec-janitor, make-it-so, next-task) SHALL determine the mode by reading the repo's `.agentic.json` at run time, defaulting to `supersede`  
4. <a name="5.4"></a>The decision-log format reference and the shared convention text for all three toolchains (Claude, Codex, Copilot wrappers) SHALL document both modes and the run-time manifest read  

### 6. Sunset of nextup and spout

**User Story:** As a developer, I want the retired skills and their entire toolchain footprint gone, so that no tool recommends, seeds, tests, or documents the failed pattern.

**Acceptance Criteria:**

1. <a name="6.1"></a>The `nextup` and `spout` skill directories SHALL be removed and the README skill registry SHALL list `backlog` in their place  
2. <a name="6.2"></a>The align toolchain SHALL stop seeding `nextup.example.md` and stop managing `nextup.md` gitignore entries, with the canonical `nextup.example.md` removed in the same change so align never runs against a seed root missing a file it requires  
3. <a name="6.3"></a>The process-status report SHALL drop both nextup columns (presence and example convergence) and their drift logic, replacing them with BACKLOG.md presence and the parse check of [3.5](#3.5)  
4. <a name="6.4"></a>The sync script SHALL remove symlinks that point into this repo's skills directory but whose target no longer exists, and SHALL NOT touch links it does not own  
5. <a name="6.5"></a>After the sunset lands, `nextup` and `spout` SHALL have no remaining references in the toolchain — skills, scripts, tests, fixtures, agent notes, runbooks, and README — with historical records (`specs/`, `CHANGELOG.md`) exempt; the known footprint at spec time spans the five align test fixture repos and seed root, three test files, four agent notes, the process-onboarding runbook, `scripts/README.md`, and the spec-janitor skill  
6. <a name="6.6"></a>The sunset changes SHALL land only after the `/backlog` skill is present in the synced toolchain, so no session is left without an intent-capture entry point  
