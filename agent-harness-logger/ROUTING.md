# Harness Logger — Routing

This file tells you when the agent fires and what it receives.

---

## When it fires

Last. After all checkers have returned, after the coordinator has made its delivery decision, after correction has fired if it needed to. A13 fires once per exchange, always, with the complete record of what happened. No exchange exits the pipeline without writing to the harness.

---

## What it receives

The full compiled verdict record assembled by the coordinator. This includes: the input_id from A1, the human's original message, the engine's output, every agent verdict from the parallel checkers, the alignment verdict from A5, the gap verdict, whether correction fired and what it produced, the final delivery decision, and a timestamp for the exchange. The coordinator builds this record and passes it as a single JSON object.

---

## What it sends back

A confirmation: the entry ID assigned by the harness and a timestamp of when the write completed. Defined in `CONTRACT.md`. The coordinator can use the entry_id to retrieve or reference this exchange later.

---

## What happens if the harness write fails

The agent logs the failure and still returns. It does not block the pipeline. The coordinator should detect an error entry_id in the response and log the failure locally so the record can be retried or recovered. A harness write failure should never prevent the human from receiving their response.

---

## The most important routing principle

Every exchange writes to the harness. Clean exchanges, violated exchanges, corrected exchanges, exchanges where the human's question resolved the alignment gap on the second pass. The harness is the permanent record of the system operating — its value comes from completeness. A missing record is a gap in the system's ability to learn from its own behaviour over time.
