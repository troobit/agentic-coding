# Smolspec: UI/UX Corpus

## Overview

Ronan reviews UI variants by commenting **inside spadre itself** — that is what spadre is
for. His comments are about the whole interface, not the document they happen to sit on:
"i like the scroll", "comment button too big". The document anchor is where the cursor was,
not what the note is about.

This feature makes those comments durable and re-usable. It adds `ui-ux/` to this
repository: a **corpus** of verbatim observations organised by UI concern, and a **library**
— `ui-ux-guide.md` — of derived principles that cite the corpus as evidence. `ui-ux-guide.md`
is the peer of `arjen-style-guide.md`: a cross-repository authority, here for UI/UX rather
than Swift, governing spadre, rtob and whatever comes after.

It also adds the path that keeps the corpus fed: a `--json` mode on the existing reader
`~/.openclaw/workspace/bin/spadre-variant-comments.sh`, and `scripts/ui_corpus_ingest.py`,
which turns that stream into observation files idempotently.

**Lane: smolspec.** This is one new documentation directory, one stdlib script and one flag
on an existing reader; the substance is two conventions, and `decision_log.md` carries them.

It does exceed the smolspec 80-LOC line — the ingest script is ~230 lines — and that is
stated here rather than hidden. The full lane is still wrong for it: no architectural
boundary moves, nothing existing depends on the new code, there is no API and no breaking
change, and a requirements/design/tasks chain would be three documents describing a
directory of Markdown files. The overrun is one leaf script with no callers.

## Non-Goals

- Automatic classification of a comment into a UI concern. Rejected in
  [Decision 3](decision_log.md): "i like the scroll" does not contain enough information to
  classify reliably, and a wrong tag in the index is worse than an untriaged one.
- Deriving principles automatically. Ingestion records; a human triages.
- Reading spadre's store over HTTP or through its API. The reader already reads the
  FileStore on disk and that is the seam being reused.
- Storing the corpus in spadre, rtob or any variant worktree. Argued in
  [Decision 1](decision_log.md) — `.spadre-data` is gitignored working state and the
  worktrees are disposable.
- Ingesting comments from anything other than the local spadre variant stores. The record
  schema carries a `source.product` field so a second source can be added later without a
  migration, but nothing else is wired today.

## Requirements

1. The corpus MUST be indexed by **UI concern**, never by document. The document id, version,
   line range and quoted anchor MUST still be recorded on every observation, as provenance.
2. Every observation MUST carry the comment body **verbatim**, byte-for-byte as spadre stored
   it, in a form that round-trips. Any derived reading MUST be a separate, clearly-labelled
   section of the same file, and MUST NOT replace the verbatim text.
3. Every principle in `ui-ux-guide.md` MUST cite at least one observation id as evidence. A
   principle with no evidence is not a principle.
4. Ingestion MUST be idempotent. Re-running it over the same threads MUST NOT create a second
   record for a comment already ingested, and MUST leave the working tree unchanged when
   nothing has changed upstream.
5. Ingestion MUST NOT overwrite human triage. `concerns`, `sentiment`, `status` and
   `principles` in an observation's frontmatter, and everything below the `<!-- triage -->`
   marker in its body, are human-owned and MUST survive re-ingestion.
6. Ingestion MUST separate real review from the seeded demo notes **without an author
   allowlist**. The rule MUST be recorded in configuration, not in code, and MUST be
   overridable per comment id.
7. Nothing MUST be silently discarded. Every comment the ingest declines MUST appear in a
   ledger with its id, author, date, variant and the reason it was declined.
8. An observation MUST record which variant the comment was left on. The preference
   generalises; the evidence does not.
9. Ingestion MUST NOT guess. A new observation MUST land with `sentiment: unclear`,
   `concerns: []` and `status: untriaged`, and MUST NOT invent rationale the comment does not
   contain.
10. Likes MUST be first-class. The sentiment vocabulary MUST include an affirming value, and
    `ui-ux-guide.md` MUST be able to state a principle whose content is "do not break this".
11. The existing reader's default human-readable output MUST be unchanged. Adding `--json`
    MUST NOT alter what `spadre-variant-comments.sh` prints today.
12. Thread parsing MUST exist in exactly one place. The ingest script MUST NOT re-implement
    spadre's thread schema.
13. `ui-ux/README.md` MUST be written for a session with no memory of this conversation: what
    the two layers are, how to read them, how to add a comment, how to triage one.
14. `CHANGELOG.md` MUST get one entry and `specs/OVERVIEW.md` one row and one section.

## Implementation Approach

