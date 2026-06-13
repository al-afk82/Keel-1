# Feedback Loop — Contract

This file defines what the feedback loop produces.

---

## The output

A file written to `work/proposed-rules.md`. One entry per proposed rule. Appended on each run — do not overwrite previous proposals.

---

## The proposal format

Each entry follows this structure:

```
## Proposed Rule — [date of this run]

Agent: [voice | constraints | antipatterns | quality]
Proposed ID: [next available ID for that agent — e.g. V06, C06, AP06, Q06]
Rule: [the rule statement in the same format used by that agent's reference file]
Severity: [low | medium | high]
Based on: [N] accepted corrections matching this pattern
Excerpts:
  - [exact quote from catch log entry 1]
  - [exact quote from catch log entry 2]
  - [exact quote from catch log entry 3]

Status: awaiting confirmation
```

---

## Field by field

`Agent` tells the user which reference file this rule belongs in.

`Proposed ID` uses the next sequential ID in that agent's numbering. Check the reference file before assigning.

`Rule` is written in the same format as the existing rules in that agent's reference file. Consistency matters — the agent reads these rules as its system prompt. A rule that does not match the format of the others introduces ambiguity.

`Based on` and `Excerpts` are the evidence. The user needs to see the pattern before confirming the rule. Include at least three excerpts. Include more if the pattern appeared many times.

`Status` is always "awaiting confirmation" when written. The user changes it to "confirmed" or "rejected" when they review.

---

## What happens after confirmation

A confirmed rule gets appended to the relevant agent's reference file. The proposed-rules.md entry is updated to "confirmed" with the date. The agent now enforces the new rule on every subsequent output.

No other changes are needed. No retraining. No redeployment. The agent's intelligence lives in its reference file. Update the file, update the agent.
