# Human Profiler — Routing

This file tells you when the agent fires and what it receives.

---

## When it fires

Every conversation turn, before the alignment check. It runs in parallel with the Engine Profiler (Agent 04). The alignment checker cannot run until both profiles exist.

It also re-fires on every loop iteration. When Agent 05 returns misaligned and the human answers the generated question, the pipeline loops back to Agent 03 — the human's role and scope are re-profiled against the new input.

---

## What it receives

The human's verbatim input, forwarded by the coordinator from Agent 01 (Human Logger). Plain text. Plus any prior conversation context the coordinator chooses to pass in.

---

## What it sends back

A single profile object. Defined in `CONTRACT.md`. Returned via `band_send_message` to the coordinator.

---

## The most important routing principle

This agent never blocks and never triggers a correction. It only describes. Its output is an input to the alignment check — it is the alignment checker, not this agent, that decides whether the human and engine are aligned.
