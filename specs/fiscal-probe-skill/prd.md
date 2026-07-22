# PRD: fiscal-probe skill

## Product summary

A skill for probing a multitude of financial documents — PDF bank and
credit-card statements, business ledgers — and producing reports in which
every claim carries a `[file p.N]` source reference, so the output can
support legal briefs in Australian family law property matters. The skill
lives at `claude/skills/fiscal-probe/`, which `make sync` symlinks into
`~/.claude/skills` so every session can invoke it.

The pipeline is two deterministic Python scripts with agent judgement in
between: `extract_transactions.py` (PDFs → normalised CSV ledger, with
per-file parse-yield reporting, date-format and currency auto-detection) and
`analyze.py` (CSV → markdown/txt report plus a machine-readable JSON payload).
The JSON payload is the contract for a planned fiscal-probe web frontend;
`references/json-contract.md` documents it.

Origin: the scripts and skill body were imported from a packaged
`financial-insights.skill` bundle and adapted — renamed, given an Australian
family-law brief section, and extended with stable transaction ids in the
JSON output for frontend claim references.

## Goals

- A session can turn a set of statement PDFs into a typed transaction ledger
  and filtered reports (cash, transfers, recurring, merchant groups) without
  bespoke code, with parse quality made visible and verified before analysis.
- Every figure in a report is traceable to a source file and page; report
  language states observations, never allegations — the solicitor draws
  conclusions.
- `--json` output is stable and documented so a web frontend can render the
  same findings with per-claim references.

## Non-goals

- The web frontend itself (future work; this PRD only fixes its data
  contract).
- OCR of scanned statements (the skill defers to rasterise/OCR guidance and
  manual parsing).
- Legal analysis: no legislation, case law, or characterisation of conduct in
  generated output.

## Acceptance

- Skill discoverable as `fiscal-probe` from `~/.claude/skills`.
- End-to-end run on synthetic AU fixtures (business account with
  debit/credit columns; personal account with balance-inferred signs and
  textual dates) yields 100% parse rate, AUD detection, recurring and
  cross-account transfer detection; worked example outputs checked in under
  `references/`.
- `analyze.py --json` emits integer pages and stable per-run transaction ids
  used by groups, recurring, and transfer entries.
