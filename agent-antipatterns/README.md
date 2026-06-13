# Anti-patterns Agent

Catches known failure modes before they reach the user.

## Responsibility

This agent knows what goes wrong. It checks every output for patterns that have failed before — things that look correct but are not, shortcuts that create problems downstream, outputs that technically pass but consistently disappoint.

## Input

The AI output text. Optionally: surrounding context.

## Output

A verdict object matching the schema in `shared/schema.json`.

## Files in this folder

- `antipatterns.md` — the failure modes this agent checks (copy from brain/anti_patterns/anti_patterns.md)
- `agent.js` (or equivalent) — the agent function
- `test-cases.md` — sample outputs that should trigger a violation, and samples that should pass clean
