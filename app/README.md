# opensiri-ai Mac App

Product app target: Spotlight-style command palette for Eliot.

The Swift package lives in `app/opensiri-ai`.

Build:

```bash
app/opensiri-ai/scripts/build.sh
```

Package an unsigned `.app` bundle:

```bash
app/opensiri-ai/scripts/package.sh
```

Run:

```bash
app/opensiri-ai/.build/release/OpenSiriAI
```

Global hotkey: `Option-Space` focuses the palette while the app is running.

Design direction: Raycast-style command palette, but native SwiftUI and backed by the deterministic Eliot harness.

Planned UI surfaces:

- Option-Space command palette.
- Conversation thread.
- Source chips for memory/files/calendar/mail/etc.
- Approval cards for destructive, send, payment, and network actions.
- Permission center for every source manifest in `eliot_harness.sources`.
- Transcript/audit viewer.
- Local model status and endpoint selector.

The Python harness is the runtime. The app should call the CLI/runtime rather than duplicate safety logic.
