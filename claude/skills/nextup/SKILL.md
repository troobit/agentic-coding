---
name: nextup
description: The universal entry point for the starwave spec workflow. Reads nextup.md, works out where you are in a feature's spec, keeps a plain-English progress record, and routes you to the right next step — resume a spec phase, start a fresh spec, or recommend implementation. Use when the user says "/nextup", "run nextup", "what's next", "pick up where we left off", or starts a session without saying which command to run.
---

# Nextup — the universal entry point for starwave

`/nextup` is the one command a user runs at the **start of any session** so they never have to remember which skill to run or repeat context they already gave. It is a **reference point, not a driver.** It does not write specs and it does not loop through phases. It does exactly three things:

1. Reads `nextup.md` to learn what the user wants and where work stands.
2. Keeps the **machine zone** of `nextup.md` up to date as a plain-English quick reference.
3. Routes the user to the single right next step and hands off.

The audience is often **non-technical**. Every message you show the user must be plain English — say where they are and what happens next, with no jargon. The spec files themselves stay technical; your spoken status does not.

## How `nextup.md` is structured

`nextup.md` lives at the **repo root** and has a clean divide between user input and machine state. A marker line separates them:

```markdown
# What I want

<!-- This is YOUR space. Write what you want to build or do next, in your own
     words. You never need to touch anything below the line. -->

<your words here>

<!-- nextup:machine — everything below is kept up to date by /nextup. Read it for
     a quick sense of where things stand; you don't need to edit it. -->

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

**Two rules govern the divide:**

- **The user zone wins.** Anything above the `<!-- nextup:machine -->` marker is the user's intent and is authoritative. If it contradicts the machine zone (e.g. the machine says "Design" but the user wrote "let's redo the requirements"), follow the user and surface the conflict in plain English.
- **The machine zone is disposable.** You rebuild it every run from the real source of truth — the files in `specs/{feature}/`. It can never be the reason something goes wrong; if it's stale, the next `/nextup` fixes it. Only ever rewrite the block below the marker; never touch the user zone.

## What `/nextup` does each run

### 1. Find or seed `nextup.md`

- Look for `nextup.md` at the root of the current working directory.
- **If it is missing**, create it so the user always has a working file: copy `nextup.example.md` if that tracked template exists at the root, otherwise write the skeleton above (empty user zone, a fresh machine zone). `nextup.md` is gitignored; `nextup.example.md` is the tracked structure it is seeded from.
- An **empty user zone is not a dead end.** Unlike a plain intake file, `/nextup` is an entry point — fall through to branch/spec detection (step 2). Stop and ask the user, in plain English, *"What's the first version (your MVP) you'd like to build?"* only when there is genuinely nothing to go on: no user text, no spec folder matching the branch, and no **in-flight** spec.
- **A stub-only spec folder is not in-flight.** A folder is in-flight only if it holds at least one spec document with real content (`requirements.md`, `design.md`, `tasks.md`, `smolspec.md`, or a non-empty `userinput.md`). A folder containing only empty/zero-byte files (e.g. a placeholder `userinput.md` that just shows the directory structure) carries no intent — it tells you the feature *name*, not what to build. So if the user zone is empty and the only spec is a stub, that counts as "nothing to go on": ask for the MVP rather than dispatching `creating-spec` with no idea to pass.

### 2. Identify the feature

In priority order:

1. **Explicit reference in the user zone wins.** If the user names a spec folder (`specs/foo/...`, `specs/bugfixes/baz/...`), that is the feature. Read every file in that folder before deciding.
2. **Branch fallback.** Run `git rev-parse --abbrev-ref HEAD`. If the branch name maps to an existing `specs/<name>` folder (stripping any `specs/` or `T-<n>/` prefix), that is the feature.
3. **Machine zone fallback.** If neither of the above resolves but the machine zone records a feature that still has a `specs/<name>` folder, use it.
4. **Fresh idea.** If nothing matches an existing spec, treat the user zone content as a fresh idea bound for `/starwave:creating-spec`. The first spec of a project is conventionally the **MVP** (`specs/mvp/`) — the smallest first version — with later refinements and features each becoming their own spec. A scaffolded but stub-only `specs/mvp/` (see "in-flight" above) gives you the feature *name* but no intent: if the user zone describes the MVP, dispatch `/starwave:creating-spec` and pass that description through to fill the folder; if the user zone is also empty, ask for the MVP first (do not dispatch with nothing to pass).

### 3. Read the true state from the spec files

The files in `specs/{feature}/` are the source of truth for how far the work has got — **not** the machine zone. Read what is present. If `decision_log.md` exists, read it and mention you did.

### 4. Honour explicit skill directives

If the user zone explicitly names a starwave skill ("run `/starwave:smolspec`", "continue with `/starwave:design`"), dispatch to that skill. An explicit user directive overrides the inference in step 6 — but if it contradicts the files (e.g. asks for `/starwave:design` with no `requirements.md`), stop and surface the conflict instead of guessing.

### 5. Update the machine zone

Rewrite everything below the `<!-- nextup:machine -->` marker to reflect what you just learned: feature name, branch, a plain-English stage line, the progress checkboxes, and the next action. Prepend a one-line dated note (use `date +%Y-%m-%d`) to the Notes list describing what this run is doing. Leave the user zone untouched. Do this **before** you hand off, because the dispatched skill ends the turn.

### 6. Route to the one right next step

Use the earliest unmet need. The spec files decide the route:

| State of `specs/{feature}/` | Route to |
|---|---|
| No folder, or only a stub / fresh idea | `/starwave:creating-spec` |
| `requirements.md` only | `/starwave:design` |
| `requirements.md` + `design.md`, no `tasks.md` | `/starwave:tasks` |
| `smolspec.md`, no `tasks.md` | `/starwave:tasks` |
| `requirements.md` + `design.md` + `tasks.md` | **Recommend implementation** (see below) |
| `smolspec.md` + `tasks.md` | **Recommend implementation** (see below) |

**When the spec is complete**, the workflow is done — so make the right implementation recommendation in plain English. Tell the user the spec is ready and recommend they run **`/make-it-so`** to build all the tasks, or **`/next-task`** to do them one at a time. Recommend; do not invoke — execution is the user's call.

If the user zone carries a `T-<number>` ticket reference, pass it through to the dispatched skill so its Transit integration can move the ticket. Do not call `mcp__transit__*` yourself.

### 7. Hand off in plain English

Before invoking the chosen skill, tell the user in one or two plain-English sentences: what you read, which feature you're on, where things stand, and what happens next. Quote the deciding signal (a path from the user zone, the branch name, or an explicit `/starwave:...` directive).

Then invoke the skill and **pass the user-zone text to it as the input**, so the user never retypes their idea — that is how the chain reads `nextup.md` into the spec without each chain skill having to open the file itself.

You MUST NOT continue past the handoff. The dispatched skill owns the rest. The user returns to `/nextup` next session to pick up again.

## How the chain uses `nextup.md`

`nextup.md` is the shared handoff medium between the user and the starwave chain:

- **Where intent persists:** the user zone is the home for the user's intent. Because the tracked `nextup.example.md` ships the structure and travels with the repo, intent seeded there survives a fresh clone — that is the right place for it, not a hand-written file under `specs/`.
- **Into a spec:** when you dispatch a fresh idea, you pass the user-zone text to the starwave skill as its input. **That starwave skill** — never you — folds those words into the right place in the spec (e.g. `specs/{feature}/userinput.md` and the requirements introduction) so the user never retypes them.
- **Out to the user:** the machine zone you maintain is the user's at-a-glance status between sessions.

You only ever maintain the machine zone of `nextup.md`. Everything under `specs/` is written by the chain.

## Hard rules

- You maintain **only** the machine zone of `nextup.md` (below the marker). You never edit the user zone, and you write no other files. (`/sendit` also writes the machine zone when it ships a spec for review; you rebuild the block from the spec files each run regardless, so the two never conflict.)
- **You never create or write anything under `specs/`.** Those folders are structured deliberately and are owned by the starwave skills; writing into them from outside that workflow is dangerous and corrupts the spec. You read them; the chain writes them. This includes `requirements.md`, `design.md`, `tasks.md`, `smolspec.md`, and `userinput.md`.
- You do not implement code or run tests.
- You do not invoke execution skills (`/make-it-so`, `/next-task`). When the spec is complete you **recommend** the right one in plain English and stop.
- The user zone is authoritative. When it conflicts with the machine zone or the files, follow the user and surface the conflict.
- Raise blockers fast and in plain English. "I can't tell which feature you mean — is it X or Y?" is the correct output when inputs are genuinely ambiguous.
- Never proceed past the handoff. One run = read, update the quick reference, route, hand off.
