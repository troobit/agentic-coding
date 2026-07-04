---
name: nextup
description: The universal entry point for a session. Reads nextup.md, works out where you are, keeps a plain-English progress record, and routes each job to the right next step — execute the user's instructions directly, run a PRD to completion via engage, honour an act-autonomously flag, resume a spec phase, start a fresh spec, send a small job straight to a focused skill, fan several independent small jobs out to parallel sub-agents, recommend implementation, or close out the session. Use when the user says "/nextup", "run nextup", "what's next", "pick up where we left off", "close out", "wrap up", or starts a session without saying which command to run.
---

# Nextup — the universal entry point

`/nextup` is the front door to a session: the user runs it so they never have to remember which skill to run or repeat context they already gave. The point of `nextup.md` is to let the user think outside Claude, write the commands, and enter — so the user zone is arbitrary instructions, treated like any prompt. When an instruction doesn't call for spec work, act on it directly. When it does — or when a focused skill owns the job — dispatch: read the intent, pick the right skill, and hand the work off. A single job hands off in this conversation as usual, and several independent jobs fan out to parallel sub-agents that each run their routed skill (see step 6b). The user has to be able to trust the routing blind, so every dispatch names the lane, the skill, and the one signal that decided it.

Run it from any branch, at any time. The branch is one signal for finding your feature, never a gate. All it needs is a `nextup.md`; if none exists it seeds one and still works.

`/nextup` is the **boundary** between the gated and ungated worlds. On one side is heavyweight, spec-driven development — the `/starwave` chain, with its approval gates. On the other is everything ungated: direct execution of whatever the user wrote, lighter focused skills (fix a bug, make a small change, iteratively improve an existing file), and the PRD lane (`/prd` → `/engage`) that runs a body of work to completion without gates. `/nextup` weighs the intent and sends it down the right lane. Prefer the lightest lane that genuinely fits; the gated lane is a recommendation for feature-shaped work, never an enforcement.

The audience is often **non-technical**. Every message you show the user is plain English — where they are and what happens next, no jargon. The spec files stay technical; your spoken status does not.

## `nextup.md`

`nextup.md` lives at the repo root and splits cleanly into a **user zone** and a **machine zone**:

```markdown
<!-- USER -->

<user inputs for next session — free-form instructions, run as written; add a line `act autonomously` to skip approval gates>

<!-- LM -->

## Where things stand

**Feature:** <name or "not started yet">
**Branch:** <branch>
**Stage:** <plain-English one-liner, e.g. "Writing requirements">

**Progress:**
- [ ] Scoped the work
- [ ] Requirements written
- [ ] Design written
- [ ] Tasks planned
- [ ] Branch created

**Next up:** <plain-English next action>

**Notes (latest first):**
- <date> — <what happened in one line>
```

**Markers.** The machine zone begins at the **first** line matching `<!-- LM -->`; everything above it is the user zone, which opens with `<!-- USER -->`. Legacy files stay valid: treat a `# What I want` heading, a `<!-- nextup:machine -->` marker, or `<!-- ML -->` as equivalent to `<!-- LM -->`, and parse the machine zone from whichever appears first. When you rewrite the machine zone, migrate any legacy marker to `<!-- LM -->`. Never add explanatory comments of your own to the template — the markers stay bare, and the only guidance text is the user-zone placeholder shipped in `nextup.example.md` (which documents the autonomy flag).

**Two rules govern the divide:**

- **The user zone wins.** It is the user's authoritative intent. If it contradicts the machine zone (the machine says "Design" but the user wrote "let's redo the requirements"), follow the user and surface the conflict in plain English.
- **The machine zone is disposable.** You rebuild it every run from the real source of truth — the files in `specs/{feature}/`. If it's stale, this run fixes it. You only ever rewrite below the marker; never touch the user zone. And it holds **only the template's fields** — feature, branch, stage, progress, next up, notes — never new sections.

## Each run: open or close?

Decide the mode first:

- **Close-out** — the user is wrapping up ("close out", "/nextup close out", "wrap up", "end the session", "save where we are", or user-zone text that asks to close). Capture a handoff into the machine zone and stop — see [Close-out mode](#close-out-mode).
- **Open** (default) — everything else. Read state and route the intent; follow the steps below.

## Open mode — route the intent

### 1. Find or seed `nextup.md`

Look for `nextup.md` at the repo root. If it's missing it never blocks — seed it (copy `nextup.example.md` if that tracked template exists, otherwise write the skeleton above) and carry on. With nothing else to go on, this run funnels into spec-driven development via `/starwave:creating-spec`. (`nextup.md` is gitignored; `nextup.example.md` is the tracked structure it's seeded from.)

