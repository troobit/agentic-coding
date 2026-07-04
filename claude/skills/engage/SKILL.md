---
name: engage
description: Execute a PRD to completion. Derives rune task files per application/code context from specs/{prd-name}/prd.md, runs the contexts in parallel worktrees via the make-it-so delegation loop, integrates the results, and reports. Use when the user hands over a PRD for autonomous execution — e.g. "engage", "execute this PRD", "run the PRD to completion". Supports --headless for non-interactive runs (used by orbit). NOT part of the gated starwave lane.
---

# Engage — PRD Execution

Take a PRD written by the prd skill and run it to completion with no approval gates. The flow is: **derive** rune task files per context → **execute** contexts in parallel worktrees → **integrate** → **report**. The only pauses are `STOP —` tasks (human-verification points authored into the PRD).

## Inputs and Modes

- Target: `specs/{prd-name}/prd.md` in the current repository. If no path was given and more than one `specs/*/prd.md` exists, list the candidates and ask — never guess.
- **Interactive mode** (default): the skill runs in a live Claude session and may ask the user at STOP tasks.
- **Headless mode** (`--headless`): no user interaction ever; STOP tasks and their dependents are left not-started and reported as blocked. This is also the mode orbit's non-interactive command uses.

## Step 1: Derive (idempotent)

Read `prd.md`. The reserved H2s are `Product summary`, `Goals`, `Non-goals`, and `Execution notes`; **every other H2 is a context**.

For each context H2:

1. Compute the slug: H2 text lowercased, every run of non-alphanumeric characters collapsed to a single `-`, leading/trailing `-` stripped (e.g. `API server` → `api-server`).
2. **Slug collision guard**: if two context H2s produce the same slug, ABORT derivation with an error naming both headings. Do not derive anything.
3. If `specs/{prd-name}/tasks-{slug}.md` already exists, SKIP this context — re-running engage derives only missing contexts and never rewrites an in-progress task file.
4. Otherwise create it with the rune skill:
   - `rune create specs/{prd-name}/tasks-{slug}.md --title "{PRD title} — {context name}" --reference prd.md`
   - `rune batch` to add phases and tasks: one phase per requirement cluster within the context; tasks derived from the numbered requirements and their acceptance criteria; `blocked_by` where tasks build on one another; streams where tasks within the context are independent (streams give intra-context parallelism).
5. Execution notes that require human verification become tasks titled with the `STOP — ` prefix, placed in the affected context's file with `blocked_by`/dependents wired so work that needs the verification cannot start before it.

## Step 2: Execute (one worktree per context)

Contexts run in parallel, one subagent per context. For each context with an incomplete task file:

1. Create a worktree branched from the current working branch:
   - `git worktree add .claude/worktrees/prd-{prd-name}-{slug} -b prd/{prd-name}-{slug}`
2. Spawn one subagent per context, all in a single message so they run in parallel. Each subagent prompt MUST include:
   - The absolute worktree path (it MUST `cd` there first) and its task file path (`specs/{prd-name}/tasks-{slug}.md` inside the worktree).
   - The instruction to read `prd.md` (the front-matter reference) before implementing.
   - The instruction to apply the **make-it-so delegation loop** against its own task file: `rune next --phase --format json`, stream detection via `rune streams --available --json`, parallel or single-subagent delegation per phase, `rune complete` per task — exactly as make-it-so specifies, with the two overrides below.
   - **Override 1 — context-qualified inner names**: inner stream branches/worktrees MUST be `stream/{slug}-<phase>-<N>` (worktrees `.claude/worktrees/{slug}-<phase>-stream-<N>`), NOT make-it-so's plain `stream/<phase>-<N>`. Branch names are repo-global; the unqualified names collide the moment two contexts each have streams.
   - **Override 2 — nobody touches CHANGELOG.md**: make-it-so's Subagent Commit Conventions apply unchanged EXCEPT that no subagent at any level, and no context, writes to `CHANGELOG.md`. Engage writes one PRD-level changelog entry after integration (Step 4).
   - The STOP protocol below.
   - Report back: context name, branch, completed task IDs, and final status (`done` | `blocked-at-STOP` with the task id | `failed`).

A context subagent failure surfaces per make-it-so convention: that context stops and is reported; other contexts continue.

## Step 3: STOP Protocol

A context subagent that reaches a ready `STOP — ` task MUST halt that context (committing completed work first) and return `blocked-at-STOP` with the task id.

- **Interactive run**: engage asks the user to perform the verification, then re-dispatches the context subagent to continue from its task file.
- **Headless run**: the STOP task and all its dependents stay not-started; the context is reported blocked. No prompt, no timeout-wait.

## Step 4: Integrate

1. Merge context branches into the working branch **in completion order** (as each context finishes, or sequentially after all return):
   - `git merge --no-ff prd/{prd-name}-{slug} -m "[merge]: prd {prd-name} context {slug}"`
2. **Any merge conflict stops integration and is reported** — never auto-resolve conflicts across contexts. Report which branches merged and which remain.
3. After all merges, run the quality gates ONCE on the integrated branch: `make build`, `make test`, `make lint` (whichever targets the Makefile defines). A context passing in isolation does not make the PRD complete. If the repository has no Makefile, note "no quality gates ran" in the report.
4. Write ONE PRD-level `CHANGELOG.md` entry summarising the PRD's work and commit it (this is the only changelog write in the entire flow).
5. Remove merged worktrees and delete merged context branches.

## Step 5: Complete and Report

A context is **complete** only when: all its rune tasks are complete, the quality gates pass (or "no quality gates ran" is noted for a Makefile-less repo), and the changes are committed.

The final report MUST list:

- Contexts completed.
- Contexts incomplete (with their remaining task IDs and why: failed, merge conflict, gates failing).
- Contexts blocked, including blocked-at-STOP with the STOP task ids.
- Whether the integrated-branch quality gates passed, or that none ran.

## Orbit Path (alternative local executor)

The derived task files are executable by orbit without modification, but parallelism needs care: orbit's `.orbit/run.lock` is **per checkout**, so pointing several orbit runs at different `--tasks-file` values in one checkout does NOT give parallelism — the second process refuses to start.

Run **one orbit process per context, each in its own worktree**:

```bash
git worktree add .claude/worktrees/prd-{prd-name}-{slug} -b prd/{prd-name}-{slug}
cd .claude/worktrees/prd-{prd-name}-{slug}
orbit run --tasks-file specs/{prd-name}/tasks-{slug}.md   # non-interactive: engage --headless STOP semantics apply
```

Integration afterwards follows Step 4 unchanged.
