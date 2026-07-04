---
name: prd
description: Author a Product Requirements Document (PRD) for autonomous execution. Use when the user wants to frame a body of work as a single PRD that a coding agent can take to completion without further steering — e.g. "write a PRD for X", "frame this as a PRD", "PRD lane". NOT part of the gated starwave lane; do not use for features that need requirements/design/tasks approval gates.
---
<!-- agentic:begin -->
# PRD Authoring

Produce exactly one PRD document that a coding agent can execute to completion without returning to the author. The PRD is the alternative lane to spec-driven development: one document in, completed work out.

## Hard Rules

- **One PRD targets exactly one repository.** Contexts are applications or modules *within* that repository. Multi-repo efforts use one PRD per repo — offer to write them separately.
- **Output is a single file**: `specs/{prd-name}/prd.md` in the target repository. Nothing else is created — no task files, no GitHub issues, no linked spec or ticket.
- **A PRD stands alone.** Creating one MUST NOT require a linked spec, ticket, or prior starwave phase.
- **Derivability is the quality bar.** The PRD MUST be written so that rune task files (or full specs) can be derived from it by a fresh session without asking the author anything. If a requirement would need clarification at derivation time, it is not done.
- Do NOT include user personas, success-metrics boilerplate, milestones, or team-sizing sections unless the author explicitly asks for them.

## Transit (Optional)

When the user gives a `T-<id>` reference, or the target repo's `.agentic.json` sets `transit_project` and the user references a ticket: move the ticket to `planning` status via `mcp__transit__update_task_status` when authoring starts, with a comment (e.g. "Moving to planning — PRD authoring started"). The PRD lane has no spec gate, so `planning` is the only status the prd skill sets; the engage skill takes over from execution. Skip this entirely when no ticket applies — a PRD never requires one.

## Workflow

**1. Clarify.** Before writing anything, ask 3-5 clarifying questions to remove ambiguity. Ask them one at a time, concretely, describing observable behavior — not implementation jargon. Cover at minimum: the target repository, the applications/code contexts involved, what is explicitly out of scope, and any points where a human must verify before work continues.

**2. Research.** Explore the target repository to identify the applications/code contexts the work touches, existing patterns, and the project's quality gates (Makefile targets, test/lint commands).

**3. Name.** Propose a kebab-case `{prd-name}` and let the user override it. Check `specs/` in the target repo for collisions.

**4. Write.** Create `specs/{prd-name}/prd.md` following the outline below.

**5. Review.** Present the PRD and ask the user to confirm it before finishing. Do not implement anything — authoring ends at the document.

## PRD Outline

The file MUST use this structure. The reserved section headings (`Product summary`, `Goals`, `Non-goals`, `Execution notes`) are fixed; every other H2 is a **context heading** — one per application or code context in the target repository. The execution skill (engage) treats any non-reserved H2 as a context, so do not add extra prose H2s.

```markdown
# PRD: {title}

## Product summary

{2-3 short paragraphs: what this is, why it is needed, and the target repository.}

## Goals

- {Outcome-focused bullet list.}

## Non-goals

- {What will NOT be done. Be explicit — this is what stops scope creep during autonomous execution.}

## {Context name}

{One H2 per application or code context, e.g. "API server", "CLI", "Web frontend".
Context names should be short — they become task-file slugs (lowercased,
non-alphanumerics collapsed to `-`) and branch names. Two contexts must not
reduce to the same slug.}

{1-2 sentences scoping the context: which directories/modules it covers.}

1. The {context} MUST {requirement}.
   - Acceptance: {observable, testable criterion}
   - Acceptance: {another criterion if needed}
2. The {context} SHOULD {requirement}.
   - Acceptance: {observable, testable criterion}

## Execution notes

- Quality gates: {the target repo's build/test/lint commands — via its Makefile
  where present; state explicitly if the repo has no Makefile}.
- {Ordering constraints or cross-context dependencies, if any.}
- STOP — {human-verification point, if any: something a human must check or do
  before dependent work continues. One bullet per point, each prefixed
  "STOP — ". Omit if none.}
```

## Writing Guidelines

- Requirements are numbered per context and use MUST/SHOULD language; each has at least one acceptance criterion describing observable behavior.
- Acceptance criteria describe WHAT is observable, not HOW to implement it.
- Reference concrete file paths and existing patterns from the target repo where they anchor a requirement — the executing agent has the codebase but not this conversation.
- Group requirements so each context is independently implementable; put anything that spans contexts into Execution notes as an explicit dependency.
- Keep the language plain and concise. No hyperbole, no marketing terms, no dividers.
<!-- agentic:end -->
