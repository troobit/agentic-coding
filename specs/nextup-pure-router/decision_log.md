# Decision Log: Nextup Pure Router

## Decision 1: Stay in the smolspec lane despite touching ~9 files

**Date**: 2026-07-25
**Status**: accepted

### Context

The smolspec escalation criteria flag changes above 3 files or 80 LOC for the full spec workflow. This change touches about thirteen files: the nextup skill rewrite, the example template, one-line-to-one-section edits in seven other skill documents, prose updates in three docs, and — after design-critic review surfaced that `make status` parses the machine zone — a bounded code deletion in `scripts/process_status.py` plus matching test updates.

### Decision

Keep the work in the smolspec lane and record the scope metrics here instead of escalating.

### Rationale

The escalation thresholds are written for risky code (API breakage, backward compatibility) and this change is process documentation plus a feature *deletion* in one internal script, covered by an existing test suite. The user's written direction — the authoritative user zone, with the autonomy flag set — is explicitly to reduce process ceremony around nextup; routing that request into the heaviest gated workflow would contradict it. The change has one coherent purpose: remove machine-zone tracking everywhere it appears.

### Alternatives Considered

- **Full spec workflow (`/starwave:requirements`)**: Requirements/design/tasks with gates - Rejected: gates contradict the autonomy flag, and the ceremony contradicts the request itself.
- **PRD lane (`/prd` → `/engage`)**: Ungated end-to-end execution - Rejected: nextup already routed this as a light-lane job; a PRD adds an authoring step without adding safety for a doc-only change.

### Consequences

**Positive:**
- Spec effort proportional to actual risk; work proceeds in one session.
- Scope metrics still recorded, so the deviation from the thresholds is auditable.

**Negative:**
- Sets a precedent for reading the file-count threshold as code-oriented; future borderline cases need the same explicit justification.

---

## Decision 2: Keep the `<!-- LM -->` marker as an inert anchor

**Date**: 2026-07-25
**Status**: accepted

### Context

The user called the machine zone "a candidate for deletion". But `scripts/align.py` step 6 converges `nextup.example.md` in downstream repos from the first `<!-- LM -->` marker down, and `tests/test_align.py` asserts that behaviour (user zone preserved byte-for-byte, machine zone converged to canonical). Removing the marker entirely would require new markerless handling in align.py plus test and fixture changes.

### Decision

Keep the `<!-- LM -->` marker in `nextup.example.md` and `nextup.md`, with only a one-line inert note below it. All status content, and every skill behaviour that reads or writes the zone, is removed.

### Rationale

The marker costs one line and keeps `align.py` and its tests untouched, holding the change to markdown-only. Convergence keyed on the marker also becomes the distribution mechanism for this very change: align will replace downstream repos' stale machine-zone templates with the inert note.

### Alternatives Considered

- **Delete the marker and zone entirely**: Cleanest end state - Rejected: drags `scripts/align.py` logic, fixtures, and tests into scope for no behavioural gain; the zone is already inert without it.
- **Keep the zone but stop updating it**: No file changes to templates - Rejected: leaves a misleading status template that readers may trust; the duplication the user objected to would persist in every downstream repo.

### Consequences

**Positive:**
- `scripts/align.py` and `tests/` stay out of scope; align propagates the slimmed template downstream automatically.
- A future change can still remove the marker in a dedicated spec that also updates align.py.

**Negative:**
- A vestigial marker line remains in the template; its purpose is documented here, in align.py's docstrings, and in the onboarding runbook / scripts README prose this change updates.

---

## Decision 3: In-chat messages and specs/OVERVIEW.md replace the machine zone as status

**Date**: 2026-07-25
**Status**: accepted

### Context

The machine zone was the at-a-glance, between-sessions status for a possibly non-technical reader, and it carried state the router itself produced: fan-out outcomes, queued gated jobs, loose ends with no tasks file, interrupt handoffs, and the "spec is out for review" marker after `/sendit`. Deleting the zone removes all of these unless replacements are named. Design-critic review flagged this as a blocker.

### Decision

Session status lives in the plain-English messages nextup and sendit already produce, plus `specs/OVERVIEW.md` for cross-feature state. Fan-out outcomes, undispatched gated jobs, interrupt handoffs, and loose ends without a tasks file are reported in the closing message; loose ends with a tasks file become rune tasks. After a `/sendit` handoff, a following `/nextup` run with no change requests in the user zone counts as approval — no stored review state.

### Rationale

The user's direction is that specs, task lists, and agent notes are the sources of truth and the zone "duplicates docs/agent-notes". Storing router state anywhere else would recreate the duplication under a new name. The closing message reaches the user at exactly the moment the state exists, and anything worth keeping longer belongs in a task list or decision log by the user's own rule.

### Alternatives Considered

- **Move the status block into docs/agent-notes/**: Same content, different file - Rejected: agent notes are for durable knowledge about code, not per-session state; this recreates the machine zone elsewhere.
- **Keep a minimal one-line status in the machine zone**: Smallest possible zone - Rejected: keeps the read/write contract alive in every skill, which is the bulk of the cost being removed.
- **Store review state in the feature's decision_log.md after /sendit**: Durable approval record - Rejected: pollutes an architecture-decision log with workflow state; the ungated direction makes implicit approval acceptable.

### Consequences

**Positive:**
- Zero duplicated state; one fewer contract for every skill to honour.
- The non-technical reader gets status in prose at session boundaries, which is how they consumed it anyway.

**Negative:**
- No persistent between-sessions status ledger; a user returning after weeks must infer state from `specs/OVERVIEW.md` and git rather than a narrative note.
- Implicit approval after `/sendit` weakens the review gate: continuing without comment advances the spec.

---
