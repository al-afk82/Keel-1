# Alignment Checker

Compares the human's role and scope against the engine's role and scope and returns aligned or misaligned with a specific reason.

## Responsibility

This is A5. It runs after the human profiler (A3) and the engine profiler (A4) have both returned. Its job is to compare the two profiles and determine whether the engine understood the conversation correctly — whether the role and scope it assumed match what the human was operating in.

This agent does not check content quality, voice, grammar, or constraint violations. Those belong to the checker agents. The alignment checker asks one question: did the engine assume the right role for this conversation? A misalignment here means the engine and the human were operating in different frames, which makes every content check downstream less reliable. Misalignment is a structural problem, not a content problem.

## Input

A JSON object containing both the human profile from A3 and the engine profile from A4. Both profiles must be present before this agent fires. If either is missing, the coordinator should wait rather than send an incomplete input.

## Output

A verdict with `status` set to "aligned" or "misaligned". If misaligned, a `reason` field describes specifically where the roles or scopes diverge. Defined in `CONTRACT.md`.

## Files in this folder

- `agent.py` — the agent function (LangGraph + Band skeleton)
- `CONTRACT.md` — the exact output shape this agent promises
- `ROUTING.md` — when it fires and what it receives

## How to run it

```
uv run python agent-alignment-checker/agent.py
```

Requires `ANTHROPIC_API_KEY` in `.env` and an `alignment_checker` entry in `agent_config.yaml`.
