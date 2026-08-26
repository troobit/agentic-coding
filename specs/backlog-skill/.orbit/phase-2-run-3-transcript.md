# Phase 2 Session Transcript

**Session ID:** `58128ca8-7912-4a19-b794-8ba104e9861c`

---

## 👤 User · 2026-08-26T23:54:13+10:00

Run /next-task --phase and when complete run /commit

---

## 🤖 Assistant · 2026-08-26T23:54:15+10:00

<details>
<summary>🔧 Skill: next-task</summary>

Base directory for this skill: /Users/r/.claude/skills/next-task

### 4. Next task

Implement the next unfinished group of tasks from the tasks list. A group of tasks is a set of tasks that start with the same number like 1.1, 1.2, but NOT 2.1.

**Constraints:**

**Task Retrieval:**
- When no explicit tasks file path was given and more than one spec has an incomplete `tasks.md`, list the candidates and ask the user to confirm — NEVER guess
- The model MUST use the rune skill to retrieve the next task(s) to work on
- Use `rune next --format json` to get the next incomplete task. This command will indicate when all tasks are complete
- If the user asks for the entire phase, use `rune next --phase --format json`
- If the retrieved result contains only a single top-level task (without subtasks like "1" instead of "1.1"), rerun with `rune next --phase --format json` to retrieve the full phase of tasks

**Stream Detection for Parallel Execution:**
- When retrieving a phase, the model MUST check for multiple work streams using `rune streams --available --json`
- If multiple streams have ready tasks, parallel execution is possible
- If only one stream has ready tasks, sequential execution within that stream is used

**Task Execution:**
- The model MUST read all files referenced in the front_matter_references
- The selected tasks MUST be added to the internal TODO list for tracking and implemented in the order specified
- The model MUST implement all of the selected tasks, including all subtasks
- Once a subtask or task is completed, use the rune skill to mark it complete (e.g., `rune complete specs/{feature}/tasks.md 1.1`)
- The model MUST NOT proceed past the selected task. Once a task is done, it needs to be put up for review by the user
- Use tools and skills as appropriate while implementing the task. For example, if you need to know the capabilities of a library, use context7, and if you want to verify your code is efficient, use the efficiency-optimizer skill

**Mid-Implementation Spec Edits:**
Any edit to documents under `specs/` made during implementation (revising a design, appending tasks, recording decisions) follows the spec-conventions reference distributed with the spec-janitor skill: a direction change marks the discarded sections superseded in the same edit rather than deleting or silently contradicting them (`SJ-SUP-*`), and tasks appended to an existing task file carry the same schema as its existing tasks — same metadata shape and stable-ID style (`SJ-TASK-*`). Recording or revising a decision-log entry defers to the repo's declared `decision_mode` (read from `.agentic.json`; default `supersede`) rather than always superseding.

**Parallel Execution with Multiple Streams:**
When a phase is pulled in and multiple streams have ready tasks:
1. The model MUST use `rune streams --available --json` to identify streams with ready work
2. If there are 2 or more streams with ready tasks:
   - The model SHOULD spawn subagents (using the Task tool) to handle each stream in parallel
   - Each subagent receives instructions to:
     - Retrieve all phase tasks for their stream using `rune next --phase --stream N --format json`
     - Read all referenced files from front_matter_references
     - Implement the tasks in dependency order
     - Mark tasks complete as they finish using `rune complete <tasks-file-path> <task-id>`
     - Report back when all tasks in the stream are done or blocked
   - The main agent coordinates by:
     - Monitoring subagent progress
     - Handling any cross-stream dependencies that become unblocked
     - Aggregating results for user review
3. If there is only 1 stream with ready tasks:
   - Execute tasks sequentially within that stream as normal
   - No subagents are needed

**Subagent Instructions Template:**
When spawning a subagent for a stream, provide these instructions:
- Stream number to work on
- Path to the tasks file
- List of front_matter_references to read
- Instruction to use `rune next --phase --stream N --format json` to retrieve all tasks for the stream
- Instruction to mark tasks complete using `rune complete <tasks-file-path> <task-id>`
- Instruction to stop when all tasks in the stream are complete or blocked by tasks in other streams

**Cross-Stream Coordination:**
- When a subagent completes a task that unblocks tasks in another stream, that stream's agent will pick up the newly unblocked work on their next `rune next --phase --stream N` call
- If all streams become blocked waiting on each other, this indicates a circular dependency problem that should be reported to the user
- The main agent should periodically check `rune streams --json` to monitor overall progress

**Headless Runs (no human present):**
When running non-interactively — e.g. driven by an external runner rather than a live user:
- The model MUST NEVER call AskUserQuestion; there is no one to answer and the questions are dismissed unanswered
- If the next task is blocked, requires user approval, or there is nothing left to do: write `.orbit/halt` in the repo root containing a one-line reason, print `ORBIT-HALT: <reason>` as the final line of output, then stop
- Keep the sentinel file name (`.orbit/halt`) and output prefix (`ORBIT-HALT:`) exactly as written — external tooling matches on them

**Specs Overview Update:**
- After completing all tasks in the current group, check if `specs/OVERVIEW.md` exists in the project
- If it exists, run `/specs-overview` once to regenerate it — it derives spec statuses and file lists from the tree. Never hand-edit `OVERVIEW.md`


ARGUMENTS: --phase

</details>

---

<details>
<summary>✅ 🔧 Bash</summary>

**Command:**
```bash
find specs -maxdepth 2 -iname "tasks*.md" | xargs -I{} sh -c 'echo "=== {} ==="; rune list {} 2>&1 | tail -5'
```

**Result:**
```
=== specs/toolset-agnostic-starwave/tasks.md ===
+-------------------------------------------------+
| specs/toolset-agnostic-starwave/requirements.md |
| specs/toolset-agnostic-starwave/design.md       |
| specs/toolset-agnostic-starwave/decision_log.md |
+-------------------------------------------------+
=== specs/spec-janitor/tasks.md ===
+------------------------------------+
| specs/spec-janitor/requirements.md |
| specs/spec-janitor/design.md       |
| specs/spec-janitor/decision_log.md |
+------------------------------------+
=== specs/agreement-invoice-skills/tasks-process-guardrails.md ===
+---------------------------------------+
| REFERENCE                             |
+---------------------------------------+
| specs/agreement-invoice-skills/prd.md |
+---------------------------------------+
=== specs/agreement-invoice-skills/tasks-customer-doc-skills.md ===
+---------------------------------------+
| REFERENCE                             |
+---------------------------------------+
| specs/agreement-invoice-skills/prd.md |
+---------------------------------------+
=== specs/fiscal-probe-skill/tasks.md ===
+---------------------------------+
| REFERENCE                       |
+---------------------------------+
| specs/fiscal-probe-skill/prd.md |
+---------------------------------+
=== specs/nextup-starwave-refinement/tasks-process-status.md ===
+-----------------------------------------+
| REFERENCE                               |
+-----------------------------------------+
| specs/nextup-starwave-refinement/prd.md |
+-----------------------------------------+
=== specs/nextup-starwave-refinement/tasks-align-tooling.md ===
+-----------------------------------------+
| REFERENCE                               |
+-----------------------------------------+
| specs/nextup-starwave-refinement/prd.md |
+-----------------------------------------+
=== specs/nextup-starwave-refinement/tasks-rollout.md ===
+-----------------------------------------+
| REFERENCE                               |
+-----------------------------------------+
| specs/nextup-starwave-refinement/prd.md |
+-----------------------------------------+
=== specs/nextup-starwave-refinement/tasks-documentation.md ===
+-----------------------------------------+
| REFERENCE                               |
+-----------------------------------------+
| specs/nextup-starwave-refinement/prd.md |
+-----------------------------------------+
=== specs/transit-workflow-integration/tasks.md ===
+------------------------------------------------+
| REFERENCE                                      |
+------------------------------------------------+
| specs/transit-workflow-integration/smolspec.md |
+------------------------------------------------+
=== specs/nextup-pure-router/tasks.md ===
| REFERENCE                                |
+------------------------------------------+
| specs/nextup-pure-router/smolspec.md     |
| specs/nextup-pure-router/decision_log.md |
+------------------------------------------+
=== specs/backlog-skill/tasks.md ===
+-------------------------------------+
| specs/backlog-skill/requirements.md |
| specs/backlog-skill/design.md       |
| specs/backlog-skill/decision_log.md |
+-------------------------------------+
```

</details>

<details>
<summary>✅ 🔧 Bash</summary>

**Command:**
```bash
rune next --phase --format json specs/backlog-skill/tasks.md 2>&1
```

**Result:**
```
{
  "success": true,
  "count": 3,
  "phase_name": "Toolchain",
  "tasks": [
    {
      "id": "4",
      "title": "BACKLOG.md column and schema check in process_status.py",
      "status": "Pending",
      "stream": 2,
      "blocked": false,
      "children": [
        {
          "id": "4.1",
          "title": "Write BACKLOG fixture tests in test_process_status.py; remove nextup-column assertions (red)",
          "status": "Pending",
          "stream": 2,
          "blocked": false,
          "details": [
            "ok fixtures: absent (renders -), valid, empty-but-valid (both phases zero entries), gapped numbering, U+2192 arrow detail, trailing-whitespace heading",
            "drift fixtures: rune-unparseable, wrong/extra/case-variant phase, checked entry, nested checked subtask (only Stats catches it), missing H1"
          ]
        },
        {
          "id": "4.2",
          "title": "Implement _backlog_status hybrid check, column swap, backlog-drift flag, docstring and argparse rewrite (green)",
          "status": "Pending",
          "stream": 2,
          "blocked": true,
          "blockedBy": [
            "4.1"
          ],
          "details": [
            "Hybrid: _rune_parses gate, raw right-trimmed case-sensitive scan of H2 set/order == [Idea, Needs Spec], rune list --format json Stats.Pending == Stats.Total, raw H1 presence scan",
            "Remove NEXTUP/EXAMPLE keys :118-119 assigns :131-132 header :188 _row :205-206 (presence-only, no drift wiring exists); add backlog-drift to drift_flags with reason detail line; rewrite module docstring :4-16 and argparse description :252",
            "Detail-line grammar deliberately unchecked (design: out of AC 3.5 scope)"
          ]
        }
      ]
    },
    {
      "id": "5",
      "title": "Owned-symlink prune in sync-claude.sh",
      "status": "Pending",
      "stream": 2,
      "blocked": false,
      "children": [
        {
          "id": "5.1",
          "title": "Write prune cases in test_sync_compat.py (red)",
          "status": "Pending",
          "stream": 2,
          "blocked": false
        },
        {
          "id": "5.2",
          "title": "Implement the prune loop in sync-claude.sh (green)",
          "status": "Pending",
          "stream": 2,
          "blocked": true,
          "blockedBy": [
            "5.1"
          ],
          "details": [
            "For each entry in ~/.agents/skills (nullglob): [ -L ] and literal target prefix $REPO_CLAUDE_DIR/skills/ and [ ! -e ] then rm; foreign links never touched; script only creates absolute links so literal prefix match suffices"
          ]
        }
      ]
    },
    {
      "id": "6",
      "title": "Remove align step 6 and the canonical template",
      "status": "Pending",
      "stream": 2,
      "blocked": false,
      "children": [
        {
          "id": "6.1",
          "title": "Rewrite test_align.py: drop step-6 classes and all 8 nextup fixtures; add stray-template-untouched and no-gitignore-write tests (red)",
          "status": "Pending",
          "stream": 2,
          "blocked": false,
          "details": [
            "Delete fixtures: nextup-{canonical,gitignore-append,gitignore-create,markerless,missing,plan-only,session-file,user-zone} plus their .gitignore files and seed-root/nextup.example.md",
            "New tests: align leaves a stray nextup.example.md in a target untouched (stop-managing means no touch, not delete); align never writes .gitignore"
          ]
        },
        {
          "id": "6.2",
          "title": "Delete align step-6 code and nextup.example.md in the same commit (green)",
          "status": "Pending",
          "stream": 2,
          "blocked": true,
          "blockedBy": [
            "6.1"
          ],
          "details": [
            "Delete: NEXTUP_EXAMPLE :90, NEXTUP_LM_MARKER :94, _ensure_nextup_gitignore :346, _converge_nextup_template :371, call :420, seed-root existence error :548, docstring managed-files entry :48; renumber remaining steps",
            "_shadow_copy :443: NEXTUP_EXAMPLE and .gitignore both leave the tuple (gitignore management existed only for nextup)",
            "Canonical nextup.example.md deleted in this same commit or align crashes on a seed root missing an expected file"
          ]
        }
      ]
    }
  ],
  "streams_summary": [
    {
      "id": 1,
      "ready": [
        "7",
        "7.1"
      ],
      "blocked": [
        "7.2"
      ],
      "active": [],
      "available": true
    },
    {
      "id": 2,
      "ready": [
        "4",
        "4.1",
        "5",
        "5.1",
        "6",
        "6.1"
      ],
      "blocked": [
        "4.2",
        "5.2",
        "6.2"
      ],
      "active": [],
      "available": true
    }
  ],
  "front_matter_references": [
    "specs/backlog-skill/requirements.md",
    "specs/backlog-skill/design.md",
    "specs/backlog-skill/decision_log.md"
  ]
}
```

