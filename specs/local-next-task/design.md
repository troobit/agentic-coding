# Local next-task runner

## Requirements

- Accept an explicit rune tasks file in a Git repository and use LM Studio's
  `8-bit` model by default. Allow a different model ID.
- Run the existing `next-task` skill once per fresh Codex session, then re-read
  the ledger before starting another session. Offer an explicit phase mode.
- Stop on completion, STOP gates, blocked work, `.orbit/halt`, an agent error,
  timeout, no newly completed tasks, or the iteration limit.
- Preserve logs for each iteration and offer a dry run without model calls or
  filesystem writes. Never mark tasks complete on the model's behalf.
- Leave changes available for review; the runner does not commit or push.

## Approach

Add `scripts/local_next_task.py` using Python's standard library, exposed through
`make local-next-task TASKS=/path/to/specs/feature/tasks.md ARGS="..."`.
Resolve the Git root from the explicit ledger, pass that root to Codex, and pass
the absolute ledger path to every rune command. Use rune's JSON output for
selection and before/after completion checks. Follow next-task's top-level
task fallback to phase retrieval; pass the selected JSON and explicit skill
paths in the prompt so the local model has an unambiguous work boundary.

Invoke `codex exec --oss --local-provider lmstudio --model 8-bit` with a writable
workspace sandbox and approval policy `never`. Ignore user config for these
sessions so unrelated MCP services, plugins and cloud model settings are not
inherited. Keep native skill discovery and explicitly point to this repo's
next-task and rune manifests. Execute sequentially on the current checkout.
Store the prompt, combined process log and final response for each iteration
under the task file's `.orbit/local-next-task/` directory. Use a process timeout
and stop its process group on interruption or timeout. Never remove a halt file.

## Portability assumptions

- Python 3.9+, Git, rune and Codex CLI are on PATH; Codex supports the flags
  above, including `--ignore-user-config`, `--ephemeral` and `--json`.
- LM Studio is serving a tool-capable model on its default local endpoint
  (`http://127.0.0.1:1234/v1`). Its model ID is exactly `8-bit` on this machine,
  verified using `/v1/models` and a live Codex smoke test on 2026-10-24.
- The runner and linked skills remain in this checkout. Paths are resolved
  from the script, not the user's home directory.
- macOS/Linux process groups are available. Host permissions still apply;
  approvals required by the target project cause a halt, not automatic consent.
- This is the iterative implementation part of make-it-so. Parallel worktrees,
  phase reviews, automatic commits and changelog automation remain outside scope.

## Validation

Use fake Codex and real rune in temporary Git repositories to exercise progress,
completion, blocked work, gates, halt output, failures, timeouts and dry runs.
Run `make test` and relevant Makefile lint targets. Verify the real local model
can use tools on a disposable tasks file; never launch it on an unnamed spec.
