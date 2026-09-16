# Decision Log: ui-ux-corpus

> Revisions to these entries follow the **supersede** default: this repository's
> `.agentic.json` declares no `decision_mode` key.

## Decision 1: Keep the corpus in agentic-coding, beside arjen-style-guide.md

**Date**: 2026-09-16
**Status**: accepted

### Context

The feedback being captured is left inside spadre, on documents in spadre worktrees, about
spadre's own interface. The obvious home is therefore the spadre repository. But the seven
variant worktrees (`spadre-ui-a` … `spadre-ui-g`) exist to be thrown away — that is what a
variant is — and their `.spadre-data` directories are gitignored working state, deleted with
the worktree. Meanwhile the preferences being recorded ("a tap target must be reachable by a
thumb", "a caret handle sits centred on its line") are not facts about spadre. They are facts
about how Ronan wants interfaces to behave, and rtob and everything after inherits them.

`arjen-style-guide.md` already occupies exactly this shape in this repository: a personal,
cross-repository style authority for Swift, distilled from three projects, that no single
project owns.

### Decision

Add `ui-ux/` to `agentic-coding`, with `ui-ux/ui-ux-guide.md` as the UI/UX peer of
`arjen-style-guide.md`. The corpus and the library both live here. No part of it lives in
spadre, in a variant worktree, or in `.spadre-data`.

### Rationale

Durability is the requirement that decides it. A corpus whose lifetime is bounded by a
worktree's lifetime does not do the job it was asked to do — "so you don't lose work" was the
brief. This repository is the only one of the candidates that is neither disposable nor
product-specific.

The placement also gets the audience right. A preference stated in the spadre repository is
advice to spadre; the same preference in `agentic-coding` is advice to whatever is being
built, which is what it actually is.

`ui-ux-guide.md` sits in `ui-ux/` rather than at the repository root, where
`arjen-style-guide.md` sits. This is a deliberate deviation: the Swift guide is a single
self-contained file with no satellite data, whereas this guide is meaningless without the
observations it cites, and a root-level directory of machine-written Markdown alongside a
root-level guide would read as two unrelated things.

### Alternatives Considered

- **`spadre/docs/ui-ux/`**: Corpus in the product repository - Rejected: it survives the
  variant worktrees but not the generalisation. Every entry would read as a spadre bug
  report, and rtob would have no reason to read it.
- **A variant worktree, next to `.spadre-data`**: Closest to the source - Rejected outright:
  gitignored, and deleted whenever the variant is rebuilt. This is the failure mode the
  feature exists to prevent.
- **The openclaw workspace (`~/.openclaw/workspace/ui-corpus/`)**: Where the raw snapshot
  already sits - Rejected as the permanent home: the workspace is this agent's operating
  space, not a versioned cross-repository authority, and nothing else consuming the guide
  would think to look there. It remains the right place for the raw JSON insurance copy.
- **A new dedicated repository**: Clean boundary - Rejected: one guide and a few dozen
  Markdown files does not justify a repository, and splitting it from `arjen-style-guide.md`
  would put the two style authorities in different places for no gain.

### Consequences

**Positive:**
- The corpus outlives every variant, branch and rebuild.
- Sits next to the existing style authority, so there is one place to look for "how should
  this be built".
- Versioned, reviewable, and diffable — a principle changing is a visible commit.

**Negative:**
- Splits the feedback from the code it describes; reading an observation means resolving a
  variant letter to a worktree that may no longer exist. Mitigated by recording the variant,
  doc id, version and quoted anchor on every observation.
- Puts product content in a process repository. Accepted, on the precedent that
  `arjen-style-guide.md` already does this.

---

## Decision 2: Separate real review from seeded notes by an epoch, not by identity

**Date**: 2026-09-16
**Status**: accepted

### Context

The variant stores hold 14 threads. Thirteen are seeded demo notes written on 2026-09-12
while the variants were being stood up — content to make the comment UI look populated —
under the display names Mash, Spud, Tattie and Tuber. One is real review: Gratin, 2026-09-15,
on variant B.

Ingestion has to tell them apart, and the obvious rule — a list of reviewer names, or of
author ids — was ruled out as something that rots. It is worse than that: it is wrong on this
very dataset. `Gratin`, the reviewer's own account, also authored a seeded note on 2026-09-12
("Does the rail show this?"). An allowlist keyed on Gratin admits a seeded comment; a denylist
of the four persona names admits it too, because Gratin is not on it. Identity does not
separate these two populations at all.

### Decision

Separate on **time**. `ui-ux/ingest.json` carries an `epoch` of `2026-09-13`; a comment
created before the epoch is pre-corpus and is declined, a comment created on or after it is
review and is ingested. Two lists of comment ids, `force_include` and `force_exclude`,
override the rule in either direction.

### Rationale

What actually separates the two populations is when they were written, not who wrote them.
The seeding was a bounded event during setup; review began afterwards. That is a fact about
project history, so an epoch never needs maintaining and cannot go stale the way a roster of
names does — and unlike a name list, it keeps working when a new reviewer is added, which is
the case the corpus most needs to survive.

It also makes the corpus and the reader agree by construction rather than by coincidence:
`spadre-variant-comments.sh` already defaults to `--since 2026-09-13` for the same reason, so
the number now has one definition instead of two.

The override lists exist because the rule will eventually be wrong about something, and
comment ids are stable, so an override is a permanent correction rather than a patch that
drifts.

### Alternatives Considered

- **Author allowlist / denylist by display name**: Ingest only Gratin, or ingest everyone
  except the four personas - Rejected on two counts: it rots as reviewers change, and it
  returns the wrong answer on the current data, where Gratin appears on both sides of the
  line.
- **Author id allowlist**: The same rule on stable ids rather than names - Rejected for the
  same correctness reason, plus it needs editing every time an account is created and is
  unreadable to a human scanning the config.
- **Hard-coded list of the 13 known seeded comment ids**: Exact, and ids never rot - Rejected
  as the primary rule: it is a snapshot of one moment that says nothing about any comment
  created later, so a second rule would be needed anyway. The capability survives as
  `force_exclude`, which is the same mechanism scoped to exceptions.
- **A marker written into the seed data itself**: Cleanest in principle - Rejected because
  the seed data already exists and is not being regenerated; a rule that requires rewriting
  history is not available.

### Consequences

**Positive:**
- Correct on the current dataset, where every identity-based rule is not.
- Zero maintenance: the epoch is a historical fact.
- One definition of the cutover, shared with the existing reader.
- Corrections are permanent, because they key on stable comment ids.

**Negative:**
- A future seeding run would land after the epoch and be ingested as review. Mitigated by
  `force_exclude` and by the ledger (Decision 4's `excluded.md`), which makes such a run
  visible on the next ingest rather than silent.
- The epoch is a magic date. Mitigated by `epoch_reason` sitting beside it in the config,
  so the number is never encountered without its justification.

---

## Decision 3: Index by UI concern; keep the document anchor as provenance only

**Date**: 2026-09-16
**Status**: accepted

### Context

Comments are left on a line of a document because spadre requires a place to attach them,
not because the document is the subject. Ronan's own framing: "I will review available docs,
and add comments about the entire ui — so the explicit doc they link to won't be completely
relevant." The single real comment proves it — it sits on line 18 of
`mobile-ui/mobile-ui-review.md`, a heading that reads "## 1. Landing screen — the entry
page", and it is about the caret handle's tap target and vertical alignment. The heading
contributes nothing.

A corpus keyed by document would therefore file every entry under the document someone
happened to be scrolled to, and a later session looking for "what do we know about tap
targets" would have to read all of it.

### Decision

Index the corpus by UI concern, from a closed vocabulary in `ui-ux/concerns.md`. Record the
document id, version id, line range and quoted anchor text on every observation as
provenance, and never use any of them as an index.

### Rationale

The index should match the question people ask of the corpus. Nobody asks "what was said
about `mobile-ui-review.md`"; they ask "what do we already know about scrolling" before
changing the scroll. Concern is the axis that answers that, and it is stable — the concern a
comment is about does not change when the document is edited, but the line number does.

Keeping the anchor is not a concession, it is what makes a thin comment recoverable. "i like
the scroll" is unreadable on its own; "i like the scroll, left on variant E, anchored at
`## 9. Version bar`" gives a later session somewhere to stand.

The vocabulary is closed and flat rather than free-text and hierarchical because the corpus
is tens of entries. Free tags at that size produce synonyms nobody reconciles; a tree
produces branches with one leaf.

### Alternatives Considered

- **Index by document, concern as a tag**: The structure the source data hands you -
  Rejected: it is the wrong axis for every question the corpus is asked, and it degrades as
  documents are edited and line numbers move.
- **Index by variant**: One folder per UI variant - Rejected: the variants are disposable, so
  the index would be too. Variant is recorded per observation because it is real evidence
  (Decision 5 in the guide's terms — a preference generalises, its evidence does not), but it
  cannot be the spine.
- **Free-text tags instead of a closed vocabulary**: No maintenance, no vocabulary drift -
  Rejected: at this size it produces `tap-target`, `tap targets` and `touch-target` as three
  tags, which is exactly the failure the index exists to avoid.
- **No index at all, just grep**: Honest and zero-cost - Rejected: it works for the verbatim
  layer and would be fine today at 1 entry, but there is no way to grep for "the principle we
  already agreed on", which is the layer that has to be read before building.

### Consequences

**Positive:**
- Reading the corpus by what you are about to build is a directory listing, not a search.
- Survives document edits, renames and deletions, because the index does not depend on them.
- Makes the low-information comments usable, since concern is the one thing "i like the
  scroll" does tell you.

**Negative:**
- A comment can belong to several concerns, so `concerns` is a list and an entry can be
  reached from more than one place. Accepted: multi-membership is true of the data, and
  forcing a single concern would be a lie.
- The vocabulary needs a human to extend it. Accepted; it is a documented edit to one file.

---

## Decision 4: Ingestion records; it never classifies, derives, or discards

**Date**: 2026-09-16
**Status**: accepted

### Context

Input is low-information and sometimes obscure: "i like the scroll" is a realistic entry. An
ingest that tried to be helpful would tag that as `scrolling`, guess a sentiment of
"positive", and write a paragraph of rationale about scroll physics that Ronan never said.
Every part of that guess is plausible and the rationale is fabricated. Worse, a wrong
classification is invisible once written — it looks exactly like a right one.

There is a second, related trap: a comment that the ingest rule declines is a comment nobody
will ever look at again, so a decline has to leave a trace.

### Decision

Split the corpus into two layers with different authorship. The **observation** layer is
machine-written, carries the comment verbatim in a round-tripping fenced block, and lands
with `concerns: []`, `sentiment: unclear`, `status: untriaged`. The **library** layer
(`ui-ux-guide.md`) is human-written, and every principle in it cites the observation ids it
rests on. Ingestion writes provenance and never touches the human-owned fields
(`concerns`, `sentiment`, `status`, `principles`, and everything under the `<!-- triage -->`
marker). Declined comments are written to `ui-ux/excluded.md` with the reason.

### Rationale

The verbatim comment is the only part that cannot be wrong, so it is the part the machine is
allowed to write. Interpretation can be wrong, so it is the part that carries a citation back
to its evidence and a human's name on the commit. Anyone reading a principle can check it
against what was actually said in one click.

Making `unclear` and `untriaged` the defaults means a thin entry stays thin, and the honest
statement "unclear which scroll — flagged" is the cheapest thing for the system to produce
rather than the most expensive. That is the right way round.

The two-layer split is also what makes re-ingestion safe: because the machine owns a known
set of fields, a merge is well defined, and an edit made by a human three weeks ago survives
a re-run today.

### Alternatives Considered

- **Classify on ingest with a keyword map** (`scroll` → `scrolling`): Cheap, catches the easy
  cases - Rejected: the easy cases are the ones a human triages in seconds anyway, and the
  hard cases are where a keyword map is confidently wrong. "The comment button is too big"
  contains "comment" and is about sizing, not the commenting flow.
- **Classify on ingest with a model call**: Better accuracy than keywords - Rejected: it makes
  ingestion non-deterministic, so a re-run produces a diff for no upstream change, which
  breaks the idempotency requirement outright. Triage by a model is fine; it just has to be an
  explicit, reviewable step rather than part of the pipe.
- **One layer, edited in place**: Fewer files, less indirection - Rejected: there is then no
  way to tell what Ronan said from what someone concluded he meant, which is the distinction
  the corpus exists to preserve.
- **Drop declined comments silently**: Simplest - Rejected: a declined comment is a decision
  the system made on its own, and an unreviewable decision about what counts as feedback is
  exactly the wrong thing to automate.

### Consequences

**Positive:**
- Nothing in the corpus is fabricated; the verbatim layer is checkable against the source.
- Re-ingestion is safe by construction, because ownership of every field is explicit.
- A wrong interpretation is a visible, revertable commit against a stable piece of evidence.
- The ingest is deterministic, so a no-change run produces a clean tree.

**Negative:**
- Triage is manual, so the corpus can accumulate untriaged entries. Mitigated by printing the
  untriaged count on every run, not by automating the guess.
- Two files to read to get the full picture of one preference. Accepted; the guide is the
  entry point and the observation is the footnote.

---

## Decision 5: Extend the existing reader with `--json` rather than parse threads twice

**Date**: 2026-09-16
**Status**: accepted

### Context

`~/.openclaw/workspace/bin/spadre-variant-comments.sh` already knows spadre's thread schema:
where the stores live, the variant-to-port map, tombstones, the `resolved` state, and how to
render an anchor usefully. It emits Markdown for a human.

Ingestion needs the same data plus the two fields the Markdown drops — the thread id and the
comment id — because those ids are what makes re-ingestion idempotent. So the Markdown output
cannot be the ingest feed, and the naive fix is a second parser in Python that reads the same
files. That is two definitions of the same schema, drifting from the day they are written.

### Decision

Lift the reader's per-file Python heredoc into a single heredoc that parses once and renders
in either Markdown or JSON, and add `--json`, `--root` and `--archive` flags. The ingest
script consumes that JSON on stdin and contains no knowledge of spadre's thread schema at all.

### Rationale

One parser, two renderings, is the only arrangement where the two consumers cannot disagree.
The alternative arrangements all end with the ingest and the reader holding different opinions
about, say, whether a tombstoned comment counts.

The pipe boundary also keeps this repository clean. `agentic-coding` is shared and
machine-agnostic; hard-coding `/Users/m/repos/spadre-ui-b/.spadre-data` into
`scripts/ui_corpus_ingest.py` would put one machine's layout into a cross-repository toolchain.
Consuming a JSON stream means the ingest works against the live stores, the archived snapshot,
or a future source, without knowing which.

`--archive` exists so the snapshot at `~/.openclaw/workspace/ui-corpus/raw/variant-*.json` is
a first-class input and the whole path can be tested without the variants running.

### Alternatives Considered

- **A second parser inside `ui_corpus_ingest.py`**: No changes to a working tool - Rejected:
  two definitions of one schema, and the brief explicitly ruled it out. The reader's own
  handling of tombstones and anchors would have to be reimplemented and kept in step forever.
- **Parse the reader's Markdown output**: Zero changes to the reader - Rejected: the Markdown
  does not contain the comment id, so idempotency is impossible, and screen-scraping a format
  designed for humans is a second parser with worse odds.
- **Move the reader into `agentic-coding/scripts/` and call it directly**: One repository,
  one tool - Rejected: the reader is machine-specific plumbing for one developer's local
  variant worktrees, and putting the Tailscale address and the port map into the shared
  toolchain repository is the wrong trade.
- **Add a JSON export endpoint to spadre**: The proper long-term seam - Rejected for now:
  it is a change to the product to serve a tooling need, and the FileStore on disk is already
  a stable, zero-cost seam. Worth revisiting if a variant ever runs against Cosmos.

### Consequences

**Positive:**
- Exactly one place knows spadre's thread schema.
- `agentic-coding` stays free of machine-specific paths.
- The archived snapshot becomes a testable input, so the ingest path is covered without
  running seven dev servers.

**Negative:**
- The reader was working and is now rewritten internally, which is a regression risk.
  Mitigated by diffing its Markdown output before and after the change, as an explicit task.
- The two halves live in different repositories, so a schema change means two commits in two
  places. Accepted: the alternative is one commit and two parsers.

### Impact

Touches `~/.openclaw/workspace/bin/spadre-variant-comments.sh`, which is outside this
repository and outside `make lint`'s `scripts/*.sh` glob. It is shellcheck-clean, verified by
hand rather than by CI.
