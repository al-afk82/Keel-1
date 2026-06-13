# Coordinator — Contract

This file defines what the coordinator promises to return to the system that calls it.

---

## The output shape

```json
{
  "output": "the text delivered to the user — corrected or original",
  "corrected": true,
  "verdicts": [
    { "agent": "voice", "status": "clean", "rule": null, "excerpt": null, "severity": null },
    { "agent": "constraints", "status": "violation", "rule": "C01", "excerpt": "...", "severity": "high" },
    { "agent": "antipatterns", "status": "clean", "rule": null, "excerpt": null, "severity": null },
    { "agent": "quality", "status": "clean", "rule": null, "excerpt": null, "severity": null }
  ],
  "log_id": "unique string referencing the catch log entry"
}
```

---

## Field by field

`output` is the text the user receives. If the corrector fired, this is the corrected text. If no correction was needed, this is the original text unchanged.

`corrected` is true if the corrector fired. False otherwise. This field drives the demo UI — it is what lights up the "caught and corrected" indicator.

`verdicts` is all four agent verdicts, always. Even if three are clean, include all four. The catch log and demo UI display all four.

`log_id` is the unique identifier for the event written to the catch log. The demo UI uses this to link the output to its log entry.

---

## What the coordinator never does

Never modifies the output directly. Correction is the corrector's job. The coordinator calls the corrector and returns what it sends back. The coordinator is the router, not the editor.

Never exposes agent errors to the user. Log them, return the original output, move on.

Never returns without writing to the catch log. Every event gets logged. The feedback loop depends on a complete log.
