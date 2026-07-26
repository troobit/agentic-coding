# Decision Log: Spec Janitor

## Decision 1: Feature named spec-janitor

**Date**: 2026-07-26
**Status**: accepted

### Context

The feature needed a name for its specs folder and skill identity. Candidates were spec-cleanup (plain), spec-janitor (custodial framing), and spec-hygiene (umbrella for cure + prevention).

### Decision

Name the feature spec-janitor.

### Rationale

The user chose the custodial framing: this is an ongoing maintenance role, not a one-shot cleanup. The name also distinguishes the mechanism from the individual cleanup actions it performs.

### Alternatives Considered

- **spec-cleanup**: Plain and descriptive - Rejected by user in favor of the role framing
- **spec-hygiene**: Emphasizes prevention + cure - Rejected; janitor communicates the acting role better

### Consequences

**Positive:**
- The name signals repeated, ongoing use rather than a one-off migration
- Distinct from the existing specs-overview skill's naming

**Negative:**
- Slightly less self-describing than spec-cleanup for first-time readers

---

## Decision 2: Tiered repair authority — auto-fix mechanical, gate judgment

**Date**: 2026-07-26
**Status**: accepted

### Context

The janitor repairs user-authored spec content. Repair authority ranged from audit-only (report, never write) to fully gated repairs to automatic application of everything.

### Decision

Mechanical fixes (dangling anchors, missing IDs, numbering, parse breakage) apply automatically; judgment repairs (supersession annotation, overlap reconciliation, file moves) are presented in batches and gated on explicit approval. Ambiguous mechanical fixes escalate to the gated batch.

### Rationale

Mechanical findings have a single correct fix and gating them is pure friction. Judgment findings encode content decisions (which spec supersedes which, what a document should now say) that belong to the user. The escalation rule keeps "mechanical" honest: anything requiring a guess is by definition not mechanical.

### Alternatives Considered

- **Gated repairs for everything**: Maximum safety - Rejected as needless friction for fixes with one correct answer
- **Audit-only**: No write risk at all - Rejected; it would leave all repair labor with the user, defeating the purpose

### Consequences

**Positive:**
- Low-friction cleanup for the common structural breakage
- Content decisions stay with the user; no silent rewriting of intent

**Negative:**
- The mechanical/judgment boundary must be specified precisely and maintained
- Auto-applied fixes still produce diffs the user must review at commit time

---

## Decision 3: Janitor creates a missing specs/OVERVIEW.md

**Date**: 2026-07-26
**Status**: accepted

### Context

The survey's strongest correlation: medata, the cleanest of the diluted-survey repos, is the only one maintaining a specs/OVERVIEW.md index with explicit supersession annotations. rune and orbit stay clean without one, but they are single-author repos by the process's originator.

### Decision

When the target repo lacks specs/OVERVIEW.md, the janitor creates it via the existing specs-overview workflow as part of cleanup.

### Rationale

The index is the governance artifact that makes supersession visible and keeps status honest (it recomputes from task checkboxes). Repos that drifted are exactly the repos that lack it; seeding it makes the cleanup stick.

### Alternatives Considered

- **Offer, don't assume**: Ask per repo - Rejected; the user chose unconditional creation, and an unwanted index is cheap to delete
- **Out of scope**: Leave indexing manual - Rejected; it discards the strongest observed cleanliness signal

### Consequences

**Positive:**
- Every cleaned repo ends with a maintained index and live status derivation
- Reuses specs-overview instead of duplicating index logic

**Negative:**
- Repos that deliberately go index-less get one anyway and must remove it

---

## Decision 4: Prevention guardrails ship with the janitor

**Date**: 2026-07-26
**Status**: accepted

### Context

Every surveyed dilution pattern was created by an authoring pass (PRD-lane tasks given full-spec anchors, revision runs appended without reconciling, tasks appended with a different schema). Cleaning without prevention means re-cleaning later.

### Decision

Guardrail edits to the prd, smolspec, and tasks authoring skills are in scope for this feature.

