# Agent 12 — Identity Agent

## One job

Check whether the engine's response is consistent with its established identity across conversations. Flag any drift from that identity. Nothing else.

## What it receives

The engine's proposed output, the engine profile from Agent 04, and the engine's identity reference file.

## What it returns

```json
{
  "agent": "identity",
  "status": "consistent | drifted",
  "reason": "specific description of how the engine's response diverges from its established identity, null if consistent"
}
```

## What it does not do

It does not check the content of the output for violations. It checks the engine's persona — is the engine still being who it is supposed to be? Values, position, perspective, and character are all identity. Content belongs to other agents.

## Why this exists

An engine can shift persona across a conversation without the human noticing. It becomes more agreeable, less direct, or adopts a different point of view in response to pressure. This is identity drift. It is distinct from voice drift and constraint violations. This agent catches it.

## Identity reference file

The identity reference file defines who the engine is: its values, its position on contested questions, its communication style at the character level, and the boundaries of its persona. This file is the authority. The agent compares every response against it.
