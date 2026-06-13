# Drift Agent

A multi-agent alignment layer that sits between a human and an AI engine. It captures the human's input, captures the engine's internal thinking, checks whether the human and engine are operating with aligned roles and scope, and continuously improves the engine's output through a structured feedback loop.

The goal is simple: the user spends less time correcting AI. The system learns what the user actually wants and enforces it automatically.

---

## The problem

AI outputs drift. The engine does not know what the human actually wants. The human does not know why the engine responded the way it did. Every correction is wasted time. Every misalignment compounds.

This system intercepts the conversation before the output reaches the user, checks alignment at the reasoning layer, and only releases the output when it passes.

---

## How it works

Every conversation flows through thirteen specialist agents coordinated by a fourteenth. Each agent does exactly one job. No agent does two.

The coordinator receives the human's message and the engine's thinking before either reaches the other party. It routes both through the agent pipeline. If alignment fails, the system asks the human one question to resolve it. If any check fails — voice, identity, constraints, anti-patterns, or quality — the output is corrected before delivery. Every result is logged to a harness that makes the next conversation better.

---

## Agent map

| Agent | Folder | One job |
|-------|--------|---------|
| 01 Human Logger | agent-human-logger/ | Log the human's input verbatim |
| 02 Thinking Logger | agent-thinking-logger/ | Log the engine's internal thinking verbatim |
| 03 Human Profiler | agent-human-profiler/ | Tag the human ID and define their role and scope in this conversation |
| 04 Engine Profiler | agent-engine-profiler/ | Tag the engine ID and define its role and scope in this conversation |
| 05 Alignment Checker | agent-alignment-checker/ | Compare human role and scope against engine role and scope. Output aligned or misaligned with reason |
| 06 Question Generator | agent-question-generator/ | When alignment fails, generate one question to ask the human that resolves the gap |
| 07 Gap Analyzer | agent-gap-analyzer/ | Compare what the human asked against what the engine produced. Output the gap |
| 08 Constraints Checker | agent-constraints/ | Check the gap against the constraints library. Flag violations |
| 09 Anti-patterns Checker | agent-antipatterns/ | Check the gap against the anti-patterns library. Flag matches |
| 10 Voice Checker | agent-voice-checker/ | Check the output against voice rules. Flag tone and style violations |
| 11 Quality Checker | agent-quality-checker/ | Check the output against quality criteria. Flag completeness and accuracy failures |
| 12 Identity Agent | agent-identity/ | Check that the engine's response is consistent with its established identity. Flag persona drift |
| 13 Harness Logger | agent-harness-logger/ | Log every agent verdict to the harness and update it |
| Coordinator | coordinator/ | Manage state, route messages between agents, decide when the loop continues or stops |

---

## Pipeline flow

```
Human message received
        |
  [Agent 01] Log human input
  [Agent 02] Log engine thinking
        |
  [Agent 03] Profile human
  [Agent 04] Profile engine
        |
  [Agent 05] Check alignment
        |
   Misaligned?
   YES → [Agent 06] Generate question → ask human → loop from Agent 03
   NO  ↓
  [Agent 07] Analyze gap
        |
  Run in parallel:
  [Agent 08] Constraints
  [Agent 09] Anti-patterns
  [Agent 10] Voice
  [Agent 11] Quality
  [Agent 12] Identity
        |
   Any violation?
   YES → Coordinator corrects output → deliver to human
   NO  → Deliver output to human
        |
  [Agent 13] Log all verdicts to harness
```

---

## The alignment loop

When Agent 05 returns misaligned, Agent 06 generates one question. That question goes to the human. The human answers. The loop runs again from Agent 03. This continues until Agent 05 returns aligned. Only then does the output move forward to Agent 07.

This loop is the core of the system. It is what reduces the time the human spends correcting AI.

---

## The harness

Agent 13 logs every verdict from every agent into a structured harness. The harness is the system's memory. It tracks what violated what, how often, and in which context. Over time the specialist agents read from the harness and get sharper. The output improves without the human doing anything.

---

## Verdict schema

Every specialist agent returns the same base shape:

```json
{
  "agent": "agent-name",
  "status": "clean | violation | aligned | misaligned | logged | profiled | gap-found | no-gap | question-ready | consistent | drifted",
  "rule": "rule ID and name if applicable, null if not",
  "excerpt": "exact offending text if applicable, null if not",
  "severity": "high | medium | low | null"
}
```

See shared/schema.json for the full schema for each agent type.

---

## Stack

Band — coordination layer between agents. Each agent is a remote agent registered in Band. The coordinator routes messages through Band sessions.

Claude Sonnet 4.6 — the model powering every agent. Extended thinking is enabled on Agent 02 to capture the engine's internal reasoning before the output is formed.

LangGraph — the graph runtime inside each agent. Each agent is a single-node graph that receives a message, calls Claude, and returns a verdict.

Python with uv — dependency management.

---

## Build status

| Agent | Status |
|-------|--------|
| 01 Human Logger | pending |
| 02 Thinking Logger | pending |
| 03 Human Profiler | pending |
| 04 Engine Profiler | pending |
| 05 Alignment Checker | pending |
| 06 Question Generator | pending |
| 07 Gap Analyzer | pending |
| 08 Constraints Checker | live |
| 09 Anti-patterns Checker | pending |
| 10 Voice Checker | pending |
| 11 Quality Checker | pending |
| 12 Identity Agent | pending |
| 13 Harness Logger | pending |
| Coordinator | pending |

---

## Setup

See build-notes/constraints-agent.md for the reference implementation. Every other agent follows the same setup. Only the reference file and system prompt change.
