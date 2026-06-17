# Human Profiler — Contract

This file defines what this agent promises to return. The alignment checker and the coordinator are built to expect exactly this shape.

---

## The output shape

```json
{
  "agent": "human-profiler",
  "status": "profiled",
  "id": "human",
  "role": "the role the human is operating in for this request",
  "scope": "what the human is trying to achieve in this conversation"
}
```

---

## Field by field

`agent` is always the string "human-profiler".

`status` is always "profiled". This agent does not pass or fail anything — it describes. There is no clean/violation outcome here.

`id` is the conversation-scoped identifier for the human. For a single-human conversation this is "human".

`role` is the hat the human is wearing for this request — student, founder, professional, beginner. Inferred from how they write and what they ask, not assumed globally.

`scope` is the concrete outcome the human needs from this specific conversation.

---

## The specificity rule

Vague role and scope make the alignment check unreliable. "A user who wants help" is not a profile. "A non-technical founder who needs a plain-language summary they can forward to investors" is. Always resolve role and scope to something the alignment checker can actually compare against.

---

## One profile only

Return one profile object per call. No commentary, no preamble, no alternatives. JSON only.