**Worktrees.** `nextup.md` is gitignored, so it never travels into a linked git worktree. When running in a worktree and `nextup.md` is missing or stale, find the main worktree (first entry of `git worktree list`) and read its `nextup.md`: treat the main copy's user zone as the source of intent, and keep the machine zone local to this worktree. Do this merge yourself — the user should never have to ask for it.

An empty user zone is not a dead end — fall through to feature detection (step 2). Stop and ask, in plain English, *"What's the first version (your MVP) you'd like to build?"* only when there is genuinely nothing to go on: no user text, no spec folder matching the branch, and no **in-flight** spec. A spec folder is in-flight only if it holds at least one spec document with real content (`requirements.md`, `design.md`, `tasks.md`, `smolspec.md`, or a non-empty `userinput.md`); a folder of empty/stub files gives you the feature *name*, not intent — so an empty user zone plus a stub-only spec counts as "nothing to go on".

### 2. Identify the feature

In priority order:

1. **Explicit reference in the user zone wins.** If the user names a spec folder (`specs/foo/...`, `specs/bugfixes/baz/...`), that is the feature — read every file in it before deciding.
2. **Branch.** Run `git rev-parse --abbrev-ref HEAD`; if the name maps to an existing `specs/<name>` folder (stripping any `specs/` or `T-<n>/` prefix), that is the feature.
3. **Machine zone.** Otherwise, if the machine zone records a feature that still has a `specs/<name>` folder, use it.
4. **Fresh idea.** If nothing matches, treat the user-zone text as a fresh idea — step 6 picks the lane. The first spec of a project is conventionally the **MVP** (`specs/mvp/`), the smallest first version, with later refinements and features each becoming their own spec. A scaffolded but stub-only `specs/mvp/` gives you the name but no intent: if the user zone describes the MVP, dispatch `/starwave:creating-spec` and pass it through; if the user zone is also empty, ask for the MVP first.

### 3. Read the true state

The files in `specs/{feature}/` are the source of truth for how far the work has got — not the machine zone. Read what is present. A `prd.md` in the folder marks the work as PRD-lane — step 6 routes it to `/engage`. If `decision_log.md` exists, read it and mention you did.

### 4. Honour explicit skill directives

If the user zone names a skill ("run `/starwave:smolspec`", "continue with `/starwave:design`", "`/fix-bug` this"), dispatch to it — this overrides the lane inference in step 6. Arguments passed to `/nextup` count as user-zone text for this run. When a directive contradicts the files (asks for `/starwave:design` with no `requirements.md`), the files win on state: name the conflict plainly, dispatch the nearest achievable step to what was asked, and say what you skipped and why. Never hard-refuse — a run that ends with a refusal and zero work is a failure.

### 5. Update the machine zone

