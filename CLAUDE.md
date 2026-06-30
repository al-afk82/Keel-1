# Keel — Map

> The single entry point to this repository. Read this first.
> Keel is a drift detection harness. It sits on an exchange between a human and an AI engine,
> catches the moment the engine drifts from what the human actually needed, names it against a
> real rule, and writes it to a permanent record.

This file is the Map. Everything below routes you to the right folder. The structure is the system:
one folder per agent, each folder a self contained module with its own context, and a flow that
runs through those folders in order.

---

## The flow

A request moves through the folders in this order. Each agent does exactly one job.

```
human message + engine reasoning
        |
  agent-human-logger        log the human input, mint one id for the exchange
  agent-thinking-logger      log the engine reasoning, carry the same id
        |
  agent-human-profiler       name the human role and scope
  agent-engine-profiler      name the engine role and scope
        |
  agent-alignment-checker    do the two profiles agree? aligned or misaligned
        |
   misaligned -> agent-question-generator -> ask the human one question -> loop
   aligned    ->
        |
  agent-gap-analyzer         what was asked vs what was produced
        |
  run together, blind to each other:
  agent-constraints  agent-antipatterns  agent-voice-checker  agent-quality-checker  agent-identity
        |
  agent-verifier             confirm each finding holds for this exact exchange
        |
  agent-harness-logger       write only the confirmed findings to the record
```

The `coordinator` runs the floor. It holds the agents in one shared session, fires them, waits for
every verdict, and aggregates. No agent reads another agent's verdict before returning its own.

---

## The verdict

Every agent returns the same five fields: `agent`, `status`, `rule`, `excerpt`, `severity`.
Status is one of three plain states, `violation`, `uncertain`, or `clean`, never a percentage,
and a flag always carries the exact `excerpt` it fired on. Evidence, not a confidence number.

---

## Folder map

| Folder | What it holds |
|--------|---------------|
| `agent-*` | One specialist per folder. Each is a module: see the agent convention below. |
| `coordinator` | Runs the floor. Streaming coordinator plus the bridge that fans the exchange across the agents. |
| `backend` | The FastAPI harness. Receives an exchange, runs the flow, stores every confirmed finding. |
| `website` / `frontend` | The live demo app. Type a prompt, watch real Claude answer, watch the agents catch the drift. |
| `feedback-loop` | The memory layer. Reads the last confirmed violations back into context so the system reasons against its own history. Built, off by default. |
| `shared` | The verdict schema and shared utilities every agent depends on. |
| `demo` | Demo assets and scripted exchanges. |
| `build-notes` | Reference notes for how each agent is built. |

---

## The agent convention

Every `agent-*` folder is the same shape, so once you read one you can read all of them:

| File | Purpose |
|------|---------|
| `ABOUT.md` | What this agent is, in one read. |
| `ARCHITECTURE.md` | How it is wired. |
| `CONTRACT.md` | The exact input it expects and the verdict it returns. |
| `GUIDE.md` | How to run and change it. |
| `ROUTING.md` | Where its input comes from and where its output goes. |
| `agent.py` | The logic. One model call, one job, one verdict. |
| `reference/` | The standard it judges against, as plain markdown. |
| `work/` | Scratch space. |

---

## The thesis

The agents are interchangeable labour. The asset is the record. Every confirmed finding is written
down, never overwritten, only added to, each one stamped with the id of the exchange that produced
it. The standard the agents judge against lives in the `reference/` folders, as files, not as prompts
buried in code. Change the standard by changing the folder. The system is only ever as sharp as the
context you put in front of it, and that context is here, on disk, where you can read and edit it.

---

## Start here

New to the repo, read `README.md` then `DESIGN.md`. Want to see it run, open the demo. Want to change
what counts as a violation, edit the `reference/` file inside the relevant `agent-*` folder. Want the
exact message shapes, read any agent's `CONTRACT.md`.
