---
name: fiscal-probe
description: Probe a multitude of financial documents (PDF bank/credit-card statements, business ledgers; AU/NZ/SG/UK/US formats incl. Westpac, ANZ, DBS, Xero-style) and produce reports where every claim carries a source reference, suitable for legal briefs in Australian family law property matters. Use whenever the user uploads statements or ledger exports, or asks about financial disclosure review, spending analysis, recurring payments, cash withdrawals, transfers between accounts, business-to-personal money flows, tracing funds for a property settlement or brief, or "where did the money go" questions — even if they don't say "statement" or "PDF" explicitly. Extracts transactions into a normalised typed ledger, groups similar/recurring transactions, cross-references transfers between accounts, and emits markdown/txt reports plus machine-readable JSON (the contract for the fiscal-probe web frontend).
---

# Fiscal Probe

Turn PDF financial statements into a normalised transaction ledger, then surface findings: spending breakdowns, recurring payments, similar-transaction groups, and cross-account transfers. Every reported transaction carries a traceable `[file p.N]` link back to its source document and page — a claim without a reference cannot go in a brief.

## Workflow

The pipeline is two deterministic scripts plus your judgement in between:

```
PDFs → extract_transactions.py → transactions.csv → [verify parse quality] → analyze.py → report.md (+ report.json)
```

### Step 1 — Inventory the PDFs

Before extracting, check each PDF has a text layer:

```bash
pdffonts statement.pdf
```

Empty font table → scanned document. `pdftotext`/pdfplumber will return nothing. Rasterise pages (`pdftoppm -jpeg -r 150`) and read them visually, or OCR with pytesseract, then feed the text through the same parsing logic manually. The pdf-reading skill covers this in depth.

### Step 2 — Extract

```bash
python3 ~/.claude/skills/fiscal-probe/scripts/extract_transactions.py statement1.pdf statement2.pdf -o transactions.csv
```

The script:
- Extracts layout-preserved text per page (`pdftotext -layout`, pdfplumber fallback)
- Auto-detects date format per document (DD/MM vs MM/DD vs ISO, resolved via unambiguous dates where day > 12; defaults to DD/MM if truly ambiguous — tell the user when this happens)
- Auto-detects currency per document: explicit ISO code first, then country cues (ABN/BSB/Pty Ltd → AUD; NZBN → NZD; UEN/PayNow/Singapore → SGD), then unambiguous symbols. **A bare `$` is never trusted** — it's ambiguous across AUD/NZD/SGD/USD and gets flagged as `$?`. Resolve with `--currency file.pdf=AUD` (or `ALL=AUD`). Getting this wrong silently corrupts cross-currency analysis, so never guess on the user's behalf — ask if cues are absent.
- Parses transaction lines (date + description + amount [+ balance])
- Infers sign from statement structure: separate debit/credit columns, trailing CR/DR markers, or balance deltas
- Writes a CSV: `source_file, page, date (ISO), description, amount, balance, currency, sign`
- Prints a **parse yield** per file: candidate lines vs parsed lines

### Step 3 — Verify parse quality (do not skip)

Bank statement layouts are heterogeneous. The parser handles common tabular layouts, but a low parse yield (<80%) or suspicious output means the format needs custom handling:

1. Dump the raw text: `pdftotext -layout statement.pdf - | head -60`
2. Compare against the CSV — check dates, signs, and amounts against the raw text for ~5 transactions
3. If the layout is unusual (multi-line descriptions, amounts on separate lines, no date column), write a bespoke parser for that file reusing the helpers in `extract_transactions.py` (import `parse_amount`, `detect_date_format`, `normalise_date`), and merge its rows into the same CSV
4. Cross-check totals: if the statement shows opening/closing balances, sum of amounts should equal the delta. Report any mismatch to the user rather than silently proceeding.

### Step 4 — Analyse and report

```bash
python3 ~/.claude/skills/fiscal-probe/scripts/analyze.py transactions.csv -o report.md --json report.json
```

Filters (composable):

| Flag | Effect |
|---|---|
| `--from 2026-01-01 --to 2026-03-31` | Date range |
| `--merchant netflix` | Fuzzy merchant filter (matches normalised group names) |
| `--min 10 --max 500` | Absolute amount range |
| `--type cash,transfer` | Transaction type: cash, transfer, card, direct_debit, deposit, payment, fee, cheque |
| `--sort=-value,date` | Listing order, multi-key; `value` = absolute amount, `-` prefix = descending. Use `=` syntax when the value starts with `-` |
| `--list` | Force the transaction listing section |
| `--json out.json` | Also emit machine-readable JSON — the web-frontend contract, see `references/json-contract.md` |
| `--recurring-only` | Only recurring payment groups |
| `--transfers-only` | Only cross-account transfer pairs |
| `--txt` | Plain-text output instead of markdown |
| `--top N` | Number of merchant groups to list (default 15) |

Translating natural-language questions to flags — examples:

