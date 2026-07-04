# Decision Log: toolset-agnostic-starwave

## Decision 1: Single Full Spec Covering All Six Workstreams

**Date**: 2026-07-04
**Status**: accepted

### Context

The feature spans six workstreams: Copilot translation, Copilot/repo config consolidation, a PRD document type, MCP codification, localml exposure to VS Code, and a new-machine bootstrap. These could be one spec or several.

### Decision

Run one full spec, `specs/toolset-agnostic-starwave/`, with task phases separating the workstreams.

### Rationale

The bootstrap depends on the Copilot layout and MCP codification; splitting would force cross-spec references for tightly coupled decisions. Phases keep the workstreams independently shippable.

### Alternatives Considered

- **Two specs (process port vs machine bootstrap)**: Cleaner review units - Rejected because the sync script and MCP source of truth are shared between both halves.
- **Reduced scope (Copilot translation only)**: Smallest spec - Rejected because the user explicitly wants the consolidation, PRD, MCP, and bootstrap outcomes now.

### Consequences

**Positive:**
- One decision log and one requirements document for interlocking choices
- Phased tasks still allow incremental delivery

**Negative:**
- Larger documents to review at each gate

---

## Decision 2: Feature Name `toolset-agnostic-starwave`

**Date**: 2026-07-04
**Status**: accepted

### Context

The spec folder needs a name; the current branch (`nextup-resume-entrypoint`) belongs to earlier work.

### Decision

Name the feature `toolset-agnostic-starwave`.

### Rationale

Names the core goal; the other workstreams serve it. Chosen by the user over `starwave-everywhere` and `machine-bootstrap`.

### Alternatives Considered

- **starwave-everywhere**: Shorter - Not chosen; less precise.
- **machine-bootstrap**: Outcome-framed - Not chosen; describes only one workstream.

### Consequences

**Positive:**
- Branch and spec folder will match the feature's intent

**Negative:**
- Long folder name

---

## Decision 3: Supported Copilot Surfaces — VS Code and Cloud Coding Agent Only

**Date**: 2026-07-04
**Status**: accepted

### Context

Copilot capabilities differ per surface: prompt files are IDE-only, skills work everywhere, custom agents vary, and the CLI has its own config tree under `~/.copilot`.

### Decision

Target VS Code Copilot and the cloud coding agent. Copilot CLI is out of scope.

### Rationale

The user selected these two surfaces. VS Code is the daily IDE surface (and where localml lands); the cloud agent gives autonomous PR-producing runs. The CLI duplicates what Claude Code already does better in the terminal.

### Alternatives Considered

- **All three surfaces including CLI**: Maximum coverage - Rejected by user; CLI adds config surface without adding a needed capability.
- **VS Code only**: Simplest - Rejected; the PRD lane's "leave an agent to its work" goal fits the cloud coding agent.

### Consequences

**Positive:**
- Prompt files and VS Code-native discovery (including `~/.claude/skills`) are usable
- No dependency on Copilot CLI symlink quirks

**Negative:**
- No terminal Copilot workflow; cloud-agent assets must be repo-level, which the per-repo tooling has to seed

---

## Decision 4: Fix Drifted Repos Now, Plus Ship the Tooling

**Date**: 2026-07-04
**Status**: accepted

### Context

rtob and sanarte reference `/Users/ronan/go/bin/mcp-devtools` (stale username), sanarte's `.vscode/mcp.json` is invalid JSON, and rtob/workscripts carry duplicated copied-in agent packs.

### Decision

Ship a lint/sync command in agentic-coding and run it across the affected repos (rtob, sanarte, workscripts, betscraper, template, agentic-coding) as implementation tasks.

### Rationale

User choice. Tooling without the cleanup leaves known-broken configs in place; the cleanup validates the tooling.

### Alternatives Considered

- **Tooling + runbook only**: Less cross-repo churn in this feature - Rejected; stale configs would persist indefinitely.
- **Template repo only**: Minimal - Rejected; existing repos would keep drifting.

### Consequences

**Positive:**
- No stale-user paths or invalid configs survive the feature
- The tool is proven against real drift before being relied on

**Negative:**
- Implementation tasks touch repositories outside agentic-coding

---

## Decision 5: PRD Is an Alternative Lane, Not a Starwave Integration

**Date**: 2026-07-04
**Status**: accepted

### Context

The original idea was PRD as an optional framing layer that specs link to. When asked where PRDs should live and how linkage works, the user redirected: a PRD is an alternative approach to spec-driven development, not something threaded through the process.

### Decision

The PRD lane is: write one PRD document, then leave a coding agent to run it to completion. Implementation derives rune task files separated per application/code context and executes them in parallel via make-it-so or orbit. PRDs are written so specs can be derived from them, but no explicit end-to-end linkage or tooling integration exists.

