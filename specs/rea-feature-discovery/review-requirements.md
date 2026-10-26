# REA Feature Discovery: Requirements Review

Review date: 2026-10-25. The user authorised implementation on 2026-10-26 by
instructing creation of the skill after reviewing these requirements.

## Scope reviewed

The reusable process studies selected features in existing apps through REA,
preserves evidence and unknowns, and routes feature adoption into the destination
app's existing Starwave lifecycle. This repository owns the reusable process and
MCP integration. Libre is an example whose product context belongs in MeData.

## Review findings

The design-critic review was followed by two independent native peer reviews.
`PERSONAL_PROJECTS` was unset, so the peer-review-validator fallback used review
agents rather than external model services.

| Perspective | Finding | Resolution |
| --- | --- | --- |
| Design critic | AC 3.2 required permanently resolvable references while AC 3.3 allowed session references to become unavailable. | AC 3.2 now requires accessibility when captured. AC 3.3 requires recovery or an explicit unresolved assumption before later planning relies on unavailable evidence. AC 6.3 includes expired-session continuation. |
| Technical feasibility and recovery | The amended evidence rules, missing-input handling, ownership, and continuation requirements are feasible and observable. | No further requirement changes requested. Storage and client details belong in design. |
| Architecture, reuse, and workflow | REA's existing investigation prompt/skill can supply analysis while Starwave remains the planning lifecycle. Destination ownership and gates are preserved. | No further requirement changes requested. Carry prompt reuse and client fallback into design. |

Both peer reviews validated the critic's resolution. No remaining scope question
or requirement-level blocker was identified. The precise Libre behaviour is an
input to a future invocation, not a prerequisite for defining the generic process.

## Requirements-stage validation

- The 22 acceptance-criterion anchors are unique, all criteria use EARS language,
  and all six requirements include user stories.
- Local Markdown references, fenced examples, and the candidate MCP JSON passed
  document checks.
- MeData `make spell` passed.
- `make lint` passed its shellcheck step, then failed because the pre-existing
  `copilot/instructions/copilot-instructions.md` was absent when the drift target
  tried to snapshot it. The generated file created during that failed check was
  removed to restore its prior absence. This spec does not change the generator.
- At review time the spec auditor reported `SJ-MODE-001` for the requirements-only
  folder because design had not yet been authored. No placeholder design or
  premature task file was created to conceal the requirements-stage gap.

## Implementation continuation

The reusable skill and MCP integration are implemented under `design.md` and
`tasks.md`. The requirements-stage findings above describe that earlier review;
current implementation validation is recorded in `verification.md`. No Libre
product implementation was added to this repository.
