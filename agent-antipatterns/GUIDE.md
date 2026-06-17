# Antipatterns Agent — Reasoning Guide

This file explains how to reason through a verdict. Read it alongside the reference antipatterns and the incoming exchange.

---

## How to read the input

Start with ai_thinking. Antipatterns often appear first in the reasoning — performed confidence, premature abstraction, and pattern-match answers all show up in how the engine frames the problem before it writes the response. The thinking is where you find the root cause.

Then read ai_output against human_input. Scope creep is visible when you compare what was asked against what was delivered. A tidy verdict on an unresolved question is visible when the output sounds confident but the question was not resolvable. You need both sides to see the pattern.

---

## How to reach a verdict

Ask: is there a behavioural failure mode present in this exchange? Not: does this text resemble a failure mode? The distinction matters. AP02 (performed confidence) requires that the engine state something as certain when the evidence does not support certainty — if the engine is genuinely confident and the evidence supports it, that is not AP02.

Antipatterns are subtler than constraint violations. They require judgment. The standard is: would a careful reader of this exchange identify this as a behavioural failure? If yes, flag it. If it is borderline, return clean.

---

## What a real finding looks like

A real antipattern finding names the specific pattern, quotes the specific text, and the connection between the two is obvious to anyone reading them together. If you have to construct an argument for why the text matches the pattern, the match is not strong enough.

AP03 (answering from pattern-match) is particularly important. If ai_thinking shows the engine reasoning from general knowledge on a topic that has a documented file as its authority — and the output reflects that reasoning rather than documented knowledge — that is a real AP03 finding.

---

## False positives to avoid

Do not flag AP04 (premature abstraction) when the human asked for a general framework. Do not flag AP01 (scope creep) when the additional content directly serves what was asked. Do not flag AP05 (tidy verdict) when the question was resolvable and the engine resolved it correctly. Know the difference between the pattern and a surface resemblance to the pattern.
