# Requirements: toolset-agnostic-starwave

## Introduction

This feature makes the agentic-coding repository the single source of truth for agent tooling across Claude Code, GitHub Copilot (VS Code and the cloud coding agent), and Codex. It adds a PRD lane — one document per target repository, from which rune task files are derived and executed autonomously — consolidates the scattered Copilot and per-repo configuration, codifies MCP server definitions in one place, exposes localml models to VS Code, and turns the repository into a complete new-machine bootstrap: clone, run one script, authenticate. The existing gated starwave workflow remains source-compatible with Claude Code while its Agent Skill instructions are made discoverable by Codex where the host supports the open `SKILL.md` format.

## Non-Goals

- The gated starwave lane (requirements/design/tasks approval gates, sendit, explain-like) is NOT ported to Copilot; it remains Claude Code only.
- Copilot CLI is not a supported surface; nothing is generated or installed under `~/.copilot/`.
- Cloud-agent PRD execution carries no rune/make-it-so orchestration guarantee; it uses the agent's native loop.
- A single PRD does not span multiple repositories; multi-repo efforts use one PRD per repo.
- No doctor-style verification command (deferred).
- No service management for localml; the user starts and stops the server.
- macOS (Apple Silicon) only; no Windows or Linux support.
- No functional changes to the PR-lifecycle or Transit skills beyond what config consolidation touches.
- No secret values stored in this repository or in generated configs.
- No Codex plugin packaging or remote skill upload; this feature uses local Agent Skill folders and symlinks only.

## Requirements

### 1. PRD Authoring Lane

**User Story:** As a developer, I want to frame a body of work as a single PRD document, so that a coding agent can take it to completion without further steering.

**Acceptance Criteria:**

1. <a name="1.1"></a>The system SHALL provide a PRD authoring workflow invocable from Claude Code, VS Code Copilot, and the cloud coding agent that produces exactly one PRD document targeting exactly one repository.
2. <a name="1.2"></a>The PRD document SHALL contain goals, non-goals, functional requirements grouped by application or code context within the target repository, and acceptance criteria, such that task files (or full specs) can be derived from it without returning to the author.
3. <a name="1.3"></a>A PRD SHALL stand alone: creating one SHALL NOT require a linked spec, ticket, or prior starwave phase.
4. <a name="1.4"></a>The PRD outline and authoring instructions SHALL be versioned in this repository, superseding the unversioned file at `~/.copilot/agents/prd.agent.md`, which is removed.

### 2. PRD Execution Lane

**User Story:** As a developer, I want a PRD turned into rune task files and implemented in parallel, so that the work completes autonomously.

**Acceptance Criteria:**

1. <a name="2.1"></a>WHEN a PRD is handed to the execution workflow, the system SHALL derive rune-managed task files separated by application or code context, stored alongside the PRD in the target repository's `specs/` tree.
2. <a name="2.2"></a>Derived task files SHALL conform to the rune tasks format, including the phase and stream structure the parallel executors require.
3. <a name="2.3"></a>The derived task files SHALL be executable in parallel, without modification, by the existing make-it-so flow and by orbit, both running locally.
4. <a name="2.4"></a>The cloud coding agent MAY execute a PRD directly through its native loop, producing a pull request; this path carries no rune orchestration guarantee.
5. <a name="2.5"></a>Local execution SHALL run to completion without approval gates. IF a task is prefixed `STOP —`, THEN in an interactive run execution SHALL pause for human verification, and in a headless run the task and its dependents SHALL be left not-started and reported as blocked.
6. <a name="2.6"></a>A context SHALL be reported complete only when all its rune tasks are complete, the target repository's quality gates (build, test, lint via the project's Makefile where present) pass, and the changes are committed. IF the repository has no Makefile, completion requires tasks complete and committed, and the report SHALL note that no quality gates ran.
7. <a name="2.7"></a>WHEN execution finishes, the workflow SHALL report which contexts completed and list any incomplete or blocked tasks.

### 3. Copilot Asset Consolidation

**User Story:** As the user, I want all Copilot agents, skills, and instructions versioned in this repository and installed via the same symlink pattern as the Claude assets, so that nothing lives only on one machine.

**Acceptance Criteria:**

