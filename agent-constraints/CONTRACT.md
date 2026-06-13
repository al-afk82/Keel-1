# Constraints Agent — Contract

This file defines what this agent promises to return. The coordinator is built to expect exactly this shape.

---

## The output shape

```json
{
  "agent": "constraints",
  "status": "clean | violation",
  "rule": "rule ID and name — null if clean",
  "excerpt": "the exact offending text — null if clean",
  "severity": "low | medium | high — null if clean"
}
```

---

## Field by field

`agent` is always the string "constraints".

`status` is "clean" or "violation". If clean, all other fields are null.

`rule` is the ID and name of the violated constraint. Example: "C03 — No fake social proof". Human-readable. This appears in the catch log.

`excerpt` is the exact text that triggered the violation. Not a summary. The exact words from the output.

`severity` for this agent will almost always be "high". Hard rules are hard. If a constraint in the reference file is marked medium or low, that means it is a guideline masquerading as a constraint and should be moved to a different agent.

---

## The one-verdict rule

Return the highest severity violation only. One verdict per agent call.

---

## A note on severity

If you find yourself writing a constraint rule with severity "low", stop. A low-severity constraint is not a constraint. It is a preference. Move it to the quality criteria or anti-patterns reference file. This agent's reference file should contain only rules where a violation requires immediate correction.
