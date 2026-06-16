# Identity Agent — Routing

This file tells you when the agent fires and what it receives.

---

## When it fires

Always, on every output. It runs in parallel with the other four checkers — constraints, anti-patterns, voice, and quality — after Agent 07 (Gap Analyzer) and before delivery.

---

## What it receives

A plain text string: the engine's proposed response being checked. Optionally, the engine profile from Agent 04 for context on the role the engine assumed this turn.

The identity definition itself is not passed in per message — it is loaded once from `reference/identity.md` and baked into the system prompt. That file is the authority the response is checked against.

---

## What it sends back

A single verdict object. Defined in `CONTRACT.md`. Returned via `band_send_message` to the coordinator.

---

## The most important routing principle

A `drifted` verdict is high priority. Identity drift is the subtlest form of drift — no rule is broken, the engine just becomes a different version of itself — and it compounds across sessions if not corrected early. The coordinator should not weigh a drift verdict the way it weighs a low-severity quality note; treat persona drift as a serious correction trigger.
