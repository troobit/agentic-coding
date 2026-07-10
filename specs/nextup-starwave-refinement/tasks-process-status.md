---
references:
    - prd.md
---
# Nextup/Starwave process refinement — Process status

## Status script

- [x] 1. Create status script with make status target and default repo list <!-- id:xdywp55 -->
  - New Python script in scripts/ accepting repo paths as arguments
  - Defaults to this repo plus a checked-in list: medata netmap tocs rtob localml loshop
  - make status prints one summary row per default repo; explicit paths report only those

- [ ] 2. Report per-repo columns <!-- id:xdywp56 -->
  - nextup.md presence; machine-zone marker validity (<!-- LM --> or legacy <!-- ML --> / <!-- nextup:machine --> / # What I want); date of newest note
  - nextup.example.md presence; .agentic.json presence
  - Each specs/ subfolder with which of requirements.md/design.md/tasks.md/smolspec.md/prd.md it contains
  - Current branch; dirty or clean working tree; date of last commit
  - Blocked-by: xdywp55 (Create status script with make status target and default repo list)

- [ ] 3. Flag drift conditions per row <!-- id:xdywp57 -->
  - Machine zone missing or malformed
  - Newest nextup note older than 14 days while working tree is dirty
  - Spec folder with requirements.md but neither design.md nor tasks.md
  - Missing .agentic.json
  - Fixtures for each condition produce that flag and only that flag
  - Blocked-by: xdywp56 (Report per-repo columns)

- [ ] 4. Guarantee the status command is read-only against target repos <!-- id:xdywp58 -->
  - Target fixture directory trees are bit-identical before and after a run
  - Blocked-by: xdywp55 (Create status script with make status target and default repo list)

## Tests

- [ ] 5. Add fixture repos and unittest coverage for the status report <!-- id:xdywp59 -->
  - make test passes with the new tests included
  - Blocked-by: xdywp56 (Report per-repo columns), xdywp57 (Flag drift conditions per row), xdywp58 (Guarantee the status command is read-only against target repos)
