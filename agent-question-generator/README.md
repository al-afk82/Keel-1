# Question Generator

Generates exactly one question to resolve an alignment gap identified by the alignment checker.

## Responsibility

This agent fires only when A5 (alignment checker) returns misaligned. Its job is to produce the one question that, if answered by the human, would give the engine enough information to re-run with the correct role and scope assumed.

The question generator does not diagnose the problem — A5 already did that. It does not ask multiple questions, it does not ask for clarification on things already provided, and it does not repeat questions already asked in this conversation. It takes the misalignment reason and translates it into the single most useful question the engine could ask the human right now.

The question is delivered to the human by the coordinator. The human's answer re-enters the pipeline at A1.

## Input

A JSON object containing the misalignment reason from A5 and a list of any questions already asked in this conversation (may be empty on first misalignment).

## Output

A single question object with `status` set to "question-ready" and a `question` field containing exactly one question addressed to the human. Defined in `CONTRACT.md`.

## Files in this folder

- `agent.py` — the agent function (LangGraph + Band skeleton)
- `CONTRACT.md` — the exact output shape this agent promises
- `ROUTING.md` — when it fires and what it receives

## How to run it

```
uv run python agent-question-generator/agent.py
```

Requires `ANTHROPIC_API_KEY` in `.env` and a `question_generator` entry in `agent_config.yaml`.
