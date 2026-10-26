# Run tasks with LM Studio

Start LM Studio's local server with a tool-capable model loaded. The default
model ID for this runner is exactly `8-bit`, verified against this machine's
`http://127.0.0.1:1234/v1/models` endpoint. Git, rune, Python 3.9+ and Codex CLI
must be on PATH.

Install the shell command once from the agentic-coding checkout:

```sh
make install-local-next-task
```

This links `~/.local/bin/local-next-task` to the runner in this checkout.
Keep the checkout available and put `~/.local/bin` on PATH. Existing foreign
files or links are preserved; reinstalling the same command is safe. Override
the install location with `make install-local-next-task BIN_DIR=/path/to/bin`.

Then use it from any directory, with a ledger path relative to that directory
or an absolute path. For example, from the agentic-coding checkout:

```sh
local-next-task ../atk/redteam/tasks.md --dry-run
local-next-task ../atk/redteam/tasks.md
```

The Make wrapper remains available from this checkout:

```sh
make local-next-task TASKS=/path/to/project/specs/feature/tasks.md ARGS="--dry-run"
```

Then run the loop:

```sh
make local-next-task TASKS=/path/to/project/specs/feature/tasks.md
```

Make takes `TASKS=...`, not a positional file path. A missing value now prints
usage; blank paths and directories are rejected before Git discovery. The
previous empty value resolved to a directory and caused the misleading
"tasks file must be inside a Git working tree" error.

The target can be in another repository. The runner finds its Git root and
sets that as the agent's working directory. The explicit ledger path is passed
to rune and included in the prompt with the selected tasks and spec references.
Use one runner per checkout at a time.

Each iteration starts `codex exec --oss --local-provider lmstudio --model 8-bit`.
By default Python runs `rune next`, checks the selection, and passes the work,
spec references, and exact rune progress/completion commands to the model.
The model implements that selection without retrieving work again.
After the session returns, the runner re-reads the ledger. Newly completed
tasks allow the loop to continue in a fresh session. The model marks its own
tasks complete after validation; the runner never completes tasks for it.

The default is one rune task and its descendants. It does not expand a
top-level task into a whole phase. For small model contexts, keep task groups
modest. Request phases explicitly or change the model and limits:

```sh
local-next-task /path/to/project/specs/feature/tasks.md \
  --phase --model 8-bit --max-iterations 10 --timeout 1800
```

To compare the original skill-driven retrieval with a more capable model:

```sh
local-next-task /path/to/project/specs/feature/tasks.md \
  --model your-model-id --selection model
```

`--selection runner` is the default. `--selection model` invokes the existing
`next-task` and rune skills and preserves their top-level-task phase fallback.
Python still preflights the selection for STOP gates and blockers; the model
must retrieve the same selection and halt if it differs. Both modes retain
ledger-based progress checks and fresh sessions. Model names do not select a
mode automatically: LM Studio aliases do not reliably indicate capability.
With Make, pass switches inside `ARGS="..."`.

This design applies the distinction between predictable workflows and dynamic
model decisions described in [Building effective agents](https://www.anthropic.com/research/building-effective-agents).
Task scheduling is predictable here; code owns it, while the model owns
implementation. The single-task default and persisted progress also follow
the incremental-session pattern in [Effective harnesses for long-running agents](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents).
These sources support the pattern; neither benchmarks this runner or proves
that a particular model benefits from switching modes.

Defaults are 20 iterations and 1800 seconds per session. `--model` accepts the
exact ID reported by LM Studio, including aliases such as `8-bit`.

The loop stops when all tasks are complete, the next selection contains a STOP
gate or an external dependency blocker, `.orbit/halt` exists in the target
repository root, the model emits `ORBIT-HALT:`, an agent fails or times out,
task IDs change or completed work reopens, no task completes, or the iteration
limit is reached. Exit status is 0 for completion or a successful dry run, 2
for a halt/error, and 130 for Ctrl+C (Make reports command failure as status 2).

Each run prints its log location. Files live beside the ledger under
`.orbit/local-next-task/run-*/`: `001.prompt.txt`, `001.jsonl` (combined process
output), `001.final.txt`, and equivalent files for subsequent iterations.
Inspect the prompt, final response and diff when a run halts. Resolve any
blocker and, if a root `.orbit/halt` exists, remove or archive it deliberately
before rerunning the same command. The ledger preserves progress across runs.
An iteration-limit halt needs only another invocation.

Sessions use Codex's `workspace-write` sandbox with approval policy `never`.
They ignore user config so unrelated MCP servers, plugins and cloud defaults
are not inherited. They still read project instructions and skills. The runner
instructs the model to leave changes for review without committing or pushing;
it implements the iterative part of `make-it-so`, without phase review or
automatic commit bookkeeping.

The native provider and non-interactive flags are documented in the
[official Codex CLI reference](https://developers.openai.com/codex/cli/reference).