### Rationale

Direct user steering: "we just want to be able to write 1 document, and leave a coding agent to its work until complete. Where it DIFFERS is the implementation… use rune to create tasks files, separated logically per the application or code context, and then implemented in parallel with make it so or orbit."

### Alternatives Considered

- **PRDs under `specs/prd/` with bidirectional spec links**: Original proposal - Rejected by user; adds tooling integration the lane doesn't need.
- **PRD as its own spec folder type**: Blurs the one-folder-one-feature rule - Rejected with the same reasoning.

### Consequences

**Positive:**
- The PRD lane stays simple: one document in, completed work out
- No new cross-document linkage conventions to maintain

**Negative:**
- No tooling-enforced traceability from PRD to derived specs/tasks; discipline lives in the PRD's writing style

---

## Decision 6: Canonical MCP Set Is All Seven Servers

**Date**: 2026-07-04
**Status**: accepted

### Context

MCP definitions are scattered across four config shapes with different subsets: devtools (Claude), devtools/svelte/azure/terraform/awesome-copilot/github (VS Code user), per-repo variants, and an empty `~/.copilot/mcp-config.json`.

### Decision

The canonical set is devtools, svelte, github, transit, azure, terraform, and awesome-copilot, defined once in agentic-coding and generated into every tool's shape.

### Rationale

User selected all offered servers. Transit's MCP server is part of the workflow ecosystem even though transit-driven skills were idle in the mined window.

### Alternatives Considered

- **Core three only (devtools, svelte, github)**: Matches observed active use - Rejected by user; infra and Transit servers belong in the canonical set even if per-repo subsets exclude them.

### Consequences

**Positive:**
- One place to update a server definition
- Per-repo subsetting still keeps project configs lean

**Negative:**
- Canonical file carries servers (azure, terraform) that most repos will not select

---

## Decision 7: Bootstrap Scope — Dependencies, MCP Generation, VS Code Seeding; No Doctor Command

**Date**: 2026-07-04
**Status**: accepted

### Context

"Clone → symlink → authenticate" needs a defined boundary for what the script automates versus what stays manual.

### Decision

The bootstrap script installs CLI dependencies (rune, mcp-devtools, uv, gh, node/npx, podman), creates all symlinks, generates all MCP configs, and seeds VS Code settings including the localml provider runbook. Authentication remains manual and is listed at the end. A doctor-style verification command is out of scope.

### Rationale

User selected dependency install, MCP generation, and VS Code/localml seeding; did not select the verify/report option.

### Alternatives Considered

- **Symlinks only (current sync-claude.sh scope)**: Simplest - Rejected; fails the "restart on a new machine" goal.
- **Including a doctor command**: Better diagnostics - Not selected; deferred.

### Consequences

**Positive:**
- A new machine reaches working state with one script plus sign-ins

**Negative:**
- No automated post-setup verification; failures surface on first use

---

## Decision 8: Copilot Port Depth — PRD Lane Only

**Date**: 2026-07-04
**Status**: accepted

### Context

The gated starwave lane could be ported to Copilot at varying depth: full gates + sendit + rune flow, spec authoring only, or nothing beyond the PRD lane.

### Decision

Copilot gets the PRD lane only: PRD authoring and autonomous execution. All gated spec authoring (requirements/design/tasks, sendit, explain-like) stays in Claude Code. The stale `copilot/prompts/` gated-lane ports are removed or replaced accordingly.

### Rationale

User choice. Claude Code remains the full-fidelity home; Copilot's value here is the autonomous executor for PRD-framed work, not a second gated workflow to maintain.

### Alternatives Considered

- **Full gated lane in Copilot**: Toolset parity - Rejected; heavy adaptation (no AskUserQuestion, different subagent model) for a workflow the user runs in Claude Code anyway.
- **Spec phases + PRD lane**: Middle ground - Rejected; same maintenance burden concern for the authoring phases.

### Consequences

**Positive:**
- Small, maintainable Copilot asset set aligned with actual usage
- Clear division: gated work in Claude Code, autonomous PRD work in either tool

**Negative:**
- No spec authoring in Copilot; a machine without Claude Code cannot run the gated lane

---

## Decision 9: Cloud Agent Role — Author Plus Native Execution

**Date**: 2026-07-04
**Status**: accepted

### Context

Design-critic review (validated by self-review; external peer reviewers unavailable — gemini CLI absent, codex unauthenticated) found the PRD execution lane infeasible on the cloud coding agent as written: make-it-so is a Claude Code skill, and rune/orbit are local binaries GitHub's sandbox cannot obtain without published artifacts and `copilot-setup-steps.yml`.

