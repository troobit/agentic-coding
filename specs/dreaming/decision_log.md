# Decision Log: Dreaming

## Quick Decisions

| ID | Date | Decision | Rationale |
|----|------|----------|-----------|
| Q1 | 2026-11-04 | Feature name is `dreaming` (`specs/dreaming/`) | The user's term |
| Q2 | 2026-11-04 | Use the full spec lane (requirements, design, tasks) | User-owned ambiguity, persisted store, contested architecture |
| Q3 | 2026-11-04 | A dream starts only on explicit request; no idle or activity monitoring; tools may start dreams per Decision 7 | User direction |
| Q4 | 2026-11-04 | Workers run sequentially; parallel execution is not a design target | The goal is context separation, not speed |
| Q5 | 2026-11-04 | Dreams may change agentic-coding, orbit/apsis and project repositories; the knowledge vault is not a write target | User selected the targets; the vault holds the user's own notes (Q22) |
| Q6 | 2026-11-04 | Default selection is newest unread sessions first within a configurable budget; each run records cost and yield | Batch size is unknown and found by experiment |
| Q7 | 2026-11-04 | Tailoring to the user means editable lenses, scripting repeated steps and spotting stalls; the report is not rewritten in simplified language | User selection |
| Q8 | 2026-11-04 | LM Studio session reading belongs in apsis, not dreaming | Other tools can reuse it |
| Q9 | 2026-11-04 | LM Studio server logs are a session source; LM Studio chat conversations are not | Logs add metadata and direct API use; bodies are truncated |
| Q10 | 2026-11-04 | Earlier dreams are in scope like any session; only the dream in progress is excluded | Prevents recursive reading of its own output |
| Q11 | 2026-11-04 | Web chat apps and interactions with no local record are out of scope | Nothing local to read |
| Q12 | 2026-11-04 | Dreams may target a repository or workflow using only matching sessions and lenses; the specification process is an improvement target | User wants targeted improvement within a general process |
| Q13 | 2026-11-04 | Dreams inspect current skills, rules and configuration for broken or inconsistent references, independent of sessions | User direction; example: recall-knowledge searches a folder capture-knowledge never writes |
| Q14 | 2026-11-04 | Dreams report MCP servers and tools configured versus used, and context spent before the first prompt | Tool bloat hurts local models; LM Studio logs give prompt sizes |
| Q15 | 2026-11-04 | Configured knowledge folders are optional read-only research sources; missing ones are reported and skipped | Research must not depend on an interactive skill |
| Q16 | 2026-11-04 | Reuse existing skills for unattended steps; defer interactive steps and report the limitation | Reuse without an interactive dependency |
| Q17 | 2026-11-04 | Only parallel execution is deferred; measuring effect and linked cross-repo changes stay in | User direction |
| Q18 | 2026-11-04 | Research on every backend uses devtools via a harness with an explicit tool list from the shared MCP definitions | A direct model request cannot run tools (Decision 2) |
| Q19 | 2026-11-04 | Sessions larger than a role's context are split into consecutive parts | Largest sessions are often the most informative |
| Q20 | 2026-11-04 | Configuration is snapshotted at run start; checks and restrictions stay editable | User accepts dreams improving their own checks (Decision 1) |
| Q21 | 2026-11-04 | Section 3 is delivered by a separate spec in the orbit repository | orbit owns `specs/apsis-*` |
| Q22 | 2026-11-04 | No knowledge-vault writes or capture-knowledge dependency | User descoped it |
| Q23 | 2026-11-04 | Run every configured check on the proposed merged result; any failure blocks auto-apply; no baseline runs | One pass/fail rule |
| Q24 | 2026-11-04 | Budgets cover all roles, retries and fallbacks; reserve capacity for review and authoring; finish the report without model calls when the limit is reached | A reading-only budget leaves later work unbounded |
| Q25 | 2026-11-04 | Evaluate changes using later independent sessions; rank recurring patterns and refine existing improvements instead of duplicating | Summaries of earlier evidence are not new support |
| Q26 | 2026-11-04 | Evidence identifiers cover session observations and file findings; verify quotes before redacting stored copies | File-only fixes need evidence; redacted quotes cannot match raw sources |
| Q27 | 2026-11-04 | Label context measurements as measured, estimated or unavailable; external configuration changes are user-applied suggestions | History may lack a breakdown; external configuration has no adoption path |
| Q28 | 2026-11-04 | Linked adoption preflights all repositories and attempts group rollback, reporting every state | Cross-repository atomicity is impossible |
| Q29 | 2026-11-04 | Default selection includes appended session content; explicit rereads revisit history; recovery reverts count as failed adoption, not user rejection | Avoids defeating rereads and wasting the rejection retry |
| Q30 | 2026-11-04 | Budget exhaustion ends a run; crash recovery keeps the remaining budget | Resuming an exhausted run makes no progress; resetting evades the budget |
| Q31 | 2026-11-04 | Every dream call leaves a record the shared reader can find and attribute to the dream; a truncated LM Studio log entry suffices for direct calls | Q10 and 1.5 need dream records readable |
| Q32 | 2026-11-04 | The names list for the public-output scan is read only from files outside every repository | A public list would publish the names (Decision 3) |
| Q33 | 2026-11-04 | After interruption following a first merge into a user checkout, resume makes no further merges or deployments, reports finish and undo commands, and may resume with no budget left | Reporting is safer than automatic finish or revert |
| Q34 | 2026-11-04 | Report merge and revert commands run the repository's generate step before committing, then deploy | Otherwise generated files go stale and lint fails |
| Q35 | 2026-11-04 | A run, including a resumed part, completes on the program version it started with | New code on old state is unsafe; discarding covers a buggy version |
| Q36 | 2026-11-04 | Resume keeps selection, budget and overrides, accepts new backend choices, re-enables failed backends, rechecks and resizes; other overrides are rejected; wall-clock counts only while running | Retrying blocked backends makes no progress; sleep must not exhaust budgets |
| Q37 | 2026-11-04 | Continue the `dreaming` spec as a foundation for personalised tooling beyond agentic-coding | User request |
| Q38 | 2026-11-04 | Recurrence supports frequency; claims that an approach worked also need a confirmed outcome in scope | Repeated untested suggestions must not become effectiveness claims |
| Q39 | 2026-11-04 | Equivalent knowledge keeps its identity and feedback across lenses; explicit user corrections resolve matching conflicts | New identifiers must not bypass corrections |
| Q40 | 2026-11-04 | The next in-scope dream reassesses revision-linked consumer feedback | Closes the personalisation loop |
| Q41 | 2026-11-04 | Unresolved scope is not global; deferred and addressed recommendations are omitted by default | Avoids unintended guidance |
| Q42 | 2026-11-05 | Personal learning covers both how the user works and what the user could learn | User selection |
| Q43 | 2026-11-05 | Provide a small reusable boundary for web or app endpoints; defer UI, server and hosting | Flexibility without added complexity |
| Q44 | 2026-11-05 | Section 3 is delivered by orbit's `apsis-shared-json` and `apsis-lmstudio-logs` specs; criteria 3.1–3.5 match their contracts | Implemented and merged (Q65); dreaming adapts instead of restating |
| Q45 | 2026-11-05 | Classify sessions as local or cloud from recorded provider and model by configured rules (2.2) | apsis records the provider only |
| Q46 | 2026-11-05 | Match duplicate interactions by recorded correlation identifiers; unattributed LM Studio diagnostics stay server-level (2.4) | The log has no request-scoped correlation field |
| Q47 | 2026-11-05 | An evidence location is any location identifying one entry plus the representation version (6.1) | apsis keeps entry identifiers, not source positions; the quote is the content check; an unresolved location defers the candidate (11.5) |
| Q48 | 2026-11-05 | Add search, recall and session-registration operations (14.6–14.8) | Local-model tools need search and recall; runs hand sessions over for indexing |
| Q49 | 2026-11-05 | Retrieval and search limits are in estimated tokens, with the estimate stated | Consumers budget in tokens |
| Q50 | 2026-11-05 | Feedback carries the outcome's basis: user-confirmed, check-confirmed with the check named, or unknown (14.5) | Lets 13.3 use checked outcomes without trusting unverified reports |
| Q51 | 2026-11-05 | Configuration can mark sources and origins non-interactive; Codex exec streams and unmatched LM Studio sessions default to non-interactive; an unmapped origin counts as interactive and is reported (2.9) | Those sources record no origin; tool-written prompts must not count as user statements |
| Q52 | 2026-11-05 | A late registration reclassifies the session's prompts and queues affected knowledge for reassessment (2.10) | Registration is the only guard for tool-started sessions |
| Q53 | 2026-11-05 | A registration can mark entries quoting the user's own words; they count as user statements (2.9, 14.8) | Otherwise the user's relayed words are lost |
| Q54 | 2026-11-05 | Sessions carry a workflow from registration; registration carries source, correlation identifier, workflow and project (2.2, 14.8) | Workflow-scoped knowledge needs the attribute |
| Q55 | 2026-11-05 | Feedback marks each revision as cited or present-only; present-only outcomes are association; a repeated feedback identifier changes nothing (14.5) | Delivered knowledge must not reinforce itself |
| Q56 | 2026-11-05 | For a matched interaction, content comes from the harness or tool session and server metadata from the log; truncated log content only when it is the only copy (2.4) | Exec streams record no prompt |
| Q57 | 2026-11-05 | Retrieval accepts any of domain, project and workflow, returns retained revisions only and states omissions; recall includes status; requester defaults to `user`; only user invocations open the browser (1.1, 10.1, 14.2, 14.7) | Running proposals are not knowledge; dismissed items must not look usable |
| Q58 | 2026-11-07 | Knowledge affected by a late registration is marked pending reassessment and not withdrawn (2.10) | Keeps knowledge usable while exposing doubt |
| Q59 | 2026-11-07 | An active "approach worked" claim needs a confirmed successful outcome; a confirmed failure counts against (13.3) | A confirmed failure must not qualify |
| Q60 | 2026-11-07 | What a later dream may do in a repository an earlier dream merged but did not deploy is a design question, with durable records of adoption steps (Design Handoff) | 9.15 already governs resume |
| Q62 | 2026-11-14 | Session sources also name Copilot, Kiro CLI and Kiro IDE (2.1) | apsis reads all three; Copilot has no origin mapping (apsis Q96), so it counts as interactive and is reported under 2.9 |
| Q63 | 2026-11-14 | A session's model is attributed per entry, falling back to the first recorded model (2.2) | apsis preserves per-entry model changes (Decision 29) |
| Q64 | 2026-11-14 | Decision 6 accepted | Requirements 13 to 15 depend on it |
| Q65 | 2026-11-14 | The orbit baseline is `origin/main` at 4bf9776; both parent specs are complete and accepted, and section 3 is unchanged | Main was reset to a squash of the merged PR |

