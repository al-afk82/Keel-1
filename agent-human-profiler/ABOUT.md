# Agent 03 — Human Profiler

## One job

Read the human's input and define their role and scope in this conversation. Nothing else.

## What it receives

The human's verbatim input from Agent 01.

## What it returns

```json
{
  "agent": "human-profiler",
  "status": "profiled",
  "id": "conversation-scoped identifier for this human",
  "role": "what role the human is operating in for this request",
  "scope": "what the human is trying to achieve in this conversation"
}
```

## What it does not do

It does not compare the human to the engine, make alignment judgements, or suggest corrections. It defines the human's position only.

## Why this exists

The alignment checker needs a clear definition of both parties before it can compare them. This agent produces the human half of that comparison. Role and scope are defined per conversation — not globally — because the same person asking different questions is operating in different roles.
