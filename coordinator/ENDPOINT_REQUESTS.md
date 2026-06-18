# Endpoint Requests

All requests are `POST` to `http://127.0.0.1:5055/api/agent/{agent-name}` with `Content-Type: application/json`.

There are three distinct payload shapes depending on the pipeline stage.

---

## 01-logger

Fire and forget. Just the base data, no enrichment.

```json
{
  "input_id": "00000000-0000-0000-0000-000000000001",
  "human_input": "Summarise the lease agreement in two sentences.",
  "engine_response": "Here is a clear two-sentence summary of your lease agreement."
}
```

---

## 03-human-profiler / 04-engine-profiler

Same base payload as the logger. Both receive this at the same time.

```json
{
  "input_id": "00000000-0000-0000-0000-000000000001",
  "human_input": "Summarise the lease agreement in two sentences.",
  "engine_response": "Here is a clear two-sentence summary of your lease agreement."
}
```

---

## 05-alignment-classifier / 07-gap-analyzer / 08-constraints-checker / 09-anti-patterns-checker / 10-voice-checker / 11-quality-checker / 12-identity-agent / 13-verifier

All eight specialists get the same enriched context. The profiler outputs are embedded directly into the body alongside the original base fields.

```json
{
  "input_id": "00000000-0000-0000-0000-000000000001",
  "human_input": "Summarise the lease agreement in two sentences.",
  "engine_response": "Here is a clear two-sentence summary of your lease agreement.",
  "human_profile": {
    "agent": "03-human-profiler",
    "status": "profiled",
    "id": "human",
    "input_id": "00000000-0000-0000-0000-000000000001",
    "role": "operator",
    "scope": "global_access",
    "error_code": null
  },
  "engine_profile": {
    "agent": "04-engine-profiler",
    "status": "profiled",
    "id": "engine",
    "input_id": "00000000-0000-0000-0000-000000000001",
    "role": "operator",
    "scope": "global_access",
    "error_code": null
  }
}
```

> 06-question-generator is skipped for now — its Band key isnt linked yet. When it gets added back it joins this same group with the exact same payload.

---

## 14-harness-logger

Fire and forget. Gets the original base payload plus every verdict collected in step 3 as a flat array.

```json
{
  "payload": {
    "input_id": "00000000-0000-0000-0000-000000000001",
    "human_input": "Summarise the lease agreement in two sentences.",
    "engine_response": "Here is a clear two-sentence summary of your lease agreement."
  },
  "findings": [
    { "agent": "05-alignment-classifier", "status": "aligned", "certainty": "clean", ... },
    { "agent": "07-gap-analyzer",         "status": "success", "certainty": "clean", ... },
    { "agent": "08-constraints-checker",  "status": "success", "certainty": "clean", ... },
    { "agent": "09-anti-patterns-checker","status": "success", "certainty": "clean", ... },
    { "agent": "10-voice-checker",        "status": "success", "certainty": "clean", ... },
    { "agent": "11-quality-checker",      "status": "success", "certainty": "clean", ... },
    { "agent": "12-identity-agent",       "status": "success", "certainty": "clean", ... },
    { "agent": "13-verifier",             "status": "clean",   "certainty": "clean", ... }
  ]
}
```
