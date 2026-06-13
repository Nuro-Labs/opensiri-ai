# opensiri-ai Mac App

Product app target: Spotlight-style command palette for Eliot.

The Swift package lives in `app/opensiri-ai`.

Build:

```bash
app/opensiri-ai/scripts/build.sh
```

Run:

```bash
app/opensiri-ai/.build/release/OpenSiriAI
```

Planned UI surfaces:

- Option-Space command palette.
- Conversation thread.
- Source chips for memory/files/calendar/mail/etc.
- Approval cards for destructive, send, payment, and network actions.
- Permission center for every source manifest in `eliot_harness.sources`.
- Transcript/audit viewer.
- Local model status and endpoint selector.

The Python harness is the runtime. The app should call the CLI/runtime rather than duplicate safety logic.
