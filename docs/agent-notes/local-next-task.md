# Local task execution

- `scripts/local_next_task.py` selects work with rune and runs it through Codex's
  native LM Studio provider. `make local-next-task TASKS=... ARGS="..."` exposes it.
  The explicit ledger determines the target Git root; it is not inferred from
  this repository's branch.
- Default `--selection runner` passes one `rune next` selection and exact rune
  progress/completion commands directly to the worker. It never invokes the
  `next-task` retrieval skill. `--phase` widens this to a whole phase. Explicit
  `--selection model` retains skill retrieval and the top-level-task phase
  fallback, with the runner's preflight selection as its boundary. Do not infer
  orchestration from LM Studio aliases. Decision 1 records the tradeoffs and
  primary-source guidance; there is no capability benchmark for the switch.
- `make install-local-next-task` runs `scripts/install-local-next-task.sh`, which
  links the executable Python file into `~/.local/bin/local-next-task` (Make
  override: `BIN_DIR`). Matching links are kept, foreign files/links/directories
  cause an error. `Path(__file__).resolve()` keeps skill paths in this checkout
  when invoked through the global symlink; task paths stay relative to the
  caller. The checkout must remain available. Installation is explicit and
  independent of client configuration sync.
- Make uses `TASKS=...`, while the global CLI takes a positional ledger. A
  missing Make variable previously passed an empty string, which Path resolved
  to a directory; Git discovery then ran from its parent and emitted a misleading
  Git-working-tree error. Make now checks the variable and Python checks blank
  and non-file paths before discovery.
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
  in temporary Git repositories; it does not require a model or network. The
  worker fake consumes the supplied selection rather than issuing `rune next`
  in runner mode. Coverage includes both modes, explicit phases, blank and
  directory paths, Make usage, global links, foreign-target preservation, and
  relative ledgers with spaces from outside this checkout.
- Live verification on 2026-10-24: `8-bit` implemented greeting and farewell
  functions in two disposable phases, added passing unit tests and completed
  the ledger. The initial 300-second smoke-test cap expired after phase one;
  rerunning with 900 seconds correctly selected phase two. Keep the normal
  1800-second default: local sessions can take several minutes.
- Verification on 2026-10-25: all 20 runner tests, full `make test`, and
  `make lint-shell` pass. The installed global command and Make wrapper both
  dry-run `../atk/redteam/tasks.md` against `/Users/r/repos/atk/redteam` and select
  its first task. No live inference check of the new prompt was possible because
  the local LM Studio endpoint refused connections.
- Full `make lint` includes a generated-file drift check that rewrites generated
  instructions temporarily. Avoid it when an expected file is absent (including
  an untracked generated file), since it cannot restore a missing snapshot;
  `make lint-shell` is independent.

## Orbit reuse assessment

- Judge simplicity by duplicated responsibilities and execution paths. This
  repo's 291-line runner owns a lifecycle that `~/repos/orbit` already owns:
  iteration, sessions, timeouts and logs. The preferred replacement is an Orbit
  agent profile and a thin global launcher, after preserving task dispatch and
  stop checks in Orbit. Nesting the two loops retains the duplication.
- Orbit's existing Codex agent accepts `model` and `extra-args`. A disposable
  run with the installed `v0.9.0-38-gadb2ad8` binary and fake Codex verified
  `--model 8-bit --oss --local-provider lmstudio`, config isolation, a workspace
  sandbox, the target working directory, saved logs and ledger completion.
  This verifies harness wiring, not local-model implementation quality.
- Use `auto-approve: false` in the alias and `--skip-permissions=false` on the
  Orbit invocation. The latter defaults to true and otherwise forces the Codex
  sandbox-bypass flag even when the alias says false. Pass the runner's existing
  sandbox/approval flags in `extra-args`. Disable pre/post prompts for parity.
- Orbit queries `rune next --phase`, but `internal/orbit/single.go` dispatches
  `o.config.Command` unchanged. Selection is used for phase bookkeeping rather
  than inserted into the implementation prompt. Native task dispatch must pass
  the selected work and references to the model, including a one-task option.
- Orbit currently lacks the runner's halt/progress checks. A disposable fake
  Codex session made no progress, wrote `.orbit/halt`, and emitted `ORBIT-HALT:`;
  Orbit still launched a second session. Preserve these checks, selected STOP
  gates, graph checks and Codex failed-turn handling before replacing the runner.
- Orbit's existing `specs/local-compute-agent/` draft already discusses progress
  guards. Its Decision 1 rationale that only OpenCode can use local endpoints is
  outdated for this LM Studio path: the Codex alias above works. This use case
  needs no new agent type or API client. Source reviewed at Orbit `08bbc33`.
