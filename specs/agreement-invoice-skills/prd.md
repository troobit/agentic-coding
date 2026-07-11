# PRD: Agreement/invoice authoring skills and process guardrails

## Product summary

Skills and documentation for authoring customer documents — Statements of Work
("agreements") and invoices — as YAML, with the cross-references between them
maintained and verified. The document domain lives in `~/repos/tocs`
(`customers/<slug>/customer.yaml`, `agreements/sow-*.yaml`,
`invoices/*.yaml` in invoicer schema; referencing rules in
`tocs/docs/invoice-linking.md`), but the skills live here in agentic-coding,
under `claude/skills/`, which `make sync` symlinks into `~/.claude` so every
session can invoke them. Because the output YAML schemas are fully known (the
worked examples under `tocs/customers/example/` document every field), the
skills are specific: free-form input in, schema-correct YAML out, references
checked.

The same intent — structure is retained, not improvised — extends to process:
sessions are required to manage tasks with the `rune` CLI and to keep work
anchored in `specs/`, but nothing currently observes or enforces either rule.
This PRD adds the guardrails: a status drift flag for non-rune task files,
strengthened conventions, and documentation, so autonomous sessions leave an
auditable spec trail.

Target repository: `~/repos/agentic-coding`.

## Goals

- A session in any repo can run a `/` command to create, update, or amend a
  customer agreement or invoice YAML from free-form input, with the
  cross-references between SoW and invoice kept correct.
- The authoring rules exist once, in a tool-neutral reference document, so the
  same instructions can be handed to Claude (via the skills), the Gemini CLI,
  or a localml-served model.
- Every new skill and structure is documented — a reader can find what exists,
  what it writes, and how to invoke it without reading skill source.
- Rune task management is observable and enforced: `make status` shows which
  repos' spec task files are rune-managed, and the conventions state the
  requirement unambiguously.

## Non-goals

- No changes inside `~/repos/tocs` or `~/repos/invoicer` — their schemas,
  templates, loaders, and docs are consumed as-is. If a schema gap is found,
  it is noted in the runbook, not fixed cross-repo.
- No invoice rendering: invoicer remains the only tool that renders invoices;
  the invoice skill produces the YAML copy under `customers/<slug>/invoices/`
  only.
- No new backend integration code for localml or Gemini — the deliverable is
  instructions those backends can consume, not plumbing that calls them.
- No automatic pushing or committing in consumer repos; the skills write
  files, the operator commits.
- No changes to align.py's managed-file set (MCP configs, `.github` assets).

## Customer-doc skills

Covers `claude/skills/` (new skill folders), `docs/reference/`, and
`docs/runbooks/`. Schema ground truth: `tocs/customers/example/customer.yaml`,
`tocs/customers/example/agreements/sow-001.yaml`,
`tocs/customers/example/invoices/AM-2026-07-05-01.yaml`, and
`tocs/docs/invoice-linking.md`.

1. A tool-neutral authoring reference MUST exist at
   `docs/reference/customer-docs-authoring.md` capturing the rules the skills
   apply: the `customers/<slug>/` folder layout, every field of the three YAML
   schemas (customer, SoW agreement, invoicer invoice), the shared line-item
   shape (`type`, `description`, `quantity`, `rate`/`rate_ref`), `rate_ref`
   resolution order (customer rate card, then `defaults.yaml` rates), and the
   referencing rules (`invoice_refs` entries match an `invoice_number` in
   `../invoices/`; the invoice back-reference rides in line descriptions).
   - Acceptance: the document names concrete file paths in tocs for each rule
     it states, and contains no Claude-specific instructions, so it can be
     pasted to the Gemini CLI or a localml-served model as-is.
   - Acceptance: the referencing section reproduces the two-way check
     (SoW → invoice via `invoice_refs`, invoice → SoW via description
     back-reference) consistent with `tocs/docs/invoice-linking.md`.
2. An `agreement` skill MUST exist at `claude/skills/agreement/SKILL.md` that
   creates or amends `customers/<slug>/agreements/sow-*.yaml` in tocs from
   free-form input (notes, email text, dictated scope).
   - Acceptance: given input naming a new customer, the skill's instructions
     produce the customer folder (`customer.yaml` copied from the example and
     edited) plus a `sow-<nnn>.yaml`, and end by running the tocs generation
     command for the SoW so schema errors surface immediately.
   - Acceptance: the skill instructs updating `invoice_refs`/`msa_ref` rather
     than leaving them stale when amending an existing SoW, and defers all
     schema detail to the authoring reference instead of duplicating it.
