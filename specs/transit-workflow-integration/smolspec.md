# Smolspec: Transit Workflow Integration

## Overview

Restore the Transit conventions that commit a0aea2e dropped and document how Transit's
kanban lifecycle maps onto the full SDD workflow across all of the user's repos. Transit
tracks projects (one per repo); its board columns are Idea, Planning, Spec, In Progress,
Done/Abandoned, with agent-handoff statuses (`ready-for-implementation`,
`ready-for-review`) rendered inside the Spec / In Progress columns. The conventions must
come back through the generated-fragments architecture (`shared/` -> `make generate`),
not by hand-editing generated files.

## Requirements

1. `shared/conventions.md` MUST restore tool-neutral Transit conventions: `T-<id>`
   references are Transit tickets; every status change carries a comment saying why;
   each repo maps to one Transit project (default: repo name; override via
   `transit_project` in `.agentic.json`). No Claude-specific tool names.
2. `shared/claude-wrapper.md` MUST carry the Claude-side specifics: `mcp__transit__*`
   tool names and the `/transit` router skill pointer.
3. `claude/CLAUDE.md` and `copilot/instructions/copilot-instructions.md` MUST be
   regenerated via `make generate`; `make lint` (drift check) MUST pass.
4. `.agentic.json` MUST gain an optional `transit_project` (string) key; align MUST
   preserve it across runs (pinned by a test in `tests/test_align.py`); this repo's
   manifest MUST set `"transit_project": "agentic-coding"`.
5. `docs/agent-notes/transit-integration.md` MUST be rewritten as the cross-project
   integration reference: full lifecycle table (status -> workflow stage -> driving
   skill -> transition trigger, including the PRD lane), cross-repo linking rules,
   the opt-in rule, and what runs where.
6. The PRD lane MUST gain optional Transit hooks: `/prd` moves a ticket to `planning`
   on authoring start; `/engage` moves it to `in-progress` on execution start and
   `ready-for-review` on completion — always with comments, always skipped when no
   ticket applies, never setting `done` autonomously.
7. `docs/runbooks/transit-mcp.md` MUST be a numbered exact-values runbook for enabling
   and smoke-testing the Transit MCP server.
8. `spec-workflow.md` SHOULD point at the integration reference without duplicating it.
9. `CHANGELOG.md` MUST get one entry dated 2026-07-05.

## Implementation Approach

- `shared/conventions.md`: add the Transit bullets to Project Conventions (tool-neutral
  wording; the generate test forbids Claude-isms in the Copilot output).
- `shared/claude-wrapper.md`: new "Transit (Claude specifics)" section.
- `make generate` regenerates both outputs; markers preserved.
- `tests/test_align.py`: new test class proving `transit_project` in an existing
  `.agentic.json` survives an applying align run byte-for-byte.
- New/rewritten docs: `docs/agent-notes/transit-integration.md`,
  `docs/runbooks/transit-mcp.md`; short section in `spec-workflow.md`.
- Skill edits: `claude/skills/prd/SKILL.md` (inside the managed block, flush against
  markers per SeedSourceMarkerTests) and `claude/skills/engage/SKILL.md`. The condensed
  `copilot/agents/prd.agent.md` seed is NOT touched — it is seeded into `.github/` for
  the cloud agent, which cannot reach the localhost-only Transit MCP.

## Risks and Assumptions

- Risk: adding content to `claude/skills/prd/SKILL.md` breaks the managed-block normal
  form. Mitigated by SeedSourceMarkerTests in `make test`.
- Assumption: align.py's no-rewrite behavior for existing manifests is the intended
  preservation mechanism; the new test pins it against regressions.
- Assumption: Transit ticket types/statuses listed here match the current Transit
  corpus (idea, planning, spec, ready-for-implementation, in-progress,
  ready-for-review, done, abandoned).
