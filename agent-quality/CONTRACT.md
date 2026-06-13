# Quality Agent — Contract

This file defines what this agent promises to return.

---

## The output shape

```json
{
  "agent": "quality",
  "status": "clean | violation",
  "rule": "criterion ID and name — null if clean",
  "excerpt": "the exact or paraphrased offending text — null if clean",
  "severity": "low | medium | high — null if clean"
}
```

---

## Field by field

`agent` is always the string "quality".

`status` is "clean" or "violation".

`rule` is the ID and name of the quality criterion that was not met. Example: "Q03 — No unanswered question".

`excerpt` is the text or structural pattern that triggered the violation. For "no unanswered question" violations, the excerpt may be a description of what was missing rather than a quote of what was present. That is acceptable.

`severity` reflects how much the quality failure blocks the user. Cannot act on the output at all: high. Output is useful but weaker than it should be: medium. Output is fine but could be tighter: low.

---

## The one-verdict rule

Return the highest severity quality failure only. One verdict per call.

---

## When to return clean

If the output answers the question, gives something specific and actionable, and does not pad or summarise unnecessarily — return clean. The quality bar is high but not impossible. Most outputs that follow the voice and constraint rules will also pass this check.

The agent is not looking for perfection. It is looking for outputs that fail the user.
