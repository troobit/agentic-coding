---
name: nextup
description: The universal entry point for a session. Reads the nextup.md user zone, works out where you are, and routes each job to the right next step — execute the user's instructions directly, run a PRD to completion via engage, honour an act-autonomously flag, resume a spec phase, start a fresh spec, send a small job straight to a focused skill, fan several independent small jobs out to parallel sub-agents, recommend implementation, or close out the session. Use when the user says "/nextup", "run nextup", "what's next", "pick up where we left off", "close out", "wrap up", or starts a session without saying which command to run.
---

# Nextup — a pure router

`/nextup` is the front door to a session: the user thinks outside Claude, writes instructions into `nextup.md`, and enters — the user zone is arbitrary instructions, treated like any prompt. `/nextup` routes: read the intent, pick the lane and the skill, dispatch. It keeps **no status record of its own** — the files in `specs/`, rune task lists, and `docs/agent-notes/` are the only record of progress, and anything the router itself learns or produces is said in plain English in this conversation. Run it from any branch, at any time; the branch is one signal for finding your feature, never a gate. The user has to be able to trust the routing blind, so every dispatch names the lane, the skill, and the one signal that decided it.

`/nextup` is the **boundary** between the gated and ungated worlds. On one side is heavyweight, spec-driven development — the `/starwave` chain, with its approval gates. On the other is everything ungated: direct execution of whatever the user wrote, lighter focused skills (fix a bug, make a small change, improve an existing file), and the PRD lane (`/prd` → `/engage`) that runs a body of work to completion without gates. Weigh the intent and send it down the right lane, preferring the lightest that genuinely fits; the gated lane is a recommendation for feature-shaped work, never an enforcement. The audience is often **non-technical**: every message you show the user is plain English — where they are and what happens next, no jargon.

## `nextup.md`

`nextup.md` lives at the repo root (gitignored; `nextup.example.md` is the tracked template it is seeded from). It is a **user-intent file**:

- The **user zone** — everything above the first recognised marker (`<!-- LM -->`; treat legacy `<!-- ML -->`, `<!-- nextup:machine -->`, or a `# What I want` heading as equivalent) — is the user's authoritative intent.
- Everything below that first marker is **not state**: ignore it — never read it as intent or status. The marker itself is a reserved anchor for tooling (`scripts/align.py` converges the template from it); the only line below it is an inert note saying so.
- You never modify an existing `nextup.md` — not the user zone, not anything else. The one write allowed: when the file is missing, seed it **verbatim** from `nextup.example.md` (whose user-zone placeholder documents the `act autonomously` flag), or write that same skeleton if the template is absent too.

**Worktrees.** `nextup.md` is gitignored, so it never travels into a linked git worktree. When running in a worktree without one, read the main worktree's `nextup.md` (first entry of `git worktree list`) user zone for intent — do this yourself; the user should never have to ask.

## Each run: open or close?

