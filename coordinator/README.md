# Coordinator

The central router. Every output passes through here.

## Responsibility

Receives the AI output. Sends it to all four agents in parallel. Collects verdicts. If any agent returns a high-severity violation, triggers the corrector. Returns either the original output (if clean) or the corrected output to the user.

## Flow

```
AI output
    → coordinator
        → voice agent
        → constraints agent
        → antipatterns agent
        → quality agent
    ← verdicts collected
    → if violation: corrector fires
    → output delivered to user
    → catch log updated
```

## Files in this folder

- `coordinator.js` (or equivalent) — the main router function
- `corrector.js` — rewrites the output when a violation is found
- `catch-log.js` — writes every caught violation to a persistent log for the demo UI
