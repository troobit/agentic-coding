# Forge Adapter: GitLab (`glab`)

Implements `CONTRACT.md` for GitLab (including self-managed instances such as
`gitlab.mantelgroup.com.au`). CLI: `glab`. Terminology: CR = merge request,
`<id>` = MR IID, thread = discussion, note = note.

`glab api` accepts the `:fullpath` placeholder, which expands to the current
repository — use it instead of hand-encoding the project path.

## PREFLIGHT

```bash
# Detected as gitlab when origin is not github.com (and glab knows the host):
git remote get-url origin | grep -qi 'github\.com' || FORGE=gitlab
# Confirm auth (stop and tell the user to run
# `glab auth login --hostname <host>` if this fails):
glab auth status
```

Never fall back to `gh` on a GitLab repo.

## CR_VIEW

```bash
# With an explicit IID, or omit <id> to infer from the current branch:
glab mr view <id> -F json --jq '{id:.iid, title, url:.web_url,
  author:.author.username, source_branch, target_branch, sha, description}'
```

If `glab mr view` with no `<id>` errors or returns nothing, the current branch is
not the source of an open MR — stop and ask the caller to pass `<id>`. (Note: glab
resolves by the *local* branch name; if it differs from the MR's source branch,
pass `<id>` explicitly.)

## CR_DIFF

```bash
glab mr diff <id>
```

## CR_FILES

```bash
glab api "projects/:fullpath/merge_requests/<id>/diffs" --paginate | jq -r '.[].new_path'
```

## CR_COMMENT

`glab mr note create` takes the body as a `-m` string (no `--body-file`), so read
the file into the argument:

```bash
glab mr note create <id> -m "$(cat <body-file>)"
```

`glab mr note create` is marked EXPERIMENTAL in glab. If it fails, fall back to the
REST API:

```bash
glab api --method POST "projects/:fullpath/merge_requests/<id>/notes" \
  --field "body=$(cat <body-file>)"
```

Do not use `glab mr approve` — post a plain note only.

## THREADS_FETCH

GitLab has a single discussions feed; one element per discussion, using its last
note. System notes (assignment, labels) are dropped. Diff-anchored discussions carry
a `position`; CR-level ones do not.

```bash
glab api "projects/:fullpath/merge_requests/<id>/discussions" --paginate | jq -c '
  [ .[] | .notes[-1] as $n
    | select(($n.system // false) == false)
    | {thread_id: .id,
       scope: (if $n.position then "diff" else "cr-level" end),
       resolved: ($n.resolved // false),
       resolvable: ($n.resolvable // false),
       author: $n.author.username,
       path: $n.position.new_path,
       line: $n.position.new_line,
       body: $n.body} ]'
```

## THREAD_RESOLVE

```bash
glab mr note resolve <thread_id> <id>
# fallback if the EXPERIMENTAL subcommand misbehaves:
glab api --method PUT \
  "projects/:fullpath/merge_requests/<id>/discussions/<thread_id>" --field resolved=true
```

## THREAD_REPLY

Append a note to an existing discussion. This endpoint also accepts the discussion
id of an *individual note* (e.g. a plain `glab mr note create` comment) and converts
it into a thread — after which the discussion is resolvable via `THREAD_RESOLVE`.

```bash
glab api --method POST \
  "projects/:fullpath/merge_requests/<id>/discussions/<thread_id>/notes" \
  --field "body=$(cat <body-file>)"
```

## CR_NOTES_LIST

```bash
glab api "projects/:fullpath/merge_requests/<id>/notes" --paginate \
  | jq -c '[ .[] | {id, author: .author.username, body} ]'
```

## CI_STATUS

Resolve the MR's head pipeline; emit `[]` when there is none (no `.gitlab-ci.yml`,
or no pipeline yet).

```bash
PID=$(glab mr view <id> -F json --jq '.head_pipeline.id // empty')
if [ -z "$PID" ]; then echo '[]'; else
  glab api "projects/:fullpath/pipelines/${PID}/jobs" | jq -c '
    [ .[] | {name, state:(.status
        | if .=="success" then "success"
          elif .=="failed" then "failed"
          elif (.=="running" or .=="pending") then "running"
          elif (.=="skipped" or .=="manual" or .=="canceled") then "skipped"
          else "other" end)} ]'
fi
```

## CI_JOB_LOG

GitLab traces by job name or id directly:

```bash
glab ci trace <job>
```

Here `<job>` is the failed entry's `name` from `CI_STATUS` (or its numeric job id).

## CR_CREATE

`glab mr create --fill` pushes the current branch itself (sets `push=true`), so no
separate `git push` is required.

```bash
# Title/body from commits; --remove-source-branch sets delete-on-merge at creation:
glab mr create --fill --yes --target-branch <target> --remove-source-branch
# …or with an explicit title (e.g. carrying a T-123 prefix):
glab mr create --yes --target-branch <target> --remove-source-branch \
  --title "<title>" --description "<body>"
# Return the new MR IID:
glab mr view -F json --jq '.iid'
```

## AUTO_REVIEWER_DETECT

An active automated reviewer = a `.gitlab-ci.yml` job that posts a Claude review.
Look for an obvious marker (a job/script referencing `claude` review or
`local-review`). No `.gitlab-ci.yml`, or no such job, means none will run.

```bash
if [ -f .gitlab-ci.yml ] && grep -qiE 'claude.*review|local-review' .gitlab-ci.yml; then
  echo 1
else
  echo 0
fi
```

## CR_MERGE

```bash
glab mr merge <id> --squash --remove-source-branch --yes
```
