# Constraints Agent

## What it does

Checks the engine's response against a set of hard rules. If any rule is violated, returns the specific rule ID, the exact failing text, and a severity rating.

## Why it exists

Hard rules exist because some failures are non-negotiable. Fake social proof, confidently wrong claims, broken promises — these cannot be caught by tone or style checks. The constraints agent is the last line of defence against outputs that would damage trust.

## Input

The engine's response, passed in by the coordinator. Rules are loaded from `reference/constraints.md`.

## Output

```json
{
  "agent": "constraints",
  "status": "clean" | "violation",
  "rule": "rule ID and name",
  "excerpt": "the exact failing text",
  "severity": "high" | "medium"
}
```

## Position in the system

Runs in parallel. A violation verdict is the highest-priority signal in the system — it triggers immediate correction before output reaches the user. This was the first agent built and the first to catch a live violation in testing.
