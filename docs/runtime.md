# Runtime Loop

The harness runtime is implemented in `eliot_harness.runtime.HarnessRuntime`.

It performs these phases every turn:

1. Compile source permissions and optional Hypersave memory into compact context.
2. Build the Eliot observation with task, app, UI tree, personal context, and previous result.
3. Call an OpenAI-compatible Eliot model server.
4. Parse and validate exactly one tool call.
5. Run the deterministic guard.
6. Ask for approval if the guard marks the action risky.
7. Execute only approved actions.
8. Append redacted audit logs and transcript records.

The model never executes tools directly.

## CLI

```bash
eliot-harness \
  --model-url http://localhost:8081 \
  --model-name default_model \
  --task "Open Notes and tell me whether a note list is visible." \
  --approval deny
```

Approval modes:

- `deny`: safe demo mode; risky actions are blocked.
- `console`: ask in the terminal.
- `yes`: test mode only.

Source flags:

- `--enable-memory`
- `--enable-files --files-root <path>`
- `--enable-web`
- `--enable-visual`

Sessions are persisted under `~/.local/share/opensiri-ai/sessions` for future reference resolution and conversation history.

Enable Hypersave context:

```bash
export HYPERSAVE_BASE_URL="https://api.hypersave.io"
export HYPERSAVE_API_KEY="..."
eliot-harness --enable-memory --task "What do I know about Daisy?"
```
