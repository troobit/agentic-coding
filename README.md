# Agentic Coding process

This repository contains my current process for working with agentic coding assistants. It's focused around spec-driven development and has a number of helpful tools and commands. Feel free to use what you see here and/or propose improvements.

The repository is the single source of truth for agent tooling across Claude Code, GitHub Copilot (VS Code and the cloud coding agent), and Codex: shared conventions and MCP server definitions are generated into each tool's config shape, portable Agent Skills are linked into each host's discovery path, and one bootstrap script sets up a new machine.

## New-Machine Quickstart

1. Clone this repository.
2. Run `scripts/bootstrap.sh` — installs Homebrew dependencies (Brewfile), Claude Code, orbit and mcp-devtools (`go install`), creates the symlinks, and generates the user-level MCP configs and VS Code settings.
3. Authenticate (the script prints this list at the end):
   - `gh auth login`
   - `claude` (log in on first run)
   - Sign in to GitHub Copilot in VS Code
   - `export GITHUB_AUTH_TOKEN="Bearer <PAT>"` for the github MCP server (the `Bearer ` prefix is required), and provide the same `Bearer <PAT>` value when a Copilot/VS Code MCP prompt asks for it
   - `codex login` (restores peer review); optionally install the gemini CLI for a second reviewer
4. Re-run `scripts/bootstrap.sh` to pick up anything that was skipped for missing authentication.

The script is safe to re-run: each step reports `did`, `already done`, or `skipped`, and on a fully configured machine a rerun makes no changes — every step reports `already done` and the config generation reports each managed target as already configured.

## Agents

The framework provides specialized AI agents for different aspects of development. These are defined for use in Claude Code, and not every tool supports sub-agents like this. Some agents have dependencies on external CLI tools (e.g., peer-review-validator requires Gemini CLI, Codex CLI, or Q Developer CLI for consulting external AI systems).

