---
references:
    - specs/dreaming/requirements.md
    - specs/dreaming/design.md
    - specs/dreaming/decision_log.md
---
# Dreaming

## Foundation

- [ ] 1. Scaffold the project and private home on the dreaming branch <!-- id:w1na5cz -->
  - Stream: 1
  - Requirements: [6.4](requirements.md#6.4), [14.4](requirements.md#14.4)
  - [ ] 1.1. Write tests for the private home and CLI entry <!-- id:w1na5d0 -->
    - tests/test_home.py: `DREAMING_HOME` created mode 0700; refuses a location inside any git repository; `dream --version` runs from an installed wheel with no checkout of agentic-coding on the path
    - Stream: 1
    - Requirements: [6.4](requirements.md#6.4), [14.4](requirements.md#14.4)
  - [ ] 1.2. Create the project skeleton and implement the home checks <!-- id:w1na5d1 -->
    - repository root is this checkout on branch `dreaming`; pyproject.toml (Python 3.12+, uv, ruff, pytest, hypothesis), Makefile with `test`, `lint`, `install`, src/dreaming/{cli,config}.py, instructions/ and tests/ directories; no import from agentic-coding
    - Blocked-by: w1na5d0 (Write tests for the private home and CLI entry)
    - Stream: 1
    - Requirements: [6.4](requirements.md#6.4), [14.4](requirements.md#14.4)

- [ ] 2. SQLite store and migrations <!-- id:w1na5d2 -->
  - Blocked-by: w1na5cz (Scaffold the project and private home on the dreaming branch)
  - Stream: 1
  - Requirements: [6.1](requirements.md#6.1), [6.3](requirements.md#6.3), [6.5](requirements.md#6.5), [6.6](requirements.md#6.6), [6.7](requirements.md#6.7), [7.5](requirements.md#7.5), [13.2](requirements.md#13.2), [13.7](requirements.md#13.7), [13.8](requirements.md#13.8)
  - [ ] 2.1. Write tests for schema, WAL and additive migrations <!-- id:w1na5d3 -->
    - Every table in the design Data Models exists; WAL with busy timeout; migrations are additive and refuse with `migration_blocked` while an unfinished run exists; a second connection can write while a run holds a transaction
    - Blocked-by: w1na5cz (Scaffold the project and private home on the dreaming branch)
    - Stream: 1
    - Requirements: [6.3](requirements.md#6.3), [7.5](requirements.md#7.5)
  - [ ] 2.2. Implement src/dreaming/store.py <!-- id:w1na5d4 -->
    - Integer `user_version` migrations; tables runs, steps, sessions_seen, calls, observations, file_findings, research_findings, patterns, knowledge_items, knowledge_revisions, feedback, changes, adoption, registrations, learning, replays, currency_findings; all evidence stored redacted with source-availability markers
    - Blocked-by: w1na5d3 (Write tests for schema, WAL and additive migrations)
    - Stream: 1
    - Requirements: [6.1](requirements.md#6.1), [6.5](requirements.md#6.5), [6.6](requirements.md#6.6), [6.7](requirements.md#6.7), [13.2](requirements.md#13.2), [13.7](requirements.md#13.7), [13.8](requirements.md#13.8)

- [ ] 3. Configuration, lens loading and run snapshot <!-- id:w1na5d5 -->
  - Blocked-by: w1na5cz (Scaffold the project and private home on the dreaming branch)
  - Stream: 1
  - Requirements: [1.2](requirements.md#1.2), [2.2](requirements.md#2.2), [2.3](requirements.md#2.3), [2.9](requirements.md#2.9), [5.1](requirements.md#5.1), [5.2](requirements.md#5.2), [7.1](requirements.md#7.1), [7.3](requirements.md#7.3), [9.12](requirements.md#9.12)
  - [ ] 3.1. Write tests for config parsing and the start-of-run snapshot <!-- id:w1na5d6 -->
    - Instructions read with `git show <default>:instructions/...`, not the working tree; snapshot copied to runs/<id>/snapshot/; names list read only from a path outside every repository and never copied; defaults for budgets, thresholds, tool lists, classification rules and origin mappings; invalid config exits 2
    - Blocked-by: w1na5cz (Scaffold the project and private home on the dreaming branch)
    - Stream: 1
    - Requirements: [7.1](requirements.md#7.1), [7.3](requirements.md#7.3), [9.12](requirements.md#9.12)
  - [ ] 3.2. Implement src/dreaming/config.py and the snapshot writer <!-- id:w1na5d7 -->
    - TOML config at `~/.dreaming/config.toml`; lenses.toml loader with versions and domain/project/workflow applicability; local/cloud classification and non-interactive origin rules; per-role backend fallback lists and per-run overrides
    - Blocked-by: w1na5d6 (Write tests for config parsing and the start-of-run snapshot)
    - Stream: 1
    - Requirements: [1.2](requirements.md#1.2), [2.2](requirements.md#2.2), [2.3](requirements.md#2.3), [2.9](requirements.md#2.9), [5.1](requirements.md#5.1), [5.2](requirements.md#5.2), [7.1](requirements.md#7.1)

- [ ] 4. Probe set for harness isolation and structured output <!-- id:w1na5d8 -->
  - Blocked-by: w1na5cz (Scaffold the project and private home on the dreaming branch)
  - Stream: 1
  - Requirements: [1.7](requirements.md#1.7), [4.4](requirements.md#4.4), [5.5](requirements.md#5.5), [5.7](requirements.md#5.7), [5.8](requirements.md#5.8)
  - [ ] 4.1. Write tests for the backend probes with fake claude and codex executables <!-- id:w1na5d9 -->
    - Probe result records version, tool list, instruction/skill/agent-tool leakage, structured-output option support, whether apsis finds the call's session, and whether the agent-launch tool can be removed; results cached by backend version; a dry run reads only the cache and `--version` and labels results cached or unprobed
    - Blocked-by: w1na5cz (Scaffold the project and private home on the dreaming branch)
    - Stream: 1
    - Requirements: [1.7](requirements.md#1.7), [5.5](requirements.md#5.5)
  - [ ] 4.2. Implement src/dreaming/backends/probe.py and `dream probe` <!-- id:w1na5da -->
    - Claude: `--safe-mode` first, then the `--setting-sources ""` set, run from a cwd under DREAMING_HOME. Codex: `codex debug prompt-input` plus a real exec session for the tool list; skills block off; saved `--json` stream registered with apsis. LM Studio via the harness. Probe calls count against the budget and are tagged as the dream's own
    - Blocked-by: w1na5d9 (Write tests for the backend probes with fake claude and codex executables)
    - Stream: 1
    - Requirements: [4.4](requirements.md#4.4), [5.5](requirements.md#5.5), [5.7](requirements.md#5.7), [5.8](requirements.md#5.8)
  - [ ] 4.3. Add opt-in live probe tests (`make test-live`) <!-- id:w1na5db -->
    - Assert the design's assumptions against the installed claude, codex and LM Studio: no ~/.claude or ~/.codex instructions in context, no spawn_agent reachable or enforcement works, apsis opens the session, structured-output flag works; skipped when a tool or login is absent
    - Blocked-by: w1na5da (Implement src/dreaming/backends/probe.py and `dream probe`)
    - Stream: 1
    - Requirements: [4.4](requirements.md#4.4), [5.5](requirements.md#5.5), [5.8](requirements.md#5.8)

- [ ] 5. apsis client and contract checks <!-- id:w1na5dc -->
  - Blocked-by: w1na5cz (Scaffold the project and private home on the dreaming branch)
  - Stream: 1
  - Requirements: [2.1](requirements.md#2.1), [2.4](requirements.md#2.4), [3.1](requirements.md#3.1), [3.2](requirements.md#3.2), [3.3](requirements.md#3.3), [3.4](requirements.md#3.4), [3.5](requirements.md#3.5), [12.1](requirements.md#12.1)
  - [ ] 5.1. Write contract tests against recorded apsis shared-json fixtures <!-- id:w1na5dd -->
    - Listing across all projects; session documents for claude, codex, codex-exec, copilot, kiro and lmstudio; thread_id present for LM Studio and Codex-served sessions; provider and origin recorded as the source records them; unknown schema_version rejected; opt-in live variant against installed apsis
    - Blocked-by: w1na5cz (Scaffold the project and private home on the dreaming branch)
    - Stream: 1
    - Requirements: [2.1](requirements.md#2.1), [3.1](requirements.md#3.1), [3.2](requirements.md#3.2), [3.3](requirements.md#3.3), [3.4](requirements.md#3.4), [3.5](requirements.md#3.5)
  - [ ] 5.2. Implement src/dreaming/sessions.py apsis client <!-- id:w1na5de -->
    - Subprocess wrapper for `apsis --all-projects --list -f shared-json` and `apsis <id> -s <source> -f shared-json`; typed listing rows and session documents; no source parsing in this repository
    - Blocked-by: w1na5dd (Write contract tests against recorded apsis shared-json fixtures)
    - Stream: 1
    - Requirements: [2.1](requirements.md#2.1), [12.1](requirements.md#12.1)

## Sessions

- [ ] 6. Session selection, dedupe and splitting <!-- id:w1na5df -->
  - Blocked-by: w1na5d2 (SQLite store and migrations), w1na5d5 (Configuration, lens loading and run snapshot), w1na5dc (apsis client and contract checks)
  - Stream: 1
  - Requirements: [1.3](requirements.md#1.3), [1.4](requirements.md#1.4), [1.5](requirements.md#1.5), [2.4](requirements.md#2.4), [2.5](requirements.md#2.5), [2.6](requirements.md#2.6), [2.7](requirements.md#2.7), [2.8](requirements.md#2.8)
  - [ ] 6.1. Write tests for selection, de-duplication and splitting <!-- id:w1na5dg -->
    - Newest-first within budget; unread additions only under unchanged lens versions; date, project and reread filters; exclude the running dream (thread_id == run id, calls.session_ref, cwd under DREAMING_HOME) and recent files; earlier dreams tagged subject=dreaming; one interaction per thread_id with harness content plus log metadata; unparseable sessions skipped with reason; scoped dreams; property: every entry lands in exactly one split part, each part fits
    - Blocked-by: w1na5d2 (SQLite store and migrations), w1na5d5 (Configuration, lens loading and run snapshot), w1na5dc (apsis client and contract checks)
    - Stream: 1
    - Requirements: [1.3](requirements.md#1.3), [1.4](requirements.md#1.4), [1.5](requirements.md#1.5), [2.4](requirements.md#2.4), [2.5](requirements.md#2.5), [2.6](requirements.md#2.6), [2.7](requirements.md#2.7), [2.8](requirements.md#2.8)
  - [ ] 6.2. Implement selection, dedupe and splitting in sessions.py <!-- id:w1na5dh -->
    - Consecutive entry ranges sized to the reader context after the prompt; an oversized entry is cut with a truncation marker; unattributed server warnings go to the report only
    - Blocked-by: w1na5dg (Write tests for selection, de-duplication and splitting)
    - Stream: 1
    - Requirements: [1.3](requirements.md#1.3), [1.4](requirements.md#1.4), [1.5](requirements.md#1.5), [2.4](requirements.md#2.4), [2.5](requirements.md#2.5), [2.6](requirements.md#2.6), [2.7](requirements.md#2.7), [2.8](requirements.md#2.8)

- [ ] 7. Attribution, registration and forgetting <!-- id:w1na5di -->
  - Blocked-by: w1na5df (Session selection, dedupe and splitting)
  - Stream: 1
  - Requirements: [2.2](requirements.md#2.2), [2.3](requirements.md#2.3), [2.9](requirements.md#2.9), [2.10](requirements.md#2.10), [2.11](requirements.md#2.11), [14.8](requirements.md#14.8)
  - [ ] 7.1. Write tests for attribution, registration and forgetting <!-- id:w1na5dj -->
    - Harness, model per entry, provider, local/cloud, project (worktree counts as parent), domain, workflow; unmapped sources listed; non-interactive and registered sessions present prompts as role `tool` except user-quote entries; late registration reclassifies and marks items pending reassessment; forget/restore properties from the design (counts and rankings equal the non-forgotten computation; restore returns original values; repeat calls change nothing; selection and registration reject forgotten sessions)
    - Blocked-by: w1na5df (Session selection, dedupe and splitting)
    - Stream: 1
    - Requirements: [2.2](requirements.md#2.2), [2.3](requirements.md#2.3), [2.9](requirements.md#2.9), [2.10](requirements.md#2.10), [2.11](requirements.md#2.11), [14.8](requirements.md#14.8)
  - [ ] 7.2. Implement attribution, registration and forget/restore <!-- id:w1na5dk -->
    - registrations table keyed by (tool, run ref, session); forgotten flag filtered in every count, ranking, rate and replay query; items left without 4.5 or 13.3 support withheld at once; forgotten observations never passed to a role
    - Blocked-by: w1na5dj (Write tests for attribution, registration and forgetting)
    - Stream: 1
    - Requirements: [2.2](requirements.md#2.2), [2.9](requirements.md#2.9), [2.10](requirements.md#2.10), [2.11](requirements.md#2.11), [14.8](requirements.md#14.8)

## Run engine

- [ ] 8. Steps, calls, budget, lock and resume <!-- id:w1na5dl -->
  - Blocked-by: w1na5d2 (SQLite store and migrations), w1na5d5 (Configuration, lens loading and run snapshot)
  - Stream: 1
  - Requirements: [1.1](requirements.md#1.1), [1.2](requirements.md#1.2), [1.6](requirements.md#1.6), [4.1](requirements.md#4.1), [4.8](requirements.md#4.8), [5.4](requirements.md#5.4), [5.6](requirements.md#5.6), [6.3](requirements.md#6.3), [7.3](requirements.md#7.3), [7.5](requirements.md#7.5)
  - [ ] 8.1. Write tests for the step table, lock, budget and crash consistency <!-- id:w1na5dm -->
    - Next ready step by dependencies; follow-up steps inserted in the same transaction as results; raw output stored on the calls row and applied on resume without a model call; flock held by the detached child and a second start exits 4 changing nothing; wall-clock counts only while running; budget equals the sum of recorded calls including retries; property: for any crash point and a fake model whose answers differ per call, resume matches an uninterrupted run; budget exhaustion ends the run and reports without model calls; exit codes 0,1,2,4,5
    - Blocked-by: w1na5d2 (SQLite store and migrations), w1na5d5 (Configuration, lens loading and run snapshot)
    - Stream: 1
    - Requirements: [1.1](requirements.md#1.1), [1.2](requirements.md#1.2), [1.6](requirements.md#1.6), [5.4](requirements.md#5.4), [5.6](requirements.md#5.6), [6.3](requirements.md#6.3), [7.5](requirements.md#7.5)
  - [ ] 8.2. Implement steps.py, budget.py and run.py <!-- id:w1na5dn -->
    - Calls row written before each call; stable runner-assigned step keys; resume keeps selection, remaining budget and overrides and rejects other overrides; run record, interrupted-run detection by process group; limits checked only between steps
    - Blocked-by: w1na5dm (Write tests for the step table, lock, budget and crash consistency)
    - Stream: 1
    - Requirements: [1.2](requirements.md#1.2), [1.6](requirements.md#1.6), [4.1](requirements.md#4.1), [4.8](requirements.md#4.8), [5.4](requirements.md#5.4), [5.6](requirements.md#5.6), [7.3](requirements.md#7.3), [7.5](requirements.md#7.5)

- [ ] 9. Dry run and rendered plan <!-- id:w1na5do -->
  - Blocked-by: w1na5d8 (Probe set for harness isolation and structured output), w1na5df (Session selection, dedupe and splitting), w1na5dl (Steps, calls, budget, lock and resume)
  - Stream: 1
  - Requirements: [1.7](requirements.md#1.7), [5.5](requirements.md#5.5)
  - [ ] 9.1. Write tests for dry run and the rune-format plan view <!-- id:w1na5dp -->
    - Dry run lists sessions, backend per role and budget, calls no model and changes no file or row; backend status labelled cached or unprobed; `dream status --plan` renders steps to runs/<id>/tasks-dream.md which real `rune list` parses and which is never read back
    - Blocked-by: w1na5d8 (Probe set for harness isolation and structured output), w1na5df (Session selection, dedupe and splitting), w1na5dl (Steps, calls, budget, lock and resume)
    - Stream: 1
    - Requirements: [1.7](requirements.md#1.7), [5.5](requirements.md#5.5)
  - [ ] 9.2. Implement `dream run --dry-run` and plan.py <!-- id:w1na5dq -->
    - Plan renderer is read-only output; verifies the design assumption that rune parses the rendered file
    - Blocked-by: w1na5dp (Write tests for dry run and the rune-format plan view)
    - Stream: 1
    - Requirements: [1.7](requirements.md#1.7), [5.5](requirements.md#5.5)

- [ ] 10. Versioned installs and launcher <!-- id:w1na5dr -->
  - Blocked-by: w1na5dl (Steps, calls, budget, lock and resume)
  - Stream: 1
  - Requirements: [7.3](requirements.md#7.3)
  - [ ] 10.1. Write tests for version pinning <!-- id:w1na5ds -->
    - Launcher runs `current` for a new run and the recorded revision for resume; a version directory is kept while any unfinished run records it; an adopted change to dreaming code does not alter a running or resumed run
    - Blocked-by: w1na5dl (Steps, calls, budget, lock and resume)
    - Stream: 1
    - Requirements: [7.3](requirements.md#7.3)
  - [ ] 10.2. Implement `make install` and the launcher <!-- id:w1na5dt -->
    - Installs into ~/.dreaming/versions/<revision>/, repoints current, links ~/.local/bin/dream; refuses to overwrite a foreign file
    - Blocked-by: w1na5ds (Write tests for version pinning)
    - Stream: 1
    - Requirements: [7.3](requirements.md#7.3)

## Backends and roles

- [ ] 11. Backend dispatcher: retry, fallback and circuit breaker <!-- id:w1na5du -->
  - Blocked-by: w1na5d8 (Probe set for harness isolation and structured output), w1na5dl (Steps, calls, budget, lock and resume)
  - Stream: 1
  - Requirements: [1.2](requirements.md#1.2), [4.7](requirements.md#4.7), [4.8](requirements.md#4.8), [5.2](requirements.md#5.2), [5.3](requirements.md#5.3), [5.4](requirements.md#5.4), [5.6](requirements.md#5.6)
  - [ ] 11.1. Write tests for retry, fallback and accounting with a scripted fake backend <!-- id:w1na5dv -->
    - One retry per backend; two transport failures mark the backend unavailable for the run and move to the next (its own single retry); two schema failures mark the input failed and not retried by later dreams unless reselected; breaker_k consecutive schema failures disable the backend; usage-limit errors count as transport failures; missing usage estimated as ceil(bytes/4) and flagged; inputs resized for the smallest context in the fallback list; no backend left saves progress and exits 5
    - Blocked-by: w1na5d8 (Probe set for harness isolation and structured output), w1na5dl (Steps, calls, budget, lock and resume)
    - Stream: 1
    - Requirements: [4.7](requirements.md#4.7), [5.2](requirements.md#5.2), [5.3](requirements.md#5.3), [5.4](requirements.md#5.4), [5.6](requirements.md#5.6)
  - [ ] 11.2. Implement src/dreaming/backends/__init__.py dispatcher <!-- id:w1na5dw -->
    - Backend protocol (probe, call), per-call timeout with process-group kill, structured-output validation against the role schema independent of the backend option
    - Blocked-by: w1na5dv (Write tests for retry, fallback and accounting with a scripted fake backend)
    - Stream: 1
    - Requirements: [1.2](requirements.md#1.2), [4.8](requirements.md#4.8), [5.3](requirements.md#5.3), [5.6](requirements.md#5.6)

- [ ] 12. Claude Code and Codex harness adapters <!-- id:w1na5dx -->
  - Blocked-by: w1na5du (Backend dispatcher: retry, fallback and circuit breaker)
  - Stream: 1
  - Requirements: [4.4](requirements.md#4.4), [4.6](requirements.md#4.6), [5.1](requirements.md#5.1), [5.7](requirements.md#5.7), [5.8](requirements.md#5.8)
  - [ ] 12.1. Write tests for the harness adapters with fake executables <!-- id:w1na5dy -->
    - Per-call MCP config filtered through the role allowlist; devtools started with ENABLE_ADDITIONAL_TOOLS omitting codex-agent and gemini-agent; Claude isolation flags and env vars; Codex events saved under runs/<id>/codex/ and the call killed on an agent-launch event; explicit tools list without Agent; no permission prompt can block; calls row has the harness session id
    - Blocked-by: w1na5du (Backend dispatcher: retry, fallback and circuit breaker)
    - Stream: 1
    - Requirements: [4.4](requirements.md#4.4), [5.7](requirements.md#5.7), [5.8](requirements.md#5.8)
  - [ ] 12.2. Implement backends/claude.py and backends/codex.py <!-- id:w1na5dz -->
    - Use the flag set the probe confirmed; a harness using LM Studio receives its role tools from the same filtered definitions; researchers can read repositories, PR threads and search and fetch the web
    - Blocked-by: w1na5dy (Write tests for the harness adapters with fake executables)
    - Stream: 1
    - Requirements: [4.4](requirements.md#4.4), [4.6](requirements.md#4.6), [5.1](requirements.md#5.1), [5.7](requirements.md#5.7), [5.8](requirements.md#5.8)

- [ ] 13. LM Studio direct adapter for tool-free roles <!-- id:w1na5e0 -->
  - Blocked-by: w1na5du (Backend dispatcher: retry, fallback and circuit breaker)
  - Stream: 1
  - Requirements: [4.4](requirements.md#4.4), [5.1](requirements.md#5.1), [5.8](requirements.md#5.8)
  - [ ] 13.1. Write tests for the LM Studio adapter against a local fake HTTP server <!-- id:w1na5e1 -->
    - client_metadata.thread_id (the run id) is the first key of the request body; context read per call from the loaded model; tool-using roles are refused; truncation-safe record of the call
    - Blocked-by: w1na5du (Backend dispatcher: retry, fallback and circuit breaker)
    - Stream: 1
    - Requirements: [5.1](requirements.md#5.1), [5.8](requirements.md#5.8)
  - [ ] 13.2. Implement backends/lmstudio.py <!-- id:w1na5e2 -->
    - OpenAI-compatible chat completion with JSON-schema response format where supported; server-log entry suffices as the dream-call record
    - Blocked-by: w1na5e1 (Write tests for the LM Studio adapter against a local fake HTTP server)
    - Stream: 1
    - Requirements: [5.1](requirements.md#5.1), [5.8](requirements.md#5.8)

- [ ] 14. Roles, schemas and the instruction set <!-- id:w1na5e3 -->
  - Blocked-by: w1na5d5 (Configuration, lens loading and run snapshot), w1na5du (Backend dispatcher: retry, fallback and circuit breaker)
  - Stream: 1
  - Requirements: [4.2](requirements.md#4.2), [4.3](requirements.md#4.3), [4.4](requirements.md#4.4), [5.2](requirements.md#5.2), [7.1](requirements.md#7.1), [7.2](requirements.md#7.2)
  - [ ] 14.1. Write tests for role inputs, schemas and lens loading <!-- id:w1na5e4 -->
    - Reader, reviewer, researcher, author and replayer schemas validate good and bad outputs; reviewer input holds summaries and evidence ids and never transcripts; inputs fit the smallest context in the fallback list; no role tool list contains an agent-launching tool; initial lenses cover every item in 7.2
    - Blocked-by: w1na5d5 (Configuration, lens loading and run snapshot), w1na5du (Backend dispatcher: retry, fallback and circuit breaker)
    - Stream: 1
    - Requirements: [4.2](requirements.md#4.2), [4.3](requirements.md#4.3), [4.4](requirements.md#4.4), [7.2](requirements.md#7.2)
  - [ ] 14.2. Implement roles.py and author instructions/ <!-- id:w1na5e5 -->
    - instructions/lenses.toml with the 7.2 initial lenses and versions, roles/{reader,reviewer,researcher,author,replayer}.md, schemas/*.json, config.example.toml; replayer is tool-free and sees only the instruction under replay
    - Blocked-by: w1na5e4 (Write tests for role inputs, schemas and lens loading)
    - Stream: 1
    - Requirements: [4.2](requirements.md#4.2), [4.3](requirements.md#4.3), [4.4](requirements.md#4.4), [7.1](requirements.md#7.1), [7.2](requirements.md#7.2)

## Observations and knowledge

- [ ] 15. Observation verification, redaction and attribution gate <!-- id:w1na5e6 -->
  - Blocked-by: w1na5d2 (SQLite store and migrations), w1na5di (Attribution, registration and forgetting), w1na5e3 (Roles, schemas and the instruction set)
  - Stream: 1
  - Requirements: [2.9](requirements.md#2.9), [6.1](requirements.md#6.1), [6.2](requirements.md#6.2), [6.3](requirements.md#6.3), [12.3](requirements.md#12.3), [13.1](requirements.md#13.1)
  - [ ] 15.1. Write tests and property tests for verification and redaction <!-- id:w1na5e7 -->
    - Property: for any entry text and quote drawn from it, verify holds before redaction and redaction is idempotent; mismatch at the recorded location is rejected and counted; reprocessing under unchanged lens versions creates no duplicates; `user_statement` rejected on tool-attributed entries; modality and outcome labels stored; assistant claims of success never become confirmed outcomes
    - Blocked-by: w1na5d2 (SQLite store and migrations), w1na5di (Attribution, registration and forgetting), w1na5e3 (Roles, schemas and the instruction set)
    - Stream: 1
    - Requirements: [2.9](requirements.md#2.9), [6.2](requirements.md#6.2), [6.3](requirements.md#6.3), [13.1](requirements.md#13.1)
  - [ ] 15.2. Implement observe.py and redact.py <!-- id:w1na5e8 -->
    - Credential patterns seeded from agentic-coding scripts/review_html/redact.py with source path, revision and licence recorded in the module header; evidence id, source location (entry id plus representation version), lens id and version, producing backend and model
    - Blocked-by: w1na5e7 (Write tests and property tests for verification and redaction)
    - Stream: 1
    - Requirements: [6.1](requirements.md#6.1), [6.2](requirements.md#6.2), [12.3](requirements.md#12.3)

- [ ] 16. Reader phase and deterministic clustering <!-- id:w1na5e9 -->
  - Blocked-by: w1na5df (Session selection, dedupe and splitting), w1na5dl (Steps, calls, budget, lock and resume), w1na5e3 (Roles, schemas and the instruction set), w1na5e6 (Observation verification, redaction and attribution gate)
  - Stream: 1
  - Requirements: [4.3](requirements.md#4.3), [6.1](requirements.md#6.1), [6.5](requirements.md#6.5)
  - [ ] 16.1. Write tests for the reader step and clustering with a fake model <!-- id:w1na5ea -->
    - Batch to observations through the dispatcher; deterministic pass normalises pattern_key and clusters by key and lens scope; property: shuffling observations before review yields the same clusters; failed inputs listed and not retried
    - Blocked-by: w1na5df (Session selection, dedupe and splitting), w1na5dl (Steps, calls, budget, lock and resume), w1na5e3 (Roles, schemas and the instruction set), w1na5e6 (Observation verification, redaction and attribution gate)
    - Stream: 1
    - Requirements: [4.3](requirements.md#4.3), [6.1](requirements.md#6.1), [6.5](requirements.md#6.5)
  - [ ] 16.2. Implement the Read steps and clustering <!-- id:w1na5eb -->
    - Read steps created from the selection; observations written in the step's result transaction; per-session pattern counts kept after transcripts are pruned
    - Blocked-by: w1na5ea (Write tests for the reader step and clustering with a fake model)
    - Stream: 1
    - Requirements: [4.3](requirements.md#4.3), [6.5](requirements.md#6.5), [6.6](requirements.md#6.6)

- [ ] 17. Reader trial command for local models <!-- id:w1na5ec -->
  - Blocked-by: w1na5e9 (Reader phase and deterministic clustering), w1na5dx (Claude Code and Codex harness adapters), w1na5e0 (LM Studio direct adapter for tool-free roles)
  - Stream: 1
  - Requirements: [5.6](requirements.md#5.6)
  - [ ] 17.1. Write tests for `dream trial reader` <!-- id:w1na5ed -->
    - Runs the reader on N recorded sessions with a chosen backend and reports schema-valid rate, quote-match rate and tokens; makes no store writes
    - Blocked-by: w1na5e9 (Reader phase and deterministic clustering), w1na5dx (Claude Code and Codex harness adapters), w1na5e0 (LM Studio direct adapter for tool-free roles)
    - Stream: 1
    - Requirements: [5.6](requirements.md#5.6)
  - [ ] 17.2. Implement `dream trial reader` <!-- id:w1na5ee -->
    - Used to decide whether a local model may be first in the reader fallback list (design Risks and Assumptions)
    - Blocked-by: w1na5ed (Write tests for `dream trial reader`)
    - Stream: 1
    - Requirements: [5.6](requirements.md#5.6)

- [ ] 18. Knowledge rules: promotion, scope, conflicts and ranking <!-- id:w1na5ef -->
  - Blocked-by: w1na5d2 (SQLite store and migrations), w1na5e6 (Observation verification, redaction and attribution gate)
  - Stream: 1
  - Requirements: [2.10](requirements.md#2.10), [4.5](requirements.md#4.5), [11.3](requirements.md#11.3), [11.4](requirements.md#11.4), [11.7](requirements.md#11.7), [13.2](requirements.md#13.2), [13.3](requirements.md#13.3), [13.4](requirements.md#13.4), [13.5](requirements.md#13.5), [13.6](requirements.md#13.6), [13.8](requirements.md#13.8), [13.9](requirements.md#13.9), [15.1](requirements.md#15.1), [15.3](requirements.md#15.3)
  - [ ] 18.1. Write tests and property tests for the knowledge rules <!-- id:w1na5eg -->
    - Promotion at min_sessions distinct sessions, one count per interaction; "approach worked" needs a confirmed success; explicit user statements apply at once within scope; contested and superseded transitions; dismissed items never reactivate under a new identifier; revision cap per scope; item version checks reject stale writes; ranking with half-life decay and id tie-break; property: promotion and retrieval are independent of input order; learning recommendation dispositions
    - Blocked-by: w1na5d2 (SQLite store and migrations), w1na5e6 (Observation verification, redaction and attribution gate)
    - Stream: 1
    - Requirements: [4.5](requirements.md#4.5), [11.3](requirements.md#11.3), [13.2](requirements.md#13.2), [13.3](requirements.md#13.3), [13.4](requirements.md#13.4), [13.5](requirements.md#13.5), [13.9](requirements.md#13.9), [15.3](requirements.md#15.3)
  - [ ] 18.2. Implement knowledge.py and review.py rules <!-- id:w1na5eh -->
    - Concepts adapted from OpenClaw and the Prior Art sources with no copied source (12.2); actor and base version on revisions; pending-reassessment queue and conclusion recording; merge_items and revalidate_after_days
    - Blocked-by: w1na5eg (Write tests and property tests for the knowledge rules)
    - Stream: 1
    - Requirements: [2.10](requirements.md#2.10), [11.4](requirements.md#11.4), [11.7](requirements.md#11.7), [13.6](requirements.md#13.6), [13.8](requirements.md#13.8), [15.1](requirements.md#15.1)

- [ ] 19. Reviewer phase <!-- id:w1na5ei -->
  - Blocked-by: w1na5e9 (Reader phase and deterministic clustering), w1na5ef (Knowledge rules: promotion, scope, conflicts and ranking), w1na5du (Backend dispatcher: retry, fallback and circuit breaker)
  - Stream: 1
  - Requirements: [4.3](requirements.md#4.3), [4.5](requirements.md#4.5), [6.5](requirements.md#6.5), [9.13](requirements.md#9.13), [9.14](requirements.md#9.14), [11.3](requirements.md#11.3), [11.4](requirements.md#11.4), [11.6](requirements.md#11.6), [13.8](requirements.md#13.8)
  - [ ] 19.1. Write tests for the Review step with a fake reviewer <!-- id:w1na5ej -->
    - Bounded summaries ordered by rank with new-cluster share reserved and a leftover count; operations validated and applied or recorded rejected with reasons; research and author steps created in the same transaction; no candidate for a pattern with an unmerged branch; a reverted change re-proposed at most once on newer observations
    - Blocked-by: w1na5e9 (Reader phase and deterministic clustering), w1na5ef (Knowledge rules: promotion, scope, conflicts and ranking), w1na5du (Backend dispatcher: retry, fallback and circuit breaker)
    - Stream: 1
    - Requirements: [4.3](requirements.md#4.3), [4.5](requirements.md#4.5), [9.13](requirements.md#9.13), [9.14](requirements.md#9.14), [11.3](requirements.md#11.3), [11.4](requirements.md#11.4)
  - [ ] 19.2. Implement the Review step <!-- id:w1na5ek -->
    - last_reviewed_run and boost_after_dreams; candidate positions and signals stored for the report; reviewer receives earlier run records as evidence about dreaming
    - Blocked-by: w1na5ej (Write tests for the Review step with a fake reviewer)
    - Stream: 1
    - Requirements: [6.5](requirements.md#6.5), [11.3](requirements.md#11.3), [11.6](requirements.md#11.6), [13.8](requirements.md#13.8)

- [ ] 20. Researcher and author phases <!-- id:w1na5el -->
  - Blocked-by: w1na5ei (Reviewer phase), w1na5dx (Claude Code and Codex harness adapters)
  - Stream: 1
  - Requirements: [4.2](requirements.md#4.2), [4.4](requirements.md#4.4), [4.6](requirements.md#4.6), [9.2](requirements.md#9.2), [9.3](requirements.md#9.3), [9.10](requirements.md#9.10), [11.5](requirements.md#11.5), [15.1](requirements.md#15.1), [15.2](requirements.md#15.2)
  - [ ] 20.1. Write tests for Research and Author steps <!-- id:w1na5em -->
    - Findings with sources kept apart from observations; each Author step first re-verifies cited evidence against current files and defers with a reason; author emits id-keyed edits citing a supporting and a counter case, never whole-file rewrites; learning recommendation versus change output; depends_on defines linked groups; `external_input` flag set when fetched web or PR text was received; interactive skills deferred and reported
    - Blocked-by: w1na5ei (Reviewer phase), w1na5dx (Claude Code and Codex harness adapters)
    - Stream: 1
    - Requirements: [4.6](requirements.md#4.6), [9.3](requirements.md#9.3), [9.10](requirements.md#9.10), [11.5](requirements.md#11.5), [15.1](requirements.md#15.1), [15.2](requirements.md#15.2)
  - [ ] 20.2. Implement Research and Author steps <!-- id:w1na5en -->
    - Target repository CLAUDE.md/AGENTS.md passed as counted input; evidence ids cited in every change (file findings cite repository, revision, path, location)
    - Blocked-by: w1na5em (Write tests for Research and Author steps)
    - Stream: 1
    - Requirements: [4.2](requirements.md#4.2), [4.4](requirements.md#4.4), [9.2](requirements.md#9.2), [11.5](requirements.md#11.5)

## API

- [ ] 21. Knowledge operations: recall, search, get, feedback, export, import <!-- id:w1na5eo -->
  - Blocked-by: w1na5ef (Knowledge rules: promotion, scope, conflicts and ranking)
  - Stream: 1
  - Requirements: [11.7](requirements.md#11.7), [13.5](requirements.md#13.5), [14.1](requirements.md#14.1), [14.2](requirements.md#14.2), [14.3](requirements.md#14.3), [14.5](requirements.md#14.5), [14.6](requirements.md#14.6), [14.7](requirements.md#14.7), [15.3](requirements.md#15.3)
  - [ ] 21.1. Write tests and property tests for the knowledge operations <!-- id:w1na5ep -->
    - Property: estimated_tokens never exceeds the limit, ordering independent of input order (specificity, confidence, recency, id), out-of-scope, unresolved and non-active items absent by default; evidence references carry redacted quote and modality; feedback idempotent by feedback id with cited/present_only revisions; export then import into a fresh store then export equals the first, importing twice equals once, imported items marked and excluded from promotion counts; incompatible_version and not_found codes
    - Blocked-by: w1na5ef (Knowledge rules: promotion, scope, conflicts and ranking)
    - Stream: 1
    - Requirements: [14.2](requirements.md#14.2), [14.3](requirements.md#14.3), [14.5](requirements.md#14.5), [14.6](requirements.md#14.6), [14.7](requirements.md#14.7)
  - [ ] 21.2. Implement api.py knowledge operations <!-- id:w1na5eq -->
    - One JSON request on stdin, one response on stdout, envelope {"dreaming_api": 1, "op": ...}; estimator utf8_bytes/4 stated in responses; pending_reassessment mark shown; no agentic-coding path required
    - Blocked-by: w1na5ep (Write tests and property tests for the knowledge operations)
    - Stream: 1
    - Requirements: [14.1](requirements.md#14.1), [14.2](requirements.md#14.2), [14.3](requirements.md#14.3), [14.5](requirements.md#14.5), [14.6](requirements.md#14.6), [14.7](requirements.md#14.7)

- [ ] 22. Run and session operations <!-- id:w1na5er -->
  - Blocked-by: w1na5di (Attribution, registration and forgetting), w1na5dl (Steps, calls, budget, lock and resume), w1na5dr (Versioned installs and launcher)
  - Stream: 1
  - Requirements: [1.1](requirements.md#1.1), [1.6](requirements.md#1.6), [2.10](requirements.md#2.10), [2.11](requirements.md#2.11), [5.4](requirements.md#5.4), [14.1](requirements.md#14.1), [14.8](requirements.md#14.8)
  - [ ] 22.1. Write tests for start, status, resume, discard, register, forget and restore <!-- id:w1na5es -->
    - start returns a run id and keeps running after the client disconnects; requester recorded (default `user`); resume rejects overrides other than backends and re-checks re-eligible backends; discard removes unmerged branches, worktrees and the run's rows, keeps a discarded run row and refuses with the 9.15 commands after any merge; register and forget idempotent; unknown ids return not_found
    - Blocked-by: w1na5di (Attribution, registration and forgetting), w1na5dl (Steps, calls, budget, lock and resume), w1na5dr (Versioned installs and launcher)
    - Stream: 1
    - Requirements: [1.1](requirements.md#1.1), [1.6](requirements.md#1.6), [5.4](requirements.md#5.4), [14.1](requirements.md#14.1), [14.8](requirements.md#14.8)
  - [ ] 22.2. Implement run and session operations in api.py and cli.py <!-- id:w1na5et -->
    - Detached child inherits the flock from the start parent; stable codes incompatible_version, not_found, already_running, invalid_scope
    - Blocked-by: w1na5es (Write tests for start, status, resume, discard, register, forget and restore)
    - Stream: 1
    - Requirements: [1.1](requirements.md#1.1), [1.6](requirements.md#1.6), [14.1](requirements.md#14.1)

## Adoption

- [ ] 23. Dream branch, commits and public-repository scan <!-- id:w1na5eu -->
  - Blocked-by: w1na5el (Researcher and author phases)
  - Stream: 1
  - Requirements: [9.1](requirements.md#9.1), [9.2](requirements.md#9.2), [9.3](requirements.md#9.3), [9.4](requirements.md#9.4), [9.5](requirements.md#9.5), [9.12](requirements.md#9.12)
  - [ ] 23.1. Write tests for worktree branches, commits and the public scan using temporary git repositories <!-- id:w1na5ev -->
    - One branch per repository named by dream from the current default branch; the user checkout untouched; one commit per change citing evidence ids; generate commands run before the commit; files written only to configured target repositories; public scan blocks transcript text over the length limit not already in the repo, credentials and listed names, saves a patch outside every repository and lists the change as withheld; commit messages scanned too
    - Blocked-by: w1na5el (Researcher and author phases)
    - Stream: 1
    - Requirements: [9.1](requirements.md#9.1), [9.2](requirements.md#9.2), [9.4](requirements.md#9.4), [9.5](requirements.md#9.5), [9.12](requirements.md#9.12)
  - [ ] 23.2. Implement adopt.py branch and commit steps and scan.py <!-- id:w1na5ew -->
    - Work copies under ~/.dreaming/work/<run>/<repo>, removed at run end with branches kept; evidence cited by identifier only in public repositories
    - Blocked-by: w1na5ev (Write tests for worktree branches, commits and the public scan using temporary git repositories)
    - Stream: 1
    - Requirements: [9.1](requirements.md#9.1), [9.2](requirements.md#9.2), [9.5](requirements.md#9.5), [9.12](requirements.md#9.12)

- [ ] 24. Checks, fast-forward merge, deploy and rollback <!-- id:w1na5ex -->
  - Blocked-by: w1na5eu (Dream branch, commits and public-repository scan)
  - Stream: 1
  - Requirements: [9.6](requirements.md#9.6), [9.7](requirements.md#9.7), [9.8](requirements.md#9.8), [9.9](requirements.md#9.9), [9.10](requirements.md#9.10), [9.11](requirements.md#9.11), [9.13](requirements.md#9.13), [9.14](requirements.md#9.14), [9.15](requirements.md#9.15), [10.2](requirements.md#10.2)
  - [ ] 24.1. Write tests for checks, merge, deploy, rollback and resumption <!-- id:w1na5ey -->
    - Checks run on the merge result in a separate worktree with that result's Makefiles and tests; no configured lint/test blocks; dirty checkout, non-default branch or moved HEAD blocks with the condition named; `merge --ff-only <tested-sha>`; merging and deploying rows precede the steps and state is recovered from git (merge-base --is-ancestor); deploy failure reverts with `git revert -m 1` and a Dreaming-Revert trailer, redeploys, reports both outcomes; linked groups preflighted and rolled back together; later dream skips a repository merged but not deployed; revert detection stores rejected, trailered reverts store failed; resume after a first merge makes no further merges and prints finish and undo commands; one held change keeps the whole branch unmerged
    - Blocked-by: w1na5eu (Dream branch, commits and public-repository scan)
    - Stream: 1
    - Requirements: [9.6](requirements.md#9.6), [9.7](requirements.md#9.7), [9.8](requirements.md#9.8), [9.9](requirements.md#9.9), [9.10](requirements.md#9.10), [9.11](requirements.md#9.11), [9.13](requirements.md#9.13), [9.14](requirements.md#9.14), [9.15](requirements.md#9.15)
  - [ ] 24.2. Implement the Adopt step in adopt.py <!-- id:w1na5ez -->
    - Limits are checked only between adoption steps; adoption continues after budget exhaustion because it makes no model calls; report commands for unapplied and applied changes include generate then deploy
    - Blocked-by: w1na5ey (Write tests for checks, merge, deploy, rollback and resumption)
    - Stream: 1
    - Requirements: [9.7](requirements.md#9.7), [9.9](requirements.md#9.9), [9.10](requirements.md#9.10), [9.15](requirements.md#9.15), [10.2](requirements.md#10.2)

- [ ] 25. Replay gate and fetched-content rule <!-- id:w1na5f0 -->
  - Blocked-by: w1na5ex (Checks, fast-forward merge, deploy and rollback), w1na5dx (Claude Code and Codex harness adapters)
  - Stream: 1
  - Requirements: [4.2](requirements.md#4.2), [4.4](requirements.md#4.4), [9.16](requirements.md#9.16), [9.17](requirements.md#9.17), [9.18](requirements.md#9.18), [9.19](requirements.md#9.19)
  - [ ] 25.1. Write tests for the replay gate <!-- id:w1na5f1 -->
    - A change that does nothing does not pass (with-change run still recurs); a session counts only if the problem recurs without the change; unclear counts as recurrence; sessions without a complete opening prompt and forgotten sessions never replayed; lens and role-prompt changes re-run the role on stored inputs; held by recurrence share, too few replayable sessions or budget; once per authoring; file-finding-only changes skip replay; `external_input` changes never enter merge; replay tokens counted in the budget
    - Blocked-by: w1na5ex (Checks, fast-forward merge, deploy and rollback), w1na5dx (Claude Code and Codex harness adapters)
    - Stream: 1
    - Requirements: [9.16](requirements.md#9.16), [9.17](requirements.md#9.17), [9.18](requirements.md#9.18), [9.19](requirements.md#9.19)
  - [ ] 25.2. Implement the replay step before checks <!-- id:w1na5f2 -->
    - Replayer runs tool-free with only the changed instruction; a reviewer-role call judges; results stored in replays and shown as association
    - Blocked-by: w1na5f1 (Write tests for the replay gate)
    - Stream: 1
    - Requirements: [4.2](requirements.md#4.2), [4.4](requirements.md#4.4), [9.16](requirements.md#9.16), [9.17](requirements.md#9.17), [9.18](requirements.md#9.18), [9.19](requirements.md#9.19)

- [ ] 26. Currency-review dream <!-- id:w1na5f3 -->
  - Blocked-by: w1na5el (Researcher and author phases), w1na5eu (Dream branch, commits and public-repository scan)
  - Stream: 1
  - Requirements: [4.6](requirements.md#4.6), [15.2](requirements.md#15.2), [16.1](requirements.md#16.1), [16.2](requirements.md#16.2), [16.3](requirements.md#16.3), [16.4](requirements.md#16.4), [16.5](requirements.md#16.5), [16.6](requirements.md#16.6)
  - [ ] 26.1. Write tests for the currency run kind <!-- id:w1na5f4 -->
    - No Read phase and no sessions; source limit and budget enforced; one source never yields a candidate and same-domain sources count once; a relied-on passage absent from the stored text rejects the finding; fetched text only in delimited data fields; changes committed to the branch and never merged; non-file findings kept as currency notes returned only on request; equivalent finding reuses its identifier, dismissed or unmerged-deleted finding not proposed again without a new independent source; findings never counted as observations
    - Blocked-by: w1na5el (Researcher and author phases), w1na5eu (Dream branch, commits and public-repository scan)
    - Stream: 1
    - Requirements: [16.1](requirements.md#16.1), [16.2](requirements.md#16.2), [16.3](requirements.md#16.3), [16.4](requirements.md#16.4), [16.5](requirements.md#16.5), [16.6](requirements.md#16.6)
  - [ ] 26.2. Implement the currency run kind <!-- id:w1na5f5 -->
    - Research step per configured target with read, search and fetch tools; verbatim passage verification in the program; fetched pages stored with title, link, retrieval date
    - Blocked-by: w1na5f4 (Write tests for the currency run kind)
    - Stream: 1
    - Requirements: [4.6](requirements.md#4.6), [16.1](requirements.md#16.1), [16.2](requirements.md#16.2), [16.3](requirements.md#16.3), [16.4](requirements.md#16.4), [16.5](requirements.md#16.5), [16.6](requirements.md#16.6)

## Outputs

- [ ] 27. Effect measurement, re-candidacy and calibration statistics <!-- id:w1na5f6 -->
  - Blocked-by: w1na5ei (Reviewer phase), w1na5ex (Checks, fast-forward merge, deploy and rollback)
  - Stream: 1
  - Requirements: [6.7](requirements.md#6.7), [11.1](requirements.md#11.1), [11.2](requirements.md#11.2), [11.6](requirements.md#11.6)
  - [ ] 27.1. Write tests for before/after rates and calibration <!-- id:w1na5f7 -->
    - Raw counts of observations and in-scope sessions before and after applied_at labelled association; insufficient evidence for a zero-session baseline, too few sessions or file-only findings; re-candidacy at or above the pre-change rate up to max_changes_per_pattern; calibration queries: distinct-session distribution per pattern and replay outcome versus later recurrence
    - Blocked-by: w1na5ei (Reviewer phase), w1na5ex (Checks, fast-forward merge, deploy and rollback)
    - Stream: 1
    - Requirements: [11.1](requirements.md#11.1), [11.2](requirements.md#11.2)
  - [ ] 27.2. Implement effect measurement and calibration queries <!-- id:w1na5f8 -->
    - Feeds the report and the reviewer context; records outcomes of evidence gathering, reflection, selection and adoption with reasons for deferrals
    - Blocked-by: w1na5f7 (Write tests for before/after rates and calibration)
    - Stream: 1
    - Requirements: [6.7](requirements.md#6.7), [11.1](requirements.md#11.1), [11.2](requirements.md#11.2), [11.6](requirements.md#11.6)

- [ ] 28. Tooling inventory and context weight <!-- id:w1na5f9 -->
  - Blocked-by: w1na5dc (apsis client and contract checks)
  - Stream: 2
  - Requirements: [8.1](requirements.md#8.1), [8.2](requirements.md#8.2)
  - [ ] 28.1. Write tests for the tooling inventory <!-- id:w1na5fa -->
    - MCP servers and tools configured per harness versus used in sessions read, never-used tools, sessions showing a need an available tool could meet; context before the first prompt by instructions, skills and tool schemas labelled measured, estimated or unavailable; flag above the configured share of a known window
    - Blocked-by: w1na5dc (apsis client and contract checks)
    - Stream: 2
    - Requirements: [8.1](requirements.md#8.1), [8.2](requirements.md#8.2)
  - [ ] 28.2. Implement inventory.py <!-- id:w1na5fb -->
    - Reads harness configuration files and shared session documents; largest contributors named
    - Blocked-by: w1na5fa (Write tests for the tooling inventory)
    - Stream: 2
    - Requirements: [8.1](requirements.md#8.1), [8.2](requirements.md#8.2)

- [ ] 29. Dream report <!-- id:w1na5fc -->
  - Blocked-by: w1na5ex (Checks, fast-forward merge, deploy and rollback), w1na5f6 (Effect measurement, re-candidacy and calibration statistics), w1na5f9 (Tooling inventory and context weight)
  - Stream: 2
  - Requirements: [7.4](requirements.md#7.4), [9.11](requirements.md#9.11), [10.1](requirements.md#10.1), [10.2](requirements.md#10.2), [10.3](requirements.md#10.3), [10.4](requirements.md#10.4), [10.5](requirements.md#10.5), [10.6](requirements.md#10.6), [12.3](requirements.md#12.3), [15.2](requirements.md#15.2), [16.2](requirements.md#16.2)
  - [ ] 29.1. Write tests for the HTML report <!-- id:w1na5fd -->
    - Written outside every repository in the exit path of complete, partial, budget-exhausted and failed runs; per-repository changes with evidence, applied state and merge or revert commands each followed by generate and deploy; statistics, tooling inventory, unmerged earlier branches, forgotten sessions, currency notes and changes, config and restriction changes; retained knowledge, learning recommendations and repository changes distinguished; browser opened only for user-initiated runs and a browser failure never fails the dream; fetched titles escaped and only http(s) links rendered
    - Blocked-by: w1na5ex (Checks, fast-forward merge, deploy and rollback), w1na5f6 (Effect measurement, re-candidacy and calibration statistics), w1na5f9 (Tooling inventory and context weight)
    - Stream: 2
    - Requirements: [10.1](requirements.md#10.1), [10.2](requirements.md#10.2), [10.3](requirements.md#10.3), [10.4](requirements.md#10.4), [10.6](requirements.md#10.6), [16.2](requirements.md#16.2)
  - [ ] 29.2. Implement report/ <!-- id:w1na5fe -->
    - CSS and page shell vendored once from the review_html module in agentic-coding scripts/ (layout and styling per 10.5) with source revision and licence recorded in the module header; no import from agentic-coding and no runtime dependency on its checkout
    - Blocked-by: w1na5fd (Write tests for the HTML report)
    - Stream: 2
    - Requirements: [10.5](requirements.md#10.5), [12.3](requirements.md#12.3)

## Integration

- [ ] 30. `dream` agent skill <!-- id:w1na5ff -->
  - Blocked-by: w1na5er (Run and session operations)
  - Stream: 2
  - Requirements: [1.1](requirements.md#1.1), [10.1](requirements.md#10.1), [14.1](requirements.md#14.1)
  - [ ] 30.1. Write tests for the skill <!-- id:w1na5fg -->
    - tests check that skills/dream/SKILL.md exists with valid frontmatter and invokes only the installed `dream` command and `dream api`; `make lint` passes
    - Blocked-by: w1na5er (Run and session operations)
    - Stream: 2
    - Requirements: [14.1](requirements.md#14.1)
  - [ ] 30.2. Add skills/dream/SKILL.md <!-- id:w1na5fh -->
    - Start (with dry-run and scope options), inspect, resume and open the report through the installed `dream` command; works from any directory; requester `user`; other harness repositories install the skill by copying this directory
    - Blocked-by: w1na5fg (Write tests for the skill)
    - Stream: 2
    - Requirements: [1.1](requirements.md#1.1), [10.1](requirements.md#10.1), [14.1](requirements.md#14.1)

- [ ] 31. Portable end-to-end test and wiring <!-- id:w1na5fi -->
  - Blocked-by: w1na5eo (Knowledge operations: recall, search, get, feedback, export, import), w1na5er (Run and session operations), w1na5fc (Dream report), w1na5ec (Reader trial command for local models), w1na5f0 (Replay gate and fetched-content rule), w1na5f3 (Currency-review dream)
  - Stream: 1
  - Requirements: [14.1](requirements.md#14.1), [14.3](requirements.md#14.3), [14.4](requirements.md#14.4)
  - [ ] 31.1. Write an end-to-end test in a fresh DREAMING_HOME <!-- id:w1na5fj -->
    - A source, backend and store outside any agentic-coding checkout, no skills installed, no target repository: a dream retains knowledge, writes the report, exports; export imports into a second fresh store preserving identifiers, scopes, availability markers, dismissed and forgotten states; unavailable optional integrations reported without blocking
    - Blocked-by: w1na5eo (Knowledge operations: recall, search, get, feedback, export, import), w1na5er (Run and session operations), w1na5fc (Dream report), w1na5ec (Reader trial command for local models), w1na5f0 (Replay gate and fetched-content rule), w1na5f3 (Currency-review dream)
    - Stream: 1
    - Requirements: [14.3](requirements.md#14.3), [14.4](requirements.md#14.4)
  - [ ] 31.2. Wire remaining gaps found by the end-to-end test <!-- id:w1na5fk -->
    - Fix integration defects only; add tests for each
    - Blocked-by: w1na5fj (Write an end-to-end test in a fresh DREAMING_HOME)
    - Stream: 1
    - Requirements: [14.1](requirements.md#14.1), [14.4](requirements.md#14.4)
