---
name: agreement
description: Create or amend a customer Statement of Work (SoW) agreement YAML in the tocs repository (~/repos/tocs) from free-form input — notes, email text, dictated scope. Writes customers/<slug>/agreements/sow-*.yaml, onboarding the customer folder first if it is new, and finishes by running the tocs SoW generation command so schema errors surface. Works from any directory by resolving ~/repos/tocs; aborts with a plain message if tocs is missing. Use when the user says "new SoW", "draft an agreement for <client>", "amend sow-002", or similar.
---

# Agreement — author a Statement of Work in tocs

Turns free-form input into a schema-correct `customers/<slug>/agreements/sow-<nnn>.yaml`
in the tocs repository. All schema and referencing rules live in the tool-neutral
reference — read it first and follow it; do not improvise fields:

- `~/repos/agentic-coding/docs/reference/customer-docs-authoring.md`

This skill adds only the workflow around those rules.

## Locate tocs

The skill operates on the tocs repository, wherever the session was started:

1. If the current directory is inside a checkout of tocs (a `customers/` folder
   and `toes.py` at the root), use it.
2. Otherwise use `~/repos/tocs`.
3. If neither exists, abort with a plain message — "The tocs repository was not
   found at ~/repos/tocs; clone it there or run this from a tocs checkout." Do
   not create a tocs skeleton.

All paths below are relative to the tocs root.

## Gather the facts

From the user's free-form input, extract: the client (name or slug), whether
this is a new SoW or an amendment to an existing one, the scope/deliverables,
the term, pricing (rates and quantities), and any MSA or invoice references.
Ask for whatever is missing rather than inventing values — especially client
identity fields and rates.

## New-customer path

If `customers/<slug>/` does not exist:

1. Copy the worked example folder: `cp -R customers/example customers/<slug>`,
   then delete the example's agreement and invoice files from the copy.
2. Edit `customers/<slug>/customer.yaml` per the reference: `client` identity,
   the `rates` card (named rates this client negotiated), and the `documents`
   dates/titles. Vendor identity stays in `defaults.yaml` — never copy it in.
3. Continue with the new-SoW path below.

## New-SoW path

1. Number the file: next free `sow-<nnn>.yaml` in `customers/<slug>/agreements/`
   (`sow-001.yaml` for the first).
2. Start from `customers/example/agreements/sow-001.yaml` as the template and
   fill every field per the reference: `sow_ref`, `date`, `title`, `term`,
   `msa_ref` (if a governing MSA exists), `invoice_refs` (usually empty for a
   new SoW), `scope`, `deliverables`, `line_items`.
3. Prefer `rate_ref` keys against the customer's rate card over inline numeric
   rates; add new named rates to the rate card rather than scattering numbers.

## Amend path

When changing an existing SoW:

1. Read the current YAML fully before editing.
2. Apply the requested changes.
3. Never leave references stale: if the amendment affects the governing MSA,
   update `msa_ref`; if invoices were raised or withdrawn, update
   `invoice_refs` so every entry still matches an `invoice_number` under
   `../invoices/`.

## Finish — generate to surface schema errors

Always end by running the tocs generation command from the tocs root:

```sh
uv run toes.py generate sow customers/<slug>/agreements/sow-<nnn>.yaml
```

- A failure means the YAML is malformed — fix and re-run.
- `Warning: invoice ref ... has no matching invoice_number` lines mean a
  dangling reference — fix `invoice_refs` (or copy the missing invoice YAML
  in) before finishing.

Report what was written and the generation result. Do not commit or push in
tocs — the operator reviews and commits.
