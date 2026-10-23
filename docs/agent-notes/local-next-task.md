# Local task execution

- `scripts/local_next_task.py` drives the existing skill through Codex's native
  LM Studio provider. `make local-next-task TASKS=... ARGS="..."` exposes it.
  The explicit ledger determines the target Git root; it is not inferred from
  this repository's branch.
- Each iteration is a new `codex exec` session with `--ignore-user-config` and
  `--ephemeral`. Model default is `8-bit`, the exact alias returned by this
  machine's LM Studio `/v1/models` endpoint. No user config is rewritten.
- The installed Codex emits model-metadata warnings for this LM Studio alias;
  live text responses and tool execution still work. Item-level metadata errors
  differ from fatal `turn.failed`/`error` events, which the runner checks.
- Rune `list` JSON uses capitalized `Tasks`, `ID`, `Status`, `Children` and
  integer status 2 for completion. `next`/phase JSON uses lowercase fields,
  string statuses and nested `children`. Phase results include blocked tasks;
  dependencies satisfied within the selected phase are expected, while an
  external dependency must halt. Inspect descendants for STOP gates too.
- Progress means at least one previously incomplete ID becomes complete. Model
  prose alone cannot advance the loop. IDs must stay fixed and completed work
  must remain complete. The runner never calls `rune complete` itself.
- Halt signals live at the target repository root (`.orbit/halt`) even though
  logs live beside the tasks file (`.orbit/local-next-task/run-*`). Existing
  halt files are preserved. Timeout/Ctrl+C terminates the child process group.
- `make test-local-next-task` exercises real rune ledgers with a fake Codex CLI
  in temporary Git repositories; it does not require a model or network.
- Live verification on 2026-10-24: `8-bit` implemented greeting and farewell
  functions in two disposable phases, added passing unit tests and completed
  the ledger. The initial 300-second smoke-test cap expired after phase one;
  rerunning with 900 seconds correctly selected phase two. Keep the normal
  1800-second default: local sessions can take several minutes.
- Full `make lint` includes a generated-file drift check that rewrites generated
  instructions temporarily. Avoid it when one of those files is already deleted
  in the user's working tree; `make lint-shell` is independent.
