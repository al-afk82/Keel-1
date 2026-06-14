# Alignment Checker

## What it does

Compares the engine's internal reasoning against the human's stated intent. Checks whether the engine is actually solving the right problem or has drifted toward answering a different question.

## Why it exists

An engine can produce a confident, well-written response that is completely misaligned with what the human asked for. The alignment checker catches the gap between intent and execution before the output reaches the user.

## Input

The human's original message (from human logger) and the engine's internal reasoning (from thinking logger), passed in by the coordinator.

## Output

```json
{
  "agent": "alignment-checker",
  "status": "aligned" | "misaligned",
  "reason": "description of the gap if misaligned"
}
```

## Position in the system

Depends on thinking logger output. One of the highest-signal agents — a misaligned verdict triggers correction regardless of what other agents return.
