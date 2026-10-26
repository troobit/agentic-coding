# REA Access and Recovery

Read this only when REA access is missing or an inspection fails. A healthy
connection needs no installation or audit before each investigation.

## Managed registration

This toolchain defines `rea` in `agentic-coding/mcp/servers.json` as:

```text
npx -y rea-agents@6.7.0 mcp
```

Resolve the skill's real path through any symlink to locate the `agentic-coding`
checkout. From that checkout, Codex registration and skill discovery use:

```bash
make sync-codex
```

The generator preserves unrelated settings and custom servers. Re-running a
converged sync should make no changes. Other supported local clients use the
same canonical definition through the existing user/repository generation flow;
its `--user` mode affects multiple clients, so choose a scope matching the task.
Do not run REA's separate setup wizard over these managed registrations.

The package is pinned to an explicit release, not to every transitive dependency.
The first `npx` launch needs registry access and may populate npm's cache. Use
the project-selected version rather than upgrading to `latest` during recovery.
Existing Node/npm are prerequisites; install only software the task authorises.

## Distinguish the failure

| Observation | Action |
| --- | --- |
| No REA tools in this session | Check the selected client's registration and startup error. If registration changed, reconnect/restart that client; shell health does not prove this session connected. |
| MCP startup or tool discovery fails | Run the production-stdio check below, then address its reported launcher/runtime error. |
| One analysis provider is unavailable | Diagnose that provider only; continue supported static/inventory work. Installing a decompiler is not required for JavaScript inspection. |
| Source input is unavailable | Record the blocked question, required input, and next supported action. A phone installation does not supply an IPA or runtime connection. |
| Tool returns partial results or a deadline error | Preserve returned Evidence and cleanup state; follow the advertised remediation or reduce the supported work. Do not retry an unchanged failing request indefinitely. |

Production stdio check (this proves transport, discovery, and target-free request
flow, not access to a particular source app):

```bash
npx -y rea-agents@6.7.0 mcp doctor --json
```

For a registration-specific issue, REA's scoped read-only diagnosis is
`npx -y rea-agents@6.7.0 doctor --client codex --json`; select the actual client.
Use the installed release's help and reported remediation for provider checks.

## CLI fallback

If this session cannot call MCP but shell analysis is available within the task,
prefer an existing `rea` command or the version-pinned package runner. For a
supplied JavaScript/Electron directory or ASAR:

```bash
npx -y rea-agents@6.7.0 analyze-javascript-application /absolute/path/to/app --json
```

Save the returned Evidence with the destination research. This is genuine REA
analysis through the CLI; it does not prove the agent's MCP connection works.
Native CLI analysis still needs its provider. Consult the release's actual
schemas/help for other target types; do not guess tool arguments or bypass a
client policy failure by silently broadening permissions.

Upstream references:

- [Installation and diagnosis](https://github.com/morluto/rea/blob/main/docs/installation.md)
- [MCP contracts](https://github.com/morluto/rea/blob/main/docs/mcp-contracts.md)
- [Investigation prompts](https://github.com/morluto/rea/blob/main/docs/mcp-prompts.md)
