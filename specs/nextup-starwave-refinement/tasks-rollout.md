---
references:
    - prd.md
---
# Nextup/Starwave process refinement — Rollout

## Rollout

- [ ] 1. Plan-only align sweep across the six consumer repos <!-- id:73v6ng1 -->
  - Run scripts/align.py in plan-only mode against /Users/r/repos/{medata,netmap,tocs,rtob,localml,loshop}
  - Record pending changes per repo before any apply

- [ ] 2. Apply align --yes only to repos with clean working trees <!-- id:73v6ng2 -->
  - Check cleanliness at execution time
  - Dirty repos stay plan-only and are listed as skipped with the reason
  - No repo that was dirty before the run has any working-tree change afterwards
  - Blocked-by: 73v6ng1 (Plan-only align sweep across the six consumer repos)

- [ ] 3. Commit align changes in each applied repo; never push <!-- id:73v6ng3 -->
  - Commit on the repo current branch with subject [chore]: align nextup/starwave process assets
  - git status clean afterwards; no remote refs changed
  - Run repos serially, one at a time
  - Blocked-by: 73v6ng2 (Apply align --yes only to repos with clean working trees)

- [ ] 4. Run final status report across all seven repos <!-- id:73v6ng4 -->
  - Use the new make status command from agentic-coding
  - Include one row per repo with remaining drift flags in the final report
  - Blocked-by: 73v6ng3 (Commit align changes in each applied repo; never push)

- [ ] 5. STOP — human reviews consumer-repo commits and decides what to push <!-- id:73v6ng5 -->
  - Agents must not push; the no-push-main hook applies
  - Execution of this context ends here
  - Blocked-by: 73v6ng4 (Run final status report across all seven repos)