</details>

<details>
<summary>✅ 🔧 Bash</summary>

**Command:**
```bash
rune streams --available --json specs/backlog-skill/tasks.md 2>&1
```

**Result:**
```
{
  "streams": [
    {
      "id": 1,
      "ready": [
        "7",
        "7.1"
      ],
      "blocked": [
        "7.2"
      ],
      "active": []
    },
    {
      "id": 2,
      "ready": [
        "4",
        "4.1",
        "5",
        "5.1",
        "6",
        "6.1"
      ],
      "blocked": [
        "4.2",
        "5.2",
        "6.2"
      ],
      "active": []
    }
  ],
  "available": [
    1,
    2
  ]
}
```

</details>

<details>
<summary>✅ 🔧 Bash</summary>

**Command:**
```bash
rune next --format json specs/backlog-skill/tasks.md 2>&1; echo "---"; rune list specs/backlog-skill/tasks.md 2>&1 | head -80
```

**Result:**
```
{
  "success": true,
  "next_task": {
    "id": "4",
    "title": "BACKLOG.md column and schema check in process_status.py",
    "status": "Pending",
    "children": [
      {
        "id": "4.1",
        "title": "Write BACKLOG fixture tests in test_process_status.py; remove nextup-column assertions (red)",
        "status": "Pending",
        "details": [
          "ok fixtures: absent (renders -), valid, empty-but-valid (both phases zero entries), gapped numbering, U+2192 arrow detail, trailing-whitespace heading",
          "drift fixtures: rune-unparseable, wrong/extra/case-variant phase, checked entry, nested checked subtask (only Stats catches it), missing H1"
        ]
      },
      {
        "id": "4.2",
        "title": "Implement _backlog_status hybrid check, column swap, backlog-drift flag, docstring and argparse rewrite (green)",
        "status": "Pending",
        "details": [
          "Hybrid: _rune_parses gate, raw right-trimmed case-sensitive scan of H2 set/order == [Idea, Needs Spec], rune list --format json Stats.Pending == Stats.Total, raw H1 presence scan",
          "Remove NEXTUP/EXAMPLE keys :118-119 assigns :131-132 header :188 _row :205-206 (presence-only, no drift wiring exists); add backlog-drift to drift_flags with reason detail line; rewrite module docstring :4-16 and argparse description :252",
          "Detail-line grammar deliberately unchecked (design: out of AC 3.5 scope)"
        ]
      }
    ]
  },
  "front_matter_references": [
    "specs/backlog-skill/requirements.md",
    "specs/backlog-skill/design.md",
    "specs/backlog-skill/decision_log.md"
  ]
}---
+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Tasks: backlog-skill Implementation Tasks                                                                                                                                                                           |
+-----+-----------------------+---------------------------------------------------------------------------------------------------------------------------------------+-----------+--------+------------------+-------+
| ID  | PHASE                 | TITLE                                                                                                                                 | STATUS    | STREAM | BLOCKEDBY        | LEVEL |
+-----+-----------------------+---------------------------------------------------------------------------------------------------------------------------------------+-----------+--------+------------------+-------+
| 1   | Skill and Conventions | Author claude/skills/backlog/SKILL.md                                                                                                 | Completed | 1      |                  | 1     |
| 2   | Skill and Conventions | decision_mode in generated conventions                                                                                                | Completed | 1      |                  | 1     |
| 2.1 | Skill and Conventions | Update test_generate goldens to expect decision_mode rules in all three outputs (red)                                                 | Completed | 1      |                  | 2     |
| 2.2 | Skill and Conventions | Add decision_mode rules to shared/conventions.md and the decision-log format reference; run make generate (green)                     | Completed | 1      | 2.1              | 2     |
| 3   | Skill and Conventions | Per-skill decision_mode edits in supersede-mandating skills                                                                           | Completed | 1      | 2                | 1     |
| 4   | Toolchain             | BACKLOG.md column and schema check in process_status.py                                                                               | Pending   | 2      |                  | 1     |
| 4.1 | Toolchain             | Write BACKLOG fixture tests in test_process_status.py; remove nextup-column assertions (red)                                          | Pending   | 2      |                  | 2     |
| 4.2 | Toolchain             | Implement _backlog_status hybrid check, column swap, backlog-drift flag, docstring and argparse rewrite (green)                       | Pending   | 2      | 4.1              | 2     |
| 5   | Toolchain             | Owned-symlink prune in sync-claude.sh                                                                                                 | Pending   | 2      |                  | 1     |
| 5.1 | Toolchain             | Write prune cases in test_sync_compat.py (red)                                                                                        | Pending   | 2      |                  | 2     |
| 5.2 | Toolchain             | Implement the prune loop in sync-claude.sh (green)                                                                                    | Pending   | 2      | 5.1              | 2     |
| 6   | Toolchain             | Remove align step 6 and the canonical template                                                                                        | Pending   | 2      |                  | 1     |
| 6.1 | Toolchain             | Rewrite test_align.py: drop step-6 classes and all 8 nextup fixtures; add stray-template-untouched and no-gitignore-write tests (red) | Pending   | 2      |                  | 2     |
| 6.2 | Toolchain             | Delete align step-6 code and nextup.example.md in the same commit (green)                                                             | Pending   | 2      | 6.1              | 2     |
| 7   | Sunset                | Sunset gate and removals                                                                                                              | Pending   | 1      |                  | 1     |
| 7.1 | Sunset                | Write the tracked-files sunset grep test (red)                                                                                        | Pending   | 1      |                  | 2     |
| 7.2 | Sunset                | Remove nextup and spout skill dirs, swap README registry, purge remaining tracked references (green)                                  | Pending   | 1      | 7.1, 1, 4.2, 6.2 | 2     |
+-----+-----------------------+---------------------------------------------------------------------------------------------------------------------------------------+-----------+--------+------------------+-------+

+-------------------------------------+
| References                          |
+-------------------------------------+
| REFERENCE                           |
+-------------------------------------+
| specs/backlog-skill/requirements.md |
| specs/backlog-skill/design.md       |
| specs/backlog-skill/decision_log.md |
+-------------------------------------+
```

</details>

<details>
<summary>✅ 🔧 Bash</summary>

**Command:**
```bash
rune next --phase --stream 1 --format json specs/backlog-skill/tasks.md 2>&1
```

**Result:**
```
{
  "success": true,
  "count": 3,
  "phase_name": "Sunset",
  "tasks": [
    {
      "id": "7",
      "title": "Sunset gate and removals",
      "status": "Pending",
      "stream": 1,
      "blocked": false,
      "children": [
        {
          "id": "7.1",
          "title": "Write the tracked-files sunset grep test (red)",
          "status": "Pending",
          "stream": 1,
          "blocked": false,
          "details": [
            "File set from git ls-files; case-insensitive nextup|spout; exempt specs/, CHANGELOG.md, and the test file itself; fails against current tree until 7.2"
          ]
        },
        {
          "id": "7.2",
          "title": "Remove nextup and spout skill dirs, swap README registry, purge remaining tracked references (green)",
          "status": "Pending",
          "stream": 1,
          "blocked": true,
          "blockedBy": [
            "7.1",
            "1",
            "4.2",
            "6.2"
          ],
          "details": [
            "Delete claude/skills/nextup and claude/skills/spout; README registry lists backlog in their place",
            "Purge: .gitignore /nextup.md and /SPOUT.md entries plus comments; docs/agent-notes align-tooling, process-status, spec-janitor, transit-integration; docs/runbooks/process-onboarding.md now points at /backlog; scripts/README.md align steps and status columns; claude/uplift-candidates.md purge or delete",
            "Ordering (AC 6.6): blocked by task 1 so the skill exists in the synced toolchain before the sunset lands"
          ]
        }
      ]
    },
    {
      "id": "7.1",
      "title": "Write the tracked-files sunset grep test (red)",
      "status": "Pending",
      "stream": 1,
      "blocked": false,
      "details": [
        "File set from git ls-files; case-insensitive nextup|spout; exempt specs/, CHANGELOG.md, and the test file itself; fails against current tree until 7.2"
      ]
    },
    {
      "id": "7.2",
      "title": "Remove nextup and spout skill dirs, swap README registry, purge remaining tracked references (green)",
      "status": "Pending",
      "stream": 1,
      "blocked": true,
      "blockedBy": [
        "7.1",
        "1",
        "4.2",
        "6.2"
      ],
      "details": [
        "Delete claude/skills/nextup and claude/skills/spout; README registry lists backlog in their place",
        "Purge: .gitignore /nextup.md and /SPOUT.md entries plus comments; docs/agent-notes align-tooling, process-status, spec-janitor, transit-integration; docs/runbooks/process-onboarding.md now points at /backlog; scripts/README.md align steps and status columns; claude/uplift-candidates.md purge or delete",
        "Ordering (AC 6.6): blocked by task 1 so the skill exists in the synced toolchain before the sunset lands"
      ]
    }
  ],
  "streams_summary": [
    {
      "id": 1,
      "ready": [
        "7",
        "7.1"
      ],
      "blocked": [
        "7.2"
      ],
      "active": [],
      "available": true
    },
    {
      "id": 2,
      "ready": [
        "4",
        "4.1",
        "5",
        "5.1",
        "6",
        "6.1"
      ],
      "blocked": [
        "4.2",
        "5.2",
        "6.2"
      ],
      "active": [],
      "available": true
    }
  ],
  "front_matter_references": [
    "specs/backlog-skill/requirements.md",
    "specs/backlog-skill/design.md",
    "specs/backlog-skill/decision_log.md"
  ]
}
```

</details>

## 🤖 Assistant · 2026-08-26T23:54:44+10:00

<details>
<summary>✅ 🔧 Read: <code>specs/backlog-skill/design.md</code></summary>

