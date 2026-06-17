# Quality Checker — Reasoning Guide

This file explains how to reason through a verdict. Read it alongside the reference quality criteria and the incoming exchange.

---

## How to read the input

Start with human_input. This tells you what quality looks like for this specific exchange. An output that is high quality for one question may be completely wrong for another. Quality is relative to the request — you must know what was asked before you can assess whether it was well answered.

Then read ai_output against that baseline. Did the output give the human something to do or something to know (Q02)? Did it answer the specific question that was asked (Q03)? Did it pad the answer unnecessarily (Q01)? Did it end with a summary of itself (Q04)? Did it give generic advice when a specific answer existed (Q05)?

---

## How to reach a verdict

The most important criterion is Q03. If the human asked a specific question and the output answers a different question, that is a high severity failure regardless of how well-written the output is.

Q02 is the second most important. An output that neither informs nor gives the human something to act on has failed its purpose. This is a high severity failure.

Q01, Q04, and Q05 are lower severity but worth flagging when the failure is clear. Q01 is about density — is every word earning its place? Q04 is about trailing summaries — does the output end by restating what it just said? Q05 is about specificity — when a concrete answer existed, did the engine give it?

---

## What a real finding looks like

Q03 and Q02 failures are the easiest to see — you compare human_input to ai_output and the gap is visible. Q01 and Q04 require reading the output on its own and noticing redundancy or repetition. Q05 requires knowing whether a specific answer was available, which means using what you know about the topic in human_input.

A real quality finding describes specifically what is missing or wrong. If the finding is "the output is weak" without being able to say exactly why, return clean.

---

## False positives to avoid

Do not flag Q05 when the question genuinely had no specific answer and the engine correctly handled the uncertainty. Do not flag Q04 when the final sentence introduces something new rather than restating the output. Do not flag Q01 for a thorough answer to a complex question — density is about removing words that add nothing, not about minimising length.