### Decision

PRDs are authored on all three surfaces. Rune-derived task files and make-it-so/orbit execution run locally only. The cloud coding agent MAY execute a PRD directly through its native loop, producing a pull request, with no rune orchestration guarantee.

### Rationale

Preserves the "leave an agent to its work" value on the cloud surface without taking on publishing orbit, building a Copilot-native executor, and maintaining sandbox setup steps in this feature.

### Alternatives Considered

- **Author-only in cloud**: Simplest - Rejected; drops the autonomous cloud-run value that motivated including the surface.
- **Full cloud execution**: Publish rune + orbit, add copilot-setup-steps.yml, build a Copilot-native executor - Rejected as significantly more work than the lane needs now.

### Consequences

**Positive:**
- Honest capability statement per surface; no infeasible ACs
- Cloud runs still produce reviewable PRs from a PRD

**Negative:**
- Cloud executions lose rune's stable task tracking and stream parallelism

---

## Decision 10: Nothing Is Generated or Installed Under `~/.copilot/`

**Date**: 2026-07-04
**Status**: accepted

### Context

The draft generated `~/.copilot/mcp-config.json` and replaced `~/.copilot/agents/prd.agent.md`, but those paths are Copilot CLI configuration and the CLI is a declared non-goal — a contradiction flagged by both reviews.

### Decision

Drop all `~/.copilot/` targets. The versioned PRD agent in this repository supersedes the unversioned `~/.copilot/agents/prd.agent.md`, which is deleted. MCP generation targets Claude Code, VS Code, and per-repo shapes only.

### Rationale

Maintaining config for a surface we refuse to support is drift by another name — the exact failure mode this feature exists to eliminate.

### Alternatives Considered

- **Keep generating for incidental CLI use**: Amend the non-goal - Rejected by user; unsupported means unsupported.

### Consequences

**Positive:**
- Non-goal and generation targets agree; one fewer config tree to manage

**Negative:**
- If Copilot CLI is adopted later, its config becomes a new feature

---

## Decision 11: One PRD Targets Exactly One Repository

**Date**: 2026-07-04
**Status**: accepted

### Context

"Separated by application or code context" left open whether a PRD could span repositories, which would break make-it-so (single-repo) and complicate where task files land.

### Decision

One PRD targets one repository; contexts are applications/modules within it, and derived task files land in that repository's `specs/` tree. Multi-repo efforts use one PRD per repo.

### Rationale

Keeps both local executors valid (make-it-so and orbit), keeps task-file placement unambiguous, and matches how the specs convention already works.

### Alternatives Considered

- **PRD may span repos**: One document for a product-wide effort - Rejected; only orbit could execute it, and task-file placement/reporting becomes multi-repo bookkeeping the lane doesn't need.

### Consequences

**Positive:**
- Unambiguous layout; both executors work on every PRD

**Negative:**
- Product-wide efforts need several PRDs kept consistent manually

---

## Decision 12: MCP Source of Truth Is JSON, Generator Is Python Stdlib

**Date**: 2026-07-04
**Status**: accepted

### Context

The canonical MCP file needs a format and the generator an implementation; the bootstrap must not depend on anything it hasn't installed yet.

### Decision

Canonical definitions live in `mcp/servers.json`; `scripts/generate.py` and `scripts/align.py` are Python 3 stdlib scripts (no third-party dependencies).

### Rationale

JSON round-trips losslessly into every target shape, python3 ships with macOS developer tooling, and stdlib-only keeps generation runnable at bootstrap time before uv/brew complete.

### Alternatives Considered

- **YAML + PyYAML via uv**: Comments and nicer hand-editing - Rejected; adds a dependency into the bootstrap path.
- **Bash + jq**: Matches sync-claude.sh style - Rejected; per-target secret mapping and idempotent JSON merging are painful and hard to test in shell.

### Consequences

**Positive:**
- Testable with stdlib unittest and golden files; no install ordering issues

**Negative:**
- No comments in the canonical file (mitigated by a `_comment` convention if needed)

---

## Decision 13: Conventions Use a Shared Fragment Plus Per-Tool Wrappers

**Date**: 2026-07-04
**Status**: accepted

### Context

Requirement 3.3 needs the core conventions maintained once and produced into both `claude/CLAUDE.md` and the Copilot instructions, with Claude-only material excluded from the Copilot output.

### Decision

`shared/conventions.md` holds the shared content; `shared/claude-wrapper.md` and `shared/copilot-wrapper.md` hold tool-specific text; `generate.py` assembles both outputs, which are checked in as generated files.

### Rationale

