---
name: spout
description: Report the current state of a repository's specs, the discrete next steps to take, and where new work belongs — an existing spec, a new spec, or (rarely, with a named reason) neither. Writes a single regenerated SPOUT.md at the repo root and nothing else. Read-only over the repo: it names the exact command for every step but never runs the work. Chains /explain-like. Written for a person to read and act on — prose and tables, no serialised output. Use when the user asks "what's the state of the specs", "what's outstanding", "where should this work go", "summarise this codebase", "spout". Not a stage of the spec workflow — it runs at any time, on any branch, without starting or advancing a spec.
---

# Spout

Produce **one document** — `SPOUT.md` at the repo root — that answers three questions: what state is every spec in, what are the discrete next steps, and **where does new work belong**. Every step names the exact invocation that performs it and the larger goal it serves, so a reader can act on any line without holding the rest of the repo in their head.

The document is **written for a person**. No JSON, no serialised step list, no schema — a reader should be able to open it, read a row, and do the thing. Structured state for machines belongs in `docs/agent-notes/` if it is wanted at all; duplicating the steps into a parseable block would only create a second copy to drift.

Spout is an **orientation tool**, not a stage of the spec workflow. Complex systems outrun anyone's working memory — expert and newcomer alike need the code areas, the drivers behind them, and the reasons a thing is half-finished summarised before they can act. Spout knows the starwave process and defaults to it when guiding new work, but it neither starts nor advances a spec: run it at any time, on any branch.

