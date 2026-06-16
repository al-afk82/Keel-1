# Thinking Logger — Routing

This file tells you when the agent fires and what it receives.

---

## When it fires

Immediately after A1, before the profilers. A1 and A2 run at the start of every exchange and create the two foundational log records — the human's message and the engine's thinking — that the rest of the pipeline reads from.

---

## What it receives

A JSON object with two fields: `input_id` (extracted from A1's response by the coordinator) and `thinking` (the engine's internal reasoning captured before the final response was produced).

---

## What it sends back

A logged record with `input_id` carried unchanged, `thinking` verbatim, and a UTC timestamp. Defined in `CONTRACT.md`.

---

## The most important routing principle

A2 does not generate a new input_id. It carries the one from A1. The coordinator must pass A1's input_id into A2's input explicitly — A2 cannot retrieve it on its own. If the coordinator sends A2 the thinking content without the input_id, the log entry will be unlinked from the human message that triggered it and the harness record will be incomplete.
