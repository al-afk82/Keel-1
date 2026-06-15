# Engine Profiler — Routing

This file tells you when the agent fires and what it receives.

---

## When it fires

Every conversation turn, before the alignment check. It runs in parallel with the Human Profiler (Agent 03). The alignment checker cannot run until both profiles exist.

It also re-fires on every loop iteration. When Agent 05 returns misaligned and the human answers the generated question, the engine produces new thinking — and that new thinking is re-profiled here before the next alignment check.

---

## What it receives

The engine's verbatim internal thinking, forwarded by the coordinator from Agent 02 (Thinking Logger). Plain text. This is the engine's reasoning, not its final output — the role is inferred from how it reasoned.

---

## What it sends back

A single profile object. Defined in `CONTRACT.md`. Returned via `band_send_message` to the coordinator.

---

## The most important routing principle

This agent never blocks and never triggers a correction. It only describes. Its output is an input to the alignment check — it is the alignment checker, not this agent, that decides whether the human and engine are aligned.
