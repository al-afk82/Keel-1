# Constraints Agent — Routing

This file tells you when the agent fires and what it receives.

---

## When it fires

Always. Every output. Hard rules do not have scope conditions.

---

## What it receives

A plain text string. The AI output being checked.

The agent does not need to know who the user is or what the conversation is about. A hard rule is a hard rule regardless of context. If the constraint file says "no selling on first contact", the agent checks whether the output contains a pitch. The surrounding context does not change whether a pitch is present.

---

## What it sends back

A single verdict object. Defined in `CONTRACT.md`.

---

## The most important routing principle

A violation from this agent always triggers the corrector. Not sometimes. Not when the coordinator decides it is serious enough. Always.

This is the difference between constraints and quality criteria. Quality violations get weighed. Constraint violations do not. Build the routing logic with that distinction in mind.
