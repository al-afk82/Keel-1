# Question Generator — Routing

This file tells you when the agent fires and what it receives.

---

## When it fires

Only when the alignment checker (A5) returns misaligned. This is not a parallel agent — it is a conditional agent. If A5 returns aligned, this agent does not fire. The coordinator routes to it only on a misaligned verdict.

---

## What it receives

A JSON object with two fields: `reason` (the misalignment reason from A5's response) and `previous_questions` (an array of questions already asked in this conversation — empty array if none have been asked yet). The coordinator is responsible for tracking which questions have been asked across turns and passing that history in.

---

## What it sends back

A single verdict with one question ready to deliver to the human. Defined in `CONTRACT.md`.

---

## What happens after the question is delivered

The coordinator delivers the question to the human and waits. When the human replies, that reply re-enters the pipeline at A1 — a fresh exchange with a new input_id. The full pipeline runs again. If A5 returns aligned this time, the pipeline continues normally. If A5 returns misaligned again, the question generator fires again with the new reason and the updated `previous_questions` list, which now includes the question that did not resolve the gap.

---

## The most important routing principle

The question generator must not repeat a question that is already in `previous_questions`. If the coordinator does not pass the full history of asked questions, the question generator has no way to avoid repetition and the human receives the same question twice. The coordinator owns the conversation history — the agent only knows what it is given.
