# Engine Profiler

## What it does

Builds a model of the engine's behaviour over time. Tracks how the engine responds, where it tends to drift, which constraints it violates most frequently, and how its tone shifts across turns.

## Why it exists

Drift is not random — engines have patterns. The engine profiler identifies those patterns so the enforcement layer knows where to look hardest. An engine that consistently softens positions under pressure will trigger the identity agent more than the constraints agent.

## Input

The engine's current response and the thinking log from the thinking logger, passed in by the coordinator.

## Output

```json
{
  "agent": "engine-profiler",
  "status": "logged",
  "profile": {
    "tone": "...",
    "drift_tendency": "...",
    "constraint_risk": "..."
  }
}
```

## Position in the system

Runs in parallel. Its output feeds the alignment checker and the coordinator's risk assessment before verdicts are assembled.
