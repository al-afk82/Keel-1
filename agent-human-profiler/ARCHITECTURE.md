# Human Profiler

## What it does

Builds a model of the human based on their input patterns. Communication style, vocabulary, level of technical knowledge, implied goals, recurring concerns. Updated on every turn.

## Why it exists

The engine cannot stay aligned with a human it does not understand. The human profiler gives the system a stable picture of who the user is so every other agent can calibrate against it. A constraint violation means something different for a technical expert than for a first-time user.

## Input

The human's current message plus any prior context passed in by the coordinator.

## Output

```json
{
  "agent": "human-profiler",
  "status": "logged",
  "profile": {
    "communication_style": "...",
    "technical_level": "...",
    "implied_goal": "..."
  }
}
```

## Position in the system

Runs in parallel. Its output informs the alignment checker and the coordinator's final decision on how to frame a corrected response.
