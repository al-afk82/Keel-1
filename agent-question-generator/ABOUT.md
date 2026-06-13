# Agent 06 — Question Generator

## One job

When alignment fails, generate exactly one question to ask the human that resolves the gap. Nothing else.

## What it receives

The misalignment reason from Agent 05.

## What it returns

```json
{
  "agent": "question-generator",
  "status": "question-ready",
  "question": "one specific question addressed to the human"
}
```

## What it does not do

It does not generate multiple questions. It does not suggest answers. It does not attempt to resolve the misalignment itself. One question. That is all.

## Why this exists

When the human and engine are misaligned, the natural response is to ask the human to clarify. But asking the wrong question, or asking too many questions, wastes the human's time and breaks the flow. This agent generates the single most useful question given the specific gap — no more.

## Question quality standard

The question must be answerable in one sentence. It must be specific to the misalignment reason. It must not ask for information the system already has. If the human answers it, Agent 05 should return aligned on the next pass.
