# Quality Agent — Routing

This file tells you when the agent fires and what it receives.

---

## When it fires

Always. Every output.

---

## What it receives

A plain text string — the AI output being checked. And optionally, the user's original prompt.

Pass the prompt when you have it. This agent's ability to detect "unanswered question" violations depends on knowing what was asked. Without the prompt, the agent can still check for padding, trailing summaries, and generic advice — but it cannot detect the most important quality failure.

---

## What it sends back

A single verdict object. Defined in `CONTRACT.md`.

---

## The severity calibration for quality

Quality severity is different from constraint severity. A constraint violation is almost always high because a rule was broken. A quality violation ranges widely.

An output that gives generic advice when a specific answer exists is medium. An output that does not answer the user's question at all is high. An output that answers correctly but uses unnecessary words is low.

Calibrate the model prompt to distinguish these. Ask the model to return severity based on how much the quality failure affects the user's ability to act on the output.
