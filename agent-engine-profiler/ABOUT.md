# Agent 04 — Engine Profiler

## One job

Read the engine's internal thinking and define its role and scope in this conversation. Nothing else.

## What it receives

The engine's verbatim thinking from Agent 02.

## What it returns

```json
{
  "agent": "engine-profiler",
  "status": "profiled",
  "id": "conversation-scoped identifier for this engine instance",
  "role": "what role the engine has assumed for this response",
  "scope": "what the engine believes it is trying to achieve"
}
```

## What it does not do

It does not compare the engine to the human, make alignment judgements, or suggest corrections. It defines the engine's position only.

## Why this exists

The engine assumes a role and scope every time it responds. It is not always the role the human intended. This agent surfaces what role the engine actually took — from its own reasoning — so the alignment checker can compare it against what the human needed.
