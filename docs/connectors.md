# Connectors

Connectors expose user-approved context to Eliot. They do not automatically dump private data into prompts.

## Implemented

- `MemoryConnector`: wraps Hypersave search/ask/save.
- `FilesConnector`: reads allowed roots, detects Finder selection, extracts text from plain text, Office/RTF via `textutil`, and PDFs via `pdftotext`/Spotlight metadata when available.
- `WebConnector`: disabled by default; world-knowledge access only when explicitly enabled.
- `NotesConnector`: reads recent note names and drafts/creates notes with approval-gated writes.
- `RemindersConnector`: reads reminders and creates reminders with approval-gated writes via EventKit helper with AppleScript fallback.
- `CalendarConnector`: reads calendar events and creates events with approval-gated writes via EventKit helper with AppleScript fallback.
- `ContactsConnector`: scoped name lookup, no broad contact dump.
- `MailConnector`: opt-in selected/recent message extraction; drafts by default; sending is approval-only.
- `MessagesConnector`: drafts by default; sending is approval-only.
- `SafariConnector`: reads tab names when enabled.
- `MessagesIndexConnector`: opt-in local `chat.db` read-only recent message extraction; requires Full Disk Access.
- `PhotosConnector`: opt-in Photos metadata, selected-photo export, OCR, and optional local VLM captions.
- `VisualConnector`: disabled by default; interactive screenshot capture with Vision OCR helper when available.
- `MapsConnector`: Apple Maps URL handoff for directions/search.
- `MusicConnector`: Music app play/search dry-run and AppleScript handoff.
- `PodcastsConnector`: Apple Podcasts search URL handoff.

## Planned

- VLM image understanding beyond OCR.
- Rich Mail/Calendar/Contacts connectors using native frameworks/App Intents instead of AppleScript bridges.

Each connector must declare:

- source name
- read/write scopes
- sensitivity level
- maximum output size
- timeout
- provenance fields
- whether content is trusted or untrusted

The macOS app includes in-app approval cards, transcript access, audit-log access, and recent session history for debugging and continuity.

Eliot is not a native vision model. For image understanding, configure an OpenAI-compatible local VLM with `OPENSIRI_VLM_URL` and `OPENSIRI_VLM_MODEL`, or set the Vision model fields in Settings. Photos/Visual connectors then feed OCR/caption summaries into Eliot.
