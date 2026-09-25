# Forge Adapter: GitHub (`gh`)

Implements `CONTRACT.md` for GitHub. CLI: `gh`. Terminology: CR = pull request,
`<id>` = PR number, thread = review thread, note = comment.

Commands mirror the original gh-based `local-review` agent, which is battle-tested.

## PREFLIGHT

```bash
# Detected as github when the origin host is github.com:
git remote get-url origin | grep -qi 'github\.com' && FORGE=github
# Confirm auth (stop and tell the user to run `gh auth login` if this fails):
gh auth status
```

## CR_VIEW

```bash
# With an explicit number, or omit <id> to infer from the current branch:
gh pr view <id> --json number,title,url,baseRefName,headRefName,author,body \
  --jq '{id:.number, title, url, author:.author.login,
         source_branch:.headRefName, target_branch:.baseRefName, description:.body}'
# `sha` (head commit) when needed:
gh pr view <id> --json headRefOid --jq '.headRefOid'
# Repo slug for any raw API calls:
gh repo view --json nameWithOwner --jq '.nameWithOwner'
```

If `gh pr view` with no `<id>` errors or returns nothing, the current branch is not
the head of an open PR — stop and ask the caller to pass `<id>`.

## CR_DIFF

```bash
gh pr diff <id>
```

## CR_FILES

```bash
gh pr view <id> --json files --jq '.files[].path'
```

## CR_COMMENT

```bash
gh pr comment <id> --body-file <body-file>
```

`gh` reads the body from a file directly, so no shell interpolation of the body is
needed. Do not use `gh pr review` — post a plain comment, matching what the upstream
`anthropics/claude-code-action` does.

## THREADS_FETCH

GitHub has three comment surfaces; this merges them into the contract's normalised
array. The `--jq` transform does the unification, so the workflow never sees the raw
GraphQL shape.

```bash
OWNER_REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner')
OWNER=${OWNER_REPO%/*}; REPO=${OWNER_REPO#*/}
gh api graphql -f query='
  query($owner:String!,$repo:String!,$pr:Int!){
    repository(owner:$owner,name:$repo){
      pullRequest(number:$pr){
        reviewThreads(first:100){nodes{id isResolved comments(last:1){nodes{body author{login} path line}}}}
        reviews(first:50){nodes{id body state author{login}}}
        comments(first:100){nodes{id body author{login}}}
      }
    }
  }' -f owner="$OWNER" -f repo="$REPO" -F pr=<id> --jq '
  [ (.data.repository.pullRequest.reviewThreads.nodes[]
       | .comments.nodes[-1] as $c
       | {thread_id:.id, scope:"diff", resolved:.isResolved, resolvable:true,
          author:$c.author.login, path:$c.path, line:$c.line, body:$c.body}),
    (.data.repository.pullRequest.reviews.nodes[]
       | select((.body // "") != "" and .state != "APPROVED")
       | {thread_id:.id, scope:"cr-level", resolved:false, resolvable:false,
          author:.author.login, path:null, line:null, body:.body}),
    (.data.repository.pullRequest.comments.nodes[]
       | {thread_id:.id, scope:"cr-level", resolved:false, resolvable:false,
          author:.author.login, path:null, line:null, body:.body}) ]'
```

## THREAD_RESOLVE

Only review-thread ids (`scope: "diff"`) are resolvable; CR-level review/issue
comments are not — skip them.

```bash
gh api graphql -f query='
  mutation($id:ID!){ resolveReviewThread(input:{threadId:$id}){ thread{ isResolved } } }
' -f id=<thread_id>
```

## THREAD_REPLY

Only review threads (`scope: "diff"`, GraphQL thread ids from `THREADS_FETCH`)
support in-thread replies. CR-level review bodies and issue comments are flat —
for those, fall back to `CR_COMMENT` quoting the original instead.

```bash
gh api graphql -f query='
  mutation($id:ID!,$body:String!){
    addPullRequestReviewThreadReply(input:{pullRequestReviewThreadId:$id, body:$body}){
      comment { id }
    }
  }' -f id=<thread_id> -f body="$(cat <body-file>)"
```

## CR_NOTES_LIST

```bash
gh pr view <id> --json comments --jq '[.comments[] | {id, author:.author.login, body}]'
```

## CI_STATUS

`gh pr checks` exits non-zero when checks are failing/pending, so guard with `|| true`.
An empty array means no checks are configured for the CR.

```bash
gh pr checks <id> --json name,bucket --jq '
  [ .[] | {name, state:(.bucket
      | if .=="pass" then "success"
        elif .=="fail" then "failed"
        elif .=="pending" then "running"
        elif .=="skipping" then "skipped"
        else "other" end)} ]' 2>/dev/null || echo '[]'
```

## CI_JOB_LOG

Identifier plumbing differs from GitLab — resolve the failed run from the CR's
branch, then dump its failed-step logs:

```bash
BRANCH=$(gh pr view <id> --json headRefName --jq '.headRefName')
RUN_ID=$(gh run list --branch "$BRANCH" --json databaseId,conclusion \
  --jq 'map(select(.conclusion=="failure"))[0].databaseId')
[ -n "$RUN_ID" ] && gh run view "$RUN_ID" --log-failed
```

The `job` input (a check name from `CI_STATUS`) is informational here; GitHub groups
logs by run, not by individual check name.

## CR_CREATE

```bash
git push -u origin HEAD
# Title/body from commits:
gh pr create --fill --base <target>
# …or with an explicit title (e.g. carrying a T-123 prefix):
gh pr create --base <target> --title "<title>" --body "<body>"
# Return the new PR number:
gh pr view --json number --jq '.number'
```

GitHub deletes the source branch via the merge flag (`CR_MERGE`), not at creation
time, so nothing extra is needed here.

## AUTO_REVIEWER_DETECT

An active automated reviewer = a workflow file GitHub will execute that references
the upstream `anthropics/claude-code-action`. A file renamed to `*.yml.disabled`,
`.bak`, etc. will not run.

```bash
ACTIVE=$(find .github/workflows -maxdepth 1 -type f \( -name '*.yml' -o -name '*.yaml' \) 2>/dev/null)
if [ -n "$ACTIVE" ] && printf '%s\n' "$ACTIVE" | xargs grep -lq 'anthropics/claude-code-action' 2>/dev/null; then
  echo 1
else
  echo 0
fi
```

## CR_MERGE

```bash
gh pr merge <id> --squash --delete-branch
```
