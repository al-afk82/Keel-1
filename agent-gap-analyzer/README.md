# Gap Analyzer

Compares what the human asked against what the engine produced and describes any gap between intent and output.

## Responsibility

This agent does not judge whether the output is good or bad. It compares. The human asked for something specific. The engine produced something. This agent names the difference — what was asked for that did not arrive, what arrived that was not asked for, what was partially addressed but not completed. A gap is a description, not a verdict.

The gap analyzer runs on every exchange regardless of whether the alignment check passed. Even when the engine understood the role correctly, it may still have missed part of the request, over-answered, or answered a slightly different question than the one asked. The gap is the gap between the human's intent and the engine's output — alignment is about frames, gap is about delivery.

## Input

A JSON object containing two fields: `input` (the human's original message) and `output` (the engine's proposed response).

## Output

A verdict with `status` set to "no-gap" or "gap-found". If a gap is found, a `gap` field describes it specifically. Defined in `CONTRACT.md`.

## Files in this folder

- `agent.py` — the agent function (LangGraph + Band skeleton)
- `CONTRACT.md` — the exact output shape this agent promises
- `ROUTING.md` — when it fires and what it receives

## How to run it

```
uv run python agent-gap-analyzer/agent.py
```

Requires `ANTHROPIC_API_KEY` in `.env` and a `gap_analyzer` entry in `agent_config.yaml`.
