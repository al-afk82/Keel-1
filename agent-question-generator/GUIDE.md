# Question Generator — Reasoning Guide

This file explains how to reason through a question. Read it alongside the misalignment reason and previous questions.

---

## What you are producing

One question. That question, if answered by the human, should give the engine enough information to re-run the exchange with the correct role and scope assumed. The alignment checker should return aligned after the human answers it.

---

## How to derive the question from the misalignment reason

The misalignment reason names the gap between what the human was in and what the engine assumed. Your question must close that gap.

If the gap is about role — the engine assumed the wrong kind of collaborator — your question should surface what kind of response the human actually needs. "Are you looking for a recommendation or an explanation of both options?" closes a role gap between advisor and teacher.

If the gap is about scope — the engine ranged beyond what the human wanted, or narrowed too far — your question should establish the boundary. "Do you want this addressed for the whole system or just the component you mentioned?" closes a scope gap.

If the gap is about both, address the role gap first. Role determines what the output is trying to do. Scope determines how far it goes. Getting the role right is more important.

---

## The non-repetition rule

Read previous_questions before generating. If the gap you are addressing was already asked about, the previous question did not resolve it — which means you need a different angle, not the same question rephrased. Look at the misalignment reason again and find a different specific aspect of the gap to ask about.

If the gap is fundamentally the same as a previous question, the problem may be that the human's answer did not give the engine enough to work with. In that case, ask about the specific thing the previous answer left ambiguous.

---

## What a good question looks like

A good question is answerable in one sentence. It is specific to the misalignment reason, not general. It does not ask for information the human already provided. It does not ask two things at once. If the human answers it honestly, the alignment checker will return aligned on the next pass.

A bad question is vague ("can you tell me more?"), compound ("what are you looking for and how detailed should it be?"), or already answered ("you mentioned earlier that you want X — do you want X?").