Spout is a **reporter, not an actor**. It reads the repo, writes `SPOUT.md`, and stops. It does not author specs, fix findings, run tasks, or dispatch skills — the one exception is chaining `/explain-like` to resolve ambiguity (see [Ambiguity](#5-ambiguity--chain-explain-like)). Guidance is delivered as a written recommendation with its reason, never as a dispatch.

## Where spout sits

| Skill | Owns | Writes |
|---|---|---|
| `/specs-overview` | The catalogue of what specs exist | `specs/OVERVIEW.md` |
| **`/spout`** | **Standing state + next steps, as a document** | **`SPOUT.md` only** |

Spout consumes ONLY extant code and documentation, and makes no changes to any code. If `specs/OVERVIEW.md` is missing or stale, that is a *step spout reports* (`SP-INDEX`), not work spout does.

## Placement — where work belongs

Whenever spout finds work that no spec covers, it must say where that work lands. **The default is always the starwave spec process.** Work leaves that process only for a reason spout names explicitly in the report; an unnamed exception is not an exception, it is an omission.

Apply the ladder in order and stop at the first rung that fits:

1. **An existing spec already owns this surface** → `SP-EXTEND:<spec>`. Amending a spec that covers the same problem beats opening a second one — two specs on one surface is the drift `/spec-janitor` exists to clean up (`SJ-SUP-001`). Name the spec and the section the work extends.
2. **No spec owns it** → `SP-SPEC:<kebab-name>` → `/starwave:creating-spec`. Do **not** decide between smolspec and a full spec here; `/starwave:creating-spec` opens with its own scope assessment and owns that call. Spout says *a spec is needed*, never *which size*.
3. **A named exception applies** → `SP-DIRECT:<kebab-name>`, and the step MUST carry the exception name from this closed list:

| Exception | Covers | Still not exempt when |
|---|---|---|
| `brevity` | A change so small the spec would outweigh it | It adds a capability, changes an interface, or needs a decision recorded — then it is a spec, and `/starwave:creating-spec` may size it down to a smolspec |
| `doc-only` | Documentation, comments, changelog prose — no behaviour change | The document is itself a spec artifact (that is `SP-EXTEND`) |
| `file-transfer` | Copying or syncing files between repos with no authoring | The copy is adapted, rewritten, or re-scoped on arrival |
| `operational` | A one-off command, investigation, or query leaving no artifact | It produces code, config, or a document that outlives the session |

Anything not matching a row defaults to rung 1 or 2. When two rungs are arguable, take the **earlier** one — over-specifying is recoverable, under-specifying is the failure this ladder exists to prevent. When the choice between rungs 1 and 2 is genuinely undecidable from the files, that is an [ambiguity](#5-ambiguity--chain-explain-like), not a coin toss.

## Arguments

`/spout` — whole repo. `/spout <spec-path|spec-name>` — scope the report to one spec, still writing the whole document (out-of-scope specs collapse to one row each in [Spec state](#spec-state) with no steps). `/spout "<focus>"` — free text narrows which steps get ranked first and is recorded verbatim in the header.

## Workflow

### 1. Preflight

- `git rev-parse --show-toplevel` for the repo root; `SPOUT.md` always lands there (not under `specs/`), because spout must also report on repos that have no `specs/`.
- Read the existing `SPOUT.md` if present — specifically the step IDs in its Next steps table — and hold them for the [Since last run](#6-delta) delta. Never merge its prose forward; it is regenerated wholesale.
- `date +%F` for the generation date. `git log -1 --format=%h` for the commit the report describes.
- Check `specs/` exists. If it does not, go to [No specs](#no-specs).

### 2. Read the state

Read in this order; later sources override earlier ones on conflict, and every claim in the report must trace to one of them.

1. `specs/OVERVIEW.md` — for curated display names, domains and summaries only. **Never** trust its Status column; recompute.
2. Each spec folder's documents — mode is recognised from primary documents alone, per the spec-janitor conventions: `requirements.md` + `design.md` → full; `smolspec.md` → smol; `prd.md` → PRD lane; `report.md` under `specs/bugfixes/<entry>/` → bugfix.
3. Task files (`tasks.md`, `tasks-*.md`) — via the three greps in [Task state](#task-state--regex-first), never by iterating files one at a time.
4. `docs/agent-notes/` — read only the notes matching specs that have open steps; use them for the *why* in evidence lines, never as a source of status.
5. `git log --format=%ad --date=short -- specs/<dir>` per spec for last-touched, and `git log --oneline -20` for repo-level context.
6. `python3 <spec-janitor-skill-dir>/spec_lint.py . --json` when the auditor is reachable, **without `--fix`**. Exit 1 means findings, not failure. Findings become `SP-HYGIENE` steps, never repairs.

Parallelise the git lookups and file reads.

### Task state — regex first

Task status is the single biggest input to the report and the easiest to get slowly. **Never loop over task files.** Three repo-wide greps answer every task question in three calls regardless of repo size, and the line numbers they return let you jump straight to any task without reading a file end to end:

```bash
# 1. Every incomplete task in the repo, with file and line — the primary signal
grep -rnE --include='tasks*.md' -e '^[[:space:]]*- \[[ ~/-]\] ' specs

# 2 & 3. Per-file totals and completions, for status derivation
grep -rcE --include='tasks*.md' -e '^[[:space:]]*- \[[ xX~/-]\] ' specs | grep -v ':0$'
grep -rcE --include='tasks*.md' -e '^[[:space:]]*- \[[xX]\] '      specs | grep -v ':0$'
```

Grep 1 is the one that matters: **empty output means every task in the repo is complete** (exit 1), and no further task reading is needed at all. Its output is already the evidence line for each `SP-IMPL` step — `file:line:` plus the task title and its `<!-- id:xxxxxxx -->` marker, in one pass.

Regex notes, each load-bearing:

- The marker class `[ ~/-]` is exactly rune's incomplete set: `[ ]` pending, plus `[-]`, `[~]`, `[/]` in progress. `[xX]` is the only complete form. Enumerate the markers — never `[^x]`, which swallows malformed lines as tasks. The `-` sits last in the class so it stays a literal.
- Leading `[[:space:]]*` catches indented subtasks; the trailing space after `\]` rejects markdown link syntax and bare `[ ]` in prose.
- `--include='tasks*.md'` scopes to task files. Add `--exclude-dir=bugfixes` when bugfix entries would otherwise be counted as spec tasks.
- `-e` guards the pattern, which begins with a bracket class; `-rl` swaps grep 1 for a filename-only pre-filter when you only need *which* specs have open work.

Then, and **only for the files grep 1 named**:

- `rune list <file> --format json` when `rune` is on PATH — for task IDs, blocked-by edges and streams.
- Absent rune, a ~10-line Read at the reported line number for that task's detail lines (`Blocked-by:`, `Stream:`, `Requirements:`).

Files with no open tasks need neither call — greps 2 and 3 fully determine their status. On a repo where most specs are finished, that is the difference between two enrichment calls and dozens.

**Human gates.** A task matching `- [ ] N. STOP` (or whose detail lines say a human reviews, pushes, or decides) is a decision gate, not agent work. It still emits `SP-IMPL`, but its `run` is the human action — `git log --oneline origin/main..HEAD` before a push review, say — never `/next-task`, which would hand a human's decision to an agent. Say plainly in the report when a spec's only open tasks are gates.

### 3. Derive steps

A **step** is one discrete action with an exact invocation. The kinds are a closed set — do not invent others:

| Kind | Fires when | Invocation |
|---|---|---|
| `SP-EXTEND` | Uncovered work that an existing spec's surface already owns (ladder rung 1) | Amend that spec — `/starwave:requirements` for a full spec, `/starwave:smolspec` for a smol one |
| `SP-SPEC` | Uncovered work no spec owns, or a folder of empty stubs (ladder rung 2) | `/starwave:creating-spec` |
| `SP-DIRECT` | Uncovered work under a named exception (ladder rung 3) | The direct command or skill that does it — and the exception name |
| `SP-DESIGN` | `requirements.md` present, `design.md` absent | `/starwave:design` |
| `SP-TASKS` | Primary documents complete, no task file (spec-janitor `SJ-MODE-002`) | `/starwave:tasks` |
| `SP-IMPL` | A task file has open tasks (grep 1 above) | `/next-task <task-file>` (or `/make-it-so` for the whole spec) — but the human action for a gate |
| `SP-BUG` | A `specs/bugfixes/` entry whose `report.md` has no Resolution section | `/fix-bug <entry>` |
| `SP-HYGIENE` | `spec_lint.py` findings, or judgment drift visible while reading | `/spec-janitor` |
| `SP-INDEX` | `specs/OVERVIEW.md` missing, or its rows disagree with recomputed status | `/specs-overview` |
| `SP-CLOSE` | Every task complete but the spec is not marked done or superseded | Human: annotate the spec, then `/specs-overview` |
| `SP-EXPLAIN` | An ambiguity fired — see [step 5](#5-ambiguity--chain-explain-like) | `/explain-like <path>` |

**Step ID** is `<kind>:<scope>`, where scope is the spec's repo-relative path under `specs/` (e.g. `SP-DESIGN:estimation/pipeline`), or the literal `repo` for repo-wide steps (`SP-INDEX:repo`). IDs are deterministic: the same outstanding work yields the same ID on every run, which is what makes the delta and the diffs meaningful. Never put line numbers or dates in an ID.

Each step carries: the ID, a one-line imperative action, the exact invocation, readiness, its blockers, the **goal it serves**, and **evidence** — the file the step was derived from and why. A step with no evidence is not emitted. `SP-EXTEND`, `SP-SPEC` and `SP-DIRECT` additionally carry **placement** — the spec path the work joins, or `new:<kebab-name>` — and `SP-DIRECT` names its **exception**.

**The goal.** A discrete step is only worth doing if it moves something larger. Every step says what that is, in a few words, in the Serves column:

- With a `/spout "<focus>"` argument, the focus **is** the goal — say how each step advances it, and demote steps that advance nothing to a closing note rather than dropping them silently.
- Without one, the goal is read from the repo: the spec the work belongs to, the release or milestone the spec serves, or the standing convention the step upholds (e.g. "spec-before-commit, per `CLAUDE.md`").
- If a step serves no goal you can name from the files, that is worth saying plainly — an action nobody can justify is usually one to drop, and spout should surface it rather than pad the table.

**Uncovered work** — the input to the [placement ladder](#placement--where-work-belongs) — is found from these signals only, each of which becomes the step's evidence:

- Uncommitted or recent changes (`git status --porcelain`, `git log --oneline -20`) touching paths no spec's scope mentions.
- Ghost references: a spec document naming work no spec folder covers (`SJ-GHOST-001` shape).
- Follow-ups recorded in `docs/agent-notes/` with no task or spec behind them.
- A `/spout "<focus>"` argument describing work not yet specced.

Spout never invents work from what a repo "should probably have" — no signal, no step.

**Blockers.** A step is blocked when another step must complete first: the starwave chain orders `SP-SPEC → SP-DESIGN → SP-TASKS → SP-IMPL` within a spec, and rune `blocked-by` edges order work inside `SP-IMPL`. Blockers are step IDs, never prose. Cross-spec blockers are only recorded when a spec document states the dependency explicitly — never inferred from topic similarity.

### 4. Rank

Rank descending by, in order: **ready before blocked**; then steps that unblock other steps; then specs touched in the last 30 days; then kind order exactly as listed in the table above, top to bottom (`SP-EXTEND` first, `SP-EXPLAIN` last). Ties break on spec path, alphabetically, so the ordering is stable across runs.

Placement steps rank ahead of the rest of the chain deliberately: work with nowhere to live is the state most likely to bypass the spec process, so the report surfaces it before implementation detail.

The report opens with exactly one **Start here** line naming a single ready step ID and its invocation. If nothing is ready — every step blocked, or no steps at all — say that in one sentence instead of manufacturing an action.

### 5. Ambiguity — chain `/explain-like`

Emit `SP-EXPLAIN` and chain `/explain-like` when any of these objectively hold. Do not use judgement about whether something "feels" unclear:

1. Two step kinds fire for the same spec with no ordering between them.
2. A spec's documents contradict each other about direction, with no supersession annotation (`SJ-SUP-002` shape).
3. Open tasks reference requirements anchors that do not resolve (`SJ-REF-001` shape) — what to implement is not determinable.
4. A `/spout <focus>` argument maps to no spec, or to more than one.
5. A design document's next step depends on a decision absent from `decision_log.md`.
6. Uncovered work fits ladder rung 1 and rung 2 equally — two existing specs could plausibly absorb it, or it is unclear whether it extends a spec or opens one. Report both candidates; never split the difference.

On trigger: run `/explain-like` against the specific document, and fold its **Intermediate level** summary plus its **Validation Findings** into the Ambiguities section of `SPOUT.md`. **Decline explain-like's offer to save `explanation.md`** — spout emits one document, and `/specs-overview` treats `explanation.md` as session-scoped anyway.

Run the chain inline for at most the **three** highest-ranked ambiguities. List the remainder with their exact `/explain-like` invocations, and state in the report how many were listed rather than run — a truncated sweep must never read as a complete one.

### 6. Delta

Compare the previous run's step IDs (held from step 1) against this run's:

- **Resolved** — in the old set, absent now.
- **New** — absent from the old set.
- **Carried** — in both. For carried steps, note how many runs they have survived if the old block recorded it.

Omit the section entirely on a first run rather than printing three empty lists.

### 7. Write

Overwrite `SPOUT.md` wholesale. This is the only file spout writes, ever.

## Output structure

````markdown
# SPOUT — <repo name>

Generated <YYYY-MM-DD> at <short-sha> from <N> specs<, focused on "<focus>">.
Regenerated wholesale by `/spout` — do not hand-edit.

**Start here:** `SP-EXTEND:estimation/pipeline` — the retry-backoff work in the last three commits has no spec; amend `specs/estimation/pipeline/requirements.md` via `/starwave:requirements`.

## Next steps

| # | ID | Do this | Run | Serves | Ready |
|---|----|---------|-----|--------|-------|
| 1 | `SP-EXTEND:estimation/pipeline` | Fold retry-backoff into the pipeline spec's §Failure handling | `/starwave:requirements` | Spec-before-commit, per `CLAUDE.md` | yes |
| 2 | `SP-IMPL:estimation/pipeline` | Implement the 4 open tasks of 9 | `/next-task specs/estimation/pipeline/tasks.md` | Finishing the estimation pipeline | yes |
| 3 | `SP-DESIGN:capture/intake` | Author the design document | `/starwave:design` | Unblocking intake capture | blocked by `SP-SPEC:capture/intake` |

## Placement

Where uncovered work belongs. The default is the spec process; exceptions are named.

| ID | Work | Lands in | Why |
|----|------|----------|-----|
| `SP-EXTEND:estimation/pipeline` | Retry backoff (commits 32e32f8, ee1b7ea) | `estimation/pipeline` §Failure handling | Existing spec owns the retry surface |
| `SP-SPEC:audit-export` | CSV export of the audit log | new spec `audit-export` | New capability; no spec covers export |
| `SP-DIRECT:sync-brewfile` | Copy Brewfile from the tooling repo | no spec — `file-transfer` | Verbatim copy, no authoring |

## Spec state

| Spec | Mode | Status | Tasks | Last touched | Open steps |
|------|------|--------|-------|--------------|------------|
| estimation/pipeline | full | In Progress | 5/9 | 2026-08-11 | `SP-IMPL` |

## Ambiguities

### `SP-EXPLAIN:capture/intake`

**Why:** design.md §Storage and §Retention describe mutually exclusive schemes with no supersession marker.

<intermediate-level explanation and validation findings from /explain-like>

**To resolve:** run `/explain-like specs/capture/intake/design.md`, then record the outcome in `decision_log.md`.

## Since last run

- **Resolved:** `SP-TASKS:estimation/pipeline`
- **New:** `SP-EXPLAIN:capture/intake`
- **Carried:** `SP-INDEX:repo` (3 runs)

## Evidence

What each step rests on, so a reader can check the reasoning rather than take it on trust.

- `SP-EXTEND:estimation/pipeline` — `src/pipeline/retry.py` changed in `32e32f8`; no spec's scope mentions retry backoff.
- `SP-DIRECT:sync-brewfile` — `Brewfile` is a verbatim copy with no authoring, so the `file-transfer` exception applies.
````

Sections with no content are omitted, not printed empty. The document ends at the evidence — there is no serialised appendix.

## No specs

When `specs/` is absent or empty, keep the same document and the same step grammar, and infer succinctly:

- Read `git log --oneline -30`, `git status --porcelain`, the README, and any `docs/agent-notes/` — nothing else.
- Run the placement ladder over each coherent body of in-flight or obviously-next work. With no specs to extend, rung 1 never fires: every body of work is `SP-SPEC:<kebab-name>` → `/starwave:creating-spec`, unless a named exception makes it `SP-DIRECT`.
- The Spec state table is replaced by a short **Repo state** table (branch, unpushed commits, dirty paths); the Placement table stays.
- Prefer tables and lists over prose; cap inference at five steps and say so if more were possible.

A repo with no specs is the case where the spec-process default matters most — a first spec is conventionally the MVP (`specs/mvp/`), the smallest first version. Recommend it; do not create it.

Never create `specs/` or any spec folder to make the report tidier.

## Constraints

- MUST write `SPOUT.md` at the repo root and **nothing else** — no spec files, no source, no `specs/OVERVIEW.md`, no `explanation.md`. The single exception is an explicit user instruction in the invoking turn to write elsewhere or additionally.
- MUST be read-only over everything else: `rune list` only (never `add`/`update`/`complete`), `spec_lint.py` without `--fix`, git query commands only.
- MUST NOT dispatch or perform the work it reports. `/explain-like` is the only skill spout invokes.
- MUST give every step an ID from the closed kind set, an exact invocation, the goal it serves, and at least one piece of evidence.
- MUST be readable end to end by a person: prose, tables and lists only. MUST NOT emit JSON, YAML, or any serialised step list — structured state for machines belongs in `docs/agent-notes/`, not here.
- MUST default uncovered work to the starwave spec process, and MUST name the exception from the closed list whenever it does not. An `SP-DIRECT` step without an exception name is invalid output.
- MUST NOT size a new spec — `/starwave:creating-spec` owns the smolspec-versus-full assessment. Spout says a spec is needed, never which kind.
- MUST prefer extending an existing spec over opening a second one on the same surface.
- MUST recompute status from task files and git; MUST NOT copy a Status value from `specs/OVERVIEW.md`.
- MUST derive task state from the three repo-wide greps, honouring rune's `[-]`, `[~]`, `[/]` markers as incomplete. MUST NOT iterate task files one at a time, and MUST NOT call `rune list` on a file grep 1 did not name.
- MUST give a human gate the human action as its `run`, never `/next-task`.
- MUST state any cap it hit **in prose** — ambiguities listed rather than explained, inferred steps truncated — rather than letting a partial sweep read as complete.
- MUST produce identical step IDs across two runs with no intervening repo change; the document may differ only in its generation date and commit.
