# The UI/UX corpus

Ronan reviews UI work by commenting **inside spadre**, on whatever document he happens to
have open. The comments are about the interface, not the document — "i like the scroll",
"comment button too big". This directory is where those comments become durable, so the same
ground is not re-covered every time a variant is rebuilt.

If you are here to **build something**, read [`ui-ux-guide.md`](ui-ux-guide.md) and stop.
The rest of this file is how the guide gets fed.

## The two layers

| | What it is | Who writes it | Can it be wrong? |
|---|---|---|---|
| [`observations/`](observations/) | One file per source comment, carrying the comment **verbatim** plus where it came from | The ingest script | No. It is a copy of what was said. |
| [`ui-ux-guide.md`](ui-ux-guide.md) | Derived principles, indexed by UI concern, each citing the observations it rests on | A human | Yes. That is why it cites. |

They are separate so that "what Ronan said" and "what someone concluded he meant" never get
confused for each other. A principle that turns out to be a misreading is one revertable
commit; the evidence under it does not move.

Supporting files: [`concerns.md`](concerns.md) is the closed vocabulary the corpus is indexed
by, [`ingest.json`](ingest.json) configures ingestion, and [`excluded.md`](excluded.md) lists
every comment the ingest declined and why.

## Reading it

- **"I'm about to change the scroll behaviour, what do we know?"** — open `ui-ux-guide.md`
  and find the `scrolling` section. That is what the concern index is for.
- **"Where did that principle come from?"** — follow the `Evidence:` link to the
  observation, and read the `## Verbatim` block. That is the actual comment.
- **"What's still untriaged?"** — `grep -l 'status: "untriaged"' observations/*.md`, or just
  run the ingest; it prints the count.

An observation's `source_variant`, `source_doc_id` and `source_anchor_quote` are
**provenance, never an index**. The document a comment sits on is usually irrelevant to what
it says — that is the whole reason this is organised by concern. The anchor is there so a
thin comment stays recoverable, not so you can browse by file.

Variant worktrees get deleted. An observation whose `source_url` no longer resolves is still
valid; the corpus was built to outlive them.

## Adding new comments

One command, from the repository root:

```bash
~/.openclaw/workspace/bin/spadre-variant-comments.sh --json --all \
  | python3 scripts/ui_corpus_ingest.py
```

`--all` is right here: the ingest does its own filtering (see **The epoch** below) and
double-filtering would hide comments from the ledger. Add `--dry-run` to the ingest to see
what would happen without writing.

If the variant worktrees are gone, the archived threads still work:

```bash
~/.openclaw/workspace/bin/spadre-variant-comments.sh --json --all \
  --archive ~/.openclaw/workspace/ui-corpus/raw \
  | python3 scripts/ui_corpus_ingest.py
```

That reader is the **only** thing that knows spadre's thread format. Do not write a second
parser; if the format changes, change the reader and everything downstream follows.

Re-running is safe. Observation files are named from the comment's own stable id, so an
already-ingested comment produces no write at all and the working tree stays clean. The
summary line tells you what happened:

```
ui-corpus ingest — 14 records in
  new        1
  updated    0
  unchanged  0
  excluded  13
  untriaged  1 of 1 observations
```

## Triaging an observation

Ingestion deliberately records and nothing else. A new observation lands with
`concerns: []`, `sentiment: "unclear"` and `status: "untriaged"`, and no invented rationale.
Turning that into something useful is a human step:

1. Read the `## Verbatim` block.
2. Set `concerns` from [`concerns.md`](concerns.md) — a list; a comment often belongs to
   several. If genuinely nothing fits, add a term to `concerns.md` in the same commit.
3. Set `sentiment` to one of `affirm`, `defect`, `mixed`, `question`, `unclear`.
   **Likes matter as much as complaints** — an `affirm` tells you what the next iteration
   must not break, which a bug list never will.
4. Set `status: "triaged"`.
5. Replace the `## Reading` section below the `<!-- triage -->` marker with what the comment
   tells you. **Keep it proportionate.** "i like the scroll" is one line, not a paragraph of
   invented reasoning.
6. Put anything genuinely ambiguous under `## Uncertain` and leave it unresolved. "Unclear
   which scroll — flagged" is a correct entry. A confident wrong reading is not.
7. If it is worth generalising, add a principle to `ui-ux-guide.md` with the next free
   `UX-NNN` id, cite the observation, and list the id in the observation's `principles`.

### Who owns which field

Ingestion rebuilds the top half of the frontmatter from the source comment every run. It
never touches the bottom half, or anything below `<!-- triage -->`.

- **Machine-owned:** `id`, `thread`, `author`, `author_id`, `role`, `created`, `edited`,
  `classification`, `ingested`, everything prefixed `source_`.
- **Human-owned:** `concerns`, `sentiment`, `status`, `principles`, and the whole body below
  the `<!-- triage -->` marker.

So triage survives a re-ingest, including when the comment was edited in spadre — in that
case the verbatim block updates and your reading stays put, which is usually what you want
but is worth a second look.

## The epoch

The variant stores contain seeded demo notes from 2026-09-12, written to make the comment UI
look populated, alongside real review. `ingest.json` carries an `epoch` of `2026-09-13`:
comments created before it are declined as pre-corpus, comments on or after it are ingested.

The split is by **time, not by author**, and that is deliberate. The reviewer's own account
wrote both a seeded note on the 12th and real feedback on the 15th, so any allowlist or
denylist of names gets this data wrong — and a name list rots the moment someone new reviews.
A date is a fact about project history and needs no maintenance.
(`../specs/ui-ux-corpus/decision_log.md`, Decision 2.)

The rule will eventually be wrong about something. Two escape hatches in `ingest.json`, both
keyed on comment ids, which are stable:

- `force_include` — ingest this comment even though the epoch declines it.
- `force_exclude` — decline this comment even though the epoch admits it. This is what to
  reach for if the stores are ever seeded again.

Nothing is dropped silently. Every declined comment is a row in
[`excluded.md`](excluded.md) with its id, author, variant, date, reason and the first line of
its body, so a wrong call is visible rather than invisible. Overturn it by moving the id into
`force_include` and re-running.

## If something breaks

- **Duplicate observations for one comment** — comment ids are not stable after all, which is
  the assumption idempotency rests on. Stop and fix the naming rule; do not delete by hand.
- **A re-ingest wiped a triage** — a bug in the merge. `git diff` will show it; the tests in
  `../tests/test_ui_corpus_ingest.py` are meant to catch exactly this.
- **The reader finds no stores** — the variants are not checked out. Use `--archive` against
  `~/.openclaw/workspace/ui-corpus/raw`, which is the insurance copy of the raw threads.

## Related

- [`ui-ux-guide.md`](ui-ux-guide.md) — the derived principles. The thing you actually read.
- [`concerns.md`](concerns.md) — the concern vocabulary.
- [`../arjen-style-guide.md`](../arjen-style-guide.md) — the Swift peer of the guide.
- [`../specs/ui-ux-corpus/`](../specs/ui-ux-corpus/) — the smolspec and the decisions behind
  this structure.
- [`../scripts/ui_corpus_ingest.py`](../scripts/ui_corpus_ingest.py) — the ingest.
