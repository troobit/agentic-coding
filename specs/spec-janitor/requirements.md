# Requirements: Spec Janitor

## Introduction

Spec directories accumulate dilution when subsequent or parallel spec work contradicts, duplicates, or bypasses earlier documents — surveyed examples include task files anchoring a requirements.md that never existed, one smolspec holding two mutually exclusive designs, and duplicate features with no cross-supersession. Spec-janitor adds an audit-and-repair workflow that detects these problems, repairs them under explicitly tiered authority, and steers users toward the conventions observed in clean repos. Its assets reach Claude Code, VS Code Copilot, and the GitHub Copilot cloud agent through this repo's existing distribution paths.

## Out of Scope

- Deleting spec folders or erasing spec history — supersession is annotated, never removed
- Applying fixes to files outside `specs/` (detection MAY read the whole repo read-only; stale `docs/`/`README` content is reported with proposed follow-ups, not edited)
- CI enforcement of the audit — this feature ships an on-demand tool
- Copilot CLI support (excluded from this toolchain by toolset-agnostic-starwave Decisions 3/10)
- Wholesale normalization of completed specs to current conventions as a default behavior — it needs a very good reason, decided at triage (Requirement 5.6); relocating a spec (into a domain sub-folder or an archive) as a gated move (Requirement 3.6) may suffice instead
- Reimplementing spec indexing — the janitor delegates to the existing specs-overview workflow
- Confirming ghost changes against code or git history — ghost-change findings claim only that a spec references work no spec folder covers

## Requirements

### 1. Mechanical Audit

**User Story:** As a developer, I want structural breakage in `specs/` detected mechanically, so that broken cross-references and unparseable files are found without judgment calls or manual reading.

**Acceptance Criteria:**

1. <a name="1.1"></a>The audit SHALL report every task-file requirement reference whose target file or anchor does not exist, covering the reference styles enumerated in the design (at minimum `[N.M](file.md#N.M)` anchor links and `references:` front-matter entries)  
2. <a name="1.2"></a>The audit SHALL report every task file that violates the task-file structure rules defined in the conventions reference (Requirement 7), every task file where some tasks carry stable-ID markers while sibling tasks do not, and out-of-sequence task numbering  
3. <a name="1.3"></a>WHEN the `rune` CLI is available, the audit SHALL additionally verify task files with it; WHEN it is absent, the audit SHALL state in the report that rune verification was skipped  
4. <a name="1.4"></a>The audit SHALL report each spec folder whose files match no recognized spec mode (full: requirements+design, smol: smolspec, PRD lane: prd, bugfix: report) and each spec folder missing its mode's task file  
5. <a name="1.5"></a>The audit SHALL report `specs/bugfixes/` entries that do not follow the bugfix report shape defined in the conventions reference  
6. <a name="1.6"></a>The audit SHALL produce a human-readable report and machine-readable output with a schema defined in the design, exit non-zero when findings exist, and run on a stock Python 3 installation with no third-party dependencies  
7. <a name="1.7"></a>The audit SHALL work in flat (`specs/<feature>/`) and nested (`specs/<domain>/<feature>/`) layouts and with PRD-lane multi-task-file specs (`tasks-<context>.md`)  
8. <a name="1.8"></a>WHEN the target repo has no `specs/` directory, the audit SHALL report that and exit zero without creating anything  

### 2. Judgment Audit

**User Story:** As a developer, I want the janitor to find dilution that requires reading and reasoning, so that overlap, contradiction, and silent supersession are surfaced — not just structural breakage.

**Acceptance Criteria:**

1. <a name="2.1"></a>The janitor SHALL identify specs that address the same problem or surface without referencing each other's resolution (duplicate or silently superseding specs)  
2. <a name="2.2"></a>The janitor SHALL identify documents whose later sections contradict earlier sections after a direction change, where the earlier sections are not marked superseded  
3. <a name="2.3"></a>The janitor SHALL identify task files whose scope does not match their spec document's scope (e.g. tasks spanning phases the smolspec does not cover)  
4. <a name="2.4"></a>The janitor SHALL identify specs referencing changes no spec folder covers (ghost changes), specs abandoned mid-workflow, and items filed in the wrong category (e.g. non-bug cleanups under `specs/bugfixes/`)  
5. <a name="2.5"></a>Every judgment finding SHALL carry the evidence it is based on (file paths and quoted content) and cite the violated rule in the conventions reference by identifier, so the report doubles as guidance  
6. <a name="2.6"></a>The janitor SHALL use recent git history of `specs/` to identify where drift is actively being introduced, and SHALL report which development pattern produced it (e.g. repeated autonomous-run layering, parallel spec authoring) so active drift is prioritized over historical drift  

### 3. Repair Dispositions and Tiered Authority

**User Story:** As a developer, I want every finding type to carry an explicit repair disposition, so that the janitor only auto-fixes what has exactly one correct fix and everything else waits for my approval.

**Acceptance Criteria:**

1. <a name="3.1"></a>Every finding type SHALL have one of three dispositions defined in a design-level disposition table: auto-fix, gated, or detect-only  
2. <a name="3.2"></a>A finding type SHALL be eligible for the auto-fix disposition only IF its repair is a single transformation that is deterministic or purely additive, and that rewrites no identifier referenced from elsewhere; all other repairable findings SHALL be gated  
3. <a name="3.3"></a>WHEN an auto-fix's preconditions do not hold for a specific finding (e.g. more than one candidate repair), the janitor SHALL demote that finding to the gated batch instead of guessing  
4. <a name="3.4"></a>WHEN the janitor applies auto-fixes, it SHALL list every applied fix in its report; WHEN it proposes gated repairs, it SHALL present them in batches and apply a batch only after explicit approval  
5. <a name="3.5"></a>Repairs SHALL annotate supersession (decision-log entries, status markers, cross-references) rather than deleting superseded content  
6. <a name="3.6"></a>File moves and renames SHALL only occur as gated repairs, and an approved move SHALL in the same batch rewrite all inbound references within `specs/` and report inbound references outside `specs/` as follow-ups  

