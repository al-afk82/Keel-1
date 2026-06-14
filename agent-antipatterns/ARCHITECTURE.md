# Antipatterns Agent

## What it does

Checks the engine's response against a library of known failure patterns. Vague promises, filler language, corporate speak, hedging under pressure, AI-default phrasing — patterns that signal the engine is operating below standard.

## Why it exists

Constraint violations are explicit. Antipatterns are subtler — they do not break a rule but they degrade quality and erode trust over time. The antipatterns agent catches the slow drift that constraints cannot.

## Input

The engine's response, passed in by the coordinator. Patterns are loaded from `reference/antipatterns.md`.

## Output

```json
{
  "agent": "antipatterns",
  "status": "clean" | "violation",
  "pattern": "the pattern name",
  "excerpt": "the exact failing text"
}
```

## Position in the system

Runs in parallel. A violation here triggers a rewrite for tone and substance rather than a hard block.
