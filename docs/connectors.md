# Connectors

Connectors expose user-approved context to Eliot. They do not automatically dump private data into prompts.

## Implemented

- `MemoryConnector`: wraps Hypersave search/ask/save.
- `FilesConnector`: reads allowed roots, detects Finder selection, extracts text from plain text, Office/RTF via `textutil`, and PDFs via `pdftotext`/Spotlight metadata when available.
- `FinderConnector`: path-boundary-checked Finder/file actions including reveal, open, quicklook, rename, copy, move, tag, compress, and trash with approval-gated writes.
- `WebConnector`: disabled by default; world-knowledge access only when explicitly enabled.
- `NotesConnector`: reads recent note names and drafts/creates notes with approval-gated writes.
- `RemindersConnector`: reads reminders and creates reminders with approval-gated writes via EventKit helper with AppleScript fallback.
- `CalendarConnector`: reads calendar events and creates events with approval-gated writes via EventKit helper with AppleScript fallback.
- `ContactsConnector`: scoped name lookup, no broad contact dump.
- `MailConnector`: opt-in selected/recent message extraction; drafts by default; sending is approval-only.
- `MessagesConnector`: drafts by default; sending is approval-only.
- `BrowserConnector`: Chrome tab/history search plus approval-gated URL/YouTube handoff.
- `SystemControlConnector`: volume, dark mode, DND, lock/sleep/display scaffolds with approval-gated mutations.
- `SafariConnector`: reads tab names when enabled.
- `MessagesIndexConnector`: opt-in local `chat.db` read-only recent message extraction; requires Full Disk Access.
- `PhotosConnector`: opt-in Photos metadata, selected-photo export, OCR, and optional local VLM captions.
- `VisualConnector`: disabled by default; interactive screenshot capture with Vision OCR helper when available.
- `MapsConnector`: Apple Maps URL handoff for directions/search.
- `MusicConnector`: Music app play/search dry-run and AppleScript handoff.
- `PodcastsConnector`: Apple Podcasts search URL handoff.

## Model-Callable Tools

The harness exposes a literal catalog of 487 Mac capability entries through
`mac_tool`. The catalog is inspectable with:

```bash
eliot-harness --list-mac-tools
```

Currently implemented catalog entries dispatch to the explicit connector tools
below. Reserved catalog entries fail closed with a clear “not implemented yet”
message instead of pretending to work.

- `mail_search`, `mail_draft`, `mail_send`
- `messages_search`, `message_draft`, `message_send`
- `file_search`, `local_search`
- `calendar_free_busy`, `contacts_resolve`, `reminders_list`
- `browser_open_url`, `browser_history_search`, `browser_open_youtube_liked`, `browser_play_youtube`
- `system_control`
- `mac_tool`

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

Eliot is not a native vision model. For image understanding, configure an OpenAI-compatible VLM with `OPENSIRI_VLM_URL`, `OPENSIRI_VLM_MODEL`, and optionally `OPENSIRI_VLM_API_KEY`, or set the Vision model fields/key in Settings. The URL may be a local base URL or a full Foundry target URI ending in `/chat/completions`. Photos/Visual connectors then feed OCR/caption summaries into Eliot.
