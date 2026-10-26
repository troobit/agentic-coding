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

- [x] 4. Runner selects one bounded task by default; explicit model mode preserves skill retrieval with regression coverage <!-- id:3zxyb99 -->
  - Default worker consumes runner selection; explicit model mode retains next-task retrieval and phase fallback. All 20 runner tests and full make test pass.
  - Blocked-by: 3zxyb98 (Makefile command and runbook explain invocation, logs, limits and resuming a halted run)

- [x] 5. Validate task paths and install a global local-next-task shell command <!-- id:3zxyb9a -->
  - Global command installed in ~/.local/bin. Global CLI and Make dry runs resolve ../atk/redteam/tasks.md to its own Git root and select task 1. Installation tests cover spaces, repeat runs and conflicts.
  - Blocked-by: 3zxyb99 (Runner selects one bounded task by default; explicit model mode preserves skill retrieval with regression coverage)

- [x] 6. Document orchestration choice, shell installation and invocation recovery <!-- id:3zxyb9b -->
  - Runbook, README, implementation notes and Decision 1 describe the modes and shell command. make lint-shell passes; full lint-drift is blocked by the pre-existing absent generated Copilot file. Live inference was unavailable because the LM Studio server was stopped.
  - Blocked-by: 3zxyb9a (Validate task paths and install a global local-next-task shell command)
