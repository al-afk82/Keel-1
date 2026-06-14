# Question Generator

## What it does

Identifies ambiguities in the human's input that the engine should have clarified before responding. Generates the questions the engine should have asked.

## Why it exists

Engines default to answering rather than clarifying. When the input is ambiguous, the engine picks an interpretation and runs with it — often the wrong one. The question generator surfaces what was left unasked so the coordinator can decide whether to request clarification or flag the assumption.

## Input

The human's message and the engine's response, passed in by the coordinator.

## Output

```json
{
  "agent": "question-generator",
  "status": "clear" | "ambiguous",
  "questions": ["question the engine should have asked"]
}
```

## Position in the system

Runs in parallel. An ambiguous verdict does not block output but flags the assumption the engine made so it can be surfaced to the human.
