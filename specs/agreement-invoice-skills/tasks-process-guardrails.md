---
references:
    - prd.md
---
# Agreement/invoice authoring skills and process guardrails — Process guardrails

## Status

- [x] 1. Add rune-drift flag to scripts/process_status.py <!-- id:022nmxf -->
  - PRD Process guardrails Req 1: a repo whose specs/** task files (tasks.md or tasks-*.md) exist but fail rune list parsing gets a rune-drift flag on its row; per-spec detail lines name the failing file
  - Stays read-only against target repos (existing --no-optional-locks discipline); a missing rune binary degrades to a warning line, never a crash
  - Stream: 1

- [x] 2. Surface prd.md spec folders in status detail lines <!-- id:022nmxg -->
  - PRD Req 5: repo detail lines list spec folders containing prd.md so PRD-lane work is visible alongside starwave specs
  - make status run from this repo shows agreement-invoice-skills with prd.md in its detail line
  - Blocked-by: 022nmxf (Add rune-drift flag to scripts/process_status.py)
  - Stream: 1

- [x] 3. Add unittest coverage for rune-drift and prd.md visibility <!-- id:022nmxh -->
  - Fixture repo with a hand-written non-rune tasks.md is flagged rune-drift and names the failing file; a live rune-format file is not flagged
  - Follow the existing fixture pattern in tests/test_process_status.py; make test passes
  - Blocked-by: 022nmxf (Add rune-drift flag to scripts/process_status.py), 022nmxg (Surface prd.md spec folders in status detail lines)
  - Stream: 1

## Conventions

- [x] 4. Strengthen the task-management rule in shared/conventions.md and regenerate <!-- id:022nmxi -->
  - PRD Req 2: tasks are managed with the rune CLI; task files live under the feature's specs/ folder; committed feature work requires its spec documents (design or PRD, plus tasks) in specs/ first
  - Run make generate so claude/CLAUDE.md and copilot instructions carry the wording; make lint shows no drift
  - Stream: 2

## Bootstrap

- [x] 5. Ensure the rune binary is on PATH via bootstrap <!-- id:022nmxj -->
  - PRD Req 3: in scripts/bootstrap.sh or the Brewfile (whichever fits the existing structure), given ~/repos/rune exists, make which rune succeed (symlink or PATH entry)
  - Re-running bootstrap is idempotent
  - Stream: 3

## Docs

- [x] 6. Write runbook docs/runbooks/rune-usage.md <!-- id:022nmxk -->
  - PRD Req 4: when task files are created (starwave tasks phase, engage derivation), where they live, day-to-day commands (rune list/add/complete, status updates), what the rune-drift flag means and how to clear it
  - Commands run as written against a real task file, e.g. one under specs/agreement-invoice-skills/
  - Blocked-by: 022nmxf (Add rune-drift flag to scripts/process_status.py)
  - Stream: 1

## Human

- [ ] 7. STOP — review and push the resulting commits <!-- id:022nmxl -->
  - Human step from PRD Execution notes: the no-push-main hook stops agents; the operator reviews the commits on main and pushes
  - No implementation work depends on this - it is the resume point after the run
  - Blocked-by: 022nmxh (Add unittest coverage for rune-drift and prd.md visibility), 022nmxi (Strengthen the task-management rule in shared/conventions.md and regenerate), 022nmxj (Ensure the rune binary is on PATH via bootstrap), 022nmxk (Write runbook docs/runbooks/rune-usage.md)
  - Stream: 1
