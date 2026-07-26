# Spec Conventions Reference

Normative conventions for `specs/` directories, enforced by the spec-janitor
toolchain. Every janitor finding cites exactly one rule ID from this document;
rule IDs are stable and never reused. Each rule carries an audit class:

- **mechanical** — detected by `spec_lint.py` (the stdlib auditor distributed
  with this reference)
- **judgment** — detected by the `/spec-janitor` skill, which reads and reasons
  over spec content

and a repair disposition — one of exactly three values: `auto-fix`, `gated`, or
`detect-only`. Auto-fix eligibility requires a single transformation that is
deterministic or purely additive and rewrites no identifier referenced from
elsewhere; when an auto-fix's preconditions do not hold for a specific finding,
that finding is demoted to the gated batch instead of guessed at.

## Spec modes (SJ-MODE)

A spec folder's mode is recognized from its primary documents alone; task files
are checked only after recognition succeeds:

| Mode | Primary documents | Task file expected |
|---|---|---|
| full | `requirements.md` + `design.md` | `tasks.md` (or `tasks-<context>.md`) |
| smol | `smolspec.md` | `tasks.md` (or `tasks-<context>.md`) |
| PRD lane | `prd.md` | `tasks.md` or one or more `tasks-<context>.md` |
| bugfix | `report.md` (optional `solution-comparison.md`) | none required |

Recognized extra files that never affect mode recognition: `decision_log.md`,
`implementation.md`, `review-*.md`, `prerequisites.md`, and verification
reports.

Discovery: a directory under `specs/` IS a spec when it directly contains any
recognized primary document (`requirements.md`, `smolspec.md`, `prd.md`,
`design.md`, `report.md`, or a task file `tasks*.md`); its subdirectories are
assets of that spec and are never audited as separate specs. A directory with
no recognized document is a domain container — discovery descends into it; a
terminal directory with no recognized document anywhere is itself a finding
(SJ-MODE-001) — discovery never skips a folder for being unrecognizable.
Dotfolders and the janitor's own bookkeeping file `specs/.janitor.json` are
exempt. `specs/bugfixes/` itself is never a regular spec: each of its child
directories is a bugfix entry checked against the report shape (SJ-MODE-003),
and a loose file directly under `specs/bugfixes/` also violates SJ-MODE-003.

### SJ-MODE-001 — folder matches no recognized spec mode

**Audit**: mechanical — disposition: detect-only

Every spec directory under `specs/` MUST contain the primary documents of
exactly one recognized mode (full: `requirements.md` and `design.md`; smol:
`smolspec.md`; PRD lane: `prd.md`; bugfix: `report.md`). A terminal folder
holding only scratch notes, fragments, or unrecognized files violates this
rule; a spec's asset subdirectories do not (they are part of their spec, not
folders of their own). The repair requires authored content or a gated move,
so the finding is report-only; the finding's subject is the folder's
repo-relative path under `specs/`.

### SJ-MODE-002 — recognized mode missing its task file

**Audit**: mechanical — disposition: detect-only

A folder recognized as a full, smol, or PRD-lane spec MUST contain its mode's
task file: `tasks.md`, or one or more `tasks-<context>.md` files for
multi-context specs. Bugfix entries need no task file. Task authoring belongs
to the tasks/engage workflows, so the janitor reports the gap and proposes a
follow-up rather than generating tasks.

### SJ-MODE-003 — bugfix entry does not match the report shape

**Audit**: mechanical — disposition: detect-only

Every entry under `specs/bugfixes/` MUST contain a `report.md` whose H2
sections include: `Description of the Issue`, `Investigation Summary`,
`Discovered Root Cause`, `Resolution for the Issue`, and `Regression Test`
(additional sections such as `Affected Files`, `Verification`, `Prevention`,
and `Related` are conventional; an optional `solution-comparison.md` may sit
alongside). A bugfixes entry with no `report.md`, or a `report.md` missing
required sections, violates this rule. A loose file directly under
`specs/bugfixes/` (outside any entry folder) also violates this rule — bug
work lives in a per-bug entry folder.

