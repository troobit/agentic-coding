# Decision Log: Transit Workflow Integration

## Decision 1: Restore Transit conventions through the generated-fragments architecture

**Date**: 2026-07-05
**Status**: accepted

### Context

Commit a0aea2e dropped the two CLAUDE.md convention lines (`T-<id>` ticket references
and the status-comment rule) when CLAUDE.md was still hand-maintained. Since then the
toolset-agnostic-starwave work made `claude/CLAUDE.md` and
`copilot/instructions/copilot-instructions.md` generated outputs assembled from
`shared/` fragments, and the conventions test forbids Claude-only mechanisms in the
Copilot output.

### Decision

Restore the conventions split across the fragment boundary: tool-neutral rules
(`T-<id>` means a Transit ticket, status changes carry a comment, one Transit project
per repo with a `transit_project` manifest override) go in `shared/conventions.md`;
the Claude-side specifics (`mcp__transit__*` tool names, the `/transit` router
pointer) go in `shared/claude-wrapper.md`.

### Rationale

The conventions apply to any agent that can reach Transit's MCP server (Claude Code
and VS Code Copilot both can), so they belong in the shared fragment. The concrete
tool names are Claude's naming scheme and would leak Claude-isms into the Copilot
output, so they belong in the wrapper. `make generate` then propagates both correctly
and the drift check keeps them from being hand-edited out again.

### Alternatives Considered

- **Hand-edit claude/CLAUDE.md directly**: Restores the original lines verbatim -
  Rejected because the file is generated; `make lint`'s drift check would fail and
  the next `make generate` would erase the edit.
- **Put everything (including tool names) in conventions.md**: One fragment to
  maintain - Rejected because `test_real_copilot_output_has_no_claude_isms` exists
  precisely to keep Claude tool naming out of the Copilot output; the test now also
  forbids `mcp__` to enforce this.

### Consequences

**Positive:**
- Both generated outputs carry the Transit conventions; Copilot output stays
  tool-neutral.
- The drift check protects the conventions from being silently dropped again.

**Negative:**
- Copilot users get the convention ("query via its MCP server") without concrete
  tool names; VS Code's MCP client discovers them at runtime instead.

---

## Decision 2: transit_project as an optional manifest key, preserved by align's no-rewrite behavior

**Date**: 2026-07-05
**Status**: accepted

### Context

Each repo maps to one Transit project, defaulting to the repo name. Repos whose
Transit project name differs need an override, and the natural home is the
`.agentic.json` manifest that align already owns. align must not destroy the field
when it runs.

### Decision

