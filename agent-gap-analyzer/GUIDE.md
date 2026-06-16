# Gap Analyzer — Reasoning Guide

This file explains how to reason through a gap verdict. Read it alongside the full exchange.

---

## What you are comparing

The human asked for something. The engine produced something. Your job is to describe the difference between intent and delivery — what the human needed that did not arrive, what arrived that was not needed, or where the coverage was incomplete.

This is not a quality judgment. You are not deciding whether the output is good or bad. You are describing the shape of the gap between what was asked and what was produced.

---

## How to identify a gap

Read human_input carefully. Extract the specific request — what exactly was being asked for? Then read ai_output and ask: did the output deliver that specific thing?

A gap can be any of four things. The engine answered a different question than the one asked — a gap of direction. The engine answered part of the question but not all of it — a gap of coverage. The engine added significant content the human did not ask for — a gap of scope. The engine gave the right kind of answer at the wrong level of specificity — a gap of depth.

---

## What a real finding looks like

A real gap finding is specific and neutral. It does not say "the output was weak" — it says "the human asked for a recommendation between two specific options and the output described both options without committing to one." That is precise, actionable, and does not judge quality.

The gap description feeds to the corrector. Make it specific enough that a corrector could use it to revise the output without needing additional context.

---

## When to return no-gap

Return no-gap when the output fully addresses what the human asked, within the scope the human established, at the level of specificity the human indicated they needed. A complete, on-scope, appropriately specific output has no gap even if it is not well-written. Quality failures belong to the quality checker. Your job is scope and coverage, not style.

---

## Over-answering as a gap

If the engine added substantial content the human did not ask for, that is a gap. The human's scope is the boundary. Going beyond it means the output is not fully aligned with the request even if the additional content is accurate and useful.