### Rationale

The taxonomy gives exact, known failure modes; the cheapest place to stop them is the skill that would otherwise generate them. Shipping cure and prevention together means the same spec documents both.

### Alternatives Considered

- **Separate follow-up spec**: Smaller feature scope - Rejected by user; splitting risks the prevention half never shipping
- **Prevention only via janitor report guidance**: No skill edits - Rejected; guidance after the fact is weaker than not generating the pattern

### Consequences

**Positive:**
- Failure modes are closed at the source; janitor findings should trend to zero
- One spec traces taxonomy → cure → prevention

**Negative:**
- Touches three existing skills, widening this feature's review surface

---

## Decision 5: Drift handling is contextual, with persistent per-spec exclusions

**Date**: 2026-07-26
**Status**: accepted

### Context

Even clean repos carry benign generational drift (bare-numeric task IDs in older specs, casing variance, scratch files). A fixed normalization policy either churns historical records or ignores real problems. Asked to choose a fixed policy, the user answered "ad hoc — depends on context — some specs can be left deliberately out of scope."

### Decision

Drift normalization is decided contextually at triage time, and the janitor supports durable per-spec (and per-finding) exclusions: declining a repair offers to record the exclusion so it is not re-proposed on later runs.

### Rationale

The user's steering makes exclusion a first-class mechanism, not an edge case. Benign drift in completed specs is raised at most once; without persistence, every janitor run would re-litigate the same deliberate choices.

### Alternatives Considered

- **Leave all benign drift**: Simple rule - Rejected; some drift is worth fixing when a spec is still active
- **Normalize active specs only**: Age-based rule - Rejected; activity is a proxy, and the user wants the call made per spec

### Consequences

**Positive:**
- Repeat runs are quiet about deliberate choices; reports stay signal-dense
- Historical specs are protected from churn by default

**Negative:**
- Requires a persistent exclusion store per repo, which is itself a file the janitor must manage

---

## Decision 6: Repair authority derives from a per-finding disposition table, not from the audit tier

**Date**: 2026-07-26
**Status**: accepted

### Context

The first requirements draft authorized auto-fixing everything the mechanical audit detects. Both reviewers (design-critic, peer validation) confirmed this conflates mechanically *detectable* with mechanically *fixable*: dangling anchors need retargeting decisions, unparseable files need reconstruction, renumbering rewrites identifiers other artifacts reference, and mode-mismatch folders need authored content.

### Decision

Every finding type carries an explicit disposition — auto-fix, gated, or detect-only — in a design-level disposition table. Auto-fix eligibility requires a single deterministic transformation that rewrites no identifier referenced from elsewhere; per-finding precondition failures demote to the gated batch.

### Rationale

This preserves the user's tiered-authority choice (Decision 2) while making the mechanical/judgment boundary a specified artifact instead of an assumption. The eligibility criterion is testable, and demotion-on-ambiguity keeps "mechanical" honest.

### Alternatives Considered

- **Auto-fix everything the mechanical audit finds**: Original draft - Rejected; multiple finding types have no unambiguous fix, so wholesale authority is unsafe
- **Gate everything**: Simpler safety story - Rejected earlier in Decision 2 as needless friction for genuinely deterministic fixes

### Consequences

**Positive:**
- The safety boundary is reviewable in the design rather than implicit in code
- False-positive detections cannot cascade into wrong automatic edits

**Negative:**
- The disposition table must be maintained as new finding types are added

---

## Decision 7: Autonomous surfaces run report-only

**Date**: 2026-07-26
**Status**: accepted

### Context

The judgment audit, batch approval, and exclusion triage are interactive; the GitHub Copilot cloud agent runs autonomously with no mid-run approval gate. The first draft promised the janitor "SHALL be available" in the cloud without saying what that means.

### Decision

Interactive surfaces (Claude Code, VS Code Copilot) get full capability. Autonomous surfaces run the mechanical audit and produce the report only — no auto-fixes, no gated repairs, no exclusion writes.

