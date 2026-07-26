---
references:
    - specs/spec-janitor/requirements.md
    - specs/spec-janitor/design.md
    - specs/spec-janitor/decision_log.md
---
# Spec Janitor Implementation

## Conventions and Auditor

- [ ] 1. Author the conventions reference with stable rule IDs <!-- id:a3keety -->
  - Create claude/skills/spec-janitor/references/spec-conventions.md
  - Rule families SJ-MODE/REF/TASK/SUP/FILE/DRIFT per the design table; each rule gets a stable ID and a one-paragraph normative statement
  - Mode recognition from primary documents alone (full: requirements+design; smol: smolspec; PRD: prd; bugfix: report); task files checked after recognition
  - Task-file grammar: front matter, phase H2s, checkbox tasks with 7-char lowercase alphanumeric stable IDs, Blocked-by/Stream/Requirements metadata lines, sequential numbering, uniform schema per file
  - Bugfix report shape (report.md sections, optional solution-comparison.md), supersession annotation rules, filing rules
  - Stream: 1
  - Requirements: [7.1](requirements.md#7.1)

- [ ] 2. Write failing detection tests with the survey fixture corpus <!-- id:a3keetz -->
  - tests/test_spec_lint.py (stdlib unittest) + fixtures under tests/fixtures/spec_lint/
  - Fixtures reproduce the survey: dangling anchors, mixed-ID task file, out-of-sequence numbering, zero-recognized-document folder (must fire SJ-MODE-001 — pins janitor-owned discovery, not specs-overview discovery), bugfix-shape violations, bugfix-shaped folder outside bugfixes/, nested domains, PRD multi-task-file, clean repo, no-specs repo
  - Pin JSON schema (evidence array, closed 3-value disposition enum), exit codes 0/1/2, dotfolder and .janitor.json exemption, rune-absent skip note with rune_available: false
  - Blocked-by: a3keety (Author the conventions reference with stable rule IDs)
  - Stream: 1
  - Requirements: [1.1](requirements.md#1.1), [1.2](requirements.md#1.2), [1.4](requirements.md#1.4), [1.5](requirements.md#1.5), [1.6](requirements.md#1.6), [1.7](requirements.md#1.7), [1.8](requirements.md#1.8), [5.5](requirements.md#5.5)

- [ ] 3. Implement spec_lint.py detection to pass the tests <!-- id:a3keeu0 -->
  - claude/skills/spec-janitor/spec_lint.py, stdlib only
  - Detectors SJ-REF-001/002, SJ-TASK-001/002/003, SJ-MODE-001/002/003; anchor grammar per design (a-name anchors + GitHub heading slugs)
  - Human report grouped by spec + --json output; rune verification via shutil.which, failures become SJ-TASK-001 with stderr evidence
  - Spec naming by repo-relative path under specs/; findings with identical id merge into one finding with multiple evidence entries
  - Blocked-by: a3keetz (Write failing detection tests with the survey fixture corpus)
  - Stream: 1
  - Requirements: [1.1](requirements.md#1.1), [1.2](requirements.md#1.2), [1.3](requirements.md#1.3), [1.4](requirements.md#1.4), [1.5](requirements.md#1.5), [1.6](requirements.md#1.6), [1.7](requirements.md#1.7), [1.8](requirements.md#1.8)

- [ ] 4. Write failing auto-fix and safety-guard tests <!-- id:a3keeu1 -->
  - SJ-REF-002 preconditions: single-segment folder-relative ref with exactly one basename candidate; cross-folder path or two candidates -> demoted: true, no write
  - SJ-TASK-002 minting is purely additive; fixed file round-trips rune list when rune present (skip otherwise)
  - Fix ordering REF-002 before TASK-002; idempotence: --fix then re-run gives zero findings for fixed items and byte-identical tree
  - Dirty specs/ tree and non-git directory refuse --fix (report still produced); --fix-dirty proceeds; without --fix no writes ever
  - Blocked-by: a3keeu0 (Implement spec_lint.py detection to pass the tests)
  - Stream: 1
  - Requirements: [3.2](requirements.md#3.2), [3.3](requirements.md#3.3), [3.4](requirements.md#3.4), [4.1](requirements.md#4.1), [4.2](requirements.md#4.2), [4.3](requirements.md#4.3)

- [ ] 5. Implement the --fix pipeline to pass the tests <!-- id:a3keeu2 -->
  - Snapshot detection, compute fixes, apply in one pass; mid-apply failure aborts remainder and reports which applied
  - Applied fixes listed in report and marked fix_applied in JSON
  - Blocked-by: a3keeu1 (Write failing auto-fix and safety-guard tests)
  - Stream: 1
  - Requirements: [3.1](requirements.md#3.1), [3.2](requirements.md#3.2), [3.3](requirements.md#3.3), [3.4](requirements.md#3.4), [4.1](requirements.md#4.1), [4.2](requirements.md#4.2), [4.3](requirements.md#4.3)

- [ ] 6. Write failing exclusion-store tests <!-- id:a3keeu3 -->
  - exclude and mark-raised subcommands are the only writers; schema-validated on write
  - Corrupt store -> backed up to .janitor.json.bak-<date> and rebuilt, reported prominently; never silently dropped
  - Identity stability: excluded finding keeps matching after line insertions AND after inserting a new task above the subject (slug subjects, not numbers)
  - Excluded specs skipped and listed in report; raised entries suppress SJ-DRIFT-001 re-raising
  - Blocked-by: a3keeu0 (Implement spec_lint.py detection to pass the tests)
  - Stream: 1
  - Requirements: [5.1](requirements.md#5.1), [5.3](requirements.md#5.3), [5.4](requirements.md#5.4), [5.6](requirements.md#5.6)

- [ ] 7. Implement store subcommands and exclusion filtering <!-- id:a3keeu4 -->
  - specs/.janitor.json: version, exclude_specs (repo-relative paths), exclude_findings, raised, last_run
  - Blocked-by: a3keeu3 (Write failing exclusion-store tests)
  - Stream: 1
  - Requirements: [5.1](requirements.md#5.1), [5.2](requirements.md#5.2), [5.3](requirements.md#5.3), [5.4](requirements.md#5.4), [5.6](requirements.md#5.6)

- [ ] 8. Add the bidirectional rule-ID parity test <!-- id:a3keeu5 -->
  - Every rule ID emitted by spec_lint.py exists in spec-conventions.md; every mechanical rule in the doc has a detector
  - Parses both artifacts; fails on drift in either direction
  - Blocked-by: a3keeu0 (Implement spec_lint.py detection to pass the tests)
  - Stream: 1
  - Requirements: [7.2](requirements.md#7.2)

## Skill and Guardrails

- [ ] 9. Author SKILL.md for /spec-janitor <!-- id:a3keeu6 -->
  - claude/skills/spec-janitor/SKILL.md implementing the 8-step workflow from the design
  - Interactive-entry contract stated: no router dispatches it autonomously; cloud surface uses the report-only agent asset
  - Judgment rules SJ-SUP/SCOPE/GHOST/FLOW/FILE/DRIFT with the finding model (per-family subjects, canonical pair ordering, related_spec/active/pattern/proposal fields)
  - Recency scan via git log since last_run (45-day default constant); triage batches by rule family, largest active cluster first; decline -> exclusion via the exclude subcommand with user-chosen granularity
  - Dirty-tree override offered via AskUserQuestion; moves rewrite inbound refs within specs/ in the same batch; supersession annotated both directions; index created/regenerated via /specs-overview
  - Blocked-by: a3keety (Author the conventions reference with stable rule IDs)
  - Stream: 3
  - Requirements: [2.1](requirements.md#2.1), [2.2](requirements.md#2.2), [2.3](requirements.md#2.3), [2.4](requirements.md#2.4), [2.5](requirements.md#2.5), [2.6](requirements.md#2.6), [3.4](requirements.md#3.4), [3.5](requirements.md#3.5), [3.6](requirements.md#3.6), [4.2](requirements.md#4.2), [5.1](requirements.md#5.1), [5.2](requirements.md#5.2), [6.1](requirements.md#6.1), [6.2](requirements.md#6.2), [6.3](requirements.md#6.3), [9.1](requirements.md#9.1)

- [ ] 10. Author the report-only copilot agent asset <!-- id:a3keeu7 -->
  - copilot/agents/spec-janitor.agent.md: runs python3 .github/skills/spec-janitor/spec_lint.py . (no --fix, no --json, no subcommands) and includes the report in its output
  - States exit 1 = findings, not failure; contains no write path
  - Blocked-by: a3keety (Author the conventions reference with stable rule IDs)
  - Stream: 3
  - Requirements: [9.2](requirements.md#9.2)

- [ ] 11. Apply prevention guardrail edits to the six skills <!-- id:a3keeu8 -->
  - engage: PRD-lane task references anchor prd.md sections, never a nonexistent requirements.md
  - starwave-smolspec: direction-changing revision passes mark discarded sections superseded in the same edit, citing SJ-SUP-*
  - starwave-tasks: task list scope matches source document; appended tasks carry the same schema as existing ones
  - fix-bug: bugfixes/ entries follow the report shape; non-bug work goes to a regular spec via smolspec
  - next-task + make-it-so: shared paragraph on mid-implementation spec edits following the conventions reference (nextup deliberately excluded — pure router)
  - Blocked-by: a3keety (Author the conventions reference with stable rule IDs)
  - Stream: 3
  - Requirements: [8.1](requirements.md#8.1), [8.2](requirements.md#8.2), [8.3](requirements.md#8.3), [8.4](requirements.md#8.4), [8.5](requirements.md#8.5)

## Distribution

- [x] 12. Write failing seed_verbatim tests <!-- id:a3keeu9 -->
  - tests/test_align.py additions with hermetic fixtures; existing tests unmodified
  - Cases: destination missing -> copy; identical -> no-op/unchanged; differing -> backup .bak-<date> and re-copy reported as changed
  - Pins that markerless existing janitor targets are NOT skipped as hand-written (the managed-block skip must not apply to verbatim-class seeds)
  - Stream: 2
  - Requirements: [9.3](requirements.md#9.3)

- [x] 13. Implement agentic_lib.seed_verbatim <!-- id:a3keeua -->
  - scripts/agentic_lib.py; reuses the existing _backup convention and ReportEntry reporting
  - Blocked-by: a3keeu9 (Write failing seed_verbatim tests)
  - Stream: 2
  - Requirements: [9.3](requirements.md#9.3)

- [x] 14. Write failing align seeding-integration tests <!-- id:a3keeub -->
  - Seeding pairs: claude/skills/spec-janitor/** -> .github/skills/spec-janitor/** (verbatim class), copilot/agents/spec-janitor.agent.md -> .github/agents/spec-janitor.agent.md
  - Stale-pack prune exempts .github/agents/spec-janitor.agent.md via SEEDED_AGENT_RELS with no zero-matches warning
  - Second aligned run reports no changes
  - Blocked-by: a3keeua (Implement agentic_lib.seed_verbatim)
  - Stream: 2
  - Requirements: [9.3](requirements.md#9.3), [9.4](requirements.md#9.4)

- [x] 15. Implement align.py seeding and prune-exemption changes <!-- id:a3keeuc -->
  - Generalize PRD_AGENT_REL to a SEEDED_AGENT_RELS set; add janitor pairs to the cloud-seeding step with the verbatim class
  - cloud_assets: true repos only, matching the prd pattern
  - Blocked-by: a3keeub (Write failing align seeding-integration tests)
  - Stream: 2
  - Requirements: [9.3](requirements.md#9.3), [9.4](requirements.md#9.4)

- [ ] 16. Add the VS Code agent symlink to sync-claude.sh with test <!-- id:a3keeud -->
  - One symlink line for copilot/agents/spec-janitor.agent.md into the VS Code prompts dir, same pattern as prd.agent.md
  - tests/test_sync_compat.py addition pinning the new symlink target
  - Blocked-by: a3keeu7 (Author the report-only copilot agent asset)
  - Stream: 2
  - Requirements: [9.1](requirements.md#9.1)

## Integration

- [ ] 17. End-to-end verification and self-audit smoke run <!-- id:a3keeue -->
  - make test and make lint pass
  - Smoke: run spec_lint.py against this repo's own specs/ in report-only mode; findings triaged, fallout fixed
  - Verify rune list parses every task file this feature touched
  - Blocked-by: a3keeu2 (Implement the --fix pipeline to pass the tests), a3keeu4 (Implement store subcommands and exclusion filtering), a3keeu5 (Add the bidirectional rule-ID parity test), a3keeu6 (Author SKILL.md for /spec-janitor), a3keeu8 (Apply prevention guardrail edits to the six skills), a3keeuc (Implement align.py seeding and prune-exemption changes), a3keeud (Add the VS Code agent symlink to sync-claude.sh with test)
  - Stream: 1
  - Requirements: [4.1](requirements.md#4.1)

- [ ] 18. Update workflow documentation and agent notes <!-- id:a3keeuf -->
  - spec-workflow.md: janitor section (when to run it, surface capability matrix)
  - docs/agent-notes/spec-janitor.md: architecture, disposition table location, verbatim seeding class, store contract
  - Blocked-by: a3keeue (End-to-end verification and self-audit smoke run)
  - Stream: 1
