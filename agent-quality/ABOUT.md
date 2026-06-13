# Quality Agent — About

An output can follow every rule, avoid every known failure pattern, and still not be worth delivering. This agent catches that.

---

## The principle

Voice, constraints, and anti-patterns are about correctness. Quality is about worth. The question this agent answers is not "did this output break a rule?" It is "is this output actually useful to the person receiving it?"

That is a harder question to answer mechanically. It requires the agent to reason about intent.

---

## The distinction that matters

A voice violation is detectable from the text alone. A quality violation often requires understanding what the output was supposed to do. An output that restates the user's question without answering it passes every mechanical check and fails completely on quality.

This is why quality is a separate agent with a separate identity. It is not a stricter version of the other checks. It is a different kind of check entirely.

---

## The builder's job

The system prompt for this agent is `reference/quality-criteria.md`. Send the output text to the model, and if available, the user's original prompt. Ask one question: does this output meet the quality bar defined in the criteria? Return a verdict in the shape defined in `CONTRACT.md`.

The user's prompt matters here more than in the other agents. An output that does not answer the question is a quality violation. You cannot detect that without knowing what the question was. Pass the prompt when you have it.

---

## Where this sits

One of four agents running in parallel. Quality violations at high severity trigger the corrector. Quality violations at low severity get logged and passed through. The system does not block every imperfect output — it catches the ones that fail the user entirely.
