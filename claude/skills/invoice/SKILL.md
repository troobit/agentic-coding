---
name: invoice
description: Create or update an invoicer-schema invoice YAML under customers/<slug>/invoices/ in the tocs repository (~/repos/tocs) for a given Statement of Work, keeping the SoW ↔ invoice cross-references correct in both directions. Copies the SoW's line items so totals agree to the cent, carries the SoW/MSA back-reference in line descriptions, and lists the invoice_number in the owning SoW's invoice_refs. Works from any directory by resolving ~/repos/tocs; aborts with a plain message if tocs is missing. Use when the user says "raise an invoice for <client>", "invoice sow-002", or similar.
---

# Invoice — raise an invoice YAML under a SoW in tocs

Produces the invoicer-schema YAML copy that lives beside the SoW it bills, and
keeps the two documents pointing at each other. All schema and referencing
rules live in the tool-neutral reference — read it first and follow it:

- `~/repos/agentic-coding/docs/reference/customer-docs-authoring.md`

tocs never renders invoices — invoicer does. This skill writes only the YAML
copy under `customers/<slug>/invoices/`.

## Locate tocs

1. If the current directory is inside a checkout of tocs (a `customers/` folder
   and `toes.py` at the root), use it.
2. Otherwise use `~/repos/tocs`.
3. If neither exists, abort with a plain message — "The tocs repository was not
   found at ~/repos/tocs; clone it there or run this from a tocs checkout."

All paths below are relative to the tocs root.

## Identify the SoW

The invoice belongs to exactly one SoW. Resolve which
`customers/<slug>/agreements/sow-<nnn>.yaml` is being billed from the user's
input; if ambiguous (multiple customers or SoWs match), ask. Read the SoW and
the owning `customer.yaml` before writing anything.

## Write the invoice YAML

Model the file on `customers/example/invoices/AM-2026-07-05-01.yaml`:

1. **`invoice_number`** — follow the numbering pattern already used in this
   customer's `invoices/` folder (the examples use
   `<prefix>-YYYY-MM-DD-NN`). If the folder is empty and the user gave no
   number, ask rather than inventing a prefix. The file is named
   `<invoice_number>.yaml`.
2. **Dates** — `issue_date` today (or as instructed); `due_date` = issue date
   plus the payment terms (`payment_terms_days` in `defaults.yaml`, 14 by
   default).
3. **Client fields** — `client_name` and `client_address` from the customer's
   `customer.yaml` `client` block.
4. **`line_items`** — copied from the SoW unchanged so the totals agree to the
   cent, with exactly two permitted transformations:
   - Resolve any `rate_ref` to its numeric `rate` (customer rate card first,
     then `defaults.yaml` rates) — the invoicer schema takes numeric rates
     only.
   - Append the SoW/MSA back-reference to descriptions, e.g.
     `"... (per Statement of Work, MSA-2026-ACME-01)"` — invoicer has no
     dedicated reference field, so the back-reference rides in the
     description. At least one line must name the Statement of Work (and the
     MSA when the SoW has an `msa_ref`).

   `type` and `quantity` are never altered. Do not add lines that are not in
   the SoW without the user explicitly asking.

## Update the owning SoW

Add the new `invoice_number` to the SoW's `invoice_refs` list (create the list
if absent). When updating an existing invoice's number or deleting one, fix
`invoice_refs` in the same step — never leave it stale.

## Final step — verify the two-way reference

Before finishing, verify both directions and report the result:

1. **SoW → invoice**: for every entry in the SoW's `invoice_refs`, confirm a
   YAML in `customers/<slug>/invoices/` has that exact `invoice_number`.
   Report any entry with no matching invoice YAML, by value.
2. **Invoice → SoW**: confirm the new invoice's line descriptions carry the
   Statement of Work back-reference.

Cross-check with the generation warning (warn-only, from the tocs root):

```sh
uv run toes.py generate sow customers/<slug>/agreements/sow-<nnn>.yaml
```

Any `Warning: invoice ref ...` line is a dangling reference to fix before
finishing. Do not commit or push in tocs — the operator reviews and commits.
