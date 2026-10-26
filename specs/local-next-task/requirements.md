# Local next-task requirements

## Purpose

Expose a local LM Studio model iteratively to a rune tasks file, following the
existing `next-task` workflow while keeping each model session small.

## Requirements

1. The runner MUST accept an explicit tasks file in a Git working tree, use
   that repository as the working directory, and default to model ID `8-bit`.
   The caller MUST be able to choose a different LM Studio model ID.
2. Each iteration MUST retrieve work with rune in the runner and pass that
   selection to a fresh model session. By default, select one task (including
   its subtasks) without invoking the `next-task` retrieval workflow again.
   `--phase` MUST select a whole phase. An explicit `--selection model` mode
   MUST retain skill-driven retrieval and its top-level-task phase fallback,
   bounded by the runner's preflight selection. Read the ledger again before
   advancing and never mark work complete on the model's behalf.
3. The runner MUST stop on completion, a selected STOP gate, an external
   dependency blocker, a root `.orbit/halt` file, `ORBIT-HALT:` output, an agent
   error, timeout, no new completions, changed IDs, reopened completed work, or
   the iteration limit. It MUST preserve existing halt files.
4. The runner MUST preserve each iteration's prompt, process output and final
   response. A dry run MUST show the next invocation without calling a model
   or writing files. A later invocation MUST resume from ledger state.
5. The runner MUST use a workspace sandbox, retain project instructions and
   request no interactive approval during a headless run. It MUST instruct the
   model to leave changes for review without committing or pushing. Work MUST
   execute sequentially with a configurable session timeout and iteration cap.
6. The runner MUST reject empty paths and directory paths with a clear usage
   error. Make MUST explain the required `TASKS=...` argument when omitted.
   A repeatable install target MUST expose `local-next-task` in the user's
   shell, accept task paths relative to the caller, and preserve foreign files
   at the install destination.

The original requirement to always invoke `next-task` and fall back to a phase
is superseded by Decision 1 in `decision_log.md`.
