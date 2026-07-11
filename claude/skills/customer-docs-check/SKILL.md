---
name: customer-docs-check
description: Audit customer document folders in the tocs repository (~/repos/tocs) for structure and reference integrity — one customers/<slug>/ folder or all of customers/. Read-only; reports dangling invoice_refs entries by their missing invoice_number, unresolvable rate_ref keys, missing back-references, and structural drift from the worked example. Works from any directory by resolving ~/repos/tocs; aborts with a plain message if tocs is missing. Use when the user says "check the customer docs", "audit customers/", "verify <client>'s folder", or similar.
---

# Customer-docs-check — audit customer folders in tocs

Audits customer folders against the authoring rules. It is strictly
**read-only**: it reports findings and never edits, creates, or deletes files.
The rules and the audit checklist live in the tool-neutral reference — read it
first; the checklist there is the definition of "clean":

- `~/repos/agentic-coding/docs/reference/customer-docs-authoring.md`

## Locate tocs

1. If the current directory is inside a checkout of tocs (a `customers/` folder
   and `toes.py` at the root), use it.
2. Otherwise use `~/repos/tocs`.
3. If neither exists, abort with a plain message — "The tocs repository was not
   found at ~/repos/tocs; clone it there or run this from a tocs checkout."

## Scope

- Given a customer (slug or name), audit `customers/<slug>/` only.
- Given no customer, audit every folder under `customers/`.

## Checks per customer folder

Run the reference's audit checklist:

1. **Structure** — `customer.yaml` exists and parses; agreements match
   `agreements/sow-*.yaml`; invoice YAMLs live under `invoices/` and each
   file's name matches its `invoice_number`. Flag stray files and misplaced
   documents.
2. **Required fields** — each SoW carries `sow_ref`, `date`, `title`, `term`,
   and `line_items`; each invoice carries `invoice_number`, `issue_date`,
   `due_date`, `client_name`, and `line_items`.
3. **SoW → invoice references** — every `invoice_refs` entry (in each
   `agreements/sow-*.yaml` and in `documents.proposal` of `customer.yaml`)
   matches the `invoice_number` of a YAML in `invoices/`. Report each dangling
   entry by its exact value, e.g.
   `invoice_refs 'AM-2026-08-01-01' in agreements/sow-002.yaml has no matching invoice_number under invoices/`.
4. **Invoice → SoW back-references** — each invoice's line descriptions carry
   the Statement of Work (and MSA, where the SoW has an `msa_ref`)
   back-reference.
5. **Rates** — every `rate_ref` key resolves against the customer's `rates`
   card or the global `rates` in `defaults.yaml`; invoice line items carry
   numeric `rate` only (no `rate_ref` in invoicer schema).
6. **Totals agreement** — where an invoice bills a SoW, the copied line items'
   `type`, `quantity`, and resolved rate values match, so totals agree to the
   cent.

## Report

One section per audited customer:

- **Clean** — say so in one line. `customers/example/` must always audit
  clean; if it does not, suspect the checker (or a schema change in tocs)
  before the data.
- **Findings** — one line each: severity (error for broken references or
  parse failures, warning for style drift), the file, and the specific value
  at fault. Dangling `invoice_refs` entries always name the missing
  `invoice_number` exactly.

Finish with a one-line summary (folders audited, errors, warnings). Suggest
fixes but do not apply them — remediation belongs to the `agreement` and
`invoice` skills or the operator.
