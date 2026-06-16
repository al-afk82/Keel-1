# Identity Agent

Checks whether the engine's response is consistent with its established identity — directness, position-holding under pressure, honesty over comfort. Flags when the engine has shifted persona.

## Responsibility

This agent checks persona, not content. It compares every response against the identity defined in `reference/identity.md` and flags drift — the engine becoming more agreeable, less direct, more flattering, or abandoning a defined characteristic under pressure. Content violations belong to the other agents.

## Input

The engine's output text. Optionally: the engine profile from Agent 04.

## Output

A verdict object matching the `identity` schema in `shared/schema.json` (`status` + `reason` — not the standard rule/excerpt/severity shape). See `CONTRACT.md`.

## Files in this folder

- `agent.py` — the agent function (LangGraph + Band skeleton, same as the reference agent)
- `reference/identity.md` — the authoritative definition of who the engine is
- `ABOUT.md` — what this agent is and why it exists
- `ARCHITECTURE.md` — how it fits the system
- `CONTRACT.md` — the exact output shape it promises
- `ROUTING.md` — when it fires and what it receives
- `work/` — scratch space

## How to run it

```
uv run python agent-identity/agent.py
```

Requires `ANTHROPIC_API_KEY` in `.env` and an `identity_agent` entry in `agent_config.yaml`. See `build-notes/constraints-agent.md` for one-time setup.
