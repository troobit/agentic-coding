---
references:
    - prd.md
---
# Nextup/Starwave process refinement — Align tooling

## Nextup template step

- [ ] 1. Add nextup-template pipeline step: seed nextup.example.md when absent <!-- id:8rijc2p -->
  - Copy canonical nextup.example.md from this repo root when the target lacks it
  - Apply-mode run creates a byte-identical copy
  - Second run reports no pending changes (idempotent)

- [ ] 2. Converge machine zone of existing nextup.example.md; preserve user zone <!-- id:8rijc2q -->
  - Everything from the first <!-- LM --> marker down converges to the canonical template
  - User zone above the marker is preserved byte-for-byte
  - A file already matching canonical reports no change
  - Blocked-by: 8rijc2p (Add nextup-template pipeline step: seed nextup.example.md when absent)

- [ ] 3. Ensure target .gitignore ignores nextup.md when seeding/converging <!-- id:8rijc2r -->
  - Append exactly one nextup.md line if missing; create .gitignore if absent
  - A repo already ignoring it is unchanged
  - Blocked-by: 8rijc2p (Add nextup-template pipeline step: seed nextup.example.md when absent)

- [ ] 4. Guarantee align never creates, modifies, or deletes target nextup.md <!-- id:8rijc2s -->
  - nextup.md is session-local
  - Fixture repo containing nextup.md ends the run bit-identical
  - Blocked-by: 8rijc2p (Add nextup-template pipeline step: seed nextup.example.md when absent)

- [ ] 5. Honour the plan-only contract for nextup-template fixes <!-- id:8rijc2t -->
  - Without --yes on a repo with an existing manifest, pending seed/convergence is reported but not applied
  - Filesystem unchanged apart from first-run .agentic.json creation
  - Blocked-by: 8rijc2q (Converge machine zone of existing nextup.example.md; preserve user zone), 8rijc2r (Ensure target .gitignore ignores nextup.md when seeding/converging)

## Tests

- [ ] 6. Add fixtures and unittest coverage for the nextup-template step <!-- id:8rijc2u -->
  - One fixture per acceptance case in PRD Align tooling requirements 1-5
  - make test passes
  - Removing the new step fails at least one new test
  - Blocked-by: 8rijc2q (Converge machine zone of existing nextup.example.md; preserve user zone), 8rijc2r (Ensure target .gitignore ignores nextup.md when seeding/converging), 8rijc2s (Guarantee align never creates, modifies, or deletes target nextup.md), 8rijc2t (Honour the plan-only contract for nextup-template fixes)