User choice over the marker-stripping alternative. Wrappers make tool-specific content structurally impossible to leak into the other tool's output — exclusion by construction rather than by marker discipline.

### Alternatives Considered

- **Markers in CLAUDE.md**: One file to edit - Rejected by user; stripping correctness depends on marker hygiene, and a missed marker silently leaks Claude-isms to Copilot.

### Consequences

**Positive:**
- Clean separation; generation is trivial concatenation

**Negative:**
- Editing conventions now touches `shared/` plus a regenerate step, not `CLAUDE.md` directly

---

## Decision 14: Per-Repo Configuration Declared in a Checked-In `.agentic.json`

**Date**: 2026-07-04
**Status**: accepted

### Context

The alignment command needs to know which canonical servers and cloud assets each repository wants, on every run, on every machine.

### Decision

Each repo carries a small `.agentic.json` (`servers` subset, `cloud_assets` flag). First run infers defaults from `default_for` rules in the canonical file and writes the manifest for the user to commit.

### Rationale

User choice. Selections survive machines and reruns, are reviewable in the repo's history, and make align runnable with no arguments.

### Alternatives Considered

- **CLI flags per run**: No repo state - Rejected; choices aren't remembered, defeating idempotent re-alignment.
- **Pure inference**: Zero config - Rejected; heuristic changes would silently alter generated configs.

### Consequences

**Positive:**
- Deterministic aligns; the manifest doubles as documentation of intent

**Negative:**
- One more dotfile per repo

---

## Decision 15: Managed-Block Markers Are the Universal Provenance Mechanism

**Date**: 2026-07-04
**Status**: accepted

### Context

Design-critic review found two blockers with a common root: align could not distinguish a file it seeded from a hand-written one, and Claude Code's `#`-memory feature appends to `~/.claude/CLAUDE.md` — which becomes a generated file — so regeneration would silently destroy memories. Both need a way to mark which part of a file the tooling owns.

### Decision

Every generated or seeded file wraps tool-owned content in `<!-- agentic:begin -->` / `<!-- agentic:end -->` markers. Generators and align rewrite only the block; content outside it is preserved verbatim. A pre-existing target file without markers is treated as hand-written: reported and skipped, never overwritten.

### Rationale

One mechanism covers regeneration safety, seeded-file convergence, repo-local additions, and the hand-written-file guard — instead of four ad-hoc rules. Presence of the markers doubles as provenance.

### Alternatives Considered

- **Checksum list of seeded versions**: Detects drift but cannot merge local additions - Rejected; every user edit would force a backup-and-reseed cycle, breaking idempotence in practice.
- **Full-file ownership with a header comment**: Simplest - Rejected; destroys Claude memory appends and forbids repo-local instruction additions by accident.

### Consequences

**Positive:**
- Regeneration and re-alignment are safe against both tool-written and human-written additions
- Idempotence holds even on files users have extended

**Negative:**
- Marker discipline is load-bearing; a deleted marker demotes a file to hand-written (surfaced by report, but converging it again needs manual re-add)

---

## Decision 16: Nextup Becomes an Autonomous Dispatcher

**Date**: 2026-07-04
**Status**: accepted

### Context

Nextup was designed as a dispatcher that routes work into the gated starwave lane. During this feature's rollout the user redefined nextup.md's primary purpose: think outside Claude, write the commands, enter — with instructions treated like any prompt. Forcing the starwave/PRD process when the job doesn't call for it is overkill, and the human-in-the-loop gates block fanning out parallel development attempts for testing.

### Decision

Nextup executes or dispatches user-zone instructions directly, reads PRDs (routing them to the execution lane), and — when an act-autonomously flag is set in the user zone — prefers the ungated lane end-to-end. The gated lane becomes a recommendation for feature-shaped work, never an enforcement (Requirement 10).

### Rationale

Direct user steering. The spec-driven gates exist to keep a human in the loop, which remains the default preference for feature work, but must not be the only path — autonomous parallel runs need an ungated route from a single written instruction.

### Alternatives Considered

- **Keep nextup dispatcher-only, add a separate autonomous entry skill**: Preserves nextup's routing purity - Rejected; nextup.md is exactly where the user writes instructions between sessions, so splitting the entry point defeats its purpose.
- **Autonomy as the default, gates opt-in**: Maximum autonomy - Rejected; the user explicitly called the human-in-the-loop gating "good for now" as the default for feature work.

### Consequences

**Positive:**
- One entry point covers gated, direct, and autonomous work
- Parallel fan-out experiments can start from a single nextup.md instruction

**Negative:**
- Nextup's routing rules grow more complex; misreading intent now has an ungated failure mode (mitigated by requiring the explicit flag for autonomy)

---
