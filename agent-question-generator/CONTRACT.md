# Question Generator — Contract

This file defines what this agent promises to return. The coordinator is built to expect exactly this shape.

This agent fires when the alignment checker returns misaligned. It receives the misalignment reason and generates exactly one question to resolve it.

---

## The input

A JSON object containing the misalignment reason and any questions already asked:

```json
{
  "reason": "the misalignment reason from the alignment checker",
  "previous_questions": ["any questions already asked in this conversation"]
}
```

`previous_questions` may be an empty array on the first misalignment.

---

## The output shape

```json
{
  "agent": "question-generator",
  "status": "question-ready",
  "question": "one specific question addressed to the human"
}
```

---

## Field by field

`agent` is always the string "question-generator".

`status` is always "question-ready".

`question` is exactly one question. It must be specific to the misalignment reason, answerable in one sentence, and must not repeat a question already in `previous_questions`. If the human answers it, the alignment checker should return aligned on the next pass.

---

## The one-question rule

One question per call. No follow-ups, no clarifying sub-questions. The coordinator delivers this single question to the human and waits for a response before running the alignment check again.
