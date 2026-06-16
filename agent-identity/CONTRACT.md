# Identity Agent — Contract

This file defines what this agent promises to return. The coordinator is built to expect exactly this shape.

This agent does **not** use the standard rule/excerpt/severity verdict. Identity drift is not a discrete rule breach — it is a shift in persona — so the verdict carries a `reason`, like the alignment checker, not a quoted rule.

---

## The output shape

```json
{
  "agent": "identity",
  "status": "consistent | drifted",
  "reason": "specific description of how the response diverges from the established identity — null if consistent"
}
```

---

## Field by field

`agent` is always the string "identity".

`status` is "consistent" or "drifted". If consistent, `reason` is null.

`reason` is a specific description of the drift — which characteristic was abandoned and where. Not "the tone is off." Instead: "Opened with encouragement the identity forbids, and softened the previous turn's position after the human pushed back." The coordinator uses this to drive the correction, so it must name the divergence concretely.

---

## One verdict only

One verdict per call. If multiple identity signals drift at once, describe the most significant one in `reason`. No commentary, no preamble. JSON only.

---

## Why no severity field

Constraints and quality grade severity because their failures vary in magnitude. Identity drift is binary at the point of detection — the persona either held or it shifted. The signal the coordinator needs is the `reason`, so it can correct the specific divergence. A drifted verdict is treated as high priority regardless: identity drift compounds across sessions if not caught early.
