# Agent 11 — Quality Checker

## One job

Check the engine's output against the quality criteria. Flag any violation. Nothing else.

## What it receives

The engine's proposed output and the gap from Agent 07.

## What it returns

```json
{
  "agent": "quality-checker",
  "status": "clean | violation",
  "rule": "rule ID and name if violated, null if clean",
  "excerpt": "exact offending text if violated, null if clean",
  "severity": "high | medium | low | null"
}
```

## What it does not do

It does not check voice, constraints, or anti-patterns. Quality is its only domain. Quality means: does the output meet the defined standard for completeness, accuracy, and usefulness given what the human asked?

## Why this exists

An output can pass every other check and still be low quality. It might be technically correct but incomplete. It might answer the wrong part of the question. Quality is a separate dimension from correctness, and it needs its own agent.
