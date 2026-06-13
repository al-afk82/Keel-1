# Voice Agent — About

Every AI system drifts. Given enough turns, it stops sounding like the person it is supposed to represent and starts sounding like an AI. This agent exists to catch that the moment it happens, before the user ever sees it.

---

## The principle

The job is narrow on purpose. This agent checks one thing: does this output sound like the right person? Not whether it is accurate. Not whether it is well structured. Not whether it answers the question. Just whether it sounds right.

That narrowness is the design. An agent that checks everything checks nothing well. Give this agent one domain and it becomes the authority on that domain.

---

## Why voice is the first thing to check

Most drift is invisible. A factual error is obvious. A tone violation is not. The output reads as correct, ships to the user, and the user does not notice in the moment. They just feel slightly less trust in the system over time. By the time the drift is visible, it has already done the damage.

Voice is the first layer of trust. If the output does not sound like the person, nothing else matters.

---

## The builder's job

The system prompt for this agent is the contents of `reference/voice-rules.md`. That file is all the intelligence this agent needs.

Your job is to send two things to the model: the output text being checked, and the voice rules as the system prompt. Ask the model one question: does this output violate any of these rules? Return a verdict in the shape defined in `CONTRACT.md`.

Do not add scoring. Do not return multiple verdicts. Do not ask the model to suggest improvements. One call. One verdict. One return.

---

## Where this sits

This agent is one of four that run in parallel through the coordinator. It does not know about the other agents. It does not need to. Its only concern is voice.

The coordinator collects all four verdicts and decides what happens next.
