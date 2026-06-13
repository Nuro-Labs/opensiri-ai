# Personal Context Indexing

`opensiri-ai` indexes personal context only when explicitly run. It can write to
Hypersave, a local SQLite full-text index, or both.

## Run

```bash
export HYPERSAVE_API_KEY="..."
opensiri-index --sources files,calendar,reminders,notes,safari,mail,messages,photos --files-root ~/Documents --local-index
```

Dry run:

```bash
opensiri-index --dry-run --files-root ~/Documents
```

Live polling index:

```bash
opensiri-index --sources mail,messages,calendar,reminders,notes,files --files-root ~/Documents --local-index --dry-run --live --interval 300
```

Harness local index lookup:

```bash
eliot-harness --task "Find the email about Google Cloud" --enable-local-index --enable-memory
```

## Sources

Implemented:

- Files: bounded text/PDF/document extraction from allowed roots.
- Calendar: today event summaries through Calendar automation.
- Reminders: reminder names through Reminders automation.
- Notes: recent note names through Notes automation.
- Safari: open tab names through Safari automation.
- Mail: opt-in recent/query metadata through Mail automation. Deep body indexing can be slow and requires future native `.emlx`/MailKit extraction.
- Messages: opt-in local `chat.db` read-only recent messages; requires Full Disk Access.
- Photos: opt-in metadata/selected export/OCR/optional VLM summaries.

## Safety

- Indexing is opt-in.
- Mail, Messages, and Photos are intentionally disabled unless included in `--sources`.
- Files are limited to allowed roots and small files.
- The model does not ingest raw sources directly; the local index/Hypersave stores bounded summaries/snippets.
- All source writes should be auditable and removable through Hypersave.
