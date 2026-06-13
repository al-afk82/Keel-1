# Build Notes — Constraints Agent

Built by: Alec
Date: 2026-06-13

---

## What I was building

An agent that connects to Band, receives an AI output as a message, checks it against hard rules, and returns a verdict in a consistent JSON format.

---

## The decisions I made and why

**Why Python**
Band's SDK is Python. The LangGraph adapter they provide works with any LangChain-compatible LLM. Anthropic's Claude is LangChain compatible via `langchain-anthropic`. Python was the only real option.

**Why the system prompt lives in the code, not Band's UI**
Band has a Prompt tab in the agent setup UI. I did not use it. The system prompt is built from the reference file at runtime. This means updating the rules means updating one file in the repo — not logging into Band and editing a UI field. The repo stays the source of truth.

**Why Claude Sonnet 4.6**
This is a constraint checking agent. It reads rules and checks text against them. It does not need the most powerful model — it needs a fast, reliable one. Sonnet 4.6 is the right balance of speed and accuracy for this task.

**Why the system prompt forces JSON only**
The coordinator expects a verdict in a specific shape. If the model returns anything else — explanation, commentary, preamble — the coordinator breaks. The system prompt instructs the model to return JSON only and nothing else.

**Why one verdict only**
Multiple violations create ambiguity in the coordinator. Which one triggers correction? Which one gets logged? The rule is simple: return the highest severity violation only. The coordinator does not need to handle arrays.

---

## How to replicate this for another agent

1. Copy `agent-constraints/agent.py` into the new agent folder
2. Change `RULES` to point at the new agent's reference file
3. Change the system prompt description to match the new agent's job
4. Change `"constraints_agent"` in `load_agent_config()` to match the key name in `agent_config.yaml`
5. Change the `"agent"` field in the verdict JSON to match the new agent name
6. Register the new agent in Band, add its ID and API key to `agent_config.yaml`
7. Run it

That is the entire replication. The logic does not change. Only the reference file and the agent name change.

---

## Setup — do this once before running anything

**1. Install dependencies**

```
uv init
uv add "band-sdk[langgraph]" langchain-anthropic python-dotenv
```

**2. Add your Anthropic API key to the .env file**

Open `.env` at the root of the repo. It looks like this:

```
BAND_API_KEY=band_a_...
ANTHROPIC_API_KEY=
```

Paste your Anthropic API key after `ANTHROPIC_API_KEY=`. Get it from console.anthropic.com.

**3. Register your agent in Band**

Go to app.band.ai. Click Agents. Click New Agent. Select Connect Remote Agent. Fill in the name, handle, and description. Band gives you an agent ID and an API key when you save.

**4. Add the agent credentials to agent_config.yaml**

Open `agent_config.yaml` at the root of the repo. Add an entry for your agent:

```yaml
your_agent_name:
  agent_id: "paste-agent-id-here"
  api_key: "paste-band-api-key-here"
```

Never commit this file. It is already in .gitignore.

---

## How to run it

```
cd hackathon-drift-agent
uv run python agent-constraints/agent.py
```

---

## What I have not solved yet

The agent receives messages through Band but I have not tested what format Band sends the message in. The coordinator needs to send the output text as a plain string. Confirm this works in Step 6 of the Band docs — Test in a Chat Room.
