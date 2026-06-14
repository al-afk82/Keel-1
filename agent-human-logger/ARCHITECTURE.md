# Human Logger

## What it does

Receives the human's input and logs it verbatim to the harness. No interpretation, no modification. The exact words the human typed, stored as the ground truth for this conversation turn.

## Why it exists

Every other agent needs to know what the human actually said. If drift is detected later, the system needs to compare the engine's output against the original intent. That comparison is only possible if the raw input is preserved exactly.

## Input

The human's message, passed in by the coordinator.

## Output

```json
{
  "agent": "human-logger",
  "status": "logged",
  "input": "the exact human message"
}
```

## Position in the system

First to run. Its output feeds into the alignment checker, human profiler, and gap analyzer — any agent that needs to compare against original intent.
