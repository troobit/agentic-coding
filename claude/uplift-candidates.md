# Uplift Candidates — MeData SDD / Claude process review

**STATUS: IMPLEMENTED AND VERIFIED** (diagnosis, implementation, and
adversarial ex-post verification all 2026-07-03). See "Implementation log"
and "Final state" at the bottom of this file.

Corpus: 158 top-level sessions + 101 subagent transcripts across 15
`~/.claude/projects/-Users-r-repos-medata*` directories (June 3 – July 3, 2026),
mined by 11 partitioned agents. Full per-partition evidence reports:
`~/.claude/projects/-Users-r-repos-agentic-coding/uplift-mining-reports/mined-*.md`

Scope per user: Gemini/Codex/Cursor and Figma MCP **service** issues (quota,
auth, plan limits) are out of scope. Interface problems those incidents exposed
(loops without stop conditions, headless sessions asking questions) are in scope.

Session-impact estimates are against the ~88 substantive sessions (70 of the
158 were one automated loop's respawns — themselves a finding, see C3).

---

## P1 — high recurrence, clear payoff

### C1: Device verify loop automation (`deploy-device` + log capture)
- **Verdict**: automation (script/Make targets + small skill) in the medata repo
- **Recurrence**: every on-device session — 15-20 sessions across 5 partitions;
  the single most repeated manual workflow in the corpus
- **Evidence**: identical xcodebuild+devicectl incantation with hardcoded device
  UUID ~50 times (fruit-plate); user as log courier — 10+ giant Console.app
  pastes, 3 truncated needing re-paste; one session killed outright by a log
  paste ("Prompt is too long", c8c2b7a6); Console filter recipe re-derived ≥4
  times; stale on-device binary silently invalidated 2-3 full human capture
  rounds; Release+stub build steps re-issued to the user in 3 sessions
- **Shape**: (a) `make deploy-device` — build, install, launch, and log a build
  stamp at app launch so staleness is detectable; (b) log capture to file via
  `log stream --predicate 'subsystem == "ie.medata.app"' > file` that Claude
  reads instead of chat pastes; (c) Console filter recipe + Debug/Release-stub
  matrix in agent-notes; (d) later: `simctl io screenshot` loop for UI
  self-verification (3 UI sessions deferred all visual checks to the human)
- **Build cost**: low-medium (scripts + notes; screenshot loop medium)
- **Impacts**: ~20% of sessions, and specifically the longest/most expensive ones

### C2: rune crib sheet + CLI fixes
- **Verdict**: fix (skill doc) + small CLI patches in ~/repos/rune
- **Recurrence**: 15+ sessions across all 8 signal-bearing partitions — the most
  widespread single tool friction
- **Evidence**: `details` must be `[]string` not string — hit ≥6 times over 3
  weeks; invented subcommands (`get`, `start`, `show`) ≥5 times; arg order
  `[file] [task-id]` confusion; `rune next` needs explicit file path in
  worktrees (cwd resets); grammar rediscovered by ~10 /tmp experiments (no YAML
  frontmatter, no free prose between phase heading and first task); Blocked-by
  title-hint parenthesis parsing corrupts task refs; token-spew corruption
  committed into two tasks.md files; task-state drift — rune's view diverging
  from the file across sessions ("already [x] yet rune reported Pending", 3+)
- **Shape**: (a) rune skill gets an exact crib sheet: valid subcommands, batch
  JSON schema with `details: []string` example, file-first arg order, "always
  cd to worktree root"; (b) CLI: coerce string→[string] in batch, fix
  parenthesis title-hint bug, `rune complete` atomic with a file re-read;
  (c) make task-completion marking part of the commit step so state can't drift
- **Build cost**: low (doc) + low-medium (Go patches)
- **Impacts**: ~20% of sessions, plus every headless phase runner

### C3: Headless loop hardening (orbit)
- **Verdict**: fix in ~/repos/orbit + prompt contract
- **Recurrence**: 60+ wasted no-op sessions (ui-restoration), 2 worktree
  collision incidents across 3 sessions (nutrition5k), ~30 session-limit stalls
- **Evidence**: loop respawned every ~60s against a known-exhausted blocker for
  ~10 hours — every session re-read notes, concluded "blocked until July 1",
  exited; two orbit runners launched 5s apart drove concurrent Claudes in one
  worktree — duplicate implementations written then discarded, a mid-edit file
  compiled; orbit kept re-prompting through "You've hit your session limit"
  windows (likely how the duplicate got spawned); 27 AskUserQuestion calls in
  headless sessions dismissed unanswered
- **Shape**: (a) per-worktree lockfile/PID check before launch; (b) parse the
  limit message and sleep until the stated reset time; (c) halt on a
  blocked/nothing-to-do sentinel (next-task exits non-zero or writes a HALT
  marker); (d) loop prompt gains "non-interactive: never ask; record blocker
  and exit"
- **Build cost**: medium (orbit is the user's Go tool; all four are contained
  changes)
- **Impacts**: prevents the two biggest waste events in the corpus; every
  future unattended run

---

## P2 — recurring, cheap to encode

### C4: nextup close-out verification (against evidence) + worktree sync
- **Verdict**: verify recent work, then one fix
- **Recurrence**: "write your plan/state to nextup.md before stopping" typed
  15+ times across 10+ sessions; nextup.md worktree sync friction in 5+
  sessions (cp/diff loops, "merge the nextup.md from main again", fresh
  creation because gitignored files don't travel); machine-marker loss 2×;
  content drift (raw log dumps) corrected 3×
- **Evidence**: strongest cluster in June 12-25; commit d0a5e5f (close-out
  mode, simpler markers) and ca9e2ef (dispatcher) land after most of it
- **Shape**: (a) verify d0a5e5f actually removes the prose-prompt need —
  the evidence predates it; (b) add: /nextup in a worktree reads/merges the
  main-repo nextup.md automatically; (c) close-out validates structure every
  time (marker present, no log dumps, explicit next-skill routing); (d) on
  interrupt, write state first, ask nothing (2 sessions needed double pause
  requests)
- **Build cost**: low (skill edits on top of existing work)
- **Impacts**: every session — /nextup is the entry point (26 user-typed
  invocations; next-task dispatched 83×)

### C5: Staging-phase "no source edits" guardrail
- **Verdict**: fix (starwave skills) + doc-audit read-only mode
- **Recurrence**: 4 corrections in 4 sessions, two pairs of the same pattern
- **Evidence**: "You are overstepping. Your job is to write the smolspec...
  Not do the work" then the same correction the next day (fruit-plate, both
  needed manual reverts); "docs only, don't touch code" stated preemptively
  once and as a mid-session correction once (docs/mvp-refine)
- **Shape**: starwave-creating-spec/smolspec/tasks: staging phases MUST NOT
  edit source, even "purely a code edit" tasks; a doc-review mode (or
  explain-like extension) with no-code-changes baked in
- **Build cost**: low (prompt-level constraint in existing skills)
- **Impacts**: ~5% of sessions, but each miss costs a revert and trust

### C6: Close-out sweep — follow-ups and doc-sync
- **Verdict**: new close-out steps (nextup close-out or sendit)
- **Recurrence**: 3 "worth a follow-up/separate ticket" items evaporated with
  no task created (deleteMeal regression test, stale-meals assertion,
  torchvision aux_loss bug); doc drift accumulated until 3 dedicated multi-hour
  audit sessions (~4MB of transcript); OVERVIEW.md handled inconsistently by
  phase runners (some hand-edit, some skip); canonical-name conflicts
  re-litigated (segmenter.mlpackage — 3 sessions)
- **Shape**: close-out (a) greps the session for follow-up phrases and creates
  rune tasks/tickets; (b) runs /specs-overview once instead of per-agent
  ad-hoc; (c) verifies names/claims touched this session against code (the
  full-audit sessions stay, but stop being the only mechanism); (d) records
  naming decisions in the decision log the first time they're adjudicated
- **Build cost**: low-medium
- **Impacts**: ~15% of sessions generate evaporating follow-ups; audit sessions
  were 3 of the longest in the corpus

### C7: make-it-so refinements
- **Verdict**: fix (skill)
- **Recurrence**: 1 dead session + 1 interrupt (target ambiguity); 2 phases
  uncompilable at phase boundary; 2 of 2 standalone verify sessions
  rubber-stamped while critic-on-diff found real gaps
- **Evidence**: bare /make-it-so resolved to the wrong spec whose next task was
  a human STOP gate (user hit Esc, restarted with explicit path); "the
  pre-existing App.swift call fails to compile because task 3 changed that
  signature; the wiring lands in task 14" — burned diagnosis time twice;
  design-critic on the implementation diff found 3 real issues the review
  prompt missed
- **Shape**: (a) when >1 tasks.md exists, list candidates and confirm — or read
  the active spec from nextup machine zone; (b) task planning keeps each phase
  commit buildable, or tasks.md notes expected breakage; (c) replace the
  "review the implementation" verify prompt with critic-on-diff; (d) relay
  batch-subagent results with a one-line plain-English "how to verify on
  device" per fix (user: "not sure I understood the problem")
- **Build cost**: low-medium
- **Impacts**: every spec implementation (the dominant workflow: 33+ headless
  phase-runner sessions)

---

## P3 — environment notes and small fixes

### C8: medata project rules (one agent-notes/CLAUDE.md pass)
- **Verdict**: fix (notes), single batch
- **Items and recurrence**:
  - `check_spelling.sh` SwiftUI false positives re-triaged in 6 sessions →
    fix the linter (exclude Swift API identifiers / App/*.swift)
  - App-target tests in MeData/Tests/ are not executable (no test target) —
    rediscovered in 5 sessions; either wire a test target or state the
    convention and stop writing non-executable "documentation contract" tests
  - New App/ files need explicit pbxproj registration (4 sessions, 1
    user-visible build break) → note now; XcodeGen/tuist is the durable fix
    but a bigger call
  - Package layout paths guessed wrong before discovery (5+ failures) → state
    where Package.swift lives per worktree
  - MVP test gate: "does it build + does it look right on device" — user said
    "Remember"; verify it was persisted, else it will be re-proposed
  - gitignore Xcode workspace user files; CHANGELOG.md union merge or generate
    at release time (2 conflict/rewrite sessions)
- **Build cost**: low (one pass) — linter fix lowest, pbxproj tooling deferred

### C9: run_silent PATH
- **Verdict**: fix (install) or soften the CLAUDE.md check
- **Recurrence**: "run_silent not found" errors in 6+ sessions, always in
  worktree/subagent shells
- **Shape**: install globally, or phrase the check so absence is a clean
  negative (`which run_silent || true`)
- **Build cost**: trivial

### C10: AskUserQuestion usage contract
- **Verdict**: CLAUDE.md note
- **Recurrence**: 27 dismissed in headless sessions (covered by C3d); in
  interactive sessions the user rejected gates or answered via free-text notes
  5+ times, and once: "ask your question succinctly again"
- **Shape**: notes field carries the real instruction — parse it as
  first-class steering; clarifying questions must be single, concrete, and
  describe observable behavior; gates should offer an "explain the doc first"
  path (sendit already covers the review-in-Prism case)
- **Build cost**: trivial

---

## Explicitly "nothing" (checked, no action)

- Write-before-read Edit errors (55): harness guard works, self-recovering
- git push permission denials: rule working as intended — keep
- API socket drops / 529s: transient; recovery via rune checkpoints worked
- /commit skill unused (user commits via prose): outcomes fine, no corrections
- Gemini/Codex/Figma service failures: out of scope per user
- One-offs: clamshell sleep, auth expiry, Figma per-host OAuth, sleep-poll
  block, zsh glob quoting

## Patterns that work — do not disturb, consider codifying

- **agent-notes as cross-session state**: ~45 loop sessions correctly refused
  to burn quota because a blocker note existed; ui-capture-flow.md prevented a
  re-probe. The single best-performing mechanism in the corpus.
- **Worktree isolation for fan-out**: made discard-and-rerun safe after an API
  outage killed 4 of 9 agents
- **nextup user-zone as async work queue**: 3 sessions ran start-to-finish with
  zero human input, correctly self-routing
- **design-critic on implementation diff**: found real gaps both times it ran;
  standalone verify passes found nothing either time (see C7c)
- **Consolidate-then-confirm when queued asks stack**: worked well; matches the
  nextup dispatcher model
- **rune-checkpoint recovery**: a make-it-so subagent died mid-run at 12/15
  tasks; per-task rune state let the parent finish the last 3 inline

---

# Implementation log (2026-07-03)

Constraint honored throughout: `rune` and `orbit` origins are
`ArjenSchwarz/*` (upstream itself, not forks) — patches there are minimal,
tested, one-commit-per-fix, written as upstream PR candidates, and never
pushed. Doc-shaped fixes went into this repo's skills instead (zero
divergence). medata and agentic-coding are ours; full fixes applied.

## C9: run_silent — DONE
- Created `claude/scripts/run_silent` (POSIX sh: buffers stdout/stderr to a
  temp file, prints only on non-zero exit, one-line `ok:` ack on success,
  preserves exit code) and installed to `~/.local/bin/run_silent`, which is on
  the non-interactive zsh PATH — verified with success and failure cases.
- Root cause of the 6+ "run_silent not found" errors: the tool never existed
  anywhere; CLAUDE.md described it aspirationally. Existing CLAUDE.md wording
  ("check with `which run_silent`") is now accurate — no doc change needed.

## In flight (sub-agents, one per repo)
- rune (`uplift-fixes` branch): C2 CLI patches — batch details coercion,
  Blocked-by parenthesis bug, worktree git discovery, subcommand suggestions
- orbit (`uplift-hardening` branch): C3 — run lock, limit-aware backoff,
  ORBIT-HALT sentinel + no-commit circuit breaker, headless prompt docs
- medata (`uplift-process-fixes` branch): C1 + C8 — Makefile device loop,
  build stamp + segmenterSource launch log, spelling-lint fix, hygiene, notes
- agentic-coding (this branch): C2 crib sheet, C4 nextup, C5 staging guard,
  C6 close-out sweep, C7 make-it-so/next-task (incl. ORBIT-HALT contract), C10
Each will be written up here as it completes, then verified ex-post by
independent review agents.

## C2 (doc half), C4, C5, C6, C7, C10: agentic-coding skills — DONE
Six commits on `nextup-resume-entrypoint` (sub-agent, verified against the
installed rune binary rather than the error reports):

- **C2 crib sheet** (5e93aba, claude/skills/rune/SKILL.md): ground-truthing
  corrected the mining record in two places — YAML frontmatter actually parses
  fine (free prose in the body is what fails), and the skill itself contained
  the wrong `"details": "string"` example that seeded the recurring batch
  error. Added: subcommand whitelist, batch JSON schema with `details:
  []string`, file-first arg order, explicit-path-in-worktrees rule, file-format
  strictness, JSON output shapes (list uses capitalized ID/Title/Status-int;
  next uses lowercase keys).
- **C4 nextup** (7fb98c9): d0a5e5f/ca9e2ef already covered close-out mode,
  marker migration, and dispatcher rules. Added the gaps: worktree rule
  (read/merge main repo's nextup.md via `git worktree list`), close-out
  structure validation (marker repair, no raw logs, explicit next-skill
  routing), interrupt protocol (write state first, ask nothing), soft
  contradiction handling (file wins, nearest achievable step — never
  hard-refuse).
- **C5 staging guardrail** (1cc4d80): "HARD RULE: No Source Edits" in
  starwave-creating-spec and starwave-smolspec; starwave-tasks' existing
  Workflow Scope section upgraded to the hard rule with the instrumentation
  clause.
- **C6 close-out sweep** (385a419): nextup close-out sweeps untracked
  follow-ups into rune tasks / Next up, runs /specs-overview once when specs
  changed, records adjudicated naming conflicts in the decision log; sendit
  captures loose ends; creating-spec Phase 4.5 now invokes /specs-overview
  instead of hand-editing OVERVIEW.md.
- **C7 make-it-so + next-task** (7f70b23): Target Resolution (nextup machine
  zone → confirm when ambiguous) and Phase Buildability blocks; review step
  sharpened from critic-over-state to critic-on-diff with a per-fix
  plain-English verification line; next-task gained the Headless Runs section
  with the exact `.orbit/halt` / `ORBIT-HALT: <reason>` sentinels orbit is
  being taught to honor.
- **C10 AskUserQuestion contract** (3ad6672, global CLAUDE.md): notes field is
  the real instruction even when the option looks like a rejection; one
  concrete observable-behavior question at a time; approval gates offer an
  "explain it first" path.

## C3: orbit hardening — DONE
Four commits on `uplift-hardening` (off 058579e; never pushed; `make test`
29/29 packages + golangci-lint clean after every commit). Divergence kept
minimal — orbit already had rate-limit-wait machinery, so the limit fix is a
targeted bug fix, not new infrastructure.

- **Run lock** (0979b17, internal/orbit/lock.go): `.orbit/run.lock`
  (pid/start/hostname JSON) acquired with O_CREATE|O_EXCL before mode
  dispatch; refuses with a clear error naming the live holder; stale/corrupt
  locks auto-removed; released on all exit paths incl. SIGINT/SIGTERM;
  skipped in dry-run. Directly prevents the two double-launch collisions.
- **Session-limit backoff** (533cef7, internal/agents/claudecode): root cause
  was two-fold — the classifier's "hit your limit" substring missed "hit your
  *session* limit", AND Claude reports limit exhaustion as a *successful*
  result whose text is the banner, so phases "succeeded" and respawned
  instantly (the ~30 dead sessions). Fixed with a tolerant regex, banner
  detection on otherwise-successful output routed into the existing
  sleep-until-reset machinery, and a 30m fallback when the reset time is
  unparseable (previously aborted the run as Unknown).
- **Halt sentinel + circuit breaker** (ea4c534, internal/orbit/halt.go):
  line-anchored `ORBIT-HALT: <reason>` checked after each phase; `.orbit/halt`
  file checked each iteration; both stop the loop reporting the reason
  (matches the next-task skill contract exactly). No-progress breaker trips
  after N consecutive iterations with no new git HEAD and no pending-task
  reduction (default 3, `no-progress-limit`/`ORBIT_NO_PROGRESS_LIMIT`,
  ≤0 disables; rate-limit waits don't count) — would have capped the 60
  no-op-session incident at 3.
- **Docs** (c5356f9): README "Loop Safety" section with the recommended
  headless prompt clause and sentinel names verbatim; env-var tables updated.
- **Deferred as recommend-upstream**: halt/breaker plumbing for variant mode
  (separate loop, needs per-variant workdir support); per-variant worktree
  locks (launch-dir lock already covers the observed incidents).

## C2 (CLI half): rune patches — DONE
Three commits on `uplift-fixes` (off local main 60b54e0; never pushed;
`make check` clean before every commit, `make test-integration` at the end).
Each written as an upstream PR candidate.

- **Batch string coercion** (17d4753): `FlexibleStrings` type coerces a bare
  JSON string into a one-element slice for `details`/`references`/
  `requirements` (array-first, null no-op; lossless). Table-driven tests + E2E.
  Kills the error that recurred 6+ times over three weeks.
- **Blocked-by parenthesis corruption** (8882a21): root cause confirmed by
  live repro of the exact `wrapper, loading, wrapper, loading...` spew — the
  hint regex `\([^)]*\)` stops at the first `)`, so nested parens leak title
  words into the ID scan, and 7-char lowercase words match the stable-ID shape
  and get appended as new dependencies every parse/render cycle. Two-sided
  fix: balanced-paren scanner in parse.go + hint sanitization in render.go.
  Regression tests include a 3-cycle parse/render fixed-point proof; pre-
  corrupted files stop growing. One root cause explains both mining incidents
  — it was rune-side, not caller-side.
- **Worktree discovery** (4637cd1): the hypothesized bug doesn't exist on
  current main — discovery uses `git rev-parse` and works from a linked
  worktree root (transcript failures were an older build). Added a real-git
  worktree regression test to lock it in. Genuine adjacent bug found but NOT
  patched (divergence constraint): discovery from a repo subdirectory returns
  a root-relative path commands then open CWD-relative → "no such file"; a
  proper fix must relax ValidateFilePath's CWD-containment security model —
  **recommend upstream issue** proposing repo-root as the containment
  boundary.
- **Invented subcommands**: skipped with evidence — cobra suggestions are
  already on (`rune get` → "did you mean next?"); `show`/`start` are beyond
  edit distance 2 and forcing them would misfire. The crib sheet (5e93aba) is
  the right lever.

## C1 + C8: medata device loop + project rules — DONE
Five commits on `uplift-process-fixes` (off `research`; never pushed).
Validation: `make build` green; `make test` exit 0 (XCTest 323 + swift-testing
16, both totals printed); `make spell` exit 0; unsigned device app build
SUCCEEDED. Device-dependent targets dry-run only — first real deploy needs the
phone connected.

- **Makefile + deploy script** (0e488be): `build`, `test`, `spell`,
  `build-app`, `deploy-device`, `logs-device`, `deploy-release-stub`, `help`;
  `DEVICE_UDID` parameterized (defaults to PhoneMax). Two empirically-driven
  decisions: iOS has no scriptable live log stream (`log stream` is
  host-only), so `logs-device` uses `log collect` + filtered `log show`, teed
  to /tmp/medata-device.log, limits documented; `deploy-release-stub` does a
  trap-guarded edit+revert of the Package.swift DEV_STUB_SEGMENTER define
  (env-var approach rejected — Xcode caches the evaluated manifest and can
  silently build the wrong configuration).
- **Launch stamp** (75e9b02): app logs `event=launch buildStamp=<sha>-<ts>
  segmenterSource=stub|coreml` at startup — the two facts whose absence cost
  wasted capture rounds and days of stub-vs-real confusion. Empirical finding:
  arbitrary `INFOPLIST_KEY_*` CLI settings are NOT injected; solved with a
  committed Info.plist + `$(MEDATA_BUILD_STAMP)`. (The "No such module
  CaptureKit" IDE diagnostic was a pre-existing indexing artifact; the build
  succeeds.)
- **Spelling linter** (0be6f57): code-aware pattern for .swift (`.center`
  members etc. no longer flagged; string catalogs stay strict). Clean tree
  passes; genuine violations still fail. Ends the 6-session re-triage loop.
- **Hygiene** (36030eb): workspace file untracked + ignored; `CHANGELOG.md
  merge=union` appended to the pre-existing .gitattributes.
- **Docs** (8559344): device-build-and-test.md (Make targets as canonical
  loop, stamp-check ritual, stub matrix, Console recipe); ui-capture-flow.md
  (app-target tests are documentation contracts; 4-location pbxproj
  checklist); swift-package.md (Package.swift at worktree root only);
  CLAUDE.md (Makefile interface + MVP test gate — the Jun-20 "already saved"
  claim was false, nothing existed); Decision 10 (canonical
  segmenter.mlpackage) in specs/estimation/model-production/decision_log.md.

## Ex-post verification

### rune — GO (adversarial verifier, all claims CONFIRMED)
- Both original bugs reproduced on a main-built binary; fixed behavior
  verified on the branch binary (token-spew line reaches a byte-identical
  fixed point across 4 renumber cycles; bare-string batch succeeds).
- Regression tests proven real: the new parse tests FAIL when run against
  main's source. Unicode/comma/multi-ref/unbalanced-paren edges all stable.
- Known remaining subdirectory-discovery bug reproduces exactly as documented
  (upstream-issue candidate confirmed).
- CHANGELOG follows Keep-a-Changelog per CONTRIBUTING; lint clean.
- Minor non-blocking polish noted for the eventual upstream PRs: the coercion
  error message no longer names the offending field; an unbalanced open paren
  in a hand-edited Blocked-by line silently drops trailing valid IDs;
  cosmetic double-space in sanitized hints. Left as-is (divergence
  minimalism) — worth folding into the upstream PR discussion.

### orbit — GO pending one fix (adversarial verifier, all 4 claims CONFIRMED)
- Limit-regex anchoring verified genuine: detection runs only on the session's
  final result field, start-anchored — legitimate output that merely mentions
  the limit does NOT match. Routing to the existing sleep-until-reset
  machinery verified end-to-end, 30m fallback confirmed.
- Halt contract cross-checked verbatim against next-task SKILL.md — both sides
  agree on `.orbit/halt` and `ORBIT-HALT:`; orbit is strictly more lenient
  (marker on any line of the final message), compatible.
- Breaker verified structurally: rate-limit waits cannot increment it; empty
  repos fall back to pending-count safely.
- **One genuine bug found and demonstrated deterministically**: stale-lock
  removal TOCTOU — two simultaneous starters over a stale lock can BOTH
  acquire (racer B's os.Remove deletes racer A's live lock), and Release()
  can remove a lock it doesn't own. Sent back to the implementer for an
  atomic-removal fix (rename-based or flock) + ownership check in Release()
  + regression test, plus two trivial nits (env-var doc wording; redundant
  assignment). Verdict recorded as final once the fix lands and passes.
- Scope note for the eventual upstream PR: the run lock gates variant mode
  too (acquired before mode dispatch) — correct behavior, but should be
  stated; a cooperative halt is currently recorded as a failed run — reviewer
  flagged as a question for upstream.

### agentic-coding skills — GO after follow-up fixes (commit eb2c87c)
Verifier ground-truthed every crib-sheet statement against the installed rune
binary and cross-checked the ORBIT-HALT contract (verbatim match with orbit,
PASS). Deployment confirmed live: ~/.claude/CLAUDE.md and ~/.claude/skills are
symlinks into this repo — the guidance is active for all sessions on this
branch now; merge to main to make it durable.

Findings fixed in eb2c87c:
- Crib sheet factual error: "discovery fails in git worktrees" was FALSE —
  discovery works; the real trap is branch-name-based path resolution (a
  worktree's branch maps to a nonexistent spec path) plus root-only cwd
  resolution. Reworded with the true mechanism, prescription unchanged.
- Batch guidance reworded as prescription ("always send arrays") so it stays
  correct when rune's coercion fix lands (blocked_by never coerces).
- nextup close-out intro + hard-rule bullet still contradicted the new
  bookkeeping exception (stale "writes no other files" sentences) — both now
  acknowledge the three named artifacts.
- make-it-so and next-task Specs Overview sections still instructed
  hand-editing OVERVIEW.md — both now run /specs-overview instead, completing
  the policy 385a419 claimed.
- Subagent templates used file-less `rune complete` — now pass the explicit
  tasks-file path, consistent with the crib sheet.
Verifier also confirmed: no-source-edits rule present in all three starwave
skills with no contradicting passages; nextup coherent end-to-end after three
edit rounds; frontmatter intact in all 8 modified files.

### medata — GO (adversarial verifier, all 5 claims CONFIRMED; nits fixed in 8bc83b0)
Every guard survived empirical attack: dirty-manifest refusal (guards run
before the trap registers, so a refusal never touches the file), drift guard,
EXIT-trap coverage verified through SIGINT/SIGTERM (only SIGKILL leaves the
edit, and the dirty guard then blocks the next run loudly), linter
false-positive and false-negative probes, unsigned build with stamp verified
via PlistBuddy. The verifier independently re-proved the "INFOPLIST_KEY_* not
injected" claim (probe key does not land in the built plist) and confirmed
segmenterSource derives from the same compile-time gate that selects the
engine — it cannot log coreml while the stub is active. .gitattributes LFS
rules verified byte-identical to research (purely additive change).
Two cosmetic findings fixed in 8bc83b0: App.swift comment pointed at the
wrong plist path; a pre-existing LFS rule targeted a dead path — retargeted
to the canonical segmenter.mlpackage location (Decision 10) so the model
would be LFS-tracked if ever committed.
(Recurring "No such module 'CaptureKit'" IDE diagnostic: confirmed
pre-existing SourceKit indexing artifact; builds succeed.)

### orbit — final GO (re-verification of b301d87)
- TOCTOU fix confirmed: whole check-remove-create sequence under exclusive
  flock on `.orbit/run.lock.guard`; no deadlock path (guard released on every
  return via defer, held only for acquisition, blocking LOCK_EX guards a
  microsecond critical section); never-unlink argument correct (standard
  flock unlink-race mitigation; cost is one persistent 0-byte file).
- Release() ownership check confirmed (PID + StartedAt must match).
- Falsification performed: with the guard neutralized the regression test
  fails deterministically ("got 2 winners", 3/3 under -race); with the fix,
  5/5 pass. The test provably detects the race; the fix provably closes it.
- Implementer's rebuttal of the "redundant assignment" nit verified correct
  (consolidator.go genuinely reads result.Error) — nit withdrawn.
- Branch scope clean (5 commits, still unpushed), 29/29 packages + lint green.
- Notes for the eventual upstream PR description: lock gates variant mode by
  design; cooperative halt records as a failed run; guard file is
  deliberately persistent.

---

# Final state (2026-07-03)

All candidates implemented and adversarially verified. Branches (none pushed):
- rune `uplift-fixes` — 3 commits, upstream-PR-ready
- orbit `uplift-hardening` — 5 commits, upstream-PR-ready
- medata `uplift-process-fixes` — 6 commits
- agentic-coding `nextup-resume-entrypoint` — 7 skill/rule commits +
  run_silent + this file

Open follow-ups (user decisions):
1. Whether to open upstream PRs to ArjenSchwarz/rune and /orbit from the two
   branches (both verified PR-ready; divergence otherwise accumulates).
2. File the recommend-upstream rune issue: subdirectory discovery returns
   root-relative paths that fail CWD-relative open (fix needs a
   ValidateFilePath security-model decision).
3. Merge medata `uplift-process-fixes` into `research`; first real
   `make deploy-device` run needs the phone connected.
4. Merge this branch to main so the skill changes survive branch switches
   (~/.claude symlinks into this working tree).
