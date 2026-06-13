# Agent 07 — Gap Analyzer

## One job

Compare what the human asked against what the engine produced. Output the gap. Nothing else.

## What it receives

The human's verbatim input from Agent 01 and the engine's proposed output.

## What it returns

If no gap:
```json
{
  "agent": "gap-analyzer",
  "status": "no-gap",
  "gap": null
}
```

If a gap exists:
```json
{
  "agent": "gap-analyzer",
  "status": "gap-found",
  "gap": "specific description of what the human asked for versus what the engine produced"
}
```

## What it does not do

It does not flag constraint violations, identify anti-patterns, or suggest corrections. Those are jobs for Agents 08 and 09. This agent only describes the gap between intent and output.

## Why this exists

A constraint checker needs to know what was asked before it can judge whether the answer is appropriate. A gap analysis gives the downstream agents the context they need to make accurate judgements rather than checking the output in isolation.
