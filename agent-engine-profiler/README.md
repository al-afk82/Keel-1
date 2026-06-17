# Engine Profiler

Defines what role the engine actually took in this conversation — inferred from its own reasoning, not from what the human asked.

## Responsibility

This agent reads the engine's internal thinking and produces a conversation-scoped profile: role and scope. It does not judge, compare, or correct. It describes the engine half of the alignment comparison.

## Input

The engine's verbatim internal thinking, forwarded from Agent 02.

## Output

A profile object matching the `profile` schema in `shared/schema.json`.

## Files in this folder

- `agent.py` — the agent function (LangGraph + Band skeleton, same as the reference agent)
- `ABOUT.md` — what this agent is and why it exists
- `ARCHITECTURE.md` — how it fits the system
- `CONTRACT.md` — the exact output shape it promises
- `ROUTING.md` — when it fires and what it receives
- `work/` — scratch space

## How to run it

```
uv run python agent-engine-profiler/agent.py
```

Requires `ANTHROPIC_API_KEY` in `.env` and an `engine_profiler` entry in `agent_config.yaml`. See `build-notes/constraints-agent.md` for one-time setup.
