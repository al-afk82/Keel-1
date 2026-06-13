# Coordinator — Routing

This file defines the flow. Every decision point is documented here.

---

## The flow

```
Raw AI output arrives
    → Send to all four agents in parallel
    → Collect four verdict objects
    → Check verdicts for severity "high"
    → If any high: send to corrector, deliver corrected output
    → If none high: deliver original output
    → Log the event either way
    → Return delivered output to user
```

---

## Parallel not sequential

All four agents run at the same time. Not one after another. Parallel.

Sequential agent calls multiply latency. If each agent takes 500ms, sequential execution costs two seconds before the user sees anything. Parallel execution costs 500ms regardless of how many agents run.

Build the coordinator to fire all four calls simultaneously and await all four results before making the correction decision.

---

## The correction threshold

Correction fires on any verdict with severity "high". Not medium. Not low. High only.

Medium and low violations get logged and passed through. The system does not intercept every imperfect output. It intercepts the ones that would damage trust or break a hard rule.

This threshold is a design decision, not a technical constraint. If you want the system to intercept medium violations too, change the threshold here. But start with high only. A system that blocks too much output becomes friction rather than a filter.

---

## What happens when an agent fails

If an agent call returns an error instead of a verdict, the coordinator treats it as clean and logs the failure. An agent error should never block output delivery. Log it, surface it in the catch log, and let the output through.

A broken agent is a bug to fix. It is not a reason to block the user.
