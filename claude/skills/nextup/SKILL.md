---
name: nextup
description: The universal entry point for the starwave spec workflow. Reads nextup.md, works out where you are, keeps a plain-English progress record, and routes you to the right next step — resume a spec phase, start a fresh spec, send a small job straight to a focused skill, recommend implementation, or close out the session. Use when the user says "/nextup", "run nextup", "what's next", "pick up where we left off", "close out", "wrap up", or starts a session without saying which command to run.
---

# Nextup — the universal entry point for starwave

`/nextup` is the front door to a session: the user runs it so they never have to remember which skill to run or repeat context they already gave. It is a **router, not an executor** — it reads intent, funnels it to the one right next step, and hands off. It never runs the work itself, and any fan-out to agents or sub-agents lives in the skill it routes to, never here.

Run it from any branch, at any time. The branch is one signal for finding your feature, never a gate. All it needs is a `nextup.md`; if none exists it seeds one and still works.

`/nextup` is the **boundary** between two worlds. On one side is heavyweight, spec-driven development — the `/starwave` chain. On the other are lighter, direct interactions: fix a bug, make a small change, iteratively improve an existing file. `/nextup` weighs the intent and sends it down the right lane. Its own job stays thin: classify, hand off. Prefer the lightest lane that genuinely fits.

The audience is often **non-technical**. Every message you show the user is plain English — where they are and what happens next, no jargon. The spec files stay technical; your spoken status does not.

## `nextup.md`

`nextup.md` lives at the repo root and splits cleanly into a **user zone** and a **machine zone**:

```markdown
<!-- USER -->

<what the user wants to build or do next, in their own words>

<!-- ML -->

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

**Markers.** The machine zone begins at the **first** line matching `<!-- ML -->` ("ML" = machine layer); everything above it is the user zone. Legacy files stay valid: treat a `# What I want` heading and a `<!-- nextup:machine -->` marker as equivalent to `<!-- USER -->` and `<!-- ML -->`, and parse the machine zone from whichever appears first. When you rewrite, keep whichever marker style the file already uses. Never write explanatory comments for the user into the template — seed and rewrite files with bare markers only.

**Two rules govern the divide:**

- **The user zone wins.** It is the user's authoritative intent. If it contradicts the machine zone (the machine says "Design" but the user wrote "let's redo the requirements"), follow the user and surface the conflict in plain English.
- **The machine zone is disposable.** You rebuild it every run from the real source of truth — the files in `specs/{feature}/`. If it's stale, this run fixes it. You only ever rewrite below the marker; never touch the user zone.

## Each run: open or close?

Decide the mode first:

- **Close-out** — the user is wrapping up ("close out", "/nextup close out", "wrap up", "end the session", "save where we are", or user-zone text that asks to close). Capture a handoff into the machine zone and stop — see [Close-out mode](#close-out-mode).
- **Open** (default) — everything else. Read state and route the intent; follow the steps below.

## Open mode — route the intent

### 1. Find or seed `nextup.md`

Look for `nextup.md` at the repo root. If it's missing it never blocks — seed it (copy `nextup.example.md` if that tracked template exists, otherwise write the skeleton above) and carry on. With nothing else to go on, this run funnels into spec-driven development via `/starwave:creating-spec`. (`nextup.md` is gitignored; `nextup.example.md` is the tracked structure it's seeded from.)

An empty user zone is not a dead end — fall through to feature detection (step 2). Stop and ask, in plain English, *"What's the first version (your MVP) you'd like to build?"* only when there is genuinely nothing to go on: no user text, no spec folder matching the branch, and no **in-flight** spec. A spec folder is in-flight only if it holds at least one spec document with real content (`requirements.md`, `design.md`, `tasks.md`, `smolspec.md`, or a non-empty `userinput.md`); a folder of empty/stub files gives you the feature *name*, not intent — so an empty user zone plus a stub-only spec counts as "nothing to go on".

### 2. Identify the feature

In priority order:

1. **Explicit reference in the user zone wins.** If the user names a spec folder (`specs/foo/...`, `specs/bugfixes/baz/...`), that is the feature — read every file in it before deciding.
2. **Branch.** Run `git rev-parse --abbrev-ref HEAD`; if the name maps to an existing `specs/<name>` folder (stripping any `specs/` or `T-<n>/` prefix), that is the feature.
3. **Machine zone.** Otherwise, if the machine zone records a feature that still has a `specs/<name>` folder, use it.
4. **Fresh idea.** If nothing matches, treat the user-zone text as a fresh idea — step 6 picks the lane. The first spec of a project is conventionally the **MVP** (`specs/mvp/`), the smallest first version, with later refinements and features each becoming their own spec. A scaffolded but stub-only `specs/mvp/` gives you the name but no intent: if the user zone describes the MVP, dispatch `/starwave:creating-spec` and pass it through; if the user zone is also empty, ask for the MVP first.

### 3. Read the true state

The files in `specs/{feature}/` are the source of truth for how far the work has got — not the machine zone. Read what is present. If `decision_log.md` exists, read it and mention you did.

### 4. Honour explicit skill directives

If the user zone names a skill ("run `/starwave:smolspec`", "continue with `/starwave:design`", "`/fix-bug` this"), dispatch to it — this overrides the lane inference in step 6. But if it contradicts the files (asks for `/starwave:design` with no `requirements.md`), stop and surface the conflict instead of guessing.

