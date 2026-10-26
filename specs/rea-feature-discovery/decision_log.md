# REA Feature Discovery Decision Log

## Quick decisions

| ID | Date | Status | Decision | Rationale |
| --- | --- | --- | --- | --- |
| Q1 | 2026-10-25 | Confirmed by user | Libre example target: Abbott Libre build `1.4.2.2128` on iOS `26.7.1`. | Example findings must be attributable to the supplied target version. |
| Q2 | 2026-10-25 | Confirmed by user | For the Libre example, the installed phone app is the only currently available input. | No IPA, local app bundle, or source code is available for that example. |
| Q3 | 2026-10-25 | Superseded by Q6 | Initially proposed the feature name `libre-mcp`. | The user's clarification separates the reusable process from this example. |
| Q4 | 2026-10-25 | Confirmed by user | This spec covers the reusable process for pulling features from existing apps through REA and codifying/planning them through Starwave. | App-specific product work is not the purpose of this repository's spec. |
| Q5 | 2026-10-25 | Confirmed by user | Libre belongs in `medata`; use it only as an example here. | Product research and implementation belong to the application that consumes them. |
| Q6 | 2026-10-25 | Replaces Q3 | Use `rea-feature-discovery` for the reusable spec folder. | Names the reusable capability rather than its first source app. |
| Q7 | 2026-10-26 | Confirmed by user | Proceed with creating the reviewed skill and its integration. | The user instructed “create the skill for us” after reviewing its requirements and proposed invocation. |
| Q8 | 2026-10-26 | Accepted | Reuse REA `6.7.0` with portable skill instructions and conditional setup/handoff references. | The version remains the published release and already passed the local production-stdio check; existing sync/generation handles distribution. |

---

## Decision 1: Reuse REA for local artifact analysis

**ID:** D1  
**Date:** 2026-10-25  
**Status:** superseded by Decision 2

### Context

The user requested a stable system and MCP service based on REA for an iPhone
installation of Abbott Libre. REA already provides an MCP server, and a local
production-stdio health check passed for version `6.7.0`. No local Libre artifact
is available, and the desired first capability is still unspecified.

### Decision

Propose reusing REA for artifact analysis through this repository's canonical
MCP definitions. Choose glucose-data retrieval separately if requested. Do not
claim an active Libre connection from a successful target-free REA health check.

### Rationale

Reusing the tested upstream protocol avoids maintaining a redundant MCP bridge.
Artifact analysis and cloud glucose retrieval have different inputs and failure
conditions; neither proves the other works.

### Alternatives considered

- **Custom MCP proxy around REA:** reject for the proposed foundation because it
  adds a process and error-translation layer without a required new capability.
- **Treat phone installation as a directly readable artifact:** reject because
  the documented Apple analysis workflow requires caller-supplied files.
- **Implement an unofficial LibreLinkUp client immediately:** defer because
  glucose retrieval has not been selected and no account region or supported
  adapter has been established.

### Consequences

Positive:

- Uses a locally verified upstream server and existing repository config tooling.
- Keeps app-analysis evidence distinct from glucose readings.

Negative:

- The installed app cannot be analyzed until an appropriate input is available.
- Native decompilation still requires an analysis provider.
- Glucose retrieval requires a separate scoped integration.

---

## Decision 2: Separate the reusable process from product features

**ID:** D2  
**Date:** 2026-10-25  
**Status:** accepted

### Context

The user clarified that this spec is about a reusable REA investigation and
Starwave planning process. The source application is an input to that process;
it is not the product capability being specified in `agentic-coding`. The
initial Libre example belongs in `medata`, which already has relevant CGM specs.

### Decision

`agentic-coding` owns the reusable REA/MCP workflow and Starwave handoff. Each
destination repository owns its app-specific research, product requirements,
design, decisions, and rune plan. Reframe this spec as `rea-feature-discovery`
and preserve Libre-specific context in `medata/docs/research/libre-rea.md`.

### Rationale

The process should work for any supported source app and destination. Looking
up the destination's existing specs avoids parallel plans for an already-owned
capability and prevents this tooling repository from accumulating product specs.

### Alternatives Considered

- **Keep a Libre-specific spec here:** rejected by the user's scope clarification;
  it makes a single example the architecture and puts product work in the wrong repo.
- **Put the reusable process entirely in medata:** rejected because other apps
  need the same REA access, evidence handling, and Starwave planning workflow.
- **Create an app-specific MCP wrapper for every investigation:** rejected as the
  default because tool access alone does not provide the reusable planning process.

### Consequences

**Positive:**

- One process can serve multiple source apps and destination repositories.
- Product features continue in the repo and spec that already own their behaviour.
- Libre remains a concrete example of incomplete access rather than a separate
  platform requirement.

**Negative:**

- Each invocation must identify both the source feature and the destination owner.
- Cross-repository research references need explicit locations and cannot depend
  solely on the current conversation.
