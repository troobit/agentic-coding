# Runbook: Transit MCP server

Follow the steps in order. Values are exact — copy them as written. Transit's MCP
server is built into the Transit macOS app and serves localhost only.

## Steps

1. Enable the server in the Transit app: open **Transit** → **Settings** → toggle
   the **MCP server** on. The default port is `3141`; leave it unless it clashes,
   and if you change it, update the `transit` entry in `mcp/servers.json` to match.

2. Regenerate the user-level MCP configs so Claude Code and VS Code pick up the
   `transit` entry (run from this repository's root):

   ```sh
   make generate
   python3 scripts/generate.py --user
   ```

3. Smoke test — list the server's tools over plain HTTP:

   ```sh
   curl -s -X POST http://127.0.0.1:3141/mcp \
     -H 'Content-Type: application/json' \
     -H 'Accept: application/json, text/event-stream' \
     -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
   ```

   A JSON response listing tools such as `query_tasks`, `update_task_status`, and
   `create_task` means the server is up. `Connection refused` means the toggle in
   step 1 is off or the Transit app is not running.

## Notes

- Maintenance tools are gated off by default in the app's settings — only the
  day-to-day task tools are exposed unless you explicitly enable the rest.
- The server binds to localhost (`127.0.0.1:3141`), so the cloud coding agent can
  never reach it. Transit's surfaces in `mcp/servers.json` are `claude` and
  `vscode` only, and cloud-seeded assets carry no Transit instructions.
- How the workflow uses Transit (statuses, skills, branch conventions):
  `docs/agent-notes/transit-integration.md`.
