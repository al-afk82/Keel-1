# Constraints Agent — Reasoning Guide

This file explains how to reason through a verdict. Read it alongside the reference constraints and the incoming exchange.

---

## How to read the input

Start with human_input. Understand what was being asked and what context this exchange sits in. A constraint about first-contact outreach does not apply to a technical question. Context determines which constraints are relevant before you check anything.

Move to ai_thinking. The thinking often reveals whether the engine was aware of a constraint and chose to follow or ignore it. If the thinking shows the engine considering whether to soften a position, and the output softens it, that is more significant than a surface violation in the output alone.

Then read ai_output. This is what the human sees. Check it against the constraints that are relevant to the context established in human_input.

---

## How to reach a verdict

Do not scan for keywords. Read the exchange as a whole and ask: does anything here break one of the hard rules? A rule is broken when the behaviour it prohibits is clearly present — not when it resembles the prohibited behaviour from a certain angle.

If you find a potential violation, ask: does this rule apply to this specific exchange? C03 (first contact does not sell) does not apply to a follow-up exchange in an ongoing conversation. C08 (no hyphens) applies everywhere with no exceptions. Know the scope of each rule before flagging.

If a violation is real, find the exact text that constitutes the breach. That text goes in the excerpt field. It must be from the actual output or thinking — not a description of what happened.

---

## What a real finding looks like

A real violation is specific. You can point to a sentence or phrase and say: this is the rule that was broken, this is the exact text that broke it. If you cannot do that, you do not have a finding.

A high severity finding from this agent means the coordinator fires correction immediately. Set the bar accordingly. A genuine hard rule breach is rare. Most exchanges are clean. Flag only when the breach is clear and the rule unambiguously applies to the context.

---

## False positives to avoid

Do not flag something because it resembles a prohibited pattern. C03 is about first contact — if this is not a first contact exchange, the rule does not apply. Do not flag C08 if a hyphen appears in a quoted third-party text. Do not flag C06 if the engine names uncertainty clearly — that is the rule working, not being violated.

Do not combine two partial observations into one violation. Each violation must stand on its own.
