# opensiri-ai Architecture

## Goal

Build opensiri-ai: a Siri-class personal Mac assistant without pretending the model is the safety boundary.

The harness owns:

- permissions
- context retrieval
- source connectors
- tool execution
- safety interception
- audit logs

The Eliot model owns:

- interpreting the current task and Accessibility tree
- choosing exactly one next action
- asking/finishing in schema

## Hypersave Integration

Hypersave is the personal-context brain. The production server already exposes:

- `/v1/save`
- `/v1/ask`
- `/v1/search`
- `/v1/query`
- `/v1/facts`
- `/v1/profile`
- `/v1/graph`
- `/v1/remind`
- `/v1/synapses`

The harness should retrieve compact, scoped context before each Eliot turn. The model should not freely browse raw memories.

## Context Compiler

Input:

- user task
- current app
- Accessibility tree
- prior result
- permission state
- optional Hypersave search results
- working memory

Output:

```text
TASK: ...
APP: ...
PERSONAL_CONTEXT:
PERMISSIONS:
- destructive actions require explicit user approval
- memory read enabled
MEMORY:
- Daisy = ...
UI:
...
RESULT: ...
```

## Connector Model

Every source is opt-in:

- Files
- Calendar
- Contacts
- Notes
- Reminders
- Mail
- Messages
- Safari
- Photos/visual later
- Hypersave

Each connector gets independent read/write settings.

## Safety

The deterministic guard is mandatory. It intercepts destructive local changes, external communication, payments, credentials, network egress, system administration, and uncertain shell mutations.

## Voice And Multimodal

Pipecat-style voice can be layered on top later:

```text
mic -> STT -> harness -> Eliot -> TTS
```

Do not make voice the first release path. Keyboard/palette first is easier to audit and safer.

## Apple Direction Alignment

Apple's public direction emphasizes personal context, app actions, on-device processing, App Intents, visual intelligence, and privacy. Eliot Harness follows the same product shape but remains open and harness-primary.