Rewrite everything below the marker to reflect what you just learned: feature, branch, a plain-English stage line, the progress checkboxes, the next action. Prepend a one-line dated note (`date +%Y-%m-%d`). Leave the user zone untouched. Do this **before** you hand off, because an inline dispatch ends the turn. (A parallel dispatch is the one exception where you're still around afterwards — update the machine zone again with the outcomes once the sub-agents return.)

### 6. Route each job to its lane

Pick a **lane** by the weight of the intent, then route within it. Prefer the lightest lane that genuinely fits — don't push a one-line fix through a full spec, and don't smuggle a real feature past requirements. The gated spec lane is a **recommendation** for feature-shaped work, never an enforcement: when the user zone plainly asks for something to be done, do it or dispatch it — never withhold direct execution in favour of a process.

**Direct lane — instructions that don't call for spec work.** Most user-zone text is just instructions: run this, update that, investigate the other. Execute or dispatch them exactly as you would any prompt — no spec folder, no starwave routing. This is the one lane where you may do the work inline yourself.

**PRD lane — a written PRD runs ungated to completion.** When the user zone references a PRD, or `specs/{name}/prd.md` exists for the named work, route it to `/engage`. When the user zone asks for a PRD that doesn't exist yet, route to `/prd` to author it.

**The autonomy flag.** A user-zone line reading `act autonomously` (canonical; treat obvious variants like `autonomous: true` or `act autonomous` the same) flips the preference to the ungated lane end-to-end, because approval gates block fanning out parallel development attempts. With the flag set: feature-shaped work goes down the PRD lane — derive `specs/{name}/prd.md` from the user-zone text via `/prd` with no review pauses (the user zone stands in for the clarifying answers), then execute it via `/engage`, one dispatch carrying both steps — and a complete gated spec dispatches straight to `/make-it-so` instead of stopping at a recommendation. No approval gates anywhere: the flag is the user's sign-off in writing. Route into the gated lane only when the user zone explicitly demands a spec.

For work that isn't plain instructions or a PRD, weigh intent by concrete signals, not vibes:

- **Light signals:** names an existing file or a specific defect; verbs like fix, tweak, rename, adjust, clean up; bounded to a few files; adds no new capability.
- **Spec signals:** a new capability or feature; several components touched; open design decisions or trade-offs; words like build, MVP, feature.
- A job matching both, or neither cleanly, starts at `/starwave:smolspec` — never guess it into the spec lane.

**Light lane — bounded intent goes straight to a focused skill.** No requirements/design ceremony:

| Intent | Route to |
|---|---|
| A specific bug to fix | `/fix-bug` |
| "Fix all the bugs" / a batch of open bugs | `/bug-blitz` (or `/blitz-merge` to fix and merge) |
| A minor change, or an iterative improvement to an existing file | `/starwave:smolspec` |

Iterative, in-place improvements to something that already exists (a skill, a doc, a config) stay in the light lane — they don't need a spec folder. If you're unsure whether a change is "minor", start it at `/starwave:smolspec`; that skill escalates to a full spec when the work turns out bigger than it looked, which keeps the funnel biased toward the lighter path without losing safety.

**Spec lane — substantial features are recommended into the starwave chain.** This is where feature-shaped work lands when no autonomy flag is set and the user zone doesn't ask for direct execution. Route by the earliest unmet need:

| State of `specs/{feature}/` | Route to |
|---|---|
| No folder, or only a stub / fresh idea | `/starwave:creating-spec` |
| `requirements.md` only | `/starwave:design` |
| `requirements.md` + `design.md`, no `tasks.md` | `/starwave:tasks` |
| `smolspec.md`, no `tasks.md` | `/starwave:tasks` |
| spec complete (`requirements.md` + `design.md` + `tasks.md`, or `smolspec.md` + `tasks.md`) | **Recommend implementation** (below) |

**When the spec is complete**, the workflow is done — tell the user in plain English that it's ready and recommend `/make-it-so` to build all tasks, or `/next-task` to do them one at a time. Recommend; do not invoke — execution is the user's call. (With the autonomy flag set, that call is already in writing: dispatch `/make-it-so` instead of stopping.)

If the user zone carries a `T-<number>` ticket, pass it through to the dispatched skill so its Transit integration can move the ticket. Do not call `mcp__transit__*` yourself.

### 6b. One job or many?

Split the user zone into **jobs**: independently completable pieces that share no files and no ordering. Most runs carry one job — hand it off inline as step 6 routed it. When there are several, route each job through step 6 on its own, then split by whether it can run unattended:

- **Unattended-safe jobs** — direct-lane or light-lane work that runs start to finish without stopping to ask the user (`/fix-bug`, a mechanical `/starwave:smolspec` change, a self-contained direct instruction) — fan out in parallel. Spawn one sub-agent per job **in a single message**, each told to invoke that job's routed skill with the job's user-zone text as input. Jobs that mutate files each get an isolated git worktree so parallel commits don't race. You stay on as overseer: wait for all to return, surface any failure plainly instead of masking it, then update the machine zone with the outcomes.
- **Gated jobs** — anything in the spec lane, because requirements and design need user sign-off a sub-agent cannot collect — never go to a sub-agent. Route the most important one inline, and queue the rest under **Next up** in the machine zone so the following `/nextup` picks them up.

A batch of same-shaped bug fixes is not a nextup fan-out — `/bug-blitz` already owns that pipeline; route the whole batch there. And a job you dispatched belongs to its skill or sub-agent — you don't implement, review, or commit it yourself on top; only a direct-lane job you kept inline is yours to do.

Before dispatching, tell the user in one or two plain sentences per job: which feature or job it is, where things stand, the lane and the skill (or direct execution) you chose, and the deciding signal (a path from the user zone, the branch name, an explicit `/...` directive, the autonomy flag). That evidence line is what lets the user trust the routing without re-checking it.

Then dispatch and **pass the user-zone text as the input** — inline for a single job, via the sub-agent prompts for a parallel fan-out — so the user never retypes their idea. That is how the chain reads `nextup.md` into the work without each skill opening the file itself.

You MUST NOT continue past the dispatch. Inline, the routed skill owns the rest of the turn (a direct-lane job you execute yourself simply runs to completion instead); in a fan-out, your last act is integrating the sub-agents' results into the machine zone and reporting the outcomes. Either way the user returns to `/nextup` next session to pick up again.

## Close-out mode

The mirror of opening: instead of routing forward, capture what just happened so the next `/nextup` (or the next person) picks up cleanly. It stays local — the lightweight counterpart to `/sendit`, which ships spec documents to Prism; close-out writes the machine zone plus the three bookkeeping artifacts named in step 2 (rune tasks, `decision_log.md`, regenerated `OVERVIEW.md`), nothing else.

1. **Re-read the ground truth** — the spec files in `specs/{feature}/` and the git state (`git rev-parse --abbrev-ref HEAD`, recent commits, `git status`) — so the handoff reflects reality, not memory.
2. **Sweep for loose ends.** Anything flagged during the session but never captured evaporates — don't let it:
   - Scan the session for flagged-but-untracked items ("worth a follow-up", "separate ticket", "worth a regression test"). Add each to the feature's active tasks file via the rune skill; if there is no active tasks file, list them under **Next up** in the machine zone instead.
   - If any spec document changed this session, run `/specs-overview` once to regenerate `specs/OVERVIEW.md` — never hand-edit it.
   - If a naming or canonicality conflict was adjudicated this session (which name or artifact is the real one), record it in the feature's `decision_log.md` before closing so it isn't re-litigated next session.
3. **Write the handoff into the machine zone.** Capture what this session established — what changed, what was decided, what's blocked, the clear next step — inside the template's existing fields: the stage line, **Next up**, and dated **Notes** lines. Never add sections beyond the template. **Next up** names the concrete next step *and the skill that runs it* (e.g. "run `/starwave:design` for the auth spec"), so the next `/nextup` routes without re-deriving it.
4. **Validate the structure.** Every close-out: confirm the `<!-- LM -->` marker is present — if it has been lost, repair it rather than appending a second machine zone — and strip any raw logs or command output from the file. A line earns its place only if it matters to future work.
5. **Prepend a dated note** (`date +%Y-%m-%d`) summarising the session in one line.
6. **Stop.** Do not route or dispatch — close-out ends the turn; the routing lives in **Next up**, not in this turn's output. Leave the user zone untouched.

### Interrupts

When the user interrupts or asks to pause mid-run, write the current state into the machine zone **first** — before finishing any in-flight work and without asking a single question — then stop. A pause request is a close-out with whatever ground truth you have.

## How the chain uses `nextup.md`

`nextup.md` is the shared handoff medium between the user and the work:

- **Intent persists** in the user zone. Because the tracked `nextup.example.md` ships the structure and travels with the repo, intent seeded there survives a fresh clone — the right home for it, not a hand-written file under `specs/`.
- **Into a spec:** when you dispatch a fresh idea, you pass the user-zone text to the target skill as input. That skill — never you — folds it into the right place (e.g. `specs/{feature}/userinput.md` and the requirements introduction).
- **Out to the user:** the machine zone you maintain is the at-a-glance status between sessions, and the handoff you write on close-out.

## Hard rules

- You maintain **only** the machine zone of `nextup.md` (below the marker). You never edit the user zone, and — outside the close-out bookkeeping exception in the next bullet — routing itself writes no other files. A direct-lane job you execute inline writes whatever the instruction calls for, like any prompt. (`/sendit` also writes the machine zone when it ships a spec; you rebuild the block from the spec files each run, so the two never conflict.)
- You **never** create or write anything under `specs/` — those folders are owned by the starwave and PRD skills and writing into them from outside corrupts the spec. You read them; the chain writes them. This includes `requirements.md`, `design.md`, `tasks.md`, `smolspec.md`, `prd.md`, and `userinput.md`. **Close-out bookkeeping is the one exception**: the sweep may add follow-up tasks via the rune skill, append adjudicated decisions to `decision_log.md`, and regenerate `specs/OVERVIEW.md` via `/specs-overview`.
- In the **gated lane** you are a dispatcher, not an implementer: you never write a spec feature's code, run its tests, or fix it inline, and without the autonomy flag you never invoke execution skills (`/make-it-so`, `/next-task`) — when a spec is complete you **recommend** and stop. The ungated lanes are different: a direct-lane instruction may be executed right here like any prompt, and the autonomy flag dispatches execution end-to-end. Dispatched work still happens only inside its routed skill: in this conversation for a single job, or inside the sub-agents you spawn for a parallel fan-out (step 6b). Sub-agents run one skill each; deeper fan-out belongs to the skill itself.
- The user zone is authoritative. When it conflicts with the machine zone or the files, follow the user and surface the conflict.
- Raise blockers fast and in plain English — "I can't tell which feature you mean — is it X or Y?" is the right output when inputs are genuinely ambiguous.
- One run does one mode: open (read, update the quick reference, execute or dispatch — one job inline or several via parallel sub-agents) or close out (capture the handoff and stop). Never proceed past the dispatch.
