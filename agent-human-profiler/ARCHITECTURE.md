# Human Profiler

## What it does

Reads the human's verbatim input and defines the role and scope they are operating in for this specific conversation. Role and scope are conversation-scoped — the same person asking a different question is in a different role.

## Why it exists

The alignment checker (Agent 05) needs a clear definition of both parties before it can compare them. This agent produces the human half of that comparison. Without a defined human role and scope, alignment is a guess.

## Input

The human's verbatim input, forwarded from Agent 01 (Human Logger) by the coordinator.

## Output

```json
{
  "agent": "human-profiler",
  "status": "profiled",
  "id": "human",
  "role": "the role the human is operating in for this request",
  "scope": "what the human is trying to achieve in this conversation"
}
```

## Position in the system

Runs in parallel with Agent 04 (Engine Profiler), after the loggers and before the alignment check. Its output is one of the two inputs to Agent 05.
