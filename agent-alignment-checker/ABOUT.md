# Agent 05 — Alignment Checker

## One job

Compare the human's role and scope against the engine's role and scope. Return aligned or misaligned with a reason. Nothing else.

## What it receives

The output of Agent 03 (human profile) and Agent 04 (engine profile).

## What it returns

If aligned:
```json
{
  "agent": "alignment-checker",
  "status": "aligned",
  "reason": null
}
```

If misaligned:
```json
{
  "agent": "alignment-checker",
  "status": "misaligned",
  "reason": "specific description of where the roles or scopes diverge"
}
```

## What it does not do

It does not ask the human questions, suggest corrections, or decide what to do about misalignment. That is Agent 06's job. This agent only decides whether alignment exists.

## Why this exists

Every correction the human makes to an AI output is evidence that alignment failed. This agent catches that failure before it reaches the output. If the engine assumed the wrong role — too formal, too broad, wrong domain — the human will have to correct it. This agent stops that from happening.

## Stopping condition

Aligned means: the human's intended role and scope match the role and scope the engine took in its reasoning. If they match, the loop stops and the output moves forward. If they do not match, Agent 06 generates a question and the loop runs again.
