---
references:
    - prd.md
---
# Agreement/invoice authoring skills and process guardrails — Customer-doc skills

## Reference

- [x] 1. Write tool-neutral authoring reference docs/reference/customer-docs-authoring.md <!-- id:jzl621k -->
  - Covers PRD Customer-doc skills Req 1: customers/<slug>/ folder layout; all fields of customer.yaml, agreements/sow-*.yaml, and invoicer-schema invoice YAML; shared line-item shape (type, description, quantity, rate/rate_ref); rate_ref resolution order (customer rate card, then defaults.yaml rates); two-way referencing rules (invoice_refs -> invoice_number, back-reference in line descriptions)
  - Every rule names a concrete tocs file path; ground truth is tocs/customers/example/* and tocs/docs/invoice-linking.md
  - No Claude-specific instructions anywhere - pasteable to Gemini CLI or a localml-served model as-is
  - Stream: 1

## Skills

- [ ] 2. Create agreement skill claude/skills/agreement/SKILL.md <!-- id:jzl621l -->
  - PRD Req 2 + 5: creates or amends customers/<slug>/agreements/sow-*.yaml in tocs from free-form input
  - New-customer path: create the customer folder by copying/editing the example customer.yaml, then add sow-<nnn>.yaml; end by running the tocs SoW generation command so schema errors surface
  - Amend path: update invoice_refs/msa_ref rather than leaving them stale
  - Defers schema detail to docs/reference/customer-docs-authoring.md instead of duplicating it
  - Description names tocs; covers behaviour when invoked outside tocs (resolve ~/repos/tocs, abort plainly if missing)
  - Blocked-by: jzl621k (Write tool-neutral authoring reference docs/reference/customer-docs-authoring.md)
  - Stream: 1

- [ ] 3. Create invoice skill claude/skills/invoice/SKILL.md <!-- id:jzl621m -->
  - PRD Req 3 + 5: creates or updates an invoicer-schema YAML under customers/<slug>/invoices/ for a given SoW
  - line_items copied unchanged from the SoW so totals agree to the cent; SoW/MSA back-reference carried in line descriptions; invoice_number listed in the owning SoW's invoice_refs
  - Final step verifies the two-way reference and reports any invoice_refs entry with no matching invoice YAML
  - Defers schema detail to the authoring reference; description names tocs and the not-in-tocs case
  - Blocked-by: jzl621k (Write tool-neutral authoring reference docs/reference/customer-docs-authoring.md)
  - Stream: 2

- [ ] 4. Create customer-docs-check skill claude/skills/customer-docs-check/SKILL.md <!-- id:jzl621n -->
  - PRD Req 4 + 5: audits one customer folder (or all of customers/) for structure and reference integrity
  - Clean run against tocs/customers/example/; against a dangling invoice_refs fixture it reports the specific missing invoice_number
  - Description names tocs and the not-in-tocs case
  - Blocked-by: jzl621k (Write tool-neutral authoring reference docs/reference/customer-docs-authoring.md)
  - Stream: 3

## Docs

- [ ] 5. Write runbook docs/runbooks/customer-docs.md <!-- id:jzl621o -->
  - PRD Req 6: documents the workflow end to end - the three skills, the authoring reference, and how to drive the same rules from the Gemini CLI or a localml-served model (point the backend at the reference document)
  - Lists each skill with a one-line invocation example; links docs/reference/customer-docs-authoring.md and tocs/docs/invoice-linking.md
  - Blocked-by: jzl621l (Create agreement skill claude/skills/agreement/SKILL.md), jzl621m (Create invoice skill claude/skills/invoice/SKILL.md), jzl621n (Create customer-docs-check skill claude/skills/customer-docs-check/SKILL.md)
  - Stream: 1
