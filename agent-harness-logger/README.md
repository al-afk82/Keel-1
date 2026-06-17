# Harness Logger

Receives the compiled verdict record from the coordinator and writes it to the harness API for permanent storage.

## Responsibility

This is A13 — the last agent in the pipeline. Every exchange that passes through the system ends here. The coordinator assembles the full verdict record — all agent verdicts, the input_id, the original human message, the engine output, and the final delivery decision — and sends it here for permanent storage. The harness logger writes it to the harness API and returns the entry ID as confirmation.

This agent does not evaluate anything. It stores. Its job is to make sure every exchange has a permanent record in the harness regardless of whether correction fired, regardless of whether the output was clean or violated. Every exchange writes to the harness. The harness is the system's memory.

## Input

The full compiled verdict record for one exchange, in JSON format. The coordinator assembles this from all agent verdicts before sending it here.

## Output

A confirmation containing the entry ID returned by the harness API and a UTC timestamp. Defined in `CONTRACT.md`.

## Files in this folder

- `agent.py` — the agent function (LangGraph + Band skeleton, with direct harness API write)
- `CONTRACT.md` — the exact output shape this agent promises
- `ROUTING.md` — when it fires and what it receives

## How to run it

```
uv run python agent-harness-logger/agent.py
```

Requires `ANTHROPIC_API_KEY`, `HARNESS_URL`, and `HARNESS_SECRET` in `.env` and a `harness_logger` entry in `agent_config.yaml`. The harness is live at `167.233.71.106:5000`.
