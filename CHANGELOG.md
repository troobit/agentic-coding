# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2026-08-26]

### Added
- **Codex support** through the generation toolchain: `codex/AGENTS.md` (generated from `shared/codex-wrapper.md`) distributes to `~/.codex/AGENTS.md` via `scripts/generate.py --user`, with Codex-specific skill guidance and communication conventions matching Claude and Copilot instructions
- **Agent Skills linking for Codex**: `scripts/sync-claude.sh` symlinks each top-level skill under `claude/skills/` individually into `~/.agents/skills` for Codex discovery, preserving existing user-installed skills and reporting conflicts
- **Codex MCP configuration**: `scripts/generate.py` writes Codex MCP settings to `~/.codex/config.toml` managed blocks; `scripts/align.py` converges per-repo `.codex/config.toml` MCP tables while preserving unrelated Codex settings
- **Bootstrap and sync updates**: `scripts/bootstrap.sh` now creates `~/.agents/skills` and `~/.codex` directories; sync-claude.sh updated to include Codex skill links; Makefile includes `codex/AGENTS.md` in generate and lint-drift checks

### Changed
- **README.md**: Expanded to document Codex integration, three-tool setup, Agent Skills discovery path, and the full suite of scripts supporting Claude/Copilot/Codex configuration
- **`docs/agent-notes/bootstrap-and-sync.md`**: Documented the Codex bootstrap sequence (mkdir targets, Codex skill links, AGENTS.md seeding, config.toml)

### Fixed
- **Test suite**: Added golden fixtures (`tests/fixtures/golden/AGENTS.md`, `tests/fixtures/golden/codex-mcp.toml`) and test cases for Codex AGENTS.md generation and `.codex/config.toml` alignment; updated `tests/test_sync_compat.py` for Codex skill symlink validation

## [2026-08-20]

### Added
- **Spout skill** (`/spout`): An orientation tool that reads the repo and reports a single `SPOUT.md` at the root, answering three questions — what state is every spec in, what are the discrete next steps with exact invocations and goals, and where new uncovered work belongs. Produces a person-readable document (prose, tables, lists) that serves as a summation before acting; runs read-only over the repo and never dispatches work itself. Operates outside the spec workflow but is aware of it, defaulting uncovered work to starwave when a spec is needed and naming exceptions explicitly. Can be scoped to a single spec or focused on a goal (`/spout "<intent>"`); chains `/explain-like` for ambiguities

### Changed
- **Language rules**: Added Python language rules documenting a gotcha with `@dataclass(frozen=True, slots=True)` and Svelte 5 language rules covering reactivity effects, SvelteKit server exports, and testing gotchas (CSS imports in jsdom, Web Storage on Node ≥22, effect compilation in node environment)
- **README.md**: Documented the spout skill under a new "Orientation Skill" section, clarifying that it sits alongside the spec workflow as a read-only guidance tool
- **.gitignore**: Added `SPOUT.md` as a generated scratch report (stale as soon as HEAD moves)

## [2026-07-27]

### Removed
- **`sendit` and `engage` skills deleted; `/prd` cut back to standalone authoring** (decision `toolset-agnostic-starwave` D17). The four starwave approval gates (requirements, design, tasks, smolspec) revert to plain approve-and-continue → design/tasks/make-it-so — the `/sendit` default-action lines were pure insertions, so removing them restores the prior flow exactly. `/prd` now authors `specs/{name}/prd.md` for a small project or first MVP and ends at the document: there is no PRD execution step, nothing derives a task file from a PRD, and `/nextup` does not route an existing `prd.md` onward. Work that must react to change or growing complexity goes through the starwave chain instead. The `act autonomously` flag now only suppresses starwave's gates and auto-dispatches `/make-it-so` on a complete spec. `nextup`, `prd`, `spec-janitor`, `README.md`, `spec-workflow.md`, and the runbooks updated to match
- **Transit workflow layer removed from this branch** (decision `transit-workflow-integration` D4). Deleted `claude/skills/transit/` and stripped ticket-tracking steps from `fix-bug`, `starwave-creating-spec`, `pr-pilot`, `code-audit`, and `prd`; removed the Transit sections from `shared/conventions.md` and `shared/claude-wrapper.md` so the `T-<id>` conventions no longer generate into every repo's `CLAUDE.md` and Copilot instructions. Inert plumbing deliberately kept: the `transit` entry in `mcp/servers.json`, `transit_project` in `.agentic.json`, and `docs/agent-notes/transit-integration.md` as the restoration blueprint. `bug-blitz` and `blitz-merge` are left intact but dormant — Transit is their bug *source* — and `/nextup`'s light lane now fans a batch of bugs out as parallel `/fix-bug` jobs rather than routing to them
- `tests/test_sync_compat.py`: `sendit` and `transit` moved out of the `PRE_FEATURE_SKILLS` baseline into a new `RETIRED_SKILLS` list, with a test asserting they are absent and that no skill is both retired and required — so the removals are an asserted expectation rather than a relaxed guardrail

## [2026-07-26]

### Fixed
- **Spec-janitor audit-and-repair pass** on this repo's `specs/` (the 14 findings the self-audit smoke run left for a gated session): 13 auto-fixes applied on a clean tree — 11 `SJ-REF-002` broken `references:` front-matter entries rewritten to repo-relative paths (across `agreement-invoice-skills`, `fiscal-probe-skill`, `nextup-starwave-refinement`, `toolset-agnostic-starwave`, `transit-workflow-integration`), and 2 `SJ-TASK-002` mixed-stable-ID files gaining minted IDs (`fiscal-probe-skill/tasks.md`, `toolset-agnostic-starwave/tasks.md`). Judgment audit surfaced one `SJ-SUP-001` gated finding: `nextup-pure-router` silently superseded the machine-zone status tracking built by `nextup-starwave-refinement`; annotated in both directions (neither deleted) and `specs/OVERVIEW.md` regenerated to record the link. The lone `SJ-TASK-001` (a plain-text requirement reference in `toolset-agnostic-starwave/tasks.md`) is detect-only and left as-is