### 5. Update the machine zone

Rewrite everything below the marker to reflect what you just learned: feature, branch, a plain-English stage line, the progress checkboxes, the next action. Prepend a one-line dated note (`date +%Y-%m-%d`). Leave the user zone untouched. Do this **before** you hand off, because the dispatched skill ends the turn.

### 6. Route to the one right next step

Pick a **lane** by the weight of the intent, then route within it. Prefer the lightest lane that genuinely fits — don't push a one-line fix through a full spec, and don't smuggle a real feature past requirements.

**Light lane — bounded intent goes straight to a focused skill.** No requirements/design ceremony:

| Intent | Route to |
|---|---|
| A specific bug to fix | `/fix-bug` |
| "Fix all the bugs" / a batch of open bugs | `/bug-blitz` (or `/blitz-merge` to fix and merge) |
| A minor change, or an iterative improvement to an existing file | `/starwave:smolspec` |

Iterative, in-place improvements to something that already exists (a skill, a doc, a config) stay in the light lane — they don't need a spec folder. If you're unsure whether a change is "minor", start it at `/starwave:smolspec`; that skill escalates to a full spec when the work turns out bigger than it looked, which keeps the funnel biased toward the lighter path without losing safety.

**Spec lane — substantial features go through the starwave chain.** Route by the earliest unmet need:

| State of `specs/{feature}/` | Route to |
|---|---|
| No folder, or only a stub / fresh idea | `/starwave:creating-spec` |
| `requirements.md` only | `/starwave:design` |
| `requirements.md` + `design.md`, no `tasks.md` | `/starwave:tasks` |
| `smolspec.md`, no `tasks.md` | `/starwave:tasks` |
| spec complete (`requirements.md` + `design.md` + `tasks.md`, or `smolspec.md` + `tasks.md`) | **Recommend implementation** (below) |

**When the spec is complete**, the workflow is done — tell the user in plain English that it's ready and recommend `/make-it-so` to build all tasks, or `/next-task` to do them one at a time. Recommend; do not invoke — execution is the user's call.

If the user zone carries a `T-<number>` ticket, pass it through to the dispatched skill so its Transit integration can move the ticket. Do not call `mcp__transit__*` yourself.

### 7. Hand off in plain English

Before invoking the chosen skill, tell the user in one or two plain sentences: what you read, which feature or job you're on, where things stand, and what happens next. Quote the deciding signal (a path from the user zone, the branch name, an explicit `/...` directive, or the lane you chose and why).

Then invoke the skill and **pass the user-zone text to it as the input**, so the user never retypes their idea — that is how the chain reads `nextup.md` into the work without each skill opening the file itself.

You MUST NOT continue past the handoff. The dispatched skill owns the rest; the user returns to `/nextup` next session to pick up again.

## Close-out mode

The mirror of opening: instead of routing forward, capture what just happened so the next `/nextup` (or the next person) picks up cleanly. It stays local — the lightweight counterpart to `/sendit`, which ships spec documents to Prism; close-out only writes the machine zone.

1. **Re-read the ground truth** — the spec files in `specs/{feature}/` and the git state (`git rev-parse --abbrev-ref HEAD`, recent commits, `git status`) — so the handoff reflects reality, not memory.
2. **Write the handoff into the machine zone.** Beyond feature / branch / stage / progress / next-up, capture what this session established — what changed, what was decided, what's blocked, the clear next step. The machine zone may grow into a real, skimmable handoff.
3. **Prepend a dated note** (`date +%Y-%m-%d`) summarising the session in one line.
4. **Stop.** Do not route, dispatch, or recommend a next skill — close-out ends the turn. Leave the user zone untouched.

## How the chain uses `nextup.md`

`nextup.md` is the shared handoff medium between the user and the work:

- **Intent persists** in the user zone. Because the tracked `nextup.example.md` ships the structure and travels with the repo, intent seeded there survives a fresh clone — the right home for it, not a hand-written file under `specs/`.
- **Into a spec:** when you dispatch a fresh idea, you pass the user-zone text to the target skill as input. That skill — never you — folds it into the right place (e.g. `specs/{feature}/userinput.md` and the requirements introduction).
- **Out to the user:** the machine zone you maintain is the at-a-glance status between sessions, and the handoff you write on close-out.

## Hard rules

- You maintain **only** the machine zone of `nextup.md` (below the marker). You never edit the user zone, and you write no other files. (`/sendit` also writes the machine zone when it ships a spec; you rebuild the block from the spec files each run, so the two never conflict.)
- You **never** create or write anything under `specs/` — those folders are owned by the starwave skills and writing into them from outside corrupts the spec. You read them; the chain writes them. This includes `requirements.md`, `design.md`, `tasks.md`, `smolspec.md`, and `userinput.md`.
- You are a **router, not an executor**: you do not implement code, run tests, or invoke execution skills (`/make-it-so`, `/next-task`), and you run no pipelines yourself — any fan-out to agents or sub-agents belongs to the skill you route to. When a spec is complete you **recommend** the right execution skill and stop.
- The user zone is authoritative. When it conflicts with the machine zone or the files, follow the user and surface the conflict.
- Raise blockers fast and in plain English — "I can't tell which feature you mean — is it X or Y?" is the right output when inputs are genuinely ambiguous.
- One run does one thing: open (read, update the quick reference, route, hand off) or close out (capture the handoff and stop). Never proceed past the handoff.
