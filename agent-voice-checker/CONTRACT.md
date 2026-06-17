# Voice Checker — Contract

This file defines what this agent promises to return. The coordinator is built to expect exactly this shape.

This agent checks whether an AI output violates the established voice and tone rules. It uses the same verdict shape as the constraints agent — rule ID, excerpt, severity — because voice violations are discrete rule breaches, not shifts in persona.

---

## The input

The AI output to check, passed as raw text.

---

## The output shape

If a violation is found:
```json
{
  "agent": "voice-checker",
  "status": "violation",
  "rule": "rule ID and name",
  "excerpt": "the exact offending text",
  "severity": "high | medium"
}
```

If no violation:
```json
{
  "agent": "voice-checker",
  "status": "clean",
  "rule": null,
  "excerpt": null,
  "severity": null
}
```

---

## Field by field

`agent` is always the string "voice-checker".

`status` is "violation" or "clean". If clean, all other fields are null.

`rule` is the ID and name of the violated voice rule. Taken from the reference file.

`excerpt` is the exact offending text from the output. Not a paraphrase — the exact words.

`severity` is "high" or "medium". Voice checker does not use "low" — if a voice rule is low severity, it is a preference, not a rule, and belongs in a different reference file.

---

## The one-verdict rule

Return the highest severity violation only. One verdict per call. If multiple rules are violated, the coordinator only receives the most serious.
