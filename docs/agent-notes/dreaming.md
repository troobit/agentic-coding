# Dreaming specification

- The feature lives in `specs/dreaming/`. Requirements are being refined; design
  and rune tasks follow requirements approval. The spec auditor reports
  `SJ-MODE-001` until a primary design document exists; do not create a placeholder
  design just to remove this phase-dependent finding.
- The user wants trusted personal automation. Tests, Makefiles, checks and
  restrictions are legitimate improvement targets. Active configuration is
  snapshotted per run; adopted configuration changes affect the next run. Every
  configured check must pass on the proposed merged result; there are no baseline
  runs or exemptions for failures already present on main.
- Vault writes and capture-knowledge dependencies are out of scope. Optional
  knowledge folders are read-only sources. External configuration changes are
  suggestions; automatic adoption applies to configured target repositories.
- Tool-using LM Studio roles run through Claude Code or Codex. Direct completions
  are only an option for tool-free roles. `mcp/servers.json` enables devtools'
  codex-agent and gemini-agent globally, so role tool lists must be constructed
  explicitly. The program owns scheduling and budgets. Existing local task-runner
  wiring is evidence of local tool execution, not proof of full role isolation.
- Decisions 1 and 2 hold the check and backend choices. Proposed Decision 6
  supersedes Decision 4's placement boundary: agentic-coding supplies initial
  integrations, while knowledge and dream operations must be usable without its
  checkout, installed skills or any target repository. Implementation language
  and component boundaries remain open for a FOSS reuse assessment; the spec
  does not establish OpenClaw as a standalone dependency. Keep apsis session
  normalization upstream in orbit rather than duplicating its readers here.
- Evidence identifiers represent both session observations and revision-linked
  file findings. Verify session quotes before redacting stored copies. Historical
  context costs may be measured, estimated or unknown. Linked adoption uses
  best-effort group rollback and reports recovery failures.
- Runs can target a repository or workflow, including its specification process;
  refine draft decisions in place while requirements are still being clarified.
- A run keeps its config snapshot and program version even if adoption changes
  dreaming's own code (live via `~/.claude/scripts`). Private scan terms live
  outside every repo, since agentic-coding and orbit are public. Every dream call
  must stay visible to apsis and be marked as the dream's, so role isolation
  cannot use config dirs that hide transcripts. After a crash mid-adoption,
  resume reports state and commands instead of continuing.
- Local-model work mostly lives in `.orbit/local*/` (`codex exec --json`
  streams): `orbit local` and `local_next_task.py` pass `--ephemeral`, so
  `~/.codex/sessions` has almost no LM Studio sessions. Claude Code transcripts
  are pruned after about 30 days, so the store keeps per-session counts.
- Sections 13–15 introduce retained personal knowledge, machine-readable access
  for other consumers, and learning recommendations. The user confirmed both
  personalisation and recommendations for their own learning (Q42). Web/app
  support means a small reusable abstraction with endpoints in mind, without
  added complexity (Q43); UI, server and hosting are deferred.
- Observations, knowledge revisions and repository changes are separate results.
  Repeated assistant suggestions do not prove effectiveness. Knowledge keeps
  scope, lineage, counter-evidence and feedback; equivalent items retain the same
  identity across lenses. Explicit user corrections supersede the prior view in
  scope; dismissed interpretations cannot reappear under a new identifier.
- Consumer feedback references the knowledge revision used. The next in-scope
  dream reassesses it and records a conclusion or insufficient evidence. Unknown
  scope is not global; default retrieval omits contested knowledge and deferred
  or addressed learning recommendations. Web transport and schema encoding are
  design choices, not requirements selected by the portability boundary.
- The knowledge/portability revision passed a critic review followed by two
  native peer reviews. External Codex timed out and Kiro was unavailable; do not
  describe that as a completed external review. The current 98-criterion draft
  awaits requirements approval before design and rune task planning.
- Alignment with orbit apsis and the screw (2026-11-05): section 3 is delivered
  by orbit's `apsis-shared-json` (provider and client origin recorded,
  never classified; recorded entry ids, no source positions) and
  `apsis-lmstudio-logs` (responses and diagnostics unattributed). Both are merged on orbit main
  (ed81863, 2026-11-13), so section 3 has no open orbit dependency.
  Dreaming classifies local/cloud and interactive/automated itself (2.2, 2.9).
  The screw (`~/repos/screw`) consumes 14.1, 14.2 and 14.5–14.8: it may start
  dreams, registers its sessions so their prompts are not counted as the user's,
  and marks entries that relay the user's own words. Most recent headless Claude
  sessions are tool-driven, which is why 2.9 defaults sources without an origin
  to non-interactive.
