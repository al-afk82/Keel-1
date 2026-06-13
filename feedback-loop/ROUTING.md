# Feedback Loop — Routing

This file defines when the feedback loop fires and what it reads.

---

## When it fires

Not on every output. The feedback loop runs on a schedule or when manually triggered by the user.

The default trigger is every 50 log entries. That threshold is a starting point, not a fixed rule. If the system is catching violations frequently, lower the threshold. If it is rarely firing, raise it. The goal is to surface patterns before they become entrenched, not to run the analysis constantly.

---

## What it reads

The full catch log. Every entry.

The feedback loop does not make model calls on individual outputs. It analyses the log as a dataset. Pattern detection across many entries, not deep analysis of one.

---

## The three signals in the log

`user_response: "accepted"` — the correction was right. Count toward the pattern threshold.

`user_response: "overridden"` — the correction was wrong. The agent flagged something it should not have. Flag the existing rule for review. Do not count toward the pattern threshold.

`user_response: null` — the user did not respond. Do not count. Null is not confirmation.

---

## What it writes

Proposed rules to `work/proposed-rules.md`. Nothing else. It does not write to agent reference files directly. It does not modify the catch log. It does not send anything to the user without human review of the proposals first.

---

## The human in the loop

This is a deliberate design choice. Automated rule generation without human review produces rules that sound correct and are not. A pattern in the log might reflect a real gap in the agent's knowledge or it might reflect an unusual week of outputs that will not recur.

The human decides. The feedback loop does the analysis work. That division is the design.
