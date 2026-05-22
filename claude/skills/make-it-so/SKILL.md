---
name: make-it-so
description: 4. Make it so (implement all tasks)
---

### 4. Make it so (implement all tasks)

Implement all the remaining tasks from the spec, one phase at a time. The main agent delegates each stream within a phase to a dedicated subagent that owns its stream end-to-end (implement → test → commit). The main agent oversees the spawn cycle, merges completed stream branches, and runs phase-level review and bookkeeping.

**Constraints:**

**Phase Retrieval (main agent):**
- The main agent MUST use the rune skill to retrieve the next phase to work on
- Use `rune next --phase --format json` to get the next incomplete phase
- If `rune next` reports that all tasks are complete, stop the loop and report completion to the user

**Stream Detection (main agent):**
- Once a phase is selected, the main agent MUST run `rune streams --available --json` to detect ready work streams
- If 2 or more streams have ready tasks: use parallel delegation (below)
- If only 1 stream has ready tasks (or the phase has no streams defined): use sequential execution (below)

**Parallel Delegation (multiple streams):**

Subagents work in isolated git worktrees so their parallel commits don't race on the shared index or on `tasks.md`.

For each ready stream the main agent MUST:
1. Create a worktree branched from the current working branch:
   - `git worktree add .claude/worktrees/<phase>-stream-<N> -b stream/<phase>-<N>`
2. Spawn one subagent per worktree, all in a single message so they run in parallel (Task tool, `general-purpose` subagent unless a more specific type fits)

Each subagent prompt MUST include:
- The stream number it owns
- The absolute path to its worktree (it MUST `cd` there before doing anything)
- The path to the tasks file inside the worktree
- The list of `front_matter_references` to read before implementing
- These instructions:
  - Use `rune next --phase --stream N --format json` to retrieve all tasks for the stream
  - Read all referenced files before implementing
  - Implement tasks in dependency order. Use tools/skills as needed (context7 for library docs, efficiency-optimizer for verification, etc.)
  - Mark each task complete with `rune complete <task-id>` as it finishes
  - Run all formatting and test commands for the project before committing
  - Stage changes (including any reformatting and the modified `tasks.md`) and commit using the **Commit Conventions** below
  - Stop when all tasks in the stream are complete, when blocked by tasks in other streams, or on unrecoverable failure
  - Report back: branch name, list of completed task IDs, list of blocking task IDs (if any), and final status (`done` | `blocked` | `failed`)

**Main Agent Oversight:**
- Wait for all spawned subagents to return
- Track which streams reported `done` / `blocked` / `failed`
- After any return, re-run `rune streams --available --json`. If newly unblocked streams appear (because another stream's completion satisfied their deps), spawn fresh subagents for them in new worktrees — same parallel pattern as above
- If every remaining stream reports `blocked` and no new work surfaces, report a circular dependency to the user and stop
- If a subagent reports `failed`, surface the failure to the user and stop the phase rather than masking it
- The main agent MUST NOT implement stream tasks itself or commit on behalf of subagents while they are running

**Integration (main agent, after all subagents in the phase have returned `done`):**
1. From the main working branch, merge each completed stream branch in turn:
   - `git merge --no-ff stream/<phase>-<N> -m "[merge]: phase <P> stream <N>"`
2. Conflicts on `tasks.md` are expected (each stream marked different tasks complete). Resolve by accepting both sides' completions
3. After all stream branches are merged, remove their worktrees and delete the branches:
   - `git worktree remove .claude/worktrees/<phase>-stream-<N>`
   - `git branch -d stream/<phase>-<N>`

**Sequential Execution (single stream or no streams):**
- The main agent works in place (no worktree)
- Read all files referenced in `front_matter_references` and any additional references included in the task
- Implement all selected tasks, including all subtasks, in the order specified
- Mark each task complete with `rune complete <task-id>` as it finishes
- Use tools and skills as appropriate (context7, efficiency-optimizer, etc.)
- Commit using the **Commit Conventions** below

**Review (main agent):**
- Once the phase is fully integrated (or sequential work is committed), use the design-critic skill over the resulting state and verify it's correct. Issues detected should be fixed (and committed as a follow-up) or recorded in the decision log

**Phase Changelog & Specs Overview (main agent):**
- After review, write a single phase-level changelog entry summarising the work from all streams (subagent commits do not touch the changelog — see Commit Conventions). Read `CHANGELOG.md` (create if missing), prepend the entry if not already present, and commit it as `[doc]: changelog for phase <P>` (or with a ticket prefix if applicable)
- Then check if all tasks in the spec are complete: `rune list specs/{feature_name}/tasks.md --format json` and verify no incomplete tasks remain
- If all tasks complete AND `specs/OVERVIEW.md` exists:
  - Update the spec's status from `Planned` or `In Progress` to `Done`
  - If new files were created in the spec directory during implementation (e.g., `implementation.md`), add them to the spec's detail section file list
- If tasks remain AND `specs/OVERVIEW.md` exists AND the spec's status is `Planned`:
  - Update the spec's status from `Planned` to `In Progress`
- Commit any overview/decision-log updates

**Compact and Continue (main agent):**
- If incomplete tasks remain in the spec, run `/compact` with: `/compact Continuing /make-it-so - implement the next phase. Current progress: [brief summary of completed phase]`
- After compaction completes, immediately continue executing `/make-it-so` to implement the next phase
- If all tasks are complete, do not compact — report completion to the user and stop

---

**Commit Conventions** (used by stream subagents and by sequential mode for the implementation commit; do NOT use these for the main agent's phase changelog commit, which is a separate single-file commit):

1. Run all formatting and test commands.
2. Use the command line to get an overview of the staged git changes. If no changes are staged, stage all files. If running the formatting resulted in unstaged changes to files, stage these as well. DO NOT revert code changes unless specifically asked to do so.
3. Stream subagents MUST NOT touch `CHANGELOG.md` — the main agent writes the per-phase changelog entry after merging all streams. Sequential-mode (single stream / no streams) MUST update `CHANGELOG.md` here, since there is no separate merge step:
    - Create a concise summary in the format defined at keepachangelog.com, excluding changes to the changelog file itself. Be specific. Ignore the marking of tasks as complete.
    - Read `CHANGELOG.md`, creating it if missing. Verify the summary isn't already present; if not, add it to the top.
    - Stage the changelog change.
4. Verify the current branch with git. Stream subagents are on `stream/<phase>-<N>`; the ticket prefix below should be derived from the **base** working branch the worktree was created from, not from the stream branch.
5. Extract any ticket numbers from the base branch:
    a. JIRA-style ticket: `ABC-123` (3–5 letters/digits, `-`, 1–5 digits) at the start of the branch name, possibly after `feature/` or `hotfix/`.
    b. A pure number, which would likely reflect a GitHub Issue.
6. If a ticket number was found, use it as the commit message prefix; otherwise use `[feat]` / `[bug]` / `[doc]` based on the branch and the nature of the changes.
7. Write a multi-line commit message prefixed with `<prefix>:`. Do NOT include any co-authored-by lines.
8. Commit.
