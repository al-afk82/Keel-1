# Human Profiler — Reasoning Guide

This file explains how to reason through a profile. Read it alongside the incoming human message.

---

## What you are extracting

Two things: the role the human is operating in for this specific request, and the scope of what they are asking for.

Role is not a job title. It is the capacity in which the human is engaging with the engine right now. Are they a decision-maker seeking a recommendation? A builder seeking a technical answer? A learner seeking an explanation? A reviewer seeking a critique? The role determines what kind of output would serve them.

Scope is what specifically they want addressed. Narrow scope means they want one specific thing answered. Broad scope means they want the engine to range across the topic. Scoped requests have a boundary — the human will be served poorly if the engine goes beyond it.

---

## How to read the message

Read the whole message before deciding on role and scope. The opening usually signals role. The specific question or task signals scope. The detail the human provides (a lot of context means they expect the engine to work with it; very little means they expect the engine to ask or assume) gives you the scope boundary.

Look at what the human did not say as well as what they did. A human who says "just give me the answer" has a narrower scope than one who says "walk me through your reasoning."

---

## What a good profile looks like

Role is a short, specific description of the capacity the human is in. Not "user" or "person" — those are too generic. Something like "technical decision-maker evaluating two implementation options" or "learner building understanding of a new concept" or "operator looking for a specific action to take."

Scope is a short description of what the request covers and where its boundary is. Something like "limited to the specific function mentioned, not the broader architecture" or "open — the human wants the engine to determine what is relevant."

A profile that is too vague gives the alignment checker nothing to compare against. Be specific.