Add optional `transit_project` (string) to the `.agentic.json` schema (documented in
`scripts/align.py`'s docstring). No code change to align: it only writes the manifest
on a first (inferring) run and treats an existing manifest as read-only, so unknown
and optional keys already survive. A new test
(`ManifestPreservationTest.test_transit_project_survives_applying_run`) pins that
behavior.

### Rationale

Inspection of `align.run` showed the manifest is written exactly once — when it does
not exist — and only read afterwards. Preservation therefore holds by construction;
the test converts that incidental property into a contract so a future refactor that
starts rewriting the manifest fails loudly.

### Alternatives Considered

- **Have _infer_manifest emit `transit_project` (repo name) on first run**: Makes the
  default explicit in every manifest - Rejected: the default is derivable (repo
  name), writing it everywhere is noise, and skills must handle the absent-key case
  anyway for existing manifests.
- **A separate config file (e.g. .transit.json)**: Keeps align out of the picture -
  Rejected: one more dotfile per repo for a single optional string; `.agentic.json`
  is already the per-repo agentic manifest.

### Consequences

**Positive:**
- Zero align code change; the preservation contract is now test-pinned.
- One manifest continues to describe a repo's agentic configuration.

**Negative:**
- The schema is enforced only by convention and docstring — align does not validate
  the field's type.

---

## Decision 3: PRD-lane Transit hooks — prd sets only `planning`; engage sets `in-progress` and `ready-for-review`, never `done`

**Date**: 2026-07-05
**Status**: accepted

### Context

The PRD lane (prd + engage) is the ungated autonomous route and previously had no
Transit integration. The gated lane's statuses include `spec` and
`ready-for-implementation`, but the PRD lane has no spec gate and no approval
checkpoints, so its tickets cannot follow the same path.

### Decision

`/prd` moves the ticket to `planning` with a comment when authoring starts and sets
nothing else. `/engage` moves it to `in-progress` on execution start and
`ready-for-review` on completion (comment includes blocked-at-STOP contexts).
Autonomous runs never set `done` — a human closes the ticket. All hooks are skipped
when no ticket applies, and only `claude/skills/prd/SKILL.md` (not the cloud-seeded
`copilot/agents/prd.agent.md`) carries them.

### Rationale

A PRD is a planning artifact, so authoring maps to `planning`; jumping the ticket to
`spec` would misrepresent the lane (there is no spec, and the Spec column's handoff
status `ready-for-implementation` implies an approval gate that never happens).
Execution and completion map cleanly onto `in-progress` and `ready-for-review`.
Stopping at `ready-for-review` keeps a human in the loop on ticket closure, matching
`/fix-bug`'s existing behavior and the rule that merge (blitz-merge/pr-pilot) or a
human sets `done`. The copilot prd agent is seeded into `.github/` for the cloud
agent, which cannot reach the localhost-only MCP server — Transit instructions there
would be dead weight that fails on every run.

### Alternatives Considered

- **prd also moves the ticket to `spec` when the document is confirmed**: Mirrors the
  gated lane - Rejected: the PRD lane skips the spec gate by design; a PRD is not a
  spec and `ready-for-implementation` would never follow, leaving tickets stranded
  mid-column.
- **engage sets `done` after a fully green integrated run**: Fewer manual steps -
  Rejected: an autonomous run marking its own work complete removes the only human
  checkpoint in the ungated lane; review happens after engage reports.
- **Hooks in the copilot/cloud prd agent too**: Parity across surfaces - Rejected:
  the cloud agent cannot reach `127.0.0.1:3141`; the instructions could only fail.

### Consequences

**Positive:**
- PRD-lane tickets are visible on the board through their whole life without
  fabricating gate statuses.
- Human closure is preserved in the ungated lane.

**Negative:**
- PRD-lane tickets never show in the Spec column, which reads as a gap unless you
  know the lane skips it (documented in the lifecycle table).
- `done` requires a manual step (or a later pr-pilot/blitz-merge run) even for
  perfect autonomous runs.

---

---

## Decision 4: Remove the Transit Workflow Layer, Keep the Plumbing

**Date**: 2026-07-27
**Status**: accepted

### Context

Decisions 1–3 wired Transit ticket tracking through the workflow: a `/transit`
routing skill, `T-<id>` status transitions inside `fix-bug`, `starwave-creating-spec`,
`pr-pilot`, `code-audit` and `prd`, and the `T-<id>` conventions in
`shared/conventions.md` and `shared/claude-wrapper.md` — the latter generated into
every repository's `CLAUDE.md` and Copilot instructions, so they loaded into every
session.

No `T-<id>` tickets are currently being raised. The instructions were therefore
consuming context in every session and constraining every workflow skill for a
tracker not in use. Transit is expected to return, so this is a suspension rather
than an abandonment.

### Decision

Remove the Transit **workflow layer** only: delete `claude/skills/transit/`, strip
the ticket-tracking steps from the five workflow skills, and remove the Transit
sections from `shared/conventions.md` and `shared/claude-wrapper.md` (regenerating
`claude/CLAUDE.md` and the Copilot instructions).

Deliberately **keep** the inert plumbing: the `transit` entry in `mcp/servers.json`
and the optional `transit_project` key in `.agentic.json`, along with
`docs/agent-notes/transit-integration.md` as the restoration blueprint.

`bug-blitz` and `blitz-merge` are left untouched with their Transit calls intact —
Transit is their bug *source*, not an optional tracker. They are dormant, and
`/nextup` no longer routes to them; a batch of bugs fans out as parallel
`/fix-bug` jobs instead.

### Rationale

The cost being removed is context and coupling, both of which live entirely in the
skill instructions and the generated convention text. The MCP server definition and
the manifest key cost nothing until enabled, and they are pinned by golden-file
tests in `test_generate.py` — removing them would mean churning those fixtures for
no benefit and more work to restore later.

Leaving the blitz skills intact rather than rewiring them to GitHub issues keeps
them faithful to the tracker they will use again, at the cost of two skills that
cannot run meanwhile. Routing was changed instead so `/nextup` never dispatches to
a skill that cannot execute.

### Alternatives Considered

- **Remove everything including `mcp/servers.json` and `.agentic.json` plumbing**: Complete removal - Rejected because it requires updating `test_generate.py`'s canonical server list and its golden JSON fixtures, and makes restoration harder, for no context saving
- **Delete only `claude/skills/transit/`**: Fastest - Rejected because the `T-<id>` conventions would keep loading into every session through the generated `CLAUDE.md`, which is the actual cost
- **Rewire `bug-blitz` / `blitz-merge` to GitHub issues**: Preserves the batch-fix capability now - Rejected on the user's call: Transit is returning, and rewiring then re-rewiring is churn
- **Delete `bug-blitz` / `blitz-merge`**: Consistent with removing Transit-dependent surface - Rejected for the same reason; they are dormant, not obsolete

### Consequences

**Positive:**
- Every session's `CLAUDE.md` drops the Transit conventions
- Five workflow skills lose their ticket-status branching and read more simply
- Restoring Transit means re-adding the skill and convention text, not rebuilding plumbing
- `/nextup` no longer routes to skills that cannot run

**Negative:**
- `bug-blitz` and `blitz-merge` are unreachable until Transit returns
- `docs/agent-notes/transit-integration.md` documents an integration that is not currently wired, and its `/engage` rows are permanently obsolete (that skill was deleted — see toolset-agnostic-starwave Decision 17)
- `mcp/servers.json` advertises a server the workflow no longer uses
- The removal is branch-local by intent; upstream retains the integration, so the two will diverge until Transit is restored

### Impact

`claude/skills/transit/` deleted. Transit steps removed from `fix-bug`,
`starwave-creating-spec`, `pr-pilot`, `code-audit`, `prd`. Transit sections removed
from `shared/conventions.md` and `shared/claude-wrapper.md`; `claude/CLAUDE.md` and
`copilot/instructions/copilot-instructions.md` regenerated. `transit` added to
`RETIRED_SKILLS` in `tests/test_sync_compat.py`. `nextup` light-lane routing
updated. Unchanged: `mcp/servers.json`, `.agentic.json`, `bug-blitz`,
`blitz-merge`, `test_generate.py`.

---
