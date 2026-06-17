# Human Profiler

Defines who the human is in this conversation — the role they are operating in and the outcome they need.

## Responsibility

This agent reads the human's input and produces a conversation-scoped profile: role and scope. It does not judge, compare, or correct. It describes the human half of the alignment comparison.

## Input

The human's verbatim input, forwarded from Agent 01.

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
uv run python agent-human-profiler/agent.py
```

Requires `ANTHROPIC_API_KEY` in `.env` and a `human_profiler` entry in `agent_config.yaml`. See `build-notes/constraints-agent.md` for one-time setup.