### Added
- **Spec-janitor toolchain** (spec `spec-janitor`, implemented): `/spec-janitor` skill + stdlib auditor `claude/skills/spec-janitor/spec_lint.py` audit and repair diluted `specs/` directories. Mechanical audit (SJ-REF/TASK/MODE rules: dangling anchors, broken `references:` entries, mixed/missing stable IDs, out-of-sequence numbering, unrecognized spec modes, bugfix-shape violations) with document-based discovery (a folder owning a primary document is the spec; subfolders are assets), `--fix` limited to two deterministic-or-additive repairs with demotion on ambiguity, dirty-tree/non-git guards, and `exclude`/`mark-raised` subcommands as the only writers of the committed `specs/.janitor.json` exclusion store. Judgment audit + gated batch triage live in the skill; the normative `references/spec-conventions.md` carries stable rule IDs pinned to the auditor by a bidirectional parity test. Distribution: `seed_verbatim` class in `agentic_lib` (managed blocks are markdown-only) seeds the skill package and the report-only `spec-janitor.agent.md` to cloud repos via align (bytecode/dotfile pollution filtered, `SEEDED_AGENT_RELS` prune exemption, `.bak-` files exempt from stale-pack candidacy); `sync-claude.sh` symlinks the agent for VS Code. Prevention guardrails added to engage, starwave-smolspec, starwave-tasks, fix-bug, next-task, and make-it-so. 169 tests; self-audit smoke run on this repo surfaced 14 pre-existing findings (left for a gated janitor session)
- **Spec-janitor spec** (spec `spec-janitor`): full planning artifacts (requirements, design, 18-task plan, 12-entry decision log) for an audit-and-repair toolchain targeting diluted `specs/` directories, grounded in surveys of diluted (medata/sdd-ui/rtob) and clean (rune/orbit/transit) repos. Design: a stdlib `spec_lint.py` mechanical auditor + `/spec-janitor` skill with disposition-tiered repair authority (auto-fix only for deterministic-or-additive transformations; judgment repairs gated; autonomous surfaces report-only), a normative `spec-conventions.md` with stable rule IDs, durable per-spec/per-finding exclusions in `specs/.janitor.json`, a new verbatim-seeding class for align (managed blocks are markdown-only), and prevention guardrail edits across six authoring/implementation skills

## [2026-07-25]

### Changed
- **Nextup pure router** (spec `nextup-pure-router`): `/nextup` no longer keeps any status record — the machine zone in `nextup.md` is removed everywhere. The skill (rewritten as a compact pure router): the user-zone contract, seeding from `nextup.example.md`, the four lanes (direct/light/PRD/gated spec), job splitting/fan-out, and the `act autonomously` flag keep their semantics; feature detection is explicit reference → branch → `specs/` contents with no machine-zone fallback; close-out shrinks to the bookkeeping sweep (rune tasks for loose ends, adjudicated decisions to `decision_log.md`, `/specs-overview` regeneration) with no `nextup.md` writes. Fan-out outcomes, interrupt handoffs, and loose ends without a tasks file are reported in the session's plain-English closing message (gated jobs that will not be dispatched are restated to the user before dispatch); a `/nextup` run after a `/sendit` handoff whose user zone carries no change requests counts as approval of the sent docs
- `nextup.example.md` + session-local `nextup.md`: user zone plus a bare `<!-- LM -->` marker with a single inert line ("reserved marker for tooling — no session status is kept here"). The marker survives as `scripts/align.py`'s convergence anchor (align itself unchanged), which distributes the slimmed template downstream
- `sendit` skill: never writes `nextup.md` — copy the spec docs to Prism, report loose ends in the closing message, stop; standalone feature resolution keeps explicit reference and branch only
- `make-it-so` / `next-task` skills: ambiguous target resolution now lists the candidates and asks the user (machine-zone fallback dropped); the `/sendit` gate boilerplate in the four starwave skills no longer mentions nextup machine notes
- `scripts/process_status.py` (`make status`): ZONE/NOTE columns and the `machine-zone`/`stale-nextup` drift flags removed — `nextup.md` is checked for presence only; remaining flags are `spec-gap`, `rune-drift`, `no-agentic-json`. `tests/test_process_status.py` updated in step
- Docs (`scripts/README.md`, `docs/runbooks/process-onboarding.md`, `docs/agent-notes/process-status.md`, `docs/agent-notes/align-tooling.md`): progress and status now live in `specs/` (plus `specs/OVERVIEW.md`), rune task lists, and the session's closing message — nothing claims nextup or sendit maintains status in `nextup.md`

## [2026-07-23]

### Added
- **fiscal-probe skill** (PRD `fiscal-probe-skill`): `claude/skills/fiscal-probe/` probes PDF financial statements (AU/NZ/SG/UK/US formats) into a normalised typed ledger and produces reports where every claim carries a `[file p.N]` source reference, targeted at legal briefs in Australian family law property matters. Two deterministic scripts (`extract_transactions.py`, `analyze.py`) with parse-yield verification between them; detects recurring payments, similar-transaction groups, and cross-account transfers. `--json` emits the documented web-frontend contract (`references/json-contract.md`) with stable per-run transaction ids; worked example reports under `references/`. Imported from a packaged `financial-insights.skill` bundle and adapted

## [2026-07-11]

### Added
- **Customer-doc skills** (PRD `agreement-invoice-skills`): `agreement`, `invoice`, and `customer-docs-check` skills under `claude/skills/` author and audit the tocs customer documents — SoW agreement YAMLs, invoicer-schema invoice copies, and the two-way `invoice_refs` ↔ `invoice_number` cross-references — from free-form input, running tocs generation to surface schema errors. Schema and referencing rules live once in the tool-neutral `docs/reference/customer-docs-authoring.md` (usable as-is with the Gemini CLI or a localml-served model); `docs/runbooks/customer-docs.md` documents the workflow and backends
- **Rune guardrails** (same PRD): `make status` gains a `rune-drift` flag — `specs/**` task files that fail `rune list` parsing are flagged per repo with the failing file named in the detail lines (missing binary degrades to a warning; report stays read-only); `shared/conventions.md` now requires rune-managed task files under `specs/` and spec documents before committed feature work (regenerated into `claude/CLAUDE.md` and the copilot instructions); bootstrap step 4b symlinks `~/repos/rune/rune` onto PATH when absent; `docs/runbooks/rune-usage.md` covers day-to-day rune usage and clearing `rune-drift`. Six new process-status tests

### Notes
- `rune list` exits 0 on files with no task lines, so an empty placeholder `tasks.md` is not flagged as drift — only malformed task lines are

## [2026-07-10]

### Added
- **Nextup-template align step** (PRD `nextup-starwave-refinement`): `scripts/align.py` pipeline step 6 seeds `nextup.example.md` verbatim into target repos when absent, converges only the machine zone (first `<!-- LM -->` down) while preserving the user zone byte-for-byte, skips markerless targets, ensures a `nextup.md` gitignore entry (append or create), and never touches the session-local `nextup.md`; shadow-copy plan runs cover the new files. 13 new tests over 8 fixture repos
- **Process status report**: stdlib-only `scripts/process_status.py` behind `make status` (`REPOS=` override) — one read-only row per repo (branch, tree state, last commit, nextup machine-zone marker and newest note date, `nextup.example.md`/`.agentic.json` presence, per-spec-folder document listing) with drift flags `machine-zone`, `stale-nextup`, `spec-gap`, `no-agentic-json`; defaults to this repo plus medata, netmap, tocs, rtob, localml, loshop. 22 fixture-based tests
- `docs/runbooks/process-onboarding.md`: how a repo joins the nextup/starwave process — plan-only first align run, manifest review, apply run, seeded artifacts, first `/nextup` session, and the lane map (direct, light, PRD, gated starwave)

### Changed
- `docs/agent-notes/align-tooling.md` documents the nextup-template step (user-zone preservation, markerless skip, gitignore handling, why `nextup.md` is never touched)
- Rollout: align applied and committed in medata, netmap, and loshop (`[chore]: align nextup/starwave process assets`, unpushed); tocs, rtob, and localml skipped as dirty and left bit-identical

