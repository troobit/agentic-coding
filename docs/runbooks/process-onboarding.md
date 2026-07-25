# Runbook: onboarding a repo to the nextup/starwave process

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
- `nextup.example.md` — the tracked session template, copied verbatim from
  this repo's canonical copy when absent. If the target already has one, only
  the part from the first `<!-- LM -->` marker down is converged to canonical
  (now just the marker plus an inert reserved-for-tooling line); the user
  zone above the marker is preserved byte-for-byte. A file without the
  marker is treated as hand-written and skipped, never overwritten.
- A `nextup.md` entry in the target's `.gitignore` (appended if missing,
  `.gitignore` created if absent). `nextup.md` itself is session-local and
  never created, modified, or deleted by align.
- MCP config — `.mcp.json` and `.vscode/mcp.json` converged to the manifest's
  server subset of the canonical `mcp/servers.json` (created if missing;
  non-canonical entries preserved).
- Optionally, when `cloud_assets` is `true` in the manifest: the `.github/`
  cloud assets (`copilot-instructions.md`, `agents/prd.agent.md`,
  `skills/prd/**`) as managed blocks.

## First session

`nextup.md` is not seeded by align — the first `/nextup` session in the target
repo does it. `/nextup` looks for `nextup.md` at the repo root and, finding
none, copies `nextup.example.md` into place and carries on. From then on the
user writes instructions in the user zone (above `<!-- LM -->`); `/nextup`
routes them and never writes the file. Below the marker sits only an inert
reserved-for-tooling line — no session status is kept there; progress lives
in `specs/` (see `specs/OVERVIEW.md`), rune task lists, and the session's
closing message. Because `nextup.md` is gitignored, each clone seeds its own
from the tracked template.

## The lanes

`/nextup` routes each session's intent down one of four lanes, preferring the
lightest that fits. The **direct** lane executes plain instructions inline,
exactly like any prompt — no spec folder. The **light** lane sends bounded
jobs to a focused skill (`/fix-bug`, `/starwave:smolspec`, and similar)
without requirements/design ceremony. The **PRD** lane runs a body of work
ungated to completion: `/prd` authors `specs/{name}/prd.md`, then `/engage`
executes it in parallel worktrees. The **gated starwave** lane is the
spec-driven chain (`/starwave:creating-spec` through requirements, design,
and tasks, each with an approval gate) recommended for substantial
feature-shaped work — a recommendation, never an enforcement.
