# Run tasks with LM Studio

Start LM Studio's local server with a tool-capable model loaded. The default
model ID for this runner is exactly `8-bit`, verified against this machine's
`http://127.0.0.1:1234/v1/models` endpoint. Git, rune, Python 3.9+ and Codex CLI
must be on PATH.

From the agentic-coding checkout, preview the next invocation:

```sh
make local-next-task TASKS=/path/to/project/specs/feature/tasks.md ARGS="--dry-run"
```

Then run the loop:

```sh
make local-next-task TASKS=/path/to/project/specs/feature/tasks.md
```

The target can be in another repository. The runner finds its Git root and
sets that as the agent's working directory. The explicit ledger path is passed
to rune and included in the prompt with the selected tasks and spec references.
Use one runner per checkout at a time.

Each iteration starts `codex exec --oss --local-provider lmstudio --model 8-bit`
and explicitly invokes the existing `next-task` and rune skill manifests.
After the session returns, the runner re-reads the ledger. Newly completed
tasks allow the loop to continue in a fresh session. The model marks its own
tasks complete after validation; the runner never completes tasks for it.

The default selection follows `next-task`: retrieve the next task, falling back
to the whole phase when rune returns a top-level task ID. For small model
contexts, keep task groups and phases modest. To request phases explicitly or
change the model and limits:

```sh
make local-next-task TASKS=/path/to/project/specs/feature/tasks.md \
  ARGS="--phase --model 8-bit --max-iterations 10 --timeout 1800"
```

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
