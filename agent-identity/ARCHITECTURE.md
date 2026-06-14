# Identity Agent

## What it does

Checks whether the engine's response is consistent with its established identity. Directness, position-holding under pressure, honesty over comfort. Flags when the engine has shifted persona.

## Why it exists

Identity drift is the subtlest and most dangerous form of drift. The engine does not violate a rule — it just becomes a different version of itself. More agreeable, less direct, more flattering. Over time the user gets a different engine than the one they configured. The identity agent catches that shift turn by turn.

## Input

The engine's response, passed in by the coordinator. Identity definition loaded from `reference/identity.md`.

## Output

```json
{
  "agent": "identity",
  "status": "consistent" | "drifted",
  "reason": "description of how the response diverges from established identity"
}
```

## Position in the system

Runs in parallel. A drifted verdict is high priority — identity drift compounds across sessions if not caught early.