## Cross-reference integrity (SJ-REF)

Task-file requirement references use markdown anchor links of the form
`[N.M](<file>.md#<fragment>)`. A link target resolves relative to the task
file's folder (falling back to the repo root); a fragment resolves via an
explicit `<a name="..."></a>` anchor or via the GitHub heading slug of a
heading in the target file. `references:` front-matter entries are
repo-root-relative paths.

### SJ-REF-001 — dangling task requirement anchor

**Audit**: mechanical — disposition: gated

Every markdown link in a task file that targets `<file>.md#<fragment>` MUST
resolve: the target file must exist and the fragment must match an `<a name>`
anchor or a heading slug in it. A link to a file the spec folder never
contained (e.g. `requirements.md` in a PRD-lane spec) or to an anchor that was
removed is a dangling reference. Retargeting requires deciding what the
reference was meant to point at, so the repair is gated. The finding's subject
is the broken reference text verbatim (`<file>.md#<fragment>`).

### SJ-REF-002 — references front-matter entry points at a missing file

**Audit**: mechanical — disposition: auto-fix

Every `references:` front-matter entry in a task file MUST resolve from the
repo root. Auto-fix preconditions: the entry has no path separator beyond the
spec folder (single-segment, folder-relative) AND exactly one existing file in
the same spec folder has that basename — the entry is then rewritten to the
unique candidate's repo-relative path. A cross-folder path, or zero or two
candidates, demotes the finding to the gated batch with `demoted: true` and no
write.

## Task-file structure (SJ-TASK)

