# Voice Checker — Routing

This file tells you when the agent fires and what it receives.

---

## When it fires

Always, on every output. It runs in parallel with the other checker agents — constraints, anti-patterns, quality, identity, and gap analyzer — after the engine has produced a proposed response. The coordinator fans all checkers out simultaneously and waits for all verdicts before making a delivery decision.

---

## What it receives

A plain text string: the engine's proposed response. The voice checker does not need the human's original message, the conversation history, or the profiler outputs. A voice rule either applies to the text or it does not — context does not change whether a prohibited phrase is present.

---

## What it sends back

A single verdict: clean or violation. If violation, the specific rule, the exact offending text, and the severity. Defined in `CONTRACT.md`.

---

## The most important routing principle

A voice violation is a hard correction trigger at high severity. The coordinator should treat a "high" severity voice violation the same way it treats a constraint violation — the output does not reach the human without correction. A "medium" severity violation should be weighed against the other verdicts arriving in parallel. The coordinator decides; the voice checker only reports what it found.
