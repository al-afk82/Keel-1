# Thinking Logger — Contract

This file defines what this agent promises to return. The coordinator is built to expect exactly this shape.

This is A2. It receives the engine's internal thinking and the input_id from A1. It does not generate a new ID — it carries the one from A1 so this log entry is tied to the same exchange.

---

## The input

A JSON object containing two fields:

```json
{
  "input_id": "the UUID4 from A1",
  "thinking": "the engine's internal dialog before its final response"
}
```

---

## The output shape

```json
{
  "agent": "thinking-logger",
  "input_id": "the input_id from A1 — unchanged",
  "status": "logged",
  "thinking": "the engine thinking verbatim",
  "timestamp": "ISO 8601 UTC timestamp"
}
```

---

## Field by field

`agent` is always the string "thinking-logger".

`input_id` is carried unchanged from A1. This agent does not generate or modify it.

`status` is always "logged".

`thinking` is the engine's internal dialog verbatim. No summarising, no trimming.

`timestamp` is the UTC time at the moment of logging in ISO 8601 format.