---

## Decision 1: Auto-Apply When Every Check Passes on the Merged Result

**Date**: 2026-11-04
**Status**: accepted

### Context

Dreams change skills, rules, MCP configuration and tooling. Harnesses link to the main checkout's working tree, so deploying from a dream worktree would repoint them at a temporary folder. Checks on the branch alone miss conflicts with newer commits on main. The user wants low friction and treats dreaming as trusted automation; checks and restrictions are ordinary improvement targets.

### Decision

Auto-apply is enabled in the user's configuration:
- One branch per repository, one commit per change, generate commands run on the branch.
- Every configured lint and test command runs once on the merge of the branch into the default branch, in a separate working copy. Any failure blocks auto-apply; there is no baseline run. A repository with no configured checks is proposal-only.
- The merge is one commit in the user's checkout, only when it is on the default branch, has nothing in the way, and its HEAD has not moved since the checks. Deploy runs from that checkout.
- If deploy fails, revert and redeploy. Linked repositories are checked together and rolled back together.
- No category of change is held for manual approval.

### Rationale

What goes live is what was tested, from the checkout harnesses use. One pass/fail rule is simple, and one commit per change keeps each change and dream revertable.

### Alternatives Considered

- **Proposal only**: Rejected by the user as too much friction.
- **Hold back risky categories**: Rejected by the user in favour of uniform treatment.
- **Merge without deploy**: Rejected: harnesses would be out of step.
- **Check the branch and fast-forward from a worktree**: Rejected: tests a different tree and deploying elsewhere repoints live links.
- **Protect checks from dream changes**: Rejected by the user.
- **Exempt checks already failing on main**: Rejected: needs baseline machinery and cannot show a worse suite.

