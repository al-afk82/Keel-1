# Voice Agent — Routing

This file tells you when the agent fires and what it receives. It is the contract between the coordinator and this agent.

---

## When it fires

Always. Every output. No exceptions.

The temptation when building is to add filters — only check long outputs, only check formal writing, only check when the user has flagged a concern. Resist that. Filters introduce gaps. Gaps become the exact place where drift hides.

---

## What it receives

A plain text string. The AI output being checked. Nothing else.

The agent does not need context about the user, the conversation history, or what the output is for. The voice rules in the reference file are self-contained. Either the output follows them or it does not.

---

## What it sends back

A single verdict object. Defined in `CONTRACT.md`.

---

## The routing decision

One question determines whether this agent's verdict matters: is the severity high?

If yes, the coordinator sends the output to the corrector before it reaches the user. If no, the output passes through and the verdict is logged. The agent does not make this decision. The coordinator does. This agent's only job is to return an honest verdict.