The task-file grammar (rune's exhibited format, normative here):

- Optional YAML front matter delimited by `---` lines, holding `references:`
  entries.
- Optional phase headings as H2 (`## Phase Name`).
- Tasks as top-level checkbox list items: `- [ ] N. Title <!-- id:xxxxxxx -->`
  (`[x]` when complete), where `N.` is the task number and the trailing comment
  carries the stable task ID.
- Stable task IDs are 7-character lowercase alphanumeric (`[a-z0-9]{7}`) —
  rune's exhibited scheme, verified by a `rune list` round-trip when rune is
  present.
- Metadata as indented detail lines: `- Blocked-by: <id> (<title>)`,
  `- Stream: <n>`, and `- Requirements: [N.M](file.md#N.M), ...` — requirement
  references MUST be markdown anchor links, not plain text.
- Task numbering is sequential (1..N) across the whole file, continuing through
  phase boundaries.
- Uniform schema per file: every task in a file carries the same metadata shape
  as its siblings.

### SJ-TASK-001 — task file violates the structure rules

**Audit**: mechanical — disposition: detect-only

Every task file MUST parse under the grammar above: checkbox lines well-formed
(`- [ ] N. Title`), ID markers (when present) matching `<!-- id:[a-z0-9]{7} -->`,
and requirement references written as markdown anchor links rather than plain
text (`Requirements: 1.1` without a link is a structure violation, not a
reference violation). When the `rune` CLI is available, `rune list` failures on
a task file are also reported under this rule with rune's stderr as evidence.
Reconstruction of a malformed file is never deterministic, so the rule is
report-only. The finding's subject is the task-file name.

### SJ-TASK-002 — mixed stable-ID presence

**Audit**: mechanical — disposition: auto-fix

Within one task file, either every task carries a stable-ID marker or none
does; a file where some tasks carry `<!-- id:... -->` markers while sibling
tasks do not violates this rule. The repair mints unique 7-character lowercase
alphanumeric IDs for the unmarked tasks only — purely additive, rewriting
nothing — and the fixed file must round-trip `rune list` when rune is present.
A file with no IDs at all is not a violation of this rule (see SJ-DRIFT-001).
The finding's subject is the task-file name.

### SJ-TASK-003 — out-of-sequence task numbering

**Audit**: mechanical — disposition: detect-only

Top-level task numbers MUST run sequentially from 1 across the file. A task
whose number breaks the sequence violates this rule. Renumbering rewrites
identifiers that commits, logs, and reviews reference, so the rule is
report-only. The finding's subject is the kebab-slug of the out-of-order
task's title (not its number — insertions renumber siblings).

## Supersession (SJ-SUP)

Supersession is annotated, never deleted: decision-log entries use status
markers (`superseded by Decision X`), documents mark discarded sections
superseded in place, and superseding and superseded specs reference each other
in both directions.

### SJ-SUP-001 — duplicate or silently superseding specs

**Audit**: judgment — disposition: gated

Two specs addressing the same problem or surface MUST reference each other's
resolution: the superseded spec names its successor and the superseding spec
names what it replaces. Silent duplication or replacement violates this rule.
The finding is emitted once per pair, under the lexicographically first spec
path; its subject is the other spec's path.

### SJ-SUP-002 — internal contradiction after a direction change

**Audit**: judgment — disposition: gated

When a later section of a document changes direction from an earlier section,
the earlier section MUST be marked superseded in the same document. Two
mutually exclusive designs coexisting without annotation violate this rule.
The repair marks the discarded sections superseded — content is never deleted.
The finding's subject is the kebab-slug of the contradicted section heading.

## Scope alignment (SJ-SCOPE)

### SJ-SCOPE-001 — task-file scope does not match the spec document

**Audit**: judgment — disposition: gated

A task file's scope MUST match its source document's scope: tasks spanning
phases or work the spec document does not cover (or a spec document covering
work the task file ignores) violate this rule. Repair options are gated:
extend the spec document, or split/annotate the task file. The finding's
subject is the task-file name.

## Ghost changes (SJ-GHOST)

### SJ-GHOST-001 — spec references work no spec folder covers

**Audit**: judgment — disposition: detect-only

A spec document referencing changes, migrations, or features that no spec
folder covers is a ghost reference. The finding claims only that the reference
is unspecced — it is never confirmed against code or git history — and the
report proposes a follow-up spec. The finding's subject is the kebab-slug of
the referenced unspecced work.

## Workflow state (SJ-FLOW)

### SJ-FLOW-001 — spec abandoned mid-workflow

**Audit**: judgment — disposition: gated

A spec that stalled between workflow stages (e.g. requirements approved but
design never authored, tasks authored but never started, implementation
half-complete with no activity) MUST either progress or be annotated as
abandoned/superseded. The gated repair offers both options. The finding's
subject is the literal `abandoned`.

## Filing (SJ-FILE)

Filing rules: one feature per kebab-case folder directly under `specs/` (or
under a domain folder for nested layouts); bug work lives under
`specs/bugfixes/` in the report shape; non-bug work never lives under
`specs/bugfixes/` — cleanups and enhancements get a regular spec folder;
scratch files inside spec folders are discouraged.

### SJ-FILE-001 — mis-filed item

**Audit**: judgment — disposition: gated

Every spec artifact MUST live where the filing rules place it: a bugfix-shaped
folder outside `specs/bugfixes/`, a non-bug cleanup filed under
`specs/bugfixes/`, or a feature folder violating the one-feature-per-folder
rule is mis-filed. The repair is a gated move that rewrites all inbound
references within `specs/` in the same batch and reports inbound references
outside `specs/` as follow-ups. The finding's subject is the mis-filed path.

## Benign drift (SJ-DRIFT)

### SJ-DRIFT-001 — benign drift in a completed spec

**Audit**: judgment — disposition: detect-only

Completed specs tolerate generational drift: older task-ID styles (e.g. bare
numeric IDs with no stable-ID markers), casing variance, and ad-hoc extra
files. Such drift is raised at most once per finding identity (tracked in the
`raised` list of `specs/.janitor.json`); normalization is decided contextually
at triage and never applied automatically. The finding's subject is the
kebab-slug of the drift kind (e.g. `bare-numeric-ids`).
