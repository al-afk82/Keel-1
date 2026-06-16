# Quality Checker — Routing

This file tells you when the agent fires and what it receives.

---

## When it fires

Always, on every output. It runs in parallel with the other four checkers — constraints, anti-patterns, voice, and identity — after Agent 07 (Gap Analyzer) and before delivery.

---

## What it receives

A plain text string: the engine's proposed output being checked. Optionally, the gap from Agent 07 for context on what the human actually asked — quality is partly judged against intent (criterion Q03, "no unanswered question").

The agent does not need profiles or alignment state. It checks the output against fixed criteria.

---

## What it sends back

A single verdict object. Defined in `CONTRACT.md`. Returned via `band_send_message` to the coordinator.

---

## The most important routing principle

A quality violation does **not** hard-block delivery. It triggers a content improvement. This is the line between quality and constraints: constraint violations are mandatory stops, quality violations are weighed. Build the routing so a quality verdict feeds the corrector as a *should-improve* signal, not a *must-block* one.
