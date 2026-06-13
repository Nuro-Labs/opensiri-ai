# Connectors

Connectors expose user-approved context to Eliot. They do not automatically dump private data into prompts.

## Implemented

- `MemoryConnector`: wraps Hypersave search/ask/save.
- `FilesConnector`: exposes allowed file roots and path-boundary checks.
- `FilesConnector`: reads allowed roots, detects Finder selection, extracts text from plain text, Office/RTF via `textutil`, and PDFs via `pdftotext`/Spotlight metadata when available.
- `WebConnector`: disabled by default; world-knowledge access only when explicitly enabled.
- `NotesConnector`: reads recent note names and drafts/creates notes with approval-gated writes.
- `RemindersConnector`: reads reminders and creates reminders with approval-gated writes.
- `CalendarConnector`: reads calendar events and creates events with approval-gated writes.
- `ContactsConnector`: scoped name lookup, no broad contact dump.
- `MailConnector`: reads recent subjects only when enabled; drafts by default; sending is approval-only.
- `MessagesConnector`: drafts by default; sending is approval-only.
- `SafariConnector`: reads tab names when enabled.
- `VisualConnector`: disabled by default; interactive screenshot capture scaffold for future OCR/VLM.

## Planned

- OCR/VLM over captured screenshots.
- Rich Mail/Calendar/Contacts connectors using native frameworks/App Intents instead of AppleScript bridges.

Each connector must declare:

- source name
- read/write scopes
- sensitivity level
- maximum output size
- timeout
- provenance fields
- whether content is trusted or untrusted
