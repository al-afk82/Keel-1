# Voice Agent

Checks AI outputs for tone and writing pattern violations.

## Responsibility

This agent knows how the user writes. It checks every output against the voice guide and flags anything that drifts — hedging language, filler phrases, wrong register, AI-sounding patterns.

## Input

The AI output text. Optionally: surrounding context.

## Output

A verdict object matching the schema in `shared/schema.json`.

## Files in this folder

- `voice-rules.md` — the rules this agent enforces (copy from brain/voice/voice_guide.md)
- `agent.js` (or equivalent) — the agent function
- `test-cases.md` — sample outputs that should trigger a violation, and samples that should pass clean
