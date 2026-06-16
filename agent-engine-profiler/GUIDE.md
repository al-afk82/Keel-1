# Engine Profiler — Reasoning Guide

This file explains how to reason through a profile. Read it alongside the engine's internal thinking.

---

## What you are extracting

Two things: the role the engine assumed in its reasoning, and the scope it treated the request as having.

Role is not what the engine said it was doing. It is what the thinking reveals about how the engine framed its task. Did it reason as an advisor? A technical expert? A teacher? A collaborator? The framing that drives the thinking is the role.

Scope is what the engine treated the request as covering. Did the thinking stay within what was asked, or did it range beyond? Did the engine decide to address adjacent topics, add unrequested context, or narrow the request to a part of what was asked?

---

## How to read the thinking

The thinking reveals the engine's model of the situation before the output is constructed. Read it for the implicit assumptions the engine made. What did it assume the human needed? What did it decide was relevant? What did it choose not to address?

The first part of the thinking usually reveals the role the engine assumed. The middle part reveals how the engine scoped the problem. The end of the thinking often reveals whether the engine stayed within scope or expanded it.

---

## What a good profile looks like

Role is a short, specific description of the capacity the engine reasoned in. Not "assistant" — something like "technical expert explaining a mechanism" or "advisor recommending between two options" or "teacher building a conceptual model."

Scope is a short description of what the engine treated the request as covering. If the engine added context the human did not ask for, note that the scope is wider than the request. If the engine narrowed the request, note the boundary it applied.

The profile feeds directly into the alignment checker. Be specific enough that the comparison to the human profile is clear.
