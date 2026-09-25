# Forge Adapter Contract

Shared operation contract for the forge-aware review tooling (`local-review` agent,
and — once converted — the `pr-pilot` and `pr-review-fixer` skills). The workflow
files describe *what* to do in forge-neutral terms and call the operations named
here. Each forge adapter (`github.md`, `gitlab.md`) implements those same operation
names with concrete commands.

**Why this exists:** GitHub (`gh`) and GitLab (`glab`) differ only in a small,
bounded set of operations. Keeping the workflow in one place and the per-forge
commands in adapters avoids maintaining two near-identical copies that drift.

## How a workflow uses this

1. Run **`PREFLIGHT`** to determine `FORGE` (`github` or `gitlab`).
2. Read the matching adapter: `~/.claude/forge-adapters/<FORGE>.md`.
3. Wherever the workflow says "perform `OPERATION` (see adapter)", run the command
   from that adapter's `## OPERATION` section, substituting the inputs.

Do **not** guess commands. If an operation has no section in the selected adapter,
stop and report it — never improvise a `gh`/`glab` invocation.

## Glossary (forge-neutral terms)

| Neutral term | GitHub | GitLab |
|---|---|---|
| **CR** (change request) | pull request (PR) | merge request (MR) |
| **CR id** | PR number (`123`) | MR IID (`!1` / `1`) |
| **thread** | review thread | discussion |
| **note** | comment | note |
| **pipeline/checks** | checks / Actions run | pipeline / jobs |
| **CLI** | `gh` | `glab` |

The CR's own integer identifier is referred to as `<id>` below; how it prints
(`#123` vs `!1`) is cosmetic.

## Operations

### PREFLIGHT  *(implemented)*

Determine the forge and confirm the CLI is authenticated.

- **Inputs:** none.
- **Output:** `FORGE` ∈ {`github`, `gitlab`}. If the CLI for the detected forge is
  not authenticated, **stop** and tell the user how to authenticate.
- **Detection rule:** inspect `git remote get-url origin`. Host `github.com`
  ⇒ `github`. Any other host that the forge CLI recognises (e.g. a self-managed
  GitLab) ⇒ `gitlab`. When ambiguous, prefer the CLI that reports an authenticated
  session for the remote's host.

### CR_VIEW  *(implemented)*

Resolve the CR and return its metadata.

- **Inputs:** `<id>` (optional). When omitted, resolve from the current branch.
- **Output:** a JSON object the workflow can read fields from: `id`, `title`,
  `url`, `author`, `source_branch`, `target_branch`, `sha`, `description`.
- **Notes:** when `<id>` is omitted, resolution works only if the current branch is
  the source of an open CR. On failure, stop and ask the caller to pass `<id>`.

### CR_DIFF  *(implemented)*

Return the full unified diff of the CR.

- **Inputs:** `<id>`.
- **Output:** unified diff text on stdout.

### CR_FILES  *(implemented)*

List the paths of files changed in the CR (for prioritising a large diff).

- **Inputs:** `<id>`.
- **Output:** one changed-file path per line on stdout.

### CR_COMMENT  *(implemented)*

Post a single note on the CR.

- **Inputs:** `<id>`, `<body-file>` (path to a file containing the Markdown body).
- **Output:** none (side effect: one note posted). The body is supplied verbatim —
  any sentinel marker is the caller's responsibility, not the adapter's.
- **Notes:** there is no bot identity on either forge here; notes post under the
  authenticated user. Callers rely on an in-body HTML sentinel for later dedup,
  never on author identity.

### THREADS_FETCH  *(implemented)*

Fetch the CR's review threads/discussions, normalised to one element per thread.

- **Inputs:** `<id>`.
- **Output:** a JSON array; each element is the **last note** of one thread:
  ```jsonc
  {
    "thread_id":  "…",        // opaque id; pass to THREAD_RESOLVE
    "scope":      "diff" | "cr-level",  // diff-anchored vs CR-level
    "resolved":   false,        // already resolved?
    "resolvable": true,         // can it be resolved at all?
    "author":     "username",
    "path":       "src/x.py",   // diff scope only, else null
    "line":       42,            // diff scope only, else null
    "body":       "…"           // the last note's Markdown body
  }
  ```
