# Nextup Pure Router

## Overview

The `/nextup` skill has grown into a state-tracking workflow: it maintains a "machine zone" in `nextup.md` (feature, stage, progress checkboxes, dated notes) that duplicates what `specs/`, rune task lists, and `docs/agent-notes/` already record. This change strips `/nextup` down to a pure router — read the user's intent, pick the lane and skill, dispatch — and removes machine-zone maintenance from the whole toolchain. Spec documents, task lists, and agent notes become the sole record of progress and context.

**Supersedes**: this spec reverses the machine-zone status tracking introduced by [`nextup-starwave-refinement`](../nextup-starwave-refinement/prd.md) — specifically its "Process status" machine-zone parsing plus the `machine-zone`/`stale-nextup` drift flags and columns in `scripts/process_status.py`, and the machine-zone content of the align nextup-template convergence (the `<!-- LM -->` marker and align.py convergence machinery survive; only the zone's template content becomes an inert marker line). Those portions of `nextup-starwave-refinement` are superseded by this spec.

## Requirements

- The nextup skill MUST route user intent to a lane and skill (or execute direct instructions) without maintaining any status record of its own — no stage lines, progress checkboxes, or dated session notes.
- `nextup.md` MUST be treated as a user-intent file only: nextup MUST NOT modify an existing `nextup.md` (seeding a missing one verbatim from `nextup.example.md` is still allowed) and MUST NOT read anything below the first recognised machine marker (`<!-- LM -->`; legacy `<!-- ML -->`, `<!-- nextup:machine -->`, `# What I want`) as state.
- Feature detection MUST rely only on explicit user references, the git branch, and the contents of `specs/` folders — no machine-zone fallback.
- Everything the machine zone used to carry MUST move in-chat or to existing artifacts: fan-out outcomes and interrupt/pause handoffs are reported in the session's plain-English closing message; gated jobs that cannot be dispatched are restated to the user there too; loose ends at close-out become rune tasks when the feature has a tasks file, otherwise they are listed in the closing message.
- Close-out mode MUST shrink to the bookkeeping sweep — rune tasks for loose ends, adjudicated decisions into the feature's `decision_log.md`, `/specs-overview` regeneration — with no `nextup.md` writes; `specs/OVERVIEW.md` plus the closing message replace the machine zone as the at-a-glance status.
- After a `/sendit` review handoff, a subsequent `/nextup` run whose user zone carries no change requests MUST count as approval of the documents that were sent; no stored review state is kept.
- Skills and scripts that read or write the machine zone MUST stop: `sendit` (writes it), `make-it-so` and `next-task` (feature fallback), the `/sendit` gate boilerplate in the four starwave skills, and `scripts/process_status.py` MUST drop machine-zone parsing together with its `machine-zone` and `stale-nextup` drift flags and columns.
- `nextup.example.md` MUST keep the `<!-- LM -->` marker so `scripts/align.py` convergence keeps working, but SHOULD carry only a one-line inert note below it instead of the status template.
- The routing lanes (direct, light, PRD, gated spec), job splitting/fan-out, and the `act autonomously` flag MUST keep their routing semantics; only their machine-zone touchpoints change as above.

## Implementation Approach

`~/.claude/skills` is a symlink to `claude/skills/` (`scripts/sync-claude.sh`), so skill edits deploy immediately.

- `claude/skills/nextup/SKILL.md` — rewrite as a router (target under 120 lines, currently 179): keep the user-zone contract, seeding, feature detection (minus machine-zone fallback), lane selection, dispatch rules, fan-out, autonomy flag, and the slimmed close-out sweep. Drop the machine-zone template, step 5 ("Update the machine zone"), machine-zone hard rules, and the "keeps a plain-English progress record" claim in the frontmatter description. The worktree rule shrinks to: read the main worktree's `nextup.md` user zone for intent.
- `nextup.example.md` — user-zone placeholder plus bare `<!-- LM -->` marker with a single inert line (e.g. "reserved marker for tooling — no session status is kept here").
- `claude/skills/sendit/SKILL.md` — remove step 3 (machine-notes update), the machine-zone feature-resolution entry, and the frontmatter mention of nextup machine notes; close-out becomes "copy to Prism, report loose ends in the closing message, stop".
- `claude/skills/make-it-so/SKILL.md:13`, `claude/skills/next-task/SKILL.md:13` — drop the machine-zone fallback; ambiguity already falls back to listing candidates and asking.
- `claude/skills/starwave-requirements/SKILL.md:81`, `starwave-design/SKILL.md:104`, `starwave-tasks/SKILL.md:167`, `starwave-smolspec/SKILL.md:171,195` — reword the `/sendit` gate boilerplate to drop "updates the nextup machine notes".
- `scripts/process_status.py` — remove `_machine_zone()` (lines 128-158), the marker table and note regex (lines 70-80), the zone/newest-note columns, and the `machine-zone`/`stale-nextup` flags (lines 233-236); keep nextup.md/nextup.example.md presence, `spec-gap`, `no-agentic-json`. Update `tests/test_process_status.py` expectations in step.
- `scripts/README.md:118-131`, `docs/runbooks/process-onboarding.md:58-62`, `docs/agent-notes/process-status.md`, `docs/agent-notes/align-tooling.md` (machine-zone framing only — align behaviour is unchanged) — update prose to the new contract.
- Root `nextup.md` (session-local, gitignored): trim its machine zone to the inert marker line.
- Pattern reference: the current contract was built by `specs/nextup-starwave-refinement/` (PRD lane); its `prd.md` documents the machine-zone convergence in `scripts/align.py`.

Out of scope:
- `scripts/align.py` and `tests/test_align.py` — untouched; convergence is keyed on the surviving `<!-- LM -->` marker and align tests assert against their own fixture canonical. Align distributes the slimmed template downstream automatically.
- `~/repos/sdd-ui` — direction context only, no changes there.
- Deleting `nextup.md`/`nextup.example.md` or the `<!-- LM -->` marker outright; changing any lane or skill routing semantics.

## Risks and Assumptions

- Risk: without the machine-zone fallback, `make-it-so`/`next-task` lose one disambiguation source | Mitigation: both already list candidates and ask the user; that stays.
- Risk: treating a change-request-free `/nextup` run as approval after `/sendit` may advance an unreviewed spec | Mitigation: `/sendit`'s closing message already tells the user the docs are out for review; continuing is an explicit user action.
- Risk: `tests/test_process_status.py` may pin column layouts and flags beyond the removed ones | Mitigation: run the test suite (`make test` or `python -m pytest tests/test_process_status.py`) after the change; only machine-zone assertions should need updating.
- Assumption: stale machine zones in downstream repos are harmless — the reworked skill ignores everything below the marker, and align converges the template's zone to the inert note on its next run.
- Assumption: after removing `process_status.py`'s machine-zone parsing, no other code parses machine-zone fields (verified by grep across scripts/, tests/, docs/; remaining hits are prose updated by this change).
- Prerequisite: none — all affected files exist in this repo.
