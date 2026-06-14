# Gap Analyzer

## What it does

Identifies missing context in the conversation that is causing the engine to operate on incomplete information. Flags what the engine does not know that it should.

## Why it exists

Engines hallucinate and drift most when context is thin. The gap analyzer finds the specific missing pieces — background on the user, prior decisions, domain knowledge — so the coordinator can flag them rather than letting the engine invent answers to fill the void.

## Input

The full conversation context and the engine's response, passed in by the coordinator.

## Output

```json
{
  "agent": "gap-analyzer",
  "status": "complete" | "gaps-found",
  "gaps": ["description of missing context"]
}
```

## Position in the system

Runs in parallel. Its output is most useful when combined with the question generator — together they map what was not asked and what was not known.
