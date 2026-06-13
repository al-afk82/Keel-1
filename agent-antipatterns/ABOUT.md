# Anti-patterns Agent — About

Some outputs look correct and are not. They pass the voice check. They pass the constraint check. They read as reasonable. And they consistently produce bad outcomes.

This agent catches those. Not rule violations. Patterns of failure.

---

## The principle

Rules are written in advance. Anti-patterns are discovered through experience. Someone tried something, it failed in a recognisable way, and that failure got documented so it would not happen again.

The difference matters for how you build this agent. A rule check is binary — did the output contain the forbidden phrase? An anti-pattern check requires judgment — does this output match the shape of a known failure?

That means the model doing this check needs to reason, not just scan. Give it the failure description and ask: does this output exhibit this pattern?

---

## The story that makes this concrete

A system was built to answer questions about documented knowledge. The constraint file said to check documented sources before answering. The agent passed that check. But when a user asked about a specific person, the agent answered from general knowledge instead of loading the file that was the authority on that person.

No rule was technically broken. The constraint said "check before answering" and the agent checked. It just checked the wrong thing. The anti-pattern was "answering from pattern-match instead of documented knowledge" — a failure mode that had happened before, in a different context, with the same shape.

That is what this agent catches.

---

## The builder's job

The system prompt for this agent is `reference/antipatterns.md`. Send the output text and the anti-pattern descriptions to the model. Ask: does this output exhibit any of these known failure patterns? Return a verdict in the shape defined in `CONTRACT.md`.

This agent requires more reasoning from the model than the others. A voice agent scans for phrases. This agent identifies patterns. Budget slightly more tokens for this call.

---

## Where this sits

One of four agents running in parallel. Violations here are high severity when the failure pattern has a direct negative consequence for the user. Low severity when the pattern is a quality issue rather than a correctness issue.
