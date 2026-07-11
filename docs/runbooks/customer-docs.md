# Runbook: customer document authoring (agreements and invoices)

End-to-end workflow for authoring customer documents — Statements of Work and
invoice YAML copies — in the tocs repository (`~/repos/tocs`), using the three
skills in this repo or any other model backend.

The pieces:

- **Authoring rules (tool-neutral)**:
  [`docs/reference/customer-docs-authoring.md`](../reference/customer-docs-authoring.md)
  — folder layout, the three YAML schemas, the shared line-item shape,
  `rate_ref` resolution, and the two-way referencing rules. Backend-agnostic
  by design; every rule names its ground-truth file in tocs.
- **Referencing ground truth**: `~/repos/tocs/docs/invoice-linking.md` — the
  SoW ↔ invoice linking rules the reference reproduces.
- **Three Claude skills** under `claude/skills/`, symlinked into `~/.claude`
  by `make sync`, so they are invocable from any session in any repo. Each
  resolves `~/repos/tocs` itself and aborts plainly if it is missing.

## The skills

| Skill | Writes | Invocation example |
|-------|--------|--------------------|
| [`agreement`](../../claude/skills/agreement/SKILL.md) | `customers/<slug>/agreements/sow-*.yaml` (plus the customer folder for a new client) | `/agreement draft a SoW for Acme Robotics: 12 users remote support at $99/user/mo, quarterly onsite visit, 12 month term` |
| [`invoice`](../../claude/skills/invoice/SKILL.md) | `customers/<slug>/invoices/<invoice_number>.yaml` and the owning SoW's `invoice_refs` | `/invoice raise this month's invoice for Acme under sow-001` |
| [`customer-docs-check`](../../claude/skills/customer-docs-check/SKILL.md) | nothing — read-only audit report | `/customer-docs-check audit customers/acme` (no argument audits all of `customers/`) |

All three defer schema detail to the authoring reference rather than carrying
their own copy — the reference is the single place the rules live. The skills
write files only; committing in tocs is the operator's step.

## Typical flow

1. `/agreement` with the free-form scope — produces (or amends) the SoW and
   runs `uv run toes.py generate sow ...` so schema errors surface
   immediately.
2. `/invoice` when billing — copies the SoW's line items (totals agree to the
   cent), adds the SoW/MSA back-reference to the descriptions, and lists the
   `invoice_number` in the SoW's `invoice_refs`.
3. `/customer-docs-check` any time — verifies structure and both reference
   directions; a dangling `invoice_refs` entry is reported with the exact
   missing `invoice_number`.

## Driving the same rules from other backends

The rules were deliberately kept out of the skills: the reference document
contains no Claude-specific instructions, so any backend that can read a file
and follow instructions can author the same YAML. Point the backend at the
reference plus the task, and review its output the same way (run the tocs
generation command; run `/customer-docs-check` afterwards or apply the
reference's audit checklist by hand).

### Gemini CLI

Pass the reference document as context with the task:

```sh
cd ~/repos/tocs
gemini -p "Follow the rules in ~/repos/agentic-coding/docs/reference/customer-docs-authoring.md exactly. Task: draft agreements/sow-002.yaml for customers/acme covering <scope>."
```

(Equivalently, paste the reference's content ahead of the task in an
interactive session — it is small enough to inline.)

### localml-served model

Serve a model locally (see
[`docs/runbooks/localml-vscode.md`](localml-vscode.md) for the server side):

```sh
cd ~/repos/localml && uv run localml serve <publisher>/<name>
```

Then send the reference as the system/first message and the task after it,
against the OpenAI-compatible endpoint:

```sh
curl -s http://127.0.0.1:8080/v1/chat/completions -H 'Content-Type: application/json' -d "$(python3 - <<'EOF'
import json, pathlib
rules = pathlib.Path.home().joinpath("repos/agentic-coding/docs/reference/customer-docs-authoring.md").read_text()
print(json.dumps({
    "model": "<publisher>/<name>",
    "messages": [
        {"role": "system", "content": "Follow these authoring rules exactly:\n\n" + rules},
        {"role": "user", "content": "Draft agreements/sow-002.yaml for customers/acme covering <scope>. Output only the YAML."},
    ],
}))
EOF
)"
```

Local models write the YAML; the operator saves it into tocs and runs the
generation command — the schema check is the same regardless of backend.

## Notes

- Ground truth for every rule is tocs itself (`customers/example/*`,
  `docs/invoice-linking.md`, `defaults.yaml.example`). tocs and invoicer are
  never edited by this workflow's tooling; if a schema gap turns up, note it
  here rather than patching those repos.
- Known gap: comments inside `tocs/customers/example/customer.yaml` name a
  `tocs.py` entry point; the actual entry point is `toes.py` (per
  `tocs/README.md`). The reference and skills use `toes.py`.
- Nothing here renders invoices — `~/repos/invoicer` remains the only
  renderer. The YAML under `customers/<slug>/invoices/` is a copy kept for
  cross-referencing.