- **Notes:** the adapter is responsible for unifying the forge's surfaces into this
  one shape. GitHub has three (review threads, review bodies, issue comments) and
  the adapter merges them; GitLab has one (discussions). System/automated notes
  (assignment, labels) are excluded by the adapter. The workflow decides what is
  *actionable* and whether a body is a Claude review (by sentinel) — the adapter
  only normalises.

### THREAD_RESOLVE  *(implemented)*

Mark a thread/discussion resolved.

- **Inputs:** `thread_id` (from `THREADS_FETCH`).
- **Output:** none (side effect). Only call for elements with `resolvable: true`
  (typically `scope: "diff"`); resolving a non-resolvable CR-level item is a no-op
  or error — skip those.

### THREAD_REPLY  *(implemented)*

Post a reply **inside** an existing thread/discussion (not a new CR-level note).

- **Inputs:** `<id>`, `thread_id` (from `THREADS_FETCH`), `<body-file>` (path to a
  file containing the Markdown body).
- **Output:** none (side effect: one note appended to the thread).
- **Notes:** on GitLab this also works on an individual (non-thread) note — the
  reply converts it into a thread, which then becomes resolvable via
  `THREAD_RESOLVE`. On GitHub only review threads (`scope: "diff"`) support
  in-thread replies; CR-level comments are flat — fall back to `CR_COMMENT` and
  quote the original.

### CR_NOTES_LIST  *(implemented)*

List CR-level notes, for counting prior overview comments by sentinel.

- **Inputs:** `<id>`.
- **Output:** a JSON array of `{ "id": …, "author": …, "body": … }`. The workflow
  counts elements whose `body` contains its iteration sentinel.

### CI_STATUS  *(implemented)*

Pipeline/checks status for the CR's head.

- **Inputs:** `<id>`.
- **Output:** a JSON array of `{ "name": …, "state": … }` where `state` is
  normalised to one of `success` | `failed` | `running` | `skipped` | `other`.
  **An empty array `[]` means no CI is configured** — the workflow treats that as
  "nothing to wait on", not a failure.

### CI_JOB_LOG  *(implemented)*

Fetch the failing log for a CI job.

- **Inputs:** `<id>` (the CR) and `job` (a failed entry's `name` from `CI_STATUS`).
- **Output:** failing-log text on stdout. Best-effort; exact identifier plumbing is
  forge-specific (see each adapter). Only invoked when `CI_STATUS` reports failures.

### CR_CREATE  *(implemented)*

Push the current branch and open a CR, returning its id.

- **Inputs:** `target` (target branch, e.g. `main`); `title`/`body` optional (when
  omitted, derive from commits). The adapter pushes the branch as part of this op.
- **Output:** the new CR `<id>` on stdout.
- **Notes:** configures the CR to delete its source branch on merge. If a `title` is
  given (e.g. carrying a `T-123` ticket prefix), it overrides the commit-derived one.

### AUTO_REVIEWER_DETECT  *(implemented)*

Report whether an automated CI/Action reviewer is already configured to post the
same Claude review comment (so the workflow can avoid duplicating it locally).

- **Inputs:** none.
- **Output:** `1` if an automated reviewer will run for this CR, else `0`.
- **Notes:** detection is by inspecting the repo's CI config for a job/workflow that
  posts the review (see each adapter). When `1`, the caller skips its local review
  step; when `0`, it runs `local-review` to fill the gap.

### CR_MERGE  *(implemented)*

Squash-merge the CR and delete its source branch.

- **Inputs:** `<id>`.
- **Output:** none (side effect). If branch protection requires a green pipeline,
  the merge will be refused until checks pass — surface that to the user rather than
  forcing it.

---

All contract operations are now implemented in both adapters.

## Authoring rules for adapters

- One `## OPERATION` heading per implemented operation, matching the names above.
- Give the exact command(s). Use `<id>` and `<body-file>` as the placeholder names.
- Document the output shape only where it differs from the contract (e.g. GitLab's
  single discussions model vs GitHub's three comment surfaces — relevant for
  `THREADS_FETCH`).
- Never embed workflow policy (loop caps, validation criteria) in an adapter — that
  belongs in the workflow file.
