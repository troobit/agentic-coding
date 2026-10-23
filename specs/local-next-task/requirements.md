# Local next-task requirements

## Purpose

Expose a local LM Studio model iteratively to a rune tasks file, following the
existing `next-task` workflow while keeping each model session small.

## Requirements

1. The runner MUST accept an explicit tasks file in a Git working tree, use
   that repository as the working directory, and default to model ID `8-bit`.
   The caller MUST be able to choose a different LM Studio model ID.
2. Each iteration MUST retrieve work with rune and invoke the existing
   `next-task` skill in a fresh session. The runner MUST support phase selection
   and follow the skill's top-level-task fallback. It MUST read the ledger
   again before advancing and MUST NOT mark work complete itself.
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
