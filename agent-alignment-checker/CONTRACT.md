# Alignment Checker — Contract

This file defines what this agent promises to return. The coordinator is built to expect exactly this shape.

This is A5. It receives the human profile from A3 and the engine profile from A4 and checks whether they are aligned. It does not check content quality, voice, or constraints — only whether the human's intended role and scope match what the engine assumed.

---

## The input

A JSON object containing both profiles:

```json
{
  "human_profile": {
    "agent": "human-profiler",
    "status": "profiled",
    "id": "human",
    "role": "...",
    "scope": "..."
  },
  "engine_profile": {
    "agent": "engine-profiler",
    "status": "profiled",
    "id": "engine",
    "role": "...",
    "scope": "..."
  }
}
```

---

## The output shape

If aligned:
```json
{
  "agent": "alignment-checker",
  "status": "aligned",
  "reason": null
}
```

If misaligned:
```json
{
  "agent": "alignment-checker",
  "status": "misaligned",
  "reason": "specific description of where the roles or scopes diverge"
}
```

---

## Field by field

`agent` is always the string "alignment-checker".

`status` is "aligned" or "misaligned".

`reason` is null when aligned. When misaligned, it describes specifically where the roles or scopes diverge — not a general statement, a concrete description of the gap. The coordinator uses this reason to route to the question generator.

---

## Misalignment threshold

On the first message of a conversation, this agent requires strong evidence before returning misaligned. Ambiguity alone is not enough. A mismatch must be clear and specific.
