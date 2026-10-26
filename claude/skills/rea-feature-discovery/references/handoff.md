# Destination Research and Handoff

Read this when creating research or continuing an earlier investigation. Use the
destination's existing research document if one already covers the question.
Otherwise keep `research-rea.md` with the owning spec. Before a new spec exists,
use the destination's research convention, defaulting to
`docs/research/rea-<capability>.md`; do not create a spec folder containing only
research. Once Starwave creates the spec, move/link the relevant research and
keep one authoritative record.

Use the following fields as a compact starting point, adapting headings to the
destination rather than creating another schema or tracking system:

```markdown
# Research: <destination capability>

## Question and owner
Source app, selected behaviour/question, destination repo, and existing spec.

## Source and access
App version/platform and input identity (path/digest/endpoint where available).
Observation date; distinguish user-supplied identity from inspected facts.
What was inspected; MCP connection/input/provider availability for this question.
Unknown fields stay unknown.

## Findings and evidence
For each finding: observed fact / inference / unresolved question, source reference,
REA Evidence ID where applicable, retained result/export location, and limitations.
Identify session-only or unavailable references explicitly.

## Adoption and validation
Behaviour to adopt, destination adaptations, and evidence each depends on.
How to verify source-observed behaviour versus adaptations chosen for this app.

## Continuation
Open questions/prerequisites and the decisions each blocks.
Destination spec path, current Starwave stage, approvals actually received,
affected downstream documents, and the next supported action.
```

Keep relevant complete REA results or supported exports at a durable location
permitted by the destination's artifact policy; include paths and enough source
identity to locate them again. Do not assume raw artifacts belong in version
control. When retaining Evidence is unavailable, record the reference loss and
keep the affected claim unresolved. A remembered ID or a copied prose conclusion
alone does not authenticate the original result.

On resume, read the existing record before editing it. Compare source version,
input identity, and evidence availability; preserve earlier dated observations
and mark only affected claims for re-verification. A changed binary is a new
observation, not permission to overwrite old evidence or approved requirements.

The handoff does not itself approve a spec. New work enters Starwave scope
assessment; existing work resumes its recorded stage and keeps requirement IDs.
Record prerequisites in the destination's established location. Put coding/testing
work into the eventual rune plan; keep manual acquisition/setup prerequisites
distinct. Validate the task file with `rune list` before describing it as ready.
