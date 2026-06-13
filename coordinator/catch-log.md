# Catch Log — Schema

Every event gets one entry. Append only. Never delete.

```json
{
  "log_id": "unique string",
  "timestamp": "ISO 8601",
  "original": "the raw AI output before correction",
  "delivered": "what the user actually received",
  "corrected": true,
  "verdicts": [
    {
      "agent": "voice",
      "status": "violation",
      "rule": "V02 — No filler openings",
      "excerpt": "Sure, happy to help with that.",
      "severity": "high"
    }
  ],
  "user_response": "accepted | overridden | null"
}
```

`user_response` is the adaptation signal. Accepted means the correction was right. Overridden means it was wrong. Null means the user did not respond. The feedback loop reads this field.
