# Runbook: localml model in VS Code

Follow the steps in order. Values are exact — copy them as written. The model id used
throughout is the `<publisher>/<name>` string you pass to `localml serve` (example:
`mlx-community/gemma-3-4b-it-qat-4bit`).

## Steps

1. Start the server:

   ```sh
   cd ~/repos/localml
   uv run localml serve <publisher>/<name>
   ```

   Defaults serve on `http://127.0.0.1:8080`. Leave this terminal running.

2. Already done by bootstrap — skip unless it is missing: the bootstrap script seeded a
   `github.copilot.chat.customOAIModels` entry in your VS Code user `settings.json` with
   `baseUrl` set to `http://127.0.0.1:8080/v1`. Verify it exists; do not re-add it.

3. Open the Command Palette (`Cmd+Shift+P`) and run `Chat: Manage Language Models`.

4. Select `OpenAI Compatible`.

5. Enter these values when prompted:

   | Field    | Value                                                        |
   |----------|--------------------------------------------------------------|
   | Base URL | `http://127.0.0.1:8080/v1`                                   |
   | API key  | `local-mlx-placeholder` (any non-empty string works; localml does not validate it) |
   | Model ID | the `<publisher>/<name>` you passed to `localml serve` in step 1 |

   The API key lives in VS Code secret storage, which is why this step is manual.

6. Open the Chat view, click the model picker at the bottom of the input box, and select
   the `<publisher>/<name>` model you just added.

## Troubleshooting

- **Connection refused**: the server from step 1 is not running, or was stopped. Restart it.
- **404 / no models found**: wrong Base URL form. VS Code needs `http://127.0.0.1:8080/v1`
  (with `/v1`), not `http://127.0.0.1:8080/`.
- **Model errors or is not listed**: the Model ID must match the argument passed to
  `localml serve` exactly, including the `<publisher>/` prefix.
- **Port already in use** (localml exits with code 3): another server holds 8080. Stop it,
  or re-serve with `--port` and update the Base URL to match.
