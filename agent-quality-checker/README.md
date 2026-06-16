# Quality Checker

Checks the engine's output against quality criteria — completeness, accuracy, specificity, usefulness. Flags responses that are technically clean but functionally weak.

## Responsibility

This agent holds the output to a higher standard than "not wrong." It checks every output against the criteria in `reference/quality-criteria.md` and flags the highest-severity failure. It does not check voice, constraints, anti-patterns, or identity.

## Input

The engine's output text. Optionally: the gap from Agent 07.

## Output

A verdict object matching the `verdict` schema in `shared/schema.json`. See `CONTRACT.md`.

## Files in this folder

- `agent.py` — the agent function (LangGraph + Band skeleton, same as the reference agent)
- `reference/quality-criteria.md` — the criteria this agent enforces, each with a fixed severity
- `ABOUT.md` — what this agent is and why it exists
- `ARCHITECTURE.md` — how it fits the system
- `CONTRACT.md` — the exact output shape it promises
- `ROUTING.md` — when it fires and what it receives
- `work/` — scratch space

## How to run it

```
uv run python agent-quality-checker/agent.py
```

Requires `ANTHROPIC_API_KEY` in `.env` and a `quality_checker` entry in `agent_config.yaml`. See `build-notes/constraints-agent.md` for one-time setup.