### Consequences

**Positive:**
- Improvements reach every harness without a manual step.
- Deployed content equals checked content; each change and dream can be reverted.

**Negative:**
- Passing checks does not prove behaviour improved.
- Auto-apply waits on dirty or non-default checkouts, and unrelated failures block it.
- MCP, hook and permission changes go live unreviewed; run dreaming only where that is acceptable.

---

## Decision 2: Backend-Neutral Roles; Harnesses Run Tool-Using Roles

**Date**: 2026-11-04
**Status**: accepted

### Context

The user runs Claude Code and Codex on subscriptions and local models through LM Studio. Dreaming must not depend on one of them or stop at a usage limit. A direct LM Studio call has no skill loader, file tools, `gh` or MCP loop, and the shared devtools definition includes agent-launching tools that would escape the program's accounting.

### Decision

Reader, reviewer, researcher and author each choose a backend in configuration, with an ordered fallback list and per-run override; calls run one at a time. Tool-using roles run through Claude Code or Codex, on a cloud provider or LM Studio; direct LM Studio calls serve tool-free roles only. Readers and reviewers get no tools; researchers get read, web search and fetch (devtools) and PR-review access; authors get what they need to prepare a change. Tools come from the shared MCP definitions through an explicit allowlist, with no agent-launch tools and no other user or project instructions, hooks, skills or servers. The program starts and counts every call. A backend that cannot meet a role's tools or isolation is skipped with a reason; when none remains, the dream saves progress and exits as partial.