## [2026-07-05]

### Added
- **Transit workflow integration**: restored the Transit conventions dropped in a0aea2e via the generated-fragments architecture — tool-neutral rules (`T-<id>` ticket references, status-change comments, one Transit project per repo with an optional `transit_project` override in `.agentic.json`) in `shared/conventions.md`, Claude-side `mcp__transit__*` tool names and the `/transit` router pointer in `shared/claude-wrapper.md`, both regenerated into the checked-in outputs. New cross-project integration reference (`docs/agent-notes/transit-integration.md`) mapping every Transit status/column onto the SDD workflow (driving skill + transition trigger, including the PRD lane), plus a `docs/runbooks/transit-mcp.md` setup/smoke-test runbook and a Transit tickets section in `spec-workflow.md`
- **PRD-lane Transit hooks (optional)**: `prd` moves a referenced ticket to `planning` on authoring start; `engage` moves it to `in-progress` on execution start and `ready-for-review` on completion — always with comments, skipped when no ticket applies, and never setting `done` autonomously
- `tests/test_align.py`: `ManifestPreservationTest` pins that align never rewrites an existing `.agentic.json`, so optional keys like `transit_project` survive; the conventions test now also forbids `mcp__` in the Copilot output

## [2026-07-04]

### Added
- **PRD lane**: `prd` skill (author a standalone PRD with per-context requirement groups) and `engage` skill (derive rune task files per context, execute contexts in parallel worktrees with context-qualified branches, STOP protocol, integrated-branch quality gate), plus `copilot/agents/prd.agent.md` so VS Code Copilot and the cloud coding agent can author PRDs — the toolset-agnostic autonomous route alongside the Claude-only gated starwave lane
- **Generation toolchain**: `shared/` convention fragments assembled by `scripts/generate.py` into `claude/CLAUDE.md` and `copilot/instructions/copilot-instructions.md` (both generated, managed-block markers, checked in); `mcp/servers.json` as the single MCP source of truth generating Claude user config, VS Code user `mcp.json`, per-repo `.mcp.json`/`.vscode/mcp.json`, and a paste-ready cloud-agent payload with per-surface secret mechanisms
- **Per-repo alignment**: `scripts/align.py` driven by a checked-in `.agentic.json` — fixes stale user paths (portable forms), invalid JSON (backup + regenerate), drifted canonical MCP entries (non-canonical preserved), checksum-matched stale agent packs (`scripts/stale-packs.json`), and seeds cloud-agent assets in managed blocks; first run plans without applying
- **Machine bootstrap**: `scripts/bootstrap.sh` (Homebrew, Brewfile, go installs, symlinks, config generation, VS Code seeding incl. the localml model provider, manual-auth list ending in re-run), `Brewfile`, `Makefile` (generate/sync/align/test/lint with a self-restoring drift check), and runbooks `docs/runbooks/localml-vscode.md` + `docs/runbooks/cloud-agent-mcp.md`
- Test suite: 66 stdlib-unittest tests with golden fixtures covering generation, alignment idempotence, seeded-file preservation, and sync backwards compatibility

### Changed
- `nextup` skill: autonomous dispatch — the user zone is arbitrary instructions executed or dispatched directly when no spec work is called for; a PRD reference routes to `/engage` (missing-but-requested PRD → `/prd`); an `act autonomously` user-zone flag prefers the ungated lane end-to-end; the gated starwave lane is a recommendation for feature-shaped work, never an enforcement. Machine-zone rules, close-out mode, and the light/spec signal tables are unchanged
- `scripts/sync-claude.sh`: existing six links unchanged; adds `mkdir -p` guards and a VS Code profile symlink for the PRD agent
- README.md and spec-workflow.md: document the lane split (gated starwave = Claude Code; PRD lane = toolset-agnostic), the new layout, and the clone → bootstrap → authenticate quickstart
- `engage` skill: precision fixes from the worked-example verification — derive commits its output, phase ordinals defined for named rune phases, Override 3 lists the make-it-so steps that don't apply inside a context, headless blocked-at-STOP contexts merge partial work with the task file as resume point, `git worktree remove --force` for artifact-dirtied worktrees

