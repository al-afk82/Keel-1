# Agent 10 — Voice Checker

## One job

Check the engine's output against the established voice rules. Flag any violation. Nothing else.

## What it receives

The engine's proposed output and the gap from Agent 07.

## What it returns

```json
{
  "agent": "voice-checker",
  "status": "clean | violation",
  "rule": "rule ID and name if violated, null if clean",
  "excerpt": "exact offending text if violated, null if clean",
  "severity": "high | medium | low | null"
}
```

## What it does not do

It does not check constraints, anti-patterns, or quality. It checks voice only. Tone, style, phrasing patterns, and writing rules are all voice. Everything else belongs to a different agent.

## Why this exists

An output can be factually correct and constraint-compliant but still wrong because it sounds like the wrong person. Voice drift is subtle and accumulates across a conversation. This agent catches it before it reaches the user.
