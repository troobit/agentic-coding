# Codex Sync Decision Log

## Decision 1: Give Codex a separate sync entry point

**ID:** 1
**Date:** 2026-10-23
**Status:** accepted

### Context

Claude sync also links Codex skills, while user MCP generation already handles
Codex. A local path edit disagrees with the documented skill discovery path.
Codex-only setup needs both skills and MCP without writing other clients' files.

### Decision

Use `sync-codex.sh` for skills and `generate.py --codex` for Codex user files.
Reuse this generator from full `--user` generation. Keep per-skill links in
`~/.agents/skills`, and disable GitHub and Terraform through canonical
`codex_enabled: false` flags, as requested by the user.

### Rationale

This follows the existing script and managed-generation conventions, provides
an independent Codex setup command, and keeps reruns consistent.

### Alternatives Considered

- Keep Codex in Claude sync: rejected because Codex-only setup would continue
  to modify Claude and VS Code files.
- Link the entire source tree to `~/.codex/skills`: rejected because it can
  hide installed skills and expose downloaded containers; the documented user
  discovery path is `~/.agents/skills`.

### Consequences

- Positive: independent client sync, shared MCP rendering, preserved local
  skills, and repeatable disabled server settings.
- Negative: bootstrap runs another entry point; some skill instructions still
  depend on host-specific tools and need Codex's existing adaptation guidance.

---

## Decision 2: Make unavailable optional MCP services opt-in for Codex

**ID:** 2
**Date:** 2026-10-23
**Status:** partially superseded by Decision 3 (Awesome Copilot removal)

### Context

Native MCP discovery found four failing services. GitHub and Terraform are
disabled by user request. Awesome Copilot also requires the stopped Podman VM,
and Transit has no installed application or running localhost endpoint.
Azure, DevTools, and Svelte connect successfully.

### Decision

Default Awesome Copilot and Transit to disabled for Codex using the same
`codex_enabled` flag. Keep their definitions for explicit re-enablement once
their prerequisites are ready. Remove the exact broken legacy skill link and
its backup as requested by the user.

### Rationale

Codex setup should finish without connection warnings from unavailable optional
services. Starting an 8 GB VM or installing an application is unnecessary for
the requested skill setup. Other clients' server definitions are unaffected.

### Alternatives Considered

- Leave the services enabled: rejected because each new Codex session would
  repeat the connection failures.
- Start Podman and install Transit automatically: rejected because ongoing
  local infrastructure is unnecessary for the user's skill setup.

### Consequences

- Positive: Codex starts with working services and preserves optional definitions.
- Negative: using Awesome Copilot or Transit requires enabling its canonical flag
  and preparing its local service first.

---

## Decision 3: Remove Awesome Copilot rather than retaining a disabled definition

**ID:** 3
**Date:** 2026-10-23
**Status:** accepted

### Context

The user states that Awesome Copilot is unused and requests complete removal.
Deleting a canonical definition alone makes existing entries appear custom,
which the merge writers normally preserve.

### Decision

Delete the definition and record its retired name. Remove old entries from
Codex TOML and managed JSON files, including the Claude user CLI path.
Keep Transit's opt-in default from Decision 2.

### Rationale

Explicit retirement converges existing installations and prevents the unused
service from surviving outside the source definition.

### Alternatives Considered

- Keep it disabled: rejected because the user requests complete removal.
- Delete only the definition: rejected because old entries would be preserved
  as non-canonical services and still start.

### Consequences

- Positive: the unused service is removed on existing and fresh installations.
- Negative: the retired-name record must remain so older installations converge.