### Fixed
- Rollout hardening: rune installs via `go install` (the brew tap ships a broken v0.0.0 placeholder that also blocked `brew bundle`'s all-or-nothing fetch); Claude-CLI MCP convergence normalizes `args`/`env` so reruns report already-configured; shellcheck findings fixed now that `make lint` actually runs it; per-repo alignment applied across rtob, sanarte, workscripts, betscraper, template, and this repo (stale `/Users/ronan` paths, invalid JSON, 14 stale agent-pack files)

### Removed
- `copilot/prompts/` (8 stale prompt/chatmode files from the pre-starwave era) — superseded by the PRD lane assets and generated instructions

## [2026-07-02]

### Fixed
- `claude/statusline.sh`: Read the effort level from `/Users/r/.claude/settings.json` instead of the hardcoded `/Users/arjen/...` path inherited from the upstream fork — the lookup silently failed on this machine, so the effort level never showed in the statusline

### Changed
- `nextup` skill: Reframe from "router, not executor" to **dispatcher, not implementer**. Routing is now evidence-based: step 6 lists concrete light-lane vs spec-lane signals (names an existing file/defect with fix/tweak/rename verbs vs new capability, several components, open design decisions), borderline jobs start at `/starwave:smolspec`, and every dispatch states the lane, skill, and deciding signal so the routing can be trusted without re-checking. New step 6b splits the user zone into independent jobs: unattended-safe light-lane jobs fan out to parallel sub-agents (one per job in a single message, each running its routed skill, worktree isolation when they mutate files, nextup staying on as overseer to integrate outcomes into the machine zone), while gated spec-lane jobs — whose approval gates a sub-agent cannot collect — run inline one at a time with the rest queued under Next up. `/bug-blitz` still owns same-shaped bug batches, and nextup still never implements, reviews, or commits work itself and only recommends `/make-it-so` / `/next-task`
- `nextup` skill + `nextup.example.md`: Machine-zone marker is now `<!-- LM -->`, mirroring `<!-- USER -->` at the top of the user zone. Legacy markers (`<!-- ML -->`, `<!-- nextup:machine -->`, `# What I want`) still parse but are migrated to `<!-- LM -->` on rewrite. The machine zone is restricted to the template's fields only (feature, branch, stage, progress, next up, notes) — close-out now writes its handoff into those fields instead of growing new sections — and the user-zone placeholder reads `<user inputs for next session>`
- `sendit` skill: Update the machine-zone reference to the `<!-- LM -->` marker (treating `<!-- ML -->` / `<!-- nextup:machine -->` as legacy equivalents); it previously matched only `<!-- nextup:machine -->` and would have missed migrated files

## [2026-06-19]

### Added
- `sendit` skill: Ship the active feature's spec documents to the user's Prism iCloud review folder (`~/Library/Mobile Documents/com~apple~CloudDocs/Prism Markdown/`) for review. Resolves the active feature the same way `/nextup` does (conversation/user-zone reference → branch → machine zone), copies `*.md` from `specs/{feature}/` into Prism as is (no subfolder or prefix, replacing same-named files), updates the `nextup.md` machine zone to record the handoff and point Next up at "review in Prism then `/nextup`", and closes out the session

### Changed
- `starwave-requirements`, `starwave-design`, `starwave-tasks`, and `starwave-smolspec` skills: Make `/sendit` the **default action** offered at every "do the requirements/design/tasks/smolspec look good?" approval gate. The reviewer is often non-technical and reviews markdown in Prism rather than the terminal, so each gate now offers `/sendit` (ship to Prism + close out) as the recommended choice alongside approving inline or requesting changes

## [2026-05-22]

### Changed
- `make-it-so` skill: Always delegate phase work to a subagent — the main agent no longer implements tasks itself in any path. Multi-stream phases still use one worktree-isolated subagent per stream as before. Single-stream and stream-less phases now spawn one subagent that implements the whole phase in place (no worktree, no merge step) and commits to the working branch. Subagent commit conventions are unified: no subagent touches `CHANGELOG.md`; the main agent always writes the single phase-level changelog entry after subagents return (and after merges, in parallel mode). Review (design-critic), specs/OVERVIEW.md update, and compact-and-continue still run on the main agent
- `make-it-so` skill: Restructure parallel execution so each ready work stream is owned end-to-end by a dedicated subagent running in its own git worktree. The main agent now only delegates and oversees — it creates a worktree per ready stream (`git worktree add .claude/worktrees/<phase>-stream-<N> -b stream/<phase>-<N>`), spawns one subagent per worktree in a single Task message, and re-checks `rune streams --available --json` after each return to spawn fresh subagents for newly unblocked streams. Stream subagents implement, mark tasks complete, run tests, and commit on their own stream branch using the project's commit conventions (skipping the changelog, which is now a single phase-level entry written by the main agent after merging all streams). After all streams report `done`, the main agent merges each stream branch with `--no-ff` (trivial `tasks.md` conflicts are expected — accept both sides), removes the worktrees, deletes the merged branches, runs design-critic, writes the phase changelog entry as a separate commit, updates `specs/OVERVIEW.md`, then compact-and-continues. Sequential single-stream / no-stream paths still work in place and still update the changelog themselves

## [2026-05-19]

### Changed
- `scripts/build_review_html.py`: Replace highlight.js diff highlighting with a self-rendered per-line markup. New `_render_diff()` splits the diff and tags each line as `diff-add`/`diff-del`/`diff-hunk`/`diff-file-header`/`diff-meta`/`diff-context`; the page CSS styles `.diff-line` as `display:block` with full-width backgrounds (via `display:inline-block; min-width:100%` on the surrounding `<code>`) so consecutive additions or deletions paint a continuous bar instead of per-line "row pills" separated by the trailing-newline gap hljs produced. The highlight.js stylesheet and three scripts are removed from the page template since nothing else used them
- `claude/CLAUDE.md` (user global): Add "Before editing any file, read it first. Before modifying a function, grep for all callers. Research before you edit" to the Development Workflow section
- `make-it-so` skill: Detect ready work streams per phase via `rune streams --available --json` and spawn one parallel subagent per stream (single message, single Task call each) when 2+ streams are ready, falling back to sequential execution when only one stream has ready work. Each subagent uses `rune next --phase --stream N --format json` to retrieve its tasks and marks them complete as it goes. The existing per-phase review → commit → specs-overview update → compact-and-continue loop is preserved, and the loop now stops cleanly without compacting when no incomplete tasks remain

## [2026-05-18]

### Added
- `local-review` agent: Sonnet-powered local replacement for the `anthropics/claude-code-action` PR review step. Reviews an open PR via `gh pr diff`, follows the project's `CLAUDE.md` for style/conventions and project-specific flag rules, and posts a single `gh pr comment` so the same review can run without burning private GitHub Actions minutes
- `pr-overview` skill: Read-only PR summary workflow that fetches a GitHub PR, surfaces unresolved code/review/discussion comments verbatim, runs the same parallel review agents as `pr-review-html` without applying fixes, and writes a self-contained `pr-overview.html` to the repo root for browsing before deciding what to do
- `scripts/build_review_html.py`: Shared HTML renderer used by `pre-push-review`, `pr-review-html`, and `pr-overview`. Consumes a JSON description plus optional per-file diff fragments and emits a self-contained Prism Dark themed page with overview cards, three-level explanation tabs (CSS-only radio buttons), important-change cards with Takeaway/Rationale/Open-question callouts, per-file diff `<details>` blocks, and an optional `<script id="review-meta">` block for `pulsar publish` consumption

### Changed
- `pr-pilot` skill: New step 1.5 runs `local-review` in steps 2.1 and 3.3 **by default** and skips it only when an active `anthropics/claude-code-action` workflow (`.github/workflows/*.yml` or `*.yaml` referencing the upstream action) will post the review on its own. Renamed `.yml.disabled` files, `.bak`, editor swap files, or a missing workflow all leave `local-review` running — the goal is "there should always be a Claude review on every PR; the local agent is the cheaper default, the GH Action is the only reason to skip it"
- `local-review` agent: Append a `<!-- claude-local-review -->` sentinel to every PR comment so downstream skills can identify it as a Claude review even though `gh pr comment` posts under the local user account, not `claude[bot]`
- `pr-review-fixer` skill: Treat `claude[bot]` author **and** body-sentinel `<!-- claude-local-review -->` as Claude reviews in all three dedup rules (code-level, PR-level reviews, PR-level issue comments). Emit `<!-- pr-review-overview -->` at the top of the iteration overview comment and match on that sentinel for iteration counting — the previous `claude[bot]`-only check missed every iteration when the skill ran outside the upstream Action
- `pr-overview` skill: Same Claude-review sentinel handling as `pr-review-fixer`; also match the iteration-overview sentinel when filtering noise out of the discussion-comments stream
- `pre-push-review` skill: Phase 7 now invokes the shared `build_review_html.py` renderer with a JSON contract instead of hand-writing HTML; Phase 6 extracts important changes, learnings, and decision rationale (with `inferred` / `unknown` markers) for the renderer even when no spec exists; new Phase 8 publishes via the optional `pulsar` binary when present; Phase 9 (formerly 8) surfaces the archived path
- `pr-review-html` skill: Same renderer refactor as `pre-push-review`. Phase 1 now keeps PR `body`, `author`, `createdAt`, and `url` so Phase 7 can render the author's framing verbatim in a `pr_description` block; Phase 6 produces the three-level explanation plus insight material in a single pass; new Phase 8 publish step and Phase 9 summary mirror `pre-push-review`
- `scripts/README.md`: Document `build_review_html.py` — purpose, CLI usage, JSON schema pointer, rendering behaviour, and output

### Added
- `capture-knowledge` skill: Capture reusable cross-project technical knowledge as notes in the user's Obsidian vault under `03-Notes/Generated/`, with per-machine vault path cache, frontmatter conventions, collision handling, and Obsidian Flavored Markdown guidance
- `pr-review-html` skill: Fetch a GitHub PR, run parallel review agents (code reuse, quality, efficiency, spec/docs), apply local fixes, verify with tests and linters, and write a self-contained `pr-review.html` to the repo root with per-file diffs, decisions, findings, and double-check items
- `claude/statusline.sh`: Custom statusline showing directory, model (with optional effort level), context window percentage, 5h/7d rate-limit usage with reset times, and git branch with dirty marker
- `arjen-style-guide.md`: Personal iOS/iPadOS/macOS 26+ SwiftUI style guide distilled from Prism, Transit, and Flux

### Changed
- `pre-push-review` skill: Add Phase 7 to generate a self-contained HTML review page (per-file diffs with highlight.js, how-it-works explanation, key decisions, review findings, things to double-check), with a spec-aware location fallback; renumber Summary to Phase 8 and include the HTML path in the verdict
- `no-push-main` hook: Honor `git -C <path>` when detecting the current branch, so push/rebase/reset/amend/checkout/restore/clean run inside worktrees check the worktree's branch instead of the shell's cwd
  - New `extract_git_cwd()` helper pulls the last `-C` argument out of the original command
  - `get_current_branch`, `on_protected_branch`, and the push/history/destructive checks all accept an optional `cwd` and pass it through to `git rev-parse`

## [2026-04-24]

### Changed
- Starwave spec skills: Tighten brevity, scope, and granularity rules across the requirements → design → tasks workflow to curb verbose output
  - `starwave:requirements`: Add "Writing Style — Signal over Volume" block (behavior-not-implementation ACs, no speculative/future-proofing reqs, no split outcomes, concrete-or-omit NFRs, no hyperbole); require a Non-Goals / Out-of-Scope section in the document format; add matching self-review gates
  - `starwave:design`: Add "Writing Style — Signal over Volume" block (no requirement restatement, no boilerplate sections, no hyperbole, distilled research); allow omitting inapplicable sections; add "Contracts and Integration Points — Do Not Cut" block (behavioral contracts, integration points, file/module placement); add non-goals and contracts gates to self-review
  - `starwave:tasks`: Add "Task Granularity — No Inflation" block (no fragmenting coherent changes across setup/implement/wire, no decorative phases or streams, no title-restating `details` bullets); add non-goals and granularity gates to self-check
  - `starwave:smolspec`: Add fragmentation and out-of-scope rules to Task Description Guidelines; extend smolspec self-review with behavior-not-mechanism and anti-hyperbole gates; extend tasks self-review with fragmentation and out-of-scope gates

## [2026-04-22]

### Changed
- `pr-review-fixer` skill: Stop writing working files inside the repo
  - Working directory moved to `/tmp/pr-review-${PR_NUM}/`; removed the `.claude/reviews/` option
  - Review overview is assembled in-context and posted inline via `gh pr comment` (no intermediate file)
  - Rune task file now lives under the temp working directory; dropped the `--reference` to a non-existent overview file
  - Removed `tee test-output.txt` from test failure handling
  - Cleaned up stale "exclude working files" guidance in commit step and Key Behaviors
- `transit` skill: Route `chore` task type to `/starwave:smolspec` instead of asking the user to clarify

## [2026-04-14]

### Added
- `claude-code-workshop` skill: Interactive workshop that teaches Claude Code features through hands-on exploration, with version-based filtering to focus on what's new since a specific release
- `WSL-settings` agent note: Document `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` and `CLAUDE_CODE_SCRIPT_CAPS` behavior on WSL2

## [2026-04-11]

### Changed
- `blitz-merge` skill: Add local main branch update after all merges complete
  - New Phase 4 checks out and pulls the local main/master branch so it stays in sync with origin
  - Renumbered Report and Cleanup phase to Phase 5
- `starwave-design` skill: Add pattern extension audit and UI consistency reference requirements
  - New "Pattern Extension Audit" section: when extending an existing pattern to a new type, requires searching all call sites and including a parity audit in the Architecture section
  - New "UI Consistency References" section: requires referencing existing UI elements as baseline instead of describing visual properties from scratch
  - Two new self-review checklist items for pattern audit and UI consistency verification
- `starwave-requirements` skill: Add guidance for acceptance criteria to reference existing UI patterns as baseline rather than describing visual properties independently

## [2026-04-03]

### Changed
- `no-push-main` hook: Handle compound commands and git global options
  - Split compound shell commands (chained with `&&`, `||`, `;`) and check each part independently
  - Strip git global options (`-C`, `--git-dir`, `--work-tree`, etc.) before matching, so `git -C /path push` is correctly blocked

### Added
- `specs-overview` skill: Generate or regenerate `specs/OVERVIEW.md` with tabular summary, status tracking, and per-spec file listings
- `make-it-so` skill: Update `specs/OVERVIEW.md` status after committing (Done/In Progress)
- `next-task` skill: Update `specs/OVERVIEW.md` status after completing task groups
- `starwave-creating-spec` skill: Add Phase 4.5 to register new specs in `specs/OVERVIEW.md`
- `orbit-guidance-2.yaml`: Multi-variant guidance file for orbit with minimal and defensive approach variants

## [2026-03-18]

### Changed
- `no-push-main` hook: Add `gh` CLI protection and fix exit code
  - Blocks `gh repo delete`, `gh repo edit --default-branch`, `gh repo sync --force --branch main`, `gh pr merge --admin`
  - Blocks mutating `gh api` calls targeting protected branch refs, branch protection rules, and rulesets
  - Detects mutation intent via HTTP method, `-f`/`-F` field flags, `--input`, and GraphQL mutations
  - Fix exit code from 1 to 2 (required by Claude Code to block execution)

### Added
- Branch protection research report (`docs/agent-notes/branch-protection-across-agents.md`)
  - Documents protection mechanisms for Claude Code, Kiro CLI, Copilot CLI, and Codex CLI
  - Covers `gh` CLI and MCP server attack surfaces with practical recommendations

## [2026-03-15]

### Added
- `no-push-main` PreToolUse hook that protects `main`/`master` branches from accidental modification
  - Push protection: direct, force, bare, refspec targets, `--delete`, and flag combinations (`-u`, `--force-with-lease`)
  - History rewrite protection: blocks `reset --hard`, `rebase`, and `commit --amend` while on protected branches
  - Destructive operation protection: blocks `checkout .`, `restore .`, and `clean -f` while on protected branches
  - Branch manipulation protection: blocks `branch -D`/`-f` targeting protected branches
  - Hook lives in `claude/hooks/` and is synced to `~/.claude/hooks/` for global use
- `claude/hooks/` directory with README documenting available hooks, setup, and how to add new ones
- Hooks symlink in `sync-claude.sh`, GitHub Action, and remote sync for consistent availability across local, CI, and sandbox environments

## [2026-03-11]

### Changed
- `pr-pilot` skill: Replace `gh pr checks --watch` with a 10-minute wait for CI and agent reviewers, then run `/pr-review-fixer` to handle new comments on rebased code
- `pre-push-review` skill: Rewrite as parallel multi-agent review with automatic fixes
  - Launches 4 concurrent review agents: code reuse, code quality, efficiency, and spec/documentation
  - Agents fix issues directly instead of only reporting them
  - Adds verification phase to run tests and linters after fixes
  - Simplifies structure into 7 clear phases

## [2026-03-05]

### Changed
- `fix-bug` skill: Add difficulty-based branching with competing implementations for complex bugs
  - Investigation checkpoint: commit failing regression tests and report before implementing the fix (red/green TDD)
  - Difficulty assessment: classify bugs as simple (direct fix) or complex (multiple approaches)
  - Complex path spawns 3 competing agents (2 Claude subagents via Agent tool + 1 Kiro via `mcp__devtools__kiro-agent` with `agent: "kiro"`)
  - Compares solutions on correctness, minimality, code quality, safety, and maintainability
  - Produces a solution comparison report and cherry-picks the winning implementation

## [2026-03-04]

### Added
- `pr-pilot` skill for shepherding a PR from push through review to merge
  - Pushes branch, creates PR, runs `/pr-review-fixer` in a loop until no blockers/critical/major issues remain (capped at 5 iterations)
  - Rebases onto latest `origin/main`, resolves conflicts, and squash-merges
  - Optional Transit ticket tracking — moves ticket to `done` after merge
- `blitz-merge` skill for batch-fixing bugs with automated review cycles and squash-merge
  - Extends bug-blitz with a review loop that runs `/pr-review-fixer` until no blockers/critical/major issues remain (capped at 5 iterations)
  - Sequentially squash-merges each clean PR after rebasing onto latest `origin/main`
  - Updates Transit tickets to `done` after successful merge

## [2026-02-27]

### Changed
- `bug-blitz` skill: Always filter bugs by the current Transit project instead of treating project filtering as optional

## [2026-02-26]

### Changed
- `fix-bug` skill: Add automated review fix step that waits 10 minutes after PR creation then runs `/pr-review-fixer` to handle first round of CI and review feedback (Transit bugs only)

## [2026-02-23]

### Changed
- `starwave-tasks` skill: Enforce red/green TDD ordering for all implementation tasks
  - Tasks must follow red (write failing test) then green (implement to pass) pairing
  - Test and implementation tasks must be adjacent and clearly paired
  - Configuration, types/interfaces, and wiring tasks are exempt
- `starwave-tasks` skill: Add self-check section before presenting tasks to user
  - Verify red/green TDD ordering
  - Run `rune list` to validate task file renders correctly (numbering, hierarchy, streams, dependencies)
  - Confirm requirement coverage, no orphaned tasks, and no circular dependencies

## [2026-02-22]

### Changed
- `pr-review-fixer` skill: Post review reports as PR comments instead of committing them as files
  - Review overview is posted via `gh pr comment` before pushing code fixes
  - Local review/task files are working files only, never committed
  - Iteration tracking now based on existing `claude[bot]` PR comments

## [2026-02-20]

### Added
- `code-audit` skill for parallel codebase quality review
  - Spawns two subagents (code-simplifier and design-critic) to independently analyse the current directory
  - Consolidates and deduplicates findings into a prioritised report grouped by category
  - Offers to create Transit tasks for actionable items

## [2026-02-18]

### Changed
- `pr-review-fixer` skill: Namespace non-spec review output by PR number (`.claude/reviews/PR-[number]/`) to prevent file conflicts when multiple PRs are worked on simultaneously

## [2026-02-16]

### Added
- `bug-blitz` skill for batch-fixing all open bugs in parallel
  - Fetches bug-type tasks in "idea" status from Transit
  - Creates isolated git worktrees per bug based off main
  - Spawns parallel subagents each running the fix-bug workflow
  - Reports results in a summary table and offers worktree cleanup

### Changed
- Added Transit comment requirement to CLAUDE.md — status changes must include an explanatory comment
- `fix-bug` skill: Auto-create branch and PR for Transit bugs instead of prompting; added Transit comment templates for status transitions
- `fix-bug` skill: Skip branch creation when current branch already matches `T-{number}/bugfix-*` (worktree support)
- `starwave-creating-spec` skill: Added Transit comment templates for `spec` and `ready-for-implementation` status transitions

## [2026-02-14]

### Changed
- Renamed `liquid-glass-forms` skill to `swiftui-forms`
- Added Transit ticket (`T-<id>`) convention to CLAUDE.md project conventions, pointing to Transit MCP tools and `transit` skill
- Added `swiftui-forms` skill reference to Swift language rules for form layout work
- `starwave-smolspec` skill: Clarified rune integration to explicitly request file creation with smolspec.md reference and `blocked_by` dependencies via batch operations

## [2026-02-13]

### Added
- `transit` routing skill for dispatching Transit tickets (`T-[number]`) to appropriate workflows by task type
  - Routes bugs to `/fix-bug`, features to `/starwave:creating-spec`, research to plan mode
  - Asks for clarification on chore and documentation types
  - Handles edge cases: task not found, done/abandoned tickets, ambiguous types
- Transit integration in `fix-bug` skill with ticket status tracking and branch creation step
  - Moves ticket to `in-progress` at start, `ready-for-review` at completion
  - Offers `T-{number}/bugfix-{bug-name}` branch naming when ticket present
- Transit integration in `starwave-creating-spec` skill with ticket status tracking
  - Moves ticket to `spec` after scope assessment approval, `ready-for-implementation` after Phase 5
  - Offers `T-{number}/{spec-name}` as recommended branch name when ticket present
- Agent notes for Transit integration (`docs/agent-notes/transit-integration.md`)

### Changed
- `commit` skill: Broadened ticket extraction pattern from 3-5 to 1-5 character prefixes to support Transit's `T-[number]` format

## [2026-02-06]

### Changed
- `next-task` skill: Updated parallel execution to use `rune next --phase --stream N` for subagents
  - Subagents now retrieve all phase tasks for their stream in one call instead of iterative claiming
  - Simplified subagent instructions and cross-stream coordination
- `pr-review-fixer` skill: Added thread resolution, auto-commit, and push
  - New step to resolve fixed code-level review threads via GraphQL mutation
  - Final step now explicitly commits and pushes to remote
  - Added thread `id` to GraphQL query for review thread resolution

### Added
- Agent Notes workflow in CLAUDE.md for maintaining implementation notes across sessions
  - Notes stored in `docs/agent-notes/`, organised by topic or module
  - Read relevant notes before starting tasks, update after completing them
- Skills Usage section in CLAUDE.md to direct agents to check existing skills before manual approaches

## [2026-02-04]

### Added
- `explain-like` skill for explaining code changes or designs at three expertise levels (beginner, intermediate, expert)
  - Supports PR/branch change explanations and design document validation
  - Generates structured explanations with different depth for different audiences
  - Can be used as a self-review mechanism to catch gaps or logic issues
- `fix-bug` skill for systematic bug investigation, resolution, and documentation
  - Integrates with `systematic-debugger` skill for root cause analysis
  - Creates regression tests before implementing fixes
  - Generates standardized bugfix reports in `specs/bugfixes/<bug-name>/`
- `orbit-guidance.yaml` template for multi-variant implementation approaches
  - Defines three implementation styles: Minimal/Pragmatic, Defensive/Thorough, Performance-Oriented
  - For use with Orbit multi-agent parallel execution

### Changed
- `pre-push-review` skill: Added implementation explanation step using `explain-like` skill
  - Generates `specs/{feature_name}/implementation.md` for documentation
  - Uses explanation as validation mechanism to verify spec completeness
  - Adds "Completeness Assessment" section to track implementation status
- `starwave-design` skill: Added self-validation step using `explain-like` skill
  - Requires explaining design at multiple expertise levels before proceeding to reviews
  - Helps identify gaps, overcomplexity, or logic issues in design documents

## [2026-02-01]

### Added
- Multi-agent parallel execution support via work streams and task dependencies
  - `rune` skill: Added stream assignment, blocked-by dependencies, task ownership/claiming, and stream status commands
  - `next-task` skill: Added stream detection and parallel subagent spawning for multi-stream execution
  - `starwave-tasks` skill: Added guidelines for creating tasks with dependencies and work stream assignments

### Changed
- `pr-review-fixer` skill: Extended to fetch PR-level comments (reviews and issue comments) in addition to code-level comments; added CI status checking and automated fix workflow for failing tests, lint, and build
- `pre-push-review` skill: Enhanced documentation section to explicitly check README.md, CLAUDE.md/AGENTS.md, and other docs for needed updates
- `starwave-requirements` skill: Changed design-critic invocation to use Task tool with subagent_type="general-purpose" instead of direct skill call
- `starwave-design` skill: Changed design-critic invocation to use Task tool with subagent_type="general-purpose" instead of direct skill call

## [2026-01-22]

### Added
- `pr-review-fixer` skill for fetching and fixing GitHub PR review comments
  - Filters out resolved comments and keeps only last claude[bot] comment per thread
  - Validates issues against current code before creating fix tasks
  - Creates review-overview and review-fixes files with iteration tracking
  - Integrates with rune for task management
  - Supports spec-based PRs (output to specs folder) and non-spec PRs (output to .claude/reviews)

## [2026-01-21]

### Changed
- Updated skill files to replace "agent" references with "skill" terminology
  - `next-task`, `make-it-so`: Changed "sub agent" to "skill" for efficiency-optimizer and design-critic
  - `starwave-requirements`, `starwave-design`: Updated to use design-critic skill and Task tool with subagent_type="peer-review-validator"
  - `starwave-smolspec`: Changed "design-critic agent" to "design-critic skill"

## [2026-01-20]

### Added
- `pre-push-review` skill for reviewing unpushed commits before pushing to remote repository
  - Reviews code quality, spec adherence, testing, and documentation
  - Provides actionable feedback categorized by severity (Critical, Important, Minor, Suggestion)
  - Skill-based alternative to the existing `pre-push-code-reviewer` agent
- `code-simplifier` skill for reviewing and simplifying code to reduce complexity
- `ui-ux-reviewer` skill for evaluating user experience of interfaces (CLI, web, mobile)
- `efficiency-optimizer` skill for analyzing code for performance improvements
- `design-critic` skill for critical review of design documents and architecture proposals

### Changed
- Updated `peer-review-validator` agent to use `kiro-agent` instead of `q-developer-agent` for AWS/cloud-native validation

### Removed
- `code-simplifier` agent (replaced by skill)
- `ui-ux-reviewer` agent (replaced by skill)
- `efficiency-optimizer` agent (replaced by skill)
- `design-critic` agent (replaced by skill)
- `pre-push-code-reviewer` agent (replaced by `pre-push-review` skill)

## [2025-01-16]

### Changed
- Restructured CLAUDE.md with organized sections (Communication Style, Development Workflow, Project Conventions, CLI Commands, Documentation Standards)
- Added availability check for `run_silent` command before using it
- Replaced XML-style tags with standard markdown headers

## [2025-01-15]

### Changed
- Updated commit skill to conditionally run tests and linting only when code files are changed, skipping for documentation-only changes

## [2025-01-14]

### Changed
- Migrated all commands to skills - commands directory has been removed
- Reorganized spec-driven development skills under `starwave-` prefix with flat folder structure:
  - `starwave-creating-spec` - Main orchestrator for the full workflow
  - `starwave-smolspec` - Lightweight specification for small changes
  - `starwave-requirements` - Requirements gathering phase
  - `starwave-design` - Design document creation phase
  - `starwave-tasks` - Task planning phase
- Skills are now invoked as `/starwave:creating-spec`, `/starwave:requirements`, etc.
- Updated spec-workflow.md with new workflow diagram showing `/starwave:creating-spec` as the main entry point
- Updated README.md to reflect new skill organization and workflow

### Added
- Optional `prerequisites.md` file support in starwave-tasks skill for manual user setup tasks
  - Supports tasks like Xcode configuration, Apple Developer portal setup, cloud console configuration
  - Organizes prerequisites by timing: Before Starting, During Implementation, Before Testing
- Smolspec section in spec-workflow.md explaining when and how to use the lightweight specification workflow

### Removed
- `claude/commands/` directory - all commands migrated to skills
- Removed `commands` symlink from sync-claude.sh and GitHub Action

## [2025-12-31]

### Added
- `project-init` skill for setting up Claude Code project configuration
  - Adds SessionStart hook to `.claude/settings.json` for remote/sandbox environments
  - Includes `setup-project.sh` script that merges hooks without overwriting existing settings
  - Language detection for automatic permission configuration (Go, Swift, Node.js, Python, Rust, Ruby, Java, Docker, Terraform)
- `skill-creator` skill for creating effective Claude skills
  - Includes `init_skill.py` script for initializing new skill directories
  - Includes `quick_validate.py` for skill validation
  - Reference documentation for workflows and output patterns
- `systematic-debugger` skill for applying modified Fagan Inspection methodology to persistent bugs
- `permission-analyzer` skill for analyzing Claude Code permission configurations
  - Includes `analyze_permissions.py` script for permission analysis
- `starwave` commands directory with design, requirements, and tasks commands
- `make-it-so` command for implementing all tasks
- `claude-remote.sh` script for pulling user configuration in sandboxed environments (GitHub Actions, online Claude Code)
- Project-level `.claude/settings.json` with SessionStart hook for remote environment setup

### Changed
- Simplified `creating-spec` skill documentation
- Updated `rune` skill with minor improvements
- Simplified `copilot/prompts/tasks.prompt.md`
- Expanded Swift language rules with additional patterns and guidelines

## [2025-12-13]

### Added
- Scripts directory symlink to setup-claude GitHub Action and sync-claude.sh script

### Fixed
- Updated README documentation in setup-claude action to reference `rules/` instead of `language-rules/`

## [2025-12-10]

### Added
- Swift language rules (`claude/rules/language-rules/swift.md`) with patterns for:
  - SwiftData and CloudKit testing with test environment detection
  - Swift 6 concurrency and MainActor patterns
  - SwiftUI Liquid Glass guidelines for iOS 26+/macOS Tahoe
  - NavigationSplitView platform-specific patterns
  - App Intents design for Shortcuts compatibility
  - Testing with Swift Testing framework
- Sync script (`scripts/sync-claude.sh`) for creating symlinks from `~/.claude/` to repository files

### Changed
- Reorganized all Claude Code configuration files into `claude/` subdirectory structure:
  - `CLAUDE.md` → `claude/CLAUDE.md`
  - `agents/` → `claude/agents/`
  - `commands/` → `claude/commands/`
  - `skills/` → `claude/skills/`
  - `language-rules/` → `claude/rules/language-rules/`
  - `references/` → `claude/rules/references/`
- Updated GitHub Action to use new `claude/` directory structure for symlinks
- Updated example workflow to verify new directory structure
- Updated README.md with new file structure documentation
- Added YAML frontmatter with `paths` glob pattern to language rules for automatic matching

## [2025-12-02]

### Added
- Self-review checklists for requirements and design commands
  - Requirements: EARS format compliance checklist (user story format, EARS keywords, testable criteria, anchor tags, vague terms, edge cases)
  - Design: Requirements traceability checklist (design element coverage, acceptance criteria tracing, data model support, error handling, testing strategy, scope creep check)
- Added checklists to both Claude Code commands and Copilot prompt versions

## [2025-12-01]

### Added
- Copilot prompt version of smolspec command (`copilot/prompts/smolspec.prompt.md`)
- Property-based testing (PBT) guidance as optional consideration in design workflow
  - Design command evaluates acceptance criteria for PBT candidates (invariants, round-trips, idempotence)
  - Tasks command includes property test tasks when design specifies them
  - Go language rules include PBT section with `pgregory.net/rapid` recommendation
- Decision log format reference document (`references/decision-log-format.md`) with Enhanced Nygard ADR structure
- Utility scripts: `scripts/convert_formats.sh` and `scripts/fetch-tickets.py`

### Changed
- Enhanced `smolspec` command with complexity estimation, self-review checklists, outcome-focused tasks, and distributed testing requirements
- Updated CLAUDE.md with decision log format reference and fixed file path syntax
- Changed `design-critic` and `peer-review-validator` agents to use opus model
- Updated Copilot prompt frontmatter to use `agent: agent` instead of `mode: agent`
- Enhanced `pr-prep.prompt.md` to save release notes to pr_description.md

## [2025-11-14]

### Added
- `smolspec` command for lightweight specification workflow for small changes
  - Combined requirements and implementation approach in single smolspec.md file
  - Separate tasks.md file compatible with next-task command
  - Built-in scope assessment with automatic escalation to full spec workflow
  - Integration with design-critic agent for review before user presentation
  - Streamlined workflow for minor changes that don't warrant full documentation
- Go Test Fixer skill for improving Go test files
  - Converts slice-based table tests to map-based table tests
  - Splits large test files into focused test files
  - Enforces Go testing best practices from language-rules/go.md

### Changed
- Updated release-prep command to specify release notes location in docs/release_notes/
- Updated Copilot prompt files to use gpt-5.1-codex model instead of gpt-5

## [2025-11-04]

### Added
- GitHub Action for setting up Claude configuration in CI/CD pipelines
  - Composite action at `.github/actions/setup-claude/action.yml` that symlinks all configuration directories
  - Action symlinks agents, commands, language-rules, scripts, skills, and CLAUDE.md to `~/.claude/`
  - Example workflow demonstrating action usage with verification steps
  - Action documentation with basic and advanced usage examples
- Skills section in README documenting `creating-spec` and `rune` skills
- GitHub Action section in README with usage examples and workflow integration
- `creating-spec` skill for orchestrating spec-driven development workflow
  - Complete three-phase workflow: requirements, design, and task planning
  - Built-in approval gates between phases
  - Integration with design-critic and peer-review-validator agents
  - Automatic decision logging and EARS format requirements
  - Rune CLI integration for task management
- Enhanced rune skill documentation with `--reference` flag support for creating task files with top-level references

### Changed
- Updated README with Skills section explaining spec-driven workflow orchestration and task management capabilities
- Enhanced README with GitHub Action documentation including basic usage, what it does, and complete CI/CD examples
- Added example pattern for creating feature task files with references to requirements, design, and decision log

## [2025-11-03]

### Added
- Rune task management skill with instructions and capabilities
- Skill configuration files (skills/rune/prompt.md, skills/rune/skill.json)

### Changed
- Updated CLAUDE.md to instruct using rune skill for task management
- Simplified next-task.md command to delegate to rune skill for task retrieval and completion
- Simplified tasks.md command to delegate task creation to rune skill instead of requiring manual JSON construction

## [2025-11-03]

### Added
- `catchup` command for analyzing branch changes and commits to quickly understand work done
- Command documentation in commands/catchup.md with workflow for understanding branch history

### Changed
- Updated README.md to include catchup command in workflow list with attribution to Shrivu Shankar

## [2025-10-28]

### Added
- GitHub Copilot prompt files in `copilot/prompts/` directory for cross-platform support
  - requirements.prompt.md, design.prompt.md, tasks.prompt.md, next-task.prompt.md
  - commit.prompt.md, pr-prep.prompt.md, design-critic.chatmode.md
- `pre-push-code-reviewer` agent for critical review of unpushed commits
- `release-prep` command for preparing releases with quality checks and documentation updates
- `.gitignore` file with `localdocs/` exclusion
- AskUserQuestion tool requirement in requirements and design commands for better user interaction
- Rune CLI integration for task management in `next-task` command
- CLAUDE.md configuration section in README documenting AI behavior guidelines

### Changed
- Updated `peer-review-validator` agent to require consultation with at least two external AI systems (Gemini, Codex, or Q Developer)
- Changed `design-critic` agent to use Sonnet model instead of Opus for improved efficiency
- Enhanced `next-task` command to use `rune next --format json` for task retrieval and `rune complete` for tracking
- Improved `commit` command to prevent reverting code changes and exclude co-authored-by information
- Enhanced `requirements` command with better feature name proposal logic and general question prompts
- Updated spec-workflow.md with detailed documentation for commit, release-prep, and code review processes
- Refined `move_code_section.py` script to extract package name from source file
- Removed hyperbolic language from documentation (e.g., "comprehensive" → "design")
- Added guideline to CLAUDE.md about avoiding hyperbolic terms

## [Unreleased]

### Added
- CLAUDE.md file with global Claude Code instructions
- Go language rules and testing guidelines in language-rules/go.md
- Scripts directory with utility tools:
  - commit-diff-summary.sh for generating change summaries
  - copilot-pr-comments.sh for extracting PR comments
  - move_code_section.py for code manipulation
  - test-conversion directory with Go test conversion tools
- Scripts README documentation explaining usage

### Changed
- Renamed commands/commits.md to commands/commit.md for consistency
- Updated all agent documentation to use specs/ directory structure instead of agents/
- Enhanced command documentation to reflect specs/ path changes
- Improved spec-workflow.md with better structure and terminology
- Updated README.md with scripts directory usage instructions
- Modified JIRA ticket format to support 3-5 character prefixes