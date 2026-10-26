# Requirements: Dreaming

## Introduction

Dreaming turns evidence from past agent sessions into knowledge about the user's preferences, effective workflows and learning opportunities, so tools can personalise their behaviour. It builds on existing FOSS, with OpenClaw's dreaming concept informing a cycle of evidence gathering, reflection, selective adoption and evaluation. agentic-coding supplies the initial integrations; the knowledge and dream operations are usable by other tools. Each dream retains learning, writes an HTML report, and can propose, merge and deploy repository changes when its configured checks pass.

## Non-Goals

- Detecting idle time or scheduling dreams itself; tools the user runs may start dreams through [14.1](#14.1).
- Running workers in parallel; deferred until after the first version.
- Starting the LM Studio server, or downloading or loading models.
- Editing harness-native memory stores (Claude Code auto memory, LM Studio presets).
- Writing to the knowledge vault or depending on capture-knowledge.
- Reading LM Studio chat conversations.
- Reading interactions that leave no local record, such as web chat apps.
- Pushing branches or merges to any remote.
- Per-project privacy routing; every transcript is eligible for every backend.
- An interactive web UI, hosted service or multi-user accounts; machine-readable access is in scope.
- Live coaching, lesson delivery or a curriculum; dreams read finished sessions only.
- Synchronising or merging divergent knowledge stores.
- Protecting checks or restrictions from modification by dreaming itself; the user controls where dreaming is appropriate for sensitive work.

## Operating Assumptions

Dreaming runs as the user's trusted automation. The user chooses repositories, session sources and backends suited to the material; output scans and role tool lists support that choice and do not contain a hostile agent. Each run uses a snapshot of its configuration and the program version it started with; adopted changes to either apply from the next run. Test files, Makefiles and restrictions are ordinary improvement targets.

An observation records source evidence. A knowledge item is a revisable interpretation supported by observations (a preference, lesson, workflow pattern or learning opportunity). Repository changes are one use of knowledge. Other consumers need no agentic-coding checkout or installed skills.

## Requirements

### 1. Starting and Scoping a Dream

**User Story:** As the user, I want to start a dream with one command and control how much it reads, so that I decide when and how much dreaming spends.

**Acceptance Criteria:**

1. <a name="1.1"></a>The system SHALL start a dream only on an explicit request through a terminal, harness skill or the machine-readable operation in [14.1](#14.1), and the run record SHALL name the requester supplied with the request, or `user` when none is supplied; the dream SHALL keep running after the invoking client disconnects.  
2. <a name="1.2"></a>The system SHALL accept configurable and per-run limits for sessions read, wall-clock time (counted only while the dream process runs) and total model tokens (counting every role, retry and fallback), and SHALL reserve a configurable share of the token budget for review and authoring. WHEN a total limit is reached, it SHALL stop model work, save progress, and end the run as budget-exhausted with a report needing no further model calls.  
3. <a name="1.3"></a>WHEN no selection is given, the system SHALL select unread sessions and unread additions to previously processed sessions, newest first, until the budget is reached.  
4. <a name="1.4"></a>WHEN the user supplies a date range, a project filter, or a request to re-read under current lens versions, the system SHALL select the matching sessions, including ones processed before.  
5. <a name="1.5"></a>The system SHALL exclude from selection the sessions and LM Studio requests of the dream in progress, and sessions modified within a configurable recent window. Sessions from earlier dreams SHALL be eligible, but SHALL be read only for the dream's own behaviour and not as evidence about the sessions they processed.  
6. <a name="1.6"></a>IF a dream is already running, THEN a second invocation SHALL exit naming the running dream and change no state. IF an interrupted dream has no running process and has remaining budget or was interrupted during adoption, THEN the next invocation SHALL resume it, report the retained selection and overrides, and reject any override other than backend choices. Completed and budget-exhausted runs SHALL NOT be resumed automatically.  
7. <a name="1.7"></a>The system SHALL provide a dry run that lists the sessions it would read, the backend for each role and the budget, without calling any model or changing any state.  

### 2. Session Sources

**User Story:** As the user, I want dreams to read sessions from every tool I use with a model, so that patterns across tools are visible.

**Acceptance Criteria:**

1. <a name="2.1"></a>The system SHALL read sessions from Claude Code, Codex, Copilot, Kiro CLI, Kiro IDE, orbit runs (including runs from `local-next-task`) and LM Studio server logs, and SHALL accept sessions from other locally recorded sources through the versioned session contract in [3.4](#3.4), including work outside software development.  
2. <a name="2.2"></a>The system SHALL attribute each session with harness, model (per entry where the source records changes, otherwise the session's first recorded model), provider, whether the model ran locally (classified from the recorded provider and model by configured rules, otherwise unknown), project (a worktree counted as its parent repository), work domain, workflow (from a registration under [14.8](#14.8), otherwise unknown) and start time; IF a source cannot supply a field, THEN the field SHALL be recorded as unknown and the session still processed.  
3. <a name="2.3"></a>The system SHALL assign a session's work domain from configured source or project mappings; IF no mapping applies, THEN its sessions SHALL be processed under an unassigned domain and the unmapped source or project SHALL be listed in the report; a missing repository SHALL NOT prevent processing.  
4. <a name="2.4"></a>WHEN the same interaction appears in more than one source, such as a Codex session served by LM Studio and LM Studio's server log, matched by a recorded correlation identifier such as the client thread identifier, the system SHALL process it once, taking content from the harness or tool session and server metadata from the log, or the log's content marked truncated where the log holds the only copy; server warnings and errors the log does not attribute to a request SHALL appear in the report only and SHALL NOT be attached to a session.  
5. <a name="2.5"></a>WHEN a processed session has grown under unchanged lens versions and no explicit reread was requested, the system SHALL read only the new part; explicit rereads under [1.4](#1.4) SHALL be able to revisit earlier content.  
6. <a name="2.6"></a>WHEN a session is larger than the context available to the role reading it, the system SHALL split it into consecutive parts that each fit and process them as one session.  
7. <a name="2.7"></a>IF a session cannot be parsed, THEN the system SHALL record it as skipped with the reason, show it in the report, and continue.  
8. <a name="2.8"></a>The system SHALL support dreams scoped to the current repository, a named repository or a workflow; a scoped dream SHALL select only matching sessions and applicable lenses, and propose only improvements relevant to that scope.  
9. <a name="2.9"></a>The system SHALL attribute a session's prompts to a tool or an unknown author, and SHALL NOT count them as user statements, preferences or examples of the user's writing, WHEN the session was registered under [14.8](#14.8), was started by a dream, or comes from a source or client origin that configuration marks non-interactive; entries a registration identifies as quoting the user remain user statements. Codex exec streams and LM Studio sessions not matched under [2.4](#2.4) SHALL be non-interactive by default. An unmapped origin SHALL count as interactive and be listed in the report. Tool results and outcomes SHALL remain usable evidence. Dream-started sessions SHALL follow [1.5](#1.5).  
10. <a name="2.10"></a>WHEN a registration under [14.8](#14.8) arrives for a session already read, the system SHALL reclassify that session's prompts under [2.9](#2.9) and queue affected knowledge for reassessment under [11.7](#11.7). Until reassessment records its conclusion, each affected item SHALL be marked pending reassessment, and retrieval under [14.2](#14.2), [14.6](#14.6) and [14.7](#14.7) SHALL show the mark.  

### 3. Shared Session Reader (apsis)

**User Story:** As the user, I want the reading of every session format to live in apsis, so that orbit, `apsis serve`, dreaming and any other tool share one reader.

Delivered by orbit specs `apsis-shared-json` and `apsis-lmstudio-logs`, merged on orbit main (`4bf9776`).

**Acceptance Criteria:**

1. <a name="3.1"></a>apsis SHALL list and render LM Studio API requests from its server logs, grouped into sessions by recorded client thread identifier, marking content the log truncated as truncated, keeping responses, warnings and errors the log does not attribute to a request as unattributed, and excluding embedding and model-management requests.  
2. <a name="3.2"></a>apsis SHALL list and render Codex `exec --json` event streams from configured directories; these streams record no prompt.  
3. <a name="3.3"></a>apsis SHALL record each session's model provider and client origin exactly as the source records them, without classifying sessions as local, cloud, interactive or automated.  
4. <a name="3.4"></a>apsis SHALL provide a versioned, machine-readable session representation with stable session identifiers; ordered entries carrying role and tool attribution and any identifier the source records; the recorded provider, model, project, start time, client origin and correlation identifiers; and explicit markers for missing, truncated or incomplete content.  
5. <a name="3.5"></a>apsis SHALL list sessions across all projects in one call, with the project path of each.  

### 4. Roles and Context

**User Story:** As the user, I want each model call to see only what its task needs while the dream keeps the cross-session view, so that patterns across workflows surface without overloading any one context.

**Acceptance Criteria:**

1. <a name="4.1"></a>The dreaming program SHALL hold the dream's control flow and state on disk, so that a dream can resume and move between backends; each model call SHALL return output in a defined structure for its role.  
2. <a name="4.2"></a>The system SHALL provide these roles, each with its own backend configuration: reader (one batch of sessions to observations), reviewer (observations and retained knowledge to proposed knowledge revisions, candidate improvements and research questions), researcher (one question to findings with sources), and author (one candidate and its research to a learning recommendation or proposed repository change, including current files when relevant).  
3. <a name="4.3"></a>Each call SHALL receive only the inputs its role needs, within its configured context limit; the reviewer SHALL receive bounded observation and pattern summaries with evidence identifiers and SHALL NOT receive full transcripts.  
4. <a name="4.4"></a>Each call SHALL expose only an explicit list of tools and skills for its role (none for readers and reviewers) and SHALL load no other user or project instructions, skills, hooks or MCP servers. No role SHALL be able to launch other agents, including devtools' codex-agent and gemini-agent. The dreaming program SHALL own call scheduling and budget accounting.  
5. <a name="4.5"></a>The reviewer SHALL treat an inferred pattern as eligible for active knowledge or a proposed improvement only when its observations come from at least a configurable number of distinct sessions; explicit user preferences follow [13.3](#13.3), and a finding from inspecting current files, such as a broken reference, SHALL be a candidate on that evidence alone, citing repository, revision, file and location.  
6. <a name="4.6"></a>Researchers SHALL be able to read target repositories, consult pull-request review threads and search and fetch web sources through devtools on every supported tool-using backend, including a harness using LM Studio. Configured knowledge folders MAY be read as additional sources; missing folders SHALL be reported and skipped without blocking research.  
7. <a name="4.7"></a>IF a call's output does not match its role's structure, THEN the call SHALL be retried once; IF it fails again, THEN its input SHALL be recorded as failed, listed in the report, and not retried by later dreams unless selected again under [1.4](#1.4).  
8. <a name="4.8"></a>Calls SHALL run one at a time.  

### 5. Backends and Failures

**User Story:** As the user, I want any role to run on Claude Code, Codex or a local LM Studio model, so that dreaming isn't tied to one tool and keeps going when one fails or is limited.

**Acceptance Criteria:**

1. <a name="5.1"></a>The system SHALL support Claude Code and Codex as role harnesses, each using its cloud provider or LM Studio, chosen per role in configuration and overridable per run; tool-using roles SHALL run through a harness, while direct LM Studio calls MAY serve tool-free roles.  
2. <a name="5.2"></a>The configuration SHALL allow an ordered fallback list of backends for each role, and the system SHALL size each role's inputs for the smallest context in that list.  
3. <a name="5.3"></a>WHEN a backend call fails, the system SHALL retry it once; IF it fails again, THEN the system SHALL record the raw error, treat that backend as unavailable for the rest of the run, and continue on the role's next backend; IF none remains, THEN it SHALL save progress, write the report for completed work, and exit with a status distinct from success and failure.  
4. <a name="5.4"></a>WHEN an interrupted dream is resumed, the system SHALL keep its selection, remaining budget and per-run overrides, SHALL NOT repeat completed reading or research, and SHALL accept new backend choices per role. Backends marked unavailable under [5.3](#5.3) SHALL become eligible again; every new or re-eligible backend SHALL be checked under [5.5](#5.5), and remaining inputs sized under [5.2](#5.2). The user SHALL be able to discard the dream instead.  
5. <a name="5.5"></a>IF a configured backend is unavailable or cannot supply a role's tools and configuration isolation, THEN the system SHALL report the reason at start and in dry run and continue with compatible fallbacks; IF no compatible backend remains, THEN it SHALL report the affected role as unavailable without starting that role.  
6. <a name="5.6"></a>The system SHALL record the backend and model behind each observation, finding and change, and the time and tokens used per backend and model.  
7. <a name="5.7"></a>A harness using LM Studio SHALL receive its role's permitted devtools tools from the shared MCP definitions, without inheriting the full server tool list or requiring a separate LM Studio MCP configuration.  
8. <a name="5.8"></a>Each model call a dream makes SHALL leave a session record where the shared session reader finds it, identifiable as belonging to that dream from the record itself or from the dream's run record ([7.5](#7.5)); for direct LM Studio calls, the server-log entry SHALL suffice even when truncated, and each such call SHALL send the dream's run identifier as its client thread identifier.  

### 6. Observation Store

**User Story:** As the user, I want findings kept between dreams, so that patterns build up over many dreams and no session is processed twice.

**Acceptance Criteria:**

1. <a name="6.1"></a>The system SHALL assign an evidence identifier to each session observation or file finding, recording project, work domain, date, lens identifier and version, and producing backend and model; session observations SHALL carry a supporting quote, session identifier, harness and source location (a location identifying one entry, with the representation version from [3.4](#3.4)), while file findings SHALL carry repository, revision, path and location.  
2. <a name="6.2"></a>The system SHALL verify each observation's quote against its source before redacting credentials and tokens from stored and displayed copies; IF the quote does not match at its recorded location, THEN it SHALL reject the observation and count it in the run statistics.  
3. <a name="6.3"></a>Processing a session again under unchanged lens versions SHALL NOT create duplicate observations.  
4. <a name="6.4"></a>The store SHALL reside outside every git repository and be readable only by the user's account.  
5. <a name="6.5"></a>Each pattern SHALL keep a persistent identifier across dreams, and the store SHALL record which observations were assigned to it.  
6. <a name="6.6"></a>The store SHALL keep per-session pattern counts after the source transcript is deleted by its harness.  
7. <a name="6.7"></a>The store SHALL record, for each pattern, its changes with their commits, when each was applied, and whether each was reverted.  

### 7. Lenses, Instructions and Configuration

**User Story:** As the user, I want focus areas and improvement instructions in plain files I can edit, so that I steer what dreams look for without changing code.

**Acceptance Criteria:**

1. <a name="7.1"></a>The system SHALL read lenses from an editable instruction file, where each lens states what to look for, which kinds of change it may propose, and optionally which work domains, projects or workflows it applies to; each lens SHALL carry a version, and adding or changing a lens or a work domain SHALL require editing configuration only.  
2. <a name="7.2"></a>The initial lenses SHALL cover: explicit preferences and corrections; approaches associated with successful outcomes; recurring requests for explanation or help; MCP server and tool use; skill use, including skills invoked then abandoned, misfiring, or missing; Xcode build, run and preview workflows; points where a coding concept, tool error or build step stalled the user; manual steps repeated across sessions that a Make target, script or skill could perform; deliverables of the same kind (reports, agreements, reviews, runbooks) repeatedly corrected by hand; context spent on instructions and tool schemas; and broken or inconsistent references in skills, rules and configuration.  
3. <a name="7.3"></a>The system SHALL snapshot its active configuration — auto-apply, budgets, thresholds, tool lists, commands and scan rules — at run start from the default branches or configured external files, SHALL record the snapshot used in the run, and SHALL complete the run, including any resumed part, on the program version it started with, even when adoption changes dreaming's own code. The names list used by [9.12](#9.12) SHALL be read only from configured files outside every repository.  
4. <a name="7.4"></a>A dream MAY propose changes to any workflow in scope, including the specification process and dreaming itself, and to its lenses, instructions, configuration and tooling; changes within target repositories SHALL follow the ordinary adoption rules and affect the next dream, while changes to external configuration SHALL be reported as suggestions for the user to apply.  
5. <a name="7.5"></a>Each dream SHALL record its run — selection, budget use, backend use, failures, rejected observations, withheld changes and outcomes — and the reviewer of later dreams SHALL receive these records as evidence about dreaming itself.  

### 8. Tooling Inventory and Context Weight

**User Story:** As the user, I want to see which tools and instructions my sessions actually use and what they cost in context, so that I can cut what bloats local-model calls and add what's missing.

**Acceptance Criteria:**

1. <a name="8.1"></a>For each harness, the system SHALL report the MCP servers and tools configured, how often each was used in the sessions read, which were never used, and which observed sessions show a need that a configured or available tool could have met.  
2. <a name="8.2"></a>For each harness and backend, the system SHALL report available measurements of context consumed before the first user prompt by instructions, skill listings and tool schemas, name the largest identifiable contributors, and label estimates and unavailable values; WHEN measured or estimated consumption exceeds a configurable share of a known context window, THEN it SHALL flag the case.  

### 9. Changes and Adoption

**User Story:** As the user, I want each dream's changes isolated, checked and applied automatically when the configured conditions hold, so that improvements land with little friction and are easy to undo.

**Acceptance Criteria:**

1. <a name="9.1"></a>The system SHALL write a dream's changes to one branch per repository with changes, named by dream, based on that repository's current default branch, and SHALL NOT modify any working tree the user has checked out while writing them.  
2. <a name="9.2"></a>Each repository change SHALL be one commit and SHALL cite the evidence identifiers it rests on, whether session observations or file findings.  
3. <a name="9.3"></a>WHERE an existing skill supports an unattended step within the role's tool list, the dream SHALL reuse it; IF a skill requires interaction, THEN the dream SHALL defer that step and report the limitation, and MAY propose a separate skill improvement.  
4. <a name="9.4"></a>The system SHALL write proposed file changes only in configured target repositories; retained knowledge and user feedback SHALL be written to the private store under [6.4](#6.4), and knowledge folders used for research SHALL remain read-only.  
5. <a name="9.5"></a>The system SHALL run each repository's configured generate commands on the dream branch, so that the branch contains every derived file its changes affect.  
6. <a name="9.6"></a>The system SHALL run every configured lint and test command on the result of merging the dream branch into the current default branch, in a working copy separate from the user's, using that result's Makefiles, tests and check implementations; any failing command SHALL block auto-apply, regardless of whether it also fails on the default branch.  
7. <a name="9.7"></a>WHERE auto-apply is enabled — it SHALL be enabled in the user's configuration — the system SHALL merge a repository's dream branch into its default branch as one merge commit in the user's checkout and run its deploy commands there, only WHEN every configured check passes, the checkout is on the default branch, has no uncommitted tracked changes or untracked files the merge would overwrite, and its HEAD has not moved since the checks ran.  
8. <a name="9.8"></a>IF a repository has no configured lint and test commands, THEN its auto-apply conditions SHALL be treated as not met.  
9. <a name="9.9"></a>IF deploy commands fail after a merge, THEN the system SHALL revert the merge, attempt deployment of the restored version, and report both outcomes; IF recovery fails, THEN it SHALL stop adoption and identify the repository requiring manual recovery.  
10. <a name="9.10"></a>WHEN changes declare dependencies across repositories, the system SHALL start adoption only when every linked repository meets its conditions; IF any linked merge or deployment fails, THEN it SHALL attempt to revert every applied member and redeploy restored versions, report each repository's resulting state, and stop adoption if recovery fails.  
11. <a name="9.11"></a>IF auto-apply is disabled or its conditions are not met for a repository, THEN that repository's changes SHALL remain on the dream branch and the report SHALL state which condition was not met.  
12. <a name="9.12"></a>For a repository configured as public, the system SHALL scan every commit and commit message for transcript text longer than a configurable length that is not already in the repository, credentials and tokens, and names listed in configuration; changes in such repositories SHALL cite evidence by identifier only; IF a change fails the scan, THEN it SHALL NOT be committed, SHALL be saved as a patch outside every repository, and SHALL be listed in the report as withheld.  
13. <a name="9.13"></a>WHEN the user reverts a change on the default branch, the system SHALL record it as rejected and propose its pattern again at most once, only on observations newer than the revert. Reverts under [9.9](#9.9)–[9.10](#9.10) and reverts of adoptions reported under [9.15](#9.15) SHALL be recorded as failed adoption, not user rejection.  
14. <a name="9.14"></a>IF a pattern already has a change on an unmerged branch from an earlier dream, THEN the dream SHALL NOT propose another change for it, and the report SHALL list unmerged branches from earlier dreams.  
15. <a name="9.15"></a>WHEN a dream resumes after an interruption that occurred after its first merge into a user checkout, it SHALL make no further merges or deployments, SHALL report each merged repository's state with the commands to finish or undo its adoption, and SHALL report unmerged repositories under [9.11](#9.11) with the interruption as the reason.  

### 10. Dream Report

**User Story:** As the user, I want one HTML page per dream opened in my browser, so that I can see what changed and how to adopt or undo it.

**Acceptance Criteria:**

1. <a name="10.1"></a>WHEN a dream ends, whether complete or partial, the system SHALL write an HTML report outside every repository and return its location; terminal and skill invocations by the user SHALL open it in the default browser unless disabled, and an unavailable browser SHALL NOT fail the dream.  
2. <a name="10.2"></a>The report SHALL list, per repository, each change with its evidence and whether it was applied, followed by the commands to run: for unapplied changes, `git -C <repo> merge --no-commit <branch>`; for applied ones, a revert command per change and one for the whole merge. Each command SHALL be followed by the repository's configured generate commands before the merge or revert is committed, and then by its deploy commands.  
3. <a name="10.3"></a>The report SHALL show run statistics: sessions read, split, skipped and failed with reasons; observations accepted and rejected; patterns; changes applied, waiting and withheld; budget used; time and tokens per backend and model; and whether the dream was partial.  
4. <a name="10.4"></a>The report SHALL include the tooling inventory and context weight from [section 8](#8-tooling-inventory-and-context-weight), unmerged branches from earlier dreams, and changes to checks, restrictions or tool lists.  
5. <a name="10.5"></a>The report SHALL match the layout and styling of the existing HTML review pages built by `scripts/build_review_html.py`.  
6. <a name="10.6"></a>The report SHALL distinguish retained knowledge revisions, learning recommendations and repository changes, including deferred or contested items and their reasons; IF a dream produces no repository changes, THEN it SHALL say so without treating retained learning as no result.  

### 11. Measuring Effect

**User Story:** As the user, I want later dreams to check whether an applied change reduced the friction it targeted, so that improvement is measured rather than assumed.

**Acceptance Criteria:**

1. <a name="11.1"></a>For each applied change, the system SHALL report its pattern's observation count and the number of sessions read within the pattern's lens scope, before and after the change was applied, as raw numbers labelled as association rather than proof of effect.  
2. <a name="11.2"></a>IF a pattern recurs at or above its pre-change rate after a configurable number of later sessions within its lens scope, THEN the reviewer SHALL treat it as a candidate again with the earlier change as context, up to a configurable maximum number of changes per pattern.  
3. <a name="11.3"></a>The reviewer SHALL rank eligible patterns using recurrence across distinct sessions, recency and, where present, recurrence across projects; the ranking settings SHALL be configurable and each candidate's position and supporting signals SHALL appear in the report.  
4. <a name="11.4"></a>WHEN a candidate overlaps an earlier pattern or improvement, THEN the reviewer SHALL propose keeping, refining or superseding it under the existing pattern identifier, with its history retained, instead of creating a duplicate.  
5. <a name="11.5"></a>Before authoring a change, the system SHALL verify that its cited evidence remains available and supports the candidate against the current target files; IF support cannot be verified, THEN it SHALL defer the candidate with a reported reason.  
6. <a name="11.6"></a>The report SHALL show the outcomes of evidence gathering, reflection, candidate selection and adoption, including reasons candidates were deferred or discarded; dream summaries SHALL NOT count as independent evidence for the underlying patterns they describe.  
7. <a name="11.7"></a>WHEN knowledge has received feedback under [14.5](#14.5), the next dream whose scope includes that item SHALL reassess the affected revision against that feedback and independent evidence, recording whether its advice, confidence or status changed and why; missing outcome evidence SHALL be reported as insufficient to assess effect.  

### 12. FOSS Foundation

**User Story:** As the user, I want dreaming to build on existing FOSS, so that it benefits from working implementations and avoids maintaining duplicate infrastructure.

**Acceptance Criteria:**

1. <a name="12.1"></a>The implementation SHALL reuse or extend existing FOSS for session reading and model/tool execution; custom functionality SHALL address gaps identified in the design rather than duplicate supported capabilities.  
2. <a name="12.2"></a>Before implementation, the design SHALL assess OpenClaw's dreaming code as well as its concepts, identify which reflection and consolidation capabilities can be reused or adapted, and explain any choice to implement an equivalent capability separately.  
3. <a name="12.3"></a>For each reused or adapted component, the design SHALL record its upstream source, inspected revision, licence, integration boundary and maintenance approach, including required attribution.  

### 13. Refining Evidence into Personal Knowledge

**User Story:** As the user, I want dreams to retain supported, revisable knowledge about my work, so that personalisation improves across sessions and tools.

**Acceptance Criteria:**

1. <a name="13.1"></a>Each observation SHALL distinguish user statements, prompts written by tools or unknown authors under [2.9](#2.9), assistant suggestions, tool results and external research, and label an outcome as user-confirmed, check-confirmed, failed or unknown with its evidence; an assistant's claim of success SHALL NOT count as confirmation or a user preference.  
2. <a name="13.2"></a>Each knowledge item SHALL retain a stable identifier, revision history, kind, scope, supporting and contradicting evidence identifiers, latest supporting date, producing lens and model, confidence with its stated basis, and a status of candidate, active, contested, superseded or dismissed; scope SHALL identify applicable domains, projects or workflows, an explicitly global application, or unresolved scope, using the source context when no scope is stated and never treating missing scope as global.  
3. <a name="13.3"></a>WHEN a verified user statement explicitly declares a preference or corrects retained knowledge, the system SHALL apply it within its scope without requiring recurrence; other interpretations SHALL remain candidates until [4.5](#4.5) is met, and an active claim that an approach worked SHALL require at least one user-confirmed or check-confirmed successful outcome for that approach in that scope rather than recurrence alone; a confirmed failed outcome SHALL NOT satisfy that requirement and SHALL count as evidence against the approach.  
4. <a name="13.4"></a>WHEN evidence conflicts within the same scope, the system SHALL retain both sides and mark the item contested unless an explicit user correction or resolution covers that conflict; such a resolution SHALL supersede the earlier interpretation within its scope and SHALL NOT be undone by later inferred evidence; a preference confined to one scope SHALL NOT become global merely through recurrence.  
5. <a name="13.5"></a>The user SHALL be able to correct an item, change its scope or dismiss it with a reason; the system SHALL retain that feedback in its history and apply it to later refinement and retrieval, and SHALL NOT reactivate a dismissed interpretation without explicit user instruction.  
6. <a name="13.6"></a>WHEN several observations or derived items trace to the same interaction, the system SHALL count that interaction once as support, including when quoted by a report, another agent or a later dream; research findings SHALL remain distinguishable from evidence about this user's behaviour.  
7. <a name="13.7"></a>WHEN a source is removed or changed, the system SHALL retain accepted redacted evidence, knowledge history and per-session counts, mark affected source references unavailable or changed, and SHALL NOT present them as freshly verified against that source.  
8. <a name="13.8"></a>A dream SHALL retain eligible knowledge and record promotions, revisions, conflicts and dismissals even when no repository is configured or no repository change is authored or adopted; each retained revision SHALL identify its originating run or user feedback.  
9. <a name="13.9"></a>WHEN refinement finds an equivalent interpretation in the same scope, it SHALL revise the existing knowledge item, preserving its corrections, dismissals and history across lenses and rereads; knowledge about an existing pattern SHALL reference its persistent identifier under [6.5](#6.5), and a new identifier SHALL NOT bypass prior feedback.  

### 14. Use Beyond agentic-coding

**User Story:** As a tool builder, I want to consume personal knowledge and control dreams independently of agentic-coding, so that terminal tools, agents and a web frontend can share the same learning.

**Acceptance Criteria:**

1. <a name="14.1"></a>The system SHALL offer versioned, machine-readable operations to start, inspect, resume and discard a dream, retrieve its report, record knowledge feedback, search and recall knowledge and register sessions, returning stable run or item identifiers, progress and explicit error or completion states without requiring an interactive harness or browser.  
2. <a name="14.2"></a>Given any of a domain, project and workflow and a limit in estimated tokens, the system SHALL return applicable active knowledge from retained revisions within that limit, stating the estimate used and whether items were left out, with each item's content, identifier, revision, scope, evidence references and confidence basis; candidate, contested, superseded, dismissed, unresolved-scope and out-of-scope items, and deferred or addressed learning recommendations, SHALL appear only when explicitly requested, and no full transcript SHALL be required to consume the result.  
3. <a name="14.3"></a>The user SHALL be able to export retained knowledge, redacted evidence, history and feedback in a versioned, machine-readable form and import it into a fresh store without an agentic-coding checkout, preserving identifiers, scopes, source-availability markers and dismissed states; importing the same export again SHALL NOT duplicate records.  
4. <a name="14.4"></a>With an equivalent configured source and backend, the system SHALL complete a dream and retain knowledge from outside an agentic-coding checkout, without its installed skills, generation or sync commands, or any target repository; unavailable optional integrations SHALL be reported without blocking knowledge refinement.  
5. <a name="14.5"></a>WHEN a consuming tool reports the knowledge revisions behind an action (each marked cited or only present in the prompt) with the outcome or a user correction, the system SHALL retain the feedback with those revisions, the run or session reference, and the outcome's basis (user-confirmed, check-confirmed with the check named, or unknown). An outcome against present-only revisions SHALL count as association, not confirmation. Delivery alone SHALL NOT count as successful use or independent evidence. Feedback repeating an earlier feedback identifier SHALL change nothing.  
6. <a name="14.6"></a>Given query text, a scope as in [14.2](#14.2) and a limit in estimated tokens, the system SHALL return matching applicable knowledge items with identifier, revision and a summary within that limit, applying the default filtering of [14.2](#14.2).  
7. <a name="14.7"></a>Given a knowledge item identifier, the system SHALL return that item's current retained revision with the fields listed in [14.2](#14.2) and its status, or an explicit not-found state.  
8. <a name="14.8"></a>WHEN a tool registers sessions, each given as a source with a harness session identifier or as a file in the representation from [3.4](#3.4), with the tool's name, a run reference, and any correlation identifier, workflow, project and entries quoting the user's own words, the system SHALL make them eligible for selection under [1.3](#1.3), apply that workflow and project under [2.2](#2.2), and attribute their prompts under [2.9](#2.9); registering a session again with the same details SHALL change nothing.  

### 15. Personal Learning Recommendations

**User Story:** As the user, I want evidence-based learning opportunities from my own work, so that I can choose what to learn alongside improvements to my tools.

**Acceptance Criteria:**

1. <a name="15.1"></a>WHEN repeated explicit requests for help or explanation meet [4.5](#4.5), or the user states a learning goal, the system SHALL retain a scoped learning recommendation with its supporting evidence, a suggested next step and the outcome it would help achieve; tool failures or assistant mistakes alone SHALL NOT be treated as evidence that the user lacks a skill.  
2. <a name="15.2"></a>The report and knowledge retrieval SHALL distinguish learning recommendations from automation opportunities and preferences, and SHALL identify any researched explanation or resource separately from observed evidence.  
3. <a name="15.3"></a>The user SHALL be able to dismiss, defer until a chosen date or explicit resumption, or mark a learning recommendation addressed; later dreams SHALL retain that disposition, make a deferred item eligible again only when its deferral ends, and SHALL NOT infer learning or mastery merely because an explanation was delivered or the pattern stopped appearing.  

---

## Design Handoff

- Assess OpenClaw's dreaming code, not only its concepts; pin inspected revisions and record licences, attribution and update duties (12).
- Verify per harness version that each harness/provider pair supplies the required tools and configuration isolation. Probe (2026-11-04): Codex's default prompt includes `~/.codex/AGENTS.md`; an empty `CODEX_HOME` drops it but still lists six skills and loses `auth.json`; `--ignore-user-config` is untested. Claude's `--setting-sources "" --strict-mcp-config` keeps the login; skill loading under it is untested. Isolation must not hide transcripts from apsis (5.8).
- Use one retry policy for transport failures and malformed output, without nested loops.
- Define token accounting when a harness omits usage, and how context estimates are labelled.
- Define insufficient evidence for before/after rates, including file-only findings and a zero-session baseline.
- Define what discarding a dream does to its branches, merges and run records, and how apsis matches one interaction across sources (2.4).
- Specify knowledge and session encodings, compatibility errors, retrieval ordering within a limit, scope matching and confidence representation, with no frontend or agentic-coding paths.
- Test the portable boundary with a source, backend and fresh store outside agentic-coding; exchange keeps evidence lineage and user dispositions.
- Decide what a later dream (not a 9.15 resume) may do in a repository an earlier dream merged but did not finish deploying. Record completed and outstanding adoption steps durably so a completed merge is distinguishable from completed adoption.

## Status

Requirements approved 2026-11-07. Design and implementation have not started. Section 3 is delivered on orbit main at `4bf9776` (see `decision_log.md` Q65).
