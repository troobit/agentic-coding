# Customer document authoring reference

Rules for authoring customer documents — Statements of Work ("agreements") and
invoices — as YAML in the `tocs` repository (`~/repos/tocs`). This document is
tool-neutral: hand it to any model or operator and the rules apply as written.

Ground truth lives in tocs itself. Every rule below names the file that
demonstrates it; when this document and tocs disagree, tocs wins:

- `tocs/customers/example/customer.yaml` — worked customer file
- `tocs/customers/example/agreements/sow-001.yaml` — worked SoW agreement
- `tocs/customers/example/invoices/AM-2026-07-05-01.yaml` — worked invoice copy
- `tocs/docs/invoice-linking.md` — the SoW ↔ invoice referencing rules
- `tocs/defaults.yaml.example` — vendor identity, tax rate, global rate card

## Folder layout

One folder is the whole picture of a customer (layout documented at the top of
`tocs/customers/example/customer.yaml`):

```
customers/<slug>/
  customer.yaml        # client identity + rate card + per-document fields
  agreements/          # one YAML per Statement of Work (sow-*.yaml)
  invoices/            # invoicer-schema invoice YAML copies
```

- `<slug>` is a short lowercase folder name for the client (e.g. `example`).
- To onboard a new client, copy `tocs/customers/example/` to
  `customers/<slug>/` and edit the values — no template edits required.
- SoW files are named `sow-<nnn>.yaml` (`sow-001.yaml`, `sow-002.yaml`, …); a
  customer accumulates one file per engagement.
- Invoice files are named after their `invoice_number`
  (e.g. `AM-2026-07-05-01.yaml`).

## customer.yaml fields

Ground truth: `tocs/customers/example/customer.yaml`. Four top-level blocks:

### `client` — client identity

| Field     | Meaning                                        |
|-----------|------------------------------------------------|
| `name`    | Legal client name (e.g. "Acme Robotics Pty Ltd") |
| `abn`     | Client ABN, 11 digits as a string              |
| `address` | Client address as printed on documents         |
| `contact` | Primary contact person                         |

Vendor identity is NOT here — it lives in `tocs/defaults.yaml` (see
`tocs/defaults.yaml.example`).

### `rates` — per-customer rate card

A map of named rates negotiated with this customer, e.g.
`support_per_user: 99.00`. Line items reference these by key via `rate_ref`
(resolution order below).

### `documents` — per-doctype fields

One block per document type (`tos`, `msa`, `proposal`, `sow`), exposed to that
document's template as `data.fields`. Common fields: `date` (ISO `YYYY-MM-DD`)
and `client_title` (signatory title). The `proposal` block additionally carries
`commitment_term`, `payout_figure`, and the cross-reference fields `msa_ref`
and `invoice_refs` (see "Two-way referencing" below). The `sow` block holds
fields that apply to every SoW for the customer; on conflict, the agreement
YAML's own fields win (documented in the `sow` comment of
`tocs/customers/example/customer.yaml`).

### `line_items` — proposal pricing

Invoicer-compatible line items (shape below) that drive the proposal's fee
table.

## Agreement (SoW) YAML fields

Ground truth: `tocs/customers/example/agreements/sow-001.yaml`. One YAML per
SoW under `customers/<slug>/agreements/`. The file carries the SoW's substance
only; client identity and the rate card come from the owning `../customer.yaml`
(the loader walks up parent directories to find it).

| Field          | Meaning                                                           |
|----------------|-------------------------------------------------------------------|
| `sow_ref`      | Names this SoW in cross-references and the output filename (e.g. `SOW-2026-ACME-001`) |
| `date`         | SoW date, `YYYY-MM-DD`                                            |
| `title`        | SoW heading and PDF header band text                              |
| `term`         | Drives the TERM section and fee-table commitment row (e.g. `12 Months`) |
| `msa_ref`      | The governing Managed Services Agreement (e.g. `MSA-2026-ACME-01`) |
| `invoice_refs` | List of invoice numbers raised under this SoW                     |
| `scope`        | Prose Markdown rendered as SCOPE OF SERVICES                      |
| `deliverables` | List of strings rendered as the DELIVERABLES bullets              |
| `line_items`   | Invoicer-compatible pricing (shape below)                         |

## Invoice YAML fields (invoicer schema)

Ground truth: `tocs/customers/example/invoices/AM-2026-07-05-01.yaml`; the
schema is invoicer's (see `~/repos/invoicer/invoice-0001.yaml` for the source
side). Files under `customers/<slug>/invoices/` are plain copies — invoicer
renders invoices; tocs never does. The copies exist so cross-references can be
verified.

