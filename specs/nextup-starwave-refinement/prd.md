# PRD: Nextup/Starwave process refinement across consumer repos

## Product summary

The nextup/starwave process is owned by this repository (agentic-coding) and consumed by sibling repositories under `~/repos/`. A survey on 2026-07-10 of six consumers (medata, netmap, tocs, rtob, localml, loshop) showed adoption is uneven: medata and rtob are fully wired (`.agentic.json`, maintained nextup machine zones, complete specs), while netmap, tocs, localml and loshop lack `.agentic.json`; no consumer repo has `nextup.example.md`, so hand-created `nextup.md` files drift (netmap and loshop hold stubs with no machine zone); and there is no way to see process health across repos without opening each one.

This PRD refines how the process is distributed and observed. It extends the align pipeline (`scripts/align.py`) to seed and converge the nextup template, adds a read-only cross-repo process status report, documents onboarding, and rolls the improved align out to the six consumer repos. The target repository is `/Users/r/repos/agentic-coding`; consumer repos are modified only by running this repo's align tool against them.

## Goals

- Every consumer repo can be brought onto the process with one `align` run: `.agentic.json`, `nextup.example.md`, and a `nextup.md` gitignore entry all converge from canonical sources here.
- A single command reports process health (nextup state, manifest presence, spec completeness, git state) across all participating repos.
- Onboarding a new repo to the process is documented as a runbook.
- The six surveyed repos are aligned to the refined process, without touching in-flight work.

## Non-goals

- No changes to the routing or gating semantics of the nextup/starwave skills (`claude/skills/*/SKILL.md` logic stays as is).
- No completion of consumer repos' in-flight work (loshop's missing `design.md`/`tasks.md`, netmap's UI idea, tocs's pending review). Per-repo feature work needs its own spec or PRD in that repo.
- No standardisation of `CLAUDE.md`, `docs/agent-notes/`, or `.claude/` permissions across consumer repos.
- No changes to `cloud_assets` behaviour or `.github/` seeding.
- No `git push` in any repository — the no-push-main hook and the human owner control pushes.

## Align tooling

Covers `scripts/align.py`, its fixtures, and the unittest suite. Align currently runs a 5-step pipeline (JSON validity, path portability, MCP convergence, stale-pack deletion, cloud seeding) driven by a read-only `.agentic.json` manifest; first run without `--yes` is plan-only against a shadow copy.

1. Align MUST seed `nextup.example.md` into the target repo root when it is absent, copied from this repo's canonical `nextup.example.md`.
   - Acceptance: running align (apply mode) against a fixture repo without the file creates it byte-identical to the canonical copy; a second run reports no pending changes.
2. When the target repo already has a `nextup.example.md`, align MUST converge only the machine zone (everything from the first `<!-- LM -->` marker down) to the canonical template and MUST preserve the target's user zone (everything above the marker) byte-for-byte.
   - Acceptance: a fixture `nextup.example.md` with a customised user zone and a stale machine zone ends with the original user zone and the canonical machine zone.
   - Acceptance: a target file already matching canonical produces no reported change.
3. When align seeds or converges `nextup.example.md`, it MUST ensure the target repo's `.gitignore` contains a `nextup.md` entry, appending one if missing (creating `.gitignore` if absent).
   - Acceptance: a fixture repo without the entry gains exactly one `nextup.md` line; a repo that already ignores it is unchanged.
4. Align MUST NOT create, modify, or delete `nextup.md` in the target repo — it is session-local.
   - Acceptance: a fixture repo containing a `nextup.md` ends the run with that file bit-identical.
5. The new behaviour MUST follow the existing plan-only contract: without `--yes` on a repo with an existing manifest, pending nextup-template fixes are reported but not applied.
   - Acceptance: plan-only run lists the pending seed/convergence; the filesystem is unchanged apart from first-run `.agentic.json` creation.
6. The unittest suite MUST cover the new pipeline step with fixtures for each acceptance case above.
   - Acceptance: `make test` passes; removing the new step makes at least one new test fail.

## Process status

A new read-only report over participating repos. Lives in `scripts/` alongside align, exposed as a Makefile target.

