# REA Feature Discovery

Spec: [rea-feature-discovery](../../specs/rea-feature-discovery/requirements.md).
Implementation: [SKILL.md](../../claude/skills/rea-feature-discovery/SKILL.md),
with conditional setup and handoff references plus Codex UI metadata.

`mcp/servers.json` pins the local stdio server to `rea-agents@6.7.0`, without a
cloud surface or wildcard project default. `make sync-codex` registers it and
links the skill into `~/.agents/skills`; Claude's existing whole-directory skills
link exposes the same source. A fresh native Codex app-server discovered the
enabled skill and all 207 REA tools. A second sync left config bytes unchanged.
The current running agent may need reconnect/restart to gain the new MCP tools.

Invoke with `$rea-feature-discovery` in Codex or `/rea-feature-discovery` in Claude
Code, supplying the source app, selected feature/question, and destination repo.
The skill ends at Starwave planning unless implementation was also requested.

This repository owns the reusable investigation and Starwave handoff. A
destination app owns its product research and specs. Libre-specific starting
context lives in the `medata` repository at `docs/research/libre-rea.md`, alongside
existing Libre ingestion, CGM Connect, and CGM Direct work. Do not recreate a
Libre product spec in this repository.

REA already supplies the `reverse-engineer-anything` skill and an
`investigate_feature` MCP prompt. The prompt renders guidance and does not run
tools. The skill adds destination selection, durable evidence, adaptation, and
Starwave continuation. Its setup reference is loaded only for missing/failed
access, so a healthy investigation does not repeatedly run diagnostics. CLI
fallback preserves genuine REA Evidence without claiming the client's MCP
connection worked.

MCP transport readiness, source access, and analysis-provider readiness are
separate facts. A target-free health check proves no access to an installed
phone app. REA session-only references also need exported evidence or explicit
unavailable status before another planning session can rely on the findings.
