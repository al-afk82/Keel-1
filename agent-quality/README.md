# Quality Agent

Checks whether the output meets the output standard.

## Responsibility

This agent knows what good looks like. It checks every output against the quality criteria — not just whether the rules were followed, but whether the result is actually worth delivering.

## Input

The AI output text. Optionally: surrounding context.

## Output

A verdict object matching the schema in `shared/schema.json`.

## Files in this folder

- `quality-criteria.md` — the standards this agent checks (copy from brain/quality/quality_criteria.md)
- `agent.js` (or equivalent) — the agent function
- `test-cases.md` — sample outputs that should trigger a violation, and samples that should pass clean
