# Backlog Skill

Spec: `specs/backlog-skill/`. `/backlog` is the entry point for forward
intent: it captures loose text and note files, routes each item to where the
work belongs, and rebuilds a view of the work already outstanding under
`specs/`.

## Components

| Piece | Path |
|---|---|
| Skill (5-step workflow) | `claude/skills/backlog/SKILL.md` |
| Generated artifact | `specs/BACKLOG.md` (created on first capture, not seeded) |
| Schema check in process-status | `scripts/process_status.py` — `_backlog_status`, `BACKLOG_PHASES`, `BACKLOG` column |

## Two entry kinds, and why it matters

`specs/BACKLOG.md` mixes durable and derived content, and almost every rule
in the skill follows from the split:

- **Captured** (`## Idea`, `## Needs Spec`) — from outside `specs/`. The only
  record of intent whose source file the skill may delete, so these persist
  across runs and leave only via reconciliation.
- **Derived** (`## Outstanding`) — restates spec state. Torn down and rebuilt
  wholesale every run, never amended in place, so it cannot go stale.

Because half the file is derived, `specs/BACKLOG.md` is a working file, not a
record: uncommitted, regenerated, and entry numbers are meaningless outside
the run that printed them. `rune` is the only writer (it is also the parser
the grammar is defined against); `rune complete`/`progress` are never run
against it, since every entry stays unchecked.

## Deriving outstanding work

Three cheap conditions plus orbit. The non-obvious one is orbit: the trigger
is `specs/<spec>/.orbit/variants.json`, **not** the `.orbit/` directory — a
finalized run leaves transcripts behind (this repo's own `backlog-skill`
spec is one), so a directory check marks every past spec outstanding forever.

A variant is unadopted when `git rev-list --count <base_commit>..<branch>` is
non-zero; all-`failed`/`canceled` with nothing ahead is noise, not work.
`git worktree list` cross-checks for orphans — a variant branch with commits
ahead and no metadata entry.

Related trap: `.orbit/` holds untracked `*.md` transcripts sitting under a
spec folder. Source detection excludes spec-folder files *by ancestry, not
immediate parent* — get that wrong and run transcripts are captured as loose
notes and offered for deletion.

## BACKLOG.md schema check (process_status.py)

Hybrid check, each layer covers a hole in the other:

- `rune list` parse gate.
- Raw-text scan of H2 headings: set/order must equal `BACKLOG_PHASES` —
  needed because an empty-but-valid backlog (all phases present, zero
  entries) has no `PhaseMarkers` at all in rune's JSON.
- `rune list --format json` Stats: `Pending == Total` — catches a checked
  entry, including a nested checked subtask, which a naive top-level-only
  `^- \[` scan would miss.
- Raw H1-title presence scan.

All three phases are required even when empty. `Outstanding` is rebuilt every
run, so an *absent* phase means a stale file while a present-but-empty one
means an idle rebuild — the distinction is why absence is drift.

Absent `specs/BACKLOG.md` renders `-` and is never drift (it's created on
first capture, not seeded ahead of time). The `backlog-drift` flag joins
`drift_flags()`, reason in the repo's detail line. The file is uncommitted by
design, so this check runs against the working tree, not the index.

## decision_mode convention

Per-repo `.agentic.json` may set a top-level `decision_mode` key:

- `overwrite` — revise a decision-log entry in place: same ID, date bumped,
  no superseding entry appended.
- `supersede`, or the key absent — default behavior: mark the old entry
  `superseded by Decision X` and append a new one.

Read at the point of revision, not cached. Documented in
`shared/conventions.md` (Documentation Standards) and
`claude/rules/references/decision-log-format.md` ("Revising a decision").
Skills that mandate supersession unconditionally (spec-janitor's SJ-SUP-*
repair, make-it-so/next-task's mid-implementation spec-edit clauses) all defer
to this key now — grep for `decision_mode` if adding a new one.

## test_sunset_grep.py

Permanent regression gate over every git-tracked file (`git ls-files`-sourced,
so untracked/gitignored files and `.worktrees/` are out of scope by
construction), matching paths and contents against its `PATTERN`. Exempt:
`specs/` and `CHANGELOG.md` (historical), the test file itself, and
`tests/test_sync_compat.py` (its `RETIRED_SKILLS` list needs the literals to
assert those directories stay gone). Nothing else — a tracked file that needs
to match `PATTERN` is a finding, not a case for a new exemption.
