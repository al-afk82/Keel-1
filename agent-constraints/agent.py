import asyncio
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, MessagesState, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import ToolNode
from band import Agent
from band.adapters.langgraph import LangGraphAdapter
from band.config import load_agent_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RULES = (Path(__file__).parent / "reference" / "constraints.md").read_text()

SYSTEM_PROMPT = f"""You are the constraints agent. Your only job is to check whether an AI output violates any of the hard rules below.

You receive a JSON object containing:
- "input_id": the unique ID assigned to this exchange by A1 at log time
- "ai_output": the AI response to check
- "context": a short description of what this exchange was about

Your verdict must carry the input_id so every violation is traceable back to the exact exchange that triggered it.

Before flagging a violation, verify that the rule actually applies to this context. A constraint about outreach copy does not apply to a technical explanation. If the rule does not apply to the context, return clean.

Use band_send_message to return this exact JSON. No other text. No explanation.

If a violation is found:
{{
  "agent": "constraints",
  "input_id": "the input_id from the incoming message",
  "status": "violation",
  "rule": "rule ID and name",
  "excerpt": "the exact offending text",
  "severity": "high or medium",
  "context_relevant": true,
  "pending_verification": true
}}

If no violation is found:
{{
  "agent": "constraints",
  "input_id": "the input_id from the incoming message",
  "status": "clean",
  "rule": null,
  "excerpt": null,
  "severity": null,
  "context_relevant": true,
  "pending_verification": false
}}

If multiple rules are violated, return the highest severity only. One verdict. Nothing else.

Violations are marked pending_verification true — they do not write to the harness until the verifier confirms them.

---

{RULES}"""


def make_graph(band_tools: list) -> object:
    llm = ChatAnthropic(
        model="claude-sonnet-4-6",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )
    llm_with_tools = llm.bind_tools(band_tools)

    def call_model(state: MessagesState) -> dict:
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: MessagesState) -> str:
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return END

    graph = StateGraph(MessagesState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(band_tools))
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, ["tools", END])
    graph.add_edge("tools", "agent")

    return graph.compile(checkpointer=InMemorySaver())


async def main():
    load_dotenv(override=True)

    agent_id, api_key = load_agent_config("constraints_agent")

    adapter = LangGraphAdapter(
        graph_factory=make_graph,
        inject_system_prompt=False,
    )

    agent = Agent.create(
        adapter=adapter,
        agent_id=agent_id,
        api_key=api_key,
    )

    logger.info("Constraints agent running. Press Ctrl+C to stop.")
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
