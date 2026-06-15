# Engine Profiler

## What it does

Reads the engine's internal thinking and defines the role and scope the engine actually assumed in this conversation — inferred from its own reasoning, not from the human's request. The role the engine took is not always the role the human intended.

## Why it exists

The alignment checker (Agent 05) needs a clear definition of both parties before it can compare them. This agent produces the engine half of that comparison. Surfacing the engine's self-assumed role is what makes misalignment detectable.

## Input

The engine's verbatim internal thinking, forwarded from Agent 02 (Thinking Logger) by the coordinator.

## Output

```json
{
  "agent": "engine-profiler",
  "status": "profiled",
  "id": "engine",
  "role": "the role the engine assumed in its reasoning",
  "scope": "what the engine believed it was trying to achieve"
}
```

## Position in the system

Runs in parallel with Agent 03 (Human Profiler), after the loggers and before the alignment check. Its output is one of the two inputs to Agent 05.
