# Runbook: onboarding a repo to the starwave process

How any repository under `~/repos/` joins the process owned by this repository
(agentic-coding). Everything is driven by `scripts/align.py` run from here —
the target repo is never edited by hand.

## Steps

1. Plan-only first run (run from this repository's root):

   ```sh
   python3 scripts/align.py <target-repo>
   ```

   The first run against a repo with no `.agentic.json` infers a manifest from
   the canonical `default_for` rules and writes it — that manifest is the only
   file changed. Every other fix is reported as a plan ("plan only - N pending
   change(s)") without being applied.

2. Review the created `.agentic.json` in the target repo: the `servers` list
   (canonical MCP server names), `cloud_assets` (inferred as `false` — seeding
   `.github/` cloud assets is an explicit opt-in edit), and the optional
   `transit_project` if the Transit project name differs from the repo name.
   Adjust and commit it.

3. Re-run align to apply. Once the manifest exists, a plain run applies
   directly; `--yes` is only needed to apply on the first (manifest-inferring)
   run:

   ```sh
   python3 scripts/align.py <target-repo>
   ```

   Re-running is always safe: a repo already in shape reports no pending
   changes.

## What gets seeded

- `.agentic.json` — the manifest (first run; read-only to align afterwards).
- MCP config — `.mcp.json` and `.vscode/mcp.json` converged to the manifest's
  server subset of the canonical `mcp/servers.json` (created if missing;
  non-canonical entries preserved).
- Optionally, when `cloud_assets` is `true` in the manifest: the `.github/`
  cloud assets (`copilot-instructions.md`, `agents/prd.agent.md`,
  `skills/prd/**`) as managed blocks.

Skills (`/backlog`, `/starwave:*`, and the rest) are distributed by the
symlink mechanism in `scripts/sync-claude.sh` / `scripts/bootstrap.sh`, not by
align — align's job is manifest, MCP config, and opt-in cloud assets only.

## First session

`/backlog` is the tracked entry point for forward intent in a newly onboarded
repo: bare invocation captures any loose `*.md` files at the repo root or
under `specs/` (outside a spec folder) into `specs/BACKLOG.md`, routing each
item to an existing spec or filing it as a backlog entry. There is no
session-status file to seed — progress lives in `specs/` (see
`specs/OVERVIEW.md`) and rune task lists.

## The lanes

Each session routes its intent to the lightest destination that fits. The
**direct** lane executes plain instructions inline, exactly like any prompt —
no spec folder. The **light** lane sends bounded jobs to a focused skill
(`/fix-bug`, `/starwave:smolspec`, and similar) without requirements/design
ceremony. **`/prd`** authors a standalone `specs/{name}/prd.md` for a small
project or first MVP and closes out there — authoring only, with no execution
step. The **gated starwave** lane is the spec-driven chain
(`/starwave:creating-spec` through requirements, design, and tasks, each with
an approval gate) recommended for substantial feature-shaped work — a
recommendation, never an enforcement. Loose intent that doesn't fit any of
these yet — a note, an idea, an audit finding — goes to `/backlog`.