| Field            | Meaning                                            |
|------------------|-----------------------------------------------------|
| `invoice_number` | The invoice's identity; what `invoice_refs` matches (e.g. `AM-2026-07-05-01`) |
| `issue_date`     | `YYYY-MM-DD`                                        |
| `due_date`       | `YYYY-MM-DD` (issue date + payment terms; `payment_terms_days` in `tocs/defaults.yaml.example` is 14) |
| `client_name`    | Client name as billed                               |
| `client_address` | Client billing address                              |
| `client_abn`, `client_identity` | Optional; present in invoicer's own examples (`~/repos/invoicer/invoice-0001.yaml`), may be empty |
| `line_items`     | Numeric-rate line items (shape below); no `rate_ref` here |

## Shared line-item shape

Both schemas use the same line-item shape, per the table in
`tocs/docs/invoice-linking.md`:

| Field         | Meaning                                                      |
|---------------|--------------------------------------------------------------|
| `type`        | Free-form label (`monthly`, `daily`, `other_bespoke`, …)     |
| `description` | Line description; on invoices it also carries the SoW/MSA back-reference |
| `quantity`    | Units                                                        |
| `rate`        | Unit price ex-GST, numeric                                   |
| `rate_ref`    | Alternative to `rate` in tocs files only: a named-rate key   |

Derived figures are never written into the YAML: `net = quantity × rate`, GST
applies at the `tax_rate` from `tocs/defaults.yaml` (0.10 in
`tocs/defaults.yaml.example`), and both tools derive them identically
(`lib/models.py` is mirrored between the repos), so a SoW total and an invoice
total for the same lines agree to the cent.

### `rate_ref` resolution order

A line item in `customer.yaml` or an `agreements/sow-*.yaml` may carry
`rate_ref: <key>` instead of a numeric `rate`. Resolution order (documented in
the rate-card comment of `tocs/customers/example/customer.yaml` and the
line-items comment of `tocs/customers/example/agreements/sow-001.yaml`):

1. The customer's own `rates` map in `customers/<slug>/customer.yaml`.
2. The global `rates` map in `tocs/defaults.yaml` (see
   `tocs/defaults.yaml.example`: `daily`, `overtime`, `white_glove`, `on_call`).

An explicit `rate` always wins over `rate_ref`. Invoice YAMLs are invoicer
schema and take numeric `rate` only — when copying SoW line items to an
invoice, replace each `rate_ref` with its resolved numeric value; every other
field is copied unchanged so the totals stay identical.

## Two-way referencing rules

Ground truth: `tocs/docs/invoice-linking.md`. The SoW and the invoice each
point at the other:

1. **SoW → invoice**: every entry in a SoW's (or proposal's) `invoice_refs`
   list must match the `invoice_number` of a YAML in the customer's
   `../invoices/` folder. tocs checks this at generation time and prints a
   warn-only stderr line per missing reference, e.g.

   ```
   Warning: invoice ref 'AM-2026-08-01-01' has no matching invoice_number under 'customers/example/invoices'
   ```

2. **Invoice → SoW**: invoicer has no dedicated reference field, so the
   back-reference rides in the line `description` text, e.g.
   `"Fixed Fee Remote Support Agreement Per User (per Statement of Work,
   MSA-2026-ACME-01)"` in
   `tocs/customers/example/invoices/AM-2026-07-05-01.yaml`.

Consequences when authoring:

- Raising a new invoice under a SoW means TWO edits: write the invoice YAML
  into `customers/<slug>/invoices/`, and add its `invoice_number` to the
  owning SoW's `invoice_refs`.
- Amending a SoW must not leave `invoice_refs` or `msa_ref` stale — remove or
  correct references when the underlying documents change.
- A dangling `invoice_refs` entry (no matching `invoice_number` file) is the
  defect to report by name when auditing.

## Generating documents (schema check)

Run from the tocs repo root (commands per `tocs/README.md`):

```sh
uv run toes.py generate sow customers/<slug>/agreements/sow-<nnn>.yaml
uv run toes.py generate proposal customers/<slug>
```

Generation is the schema check: it fails on malformed YAML or missing required
fields, and prints the invoice-reference warnings described above. Always
generate after creating or amending a SoW so errors surface immediately.

Note: the entry point is `toes.py` (per `tocs/README.md`); some in-file
comments in `tocs/customers/example/customer.yaml` refer to `tocs.py`, which
does not exist.

## Audit checklist

To verify a customer folder (`customers/<slug>/`):

1. Structure: `customer.yaml` exists; `agreements/` and `invoices/` are the
   only document subfolders; SoWs match `sow-*.yaml`.
2. Every `invoice_refs` entry (in each `agreements/sow-*.yaml` and in
   `documents.proposal` of `customer.yaml`) matches an `invoice_number` in
   `invoices/`. Report each dangling reference by its exact value.
3. Every `rate_ref` key resolves against the customer rate card or the global
   `rates` in `tocs/defaults.yaml`.
4. Invoice line descriptions carry the SoW/MSA back-reference.
5. Where an invoice copies a SoW's line items, `type`/`quantity`/rate values
   match, so totals agree to the cent.

`tocs/customers/example/` passes this checklist and is the fixture to compare
against.
