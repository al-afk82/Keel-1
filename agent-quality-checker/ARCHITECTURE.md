# Quality Checker

## What it does

Checks the engine's response against output quality criteria. Specificity, completeness, actionability, accuracy. Flags responses that are technically clean but functionally weak.

## Why it exists

A response can pass every constraint and voice check and still be useless. Vague answers, incomplete explanations, generic advice — these are quality failures, not rule violations. The quality checker holds the output to a higher standard than just not being wrong.

## Input

The engine's response, passed in by the coordinator. Criteria loaded from `reference/quality-criteria.md`.

## Output

```json
{
  "agent": "quality-checker",
  "status": "clean" | "violation",
  "rule": "criteria ID and name",
  "excerpt": "the failing text or what is missing",
  "severity": "high" | "medium"
}
```

## Position in the system

Runs in parallel. A violation here triggers a content improvement rather than a hard block.
