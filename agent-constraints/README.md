# Constraints Agent

Checks AI outputs against hard rules that must never be violated.

## Responsibility

This agent knows the constraint set. It checks every output and flags any hard rule breach — no exceptions, no edge cases. If the rule exists, the agent enforces it.

## Input

The AI output text. Optionally: surrounding context.

## Output

A verdict object matching the schema in `shared/schema.json`.

## Files in this folder

- `constraints.md` — the rules this agent enforces (copy from brain/constraints/constraints.md)
- `agent.js` (or equivalent) — the agent function
- `test-cases.md` — sample outputs that should trigger a violation, and samples that should pass clean
