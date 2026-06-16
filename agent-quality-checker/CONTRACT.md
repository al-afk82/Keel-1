# Quality Checker — Contract

This file defines what this agent promises to return. The coordinator is built to expect exactly this shape.

---

## The output shape

```json
{
  "agent": "quality-checker",
  "status": "clean | violation",
  "rule": "criteria ID and name — null if clean",
  "excerpt": "the failing text or a description of what is missing — null if clean",
  "severity": "low | medium | high — null if clean"
}
```

---

## Field by field

`agent` is always the string "quality-checker".

`status` is "clean" or "violation". If clean, all other fields are null.

`rule` is the ID and name of the failed criterion. Example: "Q03 — No unanswered question". Human-readable. Taken from the reference file.

`excerpt` is the exact failing text — or, when the failure is an omission, a short description of what is missing. Quality failures are often about what is *absent*, so a description is allowed here where the constraints agent would always quote text.

`severity` comes from the criterion in `reference/quality-criteria.md`, not from the model's judgement. Each criterion has a fixed severity. Unlike constraints, quality criteria legitimately span `low` to `high` — `low` is a valid value here.

---

## The one-verdict rule

Return the highest severity failure only. One verdict per agent call. If multiple criteria fail, the coordinator only needs the most serious.

---

## How this differs from constraints

A constraint violation is a hard block — the corrector always fires. A quality violation triggers a *content improvement*, not a block. The output is not wrong; it is weak. The coordinator weighs quality verdicts; it does not treat them as mandatory stops.
