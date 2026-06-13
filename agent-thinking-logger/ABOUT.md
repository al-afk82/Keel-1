# Agent 02 — Thinking Logger

## One job

Log the engine's internal thinking verbatim before the output is formed. Nothing else.

## What it receives

The thinking blocks returned by Claude's extended thinking API. These are the raw reasoning steps the engine took before producing a response.

## What it returns

```json
{
  "agent": "thinking-logger",
  "status": "logged",
  "thinking": "the engine's internal reasoning verbatim",
  "timestamp": "ISO 8601 timestamp"
}
```

## What it does not do

It does not evaluate the thinking, flag problems, or modify it. It logs it exactly as the engine produced it.

## Why this exists

Drift happens in the reasoning layer before it shows up in the output. If the engine's thinking is misaligned with what the human needs, the output will be wrong — even if it sounds right. This agent preserves the raw thinking so downstream agents can check alignment at the source.

## Technical note

Extended thinking must be enabled on the coordinator's Claude call. The coordinator captures the thinking blocks and passes them to this agent. This agent does not call Claude — it only logs what the coordinator sends it.
