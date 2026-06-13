# Personal Context Indexing

`opensiri-ai` indexes personal context into Hypersave only when explicitly run.

## Run

```bash
export HYPERSAVE_API_KEY="..."
opensiri-index --sources files,calendar,reminders,notes,safari --files-root ~/Documents
```

Dry run:

```bash
opensiri-index --dry-run --files-root ~/Documents
```

## Sources

Implemented:

- Files: bounded text/PDF/document extraction from allowed roots.
- Calendar: today event summaries through Calendar automation.
- Reminders: reminder names through Reminders automation.
- Notes: recent note names through Notes automation.
- Safari: open tab names through Safari automation.

Skipped until explicit safe connectors exist:

- Mail
- Messages
- Photos

## Safety

- Indexing is opt-in.
- Mail, Messages, and Photos are intentionally skipped by default.
- Files are limited to allowed roots and small files.
- The model does not ingest raw sources directly; Hypersave stores indexed context.
- All source writes should be auditable and removable through Hypersave.