| User asks | Run |
|---|---|
| "Show me cash withdrawals on all accounts, order by value and date" | `--type cash --sort=-value,date` |
| "All transfers over $5k in May" | `--type transfer --min 5000 --from 2026-05-01 --to 2026-05-31` |
| "Everything at Harvey Norman" | `--merchant "harvey norman"` |
| "What's leaving the business account regularly?" | `--recurring-only` (filter CSV to that source file first) |

Type classification rules live in `TYPE_RULES` in `analyze.py` and cover UK/US/AU/NZ/SG payment rails (ATM/branch cash, Osko, EFTPOS, GIRO, PayNow, telegraphic transfers, direct debits). Extend the patterns when a statement uses vocabulary they miss — check the listing's type column against the descriptions.

The report contains: summary (period, totals, per-currency), monthly in/out, top merchant groups, recurring payments (interval + amount stability), cross-account transfer pairs, and the filtered transaction listing. Each transaction line ends with `[file p.N]` — the source link. Worked examples: `references/example-full-report.md`, `references/example-cash-listing.md`.

### Step 5 — Iterate with the user

Filtering is expected to be refined conversationally. Re-run `analyze.py` with different flags rather than re-extracting. The CSV is the durable intermediate — keep it. If the user asks something the flags don't cover (e.g. "weekends only", "everything except groceries"), filter the CSV with pandas/awk inline and pass the filtered CSV to `analyze.py`.

## Australian family law briefs (primary use)

When the output supports a brief in a family law property matter (typically FCFCOA Division 2, where most matters are filed; the same rules apply if a matter is in Division 1), apply these rules on top of the general workflow:

- **Every claim needs its reference.** Any figure, pattern, or transaction cited in prose must end with its `[file p.N]` link(s); totals must be re-derivable from the listed transactions. If a statement in the report cannot be traced to a source page, remove it.
- **Observations, not allegations.** Write "three branch cash withdrawals totalling A$57,000 [refs]" — never "funds were concealed" or any characterisation of intent. The solicitor decides relevance and characterisation (add-backs, wastage, disclosure breaches); do not cite legislation or case law in generated reports.
- **Flag disclosure gaps explicitly**: statement-period gaps within an account, accounts that appear as transfer counterparties but have no statements provided (a BSB/account number in a description with no matching source file), and periods where one party's documents stop. Gaps are findings in their own right — list them with the references that reveal them.
- **Patterns worth surfacing** (as facts with references): business→personal flows, cash withdrawal sequences, transfers to overseas accounts, round-amount or escalating withdrawals, new recurring payments starting near separation dates. Ask the user for the relevant date range (e.g. separation date) and run `--from/--to` splits around it.
- **A$ amounts to the cent**, per-currency totals never merged.

## How similarity works (so you can explain/adjust it)

- **Merchant normalisation**: uppercase, strip card refs, dates-in-descriptions, long digit runs, and payment-rail noise tokens (POS, DD, SO, VIS, CRD, BGC, FPI...). See `NOISE_TOKENS` in `analyze.py`.
- **Grouping**: exact normalised-name match, then fuzzy merge of groups at difflib ratio ≥ 0.85. Lower `FUZZY_THRESHOLD` if the user reports the same merchant split across groups; raise it if unrelated merchants merge.
- **Recurring detection**: group has ≥ 3 transactions, median interval 6–95 days, interval coefficient of variation < 0.35, amount spread < 25% of median. Constants at top of `analyze.py` — tune on user feedback.
- **Transfer detection**: opposite-sign amounts of equal absolute value across *different source files* within ±3 days.

## Output contract

Reports are markdown by default (`--txt` for plain text). `--json` additionally writes the machine-readable payload consumed by the fiscal-probe web frontend; its schema is documented in `references/json-contract.md` — treat that file as the contract and update it whenever the payload shape changes. Never invent transactions or categories not present in the data. If the user asks for category spending (groceries, transport...), the data usually lacks categories — propose a merchant→category mapping, confirm it with the user, then apply it.

## Investigation / audit context

When statements are being reviewed for irregularities (fraud, audit, dispute):

- **Never assert fraud.** Report observable patterns — round-amount cash withdrawals, business→personal flows, transfers to overseas accounts, structuring-like sequences — as facts with source links, and let the investigator draw conclusions.
- **Evidence integrity**: keep the raw PDFs untouched, keep the CSV as the working copy, and preserve `[file p.N]` links on every claim so findings are independently verifiable against source documents.
- **Reconcile before reporting.** Balance-vs-amount-sum mismatches can indicate parser error OR altered/fabricated statements — distinguish them by checking the raw text, and report discontinuities in the running balance explicitly either way.
- Money-flow tracing across accounts: run all statements through one extraction so `--transfers-only` matches across files. Amounts that leave one account and arrive at another minus a fee will NOT auto-match (matching is exact-amount); look for near-matches manually when fees apply.

## Caveats to surface to the user

- Amounts whose sign was inferred from balance deltas are marked `sign=inferred` in the CSV — flag these if totals look off.
- Overlapping statement periods are deduplicated on (date, amount, normalised description); exact same-day duplicates of identical amounts at the same merchant are kept (they're usually real).
- Multi-currency ledgers are never summed together; the report separates per currency.
