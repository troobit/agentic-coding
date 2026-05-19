---
name: make-it-so
description: 4. Make it so (implement all tasks)
---

### 4. Make it so (implement all tasks)

Implement all the remaining tasks from the spec, one phase at a time, using parallel agents per stream where possible.

**Constraints:**

**Phase Retrieval:**
- The model MUST use the rune skill to retrieve the next phase to work on
- Use `rune next --phase --format json` to get the next incomplete phase
- If `rune next` reports that all tasks are complete, stop the loop and report completion to the user

**Stream Detection:**
- Once a phase is selected, the model MUST run `rune streams --available --json` to detect ready work streams
- If 2 or more streams have ready tasks in the current phase: use parallel execution
- If only 1 stream has ready tasks (or the phase has no streams defined): use sequential execution

**Parallel Execution (multiple streams):**
- Spawn one subagent (via the Task tool) per stream with ready work, all in a single message so they run in parallel
- Each subagent receives:
  - The stream number to work on
  - Path to the tasks file
  - List of front_matter_references to read
  - Instruction to use `rune next --phase --stream N --format json` to retrieve all tasks for that stream
  - Instruction to read all referenced files before implementing
  - Instruction to implement tasks in dependency order, using tools/skills as needed (context7 for library docs, efficiency-optimizer for verification, etc.)
  - Instruction to mark tasks complete with `rune complete <task-id>` as each one finishes
  - Instruction to stop when all tasks in the stream are complete or blocked by tasks in other streams, and report status back
- The main agent coordinates by:
  - Waiting for all subagents to return
  - If any stream is blocked but others have unblocked new work, re-check `rune streams --available --json` and spawn a follow-up subagent for the unblocked stream
  - If all streams become blocked waiting on each other, report a circular dependency to the user and stop
  - The main agent MUST NOT implement stream tasks itself while subagents are running

**Sequential Execution (single stream or no streams):**
- The model MUST read all files referenced in the front_matter_references and any additional references included in the task
- Add the selected tasks to the internal TODO list for tracking and implement in the order specified
- Implement all selected tasks, including all subtasks
- Mark each task complete with `rune complete <task-id>` as it finishes
- Use tools and skills as appropriate (context7, efficiency-optimizer, etc.)

**Review:**
- Once the phase is completely implemented (all streams reported done), use the design-critic skill to look over the implemented work and verify that it's correct. Issues detected should be fixed or updated in the decision log.

**Commit:**
After the review, commit the work using the below process.

1. Run all formatting and test commands.
2. Use the command line to get an overview of the staged git changes. If no changes are staged, stage all files. If running the formatting resulted in unstaged changes to files, stage these as well. DO NOT revert code changes unless specifically asked to do so.
3. Create a concise, well-documented summary of the changes in the format as defined at keepachangelog.com, excluding any changes to the changelog file itself. Use proper formatting and be specific about the changes. Ignore the marking of tasks as complete.
4. Read the CHANGELOG.md file, if the file does not exist, create it.
5. Verify if the summary is already present in the changelog, if not add it to the top of the file.
6. Add the changelog to staged commits
7. Verify the current git branch using the git command.
8. Extract any ticket numbers from the branch, check for the below options based on what is likely.
    a. Extract the JIRA ticket number from the branch. The ticket number will be in the format ABC-123 and will be the combination of 3-5 letters or numbers, a -, and 1-5 numbers. This will be at the start of the branch name, possibly preceeded by something like feature/ or hotfix/.
    b. Check for a pure number, this would likely reflect a GitHub Issue.
9. If a ticket number was found, use this as the commit message prefix, otherwise use [feat] / [bug] / [doc] as appropriate based on any prefixes in the branchname and/or the code changes
10. Summarise the changes into a multi-line detailed commit message, prefixed with the commit message prefix and :. Do NOT include any co-authored-by information in the commit message.
11. Commit the code

**Specs Overview Update:**
- After committing, check if all tasks in the spec are now complete (use `rune list specs/{feature_name}/tasks.md --format json` and verify no incomplete tasks remain)
- If all tasks are complete AND `specs/OVERVIEW.md` exists:
  - Update the spec's status from `Planned` or `In Progress` to `Done` in the table row
  - If any new files were created in the spec directory during implementation (e.g., implementation.md), add them to the spec's detail section file list
- If tasks remain incomplete AND `specs/OVERVIEW.md` exists AND the spec's status is `Planned`:
  - Update the spec's status from `Planned` to `In Progress` in the table row

**Compact and Continue:**
- After the commit and overview update, if any incomplete tasks remain in the spec, run `/compact` with instructions that preserve only the `/make-it-so` skill context
- Use this exact format: `/compact Continuing /make-it-so - implement the next phase. Current progress: [brief summary of completed phase]`
- After compaction completes, immediately continue executing `/make-it-so` to implement the next phase
- If all tasks are complete, do not compact — report completion to the user and stop
