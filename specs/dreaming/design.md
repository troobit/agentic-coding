# Design: Dreaming

## Overview

Dreaming is a small Python program (`dream`) that runs a dream as a resumable list of model calls. Each call is a narrow role (reader, reviewer, researcher, author) that returns structured output. The program owns ordering, budgets, state and git; the models own judgement; what to look for lives in plain files the user edits (lenses, role prompts, schemas). Sessions are read through apsis, steps and their order live in SQLite (with a rune-format plan rendered from them for reading), and model calls go straight to `claude`, `codex` or LM Studio. An observation is a verified quote from one session entry; a pattern is a persistent identifier grouping observations that describe the same thing; a knowledge item is a revisable interpretation of patterns (preference, lesson, workflow pattern or learning opportunity). Requirements are in [requirements.md](requirements.md); decisions in [decision_log.md](decision_log.md) (Decisions 5, 9–11).

## Architecture

```
dream start ─▶ lock ─▶ snapshot config + instructions ─▶ select sessions (apsis listing)
            ─▶ insert Read/Review steps ─▶ loop: next ready step ─▶ call ─▶ store raw output
               ─▶ one transaction: apply results + insert follow-up steps + mark step done
            ─▶ finally: report (HTML) ─▶ exit code
```

| Concern | Provided by | Custom code |
|---|---|---|
| Session discovery and parsing | `apsis --all-projects --list -f shared-json`, `apsis <id> -s <source> -f shared-json` | Selection, dedupe by `thread_id`, splitting |
| Readable plan | `rune` file format, rendered from the `steps` table | `plan.py` (renderer, read-only view) |
| Model calls and tools | `claude`, `codex` CLIs; LM Studio HTTP for tool-free roles | Backend adapters, per-call config, budget |
| Run record, lock, snapshot, exit codes | screw's conventions, reimplemented without importing screw | `run.py` |
| Reflection concepts | OpenClaw (adapted, no code) | `knowledge.py`, `review.py` |
| Report styling | CSS and page shell of the `review_html` module in agentic-coding `scripts/`, vendored once into `report/` | `report/` |

### Placement

The program, its tests, the instruction set, the `dream` skill and this spec (`specs/dreaming/`) live in one repository, developed on a branch named `dreaming`. It is an installable package (Python 3.12+, uv, ruff, pytest, as in screw) with its own Makefile (`make test`, `make lint`, `make install`). The user's data lives under `~/.dreaming/` (override `DREAMING_HOME`), mode 0700, checked at start to be outside every git repository (6.4).

```
(repository root)
  pyproject.toml  Makefile
  src/dreaming/
    cli.py api.py config.py run.py steps.py plan.py store.py
    sessions.py          # apsis calls, dedupe, split, attribution (2.x)
    backends/            # claude.py codex.py lmstudio.py probe.py
    roles.py budget.py observe.py knowledge.py review.py inventory.py
    adopt.py scan.py     # git worktrees, checks, merge, deploy, public scan
    report/
  instructions/          # the editable instruction set
    lenses.toml  roles/{reader,reviewer,researcher,author,replayer}.md  schemas/*.json  config.example.toml
  skills/dream/SKILL.md  # start, dry-run, open report (initial integration)
  specs/dreaming/        # requirements, design, decisions, tasks
  tests/
```

The skill reaches the program only through the installed `dream` command and `dream api`, so it works from any directory; other harness repositories install it by copying `skills/dream/`.

### Versioned installs (7.3)

`make install-dreaming` installs the package into `~/.dreaming/versions/<revision>/` and repoints `~/.dreaming/current`. `~/.local/bin/dream` is a launcher that runs `current` for a new run and the run's recorded revision on resume. Adoption of dreaming's own code deploys a new version for the next run; the running or resumed run keeps its revision. A version directory is deleted only when no unfinished run records it. Schema migrations are additive within a major version and run only when no unfinished run exists; otherwise the newer command refuses with `migration_blocked` naming the run.

### Instruction set and snapshot (7.1, 7.3)

At start, `instructions/` is read from the default branch of the configured instruction repository (`git show <default>:instructions/...`, not the working tree) and copied with the config into `runs/<id>/snapshot/`. The names list for the public scan (9.12) is read from a configured path outside every repository and is never copied into a repository or the report.

### OpenClaw and reuse (12.1–12.3)

Inspected: `openclaw/openclaw` at `9bf3e79c823a51b098ab892d2f8f505931cd5671` (2026-11-14), MIT, © OpenClaw Foundation. Its dreaming is the `extensions/memory-core` plugin (TypeScript), bound to its gateway scheduler, SQLite plugin state and `MEMORY.md`. No code is reused: the coupling means reuse would carry the gateway and a second runtime. Concepts adopted, each re-implemented in `knowledge.py`/`review.py`, with no copied source and so no attribution duty beyond this record:

