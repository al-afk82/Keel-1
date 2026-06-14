# Thinking Logger

## What it does

Captures the engine's internal reasoning before the final response is produced. Uses Anthropic's extended thinking API to surface the chain of thought the model used to arrive at its answer.

## Why it exists

Drift often lives in the reasoning, not the output. An engine can produce a response that looks clean while the internal logic is misaligned with the human's intent. This agent makes that reasoning visible and stores it for the alignment checker and gap analyzer to inspect.

## Input

The human's message, passed in by the coordinator. The agent calls the engine with extended thinking enabled.

## Output

```json
{
  "agent": "thinking-logger",
  "status": "logged",
  "thinking": "the engine's internal reasoning chain"
}
```

## Position in the system

Runs in parallel with all other agents. Its output is the primary input for the alignment checker — you cannot check alignment without seeing the reasoning.
