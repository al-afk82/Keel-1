# Constraints Agent — About

Some things must never happen. Not "should not usually happen." Never. This agent exists to enforce that line. No exceptions, no edge cases, no context that makes a violation acceptable.

---

## The principle

Every system has rules that bend and rules that do not. Most quality checks are about degree — this output is slightly off, that one is noticeably wrong. Constraints are different. A constraint violation is binary. Either the rule was broken or it was not.

This agent does not judge degree. It checks the line.

---

## Why constraints need their own agent

The temptation when building is to combine constraint checking with voice checking or quality checking into one general evaluation agent. Do not do this.

A general evaluation agent produces general verdicts. It will tell you something is "slightly off" when you need to know whether a hard rule was broken. The precision disappears. The hard rules get treated like preferences.

Give hard rules their own agent and the coordinator knows exactly what it is dealing with. A violation from this agent means the corrector fires. No debate.

---

## The builder's job

The system prompt for this agent is the contents of `reference/constraints.md`. Send the output text and the constraint list to the model. Ask one question: does this output violate any of these rules? Return a verdict in the shape defined in `CONTRACT.md`.

The rules in the reference file are written as binary checks. Use that. Do not ask the model to grade severity on a scale. The severity for each rule is already defined in the reference file.

---

## Where this sits

One of four agents running in parallel. The coordinator treats a high-severity verdict from this agent as a mandatory correction trigger. There is no override on a hard rule violation.