### Rationale

Per-role backends let cheap work run locally and judgement run on a stronger model without code changes. Existing harnesses already execute tools, and explicit lists bound context and cost.

### Alternatives Considered

- **Local first, cloud opt-in**: Rejected by the user as a needless constraint.
- **Local only**: Rejected: caps quality and excludes the harnesses to improve.
- **Cloud by default**: Rejected: makes the cheap path the exception.
- **Direct LM Studio for every role**: Rejected: research and authoring need tools.
- **A new tool-execution loop**: Rejected unless the FOSS assessment (12.2) finds a gap.
- **Full devtools passthrough**: Rejected: adds context and unaccounted delegation.
- **Parallel calls**: Rejected for now (Q4, Q17).

### Consequences

**Positive:**
- One subscription's limit does not stop a dream; role backends can be tuned from statistics.
- Local models can research and author through existing tooling.

**Negative:**
- Each harness and provider pairing must be verified; isolation differs by version.
- LM Studio alone is not enough for tool-using roles.
- Output quality varies, so findings record backend and model.

---

## Decision 3: Treat All Transcripts Alike; Scrub Public Output

**Date**: 2026-11-04
**Status**: accepted

### Context

Transcripts span personal and client-looking projects. agentic-coding and orbit are public. Observations store verbatim quotes.

### Decision

Every transcript is eligible for every backend; there is no per-project routing. The store lives outside every git repository. Changes to a public repository are scanned for transcript text, credentials, tokens and private names, and withheld on a match. The names list is kept only in files outside every repository.

### Rationale

The user chose no project distinction. The same backends already saw these transcripts, so the remaining risk is publication, which the store location and scan address.

### Alternatives Considered

- **Local-only project list**: Rejected by the user as unnecessary.
- **Exclusion list**: Rejected: loses lessons from that work.
- **Scan terms in default-branch configuration**: Rejected: the branch is public.

### Consequences

**Positive:**
- No per-project configuration; no lessons lost.
- Public repositories get only scanned changes.

**Negative:**
- A scan can miss identifiers it does not recognise.
- The default is wrong for a work machine.

---

## Decision 5: A Program Runs the Dream; Models Make Judgements

**Date**: 2026-11-04
**Status**: accepted

### Context

The user wants context separated between an orchestrator and narrow workers. Dreams must lock, dry-run, resume, deduplicate, apply thresholds and gate merges identically every time, with any role movable between backends (Decision 2).

### Decision

The program holds control flow and all state on disk. Model calls are stateless judgements in four roles, each given only its inputs and tools and returning a defined structure. The program plus the reviewer, which sees summaries and never full transcripts, is the "orchestrator". Whether the program is new or adapted FOSS is settled by the design (12.2).

### Rationale

An agent running the loop keeps state in one context that cannot change backend or survive a crash, and its adherence to gates varies. Stateless calls over on-disk state can be retried, resumed and moved; reviewer input stays bounded.

### Alternatives Considered

- **LLM agent as orchestrator**: Rejected: state is tied to one context and backend, and gates depend on instruction following.
- **Program for gates, one agent for the rest**: Rejected: one session would hold transcripts and the cross-session view together.

### Consequences

**Positive:**
- Resume, fallback and adoption behave identically each run.
- Each role can use the cheapest suitable backend; reviewer input stays bounded.

**Negative:**
- The program owns more logic, which needs tests.
- Roles cannot improvise; new steps need program changes, which dreams may propose (7.4).

