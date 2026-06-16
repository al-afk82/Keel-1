# Gap Analyzer — Routing

This file tells you when the agent fires and what it receives.

---

## When it fires

On every exchange, after the engine has produced a proposed response. It runs in parallel with the checker agents — constraints, anti-patterns, voice, quality, identity — not after them. All of these fire at the same time once the engine's output is ready. The coordinator fans them out in parallel and waits for all verdicts before making a routing decision.

---

## What it receives

A JSON object with two fields: `input` (the human's original message, taken from A1's logged record) and `output` (the engine's proposed response before it is delivered to the human).

---

## What it sends back

A single verdict: no-gap or gap-found. If a gap is found, a description of the specific difference between what was asked and what was produced. Defined in `CONTRACT.md`.

---

## The most important routing principle

A gap-found verdict means something in the output does not match the request. The coordinator should treat this as a content correction signal — the output needs to be revised before delivery. The gap description itself is the correction brief: it tells the coordinator (and any corrector agent) exactly what needs to change. A gap is not the same as a quality violation. A quality violation means the output is weak. A gap means the output missed the target.
