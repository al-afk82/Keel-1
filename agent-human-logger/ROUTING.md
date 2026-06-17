# Human Logger — Routing

This file tells you when the agent fires and what it receives.

---

## When it fires

Always. Every exchange. First. Before A2, before the profilers, before any checker. No message enters the system without passing through A1.

---

## What it receives

The raw human message as a plain text string. Nothing else. The coordinator does not need to wrap it or annotate it — A1 handles the structure.

---

## What it sends back

A logged record with four fields: `input_id` (a freshly generated UUID4), `input` (the exact human message verbatim), `status` (always "logged"), and `timestamp` (UTC at the moment of logging). Defined in `CONTRACT.md`.

---

## The most important routing principle

The `input_id` in A1's response is the backbone of the entire tracing system. The coordinator must capture it immediately and inject it into every downstream agent's input. If any agent downstream receives a message without an input_id, the harness cannot tie that verdict back to the exchange that triggered it. The tracing chain breaks at the coordinator, not at the agents — so the coordinator's responsibility is to carry this ID from A1's response to every subsequent call.