1. The repo MUST provide `make status` (wrapping a new `scripts/` Python script) that accepts one or more repo paths as arguments and defaults to this repo plus the repos listed in a checked-in default list containing medata, netmap, tocs, rtob, localml and loshop.
   - Acceptance: `make status` with no arguments prints one summary row per default repo; passing explicit paths reports only those.
2. Per repo, the report MUST show: `nextup.md` presence and whether its machine zone (`<!-- LM -->` marker, or legacy `<!-- ML -->`/`<!-- nextup:machine -->`/`# What I want` equivalents) is present and the date of its newest note; `nextup.example.md` presence; `.agentic.json` presence; each `specs/` subfolder with which of `requirements.md`/`design.md`/`tasks.md`/`smolspec.md`/`prd.md` it contains; current branch; dirty/clean working tree; date of last commit.
   - Acceptance: run against a fixture repo with known contents, every column matches the fixture.
3. The report MUST flag drift conditions on the row: nextup machine zone missing or malformed; newest nextup note older than 14 days while the working tree is dirty; a spec folder with `requirements.md` but neither `design.md` nor `tasks.md`; missing `.agentic.json`.
   - Acceptance: fixtures for each condition produce that flag and only that flag.
4. The status command MUST be read-only against target repos.
   - Acceptance: target fixture directory trees are bit-identical before and after a run.
5. The unittest suite MUST cover the report with fixture repos.
   - Acceptance: `make test` passes with the new tests included.

## Documentation

Covers `docs/runbooks/` and `docs/agent-notes/` in this repo.

1. The repo MUST gain `docs/runbooks/process-onboarding.md` describing how a repo joins the process: run align from agentic-coding (plan-only first run, then `--yes`), what gets seeded (`.agentic.json`, `nextup.example.md`, gitignore entry, MCP config), how the first `/nextup` session seeds `nextup.md`, and a one-paragraph map of the lanes (direct, light, PRD, gated starwave). Keep it generic — no per-repo state snapshots.
   - Acceptance: the runbook exists, mentions plan-only vs `--yes`, and names every seeded artifact.
2. `docs/agent-notes/align-tooling.md` MUST be updated to describe the nextup-template pipeline step and its user-zone-preservation rule.
   - Acceptance: the note describes the new step and why `nextup.md` itself is never touched.

## Rollout

Applies the refined align to the six consumer repos. Runs from this repo; consumer repos are modified only via `scripts/align.py` and `git commit` inside them.

1. Rollout MUST run align in plan-only mode first against each of `/Users/r/repos/{medata,netmap,tocs,rtob,localml,loshop}` and record the pending changes per repo.
   - Acceptance: the run summary lists per-repo planned changes before any apply.
2. Rollout MUST apply align (`--yes`) only to repos whose working tree is clean at execution time; dirty repos get plan-only and are listed as skipped with the reason.
   - Acceptance: no repo that was dirty before the run has any working-tree change afterwards.
3. In each applied repo, rollout MUST commit the align-produced changes on the repo's current branch with subject `[chore]: align nextup/starwave process assets`, and MUST NOT push.
   - Acceptance: `git log -1` in each applied repo shows the commit; `git status` is clean; no remote refs changed.
4. Rollout MUST finish by running the new status command across all six repos plus this one and including its output in the final report.
   - Acceptance: the final report contains one row per repo with the drift flags remaining after rollout.

## Execution notes

- Quality gates: `make test` (Python unittest) and `make lint` (shellcheck + generated-file drift check) in this repo. Run both before finishing any context.
- Ordering: "Align tooling" and "Process status" are independent and can run in parallel. "Documentation" depends on "Align tooling" (it documents the new step). "Rollout" runs last and depends on both "Align tooling" and "Process status".
- Rollout mutates sibling repositories outside any worktree isolation — it must run serially, one repo at a time, and only via `scripts/align.py` plus a single `git commit` per repo. Never `git push` anywhere.
- The canonical `nextup.example.md` machine-zone template is the source of truth for convergence; do not edit its wording as part of this work.
- STOP — after rollout, a human reviews the commits in the consumer repos and decides what to push; agents must not push (no-push-main hook applies).
