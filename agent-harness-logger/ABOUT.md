# Agent 10 — Harness Logger

## One job

Log every agent verdict from every conversation to the harness and update it. Nothing else.

## What it receives

The complete set of verdicts from all agents in the current conversation pipeline.

## What it returns

```json
{
  "agent": "harness-logger",
  "status": "logged",
  "entry_id": "unique identifier for this conversation record",
  "timestamp": "ISO 8601 timestamp"
}
```

## What it does not do

It does not analyse the verdicts, make decisions, or generate corrections. It logs and updates. The harness is read by other agents in future conversations to improve their accuracy over time.

## Harness entry format

Each entry in the harness records:
- The human input verbatim
- The engine thinking verbatim
- Human profile (role and scope)
- Engine profile (role and scope)
- Alignment result and reason if misaligned
- Gap analysis result
- Constraint verdicts
- Anti-pattern verdicts
- Final output delivered to the human

## Why this exists

Without a memory of what happened, the system cannot improve. The harness is that memory. Over time it becomes the dataset that makes every specialist agent sharper — not through retraining, but through accumulated context that informs future alignment checks.
