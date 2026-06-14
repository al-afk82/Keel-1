# Harness Logger

## What it does

Receives the compiled verdict record from the coordinator and writes it to the harness API. Every verdict from every agent, timestamped and stored in SQLite.

## Why it exists

The harness is the memory of the system. Without it, every session starts from zero. With it, you can see patterns across conversations — which constraints get violated most, which agents fire most often, how drift evolves over time. The harness logger is the bridge between one conversation and the system getting smarter.

## Input

The full compiled verdict record from the coordinator, containing all agent outputs for this turn.

## Output

```json
{
  "agent": "harness-logger",
  "status": "logged",
  "entry_id": "UUID of the stored record",
  "timestamp": "ISO 8601"
}
```

## Position in the system

Last to run. Depends on the coordinator having assembled all verdicts. Its output is visible in real time at dashboard.malecsystems.com.
