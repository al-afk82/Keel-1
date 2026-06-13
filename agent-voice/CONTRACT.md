# Voice Agent — Contract

This file defines what this agent promises to return. Every builder working on this agent is bound by this contract. The coordinator is built to expect exactly this shape.

---

## The output shape

```json
{
  "agent": "voice",
  "status": "clean | violation",
  "rule": "rule ID and name — null if clean",
  "excerpt": "the exact offending text — null if clean",
  "severity": "low | medium | high — null if clean"
}
```

---

## Field by field

`agent` is always the string "voice". It tells the coordinator which agent produced this verdict.

`status` is either "clean" or "violation". Nothing else. If the output passes all rules, status is clean and the remaining fields are null.

`rule` is the ID and name of the rule that was violated. Example: "V02 — No filler openings". This is what appears in the catch log and the demo UI. Make it human-readable.

`excerpt` is the exact text from the output that triggered the violation. Not a paraphrase. Not a summary. The exact words. This is what gets shown in the before-and-after comparison.

`severity` is the weight of the violation. Low means the output is slightly off. Medium means it is noticeably wrong. High means the coordinator must trigger the corrector before the output reaches the user.

---

## The one-verdict rule

If multiple rules are violated, return the highest severity violation only. The coordinator is not built to handle arrays of violations per agent. One verdict. Highest severity wins.

---

## Why this contract exists

Four agents run in parallel. The coordinator cannot know in advance which agents will flag a violation. It can only work with a consistent shape across all four. If one agent returns a different structure, the coordinator breaks.

Do not change the shape without updating the coordinator and all other agent contracts.
