# Alignment Checker — Routing

This file tells you when the agent fires and what it receives.

---

## When it fires

After A3 (human profiler) and A4 (engine profiler) have both returned. The coordinator must wait for both profiles before calling A5 — the comparison requires both sides. A3 and A4 can run in parallel with each other; A5 runs once both are complete.

---

## What it receives

A JSON object containing the full human profile from A3 and the full engine profile from A4, combined into a single input. The coordinator is responsible for assembling this — the alignment checker does not retrieve profiles itself.

---

## What it sends back

A single verdict: aligned or misaligned. If misaligned, a specific reason describing the divergence. Defined in `CONTRACT.md`.

---

## What happens on misaligned

A misaligned verdict routes to the question generator (A6). The coordinator passes the `reason` from A5's response to A6 as input. A6 generates one question to resolve the gap. That question is delivered to the human. The coordinator waits for the human's response, then re-runs the full pipeline from A1.

---

## The most important routing principle

On the first message of a conversation, this agent requires strong evidence before returning misaligned. Ambiguity is not enough — the engine has not had a chance to demonstrate misalignment yet. The coordinator should treat a first-message misaligned verdict with caution and only route to the question generator if the reason is concrete and specific.