| OpenClaw concept | Dreaming equivalent |
|---|---|
| Staged light/REM/deep phases; only deep writes durable memory | Readers write observations only; the reviewer proposes revisions; the program applies promotion rules (13.x) |
| Score, recall-count, unique-query gates | Distinct-session threshold (4.5) and ranking (11.3) |
| Taint gate: drop `untrusted`/`system` provenance | Non-interactive attribution (2.9, Decision 8) |
| Interactive sessions only; strip recalled context | Recalled knowledge is stripped from evidence by 13.6 |
| Preimage stored before a rewrite; diff highlights in the diary | Revisions are append-only history; the report shows diffs |
| Model returns operations, not prose | Reviewer returns revision operations against knowledge identifiers |

Update duty: none; revisit this table only when the user asks.

### Prior art beyond OpenClaw

Sources checked 2026-11-14 (papers by their abstract pages; products by their documentation). The design follows what recurs across them and drops what they report as harmful.

| Source | Finding used | Where it lands |
|---|---|---|
| Mukta, "Learning while you sleep: Beyond memory to dreaming" (AI Native DevCon, 2026-06; youtube.com/watch?v=tTcxVv8HHNw) | Out-of-band batch consolidation by sub-agents over transcripts and the memory store, proposals with example transcripts and prevalence stats, versioned writes recording the source session, optimistic concurrency by hash | Roles; revisions carry `actor` and `base_version` |
| Liao et al., "Experience Graphs" (arXiv:2606.29823, CIDR'27) | Durable state with disposable workers; heavier retrieval injection reduced failures but anchored the agent on fewer strategies | Steps table; recall note on injection |
| "Useful Memories Become Faulty When Continuously Updated by LLMs" (arXiv:2605.12978) | LLM consolidation can leave an agent worse than no memory; raw episodes beat forced consolidation | Knowledge stays derived from raw redacted evidence; revisions are append-only; recall returns the quotes |
| "Manufactured Confidence" (arXiv:2606.29279) | Consolidation turns hedged remarks into confident facts; a verification tag was ignored | `modality` on observations; recall shows the quote |
| MemForm (arXiv:2610.14431); MemSecBench (arXiv:2607.27080); MINJA (arXiv:2503.03704) | Consolidation order changes outcomes; poisoned memory persists and is hard to repair | Deterministic review order; revision cap; evidence-addressed dismissal |
| ACE (arXiv:2510.04618); AutoManual (arXiv:2405.16247) | Incremental delta edits avoid context collapse; rules that cite supporting and counter cases hallucinate less | Author emits id-keyed edits with both cases |
| GEPA (arXiv:2507.19457); Darwin Gödel Machine (arXiv:2505.22954) | Self-modification is validated against evaluations, not only static checks | See Risks and Assumptions (replay check) |
| ExpeL (2308.10144), Agent Workflow Memory (2409.07429), Generative Agents (2304.03442), Reflexion (2303.11366), Sleep-time Compute (2504.13171) | Insight distillation, workflow induction, reflection and offline precomputation | Already the shape of the design |
| LongMemEval (2410.10813), MemoryAgentBench (2507.05257) | Test competencies: knowledge update, abstention, selective forgetting, test-time learning | Testing Strategy fixtures |
| Anthropic Managed Agents Dreams (research preview), Letta sleep-time agents, Codex memories, Cognee `improve()`, Mem0 | Staged output before promotion; model review of proposed updates; excluding externally influenced chats; flagging conflicts instead of rewriting; reconcile-by-LLM judged lossy | Candidate status before active; `contested`; append-only history |

Not adopted: embeddings and graph stores (Mem0, Zep/Graphiti, A-MEM, HippoRAG), because scoped SQLite retrieval suffices at one user's scale; bi-temporal validity (when a fact stopped being true), because revisions already carry a latest supporting date and supersession; scheduled or idle triggers (Q3).

## Components and Interfaces

### Roles and calls (4.x, 5.x)

```python
class Backend(Protocol):
    name: str; context_tokens: int; supports_tools: bool
    def probe(self) -> ProbeResult: ...          # version, tools, isolation (5.5)
    def call(self, role: str, prompt: str, schema: dict, tools: list[str]) -> CallResult: ...

@dataclass
class CallResult:
    output: dict; tokens_in: int; tokens_out: int; usage_estimated: bool
    session_ref: str          # harness session id, or LM Studio thread id == run id (5.8)
```

- One retry policy for every call: on transport failure or schema-invalid output, retry once on the same backend. Two transport failures mark the backend unavailable for the run and the call moves to the role's next backend (which gets its own single retry; not nested). Two schema failures mark the input failed (4.7) with no backend change, except that `breaker_k` consecutive schema failures on one backend mark that backend unavailable for the run, and inputs that failed on it stay eligible for the next backend. A harness usage-limit error counts as a transport failure. Every call has a timeout and is killed as a process group.
- The replayer role (9.16) runs with an empty tool list and no network, and gets only the instruction under replay; its output is judged by a reviewer-role call.
- A `calls` row (task key, attempt, backend, harness session id where the harness accepts one, e.g. Claude `--session-id`) is written before the call; the raw output is written to it as soon as the call returns. Sessions whose working directory is under `DREAMING_HOME` count as dream sessions for 1.5 even if a row is missing.
- Tools: `mcp/servers.json` is filtered by the role's allowlist into a per-call config, and each call's devtools server is started with `ENABLE_ADDITIONAL_TOOLS` omitting `codex-agent` and `gemini-agent`, so the model never sees agent-launching tools regardless of harness.
- Claude: isolation flags in order of preference `--safe-mode` (keeps login; disables CLAUDE.md, skills, plugins, hooks, MCP and agents), otherwise `--setting-sources "" --strict-mcp-config --disable-slash-commands` with `CLAUDE_CODE_DISABLE_CLAUDE_MDS=1` and `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`; an explicit tools list without `Agent`; a permission mode that never prompts. The call's working directory is under `DREAMING_HOME`, so no parent-directory instruction file loads (probed).
- Codex: `codex exec --json` with the skills block and user instructions suppressed (`-c skills.include_instructions=false`; an empty `CODEX_HOME` only if the probe shows auth and apsis visibility both survive). Its JSON event stream is saved under `runs/<id>/codex/` and registered with apsis through `--codex-exec-dir` alongside the user's existing directories. If the probe shows an agent-launch tool (`spawn_agent`) cannot be removed, the adapter kills the call on any agent-launch event and records it as a failed call.
- Transcripts are never hidden from apsis (5.8). Direct LM Studio calls put `client_metadata.thread_id` first in the request body so the server log keeps it when it truncates long bodies.
- A dry run probes with `--version`, config checks and the cached result of the last real probe (keyed by backend version) and labels each as `cached` or `unprobed`; the call-based probe runs only at a real start and counts against the budget (1.7, 5.5).
- The author receives the target repository's `CLAUDE.md`/`AGENTS.md` as counted input; harnesses never load it themselves (4.4).
- A harness using LM Studio gets its role's allowed devtools tools from the same filtered config (5.7).
- Usage missing from a harness is estimated as `ceil(utf8 bytes / 4)` over prompt and output, and `usage_estimated` is set; budgets count the estimate (1.2).
- Inputs are sized for the smallest `context_tokens` in the role's fallback list (5.2). On a role's backend change at resume, the remaining inputs are re-sized (5.4).

### Steps and plan view (`steps.py`, `plan.py`)

The `steps` table is the only record of what a dream will do and has done: `(run, key, phase, depends_on, state, attempts, input_ref)`, where `key` is a stable identifier the runner assigns (for example `read:<batch>`, `research:<question hash>`, `author:<candidate>`, `adopt:<group>`) and `state` is `pending|running|done|failed|skipped`. Phases: Read (one step per session batch), Review, Research (one per question), Author (one per candidate; begins with a verify action, see Review), Adopt (one per linked group of repositories, unlinked repositories being groups of one). Review depends on all Read steps. The next step is the first `pending` one whose dependencies are `done`. The report is not a step: it runs in the exit path so a budget-exhausted or failed run still produces it (10.1). Hitting a limit or an interrupt is checked between steps and never kills a running check, merge or deploy.

Contract: a step's follow-up steps are inserted in the same SQLite transaction that applies its results and marks it `done`. The raw model output is stored on the `calls` row as soon as the call returns; on resume, a step with stored raw output and no `done` state applies that output without calling a model, so a crash cannot produce a second, different answer. Re-sizing on resume (5.4) rewrites only `pending` Read steps. SQLite runs in WAL mode with a busy timeout, because `dream api` writes (feedback, registration) while a dream runs.

`dream status --plan` renders the steps as a rune-format file `runs/<id>/tasks-dream.md` for reading with `rune list`; it is never read back and never edited.

### Lock

The `dream start` parent takes an `flock` on `~/.dreaming/lock`, inserts the run row and hands the held descriptor to the detached child, so the kernel releases it when the child dies; there is no stale-pid logic and no start race (1.6). The run records the child's process group, and reclaiming an interrupted run kills any survivor of that group first.

### Selection and reading (`sessions.py`, 1.x–3.x)

- Listing comes from apsis; rows already read (store: session id, lens versions, entry count read) are dropped unless 1.4 applies. Growth under unchanged lens versions selects only entries after the recorded count (2.5).
- Sessions of the dream in progress (calls table `session_ref`, LM Studio `thread_id == run id`) and sessions modified inside the recent window are excluded (1.5). Sessions from earlier dreams are tagged `subject=dreaming`; their observations feed only the dream-behaviour lens and never count as evidence about the sessions those dreams processed.
- Duplicates are matched by `thread_id` from the session document; the harness copy supplies content, the LM Studio log supplies server metadata, or truncated content when it is the only copy (2.4). Unattributed server warnings go to the report only.
- Attribution (2.2, 2.3, 2.9): local/cloud, domain, interactivity come from config rules applied by the program. Entries in non-interactive or registered sessions are presented to the reader with role `tool`, and observations of kind `user_statement` on such entries are rejected by the program.
- Splitting (2.6): consecutive entry ranges that fit the reader's context after the prompt; an entry larger than that is cut with an explicit truncation marker.
- Reader input per batch: session parts with entry ids. Reader output: observations `{entry_id, quote, kind, modality, outcome, lens, pattern_key}`, where `modality` is `asserted|hedged|tentative` as the source text states it. The program, not the model, verifies the quote against the entry text (whitespace-normalised) before redaction and rejects mismatches (6.2).

### Review and knowledge (`review.py`, `knowledge.py`, 4.x, 11.x, 13.x)

A deterministic pass runs before review: it normalises each observation's `pattern_key` (case, whitespace, lens prefix) and clusters new observations by key and by the lens's scope. The reviewer receives the new clusters plus the nearest existing pattern summaries, and `assign` or `merge` operations return persistent pattern ids; only the program creates a new id. A share of the reviewer's context (`new_cluster_share`) is reserved for new clusters. The reviewer receives per-pattern summaries (counts, distinct sessions and projects, last date, status, evidence ids with short redacted quotes, earlier changes and their before/after counts, run records of earlier dreams), never transcripts. Existing-pattern summaries are ordered by the ranking below and included until the remaining context is full; the remainder appears as a count per lens. Each pattern records `last_reviewed_run`, and ranking boosts patterns unreviewed for `boost_after_dreams` dreams so none is starved. It returns operations: assign observations to patterns, create/revise/supersede/contest/dismiss knowledge items, propose candidate changes, ask research questions. The program validates each operation against the rules below and applies it or records it as rejected with the reason.

Rules enforced by the program:
- Promotion: inferred item → active only with ≥ `min_sessions` distinct sessions (4.5; one session per interaction, 13.6); "approach worked" additionally needs a user- or check-confirmed success in scope (13.3); explicit user statements apply within scope at once.
- Scope: `{domains, projects, workflows, global: bool, unresolved: bool}`; items with `unresolved` never match a query (13.2). Conflicts within a scope mark `contested`, unless an explicit user correction exists, which supersedes and is never overridden by inferred evidence (13.4).
- Review is deterministic: observations and clusters are sorted by (date, evidence id) before the reviewer sees them, so input order never changes the result. Revisions cite the observations they rest on and never replace them; no knowledge item exists without evidence ids.
- Revision cap: a single run may supersede or dismiss at most `max_revision_fraction` of the active items in one scope; operations beyond that are recorded as `candidate` with the reason and reviewed next run.
- Optimistic versions: each item carries a `version`; reviewer operations and feedback name the version they read, and a mismatch is rejected and re-queued, so a mid-run correction is never overwritten.
- Dismissal addresses evidence: `knowledge.feedback` can dismiss an item and mark its supporting observation ids `excluded`, so they no longer count toward any pattern (13.5).
- The reviewer may also merge duplicate items (`merge_items`) and must re-validate each active item in scope whose latest support is older than `revalidate_after_days`, recording `confirmed` or `contested` (11.7).
- Equivalent items: the reviewer names an existing identifier to revise; a new item whose normalised summary equals a dismissed item's in the same scope is rejected (13.9, 13.5).
- Ranking (11.3): `w_sessions·distinct_sessions + w_recency·2^(-age_days/half_life_days) + w_projects·distinct_projects`, weights and `half_life_days` in config, ties broken by id; the position and the three signals are stored with the candidate.
- Before authoring (11.5), the Author step's first action re-checks that the cited evidence is still available and supports the candidate against the current files; failure defers the candidate with a reason. Rate for 11.2 is `observations of the pattern / sessions read in its lens scope`; a pattern at or above its pre-change rate after `recurrence_sessions` later sessions becomes a candidate again until `max_changes_per_pattern`.
- Entries a registration marks as quoting the user keep role `user` in reader input even in non-interactive sessions (2.9).
- Candidates from file inspection (broken references) cite repository, revision, path, location and skip the session threshold (4.5).

### Retrieval and operations (`api.py`, 14.x)

`dream api` reads one JSON request on stdin and writes one JSON response; every message carries `{"dreaming_api": 1, "op": ...}`. Ops: `dream.start|status|resume|discard|report`, `knowledge.recall|search|get|feedback|export|import`, `session.register|forget|restore`. Responses carry `ok`, stable `code` on error (`incompatible_version`, `not_found`, `already_running`, `invalid_scope`), and ids. `dream.start` launches the run as a detached process (new session) and returns the run id (1.1).

- `recall` / `search` filtering: status `active` only, unless `include` lists others. An item applies when every dimension it constrains (domain, project, workflow) is supplied by the query and matches; a project maps to its domain via config. Global items always apply; unresolved items never.
- Ordering within the limit: scope specificity (workflow, project, domain, global), confidence (high, medium, low), latest supporting date descending, then id. Items are added in that order until the next item would exceed the limit; the response states `estimator: "utf8_bytes/4"`, `estimated_tokens`, and `omitted_count`.
- Items under reassessment carry `pending_reassessment: true` (2.10). Each evidence reference in a response carries the redacted quote (truncated to `quote_chars`) and its `modality`, so a consumer sees a hedge as a hedge. Delivering more items does not make an agent better; the default `limit` is small, and feedback marking revisions `cited` or `present_only` lets a later dream compare outcomes by how much was injected.
- Confidence is `low|medium|high` plus a free-text basis; it is assigned by the reviewer from stated rules (distinct sessions, confirmed outcomes, contradictions) and checked by the program for monotonic consistency with those counts.
- Feedback is keyed by the caller's feedback id (repeat = no-op) and stores revisions marked `cited` or `present_only`, the outcome basis, and the run or session reference (14.5). `session.register` is keyed by (tool, run reference, session) and is idempotent; a late registration reclassifies that session's prompts and flags affected items for reassessment (2.10).
- Export/import: a single JSON document `{"kind": "dreaming-export", "schema_version": 1, ...}` with items, revisions, redacted observations, feedback, dispositions and source-availability markers. Import upserts by identifier, so a second import changes nothing; imported items keep their stated status and evidence, are marked `imported`, and do not count toward promotion thresholds; an unknown major version returns `incompatible_version`.

### Forgetting a session (`knowledge.py`, 2.11)

`session.forget` sets the `forgotten` flag on every source copy matched by `thread_id` and, in one transaction, marks every knowledge item whose supporting evidence includes the session `pending_reassessment` and queues it for the next in-scope dream. Observations stay stored. All queries that count support, rank patterns, compute rates (11.1) or select replay sessions filter on `forgotten = 0`; retrieval drops evidence references from forgotten sessions; selection and `session.register` reject them with `state: "forgotten"`. A running dream re-reads the flag before each call, so the exclusion takes effect before its next call; adoptions already merged are not touched. Items whose remaining support fails the promotion rules (4.5, 13.3) are withheld from default retrieval and from adoption at once, not at the next reassessment. The forgotten session's observations and run-record entries are never passed to any role, and dream call sessions whose input contained them are marked excluded under 1.5. `session.restore` clears the flag and re-queues the same items. Forgetting never deletes stored data (non-goal). Both are no-ops when already in that state, and an unknown id returns `not_found`.

### Currency review (`review.py`, 16.x)

A currency dream is a run of kind `currency` with no Read phase. Its steps are Research (one per configured target) and Author (one per candidate), then the usual Adopt step limited to committing the branch. The researcher gets read, web search and fetch only, within the token and time budget and a `max_sources` cap. Fetched pages are stored, and reach roles only inside delimited data fields declared as data in the role prompt. A finding becomes a candidate only when at least `currency_min_sources` sources on distinct registrable domains, sharing no relied-on passage, support it and the program confirms each relied-on passage appears verbatim in the stored fetched text; otherwise it is retained as a currency note. A finding reuses the identifier of an equivalent finding for the same target (the reviewer names it, as for knowledge items, 13.9); a dismissed finding, or one whose branch was deleted unmerged, is not proposed again unless a new independent source supports it. The report shows fetched titles as text and renders only http and https links. Currency changes are committed to the branch and never enter step 4 of Adoption; the report lists them with sources and merge commands. Currency notes appear in the report and in retrieval only when requested.

### Tooling inventory and context weight (`inventory.py`, 8.x)

Reads each harness's configuration files for MCP servers and tools, counts tool and skill use from the shared session documents, and for context weight uses measured prompt tokens where a session document carries them (LM Studio log, harness usage on the first request) or labelled estimates otherwise. Flags consumption above the configured share of a known window.

### Adoption (`adopt.py`, `scan.py`, 9.x)

Per repository with changes:
1. `git worktree add` a work copy under `~/.dreaming/work/<run>/<repo>` on branch `dream/<run-id>` from the default branch; the user's checkout is never touched here (9.1). The author edits there with a file-tool allowlist; the program makes one commit per change citing evidence ids, running the repository's generate commands first so derived files are in the same commit (9.2, 9.5). An unattended skill is used where the author's tool list includes it; an interactive one is deferred and reported (9.3). The author's output is either a repository change, expressed as id-keyed edits to named rules or skill sections (never a whole-file rewrite) where each edit cites a supporting and a counter case from the evidence, or a learning recommendation (stored in `learning`, never committed); a change may name other changes it depends on (`depends_on`), which defines the linked group for 9.10.
2. Public repositories: `scan.py` checks every commit and message — credentials (patterns seeded from `scripts/review_html/redact.py`), quote text of configured length not already in the repository, and names from the external list. A failing change is saved as a patch under `~/.dreaming/patches/` and not committed (9.12).
2a. Replay (9.16–9.18): for a change to a skill or rule that cites session observations, the Adopt step runs the replayer once per authoring on up to `replay_max_sessions` sessions showing the pattern (never forgotten ones, and only those with a complete recorded opening prompt). Each session runs twice on one backend, without and with the change. The replayer is a tool-free role: it receives the session's opening prompt and, in the second run, the changed instruction (loaded from the throwaway copy, the only instruction it sees, 4.4), and returns its first response and plan. A reviewer-role call judges both outputs: a session counts as replayed only if the problem recurs without the change, and its with-change result is `recurs|resolved|unclear`, where `unclear` counts as `recurs`. For a lens or role-prompt change, the affected role is re-run on the stored inputs of its earlier calls and the outputs are compared the same way. The change is held if the `recurs` share exceeds `replay_max_recurrence`, fewer than `replay_min_sessions` sessions were replayed, or the budget could not cover it; a held change keeps its whole repository branch unmerged (9.17), with the reason in the report. A change citing only file findings is not replayed.
2b. Fetched content (9.19): the author step records whether the research it received contained fetched web or pull-request text (`changes.external_input`). A change with `external_input` is committed to the branch and never enters step 4, exactly as currency changes.
3. Checks: a detached worktree of `merge(default, dream branch)` runs every lint and test command from that result. No configured commands, or any failure, blocks auto-apply (9.6, 9.8).
4. Merge: the check worktree creates the merge commit (`--no-ff`) and tests it. Adoption then runs `git merge --ff-only <tested-sha>` in the user checkout, allowed only when auto-apply is on, the checkout is on the default branch and HEAD equals the HEAD the merge commit was built on; git itself refuses a moved HEAD or conflicting local changes, which is reported as a condition not met. The deployed commit is therefore the tested commit (9.7). A `merging` row with `head_before` is written first, and state after a crash is derived from git (`git merge-base --is-ancestor <sha> HEAD`), not from the row alone. A `deploying` row precedes deploy commands, which leave no trace in git; `deploying` without `deployed` on resume is the 9.15 state.
5. Failure: `git revert -m 1` the merge with a `Dreaming-Revert: <run>` trailer, redeploy, report both outcomes; linked repositories are preflighted together and reverted together (9.9–9.10). A harness session already sees merged files at merge time (`sync-claude.sh` links them to the checkout), so the revert is the real rollback and deploy commands must be safe to re-run. Steps are recorded durably in `adoption(repo, branch, step, head_before, head_after, at)` with steps `checking|checked|merging|merged|deploying|deployed|reverted`.

Worktrees are removed when a run ends; branches stay. `dream.discard` deletes the run's unmerged branches and worktrees, removes the run's rows (observations, revisions, calls, steps) in one transaction, keeps a `runs` row with status `discarded`, and refuses, printing the 9.15 commands, when any repository was merged. After the budget is exhausted, authored changes still proceed through adoption, which makes no model calls.

A later dream (not a 9.15 resume) never starts a new branch or merge in a repository whose latest adoption is `merged` without `deployed`; it lists the repository with the finish and undo commands and proceeds with other repositories. A dream with an unmerged branch for a pattern proposes nothing for that pattern (9.14). Reverts of merged changes are detected by the next dream from git history and stored as `rejected` unless they carry the `Dreaming-Revert` trailer (those are `failed`); a reset or manual undo is not detected, and after a recovery revert the report gives "revert the revert" instead of a merge command; the pattern is re-proposed at most once on observations newer than the revert (9.13).

### Report (`report/`, 10.x)

Rendered with the CSS and page shell of the `review_html` module in agentic-coding's `scripts/`, vendored once into the package with its source revision and licence recorded, so the package has no import path into that repository and no runtime dependency on its checkout (14.4, 10.5). Written to `~/.dreaming/reports/<run-id>.html`; opened with the default browser only for user-initiated terminal or skill runs; a browser failure is logged only (10.1). Sections: summary and statistics, knowledge revisions, learning recommendations, repository changes with merge/revert commands (each followed by generate and deploy commands, 10.2), deferred and discarded candidates with reasons, tooling inventory, unmerged branches, config/restriction/tool-list changes.

## Data Models

SQLite at `~/.dreaming/dreaming.db`, migrations by integer `user_version`.

| Table | Key fields |
|---|---|
| `runs` | id, requester, status (`running|interrupted|complete|partial|budget_exhausted|discarded`), revision, started/ended, process group, overrides, budget JSON |
| `steps` | see Steps and plan view |
| `sessions_seen` | session id, source, thread_id, harness, model, provider, local, project, domain, workflow, interactive, lens versions, entries_read, state (`read|skipped|failed`), forgotten flag |
| `calls` | run, task id, attempt, role, backend, model, tokens in/out, estimated, seconds, session_ref, outcome |
| `observations` | evidence id, session, entry id, source location + representation version, redacted quote, kind, modality, excluded flag, outcome, lens id+version, pattern id, backend/model, subject |
| `file_findings` | evidence id, repo, revision, path, location, lens, finding |
| `research_findings` | id, question, finding, sources, backend/model, run; kept apart from observations, never counted as behaviour evidence (13.1, 13.6) |
| `patterns` | persistent id, key, lens scope, created |
| `knowledge_items`, `knowledge_revisions` | id, version, kind, scope, status, confidence + basis, supporting/contradicting evidence ids, latest support date, lens, model, originating run or feedback, actor (`dream|user|feedback`), base version, pending_reassessment |
| `feedback` | feedback id, revisions (cited/present_only), run/session ref, outcome, basis |
| `changes` | pattern or currency finding, repo, branch, commit, external_input flag, applied_at, reverted_at, status (`proposed|applied|waiting|withheld|rejected|failed`), rank signals |
| `replays` | change, session, backend/model, judgement (`recurs|resolved|unclear`), tokens; at most one set per authoring |
| `currency_findings` | id, target, claim, sources (title, link, retrieval date, stored text), status |
| `adoption` | see Adoption |
| `registrations` | tool, run ref, session, correlation id, workflow, project, user-quote entry ids |
| `learning` | recommendation id, scope, evidence, next step, outcome, disposition (`open|dismissed|deferred_until|addressed`) |

Evidence stored is redacted; source references carry an availability marker (`available|unavailable|changed`) updated when a source disappears (13.7). Per-session pattern counts stay after the transcript is gone (6.6).

Effect measurement (11.1): for each applied change, count observations of its pattern and sessions read in the pattern's lens scope in the periods before and after `applied_at`, reported as raw numbers labelled association. The result is "insufficient evidence" when the before or after session count is below `min_sessions_for_rate`, when the before count is zero, or for file-only findings.

## Error Handling

| Failure | Behaviour |
|---|---|
| Second start | Exit 4 naming the running dream, state unchanged (1.6) |
| Budget or wall-clock reached | Stop new calls, save, run `report`, exit 5 with status `budget_exhausted` |
| All backends for a role unavailable | Save, report completed work, exit 5 with status `partial` (5.3) |
| Parse failure of a session | Record skipped with reason; continue (2.7) |
| Report without a browser | Log only (10.1) |
| Resume after a merge into a user checkout | No further merges or deploys; report state and commands (9.15) |
| Process gone while holding the lock | The kernel releases the flock; run resumes if interrupted (1.6) |
| Migration while a run is unfinished | Refused with `migration_blocked` naming the run; resume or discard it first |

Exit codes follow screw: 0 success, 1 failure, 2 usage or config, 4 skipped (already running), 5 partial or budget-exhausted.

## Risks and Assumptions

- Risk: harness isolation holds per version | Verify: first implementation task probes each backend and version — `codex debug prompt-input` for Codex, a real exec session for its tool list (the prompt view may ignore feature flags, and `spawn_agent` stayed listed under every flag tried), `claude --safe-mode` with `--mcp-config` and the parent-directory instruction walk from `DREAMING_HOME` for Claude — and confirms apsis finds the call's session | If wrong: the backend is skipped for roles needing isolation (5.5), or for Codex the adapter enforces by killing the call on an agent-launch event; the probe result names the leak.
- Risk: each harness's structured-output option differs by version | Verify: same probe task | If wrong: take the final message as JSON and rely on program validation alone.
- Risk: a local model produces schema-valid, quote-accurate reader output | Verify: run the reader on ten recorded sessions in a dry trial before enabling it as the default backend | If wrong: configure a cloud backend first in the reader's fallback list.
- Assumption: rune renders and parses the plan file written by `plan.py` and does not need it read back | Verify: plan-view test against the installed rune | If wrong: drop the rune-format rendering and print plain text.
- Risk: LLM-consolidated knowledge can be worse than none (arXiv:2605.12978) | Verify: after the first month of real dreams, sample active items and compare a recorded session's outcome with recall on and off, by hand or with the reader | If wrong: raise `min_sessions`, restrict recall to items with user-confirmed outcomes, or return raw quotes only.
- Risk: a past session's opening prompt with and without a changed instruction does not predict real behaviour, few sessions reproduce the problem without the change (so instruction changes often wait on their branch), and the recurrence judge is an LLM | Verify: for the first five instruction changes, compare the replay result with whether the pattern recurs in later sessions (11.1) | If wrong: raise `replay_min_sessions`, or turn auto-apply off for repositories holding instructions (9.11 keeps changes on the branch).
- Assumption: `min_sessions` and `min_sessions_for_rate` are not validated by the literature | Verify: record the observed distribution of distinct sessions per pattern over the first dreams | If wrong: adjust in configuration.
- Assumption: apsis `shared-json' session documents contain `thread_id` for LM Studio and Codex-served sessions | Verify: contract test against real apsis output.

## Testing Strategy

Unit and integration tests use fake `claude`/`codex` executables and a fake apsis fixture directory, with temporary git repositories and real rune for the plan view (the pattern in `tests/test_local_next_task.py`). `make test` in the dreaming repository runs them. Each acceptance criterion has at least one test; the groups:

| Area | Tests |
|---|---|
| Start, lock, resume, dry run (1.x, 5.4) | Second start exits 4; interrupt in each phase then resume repeats no completed call; dry run makes no call and changes no file |
| Sessions (2.x) | Dedupe by `thread_id`; non-interactive entries cannot yield user statements; late registration reclassifies |
| Observations (6.x) | Quote verify then redact; duplicate processing creates no duplicates |
| Knowledge (13.x, 14.x) | Promotion rules, contested/superseded transitions, dismissal stays dismissed, feedback idempotence; fixtures in the style of LongMemEval and MemoryAgentBench: a fact updated later is recalled in its new form, recall abstains when scope matches nothing, a dismissed item and its excluded evidence stay out, a hedged quote is never returned as asserted |
| Replay (9.16–9.19) | A change that does nothing does not pass (the with-change run still recurs); an unclear judgement counts as recurrence; sessions where the problem does not recur without the change are not counted; a held change keeps its repository branch unmerged; a change that received fetched web or PR content is never auto-applied; too few replayable sessions or too little budget does the same; forgotten sessions are never replayed; a file-finding change is not replayed |
| Forget (2.11) | Forgetting excludes the session from counts, rankings, selection, registration and evidence references; restoring reverses it; repeat calls change nothing; a running dream honours it before the next call |
| Currency (16.x) | One source never yields a candidate; sources on the same domain count once; a relied-on passage absent from the stored text rejects the finding; page text appears only in delimited data fields; a rejected finding is not re-proposed unless a source changed; no currency change reaches step 4 |
| Adoption (9.x) | Dirty checkout blocks merge; HEAD moved blocks merge; deploy failure reverts; public scan withholds; linked repositories roll back together |
| Portability (14.4) | Fresh `DREAMING_HOME`, source and backend outside this checkout, no skills installed: a dream retains knowledge; export imports into another fresh store |

Property-based tests (Hypothesis) where universal guarantees exist:
- Redaction: for any entry text and quote drawn from it, `verify(quote)` holds before redaction, and redaction is idempotent.
- Retrieval: for any item set, scope and limit, `estimated_tokens ≤ limit`, output order is independent of input order, and out-of-scope, unresolved and non-active items never appear by default.
- Export/import: `import(export(store))` into a fresh store then `export` again equals the first export; importing twice equals once.
- Forgetting: for any sequence of forget and restore calls, counts and rankings equal those computed from the non-forgotten sessions only, and forget followed by restore returns the original values; an item or change left without sufficient support is withheld immediately.
- Review order: for any set of observations, shuffling them before review yields the same items, revisions and confidence.
- Budget accounting: for any call sequence, tokens used equals the sum of recorded calls including retries and fallbacks, and no call starts once the limit is reached.
- Crash consistency: for any crash point (before the call, after the call and before the commit, after the commit), resume with a fake model whose answers differ on every call yields the same observations, steps and knowledge as an uninterrupted run, and never applies two different outputs for one step.