### 4. Safety and Idempotence

**User Story:** As a developer, I want to get a full report without any writes and to trust that repeated runs are quiet, so that running the janitor is never risky.

**Acceptance Criteria:**

1. <a name="4.1"></a>The janitor SHALL support a report-only invocation that performs no writes  
2. <a name="4.2"></a>WHEN the working tree has uncommitted changes under `specs/`, the janitor SHALL NOT apply auto-fixes unless the user explicitly overrides, and SHALL fall back to report-only with a warning  
3. <a name="4.3"></a>WHEN a run completes and the janitor is immediately re-run, the second run SHALL produce no new findings for repaired items and no writes  

### 5. Scoping and Exclusions

**User Story:** As a developer, I want to deliberately leave some specs or findings out of the janitor's reach, so that historical or intentionally unconventional specs are not churned and declined proposals are not re-litigated.

**Acceptance Criteria:**

1. <a name="5.1"></a>The janitor SHALL support durable exclusions at two granularities — a whole spec, or a single finding — with the granularity chosen by the user at triage time  
2. <a name="5.2"></a>WHEN the user declines a proposed repair, the janitor SHALL offer to record an exclusion so the finding is not re-proposed on later runs  
3. <a name="5.3"></a>Excluded specs and findings SHALL be skipped in later audits and listed as excluded in the report  
4. <a name="5.4"></a>Each finding SHALL have a stable identity (defined in the design) that survives unrelated edits and line moves, so exclusions keep matching across runs  
5. <a name="5.5"></a>The janitor's own bookkeeping files SHALL be exempt from its audits  
6. <a name="5.6"></a>Benign drift in completed specs (older ID styles, casing variance, ad-hoc extra files) SHALL be raised at most once per finding identity, with normalization decided contextually at triage — never applied automatically  

### 6. Index and Supersession Governance

**User Story:** As a developer, I want every cleaned repo to end up with the governance signals that correlate with staying clean, so that the cleanup persists.

**Acceptance Criteria:**

1. <a name="6.1"></a>WHEN the target repo has specs but no `specs/OVERVIEW.md`, the janitor SHALL create one through the specs-overview workflow  
2. <a name="6.2"></a>WHEN repairs change spec status or supersession, the janitor SHALL regenerate the overview so index rows match the repaired state  
3. <a name="6.3"></a>WHEN a repair marks a spec superseded, the janitor SHALL record which spec supersedes it in both directions (superseded spec and superseding spec)  

### 7. Conventions Reference

**User Story:** As a developer, I want the conventions the janitor enforces written down once, so that findings cite stable rules instead of freelancing guidance per run.

**Acceptance Criteria:**

1. <a name="7.1"></a>A canonical conventions reference SHALL exist in this repo defining, with stable rule identifiers: the spec modes and their canonical files, task-file structure rules, the bugfix report shape, supersession annotation, and filing rules  
2. <a name="7.2"></a>The mechanical audit's checks and the judgment audit's citations SHALL derive from the conventions reference, and the reference SHALL be distributed with the janitor to every surface the janitor reaches  

### 8. Prevention Guardrails

**User Story:** As a developer, I want the authoring skills hardened against the observed failure modes, so that the same dilution patterns are not re-created after cleanup.

**Acceptance Criteria:**

1. <a name="8.1"></a>PRD-lane task authoring SHALL anchor task requirement references to `prd.md` sections and SHALL NOT emit references to a `requirements.md` the spec folder does not contain  
2. <a name="8.2"></a>The smolspec skill's revision guidance SHALL require that a pass changing a spec's direction marks the discarded design's sections as superseded in the same edit  
3. <a name="8.3"></a>The tasks skill SHALL require the task list's scope to match the source document's scope, and additions from later passes to carry the same schema as existing tasks  
4. <a name="8.4"></a>Bugfix filing guidance SHALL state that `specs/bugfixes/` entries follow the report shape and that non-bug work belongs in a regular spec folder  
5. <a name="8.5"></a>Guardrails SHALL also cover skills that edit spec documents during implementation and autonomous modes (e.g. nextup routing, make-it-so/next-task passes): mid-implementation spec edits follow the same conventions reference, including supersession annotation and task-schema consistency  

### 9. Cross-Toolset Distribution

**User Story:** As a developer, I want the janitor available in every surface I work in, with each surface doing only what it can do safely, so that cleanup does not depend on which tool I have open.

**Acceptance Criteria:**

1. <a name="9.1"></a>The janitor skill SHALL be invocable from Claude Code and VS Code Copilot through the same distribution path as existing skills, with full capability (audit, auto-fix, gated repair, exclusion triage)  
2. <a name="9.2"></a>In autonomous surfaces (the GitHub Copilot cloud agent), the janitor SHALL run the mechanical audit and produce the report only — no auto-fixes, no gated repairs, no exclusion writes  
3. <a name="9.3"></a>Cloud-agent distribution SHALL follow the existing prd seeding pattern (managed blocks; markerless pre-existing targets skipped, never overwritten) for repos with cloud assets enabled  
4. <a name="9.4"></a>The mechanical audit SHALL be runnable in any target repo without that repo installing this repository's tooling beyond the seeded assets  