---

## Decision 6: Portable Learning Foundation with Initial Workspace Integrations

**Date**: 2026-11-05
**Status**: accepted

### Context

The user wants refinement and personal learning to underpin personalised tooling, possibly with a web frontend. Repository commits alone cannot hold preferences and lessons that need no file change, and tying access to the agentic-coding checkout would limit other consumers.

### Decision

Keep the spec and initial integrations in agentic-coding, but make dream operations and retained knowledge independently usable through versioned machine-readable operations and exchange. Repository adoption is an optional output with unchanged checks. Cover personalisation and learning recommendations; defer UI, server and hosting. Build on FOSS: session readers live in apsis, and the design assesses OpenClaw's dreaming code before choosing runtime, language or orchestration (12.2–12.3). Failures follow one retry, then the next backend, with raw errors recorded and vendor limit messages not parsed.

### Rationale

Separating evidence, revisable knowledge and its uses keeps refinement valuable without a repository change. A machine-readable boundary lets another frontend reuse it without choosing a server or framework.

### Alternatives Considered

- **Repository improvements as the only output**: Rejected: loses preferences that are not files.
- **A web product now**: Deferred: adds hosting and accounts not needed for the foundation.
- **An unstructured global profile**: Rejected: loses scope, counter-evidence and history.
- **A new standalone runtime before reuse research**: Rejected: portability does not justify duplicating FOSS.

### Consequences

**Positive:**
- Knowledge works across tools, domains and frontends; evidence, interpretation and corrections stay distinct.

**Negative:**
- Knowledge refinement and exchange need their own acceptance checks.
- Versioned contracts and histories add maintenance.
- A web deployment needs its own requirements.

---

## Decision 7: Tools Acting for the User May Start Dreams

**Date**: 2026-11-05
**Status**: accepted

### Context

Q3 limited starts to the user. The user's scheduled automation acts for them and reads dreaming's knowledge. Continuous refinement with less hands-on work needs more than manual starts.

### Decision

A tool acting for the user may start a dream through 14.1. Dreaming has no scheduler or idle detection, the run record names the requester, and budgets, checks and adoption rules are unchanged.

### Rationale

Scheduling stays in one place; only who may call the existing start operation changes.

### Alternatives Considered

- **Manual starts only**: Rejected: knowledge refreshes only when remembered.
- **Tool-started dreams without auto-apply**: Rejected: two adoption rule sets; checks already gate auto-apply.
- **A scheduler inside dreaming**: Rejected: duplicates the existing scheduler.
- **A cap on start frequency**: Rejected for now: the caller's schedule and per-run budgets bound spend.

### Consequences

**Positive:**
- Knowledge stays current; one scheduler.

**Negative:**
- Unattended dreams may merge and deploy while the user is away.
- Per-run limits do not cap start frequency.
- A scheduled dream can overlap the tool's own work and cause model reloads.
- A tool's start can resume a user-started interrupted dream (1.6, 9.15).

---

## Decision 8: Prompts in Tool-Started Sessions Are Not User Evidence

**Date**: 2026-11-05
**Status**: accepted

### Context

Preferences rest on user statements (13.1, 13.3), but many sessions are started by tools that write the prompts. apsis records the client origin without classifying it.

### Decision

When a session was registered by a tool (14.8), started by a dream, or has a recorded origin configuration marks non-interactive, attribute its prompts to that tool or an unknown author (2.9). They are not user statements, preferences or writing examples, except entries a registration marks as the user's own words; tool results and outcomes remain evidence. Sources with no recorded origin, such as Codex exec streams and unmatched LM Studio sessions, default to non-interactive (Q51).

### Rationale

Counting tool-written prompts would teach dreaming the automation's phrasing as the user's. A configured origin mapping keeps classification out of apsis and user-correctable.

### Alternatives Considered

- **Count every prompt as the user's**: Rejected: corrupts personal knowledge.
- **Rely on registration alone**: Rejected: most headless sessions are unregistered.
- **Treat sessions with no origin as unknown-author**: Rejected: Copilot and Kiro record no origin and are mostly interactive.

### Consequences

**Positive:**
- Preference and style knowledge rests on the user's own words; tool-started sessions still inform tool and workflow lenses.

**Negative:**
- Prompts typed into a headless run are not counted.
- The user's words arrive via a tool only if it marks them (Q53).
- The origin mapping needs updating as harnesses add entry points.
