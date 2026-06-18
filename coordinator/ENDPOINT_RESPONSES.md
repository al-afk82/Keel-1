# Endpoint Responses

All responses are `200 OK` with `Content-Type: application/json`.

There are two response shapes: a profile (profilers only) and a verdict (everyone else). Loggers return a minimal ack.

---

## 01-logger / 14-harness-logger

Simple ack, nothing useful inside. Dont parse this.

```json
{
  "agent": "01-logger",
  "status": "logged"
}
```

---

## 03-human-profiler / 04-engine-profiler

Returns a profile blob. The coordinator picks this up and embeds it into the context for step 3.

| field | type | notes |
|---|---|---|
| `agent` | string | name of the profiler |
| `status` | string | `"profiled"` on success, `"error"` on failure |
| `id` | string \| null | `"human"` or `"engine"` |
| `input_id` | string \| null | echoes back the input_id it received |
| `role` | string | e.g. `"operator"` |
| `scope` | string | `"global_access"` or `"restricted_access"` |
| `error_code` | string \| null | set if something went wrong |

```json
{
  "agent": "03-human-profiler",
  "status": "profiled",
  "id": "human",
  "input_id": "00000000-0000-0000-0000-000000000001",
  "role": "operator",
  "scope": "global_access",
  "error_code": null
}
```

---

## 05-alignment-classifier / 07-gap-analyzer / 08-constraints-checker / 09-anti-patterns-checker / 10-voice-checker / 11-quality-checker / 12-identity-agent / 13-verifier

All specialists return the same verdict shape.

| field | type | notes |
|---|---|---|
| `agent` | string | name of the agent that produced this |
| `status` | string | `"aligned"` / `"success"` / `"clean"` / `"violation"` |
| `certainty` | string | `"clean"` or `"violation"` |
| `rule` | string \| null | which rule was triggered, if any |
| `excerpt` | string \| null | relevant snippet from the payload, if any |
| `severity` | string \| null | `"high"` or `"medium"`, null when clean |
| `reason` | string \| null | short explanation of the finding |
| `error_code` | string \| null | set if the agent itself errored |

**Clean verdict:**
```json
{
  "agent": "07-gap-analyzer",
  "status": "success",
  "certainty": "clean",
  "rule": null,
  "excerpt": null,
  "severity": null,
  "reason": null,
  "error_code": null
}
```

**Violation verdict:**
```json
{
  "agent": "05-alignment-classifier",
  "status": "misaligned",
  "certainty": "violation",
  "rule": null,
  "excerpt": "Requested context out-of-bounds",
  "severity": null,
  "reason": "Scope mismatch detected",
  "error_code": null
}
```

**Verifier violation (13):**
```json
{
  "agent": "13-verifier",
  "status": "violation",
  "certainty": "violation",
  "rule": "SUPREME_GUARDRAIL",
  "excerpt": "Trace payload violation",
  "severity": "high",
  "reason": null,
  "error_code": null
}
```

---

## Error sentinels

If an agent times out or the network drops, the coordinator doesnt crash — it substitutes a sentinel verdict and keeps going.

| error_code | cause |
|---|---|
| `NETWORK_DISCONNECT` | agent didnt respond |
| `JSON_PARSE_ERR` | response wasnt valid JSON |
| `DESERIALIZATION_ERR` | JSON was valid but didnt match the expected shape |
| `AGENT_TIMEOUT` | no reply within 30 seconds |

```json
{
  "agent": "10-voice-checker",
  "status": "violation",
  "certainty": "violation",
  "rule": null,
  "excerpt": null,
  "severity": null,
  "reason": null,
  "error_code": "AGENT_TIMEOUT"
}
```
