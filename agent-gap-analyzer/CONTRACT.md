# Gap Analyzer — Contract

This file defines what this agent promises to return. The coordinator is built to expect exactly this shape.

This agent compares what the human asked against what the engine produced. It does not judge whether the output is good or bad — it describes the difference between intent and output.

---

## The input

A JSON object containing the human's original input and the engine's proposed output:

```json
{
  "input": "the human's original message",
  "output": "the engine's proposed response"
}
```

---

## The output shape

If no gap:
```json
{
  "agent": "gap-analyzer",
  "status": "no-gap",
  "gap": null
}
```

If a gap exists:
```json
{
  "agent": "gap-analyzer",
  "status": "gap-found",
  "gap": "specific description of what the human asked for versus what the engine produced"
}
```

---

## Field by field

`agent` is always the string "gap-analyzer".

`status` is "no-gap" or "gap-found".

`gap` is null when no gap exists. When a gap is found, it describes specifically what is missing or wrong — what the human asked for that the engine did not deliver, or what the engine added that the human did not ask for. It is a description, not a verdict.

---

## What counts as a gap

A gap exists when the engine's output does not fully address what the human asked, answers the wrong question, misses key parts of the request, or adds things the human did not ask for. Partial coverage counts as a gap. Over-answering counts as a gap.
