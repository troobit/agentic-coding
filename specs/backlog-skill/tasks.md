---
references:
    - specs/backlog-skill/requirements.md
    - specs/backlog-skill/design.md
    - specs/backlog-skill/decision_log.md
---
# backlog-skill Implementation Tasks

## Skill and Conventions

- [x] 1. Author claude/skills/backlog/SKILL.md <!-- id:dd74a8k -->
  - Six-step workflow per design: preflight parse gate (rune list; missing rune = no BACKLOG writes, no deletions), reconcile (spec folders authoritative, OVERVIEW.md a hint), gather (root nextup.md any tracked status user-zone-only; markers LM/ML/nextup:machine end the zone, USER belongs to it, none = whole file; exclude SPOUT.md, BACKLOG.md, OVERVIEW.md), route (task-file selection rule; per-item confirmation before requirement amendments; no anchor renumbering; staleness task), file (max-existing + 1), clear (per-source outcome listing always; tracked sources retained; one approval per run)
  - Embed the normative BACKLOG.md grammar: H1, phases Idea then Needs Spec always both present, one-line entries, detail line <source>, <YYYY-MM-DD> with arrow-spec suffix only on Needs Spec entries
  - Duplicate criterion is repo-realized (Decision 13); never run rune write commands on BACKLOG.md; never delete tracked files
  - Stream: 1
  - Requirements: [1.1](requirements.md#1.1), [1.2](requirements.md#1.2), [1.3](requirements.md#1.3), [1.4](requirements.md#1.4), [1.5](requirements.md#1.5), [2.1](requirements.md#2.1), [2.2](requirements.md#2.2), [2.3](requirements.md#2.3), [2.4](requirements.md#2.4), [2.5](requirements.md#2.5), [2.6](requirements.md#2.6), [3.1](requirements.md#3.1), [3.2](requirements.md#3.2), [3.3](requirements.md#3.3), [3.4](requirements.md#3.4), [3.6](requirements.md#3.6), [3.7](requirements.md#3.7), [4.1](requirements.md#4.1), [4.2](requirements.md#4.2), [4.3](requirements.md#4.3), [4.4](requirements.md#4.4), [4.5](requirements.md#4.5)

- [x] 2. decision_mode in generated conventions <!-- id:dd74a8l -->
  - Stream: 1
  - Requirements: [5.1](requirements.md#5.1), [5.2](requirements.md#5.2), [5.3](requirements.md#5.3), [5.4](requirements.md#5.4)
  - [x] 2.1. Update test_generate goldens to expect decision_mode rules in all three outputs (red) <!-- id:dd74a8m -->
    - Stream: 1
  - [x] 2.2. Add decision_mode rules to shared/conventions.md and the decision-log format reference; run make generate (green) <!-- id:dd74a8n -->
    - conventions.md Documentation Standards: read .agentic.json decision_mode before revising a decision; overwrite = edit in place same ID new date; supersede/absent = current behavior
    - decision-log-format.md gains a Revising a decision section covering both modes and the manifest read
    - Blocked-by: dd74a8m (Update test_generate goldens to expect decision_mode rules in all three outputs red)
    - Stream: 1

- [x] 3. Per-skill decision_mode edits in supersede-mandating skills <!-- id:dd74a8o -->
  - spec-janitor/SKILL.md:97 and spec-janitor/references/spec-conventions.md: audit must not flag overwrite-mode logs as drift; also reword its nextup mention
  - make-it-so/SKILL.md:91 and next-task/SKILL.md:33: mid-implementation edit clauses defer to the repo declared mode
  - One sentence each; behavior-scoped list per Decision 14
  - Blocked-by: dd74a8l (decision_mode in generated conventions)
  - Stream: 1
  - Requirements: [5.1](requirements.md#5.1), [5.3](requirements.md#5.3)

## Toolchain

- [x] 4. BACKLOG.md column and schema check in process_status.py <!-- id:dd74a8p -->
  - Stream: 2
  - Requirements: [3.1](requirements.md#3.1), [3.5](requirements.md#3.5), [6.3](requirements.md#6.3)
  - [x] 4.1. Write BACKLOG fixture tests in test_process_status.py; remove nextup-column assertions (red) <!-- id:dd74a8q -->
    - ok fixtures: absent (renders -), valid, empty-but-valid (both phases zero entries), gapped numbering, U+2192 arrow detail, trailing-whitespace heading
    - drift fixtures: rune-unparseable, wrong/extra/case-variant phase, checked entry, nested checked subtask (only Stats catches it), missing H1
    - Stream: 2
  - [x] 4.2. Implement _backlog_status hybrid check, column swap, backlog-drift flag, docstring and argparse rewrite (green) <!-- id:dd74a8r -->
    - Hybrid: _rune_parses gate, raw right-trimmed case-sensitive scan of H2 set/order == [Idea, Needs Spec], rune list --format json Stats.Pending == Stats.Total, raw H1 presence scan
    - Remove NEXTUP/EXAMPLE keys :118-119 assigns :131-132 header :188 _row :205-206 (presence-only, no drift wiring exists); add backlog-drift to drift_flags with reason detail line; rewrite module docstring :4-16 and argparse description :252
    - Detail-line grammar deliberately unchecked (design: out of AC 3.5 scope)
    - Blocked-by: dd74a8q (Write BACKLOG fixture tests in test_process_status.py; remove nextup-column assertions red)
    - Stream: 2

- [x] 5. Owned-symlink prune in sync-claude.sh <!-- id:dd74a8s -->
  - Stream: 2
  - Requirements: [6.4](requirements.md#6.4)
  - [x] 5.1. Write prune cases in test_sync_compat.py (red) <!-- id:dd74a8t -->
    - Stream: 2
  - [x] 5.2. Implement the prune loop in sync-claude.sh (green) <!-- id:dd74a8u -->
    - For each entry in ~/.agents/skills (nullglob): [ -L ] and literal target prefix $REPO_CLAUDE_DIR/skills/ and [ ! -e ] then rm; foreign links never touched; script only creates absolute links so literal prefix match suffices
    - Blocked-by: dd74a8t (Write prune cases in test_sync_compat.py red)
    - Stream: 2

- [x] 6. Remove align step 6 and the canonical template <!-- id:dd74a8v -->
  - Stream: 2
  - Requirements: [6.2](requirements.md#6.2)
  - [x] 6.1. Rewrite test_align.py: drop step-6 classes and all 8 nextup fixtures; add stray-template-untouched and no-gitignore-write tests (red) <!-- id:dd74a8w -->
    - Delete fixtures: nextup-{canonical,gitignore-append,gitignore-create,markerless,missing,plan-only,session-file,user-zone} plus their .gitignore files and seed-root/nextup.example.md
    - New tests: align leaves a stray nextup.example.md in a target untouched (stop-managing means no touch, not delete); align never writes .gitignore
    - Stream: 2
  - [x] 6.2. Delete align step-6 code and nextup.example.md in the same commit (green) <!-- id:dd74a8x -->
    - Delete: NEXTUP_EXAMPLE :90, NEXTUP_LM_MARKER :94, _ensure_nextup_gitignore :346, _converge_nextup_template :371, call :420, seed-root existence error :548, docstring managed-files entry :48; renumber remaining steps
    - _shadow_copy :443: NEXTUP_EXAMPLE and .gitignore both leave the tuple (gitignore management existed only for nextup)
    - Canonical nextup.example.md deleted in this same commit or align crashes on a seed root missing an expected file
    - Blocked-by: dd74a8w (Rewrite test_align.py: drop step-6 classes and all 8 nextup fixtures; add stray-template-untouched and no-gitignore-write tests red)
    - Stream: 2

## Sunset

- [x] 7. Sunset gate and removals <!-- id:dd74a8y -->
  - Stream: 1
  - Requirements: [6.1](requirements.md#6.1), [6.5](requirements.md#6.5), [6.6](requirements.md#6.6)
  - [x] 7.1. Write the tracked-files sunset grep test (red) <!-- id:dd74a8z -->
    - File set from git ls-files; case-insensitive nextup|spout; exempt specs/, CHANGELOG.md, and the test file itself; fails against current tree until 7.2
    - Stream: 1
  - [x] 7.2. Remove nextup and spout skill dirs, swap README registry, purge remaining tracked references (green) <!-- id:dd74a90 -->
    - Delete claude/skills/nextup and claude/skills/spout; README registry lists backlog in their place
    - Purge: .gitignore /nextup.md and /SPOUT.md entries plus comments; docs/agent-notes align-tooling, process-status, spec-janitor, transit-integration; docs/runbooks/process-onboarding.md now points at /backlog; scripts/README.md align steps and status columns; claude/uplift-candidates.md purge or delete
    - Ordering (AC 6.6): blocked by task 1 so the skill exists in the synced toolchain before the sunset lands
    - Blocked-by: dd74a8z (Write the tracked-files sunset grep test red), dd74a8k (Author claude/skills/backlog/SKILL.md), dd74a8r (Implement _backlog_status hybrid check, column swap, backlog-drift flag, docstring and argparse rewrite green), dd74a8x (Delete align step-6 code and nextup.example.md in the same commit green)
    - Stream: 1
