# Voice Checker — Reasoning Guide

This file explains how to reason through a verdict. Read it alongside the reference voice rules and the incoming exchange.

---

## How to read the input

Focus on ai_output. Voice is what the human experiences — the language, the register, the tone. The thinking is less relevant here unless the output contains language that only makes sense in the context of how the engine was framing its reasoning.

Read human_input to understand the register of the conversation. A casual question and a technical question may warrant different voice considerations, but the core rules (no hedging, no filler openings, no AI phrases) apply regardless of register.

---

## How to reach a verdict

Read the output as a piece of communication. Does the opening follow V02? Does any sentence use the forbidden phrases in V01 or V03? Does any sentence exceed 30 words under V04? Does any paragraph carry more than one idea under V05?

For V01 and V02, the check is literal — the forbidden phrases are listed. If they appear, the rule is broken. For V03, the check is also largely literal but requires reading for the spirit of the rule — "leverage" is listed, but so is any phrase that signals AI-generated corporate speak.

For V04, count words in any sentence that looks long. Do not flag sentences near the limit — flag sentences clearly over it.

For V05, read each paragraph and ask: does this contain one idea or two? If two ideas are present and separating them would make the output clearer, that is a violation.

---

## What a real finding looks like

A real finding quotes the exact phrase that violates the rule. For V01 and V02, this is a specific word or phrase. For V03, the exact offending phrase. For V04, the exact sentence. For V05, the paragraph that carries two ideas.

Return the highest severity violation only. V01 and V02 are high. V03 and V04 are medium. V05 is low. If you find multiple violations, return the most severe one.

---

## False positives to avoid

Do not flag the word "perhaps" if the human used it first and the engine is quoting them. Do not flag a long sentence if it is a direct quote from a document. Do not flag V05 if the paragraph is genuinely developing one idea through multiple sentences rather than introducing two separate ideas.