### Rationale

Auto-fixing in an autonomous loop changes the safety model from "user approves or reviews immediately" to "unreviewed until PR review", which was never agreed. A report in the cloud agent's output is still useful (it lands in the PR body or logs) and keeps one consistent authority model everywhere.

### Alternatives Considered

- **Auto-fixes as a PR from the cloud agent**: More automation - Rejected; silently shifts the approval point and can conflict with concurrent local runs
- **No cloud presence at all**: Simplest - Rejected; the mandate requires transfer to copilot surfaces, and report-only transfers cleanly

### Consequences

**Positive:**
- One authority model; the cloud surface can never write to specs
- The stdlib-only audit script is the only piece that must run in constrained environments

**Negative:**
- Cloud runs surface problems without fixing them; a human still closes the loop locally

---

## Decision 8: A canonical conventions reference is in scope and is the citation target

**Date**: 2026-07-26
**Status**: accepted

### Context

Findings must cite the convention they violate, but the conventions lived only in survey observations and scattered skill prose. Both reviewers flagged that citing undocumented rules means every run freelances its own guidance, and the mechanical audit needs a normative definition of task-file structure and the bugfix report shape.

### Decision

This feature authors a canonical conventions reference (stable rule identifiers for spec modes, canonical files, task-file structure, bugfix report shape, supersession annotation, filing rules). Both audits derive from it, and it is distributed with the janitor to every surface.

### Rationale

One normative document makes findings testable, keeps guidance consistent across runs and surfaces, and doubles as the "guide users toward good practice" artifact the feature exists to provide.

### Alternatives Considered

- **Cite the survey report**: No new document - Rejected; the survey is descriptive, not normative, and is not distributed
- **Leave rules inline in the skill prose**: Status quo - Rejected; the stdlib audit script and the skill would each carry their own drift-prone copy

### Consequences

**Positive:**
- Stable rule IDs make findings, exclusions, and guardrails reference the same source
- New repos get the conventions document alongside the janitor

**Negative:**
- Another distributed artifact to keep converged across surfaces

---

## Decision 9: Janitorial remit includes active-drift detection and autonomous-mode guardrails

**Date**: 2026-07-26
**Status**: accepted

### Context

At requirements approval the user steered: extant skills like nextup and the "work autonomously" modes (make-it-so, next-task) drive the same spec-driven workflow, and part of the janitorial work is auditing recent development patterns and fixing drift where it is actively happening. The user also amended Out of Scope so wholesale normalization is not forbidden but needs a very good reason decided at triage, with gated relocation (domain sub-folder or archive) as a lighter alternative.

### Decision

The judgment audit uses recent git history of `specs/` to find actively drifting specs and names the development pattern that produced the drift (AC 2.6). Prevention guardrails extend beyond authoring skills to skills that edit spec documents during implementation and autonomous modes (AC 8.5). Relocation, including archiving, is a permissible gated move at triage.

### Rationale

Dilution is introduced by ongoing development flows, not just initial authoring — the surveyed "Run 2/3/5" accretion came from repeated execution passes. Auditing recency focuses effort where cleanup pays off most, and guarding the autonomous editing paths closes the loop the authoring-only guardrails would leave open.

### Alternatives Considered

- **Authoring-skill guardrails only**: Smaller surface - Rejected; autonomous implementation passes are a proven source of accretion
- **Full-history audit with no recency signal**: Simpler - Rejected; treats settled historical drift the same as active bleeding, inverting the user's priority

### Consequences

**Positive:**
- Reports distinguish "actively getting worse" from "old and stable", matching triage priorities
- Autonomous modes stop being an unguarded path for the patterns the janitor cleans

**Negative:**
- Guardrail scope now touches more skills, widening review and maintenance surface

---

## Decision 10: Janitor assets seed verbatim, not via managed blocks

**Date**: 2026-07-26
**Status**: accepted

### Context

