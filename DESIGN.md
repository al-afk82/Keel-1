# System Design

## The problem

AI outputs drift over time. Constraints get violated. The user has to manually correct the same mistakes repeatedly. This system catches drift automatically, logs it, and builds a record so corrections happen less often over time.

## The core idea

Every exchange has two things worth capturing — what the human said and what the AI was thinking before it responded. The human's next message tells you whether it worked. That signal drives everything.

## Two scenarios

**Disagreement path**

A1 logs the human input verbatim and generates a unique input_id for the exchange. A2 logs the AI's internal thinking verbatim and carries the same input_id. A3 waits for the human's next message and classifies it. If A3 detects disagreement — explicit rejection, frustration, restatement, or correction — it routes to the checking agents. The constraints agent, antipatterns agent, voice checker, quality checker, and identity agent each examine a different dimension of the failure. Every verdict carries the input_id. Findings are marked pending and sent to the verifier. The verifier confirms relevance before anything writes to the harness. The question generator produces a clarifying question back to the human. The human never sees the background process.

**Agreement path**

A1 and A2 still run and log everything. A3 detects agreement — explicit affirmation, addition, continuation, or appreciation — and routes to the tracking agents. The same checking agents run but silently. No question is generated. No interruption to the human. Findings that pass verification are filed to the harness as positive signals in the background.

## The input_id

Every human input gets a unique UUID4 the moment A1 logs it. Every agent downstream carries that ID in its verdict. This makes every harness entry traceable back to the exact exchange that triggered it.

## A3 confidence scoring

A3 returns a confidence score between 0.0 and 1.0 alongside its verdict. Above 0.75 the verdict routes immediately. Between 0.5 and 0.75 the verdict routes with a low confidence flag. Below 0.5 the verdict is uncertain and does not route to either path. Known gap: sarcasm cannot be detected in a single turn without prior context.

## The verifier

Violations do not write to the harness directly. Every finding from every agent goes to the verifier first. The verifier checks that the rule or pattern applies to the context of that specific exchange before confirming. A constraint about outreach copy does not apply to a technical explanation. Relevance must be confirmed. Only verified findings write to the harness.

## What is built

- A1 — human logger with input_id generation
- A2 — thinking logger with input_id propagation
- A3 — alignment classifier with confidence scoring and signal detection
- Constraints agent — with input_id tracing and context relevance check
- Harness — FastAPI on server, stores all verified entries
- Dashboard — live at dashboard.malecsystems.com

## What still needs to be designed

- Antipatterns agent — verification rules
- Voice checker — verification rules
- Quality checker — verification rules
- Identity agent — verification rules
- Gap analyzer — verification rules
- Question generator — verification rules
- Human profiler — verification rules
- Engine profiler — verification rules
- Verifier — full logic for what passes and fails verification
- Coordinator — routes messages between all 13 agents, entry point for every exchange, not yet built

## What still needs to be decided

- Exact verifier pass and fail criteria
- What the agreement path filing looks like in detail
- How the coordinator manages state across a multi-turn conversation
- How the system handles the uncertain verdict from A3
