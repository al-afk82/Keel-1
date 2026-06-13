# Anti-patterns Agent — Contract

This file defines what this agent promises to return.

---

## The output shape

```json
{
  "agent": "antipatterns",
  "status": "clean | violation",
  "rule": "pattern ID and name — null if clean",
  "excerpt": "the exact or paraphrased offending text — null if clean",
  "severity": "low | medium | high — null if clean"
}
```

---

## Field by field

`agent` is always the string "antipatterns".

`status` is "clean" or "violation".

`rule` is the ID and name of the anti-pattern matched. Example: "AP02 — Performed confidence". Human-readable.

`excerpt` is the text from the output that exhibits the pattern. For anti-patterns, this may be a paraphrase rather than an exact quote, because the issue is often structural rather than a specific phrase. That is acceptable here where it is not in the voice or constraints agents.

`severity` reflects the consequence of the failure pattern. A pattern that causes the user to act on false certainty is high. A pattern that produces unnecessary complexity is low.

---

## The one-verdict rule

Return the highest severity match only. One verdict per call.

---

## The false positive problem

This agent is the most likely to produce false positives because it reasons about patterns rather than checking rules. If the model is uncertain, the verdict should be clean. A system that cries wolf on anti-patterns loses the user's trust. A system that occasionally misses one does not.

Build the model prompt with an explicit instruction: when in doubt, return clean.
