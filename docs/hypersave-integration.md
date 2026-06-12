# Hypersave Integration Plan

## Current Server Facts

Verified server state:

- API process `hypersave` online under PM2.
- Worker process `hypersave-worker` online under PM2.
- Health endpoint returns healthy.
- API entrypoint is `dist/server-new.js`.
- Worker entrypoint is `dist/workers/sleep-worker.js`.

## Harness Tools

Expose these to the harness, not directly to the model as unbounded tools:

| Tool | Endpoint | Default permission |
|---|---|---|
| `memory_search` | `/v1/search` | read-only, opt-in |
| `memory_ask` | `/v1/ask` | read-only, opt-in |
| `memory_facts` | `/v1/facts` | read-only, opt-in |
| `memory_profile` | `/v1/profile` | read-only, opt-in |
| `memory_save` | `/v1/save` | approval required |
| `memory_remind` | `/v1/remind` | approval required |

## Context Policy

Retrieve only task-relevant snippets. Do not dump full profile or full memories into the model.

Recommended defaults:

- max 5 memory snippets
- max 300 chars per snippet
- max sensitivity `high`, not `hyper`, unless user explicitly opts in
- Messages/Mail off by default

## Data Flow

```text
User task
  -> source classifier
  -> Hypersave search/facts/profile if permitted
  -> compact context
  -> Eliot model
  -> tool guard
  -> action executor
  -> optional memory_save after user approval
```
