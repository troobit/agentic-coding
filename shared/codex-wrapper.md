# Codex Instructions

These instructions apply to Codex CLI, the Codex IDE extension, and Codex in the ChatGPT desktop app.

## Skill Usage

Use the Agent Skills linked into `~/.agents/skills` when the user's request matches a skill description. The skills are sourced from this repository's `claude/skills/` tree; when a skill mentions a host-specific mechanism that Codex does not expose, preserve the workflow intent and use the nearest Codex-native tool or ask for the missing input.

## Starwave

The Starwave specification workflow is available as `starwave:*` skills. Continue existing specs in place, keep requirements/design/tasks/decision-log files self-contained, and record any portability assumptions in the spec before implementing them.