1. <a name="3.1"></a>All Copilot customization assets (custom agents, instructions, skills) SHALL live under version control in this repository, and the user-level assets SHALL be installed by the sync script.
2. <a name="3.2"></a>The stale prompt files under `copilot/prompts/` that duplicate the gated starwave lane SHALL be removed or replaced by the PRD-lane assets.
3. <a name="3.3"></a>The core convention sections shared with `claude/CLAUDE.md` (communication style, development workflow, spec and rune conventions, decision-log format) SHALL be maintained in a single source from which both the Claude and Copilot instruction files are produced; Claude-only material (AskUserQuestion contract, skill routing) SHALL NOT appear in the Copilot output.
4. <a name="3.4"></a>WHEN the sync script has run on a machine, VS Code Copilot SHALL discover the user-level agents and skills without manual copying; repo-level discovery for the cloud coding agent is covered by Requirement 6.

### 4. MCP Single Source of Truth

**User Story:** As the user, I want MCP servers defined once and generated into every tool's config shape, so that definitions never drift between tools or machines.

**Acceptance Criteria:**

1. <a name="4.1"></a>The repository SHALL define the canonical MCP server set (devtools, svelte, github, transit, azure, terraform, awesome-copilot) in a single file, including which values are secret.
2. <a name="4.2"></a>A generation command SHALL produce the Claude Code user-level MCP config, the VS Code user `mcp.json`, and per-repo `.mcp.json` / `.vscode/mcp.json` from the canonical definitions.
3. <a name="4.3"></a>Generated configs SHALL contain no secret values; the generator SHALL emit each target's native secret-reference mechanism (environment-variable expansion for Claude Code, prompt inputs for VS Code), and generation SHALL fail with an error for a target that has no such mechanism for a required secret.
4. <a name="4.4"></a>Per-repo generation SHALL support selecting a subset of the canonical server set.
5. <a name="4.5"></a>Rerunning generation SHALL converge entries whose names are in the canonical set back to canonical; entries outside the canonical set SHALL be preserved and reported, never silently removed.
6. <a name="4.6"></a>The generation command SHALL produce Codex MCP configuration for the user-level `~/.codex/config.toml` and per-repo `.codex/config.toml` config shapes, preserving unrelated Codex settings.

### 5. Per-Repo Config Alignment

**User Story:** As the user, I want a command that brings any repository's agent configs into line, so that stale paths, invalid files, and drifted copies are corrected everywhere.

**Acceptance Criteria:**

1. <a name="5.1"></a>The command SHALL detect and fix: user-specific absolute paths (e.g. `/Users/ronan/...`), invalid JSON in agent/MCP config files, and canonical-named MCP definitions that diverge from the canonical set. Path fixes SHALL produce portable forms (`$HOME`-relative or PATH-resolved commands) that survive a username change, not a substitution of the current username.
2. <a name="5.2"></a>The command SHALL preserve non-canonical MCP entries and unmanaged files, and SHALL report each change it makes, per file.
3. <a name="5.3"></a>WHEN run against a repository containing any of the known drift classes (stale user paths, invalid JSON, drifted canonical MCP entries, duplicated agent packs, missing or stale cloud-agent assets per Requirement 6), a single invocation SHALL fix all instances, and an immediate second invocation SHALL report no changes.

### 6. Cloud Coding Agent Enablement

**User Story:** As the user, I want a repository prepared for the cloud coding agent in one step, so that PRD-lane work can be assigned on github.com without per-repo hand-setup.

**Acceptance Criteria:**

1. <a name="6.1"></a>The Requirement 5 alignment command SHALL seed the repo-level Copilot assets the cloud agent discovers: the PRD custom agent, the repo instructions file, and the skill directories the PRD lane needs. Existing hand-written files at those locations SHALL be handled per Requirement 8.4 semantics (preserve, back up, or report — never silently overwrite).
2. <a name="6.2"></a>WHERE the cloud agent needs MCP servers, the generation command SHALL emit a paste-ready cloud-agent MCP configuration plus a runbook covering its application in repository settings and the `COPILOT_MCP_*` Actions-secret naming; no API-writable delivery is required.

### 7. localml Models in VS Code

**User Story:** As a developer, I want localml-served models selectable in VS Code, so that local MLX models can drive editor AI features.

**Acceptance Criteria:**

