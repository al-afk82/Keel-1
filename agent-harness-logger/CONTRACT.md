# Harness Logger — Contract

This file defines what this agent promises to return. The coordinator is built to expect exactly this shape.

This is A13 — the last agent in the pipeline. It receives the compiled verdict record from the coordinator and writes it to the harness API. It is the only agent that writes to external storage.

---

## The input

The full compiled verdict record for one conversation exchange, in JSON format. The coordinator assembles this from all agent verdicts before sending it here.

---

## The output shape

```json
{
  "agent": "harness-logger",
  "status": "logged",
  "entry_id": "the entry ID returned by the harness API",
  "timestamp": "ISO 8601 UTC timestamp"
}
```

---

## Field by field

`agent` is always the string "harness-logger".

`status` is "logged" on success. If the harness write fails, this agent still returns — the coordinator should treat a missing or error entry_id as a failed write and log the failure locally.

`entry_id` is the ID assigned by the harness API to the stored entry. The coordinator can use this to look up the entry later.

`timestamp` is the UTC time at the moment of logging.

---

## Harness write behaviour

This agent writes to the harness at `HARNESS_URL/write` using the `x-secret` header. The write happens before the Band response is sent. If the write fails, the agent logs the error and continues — it does not block the pipeline.
