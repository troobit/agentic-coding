# Local next-task decisions

## Quick decisions

| Decision | Rationale |
| --- | --- |
| Use Codex's native LM Studio provider | The installed CLI supports local execution and discovers the existing skills; a live call to `8-bit` succeeded. |
| Start a fresh session after each selected group | The task ledger carries progress across sessions without accumulating the whole conversation in the model context. |
| Leave commits and phase reviews to the caller | The requested loop exposes the local model iteratively to tasks; it does not need make-it-so's delegation and release bookkeeping. |
| Use the checkout's skill manifests explicitly (superseded by Decision 1) | The original implementation always invoked next-task, which repeated retrieval already performed by the runner. |

---

## Decision 1: Select tasks in the runner by default

- **ID:** 1
- **Date:** 2026-10-25
- **Status:** Accepted
- **Context:** The runner already retrieves work with rune, but its prompt
  invokes `next-task`, which requires the model to retrieve the same work again.
  Its top-level fallback can also expand a single task into an entire phase.
  Local models spend context and tool calls on this mechanical work. An empty
  Make `TASKS` value resolves to the checkout directory and produces an unrelated
  Git-root error. The caller also needs a command usable outside this checkout.
- **Decision:** Select one task and descendants in Python by default; provide
  an explicit execution prompt and rune commands. Offer `--phase` for larger
  selections and `--selection model` for the original skill retrieval, retaining
  runner gate/blocker checks. Reject blank/directory paths. Install an executable
  symlink with `make install-local-next-task`; retain Make's variable syntax.
- **Rationale:** Predictable scheduling belongs in code; implementation still
  benefits from model judgment. An explicit mode supports comparison without
  assuming capability from an arbitrary local model name. A symlink keeps the
  command current and preserves skill path resolution without copying assets.
- **Alternatives Considered:**
  - Always invoke `next-task`: rejected because it repeats retrieval and widens
    small tasks into phases for models with limited context.
  - Infer orchestration mode from model names: rejected because LM Studio aliases
    carry no reliable capability information.
  - Copy the runner into a global bin directory: rejected because copies drift
    and relative skill paths would point outside the source checkout.
  - Treat Make goals as positional arguments: rejected because Make already
    has `TASKS=...`; a global CLI supplies the natural positional interface.
- **Consequences:**
  - Positive: fewer retrieval tool calls by default, smaller session scope,
    explicit comparison mode, useful path errors, and a command on shell PATH.
  - Negative: the default group size changes; callers wanting phases must pass
    `--phase`. Model mode still has retrieval overhead. The global link depends
    on the checkout remaining in place and its bin directory being on PATH.

### References

- [Building effective agents](https://www.anthropic.com/research/building-effective-agents)
  distinguishes predictable code-driven workflows from dynamic model decisions.
- [Effective harnesses for long-running agents](https://www.anthropic.com/research/effective-harnesses-for-long-running-agents)
  describes incremental sessions, durable progress, and validation before
  marking work complete. These support the design choice; they do not benchmark
  this runner or establish a capability threshold for switching modes.