1. <a name="7.1"></a>The repository SHALL provide the provider configuration and runbook such that, following it while localml is serving, the served model is selectable in VS Code's language-model picker.
2. <a name="7.2"></a>The bootstrap SHALL seed whatever part of the provider setup is file-writable; WHERE VS Code requires manual entry, the runbook SHALL give step-by-step exact values (URL form, placeholder API key, model id), not an explanation.

### 8. New-Machine Bootstrap

**User Story:** As the user, I want a new machine working by cloning this repo, running one script, and authenticating, so that setup requires no memory of past configuration.

**Acceptance Criteria:**

1. <a name="8.1"></a>A single script SHALL: create the Claude, Copilot, and Codex links, install the workflow's CLI dependencies (rune via its Homebrew tap, orbit via `go install`, mcp-devtools, uv, gh, node/npx, and podman for the container-based MCP servers), generate all MCP configs per Requirement 4, seed Codex and VS Code instruction/config files, and seed the required VS Code settings per Requirement 7. IF a dependency cannot be installed unauthenticated (e.g. a private clone before `gh auth login`), the script SHALL skip it with a report and add it to the remaining-steps list per Requirement 8.3.
2. <a name="8.2"></a>The script SHALL be idempotent: rerunning it on a configured machine SHALL make no destructive changes and SHALL leave a working setup.
3. <a name="8.3"></a>WHEN the script completes, it SHALL list the remaining manual authentication steps (gh auth login, Claude Code login, Copilot sign-in, MCP tokens).
4. <a name="8.4"></a>IF the script encounters an existing file it does not manage at a target location, it SHALL preserve that file (back up or skip with a report); within managed config files, only canonical-named entries are rewritten per Requirement 4.5.

### 9. Claude Code Backwards Compatibility

**User Story:** As the user, I want the existing Claude Code workflow untouched, so that daily work continues unchanged while the Copilot assets evolve.

**Acceptance Criteria:**

1. <a name="9.1"></a>After implementation: the sync script SHALL produce the same `~/.claude` symlink targets as today, no existing skill or slash-command SHALL be renamed, moved, or removed, and the gated starwave lane's skill content SHALL be functionally unchanged.

### 10. Nextup Autonomous Dispatch

**User Story:** As the user, I want nextup to act on my written instructions directly — including PRDs — so that a session started from nextup.md is not forced through the gated spec process.

**Acceptance Criteria:**

1. <a name="10.1"></a>WHEN the user zone contains instructions that do not call for spec work, nextup SHALL execute or dispatch them directly, as it would any prompt, without routing into the starwave lane.
2. <a name="10.2"></a>WHEN the user zone references a PRD (or a `specs/{name}/prd.md` exists for the named work), nextup SHALL route it to the PRD execution lane.
3. <a name="10.3"></a>WHEN an act-autonomously flag is present in the user zone, nextup SHALL prefer the ungated lane end-to-end (PRD derivation and execution, no approval gates), using gated-lane routing only when the user zone explicitly demands it.
4. <a name="10.4"></a>WHERE work is feature-shaped and no autonomy flag is set, nextup MAY recommend the gated lane, but SHALL NOT withhold direct execution when the user zone asks for it.

### 11. Codex Agent Skills Discovery

**User Story:** As the user, I want the Starwave and related skills discoverable by Codex from the same source as Claude Code, so that the specification-driven process is available in Codex without copied local files.

**Acceptance Criteria:**

1. <a name="11.1"></a>The sync workflow SHALL expose every top-level skill directory under `claude/skills/` to Codex through `~/.agents/skills/{skill-name}`.
2. <a name="11.2"></a>WHEN `~/.agents/skills/{skill-name}` already exists and is not a symlink to the repository skill, the sync workflow SHALL preserve it and report the conflict instead of overwriting it.
3. <a name="11.3"></a>WHEN the sync workflow is run repeatedly, Codex skill links that already point at repository skills SHALL remain unchanged and the run SHALL not create duplicate files or directories.
4. <a name="11.4"></a>The sync and bootstrap documentation SHALL describe Codex discovery through `~/.agents/skills`, including the fact that host-specific Claude mechanisms still depend on the host's available tools.
5. <a name="11.5"></a>The sync workflow SHALL keep the existing Claude Code link map unchanged while adding Codex links.
6. <a name="11.6"></a>The generation workflow SHALL produce Codex global instructions at `~/.codex/AGENTS.md` from the shared conventions plus a Codex-specific wrapper, preserving content outside the managed block.
