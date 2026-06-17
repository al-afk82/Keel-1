# Thinking Logger

Receives the engine's internal thinking and logs it verbatim alongside the input_id from A1.

## Responsibility

This is A2. It runs immediately after A1. The engine's internal thinking — the reasoning that happens before the final response is produced — is captured here before anything else touches it. The thinking logger does not evaluate whether the reasoning was good or bad. It logs it exactly as it arrived and ties it to the same exchange as the human message by carrying the input_id unchanged.

This record is important because it is the raw material for the profilers. A3 (human profiler) reads the human's message. A4 (engine profiler) reads the engine's thinking. Without A2 creating a clean, verbatim record of that thinking, A4 has nothing reliable to work from.

## Input

A JSON object containing two fields: `input_id` (carried from A1) and `thinking` (the engine's internal dialog before its final response).

## Output

A logged record containing the input_id unchanged, the thinking verbatim, and a UTC timestamp. Defined in `CONTRACT.md`.

## Files in this folder

- `agent.py` — the agent function (LangGraph + Band skeleton)
- `CONTRACT.md` — the exact output shape this agent promises
- `ROUTING.md` — when it fires and what it receives

## How to run it

```
uv run python agent-thinking-logger/agent.py
```

Requires `ANTHROPIC_API_KEY` in `.env` and a `thinking_logger` entry in `agent_config.yaml`.
