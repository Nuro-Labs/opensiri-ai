# Connectors

Connectors expose user-approved context to Eliot. They do not automatically dump private data into prompts.

## Implemented

- `MemoryConnector`: wraps Hypersave search/ask/save.
- `FilesConnector`: exposes allowed file roots and path-boundary checks.
- `WebConnector`: disabled by default; world-knowledge access only when explicitly enabled.

## Planned

- Calendar connector: read free/busy and events, write events with approval.
- Contacts connector: resolve names and ambiguity.
- Notes connector: local note search and read, create note with approval.
- Reminders connector: read lists, create reminders, delete/complete with approval.
- Mail connector: read/search metadata first; sending always requires approval.
- Messages connector: off by default; sending always requires approval.
- Safari connector: tabs/bookmarks/history opt-in.
- Visual connector: screenshots/OCR/VLM later.

Each connector must declare:

- source name
- read/write scopes
- sensitivity level
- maximum output size
- timeout
- provenance fields
- whether content is trusted or untrusted
