---
references:
    - requirements.md
    - design.md
    - decision_log.md
---
# Toolset-Agnostic Starwave Implementation

## Implementation

- [ ] 1. Write golden-fixture tests for conventions assembly <!-- id:rv5n0l9 -->
  - Fixtures: shared fragments in, expected claude/CLAUDE.md and copilot/instructions/copilot-instructions.md out
  - Assert Copilot output contains no claude-wrapper content and no Claude-tree paths (rules/references, .claude/scripts)
  - Assert content outside <!-- agentic:begin/end --> markers survives regeneration (Claude memory-append case)
  - Stream: 1
  - Requirements: [3.3](requirements.md#3.3)

- [ ] 2. Author shared/ fragments by splitting claude/CLAUDE.md <!-- id:rv5n0la -->
  - shared/conventions.md (tool-neutral), shared/claude-wrapper.md (AskUserQuestion contract, skill routing, Claude-tree path references), shared/copilot-wrapper.md (PRD-lane preamble)
  - conventions.md contract: no skill names, no AskUserQuestion, no Claude-tree file paths
  - Stream: 1
  - Requirements: [3.3](requirements.md#3.3)

- [ ] 3. Implement conventions assembly in scripts/generate.py <!-- id:rv5n0lb -->
  - Managed-block writer implemented as shared library code - align.py reuses it
  - Generated outputs are checked in; make lint fails when they drift from sources
  - Blocked-by: rv5n0l9 (Write golden-fixture tests for conventions assembly), rv5n0la (Author shared/ fragments by splitting claude/CLAUDE.md)
  - Stream: 1
  - Requirements: [3.3](requirements.md#3.3)

- [ ] 4. Write tests for MCP config generation <!-- id:rv5n0lc -->
  - Golden outputs per target: Claude user config, VS Code user mcp.json, .mcp.json, .vscode/mcp.json, cloud paste-ready JSON
  - Failure case: secret with no mechanism for a target aborts naming server and target
  - Preservation: non-canonical entries and unrelated ~/.claude.json keys untouched; invalid target JSON gets .bak plus warning that non-canonical entries may be in the backup
  - Stream: 1
  - Requirements: [4.2](requirements.md#4.2), [4.3](requirements.md#4.3), [4.5](requirements.md#4.5)

- [ ] 5. Create mcp/servers.json with the canonical seven servers <!-- id:rv5n0ld -->
  - devtools, svelte, github, transit, azure, terraform, awesome-copilot with transport, secrets, surfaces, default_for per design schema
  - Commands are PATH-resolved bare names, never absolute user paths
  - default_for grammar: marker-file globs; literal * means always included
  - Stream: 1
  - Requirements: [4.1](requirements.md#4.1)

- [ ] 6. Implement MCP generation in scripts/generate.py <!-- id:rv5n0le -->
  - Prefer claude mcp add-json --scope user when the CLI is on PATH (avoids racing a running Claude Code); direct managed merge as fallback
  - Cloud-agent paste-ready emission is library code consumed by align --cloud-mcp
  - Blocked-by: rv5n0lc (Write tests for MCP config generation), rv5n0ld (Create mcp/servers.json with the canonical seven servers)
  - Stream: 1
  - Requirements: [4.2](requirements.md#4.2), [4.3](requirements.md#4.3), [4.4](requirements.md#4.4), [4.5](requirements.md#4.5)

- [ ] 7. Write tests for VS Code settings merge <!-- id:rv5n0lf -->
  - Merge preserves unrelated keys; handles JSONC (comments, trailing commas) conservatively - unparseable settings.json is backed up and reported, never clobbered
  - Seeds chat.instructionsFilesLocations pointing at copilot/instructions/ and the localml entry under github.copilot.chat.customOAIModels (baseUrl http://127.0.0.1:8080/v1, placeholder model id)
  - chat.useClaudeMdFile must NOT be enabled - it would deliver the Claude wrapper to Copilot
  - Stream: 1
  - Requirements: [7.1](requirements.md#7.1), [7.2](requirements.md#7.2), [3.4](requirements.md#3.4)

- [ ] 8. Implement VS Code settings merge in generate.py --user <!-- id:rv5n0lg -->
  - Same managed-merge discipline as MCP targets; bootstrap delegates all JSON work here
  - Blocked-by: rv5n0lf (Write tests for VS Code settings merge)
  - Stream: 1
  - Requirements: [7.2](requirements.md#7.2), [3.4](requirements.md#3.4)

- [ ] 9. Write align drift-class fixture tests <!-- id:rv5n0lh -->
  - One fixture repo per class: stale user path, invalid JSON, drifted canonical MCP entry, stale agent pack, missing cloud assets, seeded file with local additions outside the managed block, markerless hand-written file
  - Idempotence property: second applying run reports zero changes on every fixture
  - First run with no .agentic.json writes the manifest and prints the plan without applying
  - Stream: 2
  - Requirements: [5.1](requirements.md#5.1), [5.2](requirements.md#5.2), [5.3](requirements.md#5.3), [6.1](requirements.md#6.1)

- [ ] 10. Generate scripts/stale-packs.json from the drifted repos <!-- id:rv5n0li -->
  - SHA-256 of the actual pack file bytes in ~/repos/rtob/.github/agents and ~/repos/workscripts/.github/agents
  - align warns when .github/agents has files but zero checksum matches (near-miss must not silently no-op)
  - Stream: 2
  - Requirements: [5.1](requirements.md#5.1)

- [ ] 11. Implement scripts/align.py <!-- id:rv5n0lj -->
  - Pipeline order: JSON validity, path portability, MCP convergence, stale-pack deletion, cloud seeding with managed blocks
  - Manifest inference from default_for; --yes applies on first run; --cloud-mcp prints paste-ready JSON with COPILOT_MCP_* secret names
  - Touches managed files only (design Data Models list); refuses non-git directories
  - Blocked-by: rv5n0le (Implement MCP generation in scripts/generate.py), rv5n0lh (Write align drift-class fixture tests), rv5n0li (Generate scripts/stale-packs.json from the drifted repos)
  - Stream: 2
  - Requirements: [5.1](requirements.md#5.1), [5.2](requirements.md#5.2), [5.3](requirements.md#5.3), [4.4](requirements.md#4.4), [6.1](requirements.md#6.1), [6.2](requirements.md#6.2)

- [x] 12. Write claude/skills/prd/SKILL.md authoring skill <!-- id:rv5n0lk -->
  - Sections per design: product summary, goals/non-goals, functional requirements grouped per context H2, acceptance criteria, execution notes (quality gates, STOP)
  - Adapted from the old prd.agent.md outline; drop personas/metrics boilerplate and the GitHub-issue step
  - Output specs/{prd-name}/prd.md; one PRD targets one repository
  - Stream: 3
  - Requirements: [1.1](requirements.md#1.1), [1.2](requirements.md#1.2), [1.3](requirements.md#1.3)

- [x] 13. Write claude/skills/engage/SKILL.md execution skill <!-- id:rv5n0ll -->
  - Derive: per-context tasks-{context}.md via rune create/batch with phases+streams, slug rule, STOP tasks from execution notes, skip existing files, abort on slug collision
  - Execute: worktree .claude/worktrees/prd-{prd}-{context}, branch prd/{prd}-{context}, inner stream branches stream/{context}-<phase>-<N>
  - STOP protocol: subagent returns blocked-at-STOP; interactive gate vs --headless blocked report
  - Integrate: merge context branches in completion order, conflicts stop-and-report, quality gates rerun on integrated branch, single PRD-level changelog entry written by engage
  - Orbit path documented: one orbit process per context, each in its own worktree (.orbit/run.lock is per checkout)
  - Stream: 3
  - Requirements: [2.1](requirements.md#2.1), [2.2](requirements.md#2.2), [2.3](requirements.md#2.3), [2.4](requirements.md#2.4), [2.5](requirements.md#2.5), [2.6](requirements.md#2.6), [2.7](requirements.md#2.7)

- [x] 14. Write copilot/agents/prd.agent.md and delete stale copilot/prompts <!-- id:rv5n0lm -->
  - .agent.md frontmatter (name, description, tools) instructing the prd skill outline
  - Delete all 8 files under copilot/prompts/ including design-critic.chatmode.md
  - Blocked-by: rv5n0lk (Write claude/skills/prd/SKILL.md authoring skill)
  - Stream: 3
  - Requirements: [1.4](requirements.md#1.4), [3.2](requirements.md#3.2), [1.1](requirements.md#1.1)

- [ ] 15. Add Brewfile and Makefile <!-- id:rv5n0ln -->
  - Brewfile: gh, uv, node, podman, go, arjenschwarz/rune/rune, codex CLI, visual-studio-code cask
  - Makefile targets: generate, sync, align, lint (shellcheck + generated-drift + conventions checks), test
  - Stream: 4
  - Requirements: [8.1](requirements.md#8.1)

- [ ] 16. Extend scripts/sync-claude.sh with VS Code profile links and compat check <!-- id:rv5n0lo -->
  - Adds symlink: VS Code User/prompts/prd.agent.md -> copilot/agents/prd.agent.md; mkdir -p targets first
  - Existing six link targets unchanged; test asserts the link map and pre-feature skill directory names (Req 9.1)
  - chat.agentFilesLocations fallback documented if profile discovery fails - verify during implementation
  - Stream: 4
  - Requirements: [3.1](requirements.md#3.1), [3.4](requirements.md#3.4), [9.1](requirements.md#9.1)

- [ ] 17. Implement scripts/bootstrap.sh <!-- id:rv5n0lp -->
  - Order per design; no JSON manipulation in shell - delegates to generate.py (Decision 12 rationale)
  - --dry-run flag; unauthenticated steps skip with report and land on the manual list
  - Manual list: gh auth login, claude login, Copilot sign-in, GitHub MCP token, codex login (restores peer review), optional gemini CLI install; ends with re-run bootstrap.sh after authenticating
  - Removes ~/.copilot/agents/prd.agent.md if present, reported
  - Blocked-by: rv5n0lg (Implement VS Code settings merge in generate.py --user), rv5n0ln (Add Brewfile and Makefile), rv5n0lo (Extend scripts/sync-claude.sh with VS Code profile links and compat check)
  - Stream: 4
  - Requirements: [8.1](requirements.md#8.1), [8.2](requirements.md#8.2), [8.3](requirements.md#8.3), [8.4](requirements.md#8.4), [1.4](requirements.md#1.4)

- [ ] 18. Write docs/runbooks/localml-vscode.md <!-- id:rv5n0lq -->
  - Step-by-step exact values only: start command, Manage Language Models fields, placeholder API key, model picking
  - References the seeded settings entry as the already-done part
  - Stream: 5
  - Requirements: [7.1](requirements.md#7.1), [7.2](requirements.md#7.2)

- [ ] 19. Write docs/runbooks/cloud-agent-mcp.md <!-- id:rv5n0lr -->
  - Applying align --cloud-mcp output in github.com repo settings; COPILOT_MCP_* Actions-secret naming in the copilot environment
  - Blocked-by: rv5n0lj (Implement scripts/align.py)
  - Stream: 5
  - Requirements: [6.2](requirements.md#6.2)

- [ ] 20. Update README.md and spec-workflow.md for the new layout <!-- id:rv5n0ls -->
  - Document shared/, mcp/, copilot/agents, the PRD lane, and the clone -> bootstrap -> authenticate quickstart
  - Remove references to the deleted copilot/prompts files
  - Blocked-by: rv5n0lj (Implement scripts/align.py), rv5n0lm (Write copilot/agents/prd.agent.md and delete stale copilot/prompts), rv5n0lp (Implement scripts/bootstrap.sh)
  - Stream: 5
  - Requirements: [3.1](requirements.md#3.1), [3.2](requirements.md#3.2)

## Rollout & Verification

- [ ] 21. Run align across the six repos and commit the fixes <!-- id:rv5n0lt -->
  - rtob, sanarte, workscripts, betscraper, template, agentic-coding; review each inferred .agentic.json before --yes
  - Expected outcomes: /Users/ronan paths portable, sanarte .vscode/mcp.json valid, stale packs removed, cloud assets seeded where opted in
  - Verify the second run reports no changes in every repo
  - Blocked-by: rv5n0lj (Implement scripts/align.py)
  - Requirements: [5.3](requirements.md#5.3)

- [ ] 22. Run bootstrap on this machine and verify idempotence <!-- id:rv5n0lu -->
  - Second run must report no changes (AC 8.2)
  - Verify VS Code discovers the PRD agent and skills; ~/.copilot/agents/prd.agent.md removed
  - Existing ~/.claude symlinks and skill names unchanged
  - Blocked-by: rv5n0lp (Implement scripts/bootstrap.sh)
  - Requirements: [8.2](requirements.md#8.2), [8.3](requirements.md#8.3), [9.1](requirements.md#9.1)

- [ ] 23. Execute the PRD-lane worked example in a scratch repo <!-- id:rv5n0lv -->
  - PRD with at least two contexts each having streams - exercises the context-qualified branch naming
  - Include one STOP task; verify blocked-at-STOP behaviour in --headless mode and the integrated-branch quality gate
  - Blocked-by: rv5n0ll (Write claude/skills/engage/SKILL.md execution skill), rv5n0lm (Write copilot/agents/prd.agent.md and delete stale copilot/prompts)
  - Requirements: [1.1](requirements.md#1.1), [2.1](requirements.md#2.1), [2.2](requirements.md#2.2), [2.3](requirements.md#2.3), [2.5](requirements.md#2.5), [2.6](requirements.md#2.6), [2.7](requirements.md#2.7)
