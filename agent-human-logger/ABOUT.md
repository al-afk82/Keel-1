# Agent 01 — Human Logger

## One job

Log the human's input verbatim. Nothing else.

## What it receives

The raw message the human sent before it reaches the engine.

## What it returns

```json
{
  "agent": "human-logger",
  "status": "logged",
  "input": "the exact human message verbatim",
  "timestamp": "ISO 8601 timestamp"
}
```

## What it does not do

It does not interpret, summarise, classify, or modify the input. It logs it exactly as received and returns confirmation.

## Why this exists

The rest of the pipeline needs the original human message preserved exactly. If any downstream agent receives a paraphrased or modified version, alignment checks become unreliable. This agent is the source of truth for what the human actually said.