- **`code-simplifier`** - Reviews code for complexity reduction and maintainability improvements
- **`design-critic`** - Provides critical review of design documents and architecture proposals (now using Sonnet model for improved efficiency)
- **`efficiency-optimizer`** - Analyzes code for performance optimization opportunities
- **`local-review`** - Sonnet-powered local replacement for the `anthropics/claude-code-action` PR review step. Reviews an open PR (code quality, bugs, performance, security, test coverage, plus whatever the project's `CLAUDE.md` mandates) and posts a single `gh pr comment` instead of consuming private GitHub Actions minutes
- **`peer-review-validator`** - Validates decisions by consulting with at least two external AI systems (Gemini, Codex, or Q Developer) to ensure balanced perspective
- **`pre-push-code-reviewer`** - Critically reviews unpushed commits before pushing to ensure code quality and spec adherence
- **`research-agent`** - Conducts research and generates structured reports (stolen from @sammcj)
- **`ui-ux-reviewer`** - Evaluates user interfaces for usability and accessibility improvements

## Skills

The framework includes Claude Code skills for the complete feature development workflow (detailed in [spec-workflow](spec-workflow.md)), plus skills that sit alongside that workflow rather than inside it:

**Starwave Skills (Spec-Driven Development):**
- **`starwave:creating-spec`** - Main entry point that orchestrates the complete spec-driven workflow. Assesses scope, routes to appropriate workflow, and guides through all phases with built-in review gates.
- **`starwave:smolspec`** - Lightweight specification for minor changes (<80 LOC, 1-3 files)
- **`starwave:requirements`** - Generate and refine feature requirements in EARS format
- **`starwave:design`** - Create design documents based on approved requirements
- **`starwave:tasks`** - Convert designs into actionable implementation task lists

**Implementation Skills:**
- **`next-task`** - Execute the next group of tasks from the implementation plan
- **`make-it-so`** - Implement all remaining tasks from the spec automatically

**PRD Skill (not part of the gated starwave lane):**
- **`prd`** - Author a single standalone PRD document (`specs/{prd-name}/prd.md`) targeting exactly one repository, for a small project or a first MVP. Authoring only — there is no execution step

**Backlog Skill (outside the spec workflow, the tracked entry point for forward intent):**
- **`backlog`** - Capture loose ideas, note files, and audit findings into a tracked, rune-parseable `specs/BACKLOG.md`, route each item to where the work belongs — an existing spec's tasks, an existing spec's requirements, or the backlog itself — and clear the sources once filed. Use it bare, with free-form text, or with a named file path; it never commits.

**Utility Skills:**
- **`catchup`** - Get up to speed on branch changes by analyzing commits and modified files (inspired by [Shrivu Shankar](https://blog.sshh.io/p/how-i-use-every-claude-code-feature))
- **`commit`** - Format, stage, and commit changes with proper changelog management
- **`release-prep`** - Prepare the project for a new release with quality checks and documentation updates
- **`rune`** - Manages hierarchical task lists using the rune CLI tool. Provides efficient task creation, status tracking, phase organization, and batch operations for atomic updates.

Skills are invoked using slash commands (e.g., `/starwave:creating-spec`, `/commit`) and provide structured workflows with built-in approval gates.

## Workflow

The recommended way to start a new feature is with `/starwave:creating-spec`, which will:

1. Assess the scope of your feature
2. Route to either smolspec (small changes) or full spec workflow
3. Guide you through requirements → design → tasks phases
4. Offer to create a feature branch when planning is complete

Then implement using `/next-task` and commit with `/commit`.

Each phase requires explicit user approval before proceeding to ensure quality and alignment.

### PRDs

For a small project or a first MVP, `/prd` writes a single standalone PRD for one repository — one document describing the whole system. It is authoring only and closes out at the document; nothing derives a task file from it. Work that must react to change or growing complexity belongs in the starwave chain instead. See [spec-workflow](spec-workflow.md) for the split.

## File Structure

Top-level layout:

- `shared/` - Single-source conventions (`conventions.md`) plus the Claude, Copilot, and Codex wrapper fragments they are combined with
- `mcp/servers.json` - Canonical MCP server definitions, including which values are secret
- `claude/` - Claude Code configuration:
  - `claude/CLAUDE.md` - User-level instructions (generated from `shared/`, checked in)
  - `claude/agents/` - Specialized AI agents for different development tasks
  - `claude/skills/` - Skills for the development workflow (invoked via slash commands)
  - `claude/rules/` - Language rules and reference documentation formats, including the path-scoped `language-rules/styleguide-terraform.md` style guide
- `copilot/agents/prd.agent.md` - Custom agent wrapper for VS Code and the cloud coding agent
- `copilot/instructions/copilot-instructions.md` - Copilot instructions (generated from `shared/`, checked in)
- `codex/AGENTS.md` - Codex instructions (generated from `shared/`, checked in and also seeded to `~/.codex/AGENTS.md`)
- `scripts/bootstrap.sh` - One-script new-machine setup
- `scripts/generate.py` - Regenerates the instruction files and MCP configs from `shared/` and `mcp/servers.json`
- `scripts/align.py` - Brings any repository's agent configs into line (stale paths, invalid JSON, drifted MCP entries, cloud-agent assets)
- `Brewfile` / `Makefile` - Homebrew dependencies and the `generate` / `sync` / `align` / `lint` / `test` targets

Feature work is organized in `specs/{feature_name}/` directories containing:
- `requirements.md` - Feature requirements in EARS format
- `design.md` - Design document
- `tasks.md` - Implementation task checklist
- `decision_log.md` - Decisions and rationales

## GitHub Copilot Integration

The old `copilot/prompts/` prompt files are gone — the gated starwave lane is Claude Code only. Copilot integration now works through shared Agent Skills and generated assets:

- **VS Code Copilot** reads the Agent Skills from `~/.claude/skills` natively (the same symlink the sync script creates for Claude Code), and `sync-claude.sh` links `copilot/agents/prd.agent.md` into the VS Code profile's `User/prompts/` so the PRD agent appears in the agent picker.
- **Cloud coding agent** discovers repo-level assets that `scripts/align.py` seeds into a target repository: `.github/skills/` (the PRD-lane skills), `.github/agents/prd.agent.md`, and `.github/copilot-instructions.md`. MCP setup for the cloud agent is covered by [docs/runbooks/cloud-agent-mcp.md](docs/runbooks/cloud-agent-mcp.md).
- **Instructions** are generated: `copilot/instructions/copilot-instructions.md` is produced from `shared/conventions.md` plus the Copilot wrapper, so the core conventions stay in one source shared with `claude/CLAUDE.md`.

## Codex Integration

Codex discovers Agent Skills from `~/.agents/skills`. `scripts/sync-claude.sh` links each top-level directory under `claude/skills/` into that location individually, so Starwave, `rune`, `next-task`, and the related workflow skills are available to Codex from the same repository source.

The script does not replace `~/.agents/skills`; existing Codex/user-installed skills are preserved. If a target skill name already exists and does not point at this repository, sync reports the conflict and leaves it alone. Some skill bodies still mention Claude-specific tools or approval mechanisms, so Codex can follow the portable `SKILL.md` instructions while host-specific behavior depends on the tools available in the Codex session.

Codex instructions and MCP settings are generated too: `make generate` rebuilds the checked-in `codex/AGENTS.md`, `scripts/generate.py --user` writes managed blocks to `~/.codex/AGENTS.md` and `~/.codex/config.toml`, and `scripts/align.py <repo>` converges per-repo `.codex/config.toml` MCP tables while preserving unrelated Codex settings.

## Scripts Directory

The `scripts/` directory contains helper scripts for AI-assisted development:

- **`bootstrap.sh`** - One-script new-machine setup (see the quickstart above)
- **`sync-claude.sh`** - Syncs configuration from `claude/` to `~/.claude/`, links repo skills into Codex's `~/.agents/skills`, and links the PRD agent into the VS Code profile
- **`generate.py`** - Regenerates the instruction files and MCP configs from the canonical sources, including Codex `AGENTS.md` and `config.toml`
- **`align.py`** - Aligns a target repository's agent configs with the canonical sources, including `.codex/config.toml`

To set up your global Claude Code configuration on an already-bootstrapped machine, run:
```bash
./scripts/sync-claude.sh
```

This creates symlinks from `~/.claude/` pointing to the files in this repository's `claude/` directory and per-skill symlinks under `~/.agents/skills` for Codex, keeping your configuration centralized and version-controlled.

This framework is designed to work with Claude Code, GitHub Copilot (VS Code and the cloud coding agent), and Codex.

## GitHub Action

For CI/CD pipelines and automated workflows, you can use the included GitHub Action to set up Claude configuration in your workflows. This action symlinks all configuration directories to `~/.claude/` so Claude Code can access your custom agents, commands, language rules, scripts, and skills.

### Basic Usage

```yaml
steps:
  - name: Setup Claude Configuration
    uses: ArjenSchwarz/agentic-coding/.github/actions/setup-claude@main
```

### What It Does

The action automatically:
1. Checks out the `agentic-coding` repository
2. Creates symlinks from the repository's `claude/` directory to `~/.claude/`:
   - `claude/agents/` → `~/.claude/agents`
   - `claude/skills/` → `~/.claude/skills`
   - `claude/rules/` → `~/.claude/rules`
   - `claude/CLAUDE.md` → `~/.claude/CLAUDE.md`

### Advanced Usage

You can customize the action behavior with inputs:

```yaml
steps:
  - name: Setup Claude Configuration
    uses: ArjenSchwarz/agentic-coding/.github/actions/setup-claude@main
    with:
      ref: 'develop'  # Use a different branch or tag
      checkout-path: '.my-claude-config'  # Custom checkout path
```

### Complete Example

```yaml
name: CI with Claude Code

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Claude Configuration
        uses: ArjenSchwarz/agentic-coding/.github/actions/setup-claude@main

      - name: Run Claude Code
        run: |
          # Your Claude Code commands here
          # All custom agents, commands, etc. are now available
          claude --print "Analyze this codebase"
```

See [.github/actions/setup-claude/README.md](.github/actions/setup-claude/README.md) for complete documentation.

## CLAUDE.md Configuration

The `claude/CLAUDE.md` file contains user-level instructions that guide AI behavior when working with this framework. It is generated from `shared/conventions.md` plus `shared/claude-wrapper.md` (`make generate`); edit those sources, not the file itself. Key guidelines include:

- Emphasis on simplicity and understandable code
- Avoiding hyperbolic language and sycophantic responses
- Feature-based development using the specs directory structure
- Language-specific rules (e.g., Go development patterns in `claude/rules/language-rules/go.md`)
- Mandatory use of linters and validators after writing code

Run `./scripts/sync-claude.sh` to symlink these configurations to your global `~/.claude/` directory, or copy them to a project-specific `.claude/` directory.