Design review verified against the code that align's managed-block mechanism is markdown-only: `write_managed` re-emits the end marker bare at column 0 (a SyntaxError in a `.py` file), and `_seed_file` skips markerless existing targets as hand-written — so a seeded `spec_lint.py` would freeze at its first copy and never receive updates.

### Decision

Add a verbatim-seeding class to `agentic_lib` (`seed_verbatim`): destination missing → copy; identical → no-op; differing → back up with `.bak-<date>` and re-copy, reported as changed. All spec-janitor seeded files are declared tool-owned and use it. prd's managed-block seeding is unchanged.

### Rationale

Janitor assets carry no repo-local hand edits by contract — the auditor and conventions reference must be byte-identical on every surface, so overwrite-with-backup is correct and matches align's existing JSON-validity convention.

### Alternatives Considered

- **Comment-embedded markers in the Python file**: Reuse managed blocks - Rejected; write_managed's reconstruction produces syntactically invalid Python
- **Seed once and accept staleness**: No align change - Rejected; a frozen auditor silently diverges from the conventions it enforces

### Consequences

**Positive:**
- Auditor and conventions stay converged across repos via the ordinary align run
- Hand-modified copies are preserved as backups, never lost

**Negative:**
- A second seeding class in agentic_lib to maintain; the stale-pack prune exemption must also generalize to the new agent file

---

## Decision 11: Auto-fix eligibility is "deterministic or purely additive"

**Date**: 2026-07-26
**Status**: accepted

### Context

Requirement 3.2 originally demanded a "single deterministic transformation". Minting stable task IDs is nondeterministic (random ID values) yet safe: it only inserts new identifiers, never rewrites an existing token. As written, the design's own disposition table violated its eligibility criterion.

### Decision

Amend the criterion to: a single transformation that is deterministic or purely additive, and rewrites no identifier referenced from elsewhere. Minted IDs must round-trip `rune list` when rune is present (test-pinned).

### Rationale

The safety property the criterion protects is "cannot change the meaning of existing content or break inbound references"; purely additive transformations satisfy it regardless of the randomness of the added value.

### Alternatives Considered

- **Gate ID minting**: Keep the strict criterion - Rejected; gating a provably additive fix is friction without safety benefit
- **Deterministic IDs (content-hash)**: Restore determinism - Rejected; diverges from rune's own ID scheme and provides no additional safety

### Consequences

**Positive:**
- Both auto-fix rules pass the stated criterion honestly; the table and requirement agree
- The rune round-trip test guards against format drift

**Negative:**
- The janitor normatively pins rune's exhibited (not documented) ID format; if rune's generator changes, the conventions reference must follow

---

## Decision 12: The exclusion store is machine-written via spec_lint subcommands

**Date**: 2026-07-26
**Status**: accepted

### Context

Review found the store write path undefined: the skill hand-merging JSON risks silent corruption, and the original "corrupt store treated as empty, never overwritten" rule made recording new exclusions impossible after corruption — dropping every previously declined finding, the exact re-litigation Requirement 5 prevents.

### Decision

`spec_lint.py` gains `exclude` and `mark-raised` subcommands as the only writers of `specs/.janitor.json`, schema-validating on write. A corrupt store is backed up (`.janitor.json.bak-<date>`) and rebuilt, reported prominently.

### Rationale

A machine-written, schema-validated store cannot be silently mangled by prose-level JSON editing, and backup-then-rebuild preserves the audit trail while keeping triage functional.

### Alternatives Considered

- **Skill edits the JSON directly**: No new CLI surface - Rejected; hand-merged JSON by an LLM is the store's most likely corruption source
- **Store inside .agentic.json**: Reuse align's manifest - Rejected; align treats the manifest as read-only input, and mixing tool ownership conflates two write authorities

### Consequences

**Positive:**
- Exclusion durability survives both corruption and concurrent skill sessions writing through one validated path
- The cloud agent structurally cannot write: the report-only asset never invokes subcommands

**Negative:**
- Two more CLI subcommands to test and document
