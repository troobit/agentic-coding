---
references:
    - specs/ui-ux-corpus/smolspec.md
    - specs/ui-ux-corpus/decision_log.md
---
# UI/UX Corpus Implementation

## Corpus structure

- [x] 1. Define the concern vocabulary in `ui-ux/concerns.md` <!-- id:uxc001 -->
  - A flat, closed list of concern slugs, each with a one-line scope and a "not this" note where two concerns are easily confused
  - States the rule for adding a term: edit this file, in the same commit as the observation that needed it
  - Requirements: 1

- [x] 2. Define the observation record and write the ingest configuration <!-- id:uxc002 -->
  - Frontmatter split into an ingest-owned provenance block and a human-owned triage block, with the ownership boundary stated in the README
  - Body is the verbatim comment in a fenced block that round-trips, then the `<!-- triage -->` marker, then human text
  - `ui-ux/ingest.json` carries `epoch`, `epoch_reason`, `force_include`, `force_exclude`; JSON rather than TOML because `/usr/bin/python3` here is 3.9.6 with no `tomllib`
  - Requirements: 1, 2, 5, 6, 8, 9

- [x] 3. Create `ui-ux/ui-ux-guide.md` as the peer of `arjen-style-guide.md` <!-- id:uxc003 -->
  - H2 per concern, `UX-NNN` principles beneath, each with status, a one-line statement, and an `Evidence:` line citing observation files and naming the variant
  - Sentiment vocabulary includes an affirming value so a principle can be "do not break this"
  - Requirements: 3, 8, 10
  - Blocked-by: 1

## Ingestion

- [x] 4. Add `--json`, `--root` and `--archive` to `spadre-variant-comments.sh` <!-- id:uxc004 -->
  - Per-file Python heredoc lifted into one heredoc that parses once and renders Markdown or JSON, so there is a single definition of spadre's thread schema
  - JSON records carry thread id and comment id, which the Markdown drops and idempotency needs
  - `--archive DIR` reads the `variant-<letter>.json` snapshot files so the path is testable without the dev servers running
  - Requirements: 11, 12

- [x] 5. Verify the reader's Markdown output is byte-identical <!-- id:uxc005 -->
  - Capture `--all` and default output before the change, diff against after
  - Requirements: 11
  - Blocked-by: 4

- [x] 6. Write `scripts/ui_corpus_ingest.py` <!-- id:uxc006 -->
  - Stdlib only, `from __future__ import annotations`, no PEP 604 unions at def time (repo Python rule; interpreter is 3.9.6)
  - Reads the reader's JSON on stdin or `--from FILE`; contains no knowledge of spadre's thread schema
  - Idempotent by comment id: unchanged input writes nothing, so a no-change run leaves a clean tree
  - Merges rather than clobbers — human-owned frontmatter keys and everything under `<!-- triage -->` survive re-ingestion
  - Epoch split with `force_include`/`force_exclude` overrides; declined comments written to `ui-ux/excluded.md` with a reason
  - New observations land `concerns: []`, `sentiment: unclear`, `status: untriaged`; no rationale is invented
  - `--dry-run` and a `new / updated / unchanged / excluded / untriaged` summary
  - Requirements: 2, 4, 5, 6, 7, 9, 12
  - Blocked-by: 2, 4

- [x] 7. Cover the ingest contract in `tests/test_ui_corpus_ingest.py` <!-- id:uxc007 -->
  - Idempotency: second run over identical input reports all-unchanged and mutates no file (Req 4)
  - Triage preservation: hand-edited concerns/sentiment/status and body text below the marker survive re-ingestion, including when the upstream comment was edited (Req 5)
  - Epoch split on the real 14-thread snapshot yields 1 ingested and 13 excluded, and the overrides invert a decision in both directions (Req 6)
  - Verbatim round-trip, including a body containing a fenced block (Req 2)
  - Requirements: 2, 4, 5, 6
  - Blocked-by: 6

## Ingest the real comment

- [x] 8. Run the ingest over the archived snapshot and triage the one real observation <!-- id:uxc008 -->
  - Ingest produces one observation and thirteen ledger rows
  - Triage by hand: assign concerns and sentiment, record the reading, and flag what is genuinely ambiguous rather than resolving it
  - Promote to two principles in `ui-ux-guide.md` — one affirming, one defect — both citing the observation and naming variant B
  - Requirements: 3, 7, 8, 9, 10
  - Blocked-by: 3, 6

## Documentation

- [x] 9. Write `ui-ux/README.md` for a session with no memory of this conversation <!-- id:uxc009 -->
  - The two layers and why they are separate; how to read the corpus; the exact command to ingest; how to triage; how the epoch works and how to override it
  - Requirements: 13
  - Blocked-by: 8

- [x] 10. Update `CHANGELOG.md` and `specs/OVERVIEW.md` <!-- id:uxc010 -->
  - One `### Added` entry under `[Unreleased]` in the existing body style
  - One table row and one section in `specs/OVERVIEW.md`, matching the existing entries
  - Requirements: 14
  - Blocked-by: 9

## Verification

- [x] 11. Confirm nothing else in the toolchain moved <!-- id:uxc011 -->
  - `make test` discovers the new module and all 13 of its tests pass (187 → 200 tests)
  - `make lint` passes: shellcheck clean, no generated-file drift
  - Pre-existing, unrelated: 18 failures in `tests/test_process_status.py` (15 `BacklogStatusTest`, 3 `RuneDriftTest`) reproduce identically on a clean `main` worktree, so `make test` exits non-zero on this branch for reasons this spec did not introduce. `RuneDriftTest` needs the `rune` binary, which is not installed here
  - The modified reader is shellcheck-clean, checked by hand
  - Requirements: 11, 14
  - Blocked-by: 7, 10

- [ ] 12. Confirm the task file parses <!-- id:uxc012 -->
  - `rune list specs/ui-ux-corpus/tasks.md` parses and reports the task set
  - Note: `rune` is not installed on this machine (`which rune` finds nothing), so this was not verified at authoring time and must be run before the spec is marked done
  - Requirements: 14
