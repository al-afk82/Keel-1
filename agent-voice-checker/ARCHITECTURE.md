# Voice Checker

## What it does

Checks the engine's response against a defined voice guide. Sentence structure, directness, length, tone. Flags when the response drifts from the established communication style.

## Why it exists

Identity is expressed through voice. An engine that gradually adopts a warmer, more hedging, more corporate tone is drifting — even if it never violates a hard rule. The voice checker maintains the standard that makes outputs recognisably consistent.

## Input

The engine's response, passed in by the coordinator. Voice rules loaded from `reference/voice-rules.md`.

## Output

```json
{
  "agent": "voice-checker",
  "status": "clean" | "violation",
  "rule": "the specific voice rule broken",
  "excerpt": "the exact failing text"
}
```

## Position in the system

Runs in parallel. Violations trigger a tone rewrite — the content stays, the expression changes.
