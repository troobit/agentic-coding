# REA Feature Discovery Verification

Verified on 2026-10-26 against the implemented skill and `rea-agents@6.7.0`.

## Format, integration, and repository checks

- Skill-creator `quick_validate.py`: passed.
- Feature spec audit: no findings; all four rune tasks complete, with valid
  requirement references and stable task identifiers.
- `make test`: passed both repository unittest discovery commands.
- `make generate` restored the already-missing generated Copilot instructions;
  `make lint` then passed shellcheck and generated-output drift checks.
- `make sync-codex` linked the skill and registered the canonical REA server.
  A second sync reported no changes and preserved configuration bytes exactly.
- The parsed Codex config retained GitHub, Terraform, and Transit disabled.
- A fresh Codex app-server `skills/list` discovered `rea-feature-discovery` with
  `enabled: true`, its expected source path, and no skill discovery errors.
- Native `mcpServerStatus/list` discovered `rea` with 207 tools.
- REA `mcp doctor --json` returned `healthy: true`: production stdio,
  protocol `2025-11-25`, package `6.7.0`, all 207 tools and six prompts,
  matching package/catalog identity, and a successful target-free `binary_session`.

These checks establish the integration, not access to a particular installed app
or readiness of optional native decompilers.

## Independent forward tests

Three independent agents received the skill path, a realistic request, and
synthetic/raw fixture state. They were not given expected findings. Each could
write only in its own temporary destination, could not change live configuration
or contact the real user, and recorded needed approvals in its handoff.

### Accessible packaged application

Input: a synthetic NoteBox `1.2.0` ASAR containing a manifest and this routine:

```javascript
exports.search = function search(notes, query) {
  const prefix = query.trim().toLowerCase();
  return notes.filter(note => note.title.toLowerCase().startsWith(prefix));
};
```

The agent used the pinned REA CLI because its current session lacked MCP tools.
Analysis and extraction succeeded. It retained complete REA result envelopes,
invocation records, archive/member hashes, and extracted input beside destination
research. It distinguished the observed routine from inferred matching behaviour,
and did not claim evidence of UI integration, persistence, or offline restart.
REA's complete application graph still reported unknown semantic coverage and
16 explicit unknowns, which the handoff preserved.

The destination had no existing spec or implementation. Research stayed under
its `docs/research/` convention, and planning stopped at Starwave scope-route
approval. No speculative spec folder, tasks, or product code was created.

### App installed only on a phone

Input: user-supplied Libre build `1.4.2.2128` on iOS `26.7.1`, with no local
artifact, screenshots, runtime connection, or credentials. The synthetic
destination already had graph and ingestion specs.

The agent selected the existing graph spec and wrote its research there. It
labelled version/platform as user-supplied, documented the separate source-access
and session-connectivity gaps, and treated public Abbott documentation as
context whose correspondence to this build was unverified. It obtained no REA
Evidence and made no claim to have observed app interactions. It preserved
requirement `1.1`, recorded the missing interaction evidence/adoption decisions,
and stopped at the existing requirements review stage.

### Existing spec with an expired evidence reference

Input: an existing offline-search spec, requirement `1.1`, proposed decision D1,
`decision_mode: overwrite`, an unavailable session-only observation from
NoteBox `1.0`, and a user-supplied installation of `2.0` without inspectable input.

The agent kept the existing spec, preserved the requirement file byte-for-byte,
and retained the old observation's version/date while marking its evidence
unavailable. It did not transfer the old claim to `2.0`. D1 was revised in place,
not superseded, and remained proposed pending evidence or a destination choice.
The handoff identified affected downstream design, unanswered questions, and the
existing requirements approval boundary. No task file or implementation was added.

## Artifacts and limits

The isolated workspaces were created under a temporary `rea-forward-*` directory.
The recorded summaries above preserve the results; temporary raw exports are not
installed skill resources or production evidence. Parent verification parsed the
generated JSON and checked destination ownership, the absence of premature task
files, and preservation of the original requirement and decision identity.

No real Libre account, sensor, patient data, or installed iPhone app was accessed.
Existing sessions may need reconnection to load the newly registered REA tools;
the tested CLI fallback remains available within an authorised investigation.
