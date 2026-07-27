# Transit Integration

> **Status: not in use on this branch (as of 2026-07-27).** The Transit skill and
> the ticket-tracking instructions were removed from the workflow skills and from
> `shared/conventions.md` — the overhead was not justified while no `T-<id>`
> tickets are being raised. Transit is expected to return; this note is kept as
> the blueprint for re-enabling it. The MCP server definition in
> `mcp/servers.json` and the optional `transit_project` field in `.agentic.json`
> were deliberately left in place, so restoring the integration means re-adding
> the skill and the convention text, not rebuilding the plumbing.
>
> Still Transit-coupled and therefore dormant: `claude/skills/bug-blitz/` and
> `claude/skills/blitz-merge/`, which source their bug list from Transit.
> `/nextup` no longer routes to them.
>
> Note: the `/engage` rows in the tables below are obsolete regardless of
> Transit. That skill was deleted outright when the PRD lane was cut back to
> standalone authoring; it is not coming back with Transit.

Transit is the project tracker, accessed over its MCP server. Tickets use the
`T-<id>` format (e.g. T-42); the numeric part is the `displayId` used by the MCP
tools. Transit tracks **projects** — one per repository (see Cross-repo linking).

Board columns: **Idea, Planning, Spec, In Progress, Done/Abandoned**. The full
status flow is `idea → planning → spec → ready-for-implementation → in-progress →
ready-for-review → done` / `abandoned`. The two `ready-*` statuses are
agent-handoff statuses rendered inside the Spec and In Progress columns — they mark
where an agent has finished its stage and a human (or the next skill) picks up.

Every status change MUST carry a comment saying why (convention in
`shared/conventions.md`, generated into every repo's instructions).

## Lifecycle table

How each Transit status maps onto the SDD workflow, the skill that drives that
stage, and what triggers the transition INTO the status.

| Status (column) | Workflow stage | Driving skill(s) | Transition trigger |
|---|---|---|---|
| `idea` (Idea) | Captured, not yet scoped | `/nextup` (session entry), `/code-audit` (creates tickets from findings), manual creation | Ticket created |
| `planning` (Planning) | Scoping: full spec vs smolspec vs PRD | `/transit` (routes by type), `/starwave:creating-spec` (scope assessment), `/starwave:smolspec` | Scoping/authoring work starts on the ticket |
| `spec` (Spec) | Spec authoring: requirements → design → tasks, with approval gates and `/sendit` round-trips to Prism | `/starwave:requirements`, `/starwave:design`, `/starwave:tasks`, `/sendit` | `/starwave:creating-spec` moves it after scope assessment approval |
| `ready-for-implementation` (Spec) | Spec approved, branch created, awaiting implementation | `/starwave:creating-spec` Phase 5 | Tasks approved + feature branch created (end of Phase 5) |
| `in-progress` (In Progress) | Implementation | `/next-task`, `/make-it-so`; `/fix-bug` sets it too (after branch creation); `/engage` sets it on PRD execution start | Implementation begins |
| `ready-for-review` (In Progress) | Code complete, review/merge pending | `/fix-bug` (workflow completion, PR created), `/pre-push-review`, `/pr-pilot`; `/engage` on run completion | All checks pass and a PR / review handoff exists |
| `done` (Done) | Merged | `/blitz-merge`, `/pr-pilot` (after squash-merge) | PR merged. Autonomous runs never set `done` on their own initiative — a merge or a human closes |
| `abandoned` (Done/Abandoned) | Dropped | — (manual only) | Human decision; no skill sets this |

### PRD lane (ungated)

The PRD lane skips the spec gates, so its tickets skip the `spec` and
`ready-for-implementation` statuses:

| Status | Workflow stage | Driving skill | Transition trigger |
|---|---|---|---|
| `planning` | PRD authoring | `/prd` | Authoring starts (only status the prd skill sets) |
| `in-progress` | Autonomous execution in parallel worktrees | `/engage` | Execution starts |
| `ready-for-review` | Integrated, gates run, report delivered | `/engage` | Run completes (including blocked-at-STOP outcomes, noted in the comment) |

Autonomous runs (engage, headless or not) never set `done` — a human closes the
ticket after reviewing the merged work.

## Cross-repo linking

- **One Transit project per repository.** The project name defaults to the
  repository name; a repo overrides it with the optional `transit_project`
  (string) field in its `.agentic.json` (e.g. this repo sets
  `"transit_project": "agentic-coding"`). `scripts/align.py` never rewrites an
  existing manifest, so the field survives align runs (pinned in
  `tests/test_align.py::ManifestPreservationTest`).
- **Branch convention**: `T-{id}/{name}` — ticket reference first, e.g.
  `T-42/feature-name`, `T-42/bugfix-crash-on-save`. Used by
  `/starwave:creating-spec` (Phase 5) and `/fix-bug` as the recommended default
  when a ticket is tracked.
- **Commit prefix extraction**: the `/commit` skill extracts the ticket number
  from the branch name (its pattern accepts 1-5 letter prefixes, so `T-42`
  matches) and uses it as the commit-message prefix.

## Opt-in rule

Transit integration is opt-in at two levels. A skill skips ALL Transit steps
when no `T-<id>` ticket was mentioned AND the repo's `.agentic.json` has no
`transit_project`. The `/transit` router skill only dispatches; the target
skill owns the status transitions from that point.

## What runs where

- The MCP server is built into the Transit macOS app: `http://127.0.0.1:3141/mcp`,
  opt-in via the app's Settings. Setup and smoke test: `docs/runbooks/transit-mcp.md`.
- Surfaces are `claude` and `vscode` only (`mcp/servers.json`); the server is
  localhost-only, so the cloud coding agent can never reach it — cloud-seeded
  assets (`.github/`, including the copilot prd agent) carry no Transit
  instructions.
- Claude-side tool names (`mcp__transit__query_tasks`,
  `mcp__transit__update_task_status`, `mcp__transit__create_task`) and the
  `/transit` router pointer live in `shared/claude-wrapper.md`; the tool-neutral
  conventions live in `shared/conventions.md`. Both flow into the generated
  instructions via `make generate` — never hand-edit `claude/CLAUDE.md` or
  `copilot/instructions/copilot-instructions.md`.

## Key design decisions

- Conventions restored via the generated-fragments architecture after commit
  a0aea2e dropped them from the (then hand-maintained) CLAUDE.md; see
  `specs/transit-workflow-integration/decision_log.md`.
- The router-only `/transit` skill keeps status ownership with the workflow
  skills, so a status always changes at the moment the work actually happens.
- Ticket-first branch names make commit-prefix extraction trivial.
