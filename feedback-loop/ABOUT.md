# Feedback Loop — About

The four agents know what was wrong at the start. This layer learns what is wrong over time. It reads the catch log, finds patterns in what keeps getting corrected, and proposes new rules so the agents get better at catching the next version of the same problem.

This is the adaptation layer. Without it, the system is a static filter. With it, the system is a learning one.

---

## The principle

Every correction is a signal. An accepted correction means the agent caught something real and fixed it correctly. Three accepted corrections with the same pattern means the pattern is real and recurring. A recurring pattern that is not yet a named rule is a gap in the agent's knowledge.

This layer closes that gap. It reads the signal, identifies the pattern, and proposes a rule in the format the relevant agent already understands.

---

## The story that makes this concrete

A voice agent was built with five rules. Over three days, the corrector fired twelve times on outputs that started with the phrase "It is worth noting that." The rule that should have caught that did not exist yet. V01 covered "I think" and hedging phrases. It did not cover soft-opening qualifiers.

The feedback loop read the log, saw twelve accepted corrections with the same structure, and proposed a new rule: "V06 — No soft-opening qualifiers. Forbidden: 'It is worth noting', 'It should be said', 'It is important to mention'."

The rule was confirmed by the user and added to the voice agent's reference file. The agent did not need retraining. It just needed a better reference file.

That is the whole mechanism.

---

## What this layer does not do

It does not write rules automatically. Every proposed rule requires human confirmation before it goes into any agent's reference file. The human is the authority. The feedback loop is the analyst.

It does not read agent calls or conversation history. It reads the catch log only. The log is the single source of truth.

---

## The builder's job

Build a function that reads the catch log, groups entries by rule ID, counts accepted corrections per rule, and flags any rule that crosses the threshold defined in `reference/pattern-threshold.md`. For each flagged pattern, draft a new rule in the format used by that agent's reference file and write it to `work/proposed-rules.md`.

The user reviews `work/proposed-rules.md`. They confirm or reject each proposal. Confirmed rules get appended to the relevant agent reference file manually or by a second function.

---

## Where this sits

The feedback loop runs after the coordinator. It does not sit in the live output path. It runs on a schedule or when manually triggered. It is the background intelligence of the system.