```
1	# Design: backlog-skill
2	
3	## Overview
4	
5	One new skill (`claude/skills/backlog/SKILL.md`) plus surgical changes to the toolchain, the removal of two skills, and a test/fixture rewrite. The skill is LLM-instruction markdown like every other skill in the tree — no new runtime; the executable changes are in `process_status.py`, `align.py`, `sync-claude.sh`, the generated convention text, and four skill files that hard-code the supersede convention.
6	
7	## Architecture
8	
9	### Touch map
10	
11	| Path | Action | Requirements |
12	|---|---|---|
13	| `claude/skills/backlog/SKILL.md` | new | 1, 2, 3.6, 4 |
14	| `claude/skills/nextup/`, `claude/skills/spout/` | delete | 6.1 |
15	| `README.md` | registry entry swap | 6.1 |
16	| `nextup.example.md` | delete (same commit as align change) | 6.2 |
17	| `scripts/align.py` | delete step 6 (see Components) | 6.2 |
18	| `scripts/process_status.py` | drop nextup columns; add BACKLOG column + schema check; rewrite module docstring and argparse text | 3.5, 6.3 |
19	| `scripts/sync-claude.sh` | add owned-link prune | 6.4 |
20	| `shared/conventions.md` | decision_mode rules in Documentation Standards | 5.3, 5.4 |
21	| `claude/rules/references/decision-log-format.md` | "Revising a decision" section: both modes + manifest read | 5.4 |
22	| `claude/skills/spec-janitor/SKILL.md` + `references/spec-conventions.md` | decision_mode awareness (its supersede mandate at SKILL.md:97 conflicts with overwrite mode); also reword nextup mention | 5.3, 6.5 |
23	| `claude/skills/make-it-so/SKILL.md`, `claude/skills/next-task/SKILL.md` | decision_mode awareness in their "Mid-Implementation Spec Edits" clauses (:91, :33) | 5.3 |
24	| `.gitignore` (this repo) | remove `/nextup.md`, `/SPOUT.md` entries and their comments | 6.5 |
25	| `tests/`, `tests/fixtures/align/` | rewrite (see Testing) | 6.5 |
26	| `docs/agent-notes/`, `docs/runbooks/process-onboarding.md`, `scripts/README.md`, `claude/uplift-candidates.md` | purge/rewrite nextup+spout references | 6.5 |
27	
28	Generated files (`claude/CLAUDE.md`, `copilot/instructions/copilot-instructions.md`, `codex/AGENTS.md`) pick up the conventions change via `make generate`; `make lint-drift` enforces it. Codex additionally reads `~/.codex/AGENTS.md`, written only by `generate.py --user` — a re-run after the conventions change is a rollout step, otherwise Codex sessions keep the old text indefinitely.
29	
30	### Sunset reference audit (AC 6.5)
31	
32	The gate is a test that greps **git-tracked files only** (`git ls-files` sourced), case-insensitive `nextup|spout`, exempting `specs/`, `CHANGELOG.md`, and the test file itself. Tracked-only is both the correct scope (AC 6.5 concerns the committed toolchain) and what makes the gate stable: untracked working files, the `.worktrees/` sibling checkout, and caches are out by construction. The tracked-tree scope is a superset of AC 6.5's enumerated surfaces — stricter is acceptable.
33	
34	Work list (every tracked reference at design time):
35	
36	| Site | Action |
37	|---|---|
38	| `tests/fixtures/align/repos/nextup-*` — **8 repos** (canonical, gitignore-append, gitignore-create, markerless, missing, plan-only, session-file, user-zone) + their `.gitignore` files + `seed-root/nextup.example.md` | delete fixtures |
39	| `tests/test_align.py` (~51 refs) | delete step-6 test classes; keep unrelated convergence tests |
40	| `tests/test_process_status.py` | rewrite nextup-column assertions to BACKLOG assertions |
41	| `tests/test_sync_compat.py` | update if it enumerates skills; add prune coverage |
42	| `scripts/process_status.py` module docstring (:4–16) and argparse description (:252) | rewrite |
43	| `docs/agent-notes/align-tooling.md`, `process-status.md` | rewrite sections describing step 6 / nextup columns |
44	| `docs/agent-notes/spec-janitor.md`, `transit-integration.md` | drop or reword passing references |
45	| `docs/runbooks/process-onboarding.md` | rewrite: onboarding no longer seeds nextup; points at `/backlog` |
46	| `scripts/README.md` | rewrite align step list and status column description |
47	| `claude/skills/spec-janitor/SKILL.md` | reword its nextup mention |
48	| `claude/uplift-candidates.md` | purge or delete (closed historical report) |
49	| `.gitignore` | remove the nextup/spout entries and comments (dead once the tooling is gone; the sunset commit owns this repo's cleanup — rollout owns other repos') |
50	
51	## Components and Interfaces
52	
53	### The /backlog skill
54	
55	`claude/skills/backlog/SKILL.md`, frontmatter description covering triggers ("add this to the backlog", "capture these notes", "file this idea", bare `/backlog`). Workflow, in order:
56	
57	1. **Preflight** — `git rev-parse --show-toplevel`; `rune list specs/BACKLOG.md` if the file exists. Parse failure → report and stop; no writes of any kind this run (AC 3.6). Missing rune binary → warn and refuse all BACKLOG.md writes this run (unparseability cannot be detected without the parser); routing into spec files may proceed, and no source is deleted (items destined for the backlog are unhandled, so no source becomes delete-eligible).
58	2. **Reconcile** (AC 2.6) — for each entry: if its `→ spec:` target exists under `specs/`, or the entry's content is realized in the repo, remove and report. Spec folders are authoritative; `specs/OVERVIEW.md` is a hint only (regenerated on demand, may be stale or absent).
59	3. **Gather** — free-form argument text; named file paths; bare invocation detects a root `nextup.md` (any tracked status, user zone only — machine markers `<!-- LM -->`, `<!-- ML -->`, `<!-- nextup:machine -->` end the zone; `<!-- USER -->` belongs to it; no marker → whole file) plus untracked/gitignored `*.md` at root and under `specs/` outside spec folders. A **spec folder** is any directory under `specs/` containing at least one of requirements.md, design.md, smolspec.md, prd.md, tasks*.md, or decision_log.md. Excluded from detection: `SPOUT.md` (generated), `specs/BACKLOG.md` and `specs/OVERVIEW.md` (the skill's own artifact and the generated index). Candidates are presented before capture.
60	4. **Route** (Req 2) — per item, one destination with a one-line reason. Task-file selection: the spec's only task file; else the `tasks-*.md` whose name/stream matches the item, else `tasks.md`; create `tasks.md` if none. Requirement amendments are confirmed per item before writing, never renumber existing anchors, and append a staleness task ("re-run design/tasks for requirement X") to the selected task file.
61	5. **File** — backlog entries appended to the matching phase, numbered max-existing + 1. File and `specs/` created on first capture.
62	6. **Clear** (Req 4) — per-source outcome listing (filed/dropped/failed per item), always shown when anything was captured. Tracked sources: marked retained, removal is the user's. Delete-eligible sources: one approval for the batch, then delete. Decline → no source touched.
63	
64	Contract notes: the skill never runs rune write commands on BACKLOG.md (AC 3.4) — appends and removals are text edits; it never commits. Duplicate detection (AC 1.5/2.6) uses the repo-realization criterion of Decision 13: an item matches if its substance exists in the backlog, a spec document, or shipped work recorded in the repo (code, CHANGELOG) — consumed intent zones are typically realized via commits, not spec text. The match target is always reported.
65	
66	### BACKLOG.md schema check in process_status.py
67	
68	Replace the two presence-only nextup columns (`NEXTUP`, `EXAMPLE`: info keys :118–119, assigns :131–132, header :188, `_row` :205–206 — there is no nextup drift wiring to remove) with one `BACKLOG` column: `-` (absent, never drift, AC 3.1), `ok`, or `drift`; a `backlog-drift` flag joins `drift_flags()` with the reason in the repo's detail lines, mirroring `rune-drift`.
69	
70	The check is a hybrid — each layer covers a hole in the other:
71	
72	1. **Parse gate**: `_rune_parses` (existing) on `specs/BACKLOG.md`. rune missing → existing warning path, skip.
73	2. **Phase set/order**: raw-text scan of `^##[ ]` headings, right-trimmed, case-sensitive — must equal exactly `["Idea", "Needs Spec"]`. Raw scan rather than rune's JSON because an empty backlog yields `PhaseMarkers: []` (phases with zero entries are invisible to rune), and an empty-but-valid file is the normal post-reconciliation state. `## idea` is drift.
74	3. **Unchecked invariant**: `rune list --format json` → `Stats.Pending == Stats.Total`. This is authoritative where a raw checkbox regex is not: rune counts nested subtasks (`  - [x] …`), which a `^- \[` scan misses. (The parse gate has already run, so fenced-content evasion of the raw scans is not possible — rune rejects such files.)
75	4. **H1 presence**: raw scan for a leading `# ` title (rune parses files without one; AC 3.2 requires it).
76	
77	Deliberately out of the check's scope: detail-line grammar (source/date/arrow). AC 3.5 enumerates parse failures, phase violations, and non-pending entries; detail-line drift is visible in review diffs and correctable by the skill's next run, and enforcing prose grammar by regex is brittleness without payoff.
78	
79	### align.py step-6 removal
80	
81	Delete: `NEXTUP_EXAMPLE` (:90), `NEXTUP_LM_MARKER` (:94), `_ensure_nextup_gitignore` (:346), `_converge_nextup_template` (:371), the call at :420, the seed-root existence error (:548), the "Managed files" docstring list entry (:48), and the step-6 docstring text; renumber the remaining steps. `_shadow_copy` (:443) iterates `MANAGED_JSON + (NEXTUP_EXAMPLE, ".gitignore")` — both `NEXTUP_EXAMPLE` and `".gitignore"` leave the tuple: gitignore management existed only for the nextup entry, so align no longer touches `.gitignore` at all. No replacement behavior: align does not seed or manage BACKLOG.md (AC 3.1).
82	
83	### sync-claude.sh prune
84	
85	After the per-skill link loop: for each entry in `~/.agents/skills/` (nullglob-guarded), if it is a symlink (`[ -L ]`) whose literal target string is prefixed by `$REPO_CLAUDE_DIR/skills/` and the target does not exist (`[ ! -e ]`), remove it. Literal prefix comparison suffices — the script only ever creates absolute links (`ln -s "$skill_dir"`). Links resolving elsewhere are never touched (AC 6.4). `~/.claude/skills` is a single whole-directory link and self-heals. Dangling `nextup`/`spout` links already exist on this machine, so the prune has immediate work.
86	
87	### decision_mode plumbing
88	
89	Two delivery channels, both required — generated conventions alone do not override skill-local instructions:
90	
91	- `shared/conventions.md` § Documentation Standards gains the rule: before revising a decision, read `.agentic.json` → `decision_mode`; `overwrite` → edit the entry in place (same ID, new date, no superseding entry); `supersede`/absent → today's behavior. Reaches all three toolchains via generation; this is also how Codex/Copilot learn the mode rules (the deep format reference under `claude/rules/` stays Claude-side — AC 5.4's "all three toolchains" is satisfied by the conventions block they each receive).
92	- Per-skill edits to every skill whose text mandates supersession: `spec-janitor/SKILL.md:97` and `spec-janitor/references/spec-conventions.md` (its audit must not flag overwrite-mode logs as drift), `make-it-so/SKILL.md:91`, `next-task/SKILL.md:33`. Each gains one sentence deferring to the repo's declared mode.
93	- `claude/rules/references/decision-log-format.md` gains a "Revising a decision" section describing both modes and the manifest read.
94	
95	AC 5.3's workflow list is behavior-scoped per Decision 14: the skills whose instructions direct decision-log creation or revision (starwave skills, smolspec, spec-janitor, make-it-so, next-task).
96	
97	## Data Models
98	
99	BACKLOG.md grammar (rune-strict; both phases always present in this order, even when empty):
100	
101	```markdown
102	# Backlog
103	
104	## Idea
105	
106	- [ ] 1. <one-line item>
107	  - <source>, <YYYY-MM-DD>
108	
109	## Needs Spec
110	
111	- [ ] 2. <one-line item>
112	  - <source>, <YYYY-MM-DD> → spec: <kebab-name>
113	```
114	
115	Normative detail-line grammar: exactly one physical line per entry, `- <source>, <date>` with an optional ` → spec: <kebab-name>` suffix that appears on every Needs Spec entry and no Idea entry. `<source>` is the captured file's repo-relative path or `conversation` (AC 3.7); `<date>` is ISO `YYYY-MM-DD`. Entry titles are single lines and may not contain ` → spec: ` (the suffix is parsed from the line end). Numbering is file-global: a new entry takes max-existing + 1, and reconciliation removals never renumber survivors, so gaps are normal. Verified against the installed rune: gapped numbering parses, and rune assigns its own sequential display IDs — the written number is the stable reference.
116	
117	`.agentic.json`: optional top-level `"decision_mode": "overwrite" | "supersede"`; absent means `supersede`. align preserves unknown keys, so no align change is needed for it.
118	
119	## Error Handling
120	
121	| Failure | Behavior |
122	|---|---|
123	| BACKLOG.md unparseable at preflight | Report, stop; zero writes (AC 3.6) |
124	| rune binary missing | Skill: refuse BACKLOG.md writes and source deletion this run; spec-file routing may proceed. process-status: existing warning path |
125	| Item cannot be routed/filed | Outcome `failed`; its source is never deleted that run (AC 4.3) |
126	| Tracked-status ambiguity | `git ls-files --error-unmatch <path>` decides; tracked → retained (AC 4.4/4.5) |
127	| Source deletion fails mid-batch | Report per file; already-filed entries stay (filing is complete before any deletion starts) |
128	
129	## Testing Strategy
130	
131	- **test_align.py**: delete the step-6 classes and all 8 nextup fixture repos plus the seed-root template; assert align runs clean against a fixture repo *with* a stray `nextup.example.md` present (align must ignore it — stop-managing means no touch, not delete) and that align no longer writes `.gitignore`.
132	- **test_process_status.py**: fixture BACKLOG.md variants asserting column value and drift detail — absent (`-`, no drift), valid, **empty-but-valid** (both phases, zero entries → `ok`), gapped numbering (`ok`), U+2192 arrow detail line (`ok`), trailing-whitespace heading (`ok`), rune-unparseable, wrong/extra/case-variant phase, checked entry, **nested checked subtask** (drift via Stats), missing H1. Nextup-column assertions removed.
133	- **test_sync_compat.py**: dangling owned link (removed), dangling foreign link (kept), live owned link (kept), empty skills dir (no-op).
134	- **test_generate.py**: golden-file update — the decision_mode rules appear in all three generated outputs.
135	- **Sunset grep test** (new): `git ls-files` sourced, case-insensitive `nextup|spout`, exempting `specs/`, `CHANGELOG.md`, and itself; permanent guard against reintroduction.
136	- The skill itself is instruction markdown — exercised by the rollout migration (rollout.md carries acceptance scenarios for Requirements 1, 2, and 4), not unit tests; the schema check is what keeps skill drift detectable.
137	- Tasks file: encode the AC 6.6 ordering (skill commit before sunset commit) as rune `blocked-by` dependencies so the sequence is mechanical.
138	
139	PBT is not warranted: the only parser is rune (external, already trusted), and the schema check's failure space is enumerable and covered by the fixtures above.
140	
141	## Requirements traceability
142	
143	| Requirement | Design element |
144	|---|---|
145	| 1.1–1.5 | Skill steps 3–5; spec-folder definition; SPOUT/BACKLOG/OVERVIEW exclusions |
146	| 2.1–2.6 | Skill steps 2, 4; task-file selection rule; amendment confirmation |
147	| 3.1–3.4, 3.7 | BACKLOG grammar; skill step 5; no-rune-writes contract |
148	| 3.5 | Hybrid `_backlog_status` check in process_status.py |
149	| 3.6 | Skill step 1 preflight |
150	| 4.1–4.5 | Skill step 6 |
151	| 5.1–5.4 | conventions.md + format reference + per-skill edits (spec-janitor, make-it-so, next-task) |
152	| 6.1 | skill dir deletions + README |
153	| 6.2 | align step-6 removal + template deletion, same commit |
154	| 6.3 | process_status column swap + docstring/argparse rewrite |
155	| 6.4 | sync-claude.sh prune |
156	| 6.5 | reference audit table + tracked-files grep gate |
157	| 6.6 | skill commit precedes sunset commit; encoded as task dependencies |
158	
```

</details>

<details>
<summary>✅ 🔧 Read: <code>specs/backlog-skill/requirements.md</code></summary>

```
1	# Requirements: backlog-skill
2	
3	## Introduction
4	
5	A single `/backlog` skill replaces the sunset `nextup` and `spout` skills. It captures ideas, loose notes, and audit findings into a tracked, rune-parseable `specs/BACKLOG.md`, routes each item to where the work belongs (an existing spec's tasks, an existing spec's requirements, or the backlog itself), and clears the consumed sources. The feature also executes the sunset: removing both old skills and their toolchain footprint (align seeding, tests, fixtures, documentation), and introducing a per-repo decision overwrite mode.
6	
7	## Definitions
8	
9	- **Item outcome**: every captured item ends a run in exactly one state — **filed** (written to a backlog entry, spec task, or requirement amendment), **dropped** (recognized as already present in the backlog or realized in a spec), or **failed** (could not be processed). An item is **handled** when it is filed or dropped.
10	- **Source**: a file content was captured from. A source is **delete-eligible** when it is not tracked by git, at least one item was read from it, and every item read from it is handled with none failed.
11	- **User zone**: in a `nextup.md`, the user-intent content: everything except content at or below a recognized machine marker (`<!-- LM -->`, legacy `<!-- ML -->`, `<!-- nextup:machine -->`). A `<!-- USER -->` marker belongs to the zone it opens; WHERE no machine marker exists, the entire file is the zone.
12	
13	## Non-Goals
14	
15	- No Transit integration now — BACKLOG.md statuses are named for a clean later import, but no Transit MCP calls, `T-` ids, or column sync.
16	- No tracking of in-progress or completed work — once promoted to a spec, an item leaves the backlog; specs/OVERVIEW.md and task files own it from there.
17	- No orientation report — spout's "state of every spec" summary is retired without replacement; `specs/OVERVIEW.md` covers it.
18	- No regenerated scratch artifacts — the skill writes no SPOUT.md-style gitignored output; its only artifacts are the tracked backlog and spec amendments.
19	- No automatic commits — the skill edits files; committing remains a user action.
20	- No sweeping or deleting of tracked project documentation — tracked files can be capture sources only when the user names them (except a root `nextup.md`, which is always a candidate), and are never deleted.
21	- No changes to the starwave skills — backlog/spec consistency is owned by `/backlog`'s reconciliation pass, not by hooks in the spec workflow.
22	- No cross-repo rollout in these requirements — enrollment of new participating repos, per-repo migration runs, per-repo `decision_mode` configuration, and residual-file cleanup are post-build administration, tracked in this spec's `rollout.md`.
23	
24	## Requirements
25	
26	### 1. Capture
27	
28	**User Story:** As a developer, I want to hand loose ideas and note files to one skill, so that forward intent stops living in untracked scratch.
29	
30	**Acceptance Criteria:**
31	
32	1. <a name="1.1"></a>WHEN invoked with free-form text, the skill SHALL capture that text as one or more items and route them per Requirement 2 in the same run  
33	2. <a name="1.2"></a>WHEN invoked bare, the skill SHALL detect candidate sources in the repo — a root `nextup.md` regardless of tracked status (user zone only), plus untracked or gitignored markdown files at the repo root and under `specs/` that do not belong to a spec folder — and present them for capture  
34	3. <a name="1.3"></a>The skill SHALL exclude known generated artifacts (`SPOUT.md`) from source detection  
35	4. <a name="1.4"></a>WHEN invoked with a file path, the skill SHALL capture from that file regardless of its tracked status  
36	5. <a name="1.5"></a>IF a captured item already exists in the backlog or is already realized in the repository (a spec, or shipped work recorded in code or the changelog), THEN the skill SHALL drop it and report what it matched  
37	
38	### 2. Routing
39	
40	**User Story:** As a developer, I want each captured item placed where the work actually belongs, so that the backlog holds only work with no home yet.
41	
42	**Acceptance Criteria:**
43	
44	1. <a name="2.1"></a>The skill SHALL propose exactly one destination per item — existing-spec task, existing-spec requirement amendment, or backlog entry — with a one-line reason  
45	2. <a name="2.2"></a>WHEN an item is routed to an existing spec as a task, the skill SHALL append it as a rune-parseable task to the spec's most relevant task file, creating `tasks.md` WHERE the spec has no task file  
46	3. <a name="2.3"></a>WHEN an item is routed to an existing spec as a requirement amendment, the skill SHALL confirm the amendment before writing, SHALL add or modify the requirement in that spec's requirements.md without renumbering existing acceptance-criterion anchors, and SHALL append a task (per the task-file selection rule of [2.2](#2.2)) naming the stale downstream documents (design, tasks) whose workflows need re-running  
47	4. <a name="2.4"></a>WHEN an item warrants a spec that does not exist, the skill SHALL file it as a backlog entry with status `needs-spec` and a proposed spec name  
48	5. <a name="2.5"></a>WHEN an item is an idea with no actionable next step, the skill SHALL file it as a backlog entry with status `idea`  
49	6. <a name="2.6"></a>WHEN a run starts, the skill SHALL reconcile the backlog: entries whose proposed spec now exists or whose content is now realized in the repository (per [1.5](#1.5)) SHALL be removed and reported  
50	
51	### 3. The BACKLOG.md contract
52	
53	**User Story:** As a developer, I want the backlog to be a tracked file with a stable format, so that it survives machines, appears in diffs, and imports into Transit later.
54	
55	**Acceptance Criteria:**
56	
57	1. <a name="3.1"></a>The backlog SHALL live at `specs/BACKLOG.md` in the repo the skill runs in (the git root is the unit), created together with `specs/` on first capture; its absence SHALL NOT be reported as drift  
58	2. <a name="3.2"></a>The backlog SHALL be parseable by `rune list`, with this schema: an H1 title, exactly two H2 phases `## Idea` and `## Needs Spec` as the status carriers, task items as unchecked entries, and capture date, source name, and (for `needs-spec`) proposed spec name as indented detail lines  
59	3. <a name="3.3"></a>Every entry SHALL sit in exactly one phase; phase membership IS the status, mapping to Transit's Idea and Planning columns  
60	4. <a name="3.4"></a>All entries SHALL remain unchecked: work that starts leaves the backlog, so a checked or in-progress entry is a defect, and rune write commands SHALL NOT be used on BACKLOG.md  
61	5. <a name="3.5"></a>The per-repo process-status report SHALL rune-parse `specs/BACKLOG.md` where present and flag as drift: parse failures, phases other than the two of [3.2](#3.2), and any non-pending entry  
62	6. <a name="3.6"></a>WHEN BACKLOG.md fails to parse at the start of a run, the skill SHALL report the violation and make no changes to BACKLOG.md, spec files, or source files until the file is repaired  
63	7. <a name="3.7"></a>A source name recorded in a detail line is historical provenance (free-form input records the invocation, e.g. `conversation`); it SHALL NOT be required to resolve to an existing file  
64	
65	### 4. Clearing consumed sources
66	
67	**User Story:** As a developer, I want consumed source files removed once their content is filed, so that stale intent files cannot lie to future sessions.
68	
69	**Acceptance Criteria:**
70	
71	1. <a name="4.1"></a>WHEN a run captured from any sources, the skill SHALL show the outcome of every item per source; WHEN delete-eligible sources exist, it SHALL ask for approval once per run before deleting them — including sources whose items were all dropped as duplicates  
72	2. <a name="4.2"></a>IF approval is declined, THEN the skill SHALL leave every source file untouched while keeping the filed entries, and a later run SHALL again offer the (now all-duplicate) source for deletion  
73	3. <a name="4.3"></a>A source with any failed item SHALL NOT be deleted in that run  
74	4. <a name="4.4"></a>The skill SHALL NOT delete tracked files, regardless of how they entered the run  
75	5. <a name="4.5"></a>A fully-handled tracked source SHALL appear in the per-source outcome listing of [4.1](#4.1) marked as retained, with removal noted as a user action  
76	
77	### 5. Decision overwrite mode
78	
79	**User Story:** As a developer, I want a repo to be able to declare that decision log entries are overwritten in place instead of superseded, so that changes to design and downstream documents stay salient.
80	
81	**Acceptance Criteria:**
82	
83	1. <a name="5.1"></a>WHERE a repo's `.agentic.json` sets `decision_mode` to `overwrite`, workflows that revise a decision SHALL edit the existing entry in place, keeping its ID and updating its date, with no superseding entry appended  
84	2. <a name="5.2"></a>WHERE `decision_mode` is unset or `supersede`, decision revisions SHALL keep today's behavior: the old entry is marked superseded and a new entry is appended  
85	3. <a name="5.3"></a>Workflows whose instructions direct decision-log creation or revision (the starwave skills, smolspec, spec-janitor, make-it-so, next-task) SHALL determine the mode by reading the repo's `.agentic.json` at run time, defaulting to `supersede`  
86	4. <a name="5.4"></a>The decision-log format reference and the shared convention text for all three toolchains (Claude, Codex, Copilot wrappers) SHALL document both modes and the run-time manifest read  
87	
88	### 6. Sunset of nextup and spout
89	
90	**User Story:** As a developer, I want the retired skills and their entire toolchain footprint gone, so that no tool recommends, seeds, tests, or documents the failed pattern.
91	
92	**Acceptance Criteria:**
93	
94	1. <a name="6.1"></a>The `nextup` and `spout` skill directories SHALL be removed and the README skill registry SHALL list `backlog` in their place  
95	2. <a name="6.2"></a>The align toolchain SHALL stop seeding `nextup.example.md` and stop managing `nextup.md` gitignore entries, with the canonical `nextup.example.md` removed in the same change so align never runs against a seed root missing a file it requires  
96	3. <a name="6.3"></a>The process-status report SHALL drop both nextup columns (presence and example convergence) and their drift logic, replacing them with BACKLOG.md presence and the parse check of [3.5](#3.5)  
97	4. <a name="6.4"></a>The sync script SHALL remove symlinks that point into this repo's skills directory but whose target no longer exists, and SHALL NOT touch links it does not own  
98	5. <a name="6.5"></a>After the sunset lands, `nextup` and `spout` SHALL have no remaining references in the toolchain — skills, scripts, tests, fixtures, agent notes, runbooks, and README — with historical records (`specs/`, `CHANGELOG.md`) exempt; the known footprint at spec time spans the five align test fixture repos and seed root, three test files, four agent notes, the process-onboarding runbook, `scripts/README.md`, and the spec-janitor skill  
99	6. <a name="6.6"></a>The sunset changes SHALL land only after the `/backlog` skill is present in the synced toolchain, so no session is left without an intent-capture entry point  
100	
```

</details>

<details>
<summary>✅ 🔧 Read: <code>specs/backlog-skill/decision_log.md</code></summary>

```
1	# Decision Log: backlog-skill
2	
3	## Decision 1: Feature name and scope
4	
5	**Date**: 2026-08-26
6	**Status**: accepted
7	
8	### Context
9	
10	The nextup skill has been sunset (it did not do what was needed) and spout is slated for removal. Both failed the same way: ephemeral output — nextup zones were never cleared and went stale; SPOUT.md was gitignored and stale the moment HEAD moved. A cross-repo assessment (2026-08-26) found forward intent across all repos living in gitignored or untracked files with no tracked home.
11	
12	### Decision
13	
14	Build one replacement feature named `backlog-skill`: a `/backlog` skill plus the sunset of nextup and spout, specced together in `specs/backlog-skill/`.
15	
16	### Rationale
17	
18	The replacement and the removal are one change — the migration of nextup.md zones only makes sense with the new destination in place, and shipping the skill without the sunset would leave two competing entry points.
19	
20	### Alternatives Considered
21	
22	- **`backlog` as the name**: matches the invocation `/backlog` - Rejected because the folder name would not distinguish the skill from the BACKLOG.md artifact it manages.
23	- **`nextup-spout-sunset`**: names the removal - Rejected because it hides the new capability, which is the larger half of the work.
24	
25	### Consequences
26	
27	**Positive:**
28	- One spec covers the full round trip: new skill, toolchain retirement, migration.
29	
30	**Negative:**
31	- Larger spec surface than a skill-only feature; the migration adds multi-repo coordination.
32	
33	---
34	
35	## Decision 2: Enroll the operator's remaining active repos; migrate all participants
36	
37	**Date**: 2026-08-26
38	**Status**: accepted
39	
40	### Context
41	
42	A set of repos already participates in align; several of the operator's active repos do not, and assessment found the unenrolled ones hold some of the richest untracked backlogs. (This log is committed, so repos are referred to by role; the concrete list is session-local operator state.)
43	
44	### Decision
45	
46	Enroll the operator-designated unenrolled repos as align participants within this feature's rollout, and run the nextup.md migration across all participants.
47	
48	### Alternatives Considered
49	
50	- **Existing participants only**: defer enrollment - Rejected because the unenrolled repos are where the migration pays off most.
51	- **This repo only, others ad hoc**: smallest scope - Rejected because ad hoc migration is exactly the untracked-intent pattern being retired.
52	
53	### Consequences
54	
55	**Positive:**
56	- The repos with the largest untracked backlogs get a tracked home in the same pass.
57	
58	**Negative:**
59	- Enrollment adds per-repo `.agentic.json` setup and align verification to the rollout.
60	
61	---
62	
63	## Decision 3: BACKLOG.md holds pre-spec work only
64	
65	**Date**: 2026-08-26
66	**Status**: accepted
67	
68	### Context
69	
70	BACKLOG.md needs a lifecycle contract: either track work through its whole life (mirroring all five Transit columns) or hold only pre-spec intent.
71	
72	### Decision
73	
74	The backlog holds only pre-spec items with statuses `idea` and `needs-spec` (mapping to Transit's Idea and Planning columns). Promotion to a spec removes the entry; specs/OVERVIEW.md and task files own the work from there.
75	
76	### Rationale
77	
78	Duplicated state that goes stale is the failure mode that killed nextup and SPOUT.md. In-progress and done states are already tracked by the spec system; mirroring them would reintroduce drift.
79	
80	### Alternatives Considered
81	
82	- **Full Transit mirror**: entries persist through idea → done - Rejected because it duplicates OVERVIEW.md/task state and will drift.
83	- **Promoted-pointer hybrid**: promotion rewrites entries to pointers - Rejected as accumulating clutter that needs periodic pruning, a maintenance chore with no consumer.
84	
85	### Consequences
86	
87	**Positive:**
88	- Nothing in the backlog can contradict the spec system; the file only shrinks when work starts.
89	- Transit import later maps cleanly: backlog statuses → Idea/Planning columns.
90	
91	**Negative:**
92	- No single file shows the full pipeline; answering "what is in flight" still needs OVERVIEW.md.
93	
94	---
95	
96	## Decision 4: Confirm once per run, then delete sources
97	
98	**Date**: 2026-08-26
99	**Status**: accepted
100	
101	### Context
102	
103	Consumed sources (nextup.md zones, loose proposals) are mostly gitignored or untracked, so deletion is unrecoverable. The clearing step must balance safety against leaving stale husks.
104	
105	### Decision
106	
107	The skill shows what it filed from each source and asks for approval once per run before deleting the source files. Declining leaves all sources untouched while keeping the filed entries.
108	
109	### Alternatives Considered
110	
111	- **Delete only after commit**: strongest guarantee - Rejected because it forces a commit into the skill's flow, and committing stays a user action.
112	- **Empty, never delete**: truncate to a template - Rejected because empty husk files are exactly the clutter being retired.
113	
114	### Consequences
115	
116	**Positive:**
117	- Untracked content is safe: by the time sources are deleted, it lives in the tracked backlog.
118	
119	**Negative:**
120	- A declined confirmation leaves content duplicated between source and backlog until the next run.
121	
122	---
123	
124	## Decision 5: Routing can amend requirements, not just append tasks
125	
126	**Date**: 2026-08-26
127	**Status**: accepted
128	
129	### Context
130	
131	A captured item that belongs to an existing spec could be filed as a task (fits existing requirements) or could change the spec's scope. Filing scope changes as tasks would silently bypass the requirements gate.
132	
133	### Decision
134	
135	Routing has three destinations: existing-spec task, existing-spec requirement amendment (which flags design/tasks as stale so those workflows re-run), or backlog entry (`needs-spec` / `idea`). Items are filed directly — the backlog only ever holds work with no spec home.
136	
137	### Rationale
138	
139	Requirement amendments make downstream change salient and re-engage the design/tasks workflows rather than letting scope creep in through the task list. The user accepted the resulting rebuild churn as a cost.
140	
141	### Alternatives Considered
142	
143	- **Always park in BACKLOG.md first**: human promotes later - Rejected as adding a manual step to every item; the backlog would accumulate routed-but-unmoved entries.
144	- **Tasks-only routing**: never touch requirements - Rejected because scope changes filed as tasks bypass the requirements gate.
145	
146	### Consequences
147	
148	**Positive:**
149	- Scope changes surface as requirement diffs, not buried tasks.
150	
151	**Negative:**
152	- A requirement amendment obligates a design/tasks re-run — heavier than dropping in a task.
153	
154	---
155	
156	## Decision 6: Decision overwrite mode, per-repo opt-in
157	
158	**Date**: 2026-08-26
159	**Status**: accepted
160	
161	### Context
162	
163	For some projects the supersede convention (mark old entry superseded, append new) buries the current state of a decision under its history. The user wants decisions overwritten in place for several of their application repos, so changes to design and downstream documents stay salient — accepting fragile renumbering in code comments and rebuild churn as a cost.
164	
165	### Decision
166	
167	A `decision_mode` key in `.agentic.json`: `overwrite` edits decision entries in place (same ID, updated date, no superseding entry); unset or `supersede` keeps today's behavior. The rollout sets `overwrite` in the repos the operator designates.
168	
169	### Alternatives Considered
170	
171	- **Overwrite as the global default, supersede opt-in**: covers "etc." without a list - Rejected by the user in favor of explicit opt-in.
172	- **Global overwrite, supersede retired**: simplest - Rejected because repos where decision history matters (this repo among them) lose the audit trail.
173	
174	### Consequences
175	
176	**Positive:**
177	- Decision logs in overwrite repos always read as current state; no archaeology through superseded entries.
178	
179	**Negative:**
180	- Overwrite repos lose in-file decision history (git history still holds it).
181	- References to decision IDs in code comments and documents can silently drift when entries are rewritten.
182	
183	---
184	
185	## Decision 7: BACKLOG.md encoding — phases as status, pending-only invariant
186	
187	**Date**: 2026-08-26
188	**Status**: accepted
189	
190	### Context
191	
192	Rune's parser is strict (H1, H2 phases, checkbox task items, indented detail lines; free prose fails) and its status model is only pending/in-progress/completed. The requirements demanded rune-parseability and custom statuses (`idea`, `needs-spec`) without saying how the two coexist — flagged as a blocker by the design-critic and confirmed by peer review.
193	
194	### Decision
195	
196	Statuses are H2 phases: `## Idea` and `## Needs Spec`. Phase membership is the status. All entries stay unchecked forever — since promotion removes an entry (Decision 3), a checked or in-progress entry is a defect, not a state. Capture date, source, and proposed spec name are indented detail lines. Rune write commands are not used on BACKLOG.md, and the process-status report rune-parses the file to enforce the contract.
197	
198	### Rationale
199	
200	Phases are first-class in rune, entries move between statuses without touching detail lines, and "everything reads as Pending" converts from an apparent limitation into a checkable invariant. Detail-line statuses would be invisible to every parser and forfeit the point of rune-parseability.
201	
202	### Alternatives Considered
203	
204	- **Detail-line status (`Status: idea`)**: keeps one phase - Rejected because no parser can select on it, forcing a bespoke Transit importer later.
205	- **Rune's native checkbox states as status**: no custom encoding - Rejected because pre-spec statuses do not map onto pending/in-progress/completed.
206	
207	### Consequences
208	
209	**Positive:**
210	- The contract is mechanically checkable today (process-status parse) and importable later (phases → Transit columns).
211	
212	**Negative:**
213	- Rune's write/renumber commands must be avoided on this one file; hand-edits that break parsing block the skill until repaired.
214	
215	---
216	
217	## Decision 8: decision_mode is read from .agentic.json at run time
218	
219	**Date**: 2026-08-26
220	**Status**: accepted
221	
222	### Context
223	
224	The draft said the mode would be "generated into each repo's agent instructions" — but review verified no per-repo agent-instruction generation path exists for any repo (align writes only MCP configs into targets; copilot-instructions is gated on `cloud_assets`, which is false in the repos the mode targets). The convention agents actually follow is a globally symlinked format reference that cannot express per-repo modes.
225	
226	### Decision
227	
228	Decision-writing workflows read `decision_mode` from the repo's `.agentic.json` at run time, defaulting to `supersede`. The global decision-log format reference and the shared convention text in all three toolchain wrappers (Claude, Codex, Copilot) document both modes and the manifest read. The named workflows: starwave skills, smolspec, fix-bug, spec-janitor, /backlog.
229	
230	### Alternatives Considered
231	
232	- **Per-repo generated instruction text**: static per-repo files - Rejected because the generation path doesn't exist and would have to be built, and generated text goes stale against the manifest.
233	- **Global convention only, no manifest**: simplest - Rejected because it cannot express per-repo modes at all.
234	
235	### Consequences
236	
237	**Positive:**
238	- One source of truth per repo; no new generation machinery.
239	
240	**Negative:**
241	- Every decision-writing workflow gains a manifest-read step, and a repo without `.agentic.json` silently stays in supersede mode.
242	
243	---
244	
245	## Decision 9: Backlog/spec consistency via /backlog reconciliation, not starwave hooks
246	
247	**Date**: 2026-08-26
248	**Status**: accepted
249	
250	### Context
251	
252	"Promotion removes the entry" had no owner: specs are normally created by the starwave workflow, which this feature does not modify, so entries for promoted work would linger — the drift Decision 3 exists to prevent.
253	
254	### Decision
255	
256	`/backlog` owns consistency: every run starts with a reconciliation pass that removes and reports entries whose proposed spec now exists. The starwave skills are untouched.
257	
258	### Alternatives Considered
259	
260	- **Modify starwave-creating-spec to prune the backlog**: removal at the moment of promotion - Rejected because it couples the spec workflow to the backlog and widens this feature into skills it otherwise doesn't touch.
261	- **Manual removal**: human obligation - Rejected as the unenforced-discipline pattern that failed before.
262	
263	### Consequences
264	
265	**Positive:**
266	- One owner; the spec workflow stays ignorant of the backlog.
267	
268	**Negative:**
269	- Stale entries persist between /backlog runs (bounded by run frequency, and visible in the tracked file).
270	
271	---
272	
273	## Decision 10: Requirement amendments leave a tracked staleness task
274	
275	**Date**: 2026-08-26
276	**Status**: accepted
277	
278	### Context
279	
280	Routing an item as a requirement amendment makes design.md/tasks.md stale. Reporting that only in-session is the ephemeral-state failure mode this feature exists to kill.
281	
282	### Decision
283	
284	An amendment appends a task to the amended spec's own task file naming the stale documents and the workflows to re-run. Amendments never renumber existing acceptance-criterion anchors.
285	
286	### Alternatives Considered
287	
288	- **Status flag in specs/OVERVIEW.md**: central visibility - Rejected because OVERVIEW.md is regenerated by the specs-overview skill and hand-set flags would be overwritten.
289	- **In-session report only**: no artifact - Rejected as ephemeral state, the pattern being retired.
290	
291	### Consequences
292	
293	**Positive:**
294	- Staleness is tracked, rune-visible, and surfaced by existing process-status drift checks.
295	
296	**Negative:**
297	- The staleness task must be kept honest — completing the re-run must check it off.
298	
299	---
300	
301	## Decision 11: Sunset ordering — skill first, migrate, then remove
302	
303	**Date**: 2026-08-26
304	**Status**: accepted
305	
306	### Context
307	
308	align raises an error if its seed root lacks `nextup.example.md`, so deleting the canonical template before updating align breaks every align run. Review also found the sunset's real footprint is ~5x the skill directories: five test fixtures, three test files, four agent notes, a runbook, scripts/README, and a spec-janitor reference.
309	
310	### Decision
311	
312	Strict ordering: (1) the /backlog skill lands and syncs; (2) migration runs across participating repos; (3) the sunset removes the skills, align seeding + canonical template in the same change, tests/fixtures, and documentation. Since no seeded `nextup.example.md` copies exist in any target repo, align gets no removal behavior — residual cleanup belongs to the migration flow with human eyes on it.
313	
314	### Alternatives Considered
315	
316	- **align converges the absence of nextup.example.md**: automated cleanup - Rejected because zero seeded copies exist to clean, and post-deletion align has no canonical to judge "previously seeded" against without risking user content.
317	- **No mandated ordering**: land as convenient - Rejected because one wrong merge order breaks align for every repo.
318	
319	### Consequences
320	
321	**Positive:**
322	- No intermediate state where align is broken or intent files are orphaned without a destination.
323	
324	**Negative:**
325	- The feature cannot ship as independent parallel streams; migration gates the sunset.
326	
327	---
328	
329	## Decision 12: Rollout administration is not a requirement
330	
331	**Date**: 2026-08-26
332	**Status**: accepted
333	
334	### Context
335	
336	The draft requirements carried per-repo rollout actions — enrolling new participants, setting `decision_mode` in designated repos, migration checklists, residual-file cleanup in other repos. The user's review: adoption or removal of tools in other repos is post-build administration, not system design; keeping it in requirements pollutes context and intent. A follow-up ruling extended this: committed spec documents must not name repos outside this one or machine-local paths — they would publish what the developer works on and reference ephemeral resources.
337	
338	### Decision
339	
340	Requirements describe only system behavior — what `/backlog` does in whatever repo it runs in, and what the sunset changes in this repo's toolchain. All per-repo rollout actions move to `rollout.md` in this spec folder as a checklist. Decisions 2 (enrollment scope) and 11 (skill → migrate → sunset ordering) stand, but their per-repo substance is executed via rollout.md, and the requirements retain only the toolchain-internal ordering constraint (skill present before sunset lands).
341	
342	### Rationale
343	
344	Behaviors like nextup.md user-zone capture, duplicate dropping, and all-duplicate delete eligibility are system requirements because they hold wherever the skill runs; visiting thirteen repos is a one-time operation with no design content. Separating them keeps the requirements testable against the system rather than against the state of the user's filesystem.
345	
346	### Alternatives Considered
347	
348	- **Keep rollout in requirements as a numbered section**: everything in one document - Rejected by the user: it pollutes design context and intent with administration.
349	- **Rollout as tasks in the task phase**: tracked with the implementation - Rejected because the task phase is coding-only by convention, and repo visits are not coding.
350	
351	### Consequences
352	
353	**Positive:**
354	- Requirements stay about the system; the design phase inherits no per-repo noise.
355	- Rollout has a checkable home with exit criteria instead of being implied by ACs.
356	
357	**Negative:**
358	- rollout.md is a new document kind in the spec folder; completion tracking is manual checkboxes, not rune.
359	
360	---
361	
362	## Decision 13: Duplicate detection matches repo-realized work, not only specs
363	
364	**Date**: 2026-08-26
365	**Status**: accepted
366	
367	### Context
368	
369	The design's contract notes widened the drop criterion from "realized in a spec" to shipped work generally — flagged by the design-critic as a requirements change smuggled through the design, feeding delete-eligibility of unrecoverable untracked sources. But the narrower criterion fails on the feature's own worked examples: consumed intent zones are typically realized via commits and changelog entries, not spec text, so migration would re-file already-shipped work.
370	
371	### Decision
372	
373	An item is a duplicate when its substance exists in the backlog, a spec document, or shipped work recorded in the repository (code, CHANGELOG). ACs 1.5 and 2.6 are amended accordingly; the match target is always reported, and the per-run deletion approval remains the backstop.
374	
375	### Alternatives Considered
376	
377	- **Spec-realization only**: as originally approved - Rejected because consumed zones would never register as duplicates and migration would re-file shipped work.
378	- **Backlog-only matching**: cheapest check - Rejected because it re-files anything that skipped the backlog on its way to shipping, which is most historical work.
379	
380	### Consequences
381	
382	**Positive:**
383	- Migration recognizes consumed zones; the backlog stays free of already-shipped work.
384	
385	**Negative:**
386	- The judgment surface is larger (code and changelog, not just specs), so dedup quality depends more on session diligence; the deletion approval gate is the control.
387	
388	---
389	
390	## Decision 14: decision_mode delivery is two-channel; AC 5.3 scoped by behavior
391	
392	**Date**: 2026-08-26
393	**Status**: accepted
394	
395	### Context
396	
397	The design claimed one paragraph in shared conventions would reach all decision-writing workflows with no per-skill edits. Review disproved this: three skills hard-code the supersede convention in their own instructions (spec-janitor's audit mandate, and the mid-implementation edit clauses in make-it-so and next-task), and skill-local instructions beat generic convention text at runtime. Review also found AC 5.3's named list was wrong: fix-bug contains no decision-log behavior, and /backlog itself writes none.
398	
399	### Decision
400	
401	Deliver the mode through both channels: the generated conventions text (all three toolchains), plus one-sentence edits to every skill whose instructions direct decision-log revision — spec-janitor (SKILL.md and its spec-conventions reference), make-it-so, next-task. AC 5.3 is amended to name workflows by behavior: skills whose instructions direct decision-log creation or revision.
402	
403	### Alternatives Considered
404	
405	- **Conventions text only**: single edit - Rejected because skill-local supersede mandates override it; spec-janitor would flag overwrite-mode logs as drift.
406	- **Per-skill edits only, no conventions text**: precise - Rejected because ad-hoc decision writing outside any skill (common in sessions) would never learn the mode.
407	
408	### Consequences
409	
410	**Positive:**
411	- No skill contradicts the mode; sessions without a skill still get the rule from conventions.
412	
413	**Negative:**
414	- Four skill files gain a mode-awareness sentence that future skill authors must remember to include when a new skill touches decision logs.
415	
416	---
417	
```

</details>

---

<details>
<summary>✅ 🔧 Bash</summary>

**Command:**
```bash
wc -l scripts/process_status.py scripts/sync-claude.sh scripts/align.py tests/test_process_status.py tests/test_sync_compat.py tests/test_align.py 2>&1
```

**Result:**
```
     264 scripts/process_status.py
      73 scripts/sync-claude.sh
     574 scripts/align.py
     331 tests/test_process_status.py
     248 tests/test_sync_compat.py
    1043 tests/test_align.py
    2533 total
```

</details>

<details>
<summary>✅ 🔧 ToolSearch</summary>

**Input:**
```json
{
  "max_results": 5,
  "query": "TaskCreate TaskUpdate"
}
```

**Result:**
```
[{"tool_name":"TaskCreate","type":"tool_reference"},{"tool_name":"TaskUpdate","type":"tool_reference"},{"tool_name":"TaskList","type":"tool_reference"}]
```

</details>

<details>
<summary>✅ 🔧 Bash</summary>

**Command:**
```bash
cat Makefile 2>&1 | head -50
```

**Result:**
```
# Development tooling for agentic-coding.
#
# bootstrap one-script new-machine setup (scripts/bootstrap.sh)
# generate  rebuild the checked-in generated files (claude/CLAUDE.md,
#           copilot/instructions/copilot-instructions.md, codex/AGENTS.md)
#           and MCP configs
# sync      create the ~/.claude and VS Code profile symlinks
# align     align this repository's own agent configs
# status    read-only process-status report over participating repos
#           (this repo plus the checked-in default list; pass explicit
#           paths via REPOS="path1 path2")
# test      run the Python unittest suite
# lint      shellcheck all shell scripts + fail if generated files drift
#           from their sources in shared/ and mcp/

.PHONY: bootstrap generate sync align status test lint lint-shell lint-drift

bootstrap:
	scripts/bootstrap.sh

generate:
	python3 scripts/generate.py

sync:
	scripts/sync-claude.sh

align:
	python3 scripts/align.py

status:
	python3 scripts/process_status.py $(REPOS)

test:
	python3 -m unittest discover -s tests

lint: lint-shell lint-drift

lint-shell:
	@command -v shellcheck >/dev/null 2>&1 || { \
		echo "shellcheck is not installed (brew install shellcheck)"; exit 1; }
	shellcheck scripts/*.sh

# Generated-drift check: regenerate in a way that leaves the working tree
# untouched — snapshot the checked-in generated files, run the generator,
# diff, then restore the snapshots — and fail when the checked-in files are
# out of date. Any conventions warnings generate.py emits (e.g. tail content
# in claude/CLAUDE.md that belongs in shared/) surface in this run's output.
lint-drift:
	@tmp="$$(mktemp -d)"; \
	cp claude/CLAUDE.md "$$tmp/CLAUDE.md"; \
```

</details>

## 🤖 Assistant · 2026-08-26T23:55:26+10:00

Good — `make test` runs `python3 -m unittest discover -s tests`, `make lint` runs shellcheck + drift check. Now launching two parallel agents for the two available streams.

---

<details>
<summary>✅ 🔧 Agent: Toolchain phase: tasks 4,5,6</summary>

**Input:**
```json
{
  "description": "Toolchain phase: tasks 4,5,6",
  "prompt": "Repo: /Users/r/repos/agentic-coding (branch specs/backlog-skill). You're implementing stream 2 of the \"Toolchain\" phase from specs/backlog-skill/tasks.md — task groups 4, 5, and 6. Each group is TDD: a \"red\" subtask (write failing tests) then a \"green\" subtask (implement, tests pass).\n\nFirst read specs/backlog-skill/design.md and specs/backlog-skill/requirements.md in full for context — don't skip this. Also read specs/backlog-skill/decision_log.md decisions 3, 7, 11 (backlog phase/status encoding) since they explain why the BACKLOG.md schema check works the way it does.\n\nWork the three groups in order (4, then 5, then 6), each red-then-green. After finishing each subtask, run `rune complete specs/backlog-skill/tasks.md \u003cid\u003e` (e.g. `rune complete specs/backlog-skill/tasks.md 4.1`). Run `make test` after each green subtask; run `make lint` after all three groups are done (it runs shellcheck on scripts/*.sh and a generated-file drift check).\n\n## Task 4 — BACKLOG.md column and schema check in scripts/process_status.py\n\nDesign section \"BACKLOG.md schema check in process_status.py\": replace the two presence-only nextup columns (NEXTUP, EXAMPLE: info keys around :118-119, assigns :131-132, header :188, `_row` :205-206 — line numbers approximate, re-check by reading the file) with one BACKLOG column: `-` (absent, never drift), `ok`, or `drift`. Add a `backlog-drift` flag to `drift_flags()` with a reason in the detail lines, mirroring how `rune-drift` already works.\n\nThe check (`_backlog_status`, hybrid, each layer covers a hole the other misses):\n1. Parse gate: existing `_rune_parses` on `specs/BACKLOG.md`. rune missing → existing warning path, skip.\n2. Phase set/order: raw-text scan of `^##[ ]` headings, right-trimmed, case-sensitive — must equal exactly `[\"Idea\", \"Needs Spec\"]`. Raw scan (not rune JSON) because an empty backlog yields `PhaseMarkers: []` in rune and empty-but-valid is the normal post-reconciliation state. `## idea` (wrong case) is drift.\n3. Unchecked invariant: `rune list --format json` → `Stats.Pending == Stats.Total`. Authoritative over a raw checkbox regex because rune counts nested subtask checkboxes that a `^- \\[` scan misses. (Parse gate already ran, so fenced-content evasion isn't possible.)\n4. H1 presence: raw scan for a leading `# ` title.\n\nOut of scope deliberately: detail-line grammar (source/date/arrow format) — do not check it.\n\nAlso rewrite the module docstring (currently around :4-16) and the argparse description (around :252) to describe the BACKLOG column instead of nextup.\n\n4.1 (red): in tests/test_process_status.py, add BACKLOG fixture tests and remove the nextup-column assertions. Fixtures needed:\n- ok cases: absent (renders `-`), valid, empty-but-valid (both phases present with zero entries — must render `ok`, not drift), gapped numbering (`ok`), a detail line containing the U+2192 arrow char (`ok`), a phase heading with trailing whitespace (`ok`)\n- drift cases: rune-unparseable, wrong/extra/case-variant phase set, a checked entry, a nested checked subtask (only the Stats-based check catches this one — a naive top-level-only checkbox scan would miss it), missing H1\n\n4.2 (green): implement `_backlog_status` and wire it in per the above, then make all 4.1 tests pass.\n\n## Task 5 — Owned-symlink prune in scripts/sync-claude.sh\n\nDesign section \"sync-claude.sh prune\": after the per-skill link loop, for each entry in `~/.agents/skills/` (nullglob-guarded), if it's a symlink (`[ -L ]`) whose literal target string is prefixed by `$REPO_CLAUDE_DIR/skills/` and the target does not exist (`[ ! -e ]`), remove it. Literal prefix comparison is sufficient — the script only ever creates absolute links. Links resolving elsewhere must never be touched.\n\n5.1 (red): add prune test cases to tests/test_sync_compat.py — dangling owned link (removed), dangling foreign link (kept), live owned link (kept), empty skills dir (no-op). Read the existing test file first to match its harness style (it likely shells out to sync-claude.sh against a temp HOME).\n\n5.2 (green): implement the prune loop in scripts/sync-claude.sh, make 5.1 pass. Run `shellcheck scripts/sync-claude.sh` too.\n\n## Task 6 — Remove align step 6 and the canonical template\n\nDesign section \"align.py step-6 removal\": delete `NEXTUP_EXAMPLE`, `NEXTUP_LM_MARKER`, `_ensure_nextup_gitignore`, `_converge_nextup_template`, the call site, the seed-root existence error, the \"Managed files\" docstring list entry, and the step-6 docstring text; renumber remaining steps. `_shadow_copy` iterates `MANAGED_JSON + (NEXTUP_EXAMPLE, \".gitignore\")` — remove both `NEXTUP_EXAMPLE` and `\".gitignore\"` from that tuple (align no longer touches `.gitignore` at all — gitignore management existed only for nextup). No replacement behavior: align must not seed or manage BACKLOG.md. Delete the canonical `nextup.example.md` seed-root template file in the same commit as the code removal (align would otherwise crash on a seed root missing an expected file — check tests/fixtures/align for the seed root location).\n\n6.1 (red): rewrite tests/test_align.py — drop the step-6 test classes and all 8 nextup fixture repos (canonical, gitignore-append, gitignore-create, markerless, missing, plan-only, session-file, user-zone) plus their .gitignore files and the seed-root nextup.example.md. Add two new tests: align leaves a stray nextup.example.md untouched in a target repo that already has one (stop-managing means no touch, not delete — do NOT make align delete pre-existing files), and align never writes .gitignore anywhere.\n\n6.2 (green): delete the align step-6 code and the canonical nextup.example.md template in the same change; make 6.1 pass.\n\n## Constraints\n- Don't touch task group 7 (Sunset) — that's a different stream, being handled by another agent in parallel, and its green subtask (7.2) is blocked on your 4.2 and 6.2 finishing anyway.\n- Follow existing code style in each file exactly — don't introduce new abstractions or refactor unrelated code.\n- If you find a design/line-number detail that's actually wrong when you read the live file, follow what you observe in the file over what's written here — the design doc line numbers are approximate.\n- Do not commit anything. Do not touch specs/backlog-skill/tasks.md except via `rune complete`.\n\nReport back: which subtasks completed, `make test` and lint results, and anything you found that deviated from the design doc."
}
```

**Result:**
```
[{"text":"Async agent launched successfully. (This tool result is internal metadata — never quote or paste any part of it, including the agentId below, into a user-facing reply.)\nagentId: a258c20e3343a4f6a (internal ID - do not mention to user. Use SendMessage with to: 'a258c20e3343a4f6a', summary: '\u003c5-10 word recap\u003e' to continue this agent.)\nThe agent is working in the background. You will be notified automatically when it completes. You know nothing about its results until that notification arrives — do not report, assume, or predict them; continue other work or respond to the user in the meantime.\nDo not duplicate this agent's work — avoid working with the same files or topics it is using.\noutput_file: /private/tmp/claude-501/-Users-r-repos-agentic-coding/58128ca8-7912-4a19-b794-8ba104e9861c/tasks/a258c20e3343a4f6a.output\nDo NOT Read or tail this file via the shell tool — it is the full subagent JSONL transcript and reading it will overflow your context. If the user asks for progress, say the agent is still running; you'll get a completion notification.","type":"text"}]
```

</details>

<details>
<summary>✅ 🔧 Agent: Sunset phase: task 7.1 red test</summary>

**Input:**
```json
{
  "description": "Sunset phase: task 7.1 red test",
  "prompt": "Repo: /Users/r/repos/agentic-coding (branch specs/backlog-skill). You're implementing stream 1's currently-ready work from specs/backlog-skill/tasks.md — task 7.1 only. Task 7 (\"Sunset gate and removals\") also has a 7.2 (green) subtask, but it's blocked on other tasks (4.2, 6.2 — being done by a parallel agent right now — plus 7.1 itself) so do NOT attempt 7.2. Only do 7.1.\n\nFirst read specs/backlog-skill/design.md in full, particularly the \"Sunset reference audit (AC 6.5)\" section and the \"Testing Strategy\" section's \"Sunset grep test\" bullet. Also read specs/backlog-skill/requirements.md requirement 6 (Sunset of nextup and spout).\n\n## Task 7.1 (red) — Write the tracked-files sunset grep test\n\nAdd a new test (find the right test file — likely a new or existing file under tests/, follow the repo's existing test-file naming/style) that:\n- Sources its file set from `git ls-files` (tracked files only — untracked working files, the `.worktrees/` sibling checkout, and caches must be out of scope by construction)\n- Case-insensitive greps tracked file contents (and/or paths — check the design's work-list table for what \"reference\" means here) for `nextup` or `spout`\n- Exempts `specs/` (this spec folder and CHANGELOG.md legitimately mention nextup/spout historically), `CHANGELOG.md`, and the test file itself\n- This test SHOULD currently fail (red) — the sunset removal (task 7.2, done later by someone else) is what will make it pass. Confirm it fails for the expected reason (existing nextup/spout references still in the tree), not for some unrelated bug in the test itself.\n\nDesign's known-footprint work list (for your own sanity check of what should eventually go, not something you fix now): 8 align test fixture repos + seed root under tests/fixtures/align, tests/test_align.py refs, tests/test_process_status.py, tests/test_sync_compat.py, scripts/process_status.py docstring/argparse text, docs/agent-notes/{align-tooling,process-status,spec-janitor,transit-integration}.md, docs/runbooks/process-onboarding.md, scripts/README.md, claude/skills/spec-janitor/SKILL.md, claude/uplift-candidates.md, .gitignore.\n\nOnce the test is written and confirmed red for the right reason, mark it complete: `rune complete specs/backlog-skill/tasks.md 7.1`.\n\n## Constraints\n- Do not implement 7.2 (the actual removals) — a parallel agent and the orchestrator will handle that once its blockers clear.\n- Do not touch task groups 4, 5, 6 — another agent is handling those in parallel.\n- Do not commit anything. Do not touch specs/backlog-skill/tasks.md except via `rune complete`.\n\nReport back: the test you wrote, confirmation it currently fails for the expected reason, and its file path."
}
```

**Result:**
```
[{"text":"Async agent launched successfully. (This tool result is internal metadata — never quote or paste any part of it, including the agentId below, into a user-facing reply.)\nagentId: acfe5dcdd1845e23d (internal ID - do not mention to user. Use SendMessage with to: 'acfe5dcdd1845e23d', summary: '\u003c5-10 word recap\u003e' to continue this agent.)\nThe agent is working in the background. You will be notified automatically when it completes. You know nothing about its results until that notification arrives — do not report, assume, or predict them; continue other work or respond to the user in the meantime.\nDo not duplicate this agent's work — avoid working with the same files or topics it is using.\noutput_file: /private/tmp/claude-501/-Users-r-repos-agentic-coding/58128ca8-7912-4a19-b794-8ba104e9861c/tasks/acfe5dcdd1845e23d.output\nDo NOT Read or tail this file via the shell tool — it is the full subagent JSONL transcript and reading it will overflow your context. If the user asks for progress, say the agent is still running; you'll get a completion notification.","type":"text"}]
```

</details>

## 🤖 Assistant · 2026-08-26T23:56:04+10:00

Both agents are running in the background — one on tasks 4/5/6 (Toolchain stream), one on task 7.1 (Sunset grep test, red). I'll wait for both to finish before handling task 7.2 and running `/commit`.

---

## 👤 User · 2026-08-26T23:58:10+10:00

<task-notification>
<task-id>acfe5dcdd1845e23d</task-id>
<tool-use-id>toolu_016FvxdDeJQasCRkg6R63hpi</tool-use-id>
<output-file>/private/tmp/claude-501/-Users-r-repos-agentic-coding/58128ca8-7912-4a19-b794-8ba104e9861c/tasks/acfe5dcdd1845e23d.output</output-file>
<status>completed</status>
<summary>Agent "Sunset phase: task 7.1 red test" finished</summary>
<note>A task-notification fires each time this agent stops with no live background children of its own. The user can send it another message and resume it, so the same task-id may notify more than once.</note>
<result>Task 7.1 complete. Summary:

**File written**: `/Users/r/repos/agentic-coding/tests/test_sunset_grep.py`

The test:
- Sources its file set via `git ls-files` (subprocess, `cwd=REPO_ROOT`) — tracked files only.
- For each tracked path, checks case-insensitively for `nextup|spout` in both the path itself and its decoded UTF-8 content (binary/undecodable files are skipped as non-text).
- Exempts anything under `specs/`, `CHANGELOG.md`, and the test file itself (computed via `Path(__file__)` so it's self-referential, not hardcoded).
- Asserts the offender list is empty.

**Confirmed red for the expected reason**: ran `python3 -m unittest tests.test_sunset_grep -v` — it fails listing 40 tracked offenders, matching the design's known footprint: the 8 `nextup-*` align fixture repos and their `.gitignore`/`.agentic.json`/`nextup.example.md` files, `tests/fixtures/align/seed-root/nextup.example.md`, root `nextup.example.md`, three test files (`test_align.py`, `test_process_status.py`, `test_sync_compat.py`), four agent notes, `docs/runbooks/process-onboarding.md`, `scripts/README.md`, `scripts/align.py`, `scripts/process_status.py`, `README.md`, `.gitignore`, `claude/uplift-candidates.md`, and the `claude/skills/nextup`/`claude/skills/spout` dirs. Ran the full suite (`python3 -m unittest discover -s tests`): 178 tests, only this one new test fails — no other test broke.

One thing worth flagging to whoever picks up 7.2 (or the orchestrator): `claude/skills/backlog/SKILL.md` also currently matches (it legitimately mentions `nextup.md` and `SPOUT.md` by name because the backlog skill's own spec requires detecting a legacy `nextup.md` and excluding a generated `SPOUT.md`). Design's touch-map/footprint table doesn't list this file for cleanup, and the grep gate's exemption list (`specs/`, `CHANGELOG.md`, test file) doesn't cover it either. As written, this test will still be red after 7.2 removes everything else, purely because of these two functional filename references in the new skill. That's a design-level gap 7.2 will need to resolve (e.g., add an explicit exemption, or find phrasing that avoids the literal strings) — not something I fixed, since it's outside 7.1's scope and touches the skill file another stream is not supposed to be blocked by me editing.

Did not touch task groups 4/5/6, did not implement 7.2, did not commit anything, and `specs/backlog-skill/tasks.md` was only modified via `rune complete`.</result>
<usage><subagent_tokens>62422</subagent_tokens><tool_uses>14</tool_uses><duration_ms>127497</duration_ms></usage>
</task-notification>

---

<details>
<summary>✅ 🔧 Bash</summary>

**Command:**
```bash
cat .agentic.json 2>&1; echo "---"; cat tests/test_sunset_grep.py 2>&1
```

**Result:**
```
{
  "servers": [
    "devtools"
  ],
  "cloud_assets": false,
  "transit_project": "agentic-coding"
}
---
"""Permanent guard against reintroducing nextup/spout (Req 6.5).

Sources its file set from `git ls-files` — tracked files only, so
untracked working files, the .worktrees/ sibling checkout, and caches
are out of scope by construction. Case-insensitively checks both each
tracked file's path and its contents for "nextup" or "spout": the
known footprint at spec time includes fixture directories/files whose
*names* carry the pattern (e.g. tests/fixtures/align/repos/nextup-canonical,
nextup.example.md) as well as prose/code that merely mentions it.

Exempt: specs/ (this spec folder and others legitimately document the
sunset historically), CHANGELOG.md (historical record), and this test
file itself.

Expected to be red until task 7.2 removes the last tracked references
(skill dirs, align fixtures, docs, scripts, README). Passing is the
sunset's completion signal.
"""

import re
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
THIS_FILE = Path(__file__).resolve().relative_to(REPO_ROOT).as_posix()

PATTERN = re.compile(r"nextup|spout", re.IGNORECASE)

EXEMPT_PATH_PREFIXES = ("specs/",)
EXEMPT_FILES = {"CHANGELOG.md", THIS_FILE}


def _tracked_files():
    """Return repo-relative paths of every git-tracked file."""
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line for line in result.stdout.splitlines() if line]


def _is_exempt(rel_path):
    if rel_path in EXEMPT_FILES:
        return True
    return any(rel_path.startswith(prefix) for prefix in EXEMPT_PATH_PREFIXES)


class SunsetGrepTest(unittest.TestCase):
    """AC 6.5: no tracked nextup/spout references outside the exempt set."""

    def test_no_tracked_nextup_or_spout_references(self):
        offenders = []

        for rel_path in _tracked_files():
            if _is_exempt(rel_path):
                continue

            if PATTERN.search(rel_path):
                offenders.append(f"{rel_path}: path matches nextup|spout")
                continue

            full_path = REPO_ROOT / rel_path
            try:
                raw = full_path.read_bytes()
            except OSError:
                continue  # e.g. a tracked symlink to a missing target
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                continue  # binary file; not a text reference

            if PATTERN.search(text):
                offenders.append(f"{rel_path}: content matches nextup|spout")

        self.assertEqual(
            offenders,
            [],
            "Tracked nextup/spout references remain (removed by sunset task 7.2):\n"
            + "\n".join(offenders),
        )


if __name__ == "__main__":
    unittest.main()
```

</details>

<details>
<summary>✅ 🔧 Bash</summary>

**Command:**
```bash
grep -in "nextup\|spout" claude/skills/backlog/SKILL.md 2>&1
```

**Result:**
```
3:description: Capture loose ideas, note files, and audit findings into a tracked, rune-parseable specs/BACKLOG.md, route each item to where the work belongs — an existing spec's tasks, an existing spec's requirements, or the backlog itself — and clear the sources once filed. Replaces the sunset nextup and spout skills. Use when the user says "add this to the backlog", "capture these notes", "file this idea", "/backlog", or hands over loose text/files with forward intent and no tracked home.
27:  - A root `nextup.md`, regardless of tracked status, **user zone only**: everything above the first recognised machine marker (`<!-- LM -->`, legacy `<!-- ML -->`, or `<!-- nextup:machine -->`) ends the zone; a `<!-- USER -->` marker belongs to the zone it opens; with no marker at all, the whole file is the zone.
29:  - Excluded from detection, always: `SPOUT.md` (a generated artifact from the retired spout skill, if still present), `specs/BACKLOG.md` (this skill's own artifact), and `specs/OVERVIEW.md` (the generated index).
91:An item is a duplicate — dropped, not filed — when its substance already exists in one of: the backlog, a spec document, or shipped work recorded in the repository (code, `CHANGELOG.md`). This is deliberately wider than "already in a spec": consumed intent zones (an old `nextup.md`, a loose proposal) are typically realized via commits and changelog entries, not spec text, so a narrower check would re-file work that has already shipped. Always report the match target — which backlog entry, spec, or commit/changelog line the item matched.
117:- MUST exclude `SPOUT.md`, `specs/BACKLOG.md`, and `specs/OVERVIEW.md` from source detection.
```

</details>

## 🤖 Assistant · 2026-08-26T23:58:57+10:00

Task 7.1's agent surfaced a real gap: the sunset grep test will never go green because `claude/skills/backlog/SKILL.md` legitimately has to name `nextup.md`/`SPOUT.md` (the skill's job is to detect/exclude those exact files). That's a spec-level gap, not a bug in the test. I'll record it as a new decision and amend AC 6.5, design.md, and the test's exemption list before task 7.2 can land cleanly.

---

## 🤖 Assistant · 2026-08-26T23:58:59+10:00

<details>
<summary>✅ 🔧 Edit: <code>specs/backlog-skill/requirements.md</code></summary>

```patch
 2. <a name="6.2"></a>The align toolchain SHALL stop seeding `nextup.example.md` and stop managing `nextup.md` gitignore entries, with the canonical `nextup.example.md` removed in the same change so align never runs against a seed root missing a file it requires  
 3. <a name="6.3"></a>The process-status report SHALL drop both nextup columns (presence and example convergence) and their drift logic, replacing them with BACKLOG.md presence and the parse check of [3.5](#3.5)  
 4. <a name="6.4"></a>The sync script SHALL remove symlinks that point into this repo's skills directory but whose target no longer exists, and SHALL NOT touch links it does not own  
-5. <a name="6.5"></a>After the sunset lands, `nextup` and `spout` SHALL have no remaining references in the toolchain — skills, scripts, tests, fixtures, agent notes, runbooks, and README — with historical records (`specs/`, `CHANGELOG.md`) exempt; the known footprint at spec time spans the five align test fixture repos and seed root, three test files, four agent notes, the process-onboarding runbook, `scripts/README.md`, and the spec-janitor skill  
+5. <a name="6.5"></a>After the sunset lands, `nextup` and `spout` SHALL have no remaining references in the toolchain — skills, scripts, tests, fixtures, agent notes, runbooks, and README — with historical records (`specs/`, `CHANGELOG.md`) exempt, and with the `/backlog` skill's own functional references to the legacy filenames it must detect and exclude (`nextup.md`, `SPOUT.md`) exempt; the known footprint at spec time spans the five align test fixture repos and seed root, three test files, four agent notes, the process-onboarding runbook, `scripts/README.md`, and the spec-janitor skill  
 6. <a name="6.6"></a>The sunset changes SHALL land only after the `/backlog` skill is present in the synced toolchain, so no session is left without an intent-capture entry point  
```

</details>

<details>
<summary>✅ 🔧 Edit: <code>specs/backlog-skill/design.md</code></summary>

```patch
 
 ### Sunset reference audit (AC 6.5)
 
-The gate is a test that greps **git-tracked files only** (`git ls-files` sourced), case-insensitive `nextup|spout`, exempting `specs/`, `CHANGELOG.md`, and the test file itself. Tracked-only is both the correct scope (AC 6.5 concerns the committed toolchain) and what makes the gate stable: untracked working files, the `.worktrees/` sibling checkout, and caches are out by construction. The tracked-tree scope is a superset of AC 6.5's enumerated surfaces — stricter is acceptable.
+The gate is a test that greps **git-tracked files only** (`git ls-files` sourced), case-insensitive `nextup|spout`, exempting `specs/`, `CHANGELOG.md`, the test file itself, and `claude/skills/backlog/SKILL.md` (Decision 15 — that file must name the legacy filenames `nextup.md`/`SPOUT.md` to detect and exclude them, a functional reference rather than leftover debris). Tracked-only is both the correct scope (AC 6.5 concerns the committed toolchain) and what makes the gate stable: untracked working files, the `.worktrees/` sibling checkout, and caches are out by construction. The tracked-tree scope is a superset of AC 6.5's enumerated surfaces — stricter is acceptable.
 
 Work list (every tracked reference at design time):
 
```

</details>

<details>
<summary>✅ 🔧 Edit: <code>specs/backlog-skill/design.md</code></summary>

```patch
 - **test_process_status.py**: fixture BACKLOG.md variants asserting column value and drift detail — absent (`-`, no drift), valid, **empty-but-valid** (both phases, zero entries → `ok`), gapped numbering (`ok`), U+2192 arrow detail line (`ok`), trailing-whitespace heading (`ok`), rune-unparseable, wrong/extra/case-variant phase, checked entry, **nested checked subtask** (drift via Stats), missing H1. Nextup-column assertions removed.
 - **test_sync_compat.py**: dangling owned link (removed), dangling foreign link (kept), live owned link (kept), empty skills dir (no-op).
 - **test_generate.py**: golden-file update — the decision_mode rules appear in all three generated outputs.
-- **Sunset grep test** (new): `git ls-files` sourced, case-insensitive `nextup|spout`, exempting `specs/`, `CHANGELOG.md`, and itself; permanent guard against reintroduction.
+- **Sunset grep test** (new): `git ls-files` sourced, case-insensitive `nextup|spout`, exempting `specs/`, `CHANGELOG.md`, itself, and `claude/skills/backlog/SKILL.md` (Decision 15); permanent guard against reintroduction.
 - The skill itself is instruction markdown — exercised by the rollout migration (rollout.md carries acceptance scenarios for Requirements 1, 2, and 4), not unit tests; the schema check is what keeps skill drift detectable.
 - Tasks file: encode the AC 6.6 ordering (skill commit before sunset commit) as rune `blocked-by` dependencies so the sequence is mechanical.
 
```

</details>

---

## 🤖 Assistant · 2026-08-26T23:59:07+10:00

Now appending the decision log entry (default `decision_mode` = supersede, but this is a new decision, not a revision, so no superseding needed).

---

## 🤖 Assistant · 2026-08-26T23:59:15+10:00

<details>
<summary>✅ 🔧 Edit: <code>specs/backlog-skill/decision_log.md</code></summary>

```patch
 - Four skill files gain a mode-awareness sentence that future skill authors must remember to include when a new skill touches decision logs.
 
 ---
+
+## Decision 15: Sunset grep gate exempts the /backlog skill's own functional legacy-filename references
+
+**Date**: 2026-08-26
+**Status**: accepted
+
+### Context
+
+Implementing task 7.1 (the sunset grep test itself) surfaced that `claude/skills/backlog/SKILL.md` legitimately contains the literal strings `nextup` (in `nextup.md`) and `spout` (in `SPOUT.md`), because the skill's own job is to detect a legacy `nextup.md` file and exclude a generated `SPOUT.md` file by name. AC 6.5's exemption list (`specs/`, `CHANGELOG.md`, the test file) did not anticipate this: without an added exemption, the grep gate would stay red forever after task 7.2's removals land, flagging load-bearing skill behavior as if it were leftover sunset debris.
+
+### Decision
+
+Add `claude/skills/backlog/SKILL.md` to the sunset grep gate's exemption list, alongside `specs/` and `CHANGELOG.md`.
+
+### Rationale
+
+Exempting the whole file is the smallest fix that doesn't compromise the file's own correctness — its filename references are load-bearing spec behavior (Requirement 1.2's `nextup.md` detection, 1.3's `SPOUT.md` exclusion), not cleanup debris, and no rewording describes "detect a file named nextup.md" without the literal string.
+
+### Alternatives Considered
+
+- **Reword SKILL.md to avoid literal filename strings**: describe rather than name the files - Rejected because the skill's job is literally to look for files with those names; obscuring the string makes the instructions harder to follow correctly, for zero grep-gate benefit.
+- **Narrow the grep pattern to exclude filename-shaped matches**: keep the exemption list short - Rejected as fragile pattern engineering that would also blind the gate to genuine future regressions elsewhere.
+
+### Consequences
+
+**Positive:**
+- The grep gate can actually reach green once 7.2 lands; the exemption is narrow (one file) rather than a broad pattern change.
+
+**Negative:**
+- A fourth exempt path (beyond the original three-item list) is something future maintainers must remember when reasoning about what "exempt" covers.
+
+---
```

</details>

---

## 🤖 Assistant · 2026-08-26T23:59:17+10:00

Now updating the test file itself to add the exemption:

---

## 🤖 Assistant · 2026-08-26T23:59:19+10:00

<details>
<summary>✅ 🔧 Edit: <code>tests/test_sunset_grep.py</code></summary>

```patch
 nextup.example.md) as well as prose/code that merely mentions it.
 
 Exempt: specs/ (this spec folder and others legitimately document the
-sunset historically), CHANGELOG.md (historical record), and this test
-file itself.
+sunset historically), CHANGELOG.md (historical record), this test file
+itself, and claude/skills/backlog/SKILL.md (Decision 15 — that skill's
+own job is to detect a legacy nextup.md and exclude a generated
+SPOUT.md, so it must name both filenames literally).
 
 Expected to be red until task 7.2 removes the last tracked references
 (skill dirs, align fixtures, docs, scripts, README). Passing is the
```

</details>

<details>
<summary>✅ 🔧 Edit: <code>tests/test_sunset_grep.py</code></summary>

```patch
 PATTERN = re.compile(r"nextup|spout", re.IGNORECASE)
 
 EXEMPT_PATH_PREFIXES = ("specs/",)
-EXEMPT_FILES = {"CHANGELOG.md", THIS_FILE}
+EXEMPT_FILES = {"CHANGELOG.md", THIS_FILE, "claude/skills/backlog/SKILL.md"}
 
 
 def _tracked_files():
```

</details>

---

## 🤖 Assistant · 2026-08-26T23:59:22+10:00

Now confirming the test still fails for the right reason (no other unrelated breakage from this exemption change), and waiting for the Toolchain-stream agent.

---

<details>
<summary>✅ 🔧 Bash</summary>

**Command:**
```bash
python3 -m unittest tests.test_sunset_grep -v 2>&1 | tail -20
```

**Result:**
```
tests/fixtures/align/repos/nextup-markerless/nextup.example.md: path matches nextup|spout
tests/fixtures/align/repos/nextup-missing/.agentic.json: path matches nextup|spout
tests/fixtures/align/repos/nextup-missing/.gitignore: path matches nextup|spout
tests/fixtures/align/repos/nextup-plan-only/.gitignore: path matches nextup|spout
tests/fixtures/align/repos/nextup-plan-only/nextup.example.md: path matches nextup|spout
tests/fixtures/align/repos/nextup-session-file/.agentic.json: path matches nextup|spout
tests/fixtures/align/repos/nextup-session-file/.gitignore: path matches nextup|spout
tests/fixtures/align/repos/nextup-session-file/nextup.md: path matches nextup|spout
tests/fixtures/align/repos/nextup-user-zone/.agentic.json: path matches nextup|spout
tests/fixtures/align/repos/nextup-user-zone/.gitignore: path matches nextup|spout
tests/fixtures/align/repos/nextup-user-zone/nextup.example.md: path matches nextup|spout
tests/fixtures/align/seed-root/nextup.example.md: path matches nextup|spout
tests/test_align.py: content matches nextup|spout
tests/test_process_status.py: content matches nextup|spout
tests/test_sync_compat.py: content matches nextup|spout

----------------------------------------------------------------------
Ran 1 test in 0.035s

FAILED (failures=1)
```

</details>

## 🤖 Assistant · 2026-08-26T23:59:25+10:00

Still red for the right reason (only the pending sunset removals remain — the `SKILL.md` exemption is applied correctly and no longer appears in the offender list). Now waiting for the Toolchain-stream agent (tasks 4/5/6) to complete before tackling task 7.2.

---

<details>
<summary>❌ 🔧 ScheduleWakeup</summary>

**Input:**
```json
{
  "delaySeconds": 1200,
  "noop": false,
  "reason": "Fallback heartbeat while the Toolchain-stream subagent (tasks 4/5/6) runs in the background; its completion notification is the real wake signal"
}
```

**Result:**
```
`prompt` is required when `stop` is not true.
```

</details>

<details>
<summary>✅ 🔧 Bash</summary>

**Command:**
```bash
true
```

**Result:**
```
(Bash completed with no output)
```

</details>

## 🤖 Assistant · 2026-08-26T23:59:31+10:00

ScheduleWakeup is only for `/loop` mode, not needed here — I'll get an automatic notification when the Toolchain agent (tasks 4/5/6) finishes. Standing by until then.

---