- **Close-out** — the user is wrapping up ("close out", "wrap up", "end the session", or user-zone text that asks to close). Run the bookkeeping sweep and stop — see [Close-out mode](#close-out-mode).
- **Open** (default) — everything else: read the state, route the intent.

## Open mode — route the intent

### 1. Find or seed `nextup.md`

A missing `nextup.md` never blocks — seed it and carry on. An empty user zone is not a dead end either — fall through to feature detection. Stop and ask, in plain English, *"What's the first version (your MVP) you'd like to build?"* only when there is genuinely nothing to go on: no user text, no spec folder matching the branch, and no **in-flight** spec. A spec folder is in-flight only if it holds at least one spec document with real content (`requirements.md`, `design.md`, `tasks.md`, `smolspec.md`, or a non-empty `userinput.md`); a folder of empty stubs gives you the feature *name*, not intent.

### 2. Identify the feature

In priority order:

1. **Explicit reference in the user zone wins.** If the user names a spec folder (`specs/foo/...`, `specs/bugfixes/baz/...`), that is the feature — read every file in it before deciding.
2. **Branch.** Run `git rev-parse --abbrev-ref HEAD`; if the name maps to an existing `specs/<name>` folder (stripping any `specs/` or `T-<n>/` prefix), that is the feature.
3. **Fresh idea.** If nothing matches, treat the user-zone text as a fresh idea — step 5 picks the lane. The first spec of a project is conventionally the **MVP** (`specs/mvp/`), the smallest first version. A stub-only `specs/mvp/` gives the name but no intent: if the user zone describes the MVP, dispatch `/starwave:creating-spec` and pass it through; if the user zone is also empty, ask for the MVP first.

### 3. Read the true state

The files in `specs/{feature}/` are the source of truth for how far the work has got. Read what is present. A `prd.md` in the folder marks the work as PRD-lane — step 5 routes it to `/engage`. If `decision_log.md` exists, read it and mention you did.

**After a `/sendit` handoff:** when the previous session ended with `/sendit` shipping spec docs for review and this run's user zone carries no change requests, that **counts as approval** of the documents that were sent — continue to the next phase. No review state is stored anywhere; the user zone is the whole signal.

### 4. Honour explicit skill directives

If the user zone names a skill ("run `/starwave:smolspec`", "`/fix-bug` this"), dispatch to it — this overrides the lane inference in step 5. Arguments passed to `/nextup` count as user-zone text for this run. When a directive contradicts the files (asks for `/starwave:design` with no `requirements.md`), the files win on state: name the conflict plainly, dispatch the nearest achievable step to what was asked, and say what you skipped and why. Never hard-refuse — a run that ends with a refusal and zero work is a failure.

### 5. Route each job to its lane

Pick a **lane** by the weight of the intent, then route within it. Don't push a one-line fix through a full spec, and don't smuggle a real feature past requirements. When the user zone plainly asks for something to be done, do it or dispatch it — never withhold direct execution in favour of a process.

**Direct lane — instructions that don't call for spec work.** Most user-zone text is just instructions: run this, update that, investigate the other. Execute or dispatch them exactly as you would any prompt — no spec folder, no starwave routing. This is the one lane where you may do the work inline yourself.

**PRD lane — a written PRD runs ungated to completion.** When the user zone references a PRD, or `specs/{name}/prd.md` exists for the named work, route it to `/engage`. When the user zone asks for a PRD that doesn't exist yet, route to `/prd` to author it.

**The autonomy flag.** A user-zone line reading `act autonomously` (canonical; treat obvious variants like `autonomous: true` the same) flips the preference to the ungated lane end-to-end, because approval gates block fanning out parallel development attempts. With the flag set: feature-shaped work goes down the PRD lane — derive `specs/{name}/prd.md` from the user-zone text via `/prd` with no review pauses (the user zone stands in for the clarifying answers), then execute via `/engage`, one dispatch carrying both steps — and a complete gated spec dispatches straight to `/make-it-so` instead of stopping at a recommendation. No approval gates anywhere: the flag is the user's sign-off in writing. Route into the gated lane only when the user zone explicitly demands a spec.

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

Iterative, in-place improvements to something that already exists stay in the light lane. If you're unsure whether a change is "minor", start at `/starwave:smolspec` — it escalates to a full spec when the work turns out bigger than it looked.

**Spec lane — substantial features are recommended into the starwave chain.** Route by the earliest unmet need:

| State of `specs/{feature}/` | Route to |
|---|---|
| No folder, or only a stub / fresh idea | `/starwave:creating-spec` |
| `requirements.md` only | `/starwave:design` |
| `requirements.md` + `design.md`, no `tasks.md` | `/starwave:tasks` |
| `smolspec.md`, no `tasks.md` | `/starwave:tasks` |
| spec complete (`requirements.md` + `design.md` + `tasks.md`, or `smolspec.md` + `tasks.md`) | **Recommend implementation** (below) |

**When the spec is complete**, tell the user in plain English that it's ready and recommend `/make-it-so` to build all tasks, or `/next-task` to do them one at a time. Recommend; do not invoke — execution is the user's call. (With the autonomy flag set, that call is already in writing: dispatch `/make-it-so` instead of stopping.) If the user zone carries a `T-<number>` ticket, pass it through to the dispatched skill so its Transit integration can move the ticket — do not call `mcp__transit__*` yourself.

### 5b. One job or many?

Split the user zone into **jobs**: independently completable pieces that share no files and no ordering. Most runs carry one job — hand it off inline as step 5 routed it. When there are several, route each through step 5 on its own, then split by whether it can run unattended:

- **Unattended-safe jobs** — direct-lane or light-lane work that runs start to finish without stopping to ask the user — fan out in parallel. Spawn one sub-agent per job **in a single message**, each told to invoke that job's routed skill with the job's user-zone text as input. Jobs that mutate files each get an isolated git worktree so parallel commits don't race. You stay on as overseer: wait for all to return, surface any failure plainly instead of masking it, and report every job's outcome in the session's closing message.
- **Gated jobs** — anything in the spec lane, because requirements and design need user sign-off a sub-agent cannot collect — never go to a sub-agent. Route the most important one inline, and restate the ones you could not dispatch in the closing message so the user can bring them back next run.

A batch of same-shaped bug fixes is not a nextup fan-out — `/bug-blitz` owns that pipeline; route the whole batch there. A job you dispatched belongs to its skill or sub-agent — you don't implement, review, or commit it yourself on top; only a direct-lane job you kept inline is yours to do. Before dispatching, tell the user in one or two plain sentences per job: which job it is, the lane and the skill (or direct execution) you chose, and the deciding signal (a path from the user zone, the branch name, an explicit `/...` directive, the autonomy flag). Then dispatch and **pass the user-zone text as the input** — inline for a single job, via the sub-agent prompts for a fan-out — so the user never retypes their idea. You MUST NOT continue past the dispatch: inline, the routed skill owns the rest of the turn; in a fan-out, your last act is reporting the sub-agents' outcomes. Either way the user returns to `/nextup` next session to pick up again.

## Close-out mode

A bookkeeping sweep, then stop — nothing is written to `nextup.md`:

1. **Re-read the ground truth** — the spec files in `specs/{feature}/` and the git state (branch, recent commits, `git status`) — so the handoff reflects reality, not memory.
2. **Sweep for loose ends.** Scan the session for flagged-but-untracked items ("worth a follow-up", "separate ticket", "worth a regression test"). Add each to the feature's active tasks file via the rune skill; if there is no active tasks file, list them in the closing message instead.
3. If any spec document changed this session, run `/specs-overview` once to regenerate `specs/OVERVIEW.md` — never hand-edit it.
4. If a naming or canonicality conflict was adjudicated this session, record it in the feature's `decision_log.md` so it isn't re-litigated.
5. **Close in plain English**: what this session established, what was decided, what's blocked, and the concrete next step with the skill that runs it. That message plus `specs/OVERVIEW.md` is the at-a-glance status between sessions. Then stop — do not route or dispatch.

### Interrupts

When the user interrupts or asks to pause mid-run, give a brief in-chat handoff — where things stand and the concrete next step — and stop. Nothing is written anywhere; a pause is a spoken close-out with whatever ground truth you have.

## Hard rules

- You never write `nextup.md` (seeding a missing one is the sole exception) and never read anything below its first marker as intent or state. Routing itself writes no other files; a direct-lane job you execute inline writes whatever the instruction calls for, like any prompt.
- You **never** create or write anything under `specs/` — those folders are owned by the starwave and PRD skills; you read them, the chain writes them. **Close-out bookkeeping is the one exception**: the sweep may add follow-up tasks via the rune skill, append adjudicated decisions to `decision_log.md`, and regenerate `specs/OVERVIEW.md` via `/specs-overview`.
- In the **gated lane** you are a dispatcher, not an implementer: you never write a spec feature's code, run its tests, or fix it inline, and without the autonomy flag you never invoke execution skills (`/make-it-so`, `/next-task`) — when a spec is complete you **recommend** and stop. The ungated lanes are different: a direct-lane instruction may be executed right here, and the autonomy flag dispatches execution end-to-end. Sub-agents run one skill each; deeper fan-out belongs to the skill itself.
- The user zone is authoritative. When it conflicts with the files, follow the user and surface the conflict.
- Raise blockers fast and in plain English — "I can't tell which feature you mean — is it X or Y?" is the right output when inputs are genuinely ambiguous.
- One run does one mode: open (read, route, execute or dispatch — one job inline or several via parallel sub-agents) or close out (sweep, report, stop). Never proceed past the dispatch.