- **`ui-ux/concerns.md`** — the controlled vocabulary. A flat list of ~12 concern slugs with
  a one-line scope for each, plus the rule for adding one. Flat, not hierarchical: the corpus
  is tens of entries, and a tree would be a taxonomy nobody maintains.

- **`ui-ux/observations/<YYYY-MM-DD>-<id8>.md`** — one file per source comment, the file name
  derived from the comment's own stable id so re-ingestion is a no-op. YAML frontmatter
  splits into an ingest-owned provenance block (`id`, `thread`, `author`, `created`,
  `source.*`, `classification`, `ingested`) and a human-owned triage block (`concerns`,
  `sentiment`, `status`, `principles`). The body is the verbatim comment in a fenced block,
  then a `<!-- triage -->` marker, then whatever a human wrote under it.

- **`ui-ux/ui-ux-guide.md`** — the library. H2 per concern, `UX-NNN` principles under it,
  each with a status, a one-line statement, and an `Evidence:` line linking observations by
  file and naming the variant. Ordered by concern, which is the whole point: you read it by
  what you are building, not by what document someone was looking at.

- **`ui-ux/excluded.md`** — the ledger for Req 7. One table row per declined comment.

- **`ui-ux/ingest.json`** — `epoch`, `epoch_reason`, `force_include`, `force_exclude`. JSON,
  not TOML: `/usr/bin/python3` on this machine is 3.9.6 and has no `tomllib`.

- **`~/.openclaw/workspace/bin/spadre-variant-comments.sh`** — gains `--json`, `--root` and
  `--archive`. Its per-file Python heredoc is lifted into a single heredoc that parses once
  and renders in either format, so Req 11 and Req 12 are satisfied by the same change rather
  than traded off. Verified by diffing the script's Markdown output before and after.

- **`scripts/ui_corpus_ingest.py`** — stdlib only, `from __future__ import annotations`, no
  PEP 604 unions at def time (this repo's Python rule; the interpreter is 3.9.6). Reads the
  reader's JSON on stdin or from `--from FILE`. Maps records to observation files, merges
  rather than clobbers, writes the ledger, prints a `new / updated / unchanged / excluded`
  summary, and supports `--dry-run`.

- **`tests/test_ui_corpus_ingest.py`** — unittest, discovered by `make test`. Covers the
  idempotency contract (Req 4), the triage-preservation merge (Req 5), the epoch split and
  its overrides (Req 6), and the verbatim round-trip (Req 2).

No generated file, skill, MCP config or `.agentic.json` key is touched, so `make generate`
and `make lint` are unaffected. The new script is Python, so `lint-shell` — which globs
`scripts/*.sh` — does not see it; the modified reader lives outside this repository and is
shellcheck-clean, checked by hand.

## Risks and Assumptions

- **Risk: the epoch rule mislabels a future seeding run.** Real, and accepted. A seed written
  after the epoch is ingested as review. The mitigation is `force_exclude` plus the ledger,
  which makes a wrong call cheap to see and one line to fix. The alternative — an author
  allowlist — gets *this* dataset wrong, because the reviewer's own account appears on both
  sides of the line ([Decision 2](decision_log.md)).
- **Risk: triage never happens and the corpus is a pile of untriaged files.** Untriaged
  observations are still the asset (Req 2); the guide is the part that needs a human. The
  ingest summary names the untriaged count on every run so the backlog is visible rather than
  silent.
- **Risk: the concern vocabulary rots into a tag soup.** Mitigated by keeping it closed and
  small, with adding a term a documented edit to `concerns.md` rather than a free-text tag.
  Not enforced by tooling — deliberately, since a validator on a twelve-item list is
  ceremony.
- **Risk: the reader rewrite regresses its Markdown output.** Mitigated by capturing the
  output before the change and diffing after. This is a task, not a hope.
- **Assumption: comment ids are stable across spadre restarts and rebuilds.** They are UUIDv7
  values minted at creation and stored in the thread file; nothing in spadre regenerates
  them. This is what makes Req 4 possible, and if it turns out to be false the idempotency
  contract fails loudly (duplicate files) rather than quietly.
- **Assumption: `.spadre-data` remains a FileStore on disk in local mode.** If a variant moves
  to Cosmos, the reader needs a second source; the ingest script does not, because it consumes
  the reader's JSON rather than the store.
- **Unverified: whether "vertically not in the middle" in the one real comment refers to the
  caret handle or to the selection toolbar.** Recorded as uncertain in the observation rather
  than resolved by guessing, which is the behaviour Req 9 exists to produce.
