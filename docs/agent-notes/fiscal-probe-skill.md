# fiscal-probe skill

Skill at `claude/skills/fiscal-probe/` (symlinked into `~/.claude/skills` by
`make sync`). Probes PDF financial statements into a typed transaction ledger
and produces reports where every claim carries a `[file p.N]` reference —
primary use is supporting legal briefs in Australian family law property
matters. Spec: `specs/fiscal-probe-skill/`.

## Architecture

Two stdlib-only Python scripts (no pip dependencies; `pdftotext` from poppler
is the only external tool, with a pdfplumber fallback if installed):

- `scripts/extract_transactions.py` — PDFs → `transactions.csv`. Per-file
  auto-detection of date format (DMY/MDY via unambiguous dates) and currency
  (ISO code > country cues > unambiguous symbol; bare `$` is never trusted).
  Sign inference order: debit/credit column position > explicit CR/DR or
  minus > balance delta (`sign=inferred`) > credit-card convention.
  Prints parse yield per file; <80% means manual verification (SKILL.md step 3).
- `scripts/analyze.py` — CSV → markdown/txt report + optional `--json`
  payload. Merchant normalisation + difflib fuzzy grouping (≥0.85), recurring
  detection (≥3 txns, median interval 6–95d, CV<0.35, amount spread <25%),
  transfer pairing (equal absolute amount, opposite signs, different source
  files, ±3 days). Tunables are constants at the top.

## Non-obvious behaviour

- `analyze.py` assigns `_id` (list index after date sort) per run; the JSON
  `groups`/`recurring`/`transfers` reference these ids. Ids are NOT durable
  across runs with different filters — `references/json-contract.md` is the
  frontend contract and says what to persist instead.
- Transfer matching is exact-amount; a transfer arriving minus a fee won't
  auto-match (documented caveat in SKILL.md).
- Column detection (`find_columns`) needs a header line matching both a
  debit and a credit header regex within the first 30 lines of a page;
  amounts are assigned to the column whose edge is nearest (tol 18 chars).
- The extractor seeds the running balance from OPENING/CLOSING BALANCE lines
  (non-transaction lines) to enable balance-delta sign inference.

## Testing

Verified end-to-end with synthetic fixtures (no real financial data): a raw
PDF writer + statement generator live in the session scratchpad pattern —
two AU statements (business account with Withdrawals/Deposits/Balance
columns and DD/MM/YYYY dates; personal account with textual dates "02 Apr"
and signs only derivable from balance deltas). Results: 100% parse yield on
both, AUD detected via ABN/Pty Ltd and Westpac/NSW cues, 5 transfer pairs
and 2 recurring groups found. The checked-in
`references/example-full-report.md` and `example-cash-listing.md` were
generated from that run. If scripts change, regenerate the examples the same
way rather than hand-editing them.

## Court context

The user's "tier 2" means FCFCOA Division 2 — the general-intake division
where nearly all family law matters are filed. Division allocation is by
complexity (Division 1 takes transferred complex matters), NOT by a
capital-value threshold; don't let report wording imply one. The skill's
output rules are identical in both divisions.

## Report language rules

Reports state observations with references, never allegations or legal
characterisation — SKILL.md has the brief-specific rules (disclosure gaps
are findings; totals must re-derive from listed transactions). Keep those
sections intact when editing.
