# Human Logger

Receives the human's message, logs it verbatim, and generates the unique input_id that ties all downstream verdicts to this exchange.

## Responsibility

This is A1 — the entry point to the entire pipeline. Every conversation exchange starts here. Before any agent checks anything, the human logger creates a permanent record of exactly what the human said and assigns it a UUID4. That ID is the single thread that connects every downstream verdict back to this specific exchange. Without A1 firing first, nothing is traceable.

This agent does not evaluate, score, or classify. It logs. Its only job is to make sure no human message enters the system without a timestamp, a verbatim record, and a unique ID.

## Input

The raw human message as a plain text string. The coordinator sends this directly — no wrapping, no formatting.

## Output

A verdict object containing the input_id, the verbatim message, and a UTC timestamp. Defined in `CONTRACT.md`. The coordinator must extract the input_id from this response and pass it to every subsequent agent in the pipeline.

## Files in this folder

- `agent.py` — the agent function (LangGraph + Band skeleton)
- `CONTRACT.md` — the exact output shape this agent promises
- `ROUTING.md` — when it fires and what it receives

## How to run it

```
uv run python agent-human-logger/agent.py
```

Requires `ANTHROPIC_API_KEY` in `.env` and a `human_logger` entry in `agent_config.yaml`.
