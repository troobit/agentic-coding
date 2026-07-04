# GitHub Copilot Instructions

These instructions apply to GitHub Copilot in VS Code and to the cloud coding agent.

## PRD Lane

Autonomous work is framed as a PRD: one document targeting exactly one repository, written so tasks can be derived from it without returning to the author.

- Author PRDs with the `prd` custom agent (or by following the `prd` skill's outline). Output goes to `specs/{prd-name}/prd.md` in the target repository.
- A PRD contains goals, non-goals, functional requirements grouped by application or code context (one H2 per context, with numbered MUST/SHOULD requirements and acceptance criteria), and execution notes. No personas or metrics boilerplate unless asked.
- A PRD stands alone: it requires no linked spec or ticket.
- The cloud coding agent may execute a PRD directly through its native loop, producing a pull request. Respect the target repository's quality gates (Makefile build/test/lint where present) before declaring work complete.

The gated spec workflow (requirements/design/tasks approval gates) is not available here; it runs in Claude Code only.
