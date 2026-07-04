# Runbook: MCP servers for the cloud coding agent

Follow the steps in order. Values are exact — copy them as written. `<target-repo>` is the
path to the repository you are enabling; the server subset comes from that repo's
`.agentic.json` manifest (inferred read-only when no manifest exists).

## Steps

1. Print the paste-ready JSON (run from this repository's root):

   ```sh
   python3 scripts/align.py <target-repo> --cloud-mcp
   ```

   Secret references appear as `$COPILOT_MCP_*` placeholders, e.g. the github server's
   Authorization header is `$COPILOT_MCP_GITHUB_AUTH_TOKEN`.

2. Paste it on github.com: open the target repository → **Settings** → **Copilot** →
   **Coding agent** → **MCP configuration** → paste the entire JSON output → **Save**.

3. Create one Actions secret per `$COPILOT_MCP_*` placeholder, in the `copilot`
   environment (the cloud agent only reads secrets from that environment):

   1. Target repository → **Settings** → **Environments** → **copilot**
      (click **New environment** and name it exactly `copilot` if it does not exist).
   2. **Add environment secret**. The name is the placeholder without the `$`:

      | Server | Secret name                     | Value                                      |
      |--------|---------------------------------|--------------------------------------------|
      | github | `COPILOT_MCP_GITHUB_AUTH_TOKEN` | `Bearer <your GitHub PAT>`                 |

      With the current canonical set (`mcp/servers.json`), github is the only server
      with a secret. If step 1 printed more `$COPILOT_MCP_*` placeholders, add one
      secret per placeholder using the same rule.

4. Assign the agent a task and check the session log: the MCP servers appear during
   startup. A missing secret shows up there as an unexpanded `$COPILOT_MCP_*` string.

## Notes

- **transit is absent by design.** It serves on `http://localhost:3141` (localhost only),
  so it carries no cloud surface and is excluded from `--cloud-mcp` output. The same
  applies to awesome-copilot (VS Code only). This is not an error.
- Rerunning step 1 after editing `mcp/servers.json` or the manifest and re-pasting is the
  whole update path — there is no API-writable delivery.
