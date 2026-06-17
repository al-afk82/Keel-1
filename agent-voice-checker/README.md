# Voice Checker

Checks the engine's output against the established voice and tone rules and flags any violation.

## Responsibility

This agent knows the voice rules. It checks every output and flags any breach — the wrong register, prohibited phrases, structural patterns the voice guide forbids, or tone that contradicts the defined communication style. It does not check content accuracy, persona consistency, or quality criteria — those belong to other agents. Voice checker owns tone and language pattern only.

The voice rules are loaded from `reference/voice-rules.md` at startup and baked into the system prompt. The agent does not retrieve them per message — the same rule set applies to every check.

## Input

The engine's proposed output as a plain text string.

## Output

A verdict with `status` set to "clean" or "violation". If a violation is found, a `rule` field names the specific rule breached, an `excerpt` field quotes the exact offending text, and a `severity` field rates the violation as "high" or "medium". Defined in `CONTRACT.md`.

## Files in this folder

- `agent.py` — the agent function (LangGraph + Band skeleton)
- `reference/voice-rules.md` — the voice and tone rules this agent enforces
- `CONTRACT.md` — the exact output shape this agent promises
- `ROUTING.md` — when it fires and what it receives

## How to run it

```
uv run python agent-voice-checker/agent.py
```

Requires `ANTHROPIC_API_KEY` in `.env` and a `voice_checker` entry in `agent_config.yaml`.
