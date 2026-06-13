# Anti-patterns Agent — Routing

This file tells you when the agent fires and what it receives.

---

## When it fires

Always. Every output.

Anti-patterns are not context-specific. The pattern of "performed confidence" — stating something as certain when the evidence does not support it — can appear in any output, in any conversation, on any topic.

---

## What it receives

A plain text string. The AI output being checked.

Unlike the voice and constraints agents, this agent benefits from a small amount of context about what the output is responding to. If you have the user's prompt available, pass it alongside the output. It helps the model identify patterns like "answering a different question than was asked."

This is optional. The agent works without it. But the quality of the verdict improves with it.

---

## What it sends back

A single verdict object. Defined in `CONTRACT.md`.

---

## What makes this routing different

The other three agents check mechanical properties of the output. This agent checks behavioral patterns. That means its verdicts are more nuanced and occasionally less certain.

If the model returns low confidence on a verdict, default to clean. A false positive from this agent — flagging something as an anti-pattern when it is not — erodes trust in the system faster than a missed anti-pattern does. When in doubt, let it through.
