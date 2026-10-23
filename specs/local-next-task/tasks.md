---
references:
    - specs/local-next-task/design.md
    - specs/local-next-task/decision_log.md
    - specs/local-next-task/requirements.md
---
# Local next-task runner

- [x] 1. Local 8-bit sessions advance an explicit task ledger and stop on completion, gates, failure or stalled progress <!-- id:3zxyb96 -->
  - Live LM Studio 8-bit implemented both disposable phases, ran make test and completed the rune ledger; resuming after a 300-second smoke-test timeout selected the remaining phase.

- [x] 2. Temporary-repository tests verify loop progress and stop conditions without calling a model <!-- id:3zxyb97 -->
  - 12 runner tests pass with fake Codex and real rune; full make test and make lint-shell pass.
  - Blocked-by: 3zxyb96 (Local 8-bit sessions advance an explicit task ledger and stop on completion, gates, failure or stalled progress)

- [x] 3. Makefile command and runbook explain invocation, logs, limits and resuming a halted run <!-- id:3zxyb98 -->
  - Makefile command, README pointers, docs/runbooks/local-next-task.md and implementation notes describe usage and recovery.
  - Blocked-by: 3zxyb96 (Local 8-bit sessions advance an explicit task ledger and stop on completion, gates, failure or stalled progress)
