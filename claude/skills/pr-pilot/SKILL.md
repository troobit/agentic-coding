---
name: pr-pilot
description: Push a branch, open a change request, iterate on reviews until clean, then squash-merge. Runs /pr-review-fixer in a loop until no blockers/critical/major issues remain, rebases onto latest origin/main, and squash-merges. Works on both GitHub (gh) and GitLab (glab) — it detects the forge from the git remote. Works with or without Transit tickets. Use when you want to shepherd a PR/MR from push to merge, e.g. "push and merge this", "get this merged", "review-fix-merge loop".
# model: inherit
# allowed-tools: Read,Write,Edit,Bash,Grep,Glob,Task
---

# PR Pilot

Push a branch, open a change request (CR), loop through reviews until clean, then
squash-merge.

This skill is **forge-aware**: the repo may be on GitHub (`gh`) or GitLab (`glab`).
It does not hard-code either CLI — it follows the shared operation contract and the
adapter for whichever forge the repo uses. The `local-review` agent and
`/pr-review-fixer` skill it delegates to are themselves forge-aware, so just invoke
them; they self-detect.

## Forge setup (do this first)

1. Read `~/.claude/forge-adapters/CONTRACT.md` for the neutral terms and operations.
2. Run **`PREFLIGHT`** to determine `FORGE` and confirm the CLI is authenticated. If
   not, stop and tell the user how to authenticate.
3. Read the matching adapter `~/.claude/forge-adapters/<FORGE>.md`. Every concrete
   command comes from there — do not improvise `gh`/`glab` commands.

## Input

Works in the current working directory (or a specified worktree path). It needs:

- A branch with committed changes ready to push
- Optionally a Transit ticket reference (`T-{id}`) for status tracking
- Optionally an existing CR id (skips push and CR creation)

If invoked with arguments, parse them for:
- `T-{number}` — Transit ticket to track
- a CR id (`#123` / `!1` / bare number) — existing CR to work with
- A path — working directory override

## Workflow

### 1. Push and Open the CR

If no existing CR id was provided, run **`CR_CREATE`** with `target` = `main` (pass a
`title` that includes the `T-{number}` prefix if the branch name carries one). Keep
the returned id as `<id>`.

If an existing CR id was provided, fetch its details with **`CR_VIEW`** instead.

### 1.5 Decide Whether to Run Local Claude Review

Run `local-review` by default. Skip it only when an automated reviewer will post the
same comment, so the two don't duplicate each other.

```text
RUN_LOCAL_REVIEW = (AUTO_REVIEWER_DETECT == 0) ? 1 : 0
```

If `RUN_LOCAL_REVIEW=0`, skip every "Run Local Claude Review" step below — the
automated reviewer posts the comment on its own.

### 2. Review Loop

#### 2.1 Run Local Claude Review and Wait

If `RUN_LOCAL_REVIEW=1`, invoke the `local-review` agent on the CR (pass `<id>`) so
the Claude review note is posted from your local subscription instead of CI. It
reads the repo's `CLAUDE.md`, fetches the diff, and posts one comment that
`pr-review-fixer` absorbs in step 2.2.

Then wait for review input:
- **If CI exists** (`CI_STATUS` non-empty): wait up to 10 minutes, polling
  `CI_STATUS`, for checks and other reviewers.
- **If `CI_STATUS` is empty** (no CI configured): nothing to wait on — proceed once
  the local-review note is posted. Allow a brief pause only if human reviewers are
  expected.

#### 2.2 Run PR Review Fixer

Run the `/pr-review-fixer` skill to fetch unresolved threads and any CI failures,
validate them, and fix issues found.

After it completes, evaluate:
- **CLEAN**: no blockers, critical, or major issues. Minor and nitpick items are
  acceptable.
- **HAS_ISSUES**: blockers/critical/major items were fixed and pushed. Another round
  is needed.

#### 2.3 Evaluate and Repeat

- **HAS_ISSUES**: re-run from step 2.1 (wait only if CI exists).
- **CLEAN**: proceed to merge.

Cap the loop at 5 iterations. If still not clean after 5 rounds, inform the user and
stop. Do not merge. If a Transit ticket is tracked, add a comment: "Automated review
loop did not converge after 5 iterations — manual review needed."

### 3. Rebase and Merge

#### 3.1 Rebase onto Latest Main

```bash
git fetch origin main
git rebase origin/main
```

Resolve any conflicts, then `git rebase --continue`. Run the project's tests and
linter (Makefile target if present, else the project's documented commands) to
verify the rebase is clean.

#### 3.2 Push Rebased Branch

```bash
git push --force-with-lease
```

#### 3.3 Run Local Claude Review and Wait

If `RUN_LOCAL_REVIEW=1`, invoke `local-review` again so the post-rebase diff gets a
fresh note. Wait for checks only if `CI_STATUS` is non-empty (poll up to 10 min);
otherwise proceed. Then run `/pr-review-fixer` to check for new threads and CI
failures.

- **CLEAN**: proceed to merge.
- **HAS_ISSUES**: fix, push, and repeat (up to 3 iterations). If still not clean,
  inform the user and stop.

#### 3.4 Squash and Merge

Run **`CR_MERGE`** with `<id>`. If branch protection requires a green pipeline before
merge, the operation will refuse until checks pass — surface that rather than forcing
it.

### 4. Update Transit Ticket

If a Transit ticket is being tracked, move it to `done`:

```
mcp__transit__update_task_status(displayId={id}, status="done",
  comment="Merged via squash-and-merge — CR {id}", authorName="claude[bot]")
```

If no Transit ticket is tracked, skip this step.

### 5. Summary

Report the outcome:

```
CR {id} — {MERGED|FAILED}
- Review rounds: N
- Transit: T-{id} → done (or N/A)
```
