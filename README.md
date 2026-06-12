# Eliot Harness

Eliot Harness is the reference runtime for building a Siri-class local Mac assistant with Eliot as the action model and Hypersave as the optional personal-context memory layer.

The harness is the safety boundary. The model proposes one tool call per turn; the harness compiles context, enforces permissions, intercepts risky actions, writes audit logs, and executes approved tools.

## What This Is

- A local Mac agent harness for Eliot.
- A permissioned personal-context layer that can connect to Hypersave.
- A deterministic guard for destructive, external, credential, payment, and network actions.
- A connector architecture for Files, Calendar, Notes, Reminders, Mail, Messages, Safari, and future visual context.

## What This Is Not

- Not a claim that the model is safe by itself.
- Not a personal-context index by default.
- Not affiliated with Apple.
- Not a product named Siri. `Open Siri AI` is treated as an internal target phrase only.

## Core Loop

```text
user task
  -> permission router
  -> context compiler
  -> optional Hypersave memory retrieval
  -> current Accessibility tree
  -> Eliot model
  -> deterministic guard
  -> user approval if needed
  -> executor
  -> audit log
```

## Quickstart

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .
python -m eliot_harness.checks
```

Run the harness against an Eliot-compatible OpenAI server:

```bash
eliot-harness \
  --model-url http://localhost:8081 \
  --model-name default_model \
  --task "Open Notes and tell me whether a note list is visible." \
  --approval deny
```

Configure Hypersave only when you want personal context:

```bash
export HYPERSAVE_BASE_URL="https://api.hypersave.io"
export HYPERSAVE_API_KEY="..."
```

## Public Positioning

Use: “open-source Mac personal assistant harness.”

Avoid: product claims implying parity with Apple Siri, full personal context, or autonomous safety without the guard.

## Safety Contract

Third-party harnesses should copy the guard model:

- inspect every tool call before execution
- fail closed on destructive and external actions
- ask the user before delete/send/network/payment/overwrite
- redact secrets in logs
- keep source permissions opt-in
- make memory retrieval explicit and scoped

## Repository Status

This repo now includes a working Python runtime loop, OpenAI-compatible model client, deterministic guard, approval providers, transcript/audit logging, Hypersave client, context compiler, and initial connector framework. The Mac Accessibility bridge is optional and imported lazily so core tests run without PyObjC.