3. An `invoice` skill MUST exist at `claude/skills/invoice/SKILL.md` that
   creates or updates an invoicer-schema YAML under
   `customers/<slug>/invoices/` for a given SoW.
   - Acceptance: the produced YAML copies the SoW's `line_items` unchanged
     (so totals agree to the cent), carries the SoW/MSA back-reference in the
     line descriptions, and uses an `invoice_number` that the owning SoW's
     `invoice_refs` lists.
   - Acceptance: the skill's final step verifies the two-way reference and
     reports any `invoice_refs` entry with no matching invoice YAML.
4. A `customer-docs-check` skill MUST exist at
   `claude/skills/customer-docs-check/SKILL.md` that audits one customer
   folder (or all of `customers/`) for structure and reference integrity.
   - Acceptance: running it against `tocs/customers/example/` reports clean;
     against a fixture with a dangling `invoice_refs` entry it reports the
     specific missing `invoice_number`.
5. The three skills SHOULD state, in their descriptions, that they operate on
   the tocs repository and how they behave when invoked from elsewhere
   (resolve `~/repos/tocs`; abort with a plain message if it is missing).
   - Acceptance: each SKILL.md description names tocs; invoking guidance
     covers the not-in-tocs case.
6. A runbook MUST exist at `docs/runbooks/customer-docs.md` documenting the
   workflow end to end: the three skills, the authoring reference, and how to
   drive the same authoring rules from the Gemini CLI or a localml-served
   model (pointing the backend at the reference document).
   - Acceptance: the runbook lists each skill with a one-line invocation
     example and links the authoring reference and
     `tocs/docs/invoice-linking.md`.

## Process guardrails

Covers `shared/conventions.md` (and regenerated outputs), `scripts/process_status.py`,
`tests/`, and `docs/runbooks/`. Ground truth for rune file format: `rune list
<file>` parses it (see `tocs/specs/toes/tasks-*.md` for live examples).

1. `make status` MUST report rune drift: a repo whose `specs/**` task files
   (`tasks.md` or `tasks-*.md`) exist but fail `rune list` parsing gets a
   `rune-drift` flag on its row, and per-spec detail lines say which file
   failed.
   - Acceptance: a fixture repo with a hand-written non-rune `tasks.md` is
     flagged `rune-drift`; `tocs` (live rune files) is not flagged.
   - Acceptance: the check stays read-only against target repos, matching
     process_status.py's existing `--no-optional-locks` discipline, and a
     missing `rune` binary degrades to a warning line, never a crash.
2. `shared/conventions.md` MUST state the task-management rule enforceably:
   tasks are managed with the `rune` CLI, task files live under the feature's
   `specs/` folder, and committed feature work requires its spec documents
   (design or PRD, plus tasks) to exist in `specs/` first.
   - Acceptance: `make generate` propagates the wording into the generated
     outputs (`claude/CLAUDE.md`, copilot instructions) and `make lint` shows
     no drift.
3. `scripts/bootstrap.sh` (or the Brewfile, whichever fits its existing
   structure) MUST ensure the `rune` binary is on PATH on a fresh machine,
   given `~/repos/rune` exists.
   - Acceptance: on a machine where `which rune` fails but `~/repos/rune/rune`
     exists, bootstrap makes `which rune` succeed (symlink or PATH entry),
     and re-running bootstrap is idempotent.
4. A runbook MUST exist at `docs/runbooks/rune-usage.md`: when task files are
   created (starwave tasks phase, engage derivation), where they live, the
   commands sessions use day to day (`rune list`, `add`, status updates), and
   what the `rune-drift` status flag means and how to clear it.
   - Acceptance: the runbook's commands run as written against a real task
     file (e.g. one under this PRD's own specs folder once engage derives it).
5. The status report SHOULD surface spec retention for autonomous work: a
   repo row's detail lines list spec folders containing a `prd.md`, so
   PRD-lane work is visible alongside starwave specs.
   - Acceptance: `make status` run from this repo shows
     `agreement-invoice-skills` with `prd.md` in its detail line.

## Execution notes

- Quality gates: `make test` (Python unittest suite) and `make lint`
  (shellcheck + generated-file drift) in this repo. Run `make generate` after
  editing `shared/conventions.md`. New process_status behaviour gets tests in
  `tests/test_process_status.py` following the existing fixture pattern.
- The two contexts are independent: Customer-doc skills touches
  `claude/skills/` and `docs/`; Process guardrails touches `shared/`,
  `scripts/`, `tests/`, and `docs/runbooks/rune-usage.md` only. No shared
  files — `docs/runbooks/` gains one distinct file per context.
- Skills become invocable via the existing `make sync` symlink of
  `claude/skills` into `~/.claude`; no sync changes needed.
- Consumer repos (tocs, invoicer) are read-only reference material for both
  contexts; nothing in them is edited.
- STOP — pushing any resulting commits is a human step: the no-push-main hook
  stops agents, and the operator reviews before push.
